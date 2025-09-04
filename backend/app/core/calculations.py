"""
Calculation utilities for SGPA/CGPA and CO/PO attainment analysis
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, List, Any, Optional
from ..models.models import User, Course, Exam, Attempt, Response, CO, PO, InternalScore, InternalComponent, Question, CO_PO_Map
from decimal import Decimal
import math
from sqlalchemy import text # Ensure text is imported for raw SQL queries


# Default grade bands - can be made configurable
GRADE_BANDS = {
    "O": 10.0, "A+": 9.0, "A": 8.0, "B+": 7.5,
    "B": 7.0, "C+": 6.5, "C": 6.0, "D": 4.0, "F": 0.0
}


def get_grade_point_from_marks(marks: float, max_marks: float) -> float:
    """Convert absolute marks to grade points"""
    if max_marks == 0:
        return 0

    percentage = (marks / max_marks) * 100

    if percentage >= 95:
        return GRADE_BANDS["O"]
    elif percentage >= 90:
        return GRADE_BANDS["A+"]
    elif percentage >= 85:
        return GRADE_BANDS["A"]
    elif percentage >= 80:
        return GRADE_BANDS["B+"]
    elif percentage >= 75:
        return GRADE_BANDS["B"]
    elif percentage >= 70:
        return GRADE_BANDS["C+"]
    elif percentage >= 60:
        return GRADE_BANDS["C"]
    elif percentage >= 40:
        return GRADE_BANDS["D"]
    else:
        return GRADE_BANDS["F"]


async def calculate_sgpa(db: AsyncSession, student_id: int, semester: Optional[int] = None,
                        academic_year: Optional[str] = None) -> Dict[str, Any]:
    """Calculate Semester Grade Point Average"""

    # Get courses and assessments for the semester
    # This is a simplified implementation - adjust based on actual schema

    query = text(
        "SELECT c.id as course_id, c.credits, e.raw_score, e.max_score "
        "FROM courses c "
        "JOIN internal_scores e ON e.student_id = :student_id AND e.course_id = c.id "
        "JOIN internal_components ic ON e.component_id = ic.id "
        "WHERE 1=1"
    )

    params = {"student_id": student_id}

    if semester:
        query = text(str(query) + " AND ic.name LIKE :semester") # Assuming semester is part of component name
        params["semester"] = f"%semester {semester}%"

    if academic_year:
        query = text(str(query) + " AND ic.name LIKE :academic_year") # Assuming academic year is part of component name
        params["academic_year"] = f"%{academic_year}%"

    result = await db.execute(query, params)
    scores = result.fetchall()

    total_credits = 0
    weighted_gpa = 0

    course_grades = []

    for course_id, credits, raw_score, max_score in scores:
        if credits > 0:
            grade_point = get_grade_point_from_marks(raw_score, max_score)
            weighted_gpa += grade_point * credits
            total_credits += credits

            course_grades.append({
                "course_id": course_id,
                "credits": credits,
                "marks": raw_score,
                "max_marks": max_score,
                "grade_point": grade_point
            })

    sgpa = weighted_gpa / Decimal(total_credits) if total_credits > 0 else 0
    grade_points = weighted_gpa / Decimal(total_credits) if total_credits > 0 else 0

    return {
        "sgpa": round(float(sgpa), 2),
        "total_credits": total_credits,
        "grade_points": round(float(grade_points), 2),
        "course_grades": course_grades,
        "semester": semester,
        "academic_year": academic_year
    }


async def calculate_cgpa(db: AsyncSession, student_id: int, semester: Optional[int] = None,
                        academic_year: Optional[str] = None) -> Dict[str, Any]:
    """Calculate Cumulative Grade Point Average"""

    # Calculate multiple SGPA scores and aggregate
    semesters_query = text(
        "SELECT DISTINCT ic.name FROM internal_components ic "
        "JOIN internal_scores iss ON iss.component_id = ic.id "
        "WHERE iss.student_id = :student_id AND ic.name LIKE '%semester%' ORDER BY ic.name"
    )

    result = await db.execute(semesters_query, {"student_id": student_id})
    semester_names = [row[0] for row in result.fetchall()] # Extract string names

    total_credits_cumulative = 0
    total_weighted_gpa_cumulative = 0
    semesters_included = []

    for s_name in semester_names:
        # Attempt to parse semester number (e.g., "Fall 2023 Semester 1")
        sem_num_str = ''.join(filter(str.isdigit, s_name))
        sem_num = int(sem_num_str) if sem_num_str else None

        if sem_num is not None:
            if semester and sem_num > semester: # Filter for 'up to semester'
                continue

            sgpa_result = await calculate_sgpa(db, student_id, semester=sem_num) # Pass numeric semester
            if sgpa_result["total_credits"] > 0:
                total_weighted_gpa_cumulative += Decimal(sgpa_result["grade_points"]) * sgpa_result["total_credits"]
                total_credits_cumulative += sgpa_result["total_credits"]
                semesters_included.append(sem_num)

    cgpa = total_weighted_gpa_cumulative / Decimal(total_credits_cumulative) if total_credits_cumulative > 0 else 0

    return {
        "cgpa": round(float(cgpa), 2),
        "total_credits": total_credits_cumulative,
        "semesters_included": sorted(list(set(semesters_included))) # Unique and sorted
    }


async def calculate_co_attainment(db: AsyncSession, co_id: int, 
                                   student_ids: Optional[List[int]] = None,
                                   exam_ids: Optional[List[int]] = None) -> float:
    """Calculate CO (Course Outcome) attainment for specific students and/or exams"""

    # First, find all questions linked to this CO
    question_query = select(Question.id, Question.max_marks).where(Question.co_id == co_id)
    questions_for_co_result = await db.execute(question_query)
    questions_for_co = questions_for_co_result.fetchall()

    if not questions_for_co:
        return 0.0

    total_attainment_sum = 0.0
    total_max_marks_sum = 0.0
    
    # Iterate through each question linked to the CO
    for q_id, q_max_marks in questions_for_co:
        # Build base query for responses to this question
        # We need to join through attempts to filter by student_ids or exam_ids
        response_query = select(Response.final_score).join(Attempt, Response.attempt_id == Attempt.id).where(Response.question_id == q_id)
        
        # Filter by student_ids if provided
        if student_ids:
            response_query = response_query.where(Attempt.student_id.in_(student_ids))

        # Filter by exam_ids if provided
        if exam_ids:
            response_query = response_query.where(Attempt.exam_id.in_(exam_ids))
        
        responses_result = await db.execute(response_query)
        responses = responses_result.scalars().all()

        if responses:
            student_scores_for_question = [score for score in responses if score is not None]
            if student_scores_for_question:
                total_attainment_sum += sum(student_scores_for_question)
                # Max possible score for this question across all relevant students
                total_max_marks_sum += (q_max_marks if q_max_marks is not None else 0) * len(student_scores_for_question)


    if total_max_marks_sum == 0.0:
        return 0.0

    attainment_percentage = (total_attainment_sum / total_max_marks_sum) * 100
    return attainment_percentage


async def calculate_po_attainment(db: AsyncSession, po_id: int, 
                                  student_ids: Optional[List[int]] = None,
                                  exam_ids: Optional[List[int]] = None) -> float:
    """Calculate PO (Program Outcome) attainment using weighted projection from COs for specific students and/or exams"""

    # Get all COs mapped to this PO and their weights
    co_po_maps_result = await db.execute(
        select(CO_PO_Map.co_id, CO_PO_Map.weight)
        .where(CO_PO_Map.po_id == po_id)
    )
    co_mappings = co_po_maps_result.fetchall()

    if not co_mappings:
        return 0.0

    weighted_co_attainment_sum = 0.0
    total_weight_sum = 0.0

    for co_id, weight in co_mappings:
        co_attainment_percentage = await calculate_co_attainment(db, co_id, student_ids=student_ids, exam_ids=exam_ids)
        weighted_co_attainment_sum += co_attainment_percentage * (weight if weight is not None else 0)
        total_weight_sum += (weight if weight is not None else 0)

    if total_weight_sum == 0.0:
        return 0.0

    po_attainment_percentage = weighted_co_attainment_sum / total_weight_sum
    return po_attainment_percentage


def get_score_distribution(scores: List[float]) -> Dict[str, int]:
    """Get score distribution for analytics"""
    if not scores:
        return {}
    # Create 10 buckets inclusive of max score in the last bucket.
    min_score = min(scores)
    max_score = max(scores)
    # Avoid division by zero when all scores are equal.
    if max_score == min_score:
        return {f"{min_score:.1f}": len(scores)}

    num_buckets = 10
    range_size = (max_score - min_score) / num_buckets

    # Use bucket edges and include max_score in the last bucket
    buckets = [min_score + i * range_size for i in range(num_buckets + 1)]

    distribution: Dict[str, int] = {}
    for i in range(num_buckets):
        bmin = buckets[i]
        bmax = buckets[i + 1]
        # include the upper edge for the last bucket
        if i == num_buckets - 1:
            count = sum(1 for s in scores if bmin <= s <= bmax)
        else:
            count = sum(1 for s in scores if bmin <= s < bmax)

        if count > 0:
            bucket_name = f"{bmin:.1f}"
            distribution[bucket_name] = count

    return distribution


async def calculate_exam_statistics(db: AsyncSession, exam_id: int) -> Dict[str, Any]:
    """Calculate comprehensive exam statistics"""

    # Get basic exam info
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_result.scalar_one_or_none()

    if not exam:
        return {"error": "Exam not found"}

    # Get attempts and responses
    attempts_query = text(
        "SELECT COUNT(*) as cnt, AVG(CASE WHEN submitted_at IS NOT NULL THEN 1.0 ELSE 0.0 END) as completion_rate FROM attempts WHERE exam_id = :exam_id"
    )
    attempt_stats = await db.execute(attempts_query, {"exam_id": exam_id})
    attempts_data = attempt_stats.fetchone()

    # Get response statistics
    responses_query = text("""
        SELECT
            AVG(final_score::numeric) as avg_score,
            MIN(final_score::numeric) as min_score,
            MAX(final_score::numeric) as max_score,
            COUNT(DISTINCT r.id) as total_responses
        FROM responses r
        JOIN attempts a ON a.id = r.attempt_id
        WHERE a.exam_id = :exam_id AND r.final_score IS NOT NULL
    """)

    response_stats = await db.execute(responses_query, {"exam_id": exam_id})
    response_data = response_stats.fetchone() # Use fetchone() for single row results

    # Get proctoring events
    proctor_query = text("""
        SELECT event_type, COUNT(*) as count
        FROM public.proctor_logs pl
        JOIN public.attempts a ON a.id = pl.attempt_id
        WHERE a.exam_id = :exam_id
        GROUP BY event_type
    """)

    proctor_stats = await db.execute(proctor_query, {"exam_id": exam_id})
    proctor_data = dict(proctor_stats.fetchall())

    return {
        "exam_id": exam_id,
        "total_attempts": attempts_data[0] if attempts_data and attempts_data[0] is not None else 0,
        "completion_rate": round(attempts_data[1] * 100, 2) if attempts_data and attempts_data[1] is not None else 0,
        "avg_score": round(float(response_data.avg_score), 2) if response_data and response_data.avg_score is not None else 0,
        "min_score": float(response_data.min_score) if response_data and response_data.min_score is not None else 0,
        "max_score": float(response_data.max_score) if response_data and response_data.max_score is not None else 0,
        "total_responses": response_data.total_responses if response_data and response_data.total_responses is not None else 0,
        "proctor_events": proctor_data
    }