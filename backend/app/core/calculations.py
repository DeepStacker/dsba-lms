"""
Calculation utilities for SGPA/CGPA and CO/PO attainment analysis
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, List, Any, Optional
from ..models.models import User, Course, Exam, Attempt, Response, CO, PO, InternalScore, InternalComponent
from decimal import Decimal
import math


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

    query = """
        SELECT c.id, c.credits, e.raw_score, e.max_score
        FROM courses c
        JOIN internal_scores e ON e.student_id = $1 AND e.course_id = c.id
        JOIN internal_components ic ON e.component_id = ic.id
        WHERE 1=1
    """

    params = [student_id]

    if semester:
        query += " AND ic.name LIKE $%d" % (len(params) + 1)
        params.append(f"%semester {semester}%")

    if academic_year:
        query += " AND ic.name LIKE $%d" % (len(params) + 1)
        params.append(f"%{academic_year}%")

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

    sgpa = weighted_gpa / total_credits if total_credits > 0 else 0

    return {
        "sgpa": round(sgpa, 2),
        "total_credits": total_credits,
        "grade_points": round(weighted_gpa / total_credits if total_credits > 0 else 0, 2),
        "course_grades": course_grades,
        "semester": semester,
        "academic_year": academic_year
    }


async def calculate_cgpa(db: AsyncSession, student_id: int, semester: Optional[int] = None,
                        academic_year: Optional[str] = None) -> Dict[str, Any]:
    """Calculate Cumulative Grade Point Average"""

    # Calculate multiple SGPA scores and aggregate

    semesters_query = """
        SELECT DISTINCT ic.name
        FROM internal_components ic
        JOIN internal_scores iss ON iss.component_id = ic.id
        WHERE iss.student_id = $1
        AND ic.name LIKE '%semester%'
        ORDER BY ic.name
    """

    result = await db.execute(semesters_query, (student_id,))
    semester_names = result.fetchall()

    total_credits = 0
    total_weighted_gpa = 0
    semesters_included = []

    for semester_data in semester_names:
        semester_match = semester_data.name.lower()
        if "semester" in semester_match:
            sem_num = int(''.join(filter(str.isdigit, semester_match)))
            if semester and sem_num > semester:
                continue

            sgpa_result = await calculate_sgpa(db, student_id, semester=sem_num)
            if sgpa_result["total_credits"] > 0:
                total_weighted_gpa += sgpa_result["grade_points"] * sgpa_result["total_credits"]
                total_credits += sgpa_result["total_credits"]
                semesters_included.append(sem_num)

    cgpa = total_weighted_gpa / total_credits if total_credits > 0 else 0

    return {
        "cgpa": round(cgpa, 2),
        "total_credits": total_credits,
        "semesters_included": semesters_included
    }


async def calculate_co_attainment(db: AsyncSession, co_id: int, exam_ids: Optional[List[int]] = None) -> float:
    """Calculate CO (Course Outcome) attainment"""

    # Get all questions mapped to this CO
    query = """
        SELECT DISTINCT q.id, q.max_marks
        FROM questions q
        WHERE q.co_id = $1
    """

    params = [co_id]

    if exam_ids:
        query += """
            AND q.id IN (
                SELECT eq.question_id
                FROM exam_questions eq
                WHERE eq.exam_id IN (%s)
            )
        """ % ','.join('$' + str(len(params) + 1 + i) for i in range(len(exam_ids)))

        params.extend(exam_ids)

    result = await db.execute(query, params)
    co_questions = result.fetchall()

    if not co_questions:
        return 0.0

    total_attainment = 0
    question_count = 0

    for question_id, max_marks in co_questions:
        # Calculate attainment for this question
        attainment = await calculate_question_co_attainment(db, question_id, exam_ids)
        total_attainment += attainment
        question_count += 1

    return total_attainment / question_count if question_count > 0 else 0.0


async def calculate_question_co_attainment(db: AsyncSession, question_id: int,
                                          exam_ids: Optional[List[int]] = None) -> float:
    """Calculate CO attainment for a specific question"""

    # Get all responses for this question
    query = """
        SELECT r.ai_score, r.teacher_score, r.final_score, q.max_marks
        FROM responses r
        JOIN questions q ON q.id = r.question_id
        WHERE r.question_id = $1
    """

    params = [question_id]

    if exam_ids:
        query += """
            AND r.attempt_id IN (
                SELECT a.id FROM attempts a WHERE a.exam_id IN (%s)
            )
        """ % ','.join('$' + str(len(params) + 1 + i) for i in range(len(exam_ids)))

        params.extend(exam_ids)

    result = await db.execute(query, params)
    responses = result.fetchall()

    if not responses:
        return 0.0

    total_score = 0
    max_possible = 0

    for ai_score, teacher_score, final_score, max_marks in responses:
        score = final_score or teacher_score or ai_score or 0
        total_score += score
        max_possible += max_marks

    attainment = (total_score / max_possible) * 100 if max_possible > 0 else 0
    return attainment


async def calculate_po_attainment(db: AsyncSession, po_id: int, exam_ids: Optional[List[int]] = None) -> float:
    """Calculate PO (Program Outcome) attainment"""

    # Get all COs mapped to this PO and their weights
    query = """
        SELECT cpm.co_id, cpm.weight
        FROM co_po_maps cpm
        WHERE cpm.po_id = $1
    """

    result = await db.execute(query, (po_id,))
    co_mappings = result.fetchall()

    if not co_mappings:
        return 0.0

    total_attainment = 0
    total_weight = 0

    for co_id, weight in co_mappings:
        co_attainment = await calculate_co_attainment(db, co_id, exam_ids)
        total_attainment += co_attainment * weight
        total_weight += weight

    return total_attainment / total_weight if total_weight > 0 else 0.0


def get_score_distribution(scores: List[float]) -> Dict[str, int]:
    """Get score distribution for analytics"""
    if not scores:
        return {}

    min_score = min(scores)
    max_score = max(scores)
    range_size = (max_score - min_score) / 10 if max_score > min_score else 1

    distribution = {}
    for i in range(10):
        bucket_min = min_score + i * range_size
        bucket_max = min_score + (i + 1) * range_size
        count = sum(1 for s in scores if bucket_min <= s < bucket_max)
        if count > 0:
            bucket_name = f"{bucket_min:.1f}"
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
    attempts_query = """
        SELECT COUNT(*), AVG(CASE WHEN final_score THEN 1 ELSE 0 END) as completion_rate
        FROM attempts
        WHERE exam_id = $1
    """

    attempt_stats = await db.execute(attempts_query, (exam_id,))
    attempts_data = attempt_stats.fetchone()

    # Get response statistics
    responses_query = """
        SELECT
            AVG(final_score) as avg_score,
            MIN(final_score) as min_score,
            MAX(final_score) as max_score,
            COUNT(*) as total_responses
        FROM responses r
        JOIN attempts a ON a.id = r.attempt_id
        WHERE a.exam_id = $1 AND r.final_score IS NOT NULL
    """

    response_stats = await db.execute(responses_query, (exam_id,))
    response_data = response_stats.fetchone()

    # Get proctoring events
    proctor_query = """
        SELECT event_type, COUNT(*) as count
        FROM proctor_logs pl
        JOIN attempts a ON a.id = pl.attempt_id
        WHERE a.exam_id = $1
        GROUP BY event_type
    """

    proctor_stats = await db.execute(proctor_query, (exam_id,))
    proctor_data = dict(proctor_stats.fetchall())

    return {
        "exam_id": exam_id,
        "total_attempts": attempts_data[0] if attempts_data[0] else 0,
        "completion_rate": round(attempts_data[1] * 100, 2) if attempts_data[1] else 0,
        "avg_score": round(response_data.avg_score, 2) if response_data.avg_score else 0,
        "min_score": response_data.min_score if response_data.min_score else 0,
        "max_score": response_data.max_score if response_data.max_score else 0,
        "total_responses": response_data.total_responses if response_data.total_responses else 0,
        "proctor_events": proctor_data
    }
