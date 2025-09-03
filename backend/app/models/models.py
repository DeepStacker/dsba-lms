from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List
import enum

class Base(DeclarativeBase):
    pass

class Role(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    COORDINATOR = "coordinator"

class QuestionType(enum.Enum):
    MCQ = "mcq"
    MSQ = "msq"
    TF = "tf"
    NUMERIC = "numeric"
    DESCRIPTIVE = "descriptive"
    CODING = "coding"
    FILE_UPLOAD = "file_upload"

class ExamStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    STARTED = "started"
    ENDED = "ended"
    RESULTS_PUBLISHED = "results_published"

class AttemptStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    AUTO_SUBMITTED = "auto_submitted"

class ProctorEventType(enum.Enum):
    TAB_SWITCH = "tab_switch"
    FOCUS_LOSS = "focus_loss"
    NETWORK_DROP = "network_drop"
    PASTE = "paste"
    FULLSCREEN_EXIT = "fullscreen_exit"

class LockStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    OVERRIDDEN = "overridden"

class Program(Base):
    __tablename__ = "programs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    pos: Mapped[List["PO"]] = relationship("PO", back_populates="program")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="program")

class PO(Base):
    __tablename__ = "pos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("programs.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    program: Mapped["Program"] = relationship("Program", back_populates="pos")
    co_po_maps: Mapped[List["CO_PO_Map"]] = relationship("CO_PO_Map", back_populates="po")

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("programs.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    program: Mapped["Program"] = relationship("Program", back_populates="courses")
    cos: Mapped[List["CO"]] = relationship("CO", back_populates="course")
    class_sections: Mapped[List["ClassSection"]] = relationship("ClassSection", back_populates="course")
    internal_components: Mapped[List["InternalComponent"]] = relationship("InternalComponent", back_populates="course")

class CO(Base):
    __tablename__ = "cos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    bloom: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    course: Mapped["Course"] = relationship("Course", back_populates="cos")
    co_po_maps: Mapped[List["CO_PO_Map"]] = relationship("CO_PO_Map", back_populates="co")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="co")

class CO_PO_Map(Base):
    __tablename__ = "co_po_maps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    co_id: Mapped[int] = mapped_column(Integer, ForeignKey("cos.id"), nullable=False)
    po_id: Mapped[int] = mapped_column(Integer, ForeignKey("pos.id"), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    co: Mapped["CO"] = relationship("CO", back_populates="co_po_maps")
    po: Mapped["PO"] = relationship("PO", back_populates="co_po_maps")

class ClassSection(Base):
    __tablename__ = "class_sections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    term: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    course: Mapped["Course"] = relationship("Course", back_populates="class_sections")
    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="class_section")
    exams: Mapped[List["Exam"]] = relationship("Exam", back_populates="class_section")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.STUDENT)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    meta_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Self-referential relationship for creator
    creator: Mapped[Optional["User"]] = relationship("User", remote_side=[id])

    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="student")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="creator")
    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="student")
    grade_upload_batches: Mapped[List["GradeUploadBatch"]] = relationship("GradeUploadBatch", back_populates="uploader")
    internal_scores: Mapped[List["InternalScore"]] = relationship("InternalScore", back_populates="student")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="actor")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("class_sections.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    enrolled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    class_section: Mapped["ClassSection"] = relationship("ClassSection", back_populates="enrollments")
    student: Mapped["User"] = relationship("User", back_populates="enrollments")

class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    co_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cos.id"))
    max_marks: Mapped[float] = mapped_column(Float, nullable=False)
    rubric_json: Mapped[Optional[dict]] = mapped_column(JSON)
    model_answer: Mapped[Optional[str]] = mapped_column(Text)
    meta: Mapped[Optional[dict]] = mapped_column(JSON)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    co: Mapped[Optional["CO"]] = relationship("CO", back_populates="questions")
    creator: Mapped["User"] = relationship("User", back_populates="questions")
    options: Mapped[List["QuestionOption"]] = relationship("QuestionOption", back_populates="question")
    exam_questions: Mapped[List["ExamQuestion"]] = relationship("ExamQuestion", back_populates="question")

class QuestionOption(Base):
    __tablename__ = "question_options"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    question: Mapped["Question"] = relationship("Question", back_populates="options")

class Exam(Base):
    __tablename__ = "exams"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("class_sections.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    join_window_sec: Mapped[int] = mapped_column(Integer, default=300)
    settings_json: Mapped[Optional[dict]] = mapped_column(JSON)
    status: Mapped[ExamStatus] = mapped_column(Enum(ExamStatus), default=ExamStatus.DRAFT)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    class_section: Mapped["ClassSection"] = relationship("ClassSection", back_populates="exams")
    exam_questions: Mapped[List["ExamQuestion"]] = relationship("ExamQuestion", back_populates="exam")
    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="exam")
    grade_upload_batches: Mapped[List["GradeUploadBatch"]] = relationship("GradeUploadBatch", back_populates="exam")

class ExamQuestion(Base):
    __tablename__ = "exam_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(Integer, ForeignKey("exams.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    marks_override: Mapped[Optional[float]] = mapped_column(Float)

    exam: Mapped["Exam"] = relationship("Exam", back_populates="exam_questions")
    question: Mapped["Question"] = relationship("Question", back_populates="exam_questions")

class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    started_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[AttemptStatus] = mapped_column(Enum(AttemptStatus), default=AttemptStatus.NOT_STARTED)
    autosubmitted: Mapped[bool] = mapped_column(Boolean, default=False)

    exam: Mapped["Exam"] = relationship("Exam", back_populates="attempts")
    student: Mapped["User"] = relationship("User", back_populates="attempts")
    responses: Mapped[List["Response"]] = relationship("Response", back_populates="attempt")
    proctor_logs: Mapped[List["ProctorLog"]] = relationship("ProctorLog", back_populates="attempt")

class Response(Base):
    __tablename__ = "responses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    attempt_id: Mapped[int] = mapped_column(Integer, ForeignKey("attempts.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    ai_score: Mapped[Optional[float]] = mapped_column(Float)
    teacher_score: Mapped[Optional[float]] = mapped_column(Float)
    final_score: Mapped[Optional[float]] = mapped_column(Float)
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    audit_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="responses")

class ProctorLog(Base):
    __tablename__ = "proctor_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    attempt_id: Mapped[int] = mapped_column(Integer, ForeignKey("attempts.id"), nullable=False)
    ts: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    event_type: Mapped[ProctorEventType] = mapped_column(Enum(ProctorEventType), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON)

    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="proctor_logs")

class GradeUploadBatch(Base):
    __tablename__ = "grade_upload_batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(Integer, ForeignKey("exams.id"), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[Optional[str]] = mapped_column(Text)

    exam: Mapped["Exam"] = relationship("Exam", back_populates="grade_upload_batches")
    uploader: Mapped["User"] = relationship("User", back_populates="grade_upload_batches")

class InternalComponent(Base):
    __tablename__ = "internal_components"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight_percent: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped["Course"] = relationship("Course", back_populates="internal_components")
    internal_scores: Mapped[List["InternalScore"]] = relationship("InternalScore", back_populates="component")

class InternalScore(Base):
    __tablename__ = "internal_scores"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    component_id: Mapped[int] = mapped_column(Integer, ForeignKey("internal_components.id"), nullable=False)
    raw_score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped["User"] = relationship("User", back_populates="internal_scores")
    component: Mapped["InternalComponent"] = relationship("InternalComponent", back_populates="internal_scores")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ts: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    before_json: Mapped[Optional[dict]] = mapped_column(JSON)
    after_json: Mapped[Optional[dict]] = mapped_column(JSON)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prev_hash: Mapped[Optional[str]] = mapped_column(String(64))

    actor: Mapped["User"] = relationship("User", back_populates="audit_logs")

class LockWindow(Base):
    __tablename__ = "lock_windows"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scope: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[LockStatus] = mapped_column(Enum(LockStatus), default=LockStatus.ACTIVE)
    policy_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
