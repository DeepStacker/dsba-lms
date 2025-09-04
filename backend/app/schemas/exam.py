from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.models import ExamStatus, AttemptStatus, ProctorEventType

class ExamBase(BaseModel):
    title: str
    start_at: datetime
    end_at: datetime
    join_window_sec: int = 300
    settings_json: Optional[Dict[str, Any]] = None

    @validator('end_at')
    def validate_end_time(cls, v, values):
        if 'start_at' in values and v <= values['start_at']:
            raise ValueError('End time must be after start time')
        return v

    @validator('join_window_sec')
    def validate_join_window(cls, v):
        if v < 60 or v > 3600:  # 1 minute to 1 hour
            raise ValueError('Join window must be between 60 and 3600 seconds')
        return v

class ExamCreate(ExamBase):
    class_id: int

class ExamUpdate(BaseModel):
    title: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    join_window_sec: Optional[int] = None
    settings_json: Optional[Dict[str, Any]] = None
    status: Optional[ExamStatus] = None

    @validator('end_at')
    def validate_end_time(cls, v, values):
        if v and 'start_at' in values and values['start_at'] and v <= values['start_at']:
            raise ValueError('End time must be after start time')
        return v

    @validator('join_window_sec')
    def validate_join_window(cls, v):
        if v is not None and (v < 60 or v > 3600):
            raise ValueError('Join window must be between 60 and 3600 seconds')
        return v

class ExamResponse(ExamBase):
    id: int
    class_id: int
    status: ExamStatus
    created_at: datetime
    updated_at: datetime
    total_questions: Optional[int] = None
    total_marks: Optional[float] = None
    class_name: Optional[str] = None
    course_name: Optional[str] = None

    class Config:
        from_attributes = True

class ExamQuestionBase(BaseModel):
    order: int
    marks_override: Optional[float] = None

class ExamQuestionCreate(ExamQuestionBase):
    exam_id: int
    question_id: int

class ExamQuestionUpdate(BaseModel):
    order: Optional[int] = None
    marks_override: Optional[float] = None

class ExamQuestionResponse(ExamQuestionBase):
    id: int
    exam_id: int
    question_id: int
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    max_marks: Optional[float] = None

    class Config:
        from_attributes = True

class ExamQuestionsAddRequest(BaseModel):
    question_ids: List[int]
    marks_overrides: Optional[Dict[int, float]] = None  # question_id -> marks

class AttemptBase(BaseModel):
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    status: AttemptStatus = AttemptStatus.NOT_STARTED
    autosubmitted: bool = False

class AttemptCreate(BaseModel):
    exam_id: int
    student_id: int

class AttemptUpdate(BaseModel):
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    status: Optional[AttemptStatus] = None
    autosubmitted: Optional[bool] = None

class AttemptResponse(AttemptBase):
    id: int
    exam_id: int
    student_id: int
    student_name: Optional[str] = None
    exam_title: Optional[str] = None
    total_marks: Optional[float] = None
    obtained_marks: Optional[float] = None

    class Config:
        from_attributes = True

class ResponseBase(BaseModel):
    answer_json: Dict[str, Any]
    ai_score: Optional[float] = None
    teacher_score: Optional[float] = None
    final_score: Optional[float] = None
    feedback: Optional[str] = None
    audit_json: Optional[Dict[str, Any]] = None

class ResponseCreate(ResponseBase):
    attempt_id: int
    question_id: int

class ResponseUpdate(BaseModel):
    answer_json: Optional[Dict[str, Any]] = None
    ai_score: Optional[float] = None
    teacher_score: Optional[float] = None
    final_score: Optional[float] = None
    feedback: Optional[str] = None
    audit_json: Optional[Dict[str, Any]] = None

class ResponseResponse(ResponseBase):
    id: int
    attempt_id: int
    question_id: int
    created_at: datetime
    updated_at: datetime
    question_text: Optional[str] = None
    max_marks: Optional[float] = None

    class Config:
        from_attributes = True

class ProctorLogBase(BaseModel):
    event_type: ProctorEventType
    payload: Optional[Dict[str, Any]] = None

class ProctorLogCreate(ProctorLogBase):
    attempt_id: int

class ProctorLogResponse(ProctorLogBase):
    id: int
    attempt_id: int
    ts: datetime

    class Config:
        from_attributes = True

class ExamJoinRequest(BaseModel):
    session_token: Optional[str] = None

class ExamJoinResponse(BaseModel):
    attempt_id: int
    exam_id: int
    questions: List[ExamQuestionResponse]
    time_remaining: int  # seconds
    settings: Dict[str, Any]
    websocket_url: str

class ExamSubmitRequest(BaseModel):
    attempt_id: int
    final_submission: bool = True

class ExamMonitorResponse(BaseModel):
    exam_id: int
    total_students: int
    joined_count: int
    active_count: int
    submitted_count: int
    auto_submitted_count: int
    time_remaining: int
    active_attempts: List[AttemptResponse]
    recent_events: List[ProctorLogResponse]

class ExamResultsResponse(BaseModel):
    exam_id: int
    exam_title: str
    total_students: int
    submitted_count: int
    graded_count: int
    average_score: Optional[float] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None
    results: List[AttemptResponse]

class StudentExamResponse(BaseModel):
    id: int
    title: str
    start_at: datetime
    end_at: datetime
    status: ExamStatus
    duration_minutes: int
    total_marks: float
    can_join: bool
    can_attempt: bool
    attempt_status: Optional[AttemptStatus] = None
    obtained_marks: Optional[float] = None
    class_name: str
    course_name: str