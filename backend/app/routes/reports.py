from fastapi import APIRouter, Depends, HTTPException, status, Query, Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, text, desc
from typing import List, Optional, Dict, Any
import json
import pandas as pd
import io
from datetime import datetime, timedelta
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..models.models import (
    User, Program, Course, CO, PO, CO_PO_Map, ClassSection, Enrollment,
    Exam, Question, Attempt, Response, InternalScore, InternalComponent
)
from ..schemas.common import Response as CommonResponse
from pydantic import BaseModel

router = APIRouter()

# ==================== ANALYTICS MODELS ====================

class StudentAnalytics(BaseModel):
    student_id: int
    student_name: str
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    total_exams: int
    completed_exams: int
    average_score: Optional[float] = None
    co_attainment: Dict[str, float] = {}
    po_attainment: Dict[str, float] = {}
    strengths: List[str] = []
    weaknesses: List[str] = []
    rank: Optional[int] = None

class CourseAnalytics(BaseModel):
    course_id: int
    course_name: str
    total_students: int
    average_performance: Optional[float] = None
    co_attainment: Dict[str, Dict[str, float]] = {}  # CO -> {class_avg, target, status}
    po_attainment: Dict[str, Dict[str, float]] = {}  # PO -> {class_avg, target, status}
    exam_statistics: List[Dict[str, Any]] = []
    grade_distribution: Dict[str, int] = {}

class SystemAnalytics(BaseModel):
    total_users: int
    active_students: int
    total_courses: int
    total_exams: int
    completed_exams: int
    ai_graded_responses: int
    teacher_graded_responses: int
    system_utilization: Dict[str, Any] = {}

# ==================== STUDENT ANALYTICS ====================

@router.get("/student/{student_id}/analytics", response_model=StudentAnalytics)
async def get_student_analytics(
    student_id: int,
    semester: Optional[int] = None,
    academic_year: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics for a student"""
    # Check permissions
    if current_user.role.value == "student" and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own analytics"
        )
    
    # Get student details
    student_result = await db.execute(select(User).where(User.id == student_id))
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get student's enrollments
    enrollments_result = await db.execute(
        select(Enrollment, ClassSection, Course)
        .join(ClassSection, Enrollment.class_id == ClassSection.id)
        .join(Course, ClassSection.course_id == Course.id)
        .where(Enrollment.student_id == student_id)
    )
    
    enrollments = enrollments_result.all()
    course_ids = [course.id for _, _, course in enrollments]
    
    if not course_ids:
        return StudentAnalytics(
            student_id=student_id,
            student_name=student.name,
            total_exams=0,
            completed_exams=0
        )
    
    # Get exam attempts and scores
    attempts_result = await db.execute(
        select(
            Attempt,
            Exam,
            func.sum(Response.final_score).label('total_score'),
            func.sum(Question.max_marks).label('max_possible')
        )
        .join(Exam, Attempt.exam_id == Exam.id)
        .join(ClassSection, Exam.class_id == ClassSection.id)
        .join(Response, Response.attempt_id == Attempt.id)
        .join(Question, Response.question_id == Question.id)
        .where(
            and_(
                Attempt.student_id == student_id,
                ClassSection.course_id.in_(course_ids),
                Response.final_score.isnot(None)
            )
        )
        .group_by(Attempt.id, Exam.id)
    )
    
    attempts_data = attempts_result.all()
    
    # Calculate basic statistics
    total_exams = len(set(attempt.exam_id for attempt, _, _, _ in attempts_data))
    completed_exams = len([a for a, _, _, _ in attempts_data if a.status.value in ['submitted', 'auto_submitted']])
    
    scores = []
    for attempt, exam, total_score, max_possible in attempts_data:
        if total_score and max_possible:
            percentage = (total_score / max_possible) * 100
            scores.append(percentage)
    
    average_score = sum(scores) / len(scores) if scores else None
    
    # Calculate CO attainment
    co_attainment = await calculate_student_co_attainment(student_id, course_ids, db)
    
    # Calculate PO attainment
    po_attainment = await calculate_student_po_attainment(student_id, course_ids, db)
    
    # Calculate SGPA/CGPA
    sgpa, cgpa = await calculate_student_gpa(student_id, semester, academic_year, db)
    
    # Identify strengths and weaknesses
    strengths, weaknesses = identify_student_strengths_weaknesses(co_attainment, po_attainment)
    
    # Calculate rank (simplified - within enrolled courses)
    rank = await calculate_student_rank(student_id, course_ids, db)
    
    return StudentAnalytics(
        student_id=student_id,
        student_name=student.name,
        sgpa=sgpa,
        cgpa=cgpa,
        total_exams=total_exams,
        completed_exams=completed_exams,
        average_score=round(average_score, 2) if average_score else None,
        co_attainment=co_attainment,
        po_attainment=po_attainment,
        strengths=strengths,
        weaknesses=weaknesses,
        rank=rank
    )

async def calculate_student_co_attainment(student_id: int, course_ids: List[int], db: AsyncSession) -> Dict[str, float]:
    """Calculate CO attainment for a student"""
    co_attainment = {}
    
    # Get all COs for the courses
    cos_result = await db.execute(
        select(CO).where(CO.course_id.in_(course_ids))
    )
    cos = cos_result.scalars().all()
    
    for co in cos:
        # Get student's responses for questions mapped to this CO
        responses_result = await db.execute(
            select(
                func.avg(Response.final_score / Question.max_marks * 100).label('avg_percentage')
            )
            .join(Question, Response.question_id == Question.id)
            .join(Attempt, Response.attempt_id == Attempt.id)
            .where(
                and_(
                    Attempt.student_id == student_id,
                    Question.co_id == co.id,
                    Response.final_score.isnot(None)
                )
            )
        )
        
        avg_percentage = responses_result.scalar()
        if avg_percentage:
            co_attainment[co.code] = round(avg_percentage, 2)
    
    return co_attainment

async def calculate_student_po_attainment(student_id: int, course_ids: List[int], db: AsyncSession) -> Dict[str, float]:
    """Calculate PO attainment for a student"""
    po_attainment = {}
    
    # Get CO-PO mappings for the courses
    mappings_result = await db.execute(
        select(CO_PO_Map, CO, PO)
        .join(CO, CO_PO_Map.co_id == CO.id)
        .join(PO, CO_PO_Map.po_id == PO.id)
        .where(CO.course_id.in_(course_ids))
    )
    
    mappings = mappings_result.all()
    
    # Group by PO
    po_data = {}
    for mapping, co, po in mappings:
        if po.code not in po_data:
            po_data[po.code] = []
        
        # Get student's CO attainment for this CO
        co_responses_result = await db.execute(
            select(
                func.avg(Response.final_score / Question.max_marks * 100).label('avg_percentage')
            )
            .join(Question, Response.question_id == Question.id)
            .join(Attempt, Response.attempt_id == Attempt.id)
            .where(
                and_(
                    Attempt.student_id == student_id,
                    Question.co_id == co.id,
                    Response.final_score.isnot(None)
                )
            )
        )
        
        co_attainment_value = co_responses_result.scalar()
        if co_attainment_value:
            po_data[po.code].append(co_attainment_value * mapping.weight)
    
    # Calculate weighted PO attainment
    for po_code, values in po_data.items():
        if values:
            po_attainment[po_code] = round(sum(values) / len(values), 2)
    
    return po_attainment

async def calculate_student_gpa(student_id: int, semester: Optional[int], academic_year: Optional[str], db: AsyncSession) -> tuple:
    """Calculate SGPA and CGPA for a student"""
    # This is a simplified implementation
    # In a real system, you'd have proper grade mapping and credit calculations
    
    # Get internal scores for the student
    internal_scores_result = await db.execute(
        select(InternalScore, Course.credits, InternalComponent.weight_percent)
        .join(InternalComponent, InternalScore.component_id == InternalComponent.id)
        .join(Course, InternalScore.course_id == Course.id)
        .where(InternalScore.student_id == student_id)
    )
    
    internal_scores = internal_scores_result.all()
    
    if not internal_scores:
        return None, None
    
    # Calculate weighted scores per course
    course_scores = {}
    course_credits = {}
    
    for score, credits, weight in internal_scores:
        if score.course_id not in course_scores:
            course_scores[score.course_id] = 0
            course_credits[score.course_id] = credits
        
        weighted_score = (score.raw_score / score.max_score) * weight
        course_scores[score.course_id] += weighted_score
    
    # Convert to grade points (simplified 10-point scale)
    def percentage_to_grade_point(percentage):
        if percentage >= 90: return 10
        elif percentage >= 80: return 9
        elif percentage >= 70: return 8
        elif percentage >= 60: return 7
        elif percentage >= 50: return 6
        elif percentage >= 40: return 5
        else: return 0
    
    # Calculate SGPA (current semester)
    total_credits = sum(course_credits.values())
    weighted_grade_points = sum(
        percentage_to_grade_point(score) * course_credits[course_id]
        for course_id, score in course_scores.items()
    )
    
    sgpa = weighted_grade_points / total_credits if total_credits > 0 else None
    cgpa = sgpa  # Simplified - in reality, you'd calculate across all semesters
    
    return round(sgpa, 2) if sgpa else None, round(cgpa, 2) if cgpa else None

def identify_student_strengths_weaknesses(co_attainment: Dict[str, float], po_attainment: Dict[str, float]) -> tuple:
    """Identify student strengths and weaknesses based on CO/PO attainment"""
    strengths = []
    weaknesses = []
    
    # Analyze CO attainment
    for co_code, attainment in co_attainment.items():
        if attainment >= 80:
            strengths.append(f"Strong in {co_code}")
        elif attainment < 60:
            weaknesses.append(f"Needs improvement in {co_code}")
    
    # Analyze PO attainment
    for po_code, attainment in po_attainment.items():
        if attainment >= 80:
            strengths.append(f"Excellent {po_code} skills")
        elif attainment < 60:
            weaknesses.append(f"Develop {po_code} competency")
    
    return strengths[:5], weaknesses[:5]  # Limit to top 5

async def calculate_student_rank(student_id: int, course_ids: List[int], db: AsyncSession) -> Optional[int]:
    """Calculate student rank within their peer group"""
    # Get all students in the same courses
    peer_students_result = await db.execute(
        select(Enrollment.student_id)
        .join(ClassSection, Enrollment.class_id == ClassSection.id)
        .where(ClassSection.course_id.in_(course_ids))
        .distinct()
    )
    
    peer_student_ids = [row[0] for row in peer_students_result.fetchall()]
    
    if len(peer_student_ids) <= 1:
        return 1
    
    # Calculate average scores for all peer students
    student_averages = []
    
    for peer_id in peer_student_ids:
        avg_result = await db.execute(
            select(
                func.avg(Response.final_score / Question.max_marks * 100).label('avg_score')
            )
            .join(Question, Response.question_id == Question.id)
            .join(Attempt, Response.attempt_id == Attempt.id)
            .join(Exam, Attempt.exam_id == Exam.id)
            .join(ClassSection, Exam.class_id == ClassSection.id)
            .where(
                and_(
                    Attempt.student_id == peer_id,
                    ClassSection.course_id.in_(course_ids),
                    Response.final_score.isnot(None)
                )
            )
        )
        
        avg_score = avg_result.scalar()
        if avg_score:
            student_averages.append((peer_id, avg_score))
    
    # Sort by average score (descending)
    student_averages.sort(key=lambda x: x[1], reverse=True)
    
    # Find rank
    for rank, (peer_id, _) in enumerate(student_averages, 1):
        if peer_id == student_id:
            return rank
    
    return None

# ==================== COURSE ANALYTICS ====================

@router.get("/course/{course_id}/analytics", response_model=CourseAnalytics)
async def get_course_analytics(
    course_id: int,
    class_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_class_analytics"))
):
    """Get comprehensive analytics for a course"""
    # Get course details
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get class sections for the course
    classes_query = select(ClassSection).where(ClassSection.course_id == course_id)
    if class_id:
        classes_query = classes_query.where(ClassSection.id == class_id)
    
    classes_result = await db.execute(classes_query)
    class_sections = classes_result.scalars().all()
    class_ids = [cls.id for cls in class_sections]
    
    if not class_ids:
        return CourseAnalytics(
            course_id=course_id,
            course_name=course.title,
            total_students=0
        )
    
    # Get total students
    students_result = await db.execute(
        select(func.count(Enrollment.student_id.distinct()))
        .where(Enrollment.class_id.in_(class_ids))
    )
    total_students = students_result.scalar() or 0
    
    # Calculate average performance
    avg_performance_result = await db.execute(
        select(
            func.avg(Response.final_score / Question.max_marks * 100).label('avg_performance')
        )
        .join(Question, Response.question_id == Question.id)
        .join(Attempt, Response.attempt_id == Attempt.id)
        .join(Exam, Attempt.exam_id == Exam.id)
        .where(
            and_(
                Exam.class_id.in_(class_ids),
                Response.final_score.isnot(None)
            )
        )
    )
    
    average_performance = avg_performance_result.scalar()
    
    # Calculate CO attainment
    co_attainment = await calculate_course_co_attainment(course_id, class_ids, db)
    
    # Calculate PO attainment
    po_attainment = await calculate_course_po_attainment(course_id, class_ids, db)
    
    # Get exam statistics
    exam_statistics = await get_course_exam_statistics(class_ids, db)
    
    # Calculate grade distribution
    grade_distribution = await calculate_grade_distribution(class_ids, db)
    
    return CourseAnalytics(
        course_id=course_id,
        course_name=course.title,
        total_students=total_students,
        average_performance=round(average_performance, 2) if average_performance else None,
        co_attainment=co_attainment,
        po_attainment=po_attainment,
        exam_statistics=exam_statistics,
        grade_distribution=grade_distribution
    )

async def calculate_course_co_attainment(course_id: int, class_ids: List[int], db: AsyncSession) -> Dict[str, Dict[str, float]]:
    """Calculate CO attainment for a course"""
    co_attainment = {}
    
    # Get COs for the course
    cos_result = await db.execute(
        select(CO).where(CO.course_id == course_id)
    )
    cos = cos_result.scalars().all()
    
    for co in cos:
        # Calculate class average for this CO
        avg_result = await db.execute(
            select(
                func.avg(Response.final_score / Question.max_marks * 100).label('class_avg')
            )
            .join(Question, Response.question_id == Question.id)
            .join(Attempt, Response.attempt_id == Attempt.id)
            .join(Exam, Attempt.exam_id == Exam.id)
            .where(
                and_(
                    Exam.class_id.in_(class_ids),
                    Question.co_id == co.id,
                    Response.final_score.isnot(None)
                )
            )
        )
        
        class_avg = avg_result.scalar()
        if class_avg:
            target = 70.0  # Default target
            status = "Achieved" if class_avg >= target else "Not Achieved"
            
            co_attainment[co.code] = {
                "class_avg": round(class_avg, 2),
                "target": target,
                "status": status
            }
    
    return co_attainment

async def calculate_course_po_attainment(course_id: int, class_ids: List[int], db: AsyncSession) -> Dict[str, Dict[str, float]]:
    """Calculate PO attainment for a course"""
    po_attainment = {}
    
    # Get CO-PO mappings for the course
    mappings_result = await db.execute(
        select(CO_PO_Map, CO, PO)
        .join(CO, CO_PO_Map.co_id == CO.id)
        .join(PO, CO_PO_Map.po_id == PO.id)
        .where(CO.course_id == course_id)
    )
    
    mappings = mappings_result.all()
    
    # Group by PO
    po_data = {}
    for mapping, co, po in mappings:
        if po.code not in po_data:
            po_data[po.code] = []
        
        # Get class average for this CO
        co_avg_result = await db.execute(
            select(
                func.avg(Response.final_score / Question.max_marks * 100).label('co_avg')
            )
            .join(Question, Response.question_id == Question.id)
            .join(Attempt, Response.attempt_id == Attempt.id)
            .join(Exam, Attempt.exam_id == Exam.id)
            .where(
                and_(
                    Exam.class_id.in_(class_ids),
                    Question.co_id == co.id,
                    Response.final_score.isnot(None)
                )
            )
        )
        
        co_avg = co_avg_result.scalar()
        if co_avg:
            po_data[po.code].append(co_avg * mapping.weight)
    
    # Calculate weighted PO attainment
    for po_code, values in po_data.items():
        if values:
            class_avg = sum(values) / len(values)
            target = 70.0  # Default target
            status = "Achieved" if class_avg >= target else "Not Achieved"
            
            po_attainment[po_code] = {
                "class_avg": round(class_avg, 2),
                "target": target,
                "status": status
            }
    
    return po_attainment

async def get_course_exam_statistics(class_ids: List[int], db: AsyncSession) -> List[Dict[str, Any]]:
    """Get exam statistics for a course"""
    exams_result = await db.execute(
        select(
            Exam.id,
            Exam.title,
            func.count(Attempt.id).label('total_attempts'),
            func.avg(Response.final_score / Question.max_marks * 100).label('avg_score'),
            func.max(Response.final_score / Question.max_marks * 100).label('max_score'),
            func.min(Response.final_score / Question.max_marks * 100).label('min_score')
        )
        .outerjoin(Attempt, Exam.id == Attempt.exam_id)
        .outerjoin(Response, Response.attempt_id == Attempt.id)
        .outerjoin(Question, Response.question_id == Question.id)
        .where(Exam.class_id.in_(class_ids))
        .group_by(Exam.id, Exam.title)
    )
    
    exam_stats = []
    for exam_id, title, attempts, avg_score, max_score, min_score in exams_result.all():
        exam_stats.append({
            "exam_id": exam_id,
            "title": title,
            "total_attempts": attempts or 0,
            "average_score": round(avg_score, 2) if avg_score else None,
            "highest_score": round(max_score, 2) if max_score else None,
            "lowest_score": round(min_score, 2) if min_score else None
        })
    
    return exam_stats

async def calculate_grade_distribution(class_ids: List[int], db: AsyncSession) -> Dict[str, int]:
    """Calculate grade distribution for a course"""
    # Get all final scores
    scores_result = await db.execute(
        select(Response.final_score / Question.max_marks * 100)
        .join(Question, Response.question_id == Question.id)
        .join(Attempt, Response.attempt_id == Attempt.id)
        .join(Exam, Attempt.exam_id == Exam.id)
        .where(
            and_(
                Exam.class_id.in_(class_ids),
                Response.final_score.isnot(None)
            )
        )
    )
    
    scores = [score[0] for score in scores_result.all()]
    
    # Categorize scores
    grade_distribution = {
        "A+ (90-100)": 0,
        "A (80-89)": 0,
        "B+ (70-79)": 0,
        "B (60-69)": 0,
        "C+ (50-59)": 0,
        "C (40-49)": 0,
        "F (0-39)": 0
    }
    
    for score in scores:
        if score >= 90:
            grade_distribution["A+ (90-100)"] += 1
        elif score >= 80:
            grade_distribution["A (80-89)"] += 1
        elif score >= 70:
            grade_distribution["B+ (70-79)"] += 1
        elif score >= 60:
            grade_distribution["B (60-69)"] += 1
        elif score >= 50:
            grade_distribution["C+ (50-59)"] += 1
        elif score >= 40:
            grade_distribution["C (40-49)"] += 1
        else:
            grade_distribution["F (0-39)"] += 1
    
    return grade_distribution

# ==================== SYSTEM ANALYTICS ====================

@router.get("/system/analytics", response_model=SystemAnalytics)
async def get_system_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_all_analytics"))
):
    """Get system-wide analytics"""
    # Get user counts
    users_result = await db.execute(
        select(
            func.count(User.id).label('total'),
            func.sum(func.case((User.role == 'student', 1), else_=0)).label('students'),
            func.sum(func.case((User.is_active == True, 1), else_=0)).label('active')
        )
    )
    
    user_stats = users_result.first()
    
    # Get course count
    courses_result = await db.execute(select(func.count(Course.id)))
    total_courses = courses_result.scalar()
    
    # Get exam counts
    exams_result = await db.execute(
        select(
            func.count(Exam.id).label('total'),
            func.sum(func.case((Exam.status == 'ended', 1), else_=0)).label('completed')
        )
    )
    
    exam_stats = exams_result.first()
    
    # Get grading statistics
    grading_result = await db.execute(
        select(
            func.sum(func.case((Response.ai_score.isnot(None), 1), else_=0)).label('ai_graded'),
            func.sum(func.case((Response.teacher_score.isnot(None), 1), else_=0)).label('teacher_graded')
        )
    )
    
    grading_stats = grading_result.first()
    
    return SystemAnalytics(
        total_users=user_stats.total or 0,
        active_students=user_stats.students or 0,
        total_courses=total_courses or 0,
        total_exams=exam_stats.total or 0,
        completed_exams=exam_stats.completed or 0,
        ai_graded_responses=grading_stats.ai_graded or 0,
        teacher_graded_responses=grading_stats.teacher_graded or 0,
        system_utilization={
            "active_users_percentage": round((user_stats.active / user_stats.total * 100), 2) if user_stats.total else 0,
            "exam_completion_rate": round((exam_stats.completed / exam_stats.total * 100), 2) if exam_stats.total else 0
        }
    )

# ==================== EXPORT FUNCTIONS ====================

@router.get("/student/{student_id}/export")
async def export_student_report(
    student_id: int,
    format: str = Query("pdf", regex="^(pdf|csv|xlsx)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export student analytics report"""
    # Check permissions
    if current_user.role.value == "student" and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only export your own report"
        )
    
    # Get student analytics
    analytics = await get_student_analytics(student_id, None, None, db, current_user)
    
    if format == "csv":
        # Create CSV
        df = pd.DataFrame([{
            "Student ID": analytics.student_id,
            "Student Name": analytics.student_name,
            "SGPA": analytics.sgpa,
            "CGPA": analytics.cgpa,
            "Total Exams": analytics.total_exams,
            "Completed Exams": analytics.completed_exams,
            "Average Score": analytics.average_score,
            "Rank": analytics.rank
        }])
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        return FastAPIResponse(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=student_{student_id}_report.csv"}
        )
    
    elif format == "xlsx":
        # Create Excel file
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Basic info sheet
            basic_df = pd.DataFrame([{
                "Student ID": analytics.student_id,
                "Student Name": analytics.student_name,
                "SGPA": analytics.sgpa,
                "CGPA": analytics.cgpa,
                "Total Exams": analytics.total_exams,
                "Completed Exams": analytics.completed_exams,
                "Average Score": analytics.average_score,
                "Rank": analytics.rank
            }])
            basic_df.to_excel(writer, sheet_name="Basic Info", index=False)
            
            # CO attainment sheet
            if analytics.co_attainment:
                co_df = pd.DataFrame([
                    {"CO": co, "Attainment": attainment}
                    for co, attainment in analytics.co_attainment.items()
                ])
                co_df.to_excel(writer, sheet_name="CO Attainment", index=False)
            
            # PO attainment sheet
            if analytics.po_attainment:
                po_df = pd.DataFrame([
                    {"PO": po, "Attainment": attainment}
                    for po, attainment in analytics.po_attainment.items()
                ])
                po_df.to_excel(writer, sheet_name="PO Attainment", index=False)
        
        excel_content = excel_buffer.getvalue()
        
        return FastAPIResponse(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=student_{student_id}_report.xlsx"}
        )
    
    else:  # PDF format
        # For PDF generation, you would typically use a library like reportlab or weasyprint
        # For now, return a placeholder
        return CommonResponse(message="PDF export not yet implemented")

@router.get("/course/{course_id}/export")
async def export_course_report(
    course_id: int,
    format: str = Query("pdf", regex="^(pdf|csv|xlsx)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_class_analytics"))
):
    """Export course analytics report"""
    # Get course analytics
    analytics = await get_course_analytics(course_id, None, db, current_user)
    
    if format == "csv":
        # Create CSV with course summary
        summary_data = [{
            "Course ID": analytics.course_id,
            "Course Name": analytics.course_name,
            "Total Students": analytics.total_students,
            "Average Performance": analytics.average_performance
        }]
        
        df = pd.DataFrame(summary_data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        return FastAPIResponse(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=course_{course_id}_report.csv"}
        )
    
    # Similar implementation for xlsx and pdf...
    return CommonResponse(message=f"{format.upper()} export for course reports not yet implemented")