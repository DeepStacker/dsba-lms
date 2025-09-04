from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, text
from typing import List, Optional
from datetime import datetime, timedelta
import json
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.audit import log_audit_event, AUDIT_ACTIONS
from ..models.models import (
    User, Exam, ExamQuestion, Question, ClassSection, Course, 
    Attempt, Response, ProctorLog, ExamStatus, AttemptStatus, ProctorEventType
)
from ..schemas.exam import (
    ExamCreate, ExamUpdate, ExamResponse, ExamQuestionCreate, ExamQuestionResponse,
    ExamQuestionsAddRequest, AttemptCreate, AttemptResponse, ResponseCreate, ResponseResponse,
    ProctorLogCreate, ProctorLogResponse, ExamJoinRequest, ExamJoinResponse,
    ExamSubmitRequest, ExamMonitorResponse, ExamResultsResponse, StudentExamResponse
)
from ..schemas.common import Response as CommonResponse, BulkOperationResponse

router = APIRouter()

# ==================== EXAM CRUD ====================

@router.get("/", response_model=List[ExamResponse])
async def get_exams(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    status: Optional[ExamStatus] = None,
    class_id: Optional[int] = None,
    upcoming: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get exams with filtering"""
    query = select(Exam).options(
        selectinload(Exam.class_section).selectinload(ClassSection.course)
    )
    
    filters = []
    
    # Status filter
    if status:
        filters.append(Exam.status == status)
    
    # Class filter
    if class_id:
        filters.append(Exam.class_id == class_id)
    
    # Upcoming filter
    if upcoming is not None:
        now = datetime.utcnow()
        if upcoming:
            filters.append(Exam.start_at > now)
        else:
            filters.append(Exam.start_at <= now)
    
    # Role-based filtering
    if current_user.role.value == "student":
        # Students can only see exams for their enrolled classes
        from ..models.models import Enrollment
        enrolled_classes_query = select(Enrollment.class_id).where(Enrollment.student_id == current_user.id)
        enrolled_classes_result = await db.execute(enrolled_classes_query)
        enrolled_class_ids = [row[0] for row in enrolled_classes_result.fetchall()]
        
        if enrolled_class_ids:
            filters.append(Exam.class_id.in_(enrolled_class_ids))
        else:
            # No enrolled classes, return empty list
            return []
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(Exam.start_at.desc())
    result = await db.execute(query)
    exams = result.scalars().all()
    
    # Format response with additional data
    response_exams = []
    for exam in exams:
        # Get question count and total marks
        questions_result = await db.execute(
            select(func.count(ExamQuestion.id), func.sum(
                func.coalesce(ExamQuestion.marks_override, Question.max_marks)
            )).select_from(ExamQuestion).join(Question).where(ExamQuestion.exam_id == exam.id)
        )
        question_count, total_marks = questions_result.first() or (0, 0)
        
        exam_dict = ExamResponse.from_orm(exam).dict()
        exam_dict['total_questions'] = question_count
        exam_dict['total_marks'] = float(total_marks) if total_marks else 0.0
        exam_dict['class_name'] = exam.class_section.name if exam.class_section else None
        exam_dict['course_name'] = exam.class_section.course.title if exam.class_section and exam.class_section.course else None
        
        response_exams.append(ExamResponse(**exam_dict))
    
    return response_exams

@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    exam_data: ExamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("schedule_exams"))
):
    """Create a new exam"""
    # Verify class section exists
    class_result = await db.execute(
        select(ClassSection).options(selectinload(ClassSection.course)).where(ClassSection.id == exam_data.class_id)
    )
    class_section = class_result.scalar_one_or_none()
    
    if not class_section:
        raise HTTPException(status_code=404, detail="Class section not found")
    
    # Validate exam timing
    if exam_data.start_at <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam start time must be in the future"
        )
    
    # Create exam
    exam = Exam(**exam_data.dict())
    db.add(exam)
    await db.commit()
    await db.refresh(exam)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="exam",
        entity_id=exam.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=exam_data.dict(),
        reason="Created new exam"
    )
    
    # Load relationships for response
    result = await db.execute(
        select(Exam).options(
            selectinload(Exam.class_section).selectinload(ClassSection.course)
        ).where(Exam.id == exam.id)
    )
    exam = result.scalar_one()
    
    return ExamResponse.from_orm(exam)

@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get exam by ID"""
    result = await db.execute(
        select(Exam).options(
            selectinload(Exam.class_section).selectinload(ClassSection.course)
        ).where(Exam.id == exam_id)
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check access permissions
    if current_user.role.value == "student":
        # Check if student is enrolled in the class
        from ..models.models import Enrollment
        enrollment_result = await db.execute(
            select(Enrollment).where(
                and_(Enrollment.class_id == exam.class_id, Enrollment.student_id == current_user.id)
            )
        )
        if not enrollment_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this class"
            )
    
    # Get additional exam data
    questions_result = await db.execute(
        select(func.count(ExamQuestion.id), func.sum(
            func.coalesce(ExamQuestion.marks_override, Question.max_marks)
        )).select_from(ExamQuestion).join(Question).where(ExamQuestion.exam_id == exam_id)
    )
    question_count, total_marks = questions_result.first() or (0, 0)
    
    exam_dict = ExamResponse.from_orm(exam).dict()
    exam_dict['total_questions'] = question_count
    exam_dict['total_marks'] = float(total_marks) if total_marks else 0.0
    exam_dict['class_name'] = exam.class_section.name if exam.class_section else None
    exam_dict['course_name'] = exam.class_section.course.title if exam.class_section and exam.class_section.course else None
    
    return ExamResponse(**exam_dict)

@router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("schedule_exams"))
):
    """Update exam"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check if exam can be updated
    if exam.status in [ExamStatus.STARTED, ExamStatus.ENDED, ExamStatus.RESULTS_PUBLISHED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update exam that has started or ended"
        )
    
    before_data = {
        "title": exam.title,
        "start_at": exam.start_at.isoformat(),
        "end_at": exam.end_at.isoformat(),
        "status": exam.status.value
    }
    
    update_data = exam_data.dict(exclude_unset=True)
    
    # Validate timing if being updated
    if 'start_at' in update_data or 'end_at' in update_data:
        start_time = update_data.get('start_at', exam.start_at)
        end_time = update_data.get('end_at', exam.end_at)
        
        if start_time <= datetime.utcnow() and exam.status == ExamStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exam start time must be in the future"
            )
    
    for field, value in update_data.items():
        setattr(exam, field, value)
    
    await db.commit()
    await db.refresh(exam)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="exam",
        entity_id=exam.id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated exam"
    )
    
    # Load relationships for response
    result = await db.execute(
        select(Exam).options(
            selectinload(Exam.class_section).selectinload(ClassSection.course)
        ).where(Exam.id == exam_id)
    )
    exam = result.scalar_one()
    
    return ExamResponse.from_orm(exam)

@router.delete("/{exam_id}")
async def delete_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("schedule_exams"))
):
    """Delete exam"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check if exam can be deleted
    if exam.status not in [ExamStatus.DRAFT]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete draft exams"
        )
    
    # Check if exam has attempts
    attempts_result = await db.execute(select(Attempt).where(Attempt.exam_id == exam_id))
    if attempts_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete exam with existing attempts"
        )
    
    before_data = {"title": exam.title, "status": exam.status.value}
    await db.delete(exam)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="exam",
        entity_id=exam_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted exam"
    )
    
    return CommonResponse(message="Exam deleted successfully")

# ==================== EXAM QUESTIONS ====================

@router.get("/{exam_id}/questions", response_model=List[ExamQuestionResponse])
async def get_exam_questions(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all questions for an exam"""
    # Verify exam exists and user has access
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Get exam questions with question details
    result = await db.execute(
        select(ExamQuestion, Question.text, Question.type, Question.max_marks)
        .join(Question)
        .where(ExamQuestion.exam_id == exam_id)
        .order_by(ExamQuestion.order)
    )
    
    exam_questions = []
    for eq, q_text, q_type, q_max_marks in result.all():
        eq_dict = ExamQuestionResponse.from_orm(eq).dict()
        eq_dict['question_text'] = q_text
        eq_dict['question_type'] = q_type.value
        eq_dict['max_marks'] = float(q_max_marks)
        exam_questions.append(ExamQuestionResponse(**eq_dict))
    
    return exam_questions

@router.post("/{exam_id}/questions", response_model=List[ExamQuestionResponse])
async def add_questions_to_exam(
    exam_id: int,
    questions_request: ExamQuestionsAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("schedule_exams"))
):
    """Add questions to an exam"""
    # Verify exam exists and can be modified
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if exam.status != ExamStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only add questions to draft exams"
        )
    
    # Verify all questions exist
    questions_result = await db.execute(
        select(Question).where(Question.id.in_(questions_request.question_ids))
    )
    questions = {q.id: q for q in questions_result.scalars().all()}
    
    missing_questions = set(questions_request.question_ids) - set(questions.keys())
    if missing_questions:
        raise HTTPException(
            status_code=404,
            detail=f"Questions not found: {list(missing_questions)}"
        )
    
    # Get current max order
    max_order_result = await db.execute(
        select(func.max(ExamQuestion.order)).where(ExamQuestion.exam_id == exam_id)
    )
    max_order = max_order_result.scalar() or 0
    
    # Add questions to exam
    exam_questions = []
    for i, question_id in enumerate(questions_request.question_ids):
        # Check if question already exists in exam
        existing_result = await db.execute(
            select(ExamQuestion).where(
                and_(ExamQuestion.exam_id == exam_id, ExamQuestion.question_id == question_id)
            )
        )
        if existing_result.scalar_one_or_none():
            continue  # Skip if already exists
        
        marks_override = None
        if questions_request.marks_overrides:
            marks_override = questions_request.marks_overrides.get(question_id)
        
        exam_question = ExamQuestion(
            exam_id=exam_id,
            question_id=question_id,
            order=max_order + i + 1,
            marks_override=marks_override
        )
        
        db.add(exam_question)
        exam_questions.append(exam_question)
    
    await db.commit()
    
    # Refresh and return exam questions
    for eq in exam_questions:
        await db.refresh(eq)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="exam",
        entity_id=exam_id,
        action=AUDIT_ACTIONS["UPDATE"],
        after_json={
            "questions_added": len(exam_questions),
            "question_ids": questions_request.question_ids
        },
        reason="Added questions to exam"
    )
    
    # Get updated exam questions list
    result = await db.execute(
        select(ExamQuestion, Question.text, Question.type, Question.max_marks)
        .join(Question)
        .where(ExamQuestion.exam_id == exam_id)
        .order_by(ExamQuestion.order)
    )
    
    response_questions = []
    for eq, q_text, q_type, q_max_marks in result.all():
        eq_dict = ExamQuestionResponse.from_orm(eq).dict()
        eq_dict['question_text'] = q_text
        eq_dict['question_type'] = q_type.value
        eq_dict['max_marks'] = float(q_max_marks)
        response_questions.append(ExamQuestionResponse(**eq_dict))
    
    return response_questions

@router.delete("/{exam_id}/questions/{question_id}")
async def remove_question_from_exam(
    exam_id: int,
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("schedule_exams"))
):
    """Remove a question from an exam"""
    # Verify exam exists and can be modified
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if exam.status != ExamStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only remove questions from draft exams"
        )
    
    # Find and remove exam question
    result = await db.execute(
        select(ExamQuestion).where(
            and_(ExamQuestion.exam_id == exam_id, ExamQuestion.question_id == question_id)
        )
    )
    exam_question = result.scalar_one_or_none()
    
    if not exam_question:
        raise HTTPException(status_code=404, detail="Question not found in exam")
    
    await db.delete(exam_question)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="exam",
        entity_id=exam_id,
        action=AUDIT_ACTIONS["UPDATE"],
        after_json={"question_removed": question_id},
        reason="Removed question from exam"
    )
    
    return CommonResponse(message="Question removed from exam successfully")

# ==================== EXAM LIFECYCLE ====================

@router.post("/{exam_id}/publish")
async def publish_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("schedule_exams"))
):
    """Publish an exam"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if exam.status != ExamStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only publish draft exams"
        )
    
    # Verify exam has questions
    questions_result = await db.execute(
        select(func.count(ExamQuestion.id)).where(ExamQuestion.exam_id == exam_id)
    )
    question_count = questions_result.scalar()
    
    if question_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish exam without questions"
        )
    
    # Verify exam timing is valid
    if exam.start_at <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish exam with past start time"
        )
    
    exam.status = ExamStatus.PUBLISHED
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="exam",
        entity_id=exam_id,
        action=AUDIT_ACTIONS["PUBLISH"],
        after_json={"status": "published"},
        reason="Published exam"
    )
    
    return CommonResponse(message="Exam published successfully")

@router.post("/{exam_id}/start")
async def start_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("start_end_exam"))
):
    """Start an exam"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if exam.status != ExamStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only start published exams"
        )
    
    # Check if it's time to start the exam
    now = datetime.utcnow()
    if now < exam.start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam start time has not arrived yet"
        )
    
    exam.status = ExamStatus.STARTED
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="exam",
        entity_id=exam_id,
        action=AUDIT_ACTIONS["START"],
        after_json={"status": "started", "started_at": now.isoformat()},
        reason="Started exam"
    )
    
    return CommonResponse(message="Exam started successfully")

@router.post("/{exam_id}/end")
async def end_exam(
    exam_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("start_end_exam"))
):
    """End an exam and auto-submit all active attempts"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if exam.status != ExamStatus.STARTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only end started exams"
        )
    
    now = datetime.utcnow()
    
    # Auto-submit all active attempts
    active_attempts_result = await db.execute(
        select(Attempt).where(
            and_(
                Attempt.exam_id == exam_id,
                Attempt.status == AttemptStatus.IN_PROGRESS
            )
        )
    )
    active_attempts = active_attempts_result.scalars().all()
    
    for attempt in active_attempts:
        attempt.status = AttemptStatus.AUTO_SUBMITTED
        attempt.submitted_at = now
        attempt.autosubmitted = True
    
    exam.status = ExamStatus.ENDED
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="exam",
        entity_id=exam_id,
        action=AUDIT_ACTIONS["END"],
        after_json={
            "status": "ended",
            "ended_at": now.isoformat(),
            "auto_submitted_attempts": len(active_attempts)
        },
        reason="Ended exam"
    )
    
    return CommonResponse(
        message=f"Exam ended successfully. {len(active_attempts)} attempts auto-submitted."
    )

# ==================== STUDENT EXAM OPERATIONS ====================

@router.get("/student/available", response_model=List[StudentExamResponse])
async def get_student_exams(
    upcoming: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available exams for a student"""
    if current_user.role.value != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    # Get enrolled classes
    from ..models.models import Enrollment
    enrolled_classes_result = await db.execute(
        select(Enrollment.class_id).where(Enrollment.student_id == current_user.id)
    )
    enrolled_class_ids = [row[0] for row in enrolled_classes_result.fetchall()]
    
    if not enrolled_class_ids:
        return []
    
    # Get exams for enrolled classes
    query = select(Exam).options(
        selectinload(Exam.class_section).selectinload(ClassSection.course)
    ).where(Exam.class_id.in_(enrolled_class_ids))
    
    # Filter by upcoming if specified
    if upcoming is not None:
        now = datetime.utcnow()
        if upcoming:
            query = query.where(Exam.start_at > now)
        else:
            query = query.where(Exam.start_at <= now)
    
    # Only show published or started exams
    query = query.where(Exam.status.in_([ExamStatus.PUBLISHED, ExamStatus.STARTED, ExamStatus.ENDED]))
    query = query.order_by(Exam.start_at)
    
    result = await db.execute(query)
    exams = result.scalars().all()
    
    # Get student's attempts for these exams
    attempts_result = await db.execute(
        select(Attempt).where(
            and_(
                Attempt.student_id == current_user.id,
                Attempt.exam_id.in_([exam.id for exam in exams])
            )
        )
    )
    attempts_by_exam = {attempt.exam_id: attempt for attempt in attempts_result.scalars().all()}
    
    # Format response
    student_exams = []
    now = datetime.utcnow()
    
    for exam in exams:
        attempt = attempts_by_exam.get(exam.id)
        
        # Calculate if student can join/attempt
        can_join = (
            exam.status == ExamStatus.STARTED and
            now >= exam.start_at and
            now <= (exam.start_at + timedelta(seconds=exam.join_window_sec)) and
            (not attempt or attempt.status == AttemptStatus.NOT_STARTED)
        )
        
        can_attempt = (
            exam.status == ExamStatus.STARTED and
            now <= exam.end_at and
            attempt and attempt.status == AttemptStatus.IN_PROGRESS
        )
        
        # Get total marks
        marks_result = await db.execute(
            select(func.sum(func.coalesce(ExamQuestion.marks_override, Question.max_marks)))
            .select_from(ExamQuestion).join(Question)
            .where(ExamQuestion.exam_id == exam.id)
        )
        total_marks = marks_result.scalar() or 0
        
        # Get obtained marks if attempt exists and is graded
        obtained_marks = None
        if attempt and attempt.status in [AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]:
            responses_result = await db.execute(
                select(func.sum(Response.final_score))
                .where(Response.attempt_id == attempt.id)
            )
            obtained_marks = responses_result.scalar()
        
        duration_minutes = int((exam.end_at - exam.start_at).total_seconds() / 60)
        
        student_exam = StudentExamResponse(
            id=exam.id,
            title=exam.title,
            start_at=exam.start_at,
            end_at=exam.end_at,
            status=exam.status,
            duration_minutes=duration_minutes,
            total_marks=float(total_marks),
            can_join=can_join,
            can_attempt=can_attempt,
            attempt_status=attempt.status if attempt else None,
            obtained_marks=float(obtained_marks) if obtained_marks else None,
            class_name=exam.class_section.name,
            course_name=exam.class_section.course.title
        )
        
        student_exams.append(student_exam)
    
    return student_exams

@router.post("/{exam_id}/join", response_model=ExamJoinResponse)
async def join_exam(
    exam_id: int,
    join_request: ExamJoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Join an exam (student only)"""
    if current_user.role.value != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can join exams"
        )
    
    # Get exam with class info
    result = await db.execute(
        select(Exam).options(selectinload(Exam.class_section)).where(Exam.id == exam_id)
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check if student is enrolled in the class
    from ..models.models import Enrollment
    enrollment_result = await db.execute(
        select(Enrollment).where(
            and_(Enrollment.class_id == exam.class_id, Enrollment.student_id == current_user.id)
        )
    )
    if not enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this class"
        )
    
    # Check exam status and timing
    now = datetime.utcnow()
    
    if exam.status != ExamStatus.STARTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam is not currently active"
        )
    
    # Check join window
    join_deadline = exam.start_at + timedelta(seconds=exam.join_window_sec)
    if now > join_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Join window has expired"
        )
    
    # Check if student already has an attempt
    attempt_result = await db.execute(
        select(Attempt).where(
            and_(Attempt.exam_id == exam_id, Attempt.student_id == current_user.id)
        )
    )
    attempt = attempt_result.scalar_one_or_none()
    
    if attempt:
        if attempt.status == AttemptStatus.IN_PROGRESS:
            # Student can continue existing attempt
            pass
        elif attempt.status in [AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exam already submitted"
            )
    else:
        # Create new attempt
        attempt = Attempt(
            exam_id=exam_id,
            student_id=current_user.id,
            started_at=now,
            status=AttemptStatus.IN_PROGRESS
        )
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)
    
    # Get exam questions
    questions_result = await db.execute(
        select(ExamQuestion, Question)
        .join(Question)
        .where(ExamQuestion.exam_id == exam_id)
        .order_by(ExamQuestion.order)
    )
    
    exam_questions = []
    for eq, question in questions_result.all():
        # Don't include correct answers for students
        eq_dict = ExamQuestionResponse.from_orm(eq).dict()
        eq_dict['question_text'] = question.text
        eq_dict['question_type'] = question.type.value
        eq_dict['max_marks'] = float(eq.marks_override or question.max_marks)
        exam_questions.append(ExamQuestionResponse(**eq_dict))
    
    # Calculate time remaining
    time_remaining = int((exam.end_at - now).total_seconds())
    if time_remaining < 0:
        time_remaining = 0
    
    # Get exam settings
    settings = exam.settings_json or {}
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="attempt",
        entity_id=attempt.id,
        action=AUDIT_ACTIONS["START"],
        after_json={"exam_id": exam_id, "joined_at": now.isoformat()},
        reason="Joined exam"
    )
    
    return ExamJoinResponse(
        attempt_id=attempt.id,
        exam_id=exam_id,
        questions=exam_questions,
        time_remaining=time_remaining,
        settings=settings,
        websocket_url=f"/ws/exam/{exam_id}/attempt/{attempt.id}"
    )

@router.post("/attempts/{attempt_id}/submit")
async def submit_exam(
    attempt_id: int,
    submit_request: ExamSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an exam attempt"""
    if current_user.role.value != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit exams"
        )
    
    # Get attempt
    result = await db.execute(
        select(Attempt).options(selectinload(Attempt.exam)).where(Attempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only submit your own attempts"
        )
    
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt is not in progress"
        )
    
    # Check if exam time has expired
    now = datetime.utcnow()
    if now > attempt.exam.end_at:
        attempt.status = AttemptStatus.AUTO_SUBMITTED
        attempt.autosubmitted = True
    else:
        attempt.status = AttemptStatus.SUBMITTED
    
    attempt.submitted_at = now
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="attempt",
        entity_id=attempt_id,
        action=AUDIT_ACTIONS["SUBMIT"],
        after_json={
            "submitted_at": now.isoformat(),
            "auto_submitted": attempt.autosubmitted
        },
        reason="Submitted exam"
    )
    
    return CommonResponse(message="Exam submitted successfully")

# ==================== EXAM MONITORING ====================

@router.get("/{exam_id}/monitor", response_model=ExamMonitorResponse)
async def monitor_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("monitor_live_exams"))
):
    """Monitor live exam status"""
    # Get exam
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Get enrolled students count
    from ..models.models import Enrollment
    total_students_result = await db.execute(
        select(func.count(Enrollment.id)).where(Enrollment.class_id == exam.class_id)
    )
    total_students = total_students_result.scalar() or 0
    
    # Get attempt statistics
    attempts_result = await db.execute(
        select(Attempt.status, func.count(Attempt.id))
        .where(Attempt.exam_id == exam_id)
        .group_by(Attempt.status)
    )
    
    status_counts = {status.value: 0 for status in AttemptStatus}
    for status, count in attempts_result.all():
        status_counts[status.value] = count
    
    # Get active attempts with student details
    active_attempts_result = await db.execute(
        select(Attempt, User.name)
        .join(User, Attempt.student_id == User.id)
        .where(
            and_(
                Attempt.exam_id == exam_id,
                Attempt.status == AttemptStatus.IN_PROGRESS
            )
        )
    )
    
    active_attempts = []
    for attempt, student_name in active_attempts_result.all():
        attempt_dict = AttemptResponse.from_orm(attempt).dict()
        attempt_dict['student_name'] = student_name
        active_attempts.append(AttemptResponse(**attempt_dict))
    
    # Get recent proctor events
    recent_events_result = await db.execute(
        select(ProctorLog)
        .join(Attempt, ProctorLog.attempt_id == Attempt.id)
        .where(Attempt.exam_id == exam_id)
        .order_by(ProctorLog.ts.desc())
        .limit(20)
    )
    recent_events = [ProctorLogResponse.from_orm(log) for log in recent_events_result.scalars().all()]
    
    # Calculate time remaining
    now = datetime.utcnow()
    time_remaining = int((exam.end_at - now).total_seconds()) if exam.end_at > now else 0
    
    return ExamMonitorResponse(
        exam_id=exam_id,
        total_students=total_students,
        joined_count=status_counts.get('in_progress', 0) + status_counts.get('submitted', 0) + status_counts.get('auto_submitted', 0),
        active_count=status_counts.get('in_progress', 0),
        submitted_count=status_counts.get('submitted', 0),
        auto_submitted_count=status_counts.get('auto_submitted', 0),
        time_remaining=time_remaining,
        active_attempts=active_attempts,
        recent_events=recent_events
    )

# ==================== EXAM RESULTS ====================

@router.get("/{exam_id}/results", response_model=ExamResultsResponse)
async def get_exam_results(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_class_analytics"))
):
    """Get exam results"""
    # Get exam
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Get enrolled students count
    from ..models.models import Enrollment
    total_students_result = await db.execute(
        select(func.count(Enrollment.id)).where(Enrollment.class_id == exam.class_id)
    )
    total_students = total_students_result.scalar() or 0
    
    # Get all attempts with student details and scores
    attempts_result = await db.execute(
        select(
            Attempt,
            User.name,
            func.sum(Response.final_score).label('obtained_marks')
        )
        .join(User, Attempt.student_id == User.id)
        .outerjoin(Response, Response.attempt_id == Attempt.id)
        .where(Attempt.exam_id == exam_id)
        .group_by(Attempt.id, User.name)
        .order_by(func.sum(Response.final_score).desc().nullslast())
    )
    
    results = []
    submitted_count = 0
    graded_count = 0
    scores = []
    
    for attempt, student_name, obtained_marks in attempts_result.all():
        if attempt.status in [AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]:
            submitted_count += 1
            
            if obtained_marks is not None:
                graded_count += 1
                scores.append(float(obtained_marks))
        
        attempt_dict = AttemptResponse.from_orm(attempt).dict()
        attempt_dict['student_name'] = student_name
        attempt_dict['obtained_marks'] = float(obtained_marks) if obtained_marks else None
        results.append(AttemptResponse(**attempt_dict))
    
    # Calculate statistics
    average_score = sum(scores) / len(scores) if scores else None
    highest_score = max(scores) if scores else None
    lowest_score = min(scores) if scores else None
    
    return ExamResultsResponse(
        exam_id=exam_id,
        exam_title=exam.title,
        total_students=total_students,
        submitted_count=submitted_count,
        graded_count=graded_count,
        average_score=round(average_score, 2) if average_score else None,
        highest_score=round(highest_score, 2) if highest_score else None,
        lowest_score=round(lowest_score, 2) if lowest_score else None,
        results=results
    )

@router.post("/{exam_id}/results/publish")
async def publish_exam_results(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Publish exam results"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if exam.status != ExamStatus.ENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only publish results for ended exams"
        )
    
    # Check if all responses are graded
    ungraded_result = await db.execute(
        select(func.count(Response.id))
        .join(Attempt, Response.attempt_id == Attempt.id)
        .where(
            and_(
                Attempt.exam_id == exam_id,
                Response.final_score.is_(None)
            )
        )
    )
    ungraded_count = ungraded_result.scalar()
    
    if ungraded_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish results. {ungraded_count} responses are not graded yet."
        )
    
    exam.status = ExamStatus.RESULTS_PUBLISHED
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="exam",
        entity_id=exam_id,
        action=AUDIT_ACTIONS["PUBLISH_RESULTS"],
        after_json={"status": "results_published"},
        reason="Published exam results"
    )
    
    return CommonResponse(message="Exam results published successfully")