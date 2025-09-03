from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, cast, Float
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.models import (
    User, Program, Exam, Attempt, Response, Course,
    CO, PO, Question, ProctorLog, ClassSection,
    Enrollment, InternalScore, InternalComponent
)
from ..core.calculations import (
    calculate_sgpa, calculate_cgpa, calculate_co_attainment,
    calculate_po_attainment
)
import json


class ReportsService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user

    async def verify_exam_access(self, exam_id: int) -> Optional[Dict[str, Any]]:
        """Verify user has access to exam and return exam data"""
        result = await self.db.execute(
            select(Exam, ClassSection).join(ClassSection).where(Exam.id == exam_id)
        )
        exam_data = result.first()

        if not exam_data:
            return None

        exam, class_section = exam_data

        # Admin and teachers can access all exams
        if self.current_user.role.value in ["admin", "teacher"]:
            return {
                "exam": exam,
                "class_section": class_section,
                "has_access": True
            }

        # Students can only access enrolled exams
        if self.current_user.role.value == "student":
            enrollment_result = await self.db.execute(
                select(Enrollment).where(
                    and_(
                        Enrollment.class_id == class_section.id,
                        Enrollment.student_id == self.current_user.id
                    )
                )
            )
            if enrollment_result.scalar_one_or_none():
                return {
                    "exam": exam,
                    "class_section": class_section,
                    "has_access": True
                }

        return None

    async def verify_program_access(self, program_id: int) -> Optional[Dict[str, Any]]:
        """Verify user has access to program"""
        if self.current_user.role.value == "admin":
            result = await self.db.execute(select(Program).where(Program.id == program_id))
            program = result.scalar_one_or_none()
            return {"program": program, "has_access": True} if program else None

        if self.current_user.role.value == "teacher":
            # Teachers can access programs of courses they're teaching
            result = await self.db.execute(
                select(Program, Course).join(Course).where(Program.id == program_id)
            )
            data = result.first()
            if data:
                program, course = data
                # For now assume all teachers can access - implement proper teaching assignment later
                return {"program": program, "has_access": True}

        if self.current_user.role.value == "student":
            # Students can access their enrolled programs
            result = await self.db.execute("""
                SELECT DISTINCT p.* FROM programs p
                JOIN courses c ON p.id = c.program_id
                JOIN class_sections cs ON c.id = cs.course_id
                JOIN enrollments e ON cs.id = e.class_id
                WHERE e.student_id = $1 AND p.id = $2
            """, (self.current_user.id, program_id))
            program = result.first()
            return {"program": program, "has_access": True} if program else None

        return None

    async def get_system_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get system-wide analytics"""

        # Calculate date threshold
        date_threshold = datetime.utcnow() - timedelta(days=days)

        # Total users by role
        user_stats_result = await self.db.execute("""
            SELECT role, COUNT(*) as count
            FROM users
            GROUP BY role
        """)
        user_stats = dict(user_stats_result.fetchall())

        # Recent exam stats
        exam_stats_result = await self.db.execute("""
            SELECT
                COUNT(CASE WHEN status = 'ended' THEN 1 END) as completed_exams,
                COUNT(CASE WHEN status = 'started' THEN 1 END) as active_exams,
                COUNT(*) as total_exams
            FROM exams
            WHERE created_at >= $1
        """, (date_threshold,))
        exam_stats = exam_stats_result.fetchone()

        # Attempt stats
        attempt_stats_result = await self.db.execute("""
            SELECT
                COUNT(CASE WHEN status = 'submitted' THEN 1 END) as completed_attempts,
                COUNT(CASE WHEN status = 'auto_submitted' THEN 1 END) as auto_submitted_attempts,
                COUNT(*) as total_attempts
            FROM attempts
            WHERE started_at >= $1
        """, (date_threshold,))
        attempt_stats = attempt_stats_result.fetchone()

        # Proctor events
        proctor_events_result = await self.db.execute("""
            SELECT
                event_type,
                COUNT(*) as count
            FROM proctor_logs pl
            JOIN attempts a ON a.id = pl.attempt_id
            WHERE pl.ts >= $1
            GROUP BY event_type
        """, (date_threshold,))
        proctor_events = dict(proctor_events_result.fetchall())

        return {
            "user_stats": user_stats,
            "exam_stats": {
                "completed": exam_stats.completed_exams,
                "active": exam_stats.active_exams,
                "total": exam_stats.total_exams
            },
            "attempt_stats": {
                "completed": attempt_stats.completed_attempts,
                "auto_submitted": attempt_stats.auto_submitted_attempts,
                "total": attempt_stats.total_attempts
            },
            "proctor_events": proctor_events,
            "period_days": days
        }

    async def generate_exam_report(self, exam_id: int, include_students: bool = True,
                                 include_questions: bool = True) -> Dict[str, Any]:
        """Generate comprehensive exam report"""

        # Get exam and attempts
        result = await self.db.execute(
            select(Exam).where(Exam.id == exam_id)
        )
        exam = result.scalar_one()

        attempts_result = await self.db.execute(
            select(Attempt, User).join(User).where(Attempt.exam_id == exam_id)
        )
        attempts_data = attempts_result.fetchall()

        attempts = [{"attempt": a, "student": s} for a, s in attempts_data]

        # Get questions and responses
        questions_result = await self.db.execute("""
            SELECT q.*, eq.marks_override
            FROM questions q
            JOIN exam_questions eq ON q.id = eq.question_id
            WHERE eq.exam_id = $1
            ORDER BY eq.order
        """, (exam_id,))
        questions = questions_result.fetchall()

        # Get responses
        responses_result = await self.db.execute("""
            SELECT r.*, q.text as question_text, q.type as question_type
            FROM responses r
            JOIN questions q ON q.id = r.question_id
            WHERE r.attempt_id IN (
                SELECT a.id FROM attempts a WHERE a.exam_id = $1
            )
        """, (exam_id,))
        responses = responses_result.fetchall()

        report = {
            "exam_id": exam.id,
            "exam_title": exam.title,
            "exam_status": exam.status.value,
            "total_attempts": len(attempts),
            "completed_attempts": len([a for a, s in attempts if a["attempt"].status.value in ["submitted", "auto_submitted"]]),
            "questions_count": len(questions)
        }

        if include_students:
            student_reports = []
            for attempt_data in attempts:
                attempt = attempt_data["attempt"]
                student = attempt_data["student"]

                student_responses = [r for r in responses if r.attempt_id == attempt.id]

                student_report = {
                    "student_id": student.id,
                    "student_name": student.name,
                    "student_email": student.email,
                    "attempt_status": attempt.status.value,
                    "started_at": attempt.started_at,
                    "submitted_at": attempt.submitted_at,
                    "autosubmitted": attempt.autosubmitted,
                    "responses_count": len(student_responses),
                    "proctor_events_count": 0  # Will implement later
                }

                if student_responses:
                    # Calculate scores
                    total_marks = 0
                    ai_scores = 0
                    teacher_scores = 0
                    for response in student_responses:
                        if response.ai_score:
                            ai_scores += response.ai_score
                        if response.teacher_score:
                            teacher_scores += response.teacher_score
                        if response.final_score:
                            total_marks += response.final_score

                    student_report["ai_total_score"] = ai_scores
                    student_report["teacher_total_score"] = teacher_scores
                    student_report["final_total_score"] = total_marks

                student_reports.append(student_report)

            report["student_reports"] = student_reports

        if include_questions:
            question_analytics = []
            for question in questions:
                q_responses = [r for r in responses if r.question_id == question.id]

                analytics = {
                    "question_id": question.id,
                    "question_text": question.text,
                    "question_type": question.type.value,
                    "max_marks": question.max_marks,
                    "responses_count": len(q_responses)
                }

                if q_responses:
                    # Score distribution
                    scores = []
                    for r in q_responses:
                        score = r.final_score or r.teacher_score or r.ai_score or 0
                        scores.append(score)

                    analytics["avg_score"] = sum(scores) / len(scores) if scores else 0
                    analytics["min_score"] = min(scores) if scores else 0
                    analytics["max_score"] = max(scores) if scores else 0
                    analytics["score_distribution"] = get_score_distribution(scores) if scores else {}

                question_analytics.append(analytics)

            report["question_analytics"] = question_analytics

        return report

    async def calculate_student_sgpa(self, student_id: int, semester: Optional[int] = None,
                                   academic_year: Optional[str] = None) -> Dict[str, Any]:
        """Calculate student SGPA"""
        try:
            sgpa_data = await calculate_sgpa(
                self.db, student_id, semester=semester, academic_year=academic_year
            )
            return {
                "student_id": student_id,
                "sgpa": sgpa_data["sgpa"],
                "grade_points": sgpa_data["grade_points"],
                "total_credits": sgpa_data["total_credits"],
                "semester": semester,
                "academic_year": academic_year,
                "course_grades": sgpa_data["course_grades"]
            }
        except Exception as e:
            raise Exception(f"Failed to calculate SGPA: {str(e)}")

    async def calculate_student_cgpa(self, student_id: int, semester: Optional[int] = None,
                                   academic_year: Optional[str] = None) -> Dict[str, Any]:
        """Calculate student CGPA"""
        try:
            cgpa_data = await calculate_cgpa(
                self.db, student_id, semester=semester, academic_year=academic_year
            )
            return {
                "student_id": student_id,
                "cgpa": cgpa_data["cgpa"],
                "total_credits": cgpa_data["total_credits"],
                "semesters_included": cgpa_data["semesters_included"],
                "cumulative_data": cgpa_data
            }
        except Exception as e:
            raise Exception(f"Failed to calculate CGPA: {str(e)}")

    async def get_exam_co_achievements(self, exam_id: int) -> List[Dict[str, Any]]:
        """Calculate CO achievements for exam"""
        try:
            # Find all COs referenced by questions in this exam
            from sqlalchemy import text
            q = text(
                "SELECT DISTINCT c.id, c.code, c.title, c.course_id "
                "FROM cos c "
                "JOIN questions q ON q.co_id = c.id "
                "JOIN exam_questions eq ON eq.question_id = q.id "
                "WHERE eq.exam_id = :exam_id"
            )
            result = await self.db.execute(q, {"exam_id": exam_id})
            cos = result.fetchall()

            co_reports = []
            for co_row in cos:
                co_id = co_row.id
                attainment = await calculate_co_attainment(self.db, co_id, exam_ids=[exam_id])
                co_reports.append({
                    "co_id": co_id,
                    "co_code": co_row.code,
                    "co_title": co_row.title,
                    "course_id": co_row.course_id,
                    "attainment_percent": round(attainment, 2)
                })

            return co_reports
        except Exception as e:
            raise Exception(f"Failed to calculate CO achievements: {str(e)}")

    async def get_exam_po_mapping(self, exam_id: int) -> List[Dict[str, Any]]:
        """Get PO mapping for exam"""
        try:
            # Get all POs that are linked via COs included in this exam
            from sqlalchemy import text
            q = text(
                "SELECT DISTINCT p.id, p.code, p.title "
                "FROM pos p "
                "JOIN co_po_maps m ON m.po_id = p.id "
                "JOIN cos c ON c.id = m.co_id "
                "JOIN questions q ON q.co_id = c.id "
                "JOIN exam_questions eq ON eq.question_id = q.id "
                "WHERE eq.exam_id = :exam_id"
            )
            result = await self.db.execute(q, {"exam_id": exam_id})
            pos = result.fetchall()

            po_reports = []
            for po_row in pos:
                po_id = po_row.id
                attainment = await calculate_po_attainment(self.db, po_id, exam_ids=[exam_id])
                po_reports.append({
                    "po_id": po_id,
                    "po_code": po_row.code,
                    "po_title": po_row.title,
                    "attainment_percent": round(attainment, 2)
                })

            return po_reports
        except Exception as e:
            raise Exception(f"Failed to calculate PO mapping: {str(e)}")

    async def can_access_student_data(self, user: User, student_id: int) -> bool:
        """Check if user can access student data"""
        if user.id == student_id:  # Own data
            return True

        if user.role.value == "admin":  # Admin access all
            return True

        if user.role.value == "teacher":
            # Check if teacher is associated with any classes the student is enrolled in
            result = await self.db.execute("""
                SELECT COUNT(*) FROM enrollments e
                JOIN class_sections cs ON e.class_id = cs.id
                WHERE e.student_id = $1
                  AND cs.id IN (
                      SELECT cs2.id FROM class_sections cs2
                      WHERE cs2.id IN (SELECT class_id FROM exams)
                      -- Additional teacher-course mapping logic needed here
                  )
            """, (student_id,))
            count = result.scalar()
            return count > 0

        return False

    async def generate_program_report(self, program_id: int, semester: Optional[int] = None,
                                    academic_year: Optional[str] = None) -> Dict[str, Any]:
        """Generate program-level report"""
        # Implementation details to be completed
        return {
            "program_id": program_id,
            "semester": semester,
            "academic_year": academic_year,
            "analytics": {}
        }

    async def export_report_as_pdf(self, report_type: str, report_data: Dict[str, Any]) -> bytes:
        """Export report as PDF"""
        # Simple PDF generator using reportlab
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        import io

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 40, f"{report_type.upper()} Report")

        c.setFont("Helvetica", 10)
        y = height - 80
        for k, v in report_data.items():
            line = f"{k}: {v}"
            c.drawString(40, y, line[:120])
            y -= 14
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 40

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()

    async def export_report_as_excel(self, report_type: str, report_data: Dict[str, Any]) -> bytes:
        """Export report as Excel"""
        import io
        import pandas as pd

        buffer = io.BytesIO()
        # If report_data contains lists (like student_reports), create multiple sheets
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Top-level simple key-values
            kv = {k: v for k, v in report_data.items() if not isinstance(v, list)}
            if kv:
                df_kv = pd.DataFrame(list(kv.items()), columns=['key', 'value'])
                df_kv.to_excel(writer, sheet_name='summary', index=False)

            # Other list sections
            for key, value in report_data.items():
                if isinstance(value, list) and value:
                    try:
                        df = pd.DataFrame(value)
                        sheet_name = key[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    except Exception:
                        # Fallback: stringify
                        df = pd.DataFrame([{key: str(value)}])
                        df.to_excel(writer, sheet_name=key[:31], index=False)

        buffer.seek(0)
        return buffer.read()


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
