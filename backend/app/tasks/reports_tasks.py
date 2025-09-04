from celery import shared_task
from sqlalchemy.future import select
import asyncio
import logging
import io
import pandas as pd
import json

from ..core.database import async_session
from ..models.models import User, Exam, Question, Attempt, Response, CO, PO, Course, CO_PO_Map, ClassSection
from sqlalchemy.orm import selectinload, joinedload
from ..schemas.report import (
    StudentExamReport, StudentCOPOAttainment, StudentOverallReport,
    QuestionReportItem, COReportItem, POReportItem
)
from ..core.calculations import get_grade_point_from_marks, calculate_co_attainment, calculate_po_attainment, calculate_sgpa, calculate_cgpa, calculate_exam_statistics, get_score_distribution
from ..services.notifications import send_notification # Assuming a notification service exists

logger = logging.getLogger(__name__)

async def _get_db_session():
    """Helper to get an async session within a Celery task context."""
    async with async_session() as session:
        yield session

@shared_task(name="reports_tasks.generate_student_report_pdf")
def generate_student_report_pdf_task(student_id: int, actor_id: int):
    logger.info(f"Generating PDF student report for student {student_id} by actor {actor_id}")
    return asyncio.run(_generate_student_report_pdf(student_id, actor_id))

async def _generate_student_report_pdf(student_id: int, actor_id: int):
    async for db in _get_db_session():
        try:
            # Re-use logic from get_overall_student_report to fetch data
            # For simplicity, this is a placeholder where actual PDF generation logic would go
            # You would use a library like ReportLab or WeasyPrint here

            student_result = await db.execute(select(User).where(User.id == student_id))
            student = student_result.scalar_one_or_none()
            if not student:
                logger.error(f"Student {student_id} not found for report generation.")
                send_notification(actor_id, "Report Generation Failed", f"Student {student_id} not found for PDF report.")
                return None

            # Dummy PDF content
            content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>Contents 4 0 R>>endobj 4 0 obj<</Length 16>>stream\nBT /F1 24 Tf 100 700 Td (Student Report for ID: {student_id}) Tj ET\nendstream\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000074 00000 n\n0000000120 00000 n\n0000000201 00000 n\ntrailer<</Size 5/Root 1 0 R>>startxref\n291\n%%EOF".replace(b"{student_id}", str(student_id).encode('utf-8'))

            # In a real app, save this to a file storage (S3, local disk) and return a URL
            report_url = f"/reports/generated/student_{student_id}_report_{datetime.utcnow().timestamp()}.pdf"
            
            # Simulate saving to disk
            # with open(f"reports/{report_url.split('/')[-1]}", "wb") as f:
            #     f.write(content)

            send_notification(actor_id, "Report Generation Complete", f"PDF Student Report for {student.name} is ready at {report_url}")
            return {"status": "success", "report_url": report_url}
        except Exception as e:
            logger.error(f"Error generating PDF student report for student {student_id}: {e}", exc_info=True)
            send_notification(actor_id, "Report Generation Failed", f"PDF Student Report for {student_id} encountered an error: {e}")
            return {"status": "failed", "error": str(e)}

# Add similar tasks for other report types (class CO/PO, exam, etc.)