from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, text
from typing import List, Optional
import json
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.audit import log_audit_event, AUDIT_ACTIONS
from ..models.models import User, Question, QuestionOption, CO, Course, QuestionType
from ..schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionSearchRequest,
    QuestionOptionCreate, QuestionOptionUpdate, QuestionOptionResponse,
    QuestionBulkImportRequest, QuestionStatsResponse,
    AIQuestionGenerationRequest, AIQuestionGenerationResponse,
    RubricCreate, RubricResponse
)
from ..schemas.common import Response, BulkOperationResponse
import httpx
from ..core.config import settings

router = APIRouter()

# ==================== QUESTIONS CRUD ====================

@router.get("/", response_model=List[QuestionResponse])
async def get_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    type: Optional[QuestionType] = None,
    co_id: Optional[int] = None,
    course_id: Optional[int] = None,
    created_by: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get questions with filtering"""
    query = select(Question).options(
        selectinload(Question.options),
        selectinload(Question.creator),
        selectinload(Question.co)
    )
    
    # Apply filters
    filters = []
    if type:
        filters.append(Question.type == type)
    if co_id:
        filters.append(Question.co_id == co_id)
    if created_by:
        filters.append(Question.created_by == created_by)
    if search:
        filters.append(Question.text.ilike(f"%{search}%"))
    
    # Course filter through CO relationship
    if course_id:
        query = query.join(CO, Question.co_id == CO.id)
        filters.append(CO.course_id == course_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(Question.created_at.desc())
    result = await db.execute(query)
    questions = result.scalars().all()
    
    # Format response with additional data
    response_questions = []
    for question in questions:
        q_dict = QuestionResponse.from_orm(question).dict()
        q_dict['creator_name'] = question.creator.name if question.creator else None
        q_dict['co_code'] = question.co.code if question.co else None
        response_questions.append(QuestionResponse(**q_dict))
    
    return response_questions

@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("create_questions"))
):
    """Create a new question"""
    # Verify CO exists if provided
    if question_data.co_id:
        co_result = await db.execute(select(CO).where(CO.id == question_data.co_id))
        if not co_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="CO not found")
    
    # Create question
    question_dict = question_data.dict(exclude={'options'})
    question_dict['created_by'] = current_user.id
    question = Question(**question_dict)
    
    db.add(question)
    await db.flush()  # Get question ID
    
    # Add options if provided
    if question_data.options:
        for option_data in question_data.options:
            option = QuestionOption(
                question_id=question.id,
                **option_data.dict()
            )
            db.add(option)
    
    await db.commit()
    await db.refresh(question)
    
    # Load relationships for response
    result = await db.execute(
        select(Question).options(
            selectinload(Question.options),
            selectinload(Question.creator),
            selectinload(Question.co)
        ).where(Question.id == question.id)
    )
    question = result.scalar_one()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="question",
        entity_id=question.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=question_data.dict(),
        reason="Created new question"
    )
    
    return QuestionResponse.from_orm(question)

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get question by ID"""
    result = await db.execute(
        select(Question).options(
            selectinload(Question.options),
            selectinload(Question.creator),
            selectinload(Question.co)
        ).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return QuestionResponse.from_orm(question)

@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("edit_questions"))
):
    """Update question"""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if user can edit this question
    if question.created_by != current_user.id and not current_user.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only edit your own questions"
        )
    
    # Verify CO exists if provided
    if question_data.co_id:
        co_result = await db.execute(select(CO).where(CO.id == question_data.co_id))
        if not co_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="CO not found")
    
    before_data = {
        "text": question.text,
        "type": question.type.value,
        "max_marks": question.max_marks,
        "co_id": question.co_id
    }
    
    update_data = question_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
    
    await db.commit()
    await db.refresh(question)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="question",
        entity_id=question.id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated question"
    )
    
    # Load relationships for response
    result = await db.execute(
        select(Question).options(
            selectinload(Question.options),
            selectinload(Question.creator),
            selectinload(Question.co)
        ).where(Question.id == question_id)
    )
    question = result.scalar_one()
    
    return QuestionResponse.from_orm(question)

@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("edit_questions"))
):
    """Delete question"""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if user can delete this question
    if question.created_by != current_user.id and not current_user.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own questions"
        )
    
    # Check if question is used in any exams
    from ..models.models import ExamQuestion
    exam_usage = await db.execute(select(ExamQuestion).where(ExamQuestion.question_id == question_id))
    if exam_usage.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete question that is used in exams"
        )
    
    before_data = {"text": question.text, "type": question.type.value}
    await db.delete(question)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="question",
        entity_id=question_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted question"
    )
    
    return Response(message="Question deleted successfully")

# ==================== QUESTION OPTIONS ====================

@router.post("/{question_id}/options", response_model=QuestionOptionResponse, status_code=status.HTTP_201_CREATED)
async def add_question_option(
    question_id: int,
    option_data: QuestionOptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("edit_questions"))
):
    """Add option to a question"""
    # Verify question exists and user can edit it
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.created_by != current_user.id and not current_user.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only edit your own questions"
        )
    
    # Check if question type supports options
    if question.type not in [QuestionType.MCQ, QuestionType.MSQ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question type does not support options"
        )
    
    option = QuestionOption(
        question_id=question_id,
        **option_data.dict()
    )
    
    db.add(option)
    await db.commit()
    await db.refresh(option)
    
    return QuestionOptionResponse.from_orm(option)

@router.put("/options/{option_id}", response_model=QuestionOptionResponse)
async def update_question_option(
    option_id: int,
    option_data: QuestionOptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("edit_questions"))
):
    """Update question option"""
    result = await db.execute(
        select(QuestionOption, Question).join(Question).where(QuestionOption.id == option_id)
    )
    option_question = result.first()
    
    if not option_question:
        raise HTTPException(status_code=404, detail="Option not found")
    
    option, question = option_question
    
    if question.created_by != current_user.id and not current_user.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only edit your own questions"
        )
    
    update_data = option_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(option, field, value)
    
    await db.commit()
    await db.refresh(option)
    
    return QuestionOptionResponse.from_orm(option)

@router.delete("/options/{option_id}")
async def delete_question_option(
    option_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("edit_questions"))
):
    """Delete question option"""
    result = await db.execute(
        select(QuestionOption, Question).join(Question).where(QuestionOption.id == option_id)
    )
    option_question = result.first()
    
    if not option_question:
        raise HTTPException(status_code=404, detail="Option not found")
    
    option, question = option_question
    
    if question.created_by != current_user.id and not current_user.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only edit your own questions"
        )
    
    await db.delete(option)
    await db.commit()
    
    return Response(message="Option deleted successfully")

# ==================== QUESTION SEARCH ====================

@router.post("/search", response_model=List[QuestionResponse])
async def search_questions(
    search_request: QuestionSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advanced question search"""
    query = select(Question).options(
        selectinload(Question.options),
        selectinload(Question.creator),
        selectinload(Question.co)
    )
    
    filters = []
    
    # Text search
    if search_request.query:
        filters.append(
            or_(
                Question.text.ilike(f"%{search_request.query}%"),
                Question.model_answer.ilike(f"%{search_request.query}%")
            )
        )
    
    # Type filter
    if search_request.type:
        filters.append(Question.type == search_request.type)
    
    # CO filter
    if search_request.co_id:
        filters.append(Question.co_id == search_request.co_id)
    
    # Course filter through CO
    if search_request.course_id:
        query = query.join(CO, Question.co_id == CO.id)
        filters.append(CO.course_id == search_request.course_id)
    
    # Creator filter
    if search_request.created_by:
        filters.append(Question.created_by == search_request.created_by)
    
    # Bloom level filter (from CO)
    if search_request.bloom_level:
        if not search_request.course_id:  # Join CO if not already joined
            query = query.join(CO, Question.co_id == CO.id)
        filters.append(CO.bloom == search_request.bloom_level.lower())
    
    # Marks range filter
    if search_request.max_marks_min:
        filters.append(Question.max_marks >= search_request.max_marks_min)
    if search_request.max_marks_max:
        filters.append(Question.max_marks <= search_request.max_marks_max)
    
    # Difficulty filter (from meta JSON)
    if search_request.difficulty:
        filters.append(
            Question.meta['difficulty'].astext == search_request.difficulty
        )
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(search_request.skip).limit(search_request.limit)
    query = query.order_by(Question.created_at.desc())
    
    result = await db.execute(query)
    questions = result.scalars().all()
    
    return [QuestionResponse.from_orm(q) for q in questions]

# ==================== QUESTION STATISTICS ====================

@router.get("/stats/course/{course_id}", response_model=QuestionStatsResponse)
async def get_question_stats(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get question statistics for a course"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get all questions for the course through COs
    questions_query = select(Question).join(CO).where(CO.course_id == course_id)
    result = await db.execute(questions_query)
    questions = result.scalars().all()
    
    # Calculate statistics
    total_questions = len(questions)
    
    # By type
    by_type = {}
    for q_type in QuestionType:
        count = len([q for q in questions if q.type == q_type])
        by_type[q_type.value] = count
    
    # By bloom level (from CO)
    cos_result = await db.execute(select(CO).where(CO.course_id == course_id))
    cos = cos_result.scalars().all()
    co_bloom_map = {co.id: co.bloom for co in cos}
    
    by_bloom_level = {}
    for question in questions:
        if question.co_id and question.co_id in co_bloom_map:
            bloom = co_bloom_map[question.co_id]
            by_bloom_level[bloom] = by_bloom_level.get(bloom, 0) + 1
    
    # By difficulty (from meta)
    by_difficulty = {}
    for question in questions:
        difficulty = question.meta.get('difficulty', 'medium') if question.meta else 'medium'
        by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1
    
    # By CO
    by_co = {}
    for question in questions:
        if question.co_id:
            co_code = next((co.code for co in cos if co.id == question.co_id), f"CO{question.co_id}")
            by_co[co_code] = by_co.get(co_code, 0) + 1
    
    # Average marks
    avg_marks = sum(q.max_marks for q in questions) / total_questions if total_questions > 0 else 0
    
    # Recent additions (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_additions = len([q for q in questions if q.created_at >= week_ago])
    
    return QuestionStatsResponse(
        total_questions=total_questions,
        by_type=by_type,
        by_bloom_level=by_bloom_level,
        by_difficulty=by_difficulty,
        by_co=by_co,
        avg_marks=round(avg_marks, 2),
        recent_additions=recent_additions
    )

# ==================== AI QUESTION GENERATION ====================

@router.post("/ai/generate", response_model=AIQuestionGenerationResponse)
async def generate_questions_ai(
    generation_request: AIQuestionGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("ai_generate_questions"))
):
    """Generate questions using AI"""
    # Verify course exists
    course_result = await db.execute(
        select(Course).options(selectinload(Course.cos)).where(Course.id == generation_request.course_id)
    )
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Prepare AI service request
    ai_request = {
        "course_id": generation_request.course_id,
        "course_name": course.title,
        "syllabus": generation_request.syllabus,
        "topics": generation_request.topics,
        "question_types": [qt.value for qt in generation_request.question_types],
        "difficulty_distribution": generation_request.difficulty_distribution,
        "total_questions": generation_request.total_questions,
        "marks_per_question": generation_request.marks_per_question,
        "bloom_levels": generation_request.bloom_levels,
        "co_mapping": generation_request.co_mapping,
        "available_cos": [{"id": co.id, "code": co.code, "title": co.title, "bloom": co.bloom} for co in course.cos]
    }
    
    try:
        # Call AI service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ai_service_url}/generate-questions",
                json=ai_request,
                headers={"Authorization": f"Bearer {settings.ai_service_token}"},
                timeout=300  # 5 minutes timeout for AI generation
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI service error: {response.text}"
                )
            
            ai_response = response.json()
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )
    
    # Process AI response and create questions
    generated_questions = []
    errors = []
    success_count = 0
    
    for q_data in ai_response.get("questions", []):
        try:
            # Create question data
            question_data = QuestionCreate(
                type=QuestionType(q_data["type"]),
                text=q_data["text"],
                co_id=q_data.get("co_id"),
                max_marks=q_data["max_marks"],
                model_answer=q_data.get("model_answer"),
                meta={
                    "difficulty": q_data.get("difficulty", "medium"),
                    "bloom_level": q_data.get("bloom_level"),
                    "ai_generated": True,
                    "generation_metadata": q_data.get("metadata", {})
                },
                options=[
                    QuestionOptionCreate(text=opt["text"], is_correct=opt["is_correct"])
                    for opt in q_data.get("options", [])
                ]
            )
            
            # Create question in database
            question_dict = question_data.dict(exclude={'options'})
            question_dict['created_by'] = current_user.id
            question = Question(**question_dict)
            
            db.add(question)
            await db.flush()
            
            # Add options
            if question_data.options:
                for option_data in question_data.options:
                    option = QuestionOption(
                        question_id=question.id,
                        **option_data.dict()
                    )
                    db.add(option)
            
            await db.commit()
            await db.refresh(question)
            
            # Load relationships for response
            result = await db.execute(
                select(Question).options(
                    selectinload(Question.options),
                    selectinload(Question.creator),
                    selectinload(Question.co)
                ).where(Question.id == question.id)
            )
            question = result.scalar_one()
            
            generated_questions.append(QuestionResponse.from_orm(question))
            success_count += 1
            
        except Exception as e:
            errors.append(f"Failed to create question: {str(e)}")
            await db.rollback()
    
    # Log audit event
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="question",
        entity_id=None,
        action=AUDIT_ACTIONS["BULK_IMPORT"],
        after_json={
            "course_id": generation_request.course_id,
            "total_requested": generation_request.total_questions,
            "success_count": success_count,
            "error_count": len(errors)
        },
        reason="AI question generation"
    )
    
    return AIQuestionGenerationResponse(
        generated_questions=generated_questions,
        generation_metadata=ai_response.get("metadata", {}),
        success_count=success_count,
        error_count=len(errors),
        errors=errors
    )

# ==================== BULK OPERATIONS ====================

@router.post("/bulk-import", response_model=BulkOperationResponse)
async def bulk_import_questions(
    import_request: QuestionBulkImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("create_questions"))
):
    """Bulk import questions"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == import_request.course_id))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    
    success_count = 0
    error_count = 0
    errors = []
    
    for question_data in import_request.questions:
        try:
            # Use default CO if not specified
            if not question_data.co_id and import_request.default_co_id:
                question_data.co_id = import_request.default_co_id
            
            # Verify CO exists if specified
            if question_data.co_id:
                co_result = await db.execute(select(CO).where(CO.id == question_data.co_id))
                if not co_result.scalar_one_or_none():
                    errors.append(f"CO {question_data.co_id} not found")
                    error_count += 1
                    continue
            
            # Create question
            question_dict = question_data.dict(exclude={'options'})
            question_dict['created_by'] = current_user.id
            question = Question(**question_dict)
            
            db.add(question)
            await db.flush()
            
            # Add options
            if question_data.options:
                for option_data in question_data.options:
                    option = QuestionOption(
                        question_id=question.id,
                        **option_data.dict()
                    )
                    db.add(option)
            
            success_count += 1
            
        except Exception as e:
            errors.append(f"Failed to import question: {str(e)}")
            error_count += 1
            await db.rollback()
    
    if success_count > 0:
        await db.commit()
    
    # Log audit event
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="question",
        entity_id=None,
        action=AUDIT_ACTIONS["BULK_IMPORT"],
        after_json={
            "course_id": import_request.course_id,
            "total_questions": len(import_request.questions),
            "success_count": success_count,
            "error_count": error_count
        },
        reason="Bulk question import"
    )
    
    return BulkOperationResponse(
        success_count=success_count,
        error_count=error_count,
        total_count=len(import_request.questions),
        errors=errors
    )

# ==================== RUBRICS ====================

@router.post("/{question_id}/rubric", response_model=RubricResponse, status_code=status.HTTP_201_CREATED)
async def create_question_rubric(
    question_id: int,
    rubric_data: RubricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("edit_questions"))
):
    """Create rubric for a descriptive question"""
    # Verify question exists and is descriptive
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.type != QuestionType.DESCRIPTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rubrics can only be created for descriptive questions"
        )
    
    if question.created_by != current_user.id and not current_user.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only create rubrics for your own questions"
        )
    
    # Update question with rubric
    rubric_json = {
        "criteria": [criterion.dict() for criterion in rubric_data.criteria],
        "total_points": rubric_data.total_points,
        "strictness": rubric_data.strictness
    }
    
    question.rubric_json = rubric_json
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="question",
        entity_id=question.id,
        action=AUDIT_ACTIONS["UPDATE"],
        after_json={"rubric_created": True},
        reason="Created question rubric"
    )
    
    return RubricResponse(
        id=question.id,
        question_id=question.id,
        criteria=rubric_data.criteria,
        total_points=rubric_data.total_points,
        strictness=rubric_data.strictness,
        created_at=question.created_at,
        updated_at=question.updated_at
    )