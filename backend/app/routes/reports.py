from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role
from ..models.models import User
from ..schemas.report import (
    ExamReportRequest, ExamReportResponse, ProgramReportResponse,
    AnalyticsResponse, SGPAReportResponse, CGPAReportResponse,
    COReport, POReport
)
from ..services.reports import ReportsService

router = APIRouter()

@router.get("/exam/{exam_id}", response_model=ExamReportResponse,
           summary="Get exam report", tags=["Reports"])
async def get_exam_report(
    exam_id: int,
    include_students: bool = Query(True, description="Include individual student results"),
    include_questions: bool = Query(True, description="Include question-wise analysis"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed report for a specific exam"""
    service = ReportsService(db, current_user)

    # Verify exam access
    exam_data = await service.verify_exam_access(exam_id)
    if not exam_data:
        raise HTTPException(status_code=404, detail="Exam not found")

    report = await service.generate_exam_report(
        exam_id=exam_id,
        include_students=include_students,
        include_questions=include_questions
    )

    return ExamReportResponse(**report)

@router.get("/program/{program_id}", response_model=ProgramReportResponse,
           summary="Get program report", tags=["Reports"])
async def get_program_report(
    program_id: int,
    semester: Optional[int] = Query(None, description="Filter by semester"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive report for a program/course"""
    service = ReportsService(db, current_user)

    # Verify program access
    program_data = await service.verify_program_access(program_id)
    if not program_data:
        raise HTTPException(status_code=404, detail="Program not found")

    report = await service.generate_program_report(
        program_id=program_id,
        semester=semester,
        academic_year=academic_year
    )

    return ProgramReportResponse(**report)

@router.get("/analytics/overview", response_model=AnalyticsResponse,
           summary="Get system analytics overview", tags=["Reports"])
async def get_analytics_overview(
    days: int = Query(30, description="Days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "teacher"]))
):
    """Get system-wide analytics overview"""
    service = ReportsService(db, current_user)

    analytics = await service.get_system_analytics(days=days)
    return AnalyticsResponse(**analytics)

@router.get("/exam/{exam_id}/co-summary", response_model=List[COReport],
           summary="Get exam CO achievement summary", tags=["Reports"])
async def get_exam_co_summary(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Course Outcome (CO) achievement summary for an exam"""
    service = ReportsService(db, current_user)

    co_reports = await service.get_exam_co_achievements(exam_id)
    return [COReport(**co) for co in co_reports]

@router.get("/exam/{exam_id}/po-mapping", response_model=List[POReport],
           summary="Get exam PO mapping report", tags=["Reports"])
async def get_exam_po_mapping(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Program Outcome (PO) mapping report for an exam"""
    service = ReportsService(db, current_user)

    po_reports = await service.get_exam_po_mapping(exam_id)
    return [POReport(**po) for po in po_reports]

@router.get("/student/{student_id}/sgpa", response_model=SGPAReportResponse,
           summary="Get student SGPA report", tags=["Reports"])
async def get_student_sgpa(
    student_id: int,
    semester: Optional[int] = Query(None, description="Specific semester"),
    academic_year: Optional[str] = Query(None, description="Academic year"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Semester Grade Point Average (SGPA) for a student"""
    service = ReportsService(db, current_user)

    # Check access permissions
    if not await service.can_access_student_data(current_user, student_id):
        raise HTTPException(status_code=403, detail="Access denied")

    sgpa_report = await service.calculate_student_sgpa(
        student_id=student_id,
        semester=semester,
        academic_year=academic_year
    )

    return SGPAReportResponse(**sgpa_report)

@router.get("/student/{student_id}/cgpa", response_model=CGPAReportResponse,
           summary="Get student CGPA report", tags=["Reports"])
async def get_student_cgpa(
    student_id: int,
    semester: Optional[int] = Query(None, description="Up to specific semester"),
    academic_year: Optional[str] = Query(None, description="Up to academic year"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Cumulative Grade Point Average (CGPA) for a student"""
    service = ReportsService(db, current_user)

    # Check access permissions
    if not await service.can_access_student_data(current_user, student_id):
        raise HTTPException(status_code=403, detail="Access denied")

    cgpa_report = await service.calculate_student_cgpa(
        student_id=student_id,
        semester=semester,
        academic_year=academic_year
    )

    return CGPAReportResponse(**cgpa_report)

@router.post("/export/pdf/{report_type}", summary="Export report as PDF", tags=["Reports"])
async def export_report_pdf(
    report_type: str,
    report_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "teacher"]))
):
    """Export report as PDF file"""
    service = ReportsService(db, current_user)

    if report_type not in ["exam", "program", "analytics", "sgpa", "cgpa"]:
        raise HTTPException(status_code=400, detail="Invalid report type")

    pdf_bytes = await service.export_report_as_pdf(report_type, report_data)

    from fastapi.responses import StreamingResponse
    import io

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={report_type}_report.pdf'}
    )

@router.post("/export/excel/{report_type}", summary="Export report as Excel", tags=["Reports"])
async def export_report_excel(
    report_type: str,
    report_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "teacher"]))
):
    """Export report as Excel file"""
    service = ReportsService(db, current_user)

    if report_type not in ["exam", "program", "analytics", "sgpa", "cgpa"]:
        raise HTTPException(status_code=400, detail="Invalid report type")

    excel_bytes = await service.export_report_as_excel(report_type, report_data)

    from fastapi.responses import StreamingResponse
    import io

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={report_type}_report.xlsx'}
    )