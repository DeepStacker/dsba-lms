from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ExamReportRequest(BaseModel):
    exam_id: int
    include_students: bool = True
    include_questions: bool = True

class StudentResult(BaseModel):
    student_id: int
    student_name: str
    roll_no: Optional[str] = None
    score: float
    percentage: float
    grade: str
    submission_time: datetime
    marks_obtained: float
    total_marks: float

class QuestionStats(BaseModel):
    question_id: int
    question_text: str
    marks: float
    difficulty: str
    correct_attempts: int
    total_attempts: int
    average_time: Optional[float] = None  # in seconds
    co_achievement: Optional[float] = None

class ExamReportResponse(BaseModel):
    exam_id: int
    exam_name: str
    program_name: str
    semester: int
    total_students: int
    appeared_students: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_percentage: float
    student_results: List[StudentResult]
    question_stats: List[QuestionStats]
    generated_at: datetime
    report_type: str = "exam"

class ProgramReportResponse(BaseModel):
    program_id: int
    program_name: str
    semester: Optional[int]
    academic_year: Optional[str]
    total_exams: int
    total_students: int
    average_sgpa: float
    pass_rate: float
    co_achievements: List[Dict[str, Any]]
    grade_distribution: Dict[str, int]
    generated_at: datetime

class AnalyticsResponse(BaseModel):
    total_users: int
    total_exams: int
    total_students: int
    total_teachers: int
    active_exams_today: int
    completed_exams: int
    avg_completion_rate: float
    top_performers: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    period_days: int

class SGPAReportResponse(BaseModel):
    student_id: int
    student_name: str
    semester: int
    academic_year: str
    sgpa: float
    credit_points: float
    total_credits: int
    courses: List[Dict[str, Any]]
    generated_at: datetime

class CGPAReportResponse(BaseModel):
    student_id: int
    student_name: str
    cgpa: float
    total_semesters: int
    p_until: Optional[int] = None  # Up to which semester
    semester_wise_sgpa: List[Dict[str, Any]]
    total_credit_points: float
    total_credits: int
    generated_at: datetime

class COReport(BaseModel):
    co_code: str
    co_description: str
    achievement_percentage: float
    target_percentage: float
    status: str  # "achieved", "partially_achieved", "not_achieved"
    contributing_questions: List[Dict[str, Any]]

class POReport(BaseModel):
    po_code: str
    po_description: str
    achievement_percentage: float
    target_percentage: float
    status: str
    mapped_cos: List[Dict[str, Any]]
    supporting_evidences: List[str]