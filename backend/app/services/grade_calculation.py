from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from ..models.models import (
    User, Course, ClassSection, Enrollment, InternalComponent, InternalScore,
    Exam, Attempt, Response, Question
)

logger = logging.getLogger(__name__)

class GradeCalculationService:
    """Service for calculating grades, SGPA, and CGPA"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_internal_marks(self, student_id: int, course_id: int) -> Dict[str, Any]:
        """Calculate internal marks for a student in a course"""
        
        # Get internal components and their weights
        components_result = await self.db.execute(
            select(InternalComponent).where(InternalComponent.course_id == course_id)
        )
        components = components_result.scalars().all()
        
        if not components:
            return {
                "student_id": student_id,
                "course_id": course_id,
                "total_internal_percentage": 0.0,
                "components": [],
                "grade": "F"
            }
        
        # Get student's scores for each component
        total_weighted_percentage = 0.0
        component_details = []
        
        for component in components:
            score_result = await self.db.execute(
                select(InternalScore).where(
                    InternalScore.student_id == student_id,
                    InternalScore.component_id == component.id
                )
            )
            score = score_result.scalar_one_or_none()
            
            if score:
                percentage = (score.raw_score / score.max_score) * 100
                weighted_percentage = percentage * (component.weight_percent / 100)
            else:
                percentage = 0.0
                weighted_percentage = 0.0
            
            component_details.append({
                "component_name": component.name,
                "weight_percent": component.weight_percent,
                "raw_score": score.raw_score if score else 0,
                "max_score": score.max_score if score else 0,
                "percentage": round(percentage, 2),
                "weighted_percentage": round(weighted_percentage, 2)
            })
            
            total_weighted_percentage += weighted_percentage
        
        grade = self.percentage_to_grade(total_weighted_percentage)
        
        return {
            "student_id": student_id,
            "course_id": course_id,
            "total_internal_percentage": round(total_weighted_percentage, 2),
            "components": component_details,
            "grade": grade
        }
    
    async def calculate_exam_marks(self, student_id: int, exam_id: int) -> Dict[str, Any]:
        """Calculate marks for a student in a specific exam"""
        
        # Get student's attempt
        attempt_result = await self.db.execute(
            select(Attempt).where(
                Attempt.student_id == student_id,
                Attempt.exam_id == exam_id
            )
        )
        attempt = attempt_result.scalar_one_or_none()
        
        if not attempt:
            return {
                "student_id": student_id,
                "exam_id": exam_id,
                "status": "not_attempted",
                "total_marks": 0,
                "max_marks": 0,
                "percentage": 0,
                "grade": "F"
            }
        
        # Get all responses for this attempt
        responses_query = """
            SELECT 
                r.question_id,
                r.final_score,
                q.max_marks,
                q.text as question_text,
                q.type as question_type
            FROM responses r
            JOIN questions q ON r.question_id = q.id
            WHERE r.attempt_id = :attempt_id
        """
        
        result = await self.db.execute(responses_query, {"attempt_id": attempt.id})
        responses = result.fetchall()
        
        total_marks = sum(r.final_score or 0 for r in responses)
        max_marks = sum(r.max_marks for r in responses)
        percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0
        
        question_details = [
            {
                "question_id": r.question_id,
                "question_text": r.question_text[:100] + "..." if len(r.question_text) > 100 else r.question_text,
                "question_type": r.question_type,
                "marks_obtained": r.final_score or 0,
                "max_marks": r.max_marks,
                "percentage": round((r.final_score or 0) / r.max_marks * 100, 2)
            }
            for r in responses
        ]
        
        return {
            "student_id": student_id,
            "exam_id": exam_id,
            "attempt_id": attempt.id,
            "status": attempt.status.value,
            "total_marks": total_marks,
            "max_marks": max_marks,
            "percentage": round(percentage, 2),
            "grade": self.percentage_to_grade(percentage),
            "question_details": question_details,
            "submitted_at": attempt.submitted_at
        }
    
    async def calculate_course_total(self, student_id: int, course_id: int, 
                                   internal_weight: float = 0.3, 
                                   external_weight: float = 0.7) -> Dict[str, Any]:
        """Calculate total course marks (internal + external)"""
        
        # Get internal marks
        internal_data = await self.calculate_internal_marks(student_id, course_id)
        internal_percentage = internal_data["total_internal_percentage"]
        
        # Get external marks (from final exam)
        # For now, we'll use the highest scoring exam as external
        external_query = """
            SELECT 
                e.id as exam_id,
                e.title,
                (SUM(r.final_score) / SUM(q.max_marks)) * 100 as percentage
            FROM exams e
            JOIN attempts a ON e.id = a.exam_id
            JOIN responses r ON a.id = r.attempt_id
            JOIN questions q ON r.question_id = q.id
            JOIN class_sections cs ON e.class_id = cs.id
            WHERE a.student_id = :student_id
            AND cs.course_id = :course_id
            AND a.status IN ('submitted', 'auto_submitted')
            GROUP BY e.id, e.title
            ORDER BY percentage DESC
            LIMIT 1
        """
        
        result = await self.db.execute(external_query, {
            "student_id": student_id,
            "course_id": course_id
        })
        external_data = result.fetchone()
        
        external_percentage = external_data.percentage if external_data else 0
        
        # Calculate weighted total
        total_percentage = (internal_percentage * internal_weight) + (external_percentage * external_weight)
        
        return {
            "student_id": student_id,
            "course_id": course_id,
            "internal_percentage": round(internal_percentage, 2),
            "external_percentage": round(external_percentage, 2),
            "internal_weight": internal_weight,
            "external_weight": external_weight,
            "total_percentage": round(total_percentage, 2),
            "grade": self.percentage_to_grade(total_percentage),
            "grade_point": self.percentage_to_grade_point(total_percentage)
        }
    
    async def calculate_sgpa(self, student_id: int, semester: str, year: int) -> Dict[str, Any]:
        """Calculate SGPA for a student for a specific semester"""
        
        # Get all courses for the semester
        courses_query = """
            SELECT 
                c.id as course_id,
                c.code as course_code,
                c.title as course_title,
                c.credits
            FROM courses c
            JOIN class_sections cs ON c.id = cs.course_id
            JOIN enrollments e ON cs.id = e.class_id
            WHERE e.student_id = :student_id
            AND cs.term = :semester
            AND cs.year = :year
        """
        
        result = await self.db.execute(courses_query, {
            "student_id": student_id,
            "semester": semester,
            "year": year
        })
        courses = result.fetchall()
        
        if not courses:
            return {
                "student_id": student_id,
                "semester": semester,
                "year": year,
                "sgpa": 0.0,
                "total_credits": 0,
                "courses": []
            }
        
        total_grade_points = 0.0
        total_credits = 0.0
        course_details = []
        
        for course in courses:
            # Get course total marks
            course_total = await self.calculate_course_total(student_id, course.course_id)
            grade_point = course_total["grade_point"]
            
            course_grade_points = grade_point * course.credits
            total_grade_points += course_grade_points
            total_credits += course.credits
            
            course_details.append({
                "course_id": course.course_id,
                "course_code": course.course_code,
                "course_title": course.course_title,
                "credits": course.credits,
                "percentage": course_total["total_percentage"],
                "grade": course_total["grade"],
                "grade_point": grade_point
            })
        
        sgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
        
        return {
            "student_id": student_id,
            "semester": semester,
            "year": year,
            "sgpa": round(sgpa, 2),
            "total_credits": total_credits,
            "total_grade_points": round(total_grade_points, 2),
            "courses": course_details
        }
    
    async def calculate_cgpa(self, student_id: int) -> Dict[str, Any]:
        """Calculate CGPA for a student across all semesters"""
        
        # Get all semesters for the student
        semesters_query = """
            SELECT DISTINCT cs.term, cs.year
            FROM class_sections cs
            JOIN enrollments e ON cs.id = e.class_id
            WHERE e.student_id = :student_id
            ORDER BY cs.year, cs.term
        """
        
        result = await self.db.execute(semesters_query, {"student_id": student_id})
        semesters = result.fetchall()
        
        total_grade_points = 0.0
        total_credits = 0.0
        semester_details = []
        
        for sem in semesters:
            sgpa_data = await self.calculate_sgpa(student_id, sem.term, sem.year)
            
            total_grade_points += sgpa_data["total_grade_points"]
            total_credits += sgpa_data["total_credits"]
            
            semester_details.append({
                "semester": sem.term,
                "year": sem.year,
                "sgpa": sgpa_data["sgpa"],
                "credits": sgpa_data["total_credits"],
                "courses_count": len(sgpa_data["courses"])
            })
        
        cgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
        
        return {
            "student_id": student_id,
            "cgpa": round(cgpa, 2),
            "total_credits": total_credits,
            "total_grade_points": round(total_grade_points, 2),
            "semesters": semester_details,
            "calculated_at": datetime.utcnow()
        }
    
    def percentage_to_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade"""
        if percentage >= 90:
            return "O"
        elif percentage >= 80:
            return "A+"
        elif percentage >= 70:
            return "A"
        elif percentage >= 60:
            return "B+"
        elif percentage >= 50:
            return "B"
        elif percentage >= 40:
            return "C"
        else:
            return "F"
    
    def percentage_to_grade_point(self, percentage: float) -> float:
        """Convert percentage to 10-point grade scale"""
        if percentage >= 90:
            return 10.0
        elif percentage >= 80:
            return 9.0
        elif percentage >= 70:
            return 8.0
        elif percentage >= 60:
            return 7.0
        elif percentage >= 50:
            return 6.0
        elif percentage >= 40:
            return 5.0
        else:
            return 0.0
    
    def grade_to_grade_point(self, grade: str) -> float:
        """Convert letter grade to grade point"""
        grade_mapping = {
            "O": 10.0,
            "A+": 9.0,
            "A": 8.0,
            "B+": 7.0,
            "B": 6.0,
            "C": 5.0,
            "F": 0.0
        }
        return grade_mapping.get(grade, 0.0)