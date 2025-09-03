from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal

# Enums
class ExamStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    STARTED = "started"
    ENDED = "ended"
    RESULTS_PUBLISHED = "results_published"

class AttemptStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    AUTO_SUBMITTED = "auto_submitted"
    TIMEOUT = "timeout"

class ProctorEventType(str, Enum):
    TAB_SWITCH = "tab_switch"
    FOCUS_LOSS = "focus_loss"
    NETWORK_DROP = "network_drop"
    PASTE = "paste"
    FULLSCREEN_EXIT = "fullscreen_exit"
    MULTIPLE_FACES = "multiple_faces"
    EXTERNAL_DEVICE = "external_device"

# Exam Management Schemas
class ExamSettings(BaseModel):
    """Comprehensive exam settings"""
    shuffle_questions: bool = Field(False, description="Randomize question order")
    shuffle_options: bool = Field(False, description="Randomize MCQ options")
    negative_marking: bool = Field(False, description="Apply negative marking")
    negative_marks_percentage: float = Field(0.33, description="Negative marks per wrong answer")
    lock_answers: bool = Field(True, description="Prevent answer changes after submission")
    auto_submit_time_remaining: int = Field(300, description="Auto-submit when N seconds remaining")
    show_results_immediately: bool = Field(False, description="Show scores after submission")
    max_attempts_per_question: int = Field(1, description="Max attempts per question")
    camera_required: bool = Field(False, description="Require webcam")
    microphone_required: bool = Field(False, description="Require microphone")
    screen_sharing: bool = Field(False, description="Enable screen sharing")
    allow_calculator: bool = Field(False, description="Allow calculator usage")
    mobile_friendly: bool = Field(True, description="Enable mobile responsiveness")

class ExamBase(BaseModel):
    """Base exam schema"""
    title: str = Field(..., min_length=1, max_length=255, description="Exam title")
    description: Optional[str] = Field(None, description="Exam description")
    instructions: Optional[str] = Field(None, description="Exam instructions for students")
    settings: ExamSettings = Field(default_factory=lambda: ExamSettings(), description="Exam configuration")
    sash_window_sec: int = Field(300, ge=0, description="Join window in seconds")

class ExamCreate(ExamBase):
    """Create exam schema"""
    class_id: int = Field(..., description="Class section ID")
    start_at: datetime = Field(..., description="Exam start time")
    end_at: datetime = Field(..., description="Exam end time")
    duration_minutes: int = Field(..., ge=15, le=480, description="Exam duration in minutes")

    @validator('end_at')
    def validate_end_after_start(cls, v, values):
        if 'start_at' in values and v <= values['start_at']:
            raise ValueError('end_at must be after start_at')
        return v

class ExamUpdate(BaseModel):
    """Update exam schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    instructions: Optional[str] = Field(None)
    start_at: Optional[datetime] = Field(None)
    end_at: Optional[datetime] = Field(None)
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    settings: Optional[ExamSettings] = Field(None)
    join_window_sec: Optional[int] = Field(None, ge=0)
    status: Optional[ExamStatus] = Field(None)

    @validator('end_at')
    def validate_end_after_start(cls, v, values):
        if 'start_at' in values and values['start_at'] and v and v <= values['start_at']:
            raise ValueError('end_at must be after start_at')
        return v

class Exam(BaseModel):
    """Full exam response schema"""
    id: int
    title: str
    description: Optional[str]
    instructions: Optional[str]
    class_id: int
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    join_window_sec: int
    settings: Dict[str, Any]
    status: ExamStatus
    created_at: datetime
    updated_at: datetime
    creator_id: int

    class Config:
        from_attributes = True

class ExamListItem(BaseModel):
    """Compact exam list item"""
    id: int
    title: str
    start_at: datetime
    end_at: datetime
    status: ExamStatus
    total_questions: int = Field(..., description="Questions in exam")
    enrolled_students: int = Field(..., description="Enrolled students")

# Attempt Management
class Attempt(BaseModel):
    """Exam attempt response"""
    id: int
    exam_id: int
    student_id: int
    started_at: Optional[datetime]
    submitted_at: Optional[datetime]
    status: AttemptStatus
    autosubmitted: bool
    remaining_time_sec: Optional[int]
    current_question_index: int
    answers_provided: int
    total_questions: int
    time_spent_sec: int

    class Config:
        from_attributes = True

class AttemptCreate(BaseModel):
    """Join/create exam attempt"""
    exam_id: int
    student_id: int

class AttemptUpdate(BaseModel):
    """Update attempt (rarely used)"""
    status: Optional[AttemptStatus] = None
    current_question_index: Optional[int] = None

# Response Management
class AnswerSubmission(BaseModel):
    """Student answer submission"""
    question_id: int = Field(..., description="Question being answered")
    answer_json: Dict[str, Any] = Field(..., description="Answer data")
    answer_type: str = Field(..., description="Answer type (text, choice, etc.)")
    time_spent_sec: int = Field(0, description="Time spent on question")

class ResponseCreate(BaseModel):
    """Create response schema"""
    attempt_id: int
    question_id: int
    answer_json: Dict[str, Any]
    time_spent_sec: int = 0

class ResponseUpdate(BaseModel):
    """Update response schema"""
    answer_json: Optional[Dict[str, Any]] = None
    ai_score: Optional[Decimal] = None
    teacher_score: Optional[Decimal] = None
    final_score: Optional[Decimal] = None
    feedback: Optional[str] = None
    ai_feedback: Optional[str] = None
    teacher_feedback: Optional[str] = None

class ResponseSubmissionResponse(BaseModel):
    """Response submission confirmation"""
    success: bool = Field(True, description="Submission successful")
    question_index: int = Field(..., description="Question index updated")
    next_question_index: Optional[int] = Field(None, description="Next question if available")

class Response(BaseModel):
    """Full response with grading"""
    id: int
    attempt_id: int
    question_id: int
    answer_json: Dict[str, Any]
    ai_score: Optional[Decimal] = None
    teacher_score: Optional[Decimal] = None
    final_score: Optional[Decimal] = None
    feedback: Optional[str] = None
    grading_status: str = Field("ungraded", description="Grading status")
    ai_feedback: Optional[str] = None
    teacher_feedback: Optional[str] = None
    time_spent_sec: int
    is_correct: Optional[bool] = None
    rubric_scoring: Optional[Dict[str, Any]] = None
    audit_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Real-time Proctoring
class ProctorEvent(BaseModel):
    """Proctoring event"""
    attempt_id: int
    event_type: ProctorEventType
    severity: str = Field("info", description="Event severity")
    payload: Dict[str, Any] = Field({}, description="Event specific data")
    screenshot_url: Optional[str] = None

class ProctorLogCreate(BaseModel):
    """Create proctor log schema"""
    attempt_id: int
    event_type: ProctorEventType
    payload: Dict[str, Any] = {}

class ProctorLog(BaseModel):
    """Proctoring log entry"""
    id: int
    attempt_id: int
    timestamp: datetime
    event_type: ProctorEventType
    payload: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True

class ProctoringConfig(BaseModel):
    """Exam proctoring settings"""
    enable_tab_switching_detection: bool = True
    enable_fullscreen_monitoring: bool = True
    enable_paste_detection: bool = True
    enable_network_monitoring: bool = True
    enable_webcam_monitoring: bool = False
    strict_mode: bool = False
    auto_flag_threshold: int = 5
    screenshot_interval_sec: int = 60

# Results & Analytics
class ExamResult(BaseModel):
    """Individual exam result"""
    attempt_id: int
    student_id: int
    student_name: str
    score: Decimal
    max_score: Decimal
    percentage: Decimal
    grade: str
    correct_answers: int
    incorrect_answers: int
    unattempted: int
    time_taken_sec: int
    submitted_at: datetime
    ai_graded_questions: int
    teacher_graded_questions: int

class ExamAnalytics(BaseModel):
    """Exam-wide analytics"""
    total_attempts: int
    completed_attempts: int
    average_score: Decimal
    median_score: Decimal
    highest_score: Decimal
    lowest_score: Decimal
    score_distribution: Dict[str, int]
    question_difficulty: Dict[int, Decimal]  # question_id -> difficulty score
    co_po_achievements: Dict[str, Decimal]
    time_distribution: Dict[str, int]
    proctor_events_count: int
    cheating_suspected: int

class QuestionAnalytics(BaseModel):
    """Question-level analytics"""
    question_id: int
    question_text: str
    question_type: str
    average_score: Decimal
    difficulty: str  # easy, medium, hard
    discrimination_index: Decimal
    answer_distribution: Dict[str, int]
    co_mappings: List[str]
    po_mappings: List[str]
    ai_accuracy_score: Optional[Decimal] = None

# Monitoring & Live Updates
class ExamMonitor(BaseModel):
    """Live exam monitoring dashboard"""
    total_students: int = Field(..., description="Enrolled students")
    joined_students: int = Field(..., description="Students who joined")
    active_students: int = Field(..., description="Currently active students")
    submitted_count: int = Field(..., description="Completed submissions")
    question_completion_rate: Dict[str, int] = Field({}, description="Questions answered by count")
    time_distribution: Dict[str, int] = Field({}, description="Time spent distribution")
    proctor_events_count: int = Field(..., description="Suspicious events count")

class StudentActivity(BaseModel):
    """Individual student activity"""
    student_id: int
    student_name: str
    status: str  # joined, active, submitted, disconnected
    current_question_index: Optional[int]
    time_spent_sec: int
    last_activity: datetime
    proctor_flags: List[str]
    network_status: str

# Bulk Operations
class BulkQuestionAssignment(BaseModel):
    """Assign multiple questions to exam"""
    question_ids: List[int] = Field(..., description="Questions to add")
    marks_override: Optional[int] = Field(None, description="Override marks for all")

class BulkResultsExport(BaseModel):
    """Results export configuration"""
    include_answers: bool = False
    include_metadata: bool = True
    format: str = Field("csv", description="Export format: csv, excel, pdf")
    include_analytics: bool = True

# System Events
class ExamLifecycleEvent(BaseModel):
    """Exam status change event"""
    exam_id: int
    event_type: str  # published, started, ended, results_published
    timestamp: datetime
    triggered_by: int
    details: Dict[str, Any]

# Validation
class JoinExamRequest(BaseModel):
    """Student join exam request"""
    session_token: Optional[str] = None
    browser_info: Dict[str, Any] = Field({}, description="Browser/device info")

class JoinExamResponse(BaseModel):
    """Join exam response"""
    access_token: str = Field(..., description="Exam-specific JWT")
    attempt_id: int
    exam_starts_in_sec: int
    settings: Dict[str, Any]
    instructions: str
    duration_minutes: int

# Error Responses
class ExamError(BaseModel):
    """Exam-related error"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    suggested_action: Optional[str] = None

# Real-time Communication
class WebSocketMessage(BaseModel):
    """WebSocket message schema"""
    type: str  # exam_update, time_warning, proctor_alert, system_message
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
