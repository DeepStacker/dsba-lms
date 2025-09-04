from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging

from ..models.models import (
    User, Program, Course, CO, PO, CO_PO_Map, ClassSection, 
    Exam, Attempt, Response, Question, Enrollment
)

logger = logging.getLogger(__name__)

class ReportsService:
    """Service for generating various reports"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_co_po_attainment_report(self, program_id: int, 
                                             academic_year: Optional[int] = None) -> Dict[str, Any]:
        """Generate comprehensive CO-PO attainment report for accreditation"""
        
        # Get program details
        program_result = await self.db.execute(select(Program).where(Program.id == program_id))
        program = program_result.scalar_one_or_none()
        
        if not program:
            raise ValueError("Program not found")
        
        # Base query for CO-PO data
        base_query = """
            SELECT 
                c.code as course_code,
                c.title as course_title,
                c.credits,
                co.code as co_code,
                co.title as co_title,
                po.code as po_code,
                po.title as po_title,
                cpm.weight,
                COUNT(DISTINCT a.student_id) as students_assessed,
                AVG(r.final_score / q.max_marks) as avg_attainment,
                COUNT(r.id) as total_assessments,
                cs.year as academic_year
            FROM courses c
            JOIN cos co ON c.id = co.course_id
            JOIN co_po_maps cpm ON co.id = cpm.co_id
            JOIN pos po ON cpm.po_id = po.id
            JOIN class_sections cs ON c.id = cs.course_id
            LEFT JOIN exams e ON cs.id = e.class_id
            LEFT JOIN attempts a ON e.id = a.exam_id
            LEFT JOIN responses r ON a.id = r.attempt_id
            LEFT JOIN questions q ON r.question_id = q.id AND q.co_id = co.id
            WHERE c.program_id = :program_id
        """
        
        params = {"program_id": program_id}
        
        if academic_year:
            base_query += " AND cs.year = :academic_year"
            params["academic_year"] = academic_year
        
        base_query += """
            GROUP BY c.id, c.code, c.title, c.credits, co.id, co.code, co.title, 
                     po.id, po.code, po.title, cpm.weight, cs.year
            ORDER BY c.code, co.code, po.code
        """
        
        result = await self.db.execute(base_query, params)
        raw_data = result.fetchall()
        
        # Process data into structured format
        courses = {}
        pos_summary = {}
        
        for row in raw_data:
            course_key = f"{row.course_code}"
            
            if course_key not in courses:
                courses[course_key] = {
                    "course_code": row.course_code,
                    "course_title": row.course_title,
                    "credits": row.credits,
                    "cos": {},
                    "academic_year": row.academic_year
                }
            
            co_key = row.co_code
            if co_key not in courses[course_key]["cos"]:
                courses[course_key]["cos"][co_key] = {
                    "co_code": row.co_code,
                    "co_title": row.co_title,
                    "attainment_percentage": round((row.avg_attainment or 0) * 100, 2),
                    "students_assessed": row.students_assessed or 0,
                    "po_mappings": []
                }
            
            # Add PO mapping
            courses[course_key]["cos"][co_key]["po_mappings"].append({
                "po_code": row.po_code,
                "po_title": row.po_title,
                "weight": row.weight,
                "contribution": round((row.avg_attainment or 0) * row.weight * 100, 2)
            })
            
            # Aggregate PO summary
            if row.po_code not in pos_summary:
                pos_summary[row.po_code] = {
                    "po_code": row.po_code,
                    "po_title": row.po_title,
                    "total_contribution": 0,
                    "contributing_courses": set(),
                    "total_weight": 0
                }
            
            pos_summary[row.po_code]["total_contribution"] += (row.avg_attainment or 0) * row.weight
            pos_summary[row.po_code]["contributing_courses"].add(row.course_code)
            pos_summary[row.po_code]["total_weight"] += row.weight
        
        # Calculate final PO attainments
        for po_code, po_data in pos_summary.items():
            if po_data["total_weight"] > 0:
                po_data["attainment_percentage"] = round(
                    (po_data["total_contribution"] / po_data["total_weight"]) * 100, 2
                )
            else:
                po_data["attainment_percentage"] = 0
            po_data["contributing_courses"] = list(po_data["contributing_courses"])
        
        return {
            "program": {
                "id": program.id,
                "name": program.name,
                "year": program.year
            },
            "academic_year": academic_year,
            "courses": list(courses.values()),
            "po_summary": list(pos_summary.values()),
            "overall_attainment": round(
                sum(po["attainment_percentage"] for po in pos_summary.values()) / len(pos_summary) 
                if pos_summary else 0, 2
            ),
            "generated_at": datetime.utcnow(),
            "total_courses": len(courses),
            "total_pos": len(pos_summary)
        }
    
    async def generate_student_transcript(self, student_id: int) -> Dict[str, Any]:
        """Generate official transcript for a student"""
        
        # Get student details
        student_result = await self.db.execute(select(User).where(User.id == student_id))
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise ValueError("Student not found")
        
        # Get semester-wise performance
        transcript_query = """
            SELECT 
                cs.year,
                cs.term,
                c.code as course_code,
                c.title as course_title,
                c.credits,
                -- Calculate total percentage (internal + external)
                COALESCE(
                    (SELECT AVG(
                        (SUM(r.final_score) / SUM(q.max_marks)) * 100
                    ) FROM attempts a2
                    JOIN responses r ON a2.id = r.attempt_id
                    JOIN questions q ON r.question_id = q.id
                    JOIN exams e2 ON a2.exam_id = e2.id
                    WHERE a2.student_id = en.student_id
                    AND e2.class_id = cs.id
                    AND a2.status IN ('submitted', 'auto_submitted')
                    ), 0
                ) as exam_percentage,
                -- Internal marks
                COALESCE(
                    (SELECT SUM(
                        (ins.raw_score / ins.max_score) * ic.weight_percent / 100.0
                    ) FROM internal_scores ins
                    JOIN internal_components ic ON ins.component_id = ic.id
                    WHERE ins.student_id = en.student_id 
                    AND ic.course_id = c.id), 0
                ) * 100 as internal_percentage
            FROM enrollments en
            JOIN class_sections cs ON en.class_id = cs.id
            JOIN courses c ON cs.course_id = c.id
            WHERE en.student_id = :student_id
            ORDER BY cs.year, cs.term, c.code
        """
        
        result = await self.db.execute(transcript_query, {"student_id": student_id})
        course_records = result.fetchall()
        
        # Process into semester groups
        semesters = {}
        total_credits = 0
        total_grade_points = 0
        
        for record in course_records:
            semester_key = f"{record.year}-{record.term}"
            
            if semester_key not in semesters:
                semesters[semester_key] = {
                    "year": record.year,
                    "term": record.term,
                    "courses": [],
                    "semester_credits": 0,
                    "semester_grade_points": 0
                }
            
            # Calculate final percentage (weighted average of internal and external)
            # Assuming 30% internal, 70% external
            final_percentage = (record.internal_percentage * 0.3) + (record.exam_percentage * 0.7)
            grade = self._percentage_to_grade(final_percentage)
            grade_point = self._percentage_to_grade_point(final_percentage)
            
            course_grade_points = grade_point * record.credits
            
            semesters[semester_key]["courses"].append({
                "course_code": record.course_code,
                "course_title": record.course_title,
                "credits": record.credits,
                "internal_percentage": round(record.internal_percentage, 2),
                "exam_percentage": round(record.exam_percentage, 2),
                "final_percentage": round(final_percentage, 2),
                "grade": grade,
                "grade_point": grade_point
            })
            
            semesters[semester_key]["semester_credits"] += record.credits
            semesters[semester_key]["semester_grade_points"] += course_grade_points
            
            total_credits += record.credits
            total_grade_points += course_grade_points
        
        # Calculate SGPA for each semester
        for semester_data in semesters.values():
            if semester_data["semester_credits"] > 0:
                semester_data["sgpa"] = round(
                    semester_data["semester_grade_points"] / semester_data["semester_credits"], 2
                )
            else:
                semester_data["sgpa"] = 0.0
        
        # Calculate overall CGPA
        cgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0.0
        
        return {
            "student": {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "username": student.username,
                "department": student.department
            },
            "academic_record": {
                "semesters": list(semesters.values()),
                "overall": {
                    "total_credits": total_credits,
                    "cgpa": cgpa,
                    "total_semesters": len(semesters),
                    "classification": self._get_classification(cgpa)
                }
            },
            "generated_at": datetime.utcnow(),
            "is_official": True
        }
    
    async def generate_class_performance_report(self, class_id: int) -> Dict[str, Any]:
        """Generate detailed performance report for a class"""
        
        # Get class details
        class_result = await self.db.execute(
            select(ClassSection).where(ClassSection.id == class_id)
        )
        class_section = class_result.scalar_one_or_none()
        
        if not class_section:
            raise ValueError("Class section not found")
        
        # Get course details
        course_result = await self.db.execute(
            select(Course).where(Course.id == class_section.course_id)
        )
        course = course_result.scalar_one_or_none()
        
        # Student performance summary
        performance_query = """
            SELECT 
                u.id as student_id,
                u.name as student_name,
                u.username,
                COUNT(DISTINCT e.id) as total_exams,
                COUNT(DISTINCT CASE WHEN a.status IN ('submitted', 'auto_submitted') THEN e.id END) as attempted_exams,
                AVG(
                    CASE WHEN a.status IN ('submitted', 'auto_submitted') 
                    THEN (
                        SELECT SUM(r.final_score) / SUM(q.max_marks) * 100
                        FROM responses r
                        JOIN questions q ON r.question_id = q.id
                        WHERE r.attempt_id = a.id
                    ) END
                ) as avg_exam_percentage,
                -- Internal marks
                COALESCE(
                    (SELECT SUM(
                        (ins.raw_score / ins.max_score) * ic.weight_percent / 100.0
                    ) FROM internal_scores ins
                    JOIN internal_components ic ON ins.component_id = ic.id
                    WHERE ins.student_id = u.id 
                    AND ic.course_id = :course_id), 0
                ) * 100 as internal_percentage,
                RANK() OVER (ORDER BY AVG(
                    CASE WHEN a.status IN ('submitted', 'auto_submitted') 
                    THEN (
                        SELECT SUM(r.final_score) / SUM(q.max_marks) * 100
                        FROM responses r
                        JOIN questions q ON r.question_id = q.id
                        WHERE r.attempt_id = a.id
                    ) END
                ) DESC) as rank
            FROM users u
            JOIN enrollments en ON u.id = en.student_id
            LEFT JOIN exams e ON en.class_id = e.class_id
            LEFT JOIN attempts a ON e.id = a.exam_id AND a.student_id = u.id
            WHERE en.class_id = :class_id
            AND u.role = 'student'
            GROUP BY u.id, u.name, u.username
            ORDER BY rank
        """
        
        result = await self.db.execute(performance_query, {
            "class_id": class_id,
            "course_id": class_section.course_id
        })
        student_performance = result.fetchall()
        
        # Calculate statistics
        exam_percentages = [s.avg_exam_percentage for s in student_performance if s.avg_exam_percentage is not None]
        internal_percentages = [s.internal_percentage for s in student_performance if s.internal_percentage is not None]
        
        statistics = {
            "total_students": len(student_performance),
            "exam_stats": {
                "average": round(sum(exam_percentages) / len(exam_percentages), 2) if exam_percentages else 0,
                "highest": round(max(exam_percentages), 2) if exam_percentages else 0,
                "lowest": round(min(exam_percentages), 2) if exam_percentages else 0,
                "pass_count": len([p for p in exam_percentages if p >= 40]),
                "pass_percentage": round(len([p for p in exam_percentages if p >= 40]) / len(exam_percentages) * 100, 2) if exam_percentages else 0
            },
            "internal_stats": {
                "average": round(sum(internal_percentages) / len(internal_percentages), 2) if internal_percentages else 0,
                "highest": round(max(internal_percentages), 2) if internal_percentages else 0,
                "lowest": round(min(internal_percentages), 2) if internal_percentages else 0
            }
        }
        
        return {
            "class_section": {
                "id": class_section.id,
                "name": class_section.name,
                "term": class_section.term,
                "year": class_section.year
            },
            "course": {
                "code": course.code,
                "title": course.title,
                "credits": course.credits
            } if course else None,
            "statistics": statistics,
            "student_performance": [
                {
                    "student_id": s.student_id,
                    "student_name": s.student_name,
                    "username": s.username,
                    "total_exams": s.total_exams or 0,
                    "attempted_exams": s.attempted_exams or 0,
                    "attendance_rate": round((s.attempted_exams or 0) / (s.total_exams or 1) * 100, 2),
                    "avg_exam_percentage": round(s.avg_exam_percentage or 0, 2),
                    "internal_percentage": round(s.internal_percentage or 0, 2),
                    "overall_percentage": round(((s.avg_exam_percentage or 0) * 0.7) + ((s.internal_percentage or 0) * 0.3), 2),
                    "grade": self._percentage_to_grade(((s.avg_exam_percentage or 0) * 0.7) + ((s.internal_percentage or 0) * 0.3)),
                    "rank": s.rank
                }
                for s in student_performance
            ],
            "generated_at": datetime.utcnow()
        }
    
    def _percentage_to_grade(self, percentage: float) -> str:
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
    
    def _percentage_to_grade_point(self, percentage: float) -> float:
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
    
    def _get_classification(self, cgpa: float) -> str:
        """Get degree classification based on CGPA"""
        if cgpa >= 9.0:
            return "First Class with Distinction"
        elif cgpa >= 7.5:
            return "First Class"
        elif cgpa >= 6.0:
            return "Second Class"
        elif cgpa >= 4.0:
            return "Pass Class"
        else:
            return "Fail"