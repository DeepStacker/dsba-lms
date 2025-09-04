from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class QuestionReportItem(BaseModel):
    question_id: int
    question_text: str
    max_marks: float
    student_score: Optional[float]
    is_correct: Optional[bool]
    feedback: Optional[str]

class COReportItem(BaseModel):
    co_id: int
    co_code: str
    co_title: str
    attainment_percentage: Optional[float]

class POReportItem(BaseModel):
    po_id: int
    po_code: str
    po_title: str
    attainment_percentage: Optional[float]

class StudentExamReport(BaseModel):
    exam_id: int
    exam_title: str
    total_marks: float
    student_total_score: Optional[float]
    percentage: Optional[float]
    grade: Optional[str]
    rank: Optional[int]
    questions: List[QuestionReportItem]

class StudentCOPOAttainment(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    co_attainment: List[COReportItem]
    po_attainment: List[POReportItem]

class StudentOverallReport(BaseModel):
    student_id: int
    student_name: str
    email: str
    total_sgpa: Optional[float] = None
    total_cgpa: Optional[float] = None
    exam_reports: List[StudentExamReport] = []
    co_po_attainment_summary: List[StudentCOPOAttainment] = []