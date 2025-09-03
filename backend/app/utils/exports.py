"""
Export utilities for PDF and CSV generation
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from io import BytesIO
import logging
from pathlib import Path
from datetime import datetime
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


class PDFExporter:
    """PDF export functionality for reports"""

    def __init__(self):
        self.styles = getSampleStyleSheet()

        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )

        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10
        )

        self.table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])

    def generate_sgpa_report(self, sgpa_data: Dict[str, Any],
                           cgpa_data: Optional[Dict[str, Any]] = None) -> bytes:
        """Generate SGPA/CGPA report PDF"""

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        # Title
        story.append(Paragraph("Academic Performance Report", self.title_style))
        story.append(Spacer(1, 12))

        # Student info
        story.append(Paragraph("Student Information", self.heading_style))
        student_info = [
            ["Student ID", str(sgpa_data.get("student_id", ""))],
            ["Academic Year", str(sgpa_data.get("academic_year", ""))],
            ["Semester", str(sgpa_data.get("semester", ""))]
        ]
        story.append(Table(student_info, style=self.table_style))
        story.append(Spacer(1, 20))

        # SGPA Summary
        story.append(Paragraph("Semester Performance (SGPA)", self.heading_style))
        sgpa_summary = [
            ["SGPA", ".2f"]        ]
        story.append(Table(sgpa_summary, style=self.table_style))
        story.append(Spacer(1, 20))

        # Course grades
        if sgpa_data.get("course_grades"):
            story.append(Paragraph("Course-wise Performance", self.heading_style))
            course_headers = ["Course", "Credits", "Marks", "Grade Point", "Total Score"]

            course_data = [course_headers]
            for grade in sgpa_data["course_grades"]:
                row = [
                    str(grade.get("course_id", "")),
                    str(grade.get("credits", "")),
                    ".1f",
                    ".1f",
                    ".1f"                ]
                course_data.append(row)

            course_table = Table(course_data, style=self.table_style)
            story.append(course_table)
            story.append(Spacer(1, 20))

        # CGPA if available
        if cgpa_data:
            story.append(PageBreak())
            story.append(Paragraph("Cumulative Performance (CGPA)", self.heading_style))
            cgpa_summary = [
                ["CGPA", ".2f"],
                ["Total Credits", str(cgpa_data.get("total_credits", 0))],
                ["Semesters Completed", str(cgpa_data.get("semesters_included", 0))]
            ]
            story.append(Table(cgpa_summary, style=self.table_style))

        # Footer
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_exam_report(self, exam_data: Dict[str, Any],
                           student_reports: List[Dict[str, Any]]) -> bytes:
        """Generate comprehensive exam report PDF"""

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        # Title
        story.append(Paragraph(f"Exam Report: {exam_data.get('exam_title', '')}",
                             self.title_style))
        story.append(Spacer(1, 12))

        # Exam summary
        story.append(Paragraph("Exam Summary", self.heading_style))
        summary_data = [
            ["Exam ID", str(exam_data.get("exam_id", ""))],
            ["Status", str(exam_data.get("exam_status", ""))],
            ["Total Attempts", str(exam_data.get("total_attempts", 0))],
            ["Completed Attempts", str(exam_data.get("completed_attempts", 0))],
            ["Total Questions", str(exam_data.get("questions_count", 0))]
        ]
        story.append(Table(summary_data, style=self.table_style))
        story.append(Spacer(1, 20))

        # Student performance
        if student_reports:
            story.append(PageBreak())
            story.append(Paragraph("Student Performance", self.heading_style))

            student_headers = ["Student", "Status", "AI Score", "Final Score", "Proctor Events"]
            student_data = [student_headers]

            for student in student_reports:
                row = [
                    f"{student.get('student_name', '')}\n{student.get('student_email', '')}",
                    student.get("attempt_status", ""),
                    ".1f" if student.get("ai_total_score") else "N/A",
                    ".1f" if student.get("final_total_score") else "N/A",
                    str(student.get("proctor_events_count", 0))
                ]
                student_data.append(row)

            student_table = Table(student_data, colWidths=[100, 60, 50, 50, 60], style=self.table_style)
            story.append(student_table)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_analytics_report(self, analytics_data: Dict[str, Any]) -> bytes:
        """Generate system analytics report PDF"""

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        story.append(Paragraph("System Analytics Report", self.title_style))
        story.append(Spacer(1, 12))

        # User stats
        if analytics_data.get("user_stats"):
            story.append(Paragraph("User Distribution", self.heading_style))
            user_data = [["Role", "Count"]]
            for role, count in analytics_data["user_stats"].items():
                user_data.append([role, str(count)])
            story.append(Table(user_data, style=self.table_style))
            story.append(Spacer(1, 20))

        # Exam stats
        if analytics_data.get("exam_stats"):
            story.append(Paragraph("Exam Statistics", self.heading_style))
            exam_data = [
                ["Completed Exams", str(analytics_data["exam_stats"].get("completed", 0))],
                ["Active Exams", str(analytics_data["exam_stats"].get("active", 0))],
                ["Total Exams", str(analytics_data["exam_stats"].get("total", 0))]
            ]
            story.append(Table(exam_data, style=self.table_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


class CSVExporter:
    """CSV export functionality for reports"""

    def generate_sgpa_csv(self, sgpa_data: Dict[str, Any],
                         cgpa_data: Optional[Dict[str, Any]] = None) -> bytes:
        """Generate CSV for SGPA/CGPA data"""

        data = {
            "Student ID": [str(sgpa_data.get("student_id", ""))],
            "Academic Year": [str(sgpa_data.get("academic_year", ""))],
            "Semester": [str(sgpa_data.get("semester", ""))],
            "SGPA": [f"{sgpa_data.get('sgpa', 0):.2f}"],
            "Total Credits": [str(sgpa_data.get("total_credits", 0))]
        }

        # Add CGPA if available
        if cgpa_data:
            data["CGPA"] = [f"{cgpa_data.get('cgpa', 0):.2f}"]

        # Course grades as separate section
        if sgpa_data.get("course_grades"):
            course_data = []
            for grade in sgpa_data["course_grades"]:
                course_data.append({
                    "Course ID": grade.get("course_id", ""),
                    "Credits": grade.get("credits", 0),
                    "Marks": f"{grade.get('marks', 0):.1f}",
                    "Grade Point": f"{grade.get('grade_point', 0):.2f}"
                })

            if course_data:
                df_course = pd.DataFrame(course_data)
                data.update(df_course.to_dict('list'))

        df = pd.DataFrame(data)
        buffer = BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_exam_csv(self, exam_data: Dict[str, Any],
                         student_reports: List[Dict[str, Any]]) -> bytes:
        """Generate CSV for exam report"""

        data = []

        for student in student_reports:
            row = {
                "Student Name": student.get("student_name", ""),
                "Student Email": student.get("student_email", ""),
                "Attempt Status": student.get("attempt_status", ""),
                "Started At": student.get("started_at", ""),
                "Submitted At": student.get("submitted_at", ""),
                "AI Total Score": f"{student.get('ai_total_score', 0):.1f}",
                "Final Total Score": f"{student.get('final_total_score', 0):.1f}",
                "Proctor Events": student.get("proctor_events_count", 0)
            }
            data.append(row)

        df = pd.DataFrame(data)
        buffer = BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_analytics_csv(self, analytics_data: Dict[str, Any]) -> bytes:
        """Generate CSV for analytics data"""

        # Flatten nested dict to CSV-friendly format
        flattened_data = {
            "Period Days": analytics_data.get("period_days", 0),
            "Total Users": sum(analytics_data.get("user_stats", {}).values()),
            "Completed Exams": analytics_data.get("exam_stats", {}).get("completed", 0),
            "Active Exams": analytics_data.get("exam_stats", {}).get("active", 0),
            "Completed Attempts": analytics_data.get("attempt_stats", {}).get("completed", 0),
            "Auto-Submitted Attempts": analytics_data.get("attempt_stats", {}).get("auto_submitted", 0)
        }

        # Add role-specific user counts
        if analytics_data.get("user_stats"):
            for role, count in analytics_data["user_stats"].items():
                flattened_data[f"Users ({role.title()})"] = count

        # Add proctor events
        if analytics_data.get("proctor_events"):
            for event_type, count in analytics_data["proctor_events"].items():
                flattened_data[f"Proctor Events ({event_type})"] = count

        df = pd.DataFrame([flattened_data])
        buffer = BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer.getvalue()


# Utility functions
def export_sgpa_report_pdf(sgpa_data: Dict[str, Any], cgpa_data: Optional[Dict[str, Any]] = None) -> bytes:
    """Convenience function for PDF SGPA export"""
    exporter = PDFExporter()
    return exporter.generate_sgpa_report(sgpa_data, cgpa_data)


def export_sgpa_report_csv(sgpa_data: Dict[str, Any], cgpa_data: Optional[Dict[str, Any]] = None) -> bytes:
    """Convenience function for CSV SGPA export"""
    exporter = CSVExporter()
    return exporter.generate_sgpa_csv(sgpa_data, cgpa_data)


def export_exam_report_pdf(exam_data: Dict[str, Any], student_reports: List[Dict[str, Any]]) -> bytes:
    """Convenience function for PDF exam export"""
    exporter = PDFExporter()
    return exporter.generate_exam_report(exam_data, student_reports)


def export_exam_report_csv(exam_data: Dict[str, Any], student_reports: List[Dict[str, Any]]) -> bytes:
    """Convenience function for CSV exam export"""
    exporter = CSVExporter()
    return exporter.generate_exam_csv(exam_data, student_reports)


def export_analytics_report_pdf(analytics_data: Dict[str, Any]) -> bytes:
    """Convenience function for PDF analytics export"""
    exporter = PDFExporter()
    return exporter.generate_analytics_report(analytics_data)


def export_analytics_report_csv(analytics_data: Dict[str, Any]) -> bytes:
    """Convenience function for CSV analytics export"""
    exporter = CSVExporter()
    return exporter.generate_analytics_csv(analytics_data)