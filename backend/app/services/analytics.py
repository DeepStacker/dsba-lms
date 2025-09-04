from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from ..models.models import (
    User, Course, CO, PO, CO_PO_Map, Exam, Attempt, Response, 
    Question, ClassSection, Enrollment, InternalScore, InternalComponent
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for generating analytics and insights"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_student_performance_summary(self, student_id: int, course_id: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive performance summary for a student"""
        
        base_query = """
            SELECT 
                c.id as course_id,
                c.code as course_code,
                c.title as course_title,
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
                ) as avg_percentage,
                COUNT(DISTINCT co.id) as total_cos,
                AVG(
                    CASE WHEN r.final_score IS NOT NULL 
                    THEN r.final_score / q.max_marks 
                    END
                ) as avg_co_attainment
            FROM courses c
            JOIN class_sections cs ON c.id = cs.course_id
            JOIN enrollments en ON cs.id = en.class_id
            LEFT JOIN exams e ON cs.id = e.class_id
            LEFT JOIN attempts a ON e.id = a.exam_id AND a.student_id = en.student_id
            LEFT JOIN responses r ON a.id = r.attempt_id
            LEFT JOIN questions q ON r.question_id = q.id
            LEFT JOIN cos co ON q.co_id = co.id
            WHERE en.student_id = :student_id
        """
        
        params = {"student_id": student_id}
        
        if course_id:
            base_query += " AND c.id = :course_id"
            params["course_id"] = course_id
        
        base_query += " GROUP BY c.id, c.code, c.title ORDER BY c.code"
        
        result = await self.db.execute(base_query, params)
        course_performance = result.fetchall()
        
        # Get CO-wise performance
        co_query = """
            SELECT 
                co.code as co_code,
                co.title as co_title,
                c.code as course_code,
                AVG(r.final_score / q.max_marks) as attainment_ratio,
                COUNT(r.id) as total_assessments
            FROM responses r
            JOIN attempts a ON r.attempt_id = a.id
            JOIN questions q ON r.question_id = q.id
            JOIN cos co ON q.co_id = co.id
            JOIN courses c ON co.course_id = c.id
            WHERE a.student_id = :student_id
        """
        
        if course_id:
            co_query += " AND c.id = :course_id"
        
        co_query += " GROUP BY co.id, co.code, co.title, c.code ORDER BY c.code, co.code"
        
        co_result = await self.db.execute(co_query, params)
        co_performance = co_result.fetchall()
        
        return {
            "student_id": student_id,
            "course_performance": [
                {
                    "course_id": row.course_id,
                    "course_code": row.course_code,
                    "course_title": row.course_title,
                    "total_exams": row.total_exams or 0,
                    "attempted_exams": row.attempted_exams or 0,
                    "avg_percentage": round(row.avg_percentage or 0, 2),
                    "total_cos": row.total_cos or 0,
                    "avg_co_attainment": round((row.avg_co_attainment or 0) * 100, 2)
                }
                for row in course_performance
            ],
            "co_performance": [
                {
                    "co_code": row.co_code,
                    "co_title": row.co_title,
                    "course_code": row.course_code,
                    "attainment_percentage": round((row.attainment_ratio or 0) * 100, 2),
                    "total_assessments": row.total_assessments
                }
                for row in co_performance
            ],
            "generated_at": datetime.utcnow()
        }
    
    async def get_class_performance_analytics(self, class_id: int) -> Dict[str, Any]:
        """Get comprehensive analytics for a class"""
        
        # Basic class stats
        stats_query = """
            SELECT 
                COUNT(DISTINCT en.student_id) as total_students,
                COUNT(DISTINCT e.id) as total_exams,
                COUNT(DISTINCT a.id) as total_attempts,
                COUNT(DISTINCT CASE WHEN a.status IN ('submitted', 'auto_submitted') THEN a.id END) as completed_attempts,
                AVG(
                    CASE WHEN a.status IN ('submitted', 'auto_submitted') 
                    THEN (
                        SELECT SUM(r.final_score) / SUM(q.max_marks) * 100
                        FROM responses r
                        JOIN questions q ON r.question_id = q.id
                        WHERE r.attempt_id = a.id
                    ) END
                ) as class_avg_percentage
            FROM class_sections cs
            JOIN enrollments en ON cs.id = en.class_id
            LEFT JOIN exams e ON cs.id = e.class_id
            LEFT JOIN attempts a ON e.id = a.exam_id
            WHERE cs.id = :class_id
        """
        
        result = await self.db.execute(stats_query, {"class_id": class_id})
        stats = result.fetchone()
        
        # Student performance distribution
        distribution_query = """
            SELECT 
                u.id as student_id,
                u.name as student_name,
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
                ) as avg_percentage,
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
            GROUP BY u.id, u.name
            ORDER BY rank
        """
        
        dist_result = await self.db.execute(distribution_query, {"class_id": class_id})
        student_performance = dist_result.fetchall()
        
        # CO attainment for the class
        co_query = """
            SELECT 
                co.code as co_code,
                co.title as co_title,
                COUNT(DISTINCT a.student_id) as students_assessed,
                AVG(r.final_score / q.max_marks) as avg_attainment,
                COUNT(r.id) as total_responses
            FROM responses r
            JOIN attempts a ON r.attempt_id = a.id
            JOIN exams e ON a.exam_id = e.id
            JOIN questions q ON r.question_id = q.id
            JOIN cos co ON q.co_id = co.id
            WHERE e.class_id = :class_id
            GROUP BY co.id, co.code, co.title
            ORDER BY co.code
        """
        
        co_result = await self.db.execute(co_query, {"class_id": class_id})
        co_attainment = co_result.fetchall()
        
        return {
            "class_id": class_id,
            "overall_stats": {
                "total_students": stats.total_students or 0,
                "total_exams": stats.total_exams or 0,
                "total_attempts": stats.total_attempts or 0,
                "completed_attempts": stats.completed_attempts or 0,
                "completion_rate": round(((stats.completed_attempts or 0) / (stats.total_attempts or 1)) * 100, 2),
                "class_avg_percentage": round(stats.class_avg_percentage or 0, 2)
            },
            "student_performance": [
                {
                    "student_id": row.student_id,
                    "student_name": row.student_name,
                    "total_exams": row.total_exams or 0,
                    "attempted_exams": row.attempted_exams or 0,
                    "avg_percentage": round(row.avg_percentage or 0, 2),
                    "rank": row.rank
                }
                for row in student_performance
            ],
            "co_attainment": [
                {
                    "co_code": row.co_code,
                    "co_title": row.co_title,
                    "students_assessed": row.students_assessed,
                    "attainment_percentage": round((row.avg_attainment or 0) * 100, 2),
                    "total_responses": row.total_responses
                }
                for row in co_attainment
            ],
            "generated_at": datetime.utcnow()
        }
    
    async def get_exam_item_analysis(self, exam_id: int) -> Dict[str, Any]:
        """Get item analysis for an exam (difficulty, discrimination, etc.)"""
        
        # Question-wise statistics
        question_query = """
            SELECT 
                q.id as question_id,
                q.text as question_text,
                q.type as question_type,
                q.max_marks,
                COUNT(r.id) as total_responses,
                AVG(r.final_score / q.max_marks) as difficulty_index,
                COUNT(CASE WHEN r.final_score >= (q.max_marks * 0.6) THEN 1 END) as correct_responses,
                AVG(CASE WHEN r.final_score IS NOT NULL THEN 
                    (SELECT AVG(time_spent) FROM (
                        SELECT EXTRACT(EPOCH FROM (r2.updated_at - r2.created_at)) as time_spent
                        FROM responses r2 
                        WHERE r2.question_id = q.id 
                        AND r2.attempt_id IN (
                            SELECT id FROM attempts WHERE exam_id = :exam_id
                        )
                    ) t)
                END) as avg_time_spent
            FROM questions q
            JOIN exam_questions eq ON q.id = eq.question_id
            LEFT JOIN responses r ON q.id = r.question_id
            LEFT JOIN attempts a ON r.attempt_id = a.id AND a.exam_id = :exam_id
            WHERE eq.exam_id = :exam_id
            GROUP BY q.id, q.text, q.type, q.max_marks, eq.order
            ORDER BY eq.order
        """
        
        result = await self.db.execute(question_query, {"exam_id": exam_id})
        questions = result.fetchall()
        
        # Calculate discrimination index for each question
        question_analysis = []
        for q in questions:
            # Get top 27% and bottom 27% performers for discrimination calculation
            discrimination_query = """
                WITH student_totals AS (
                    SELECT 
                        a.student_id,
                        SUM(r.final_score) as total_score,
                        PERCENT_RANK() OVER (ORDER BY SUM(r.final_score)) as percentile
                    FROM attempts a
                    JOIN responses r ON a.id = r.attempt_id
                    WHERE a.exam_id = :exam_id
                    GROUP BY a.student_id
                ),
                top_bottom AS (
                    SELECT student_id, 
                           CASE 
                               WHEN percentile >= 0.73 THEN 'top'
                               WHEN percentile <= 0.27 THEN 'bottom'
                               ELSE 'middle'
                           END as group_type
                    FROM student_totals
                )
                SELECT 
                    tb.group_type,
                    AVG(r.final_score / :max_marks) as avg_score
                FROM responses r
                JOIN attempts a ON r.attempt_id = a.id
                JOIN top_bottom tb ON a.student_id = tb.student_id
                WHERE r.question_id = :question_id
                AND a.exam_id = :exam_id
                AND tb.group_type IN ('top', 'bottom')
                GROUP BY tb.group_type
            """
            
            disc_result = await self.db.execute(discrimination_query, {
                "exam_id": exam_id,
                "question_id": q.question_id,
                "max_marks": q.max_marks
            })
            disc_data = {row.group_type: row.avg_score for row in disc_result.fetchall()}
            
            discrimination_index = (disc_data.get('top', 0) - disc_data.get('bottom', 0))
            
            question_analysis.append({
                "question_id": q.question_id,
                "question_text": q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
                "question_type": q.question_type,
                "max_marks": q.max_marks,
                "total_responses": q.total_responses or 0,
                "difficulty_index": round(q.difficulty_index or 0, 3),
                "discrimination_index": round(discrimination_index, 3),
                "correct_responses": q.correct_responses or 0,
                "success_rate": round(((q.correct_responses or 0) / (q.total_responses or 1)) * 100, 2),
                "avg_time_spent": round(q.avg_time_spent or 0, 1)
            })
        
        return {
            "exam_id": exam_id,
            "question_analysis": question_analysis,
            "summary": {
                "total_questions": len(questions),
                "avg_difficulty": round(sum(q["difficulty_index"] for q in question_analysis) / len(question_analysis), 3) if question_analysis else 0,
                "avg_discrimination": round(sum(q["discrimination_index"] for q in question_analysis) / len(question_analysis), 3) if question_analysis else 0,
                "questions_needing_review": len([q for q in question_analysis if q["discrimination_index"] < 0.2 or q["difficulty_index"] < 0.3 or q["difficulty_index"] > 0.9])
            },
            "generated_at": datetime.utcnow()
        }
    
    async def predict_at_risk_students(self, class_id: int, threshold: float = 0.4) -> List[Dict[str, Any]]:
        """Predict students at risk of failing based on performance patterns"""
        
        query = """
            SELECT 
                u.id as student_id,
                u.name as student_name,
                u.email,
                COUNT(DISTINCT e.id) as total_exams,
                COUNT(DISTINCT CASE WHEN a.status IN ('submitted', 'auto_submitted') THEN e.id END) as attempted_exams,
                AVG(
                    CASE WHEN a.status IN ('submitted', 'auto_submitted') 
                    THEN (
                        SELECT SUM(r.final_score) / SUM(q.max_marks)
                        FROM responses r
                        JOIN questions q ON r.question_id = q.id
                        WHERE r.attempt_id = a.id
                    ) END
                ) as avg_performance,
                COUNT(DISTINCT CASE WHEN a.status = 'not_started' THEN e.id END) as missed_exams,
                -- Calculate trend (recent performance vs overall)
                AVG(
                    CASE WHEN e.start_at >= (CURRENT_DATE - INTERVAL '30 days')
                    AND a.status IN ('submitted', 'auto_submitted') 
                    THEN (
                        SELECT SUM(r.final_score) / SUM(q.max_marks)
                        FROM responses r
                        JOIN questions q ON r.question_id = q.id
                        WHERE r.attempt_id = a.id
                    ) END
                ) as recent_performance
            FROM users u
            JOIN enrollments en ON u.id = en.student_id
            LEFT JOIN exams e ON en.class_id = e.class_id
            LEFT JOIN attempts a ON e.id = a.exam_id AND a.student_id = u.id
            WHERE en.class_id = :class_id
            AND u.role = 'student'
            GROUP BY u.id, u.name, u.email
            HAVING AVG(
                CASE WHEN a.status IN ('submitted', 'auto_submitted') 
                THEN (
                    SELECT SUM(r.final_score) / SUM(q.max_marks)
                    FROM responses r
                    JOIN questions q ON r.question_id = q.id
                    WHERE r.attempt_id = a.id
                ) END
            ) < :threshold
            OR COUNT(DISTINCT CASE WHEN a.status = 'not_started' THEN e.id END) > 2
            ORDER BY avg_performance ASC
        """
        
        result = await self.db.execute(query, {"class_id": class_id, "threshold": threshold})
        at_risk_students = result.fetchall()
        
        risk_analysis = []
        for student in at_risk_students:
            risk_factors = []
            risk_score = 0
            
            # Low performance
            if (student.avg_performance or 0) < threshold:
                risk_factors.append("Low average performance")
                risk_score += 30
            
            # Missed exams
            if (student.missed_exams or 0) > 2:
                risk_factors.append("Multiple missed exams")
                risk_score += 25
            
            # Declining trend
            if (student.recent_performance or 0) < (student.avg_performance or 0):
                risk_factors.append("Declining performance trend")
                risk_score += 20
            
            # Low attendance (based on attempted vs total exams)
            attendance_rate = (student.attempted_exams or 0) / (student.total_exams or 1)
            if attendance_rate < 0.8:
                risk_factors.append("Low exam attendance")
                risk_score += 15
            
            risk_analysis.append({
                "student_id": student.student_id,
                "student_name": student.student_name,
                "email": student.email,
                "avg_performance": round((student.avg_performance or 0) * 100, 2),
                "recent_performance": round((student.recent_performance or 0) * 100, 2),
                "attendance_rate": round(attendance_rate * 100, 2),
                "missed_exams": student.missed_exams or 0,
                "risk_score": min(risk_score, 100),
                "risk_level": "High" if risk_score >= 60 else "Medium" if risk_score >= 30 else "Low",
                "risk_factors": risk_factors,
                "recommended_actions": self._get_recommended_actions(risk_factors)
            })
        
        return risk_analysis
    
    def _get_recommended_actions(self, risk_factors: List[str]) -> List[str]:
        """Get recommended interventions based on risk factors"""
        actions = []
        
        if "Low average performance" in risk_factors:
            actions.extend([
                "Schedule one-on-one counseling session",
                "Provide additional study materials",
                "Recommend peer tutoring"
            ])
        
        if "Multiple missed exams" in risk_factors:
            actions.extend([
                "Contact student to understand attendance issues",
                "Provide makeup exam opportunities",
                "Connect with student support services"
            ])
        
        if "Declining performance trend" in risk_factors:
            actions.extend([
                "Identify specific topics causing difficulty",
                "Arrange remedial classes",
                "Monitor progress more closely"
            ])
        
        if "Low exam attendance" in risk_factors:
            actions.extend([
                "Investigate attendance barriers",
                "Provide flexible exam scheduling if possible",
                "Engage with academic advisor"
            ])
        
        return list(set(actions))  # Remove duplicates