from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, text
from typing import List, Optional, Dict, Any
import json
import pandas as pd
import io
from datetime import datetime
import httpx
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.audit import log_audit_event, AUDIT_ACTIONS
from ..core.config import settings
from ..models.models import (
    User, Exam, Question, Response, Attempt, ExamQuestion, 
    QuestionType, AttemptStatus, ExamStatus
)
from ..schemas.common import Response as CommonResponse, BulkOperationResponse

router = APIRouter()

# ==================== RESPONSE GRADING ====================

class GradeRequest(BaseModel):
    response_id: int
    score: float
    feedback: Optional[str] = None
    reason: Optional[str] = None

class AIGradeRequest(BaseModel):
    response_id: int
    strictness: str = "standard"  # lenient, standard, strict
    use_rubric: bool = True

class BulkGradeRequest(BaseModel):
    grades: List[GradeRequest]

class BulkAIGradeRequest(BaseModel):
    exam_id: int
    question_ids: Optional[List[int]] = None  # If None, grade all descriptive questions
    strictness: str = "standard"
    use_rubric: bool = True
    auto_apply: bool = False  # If True, automatically apply AI grades without teacher review

class GradingProgressResponse(BaseModel):
    exam_id: int
    total_responses: int
    graded_responses: int
    ai_graded_responses: int
    teacher_graded_responses: int
    pending_responses: int
    progress_percentage: float

from pydantic import BaseModel

@router.get("/exam/{exam_id}/progress", response_model=GradingProgressResponse)
async def get_grading_progress(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Get grading progress for an exam"""
    # Verify exam exists
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Get response statistics
    stats_result = await db.execute(
        select(
            func.count(Response.id).label('total'),
            func.count(Response.final_score).label('graded'),
            func.sum(func.case((Response.ai_score.isnot(None), 1), else_=0)).label('ai_graded'),
            func.sum(func.case((Response.teacher_score.isnot(None), 1), else_=0)).label('teacher_graded')
        )
        .join(Attempt, Response.attempt_id == Attempt.id)
        .where(Attempt.exam_id == exam_id)
    )
    
    stats = stats_result.first()
    total = stats.total or 0
    graded = stats.graded or 0
    ai_graded = stats.ai_graded or 0
    teacher_graded = stats.teacher_graded or 0
    pending = total - graded
    
    progress_percentage = (graded / total * 100) if total > 0 else 0
    
    return GradingProgressResponse(
        exam_id=exam_id,
        total_responses=total,
        graded_responses=graded,
        ai_graded_responses=ai_graded,
        teacher_graded_responses=teacher_graded,
        pending_responses=pending,
        progress_percentage=round(progress_percentage, 2)
    )

@router.get("/exam/{exam_id}/responses")
async def get_exam_responses(
    exam_id: int,
    question_id: Optional[int] = None,
    student_id: Optional[int] = None,
    graded: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Get responses for grading"""
    # Verify exam exists
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not exam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Build query
    query = select(
        Response,
        Question.text.label('question_text'),
        Question.type.label('question_type'),
        Question.max_marks.label('max_marks'),
        Question.rubric_json.label('rubric'),
        User.name.label('student_name'),
        ExamQuestion.marks_override
    ).join(
        Attempt, Response.attempt_id == Attempt.id
    ).join(
        Question, Response.question_id == Question.id
    ).join(
        User, Attempt.student_id == User.id
    ).join(
        ExamQuestion, and_(
            ExamQuestion.exam_id == exam_id,
            ExamQuestion.question_id == Response.question_id
        )
    ).where(Attempt.exam_id == exam_id)
    
    # Apply filters
    if question_id:
        query = query.where(Response.question_id == question_id)
    if student_id:
        query = query.where(Attempt.student_id == student_id)
    if graded is not None:
        if graded:
            query = query.where(Response.final_score.isnot(None))
        else:
            query = query.where(Response.final_score.is_(None))
    
    # Order by student name, then question order
    query = query.order_by(User.name, ExamQuestion.order)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    responses = result.all()
    
    # Format response
    formatted_responses = []
    for response, q_text, q_type, max_marks, rubric, student_name, marks_override in responses:
        response_dict = {
            "id": response.id,
            "attempt_id": response.attempt_id,
            "question_id": response.question_id,
            "answer_json": response.answer_json,
            "ai_score": response.ai_score,
            "teacher_score": response.teacher_score,
            "final_score": response.final_score,
            "feedback": response.feedback,
            "created_at": response.created_at,
            "updated_at": response.updated_at,
            "question_text": q_text,
            "question_type": q_type.value,
            "max_marks": float(marks_override or max_marks),
            "rubric": rubric,
            "student_name": student_name,
            "needs_grading": response.final_score is None,
            "has_ai_suggestion": response.ai_score is not None
        }
        formatted_responses.append(response_dict)
    
    return {
        "responses": formatted_responses,
        "total": len(formatted_responses)
    }

@router.post("/response/{response_id}/grade")
async def grade_response(
    response_id: int,
    grade_request: GradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Grade a response manually"""
    # Get response with question details
    result = await db.execute(
        select(Response, Question, ExamQuestion.marks_override)
        .join(Question, Response.question_id == Question.id)
        .join(Attempt, Response.attempt_id == Attempt.id)
        .join(ExamQuestion, and_(
            ExamQuestion.question_id == Response.question_id,
            ExamQuestion.exam_id == Attempt.exam_id
        ))
        .where(Response.id == response_id)
    )
    
    response_data = result.first()
    if not response_data:
        raise HTTPException(status_code=404, detail="Response not found")
    
    response, question, marks_override = response_data
    max_marks = marks_override or question.max_marks
    
    # Validate score
    if grade_request.score < 0 or grade_request.score > max_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Score must be between 0 and {max_marks}"
        )
    
    # Store previous values for audit
    before_data = {
        "teacher_score": response.teacher_score,
        "final_score": response.final_score,
        "feedback": response.feedback
    }
    
    # Update response
    response.teacher_score = grade_request.score
    response.final_score = grade_request.score  # Teacher score overrides AI score
    response.feedback = grade_request.feedback
    
    # Update audit JSON
    audit_entry = {
        "graded_by": current_user.id,
        "graded_at": datetime.utcnow().isoformat(),
        "reason": grade_request.reason,
        "previous_ai_score": response.ai_score
    }
    
    if response.audit_json:
        response.audit_json.update(audit_entry)
    else:
        response.audit_json = audit_entry
    
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="response",
        entity_id=response_id,
        action=AUDIT_ACTIONS["GRADE_UPDATE"],
        before_json=before_data,
        after_json={
            "teacher_score": grade_request.score,
            "final_score": grade_request.score,
            "feedback": grade_request.feedback
        },
        reason=grade_request.reason or "Manual grading"
    )
    
    return CommonResponse(message="Response graded successfully")

@router.post("/response/{response_id}/ai-grade")
async def ai_grade_response(
    response_id: int,
    ai_request: AIGradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("ai_propose_grades"))
):
    """Get AI grading suggestion for a response"""
    # Get response with question details
    result = await db.execute(
        select(Response, Question, ExamQuestion.marks_override)
        .join(Question, Response.question_id == Question.id)
        .join(Attempt, Response.attempt_id == Attempt.id)
        .join(ExamQuestion, and_(
            ExamQuestion.question_id == Response.question_id,
            ExamQuestion.exam_id == Attempt.exam_id
        ))
        .where(Response.id == response_id)
    )
    
    response_data = result.first()
    if not response_data:
        raise HTTPException(status_code=404, detail="Response not found")
    
    response, question, marks_override = response_data
    max_marks = marks_override or question.max_marks
    
    # Check if question type supports AI grading
    if question.type not in [QuestionType.DESCRIPTIVE, QuestionType.CODING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI grading only supports descriptive and coding questions"
        )
    
    # Prepare AI service request
    ai_service_request = {
        "response_id": response_id,
        "question": {
            "id": question.id,
            "text": question.text,
            "type": question.type.value,
            "max_marks": float(max_marks),
            "model_answer": question.model_answer,
            "rubric": question.rubric_json if ai_request.use_rubric else None
        },
        "student_answer": response.answer_json,
        "strictness": ai_request.strictness
    }
    
    try:
        # Call AI service
        async with httpx.AsyncClient() as client:
            ai_response = await client.post(
                f"{settings.ai_service_url}/grade-response",
                json=ai_service_request,
                headers={"Authorization": f"Bearer {settings.ai_service_token}"},
                timeout=60
            )
            
            if ai_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI service error: {ai_response.text}"
                )
            
            ai_result = ai_response.json()
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )
    
    # Store AI grading result
    before_data = {
        "ai_score": response.ai_score,
        "feedback": response.feedback
    }
    
    response.ai_score = ai_result.get("score", 0)
    
    # Combine existing feedback with AI feedback
    ai_feedback = ai_result.get("feedback", "")
    if response.feedback:
        response.feedback = f"{response.feedback}\n\nAI Suggestion: {ai_feedback}"
    else:
        response.feedback = f"AI Suggestion: {ai_feedback}"
    
    # Update audit JSON
    audit_entry = {
        "ai_graded_by": current_user.id,
        "ai_graded_at": datetime.utcnow().isoformat(),
        "ai_strictness": ai_request.strictness,
        "ai_confidence": ai_result.get("confidence", 0),
        "ai_explanation": ai_result.get("explanation", "")
    }
    
    if response.audit_json:
        response.audit_json.update(audit_entry)
    else:
        response.audit_json = audit_entry
    
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="response",
        entity_id=response_id,
        action=AUDIT_ACTIONS["AI_GRADING"],
        before_json=before_data,
        after_json={
            "ai_score": response.ai_score,
            "ai_feedback": ai_feedback
        },
        reason="AI grading suggestion"
    )
    
    return {
        "response_id": response_id,
        "ai_score": response.ai_score,
        "ai_feedback": ai_feedback,
        "confidence": ai_result.get("confidence", 0),
        "explanation": ai_result.get("explanation", ""),
        "max_marks": float(max_marks)
    }

@router.post("/response/{response_id}/accept-ai")
async def accept_ai_grade(
    response_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Accept AI grading suggestion"""
    result = await db.execute(select(Response).where(Response.id == response_id))
    response = result.scalar_one_or_none()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    if response.ai_score is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No AI grading suggestion available"
        )
    
    before_data = {
        "final_score": response.final_score,
        "teacher_score": response.teacher_score
    }
    
    # Accept AI score as final score
    response.final_score = response.ai_score
    response.teacher_score = response.ai_score
    
    # Update audit JSON
    audit_entry = {
        "ai_accepted_by": current_user.id,
        "ai_accepted_at": datetime.utcnow().isoformat()
    }
    
    if response.audit_json:
        response.audit_json.update(audit_entry)
    else:
        response.audit_json = audit_entry
    
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="response",
        entity_id=response_id,
        action=AUDIT_ACTIONS["GRADE_UPDATE"],
        before_json=before_data,
        after_json={
            "final_score": response.final_score,
            "teacher_score": response.teacher_score
        },
        reason="Accepted AI grading suggestion"
    )
    
    return CommonResponse(message="AI grading accepted successfully")

# ==================== BULK GRADING ====================

@router.post("/bulk/manual")
async def bulk_grade_manual(
    bulk_request: BulkGradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Bulk grade responses manually"""
    success_count = 0
    error_count = 0
    errors = []
    
    for grade_req in bulk_request.grades:
        try:
            # Get response
            result = await db.execute(
                select(Response, Question, ExamQuestion.marks_override)
                .join(Question, Response.question_id == Question.id)
                .join(Attempt, Response.attempt_id == Attempt.id)
                .join(ExamQuestion, and_(
                    ExamQuestion.question_id == Response.question_id,
                    ExamQuestion.exam_id == Attempt.exam_id
                ))
                .where(Response.id == grade_req.response_id)
            )
            
            response_data = result.first()
            if not response_data:
                errors.append(f"Response {grade_req.response_id} not found")
                error_count += 1
                continue
            
            response, question, marks_override = response_data
            max_marks = marks_override or question.max_marks
            
            # Validate score
            if grade_req.score < 0 or grade_req.score > max_marks:
                errors.append(f"Invalid score for response {grade_req.response_id}: must be between 0 and {max_marks}")
                error_count += 1
                continue
            
            # Update response
            response.teacher_score = grade_req.score
            response.final_score = grade_req.score
            if grade_req.feedback:
                response.feedback = grade_req.feedback
            
            # Update audit JSON
            audit_entry = {
                "bulk_graded_by": current_user.id,
                "bulk_graded_at": datetime.utcnow().isoformat(),
                "reason": grade_req.reason
            }
            
            if response.audit_json:
                response.audit_json.update(audit_entry)
            else:
                response.audit_json = audit_entry
            
            success_count += 1
            
        except Exception as e:
            errors.append(f"Error grading response {grade_req.response_id}: {str(e)}")
            error_count += 1
    
    if success_count > 0:
        await db.commit()
        
        await log_audit_event(
            db=db,
            actor_id=current_user.id,
            entity_type="response",
            entity_id=None,
            action=AUDIT_ACTIONS["BULK_UPDATE"],
            after_json={
                "success_count": success_count,
                "error_count": error_count,
                "total_count": len(bulk_request.grades)
            },
            reason="Bulk manual grading"
        )
    
    return BulkOperationResponse(
        success_count=success_count,
        error_count=error_count,
        total_count=len(bulk_request.grades),
        errors=errors
    )

@router.post("/bulk/ai")
async def bulk_ai_grade(
    bulk_request: BulkAIGradeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("ai_propose_grades"))
):
    """Bulk AI grade responses"""
    # Verify exam exists
    exam_result = await db.execute(select(Exam).where(Exam.id == bulk_request.exam_id))
    exam = exam_result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Get responses to grade
    query = select(Response, Question, ExamQuestion.marks_override).join(
        Attempt, Response.attempt_id == Attempt.id
    ).join(
        Question, Response.question_id == Question.id
    ).join(
        ExamQuestion, and_(
            ExamQuestion.question_id == Response.question_id,
            ExamQuestion.exam_id == bulk_request.exam_id
        )
    ).where(
        and_(
            Attempt.exam_id == bulk_request.exam_id,
            Question.type.in_([QuestionType.DESCRIPTIVE, QuestionType.CODING])
        )
    )
    
    # Filter by specific questions if provided
    if bulk_request.question_ids:
        query = query.where(Response.question_id.in_(bulk_request.question_ids))
    
    # Only grade ungraded responses or those without AI scores
    if not bulk_request.auto_apply:
        query = query.where(Response.ai_score.is_(None))
    
    result = await db.execute(query)
    responses_to_grade = result.all()
    
    if not responses_to_grade:
        return BulkOperationResponse(
            success_count=0,
            error_count=0,
            total_count=0,
            errors=["No responses found to grade"]
        )
    
    # Start background task for bulk AI grading
    background_tasks.add_task(
        process_bulk_ai_grading,
        responses_to_grade,
        bulk_request,
        current_user.id,
        db
    )
    
    return CommonResponse(
        message=f"Bulk AI grading started for {len(responses_to_grade)} responses. This may take a few minutes."
    )

async def process_bulk_ai_grading(
    responses_to_grade: List,
    bulk_request: BulkAIGradeRequest,
    user_id: int,
    db: AsyncSession
):
    """Background task to process bulk AI grading"""
    success_count = 0
    error_count = 0
    
    for response, question, marks_override in responses_to_grade:
        try:
            max_marks = marks_override or question.max_marks
            
            # Prepare AI service request
            ai_service_request = {
                "response_id": response.id,
                "question": {
                    "id": question.id,
                    "text": question.text,
                    "type": question.type.value,
                    "max_marks": float(max_marks),
                    "model_answer": question.model_answer,
                    "rubric": question.rubric_json if bulk_request.use_rubric else None
                },
                "student_answer": response.answer_json,
                "strictness": bulk_request.strictness
            }
            
            # Call AI service
            async with httpx.AsyncClient() as client:
                ai_response = await client.post(
                    f"{settings.ai_service_url}/grade-response",
                    json=ai_service_request,
                    headers={"Authorization": f"Bearer {settings.ai_service_token}"},
                    timeout=60
                )
                
                if ai_response.status_code == 200:
                    ai_result = ai_response.json()
                    
                    # Update response
                    response.ai_score = ai_result.get("score", 0)
                    
                    # Auto-apply if requested
                    if bulk_request.auto_apply:
                        response.final_score = response.ai_score
                        response.teacher_score = response.ai_score
                    
                    # Update feedback
                    ai_feedback = ai_result.get("feedback", "")
                    if response.feedback:
                        response.feedback = f"{response.feedback}\n\nAI Suggestion: {ai_feedback}"
                    else:
                        response.feedback = f"AI Suggestion: {ai_feedback}"
                    
                    # Update audit JSON
                    audit_entry = {
                        "bulk_ai_graded_by": user_id,
                        "bulk_ai_graded_at": datetime.utcnow().isoformat(),
                        "ai_strictness": bulk_request.strictness,
                        "ai_confidence": ai_result.get("confidence", 0),
                        "auto_applied": bulk_request.auto_apply
                    }
                    
                    if response.audit_json:
                        response.audit_json.update(audit_entry)
                    else:
                        response.audit_json = audit_entry
                    
                    success_count += 1
                else:
                    error_count += 1
        
        except Exception as e:
            error_count += 1
    
    # Commit all changes
    await db.commit()
    
    # Log audit event
    await log_audit_event(
        db=db,
        actor_id=user_id,
        entity_type="response",
        entity_id=None,
        action=AUDIT_ACTIONS["BULK_UPDATE"],
        after_json={
            "exam_id": bulk_request.exam_id,
            "success_count": success_count,
            "error_count": error_count,
            "total_count": len(responses_to_grade),
            "auto_applied": bulk_request.auto_apply
        },
        reason="Bulk AI grading"
    )

# ==================== BULK UPLOAD ====================

@router.post("/bulk/upload")
async def bulk_upload_grades(
    exam_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("bulk_upload_grades"))
):
    """Upload grades from CSV/Excel file"""
    # Verify exam exists
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not exam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV or Excel format"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse file based on type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate required columns
        required_columns = ['student_id', 'question_id', 'score']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {missing_columns}"
            )
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                student_id = int(row['student_id'])
                question_id = int(row['question_id'])
                score = float(row['score'])
                feedback = row.get('feedback', '')
                
                # Find the response
                response_result = await db.execute(
                    select(Response, Question, ExamQuestion.marks_override)
                    .join(Attempt, Response.attempt_id == Attempt.id)
                    .join(Question, Response.question_id == Question.id)
                    .join(ExamQuestion, and_(
                        ExamQuestion.question_id == Response.question_id,
                        ExamQuestion.exam_id == exam_id
                    ))
                    .where(
                        and_(
                            Attempt.exam_id == exam_id,
                            Attempt.student_id == student_id,
                            Response.question_id == question_id
                        )
                    )
                )
                
                response_data = response_result.first()
                if not response_data:
                    errors.append(f"Row {index + 1}: Response not found for student {student_id}, question {question_id}")
                    error_count += 1
                    continue
                
                response, question, marks_override = response_data
                max_marks = marks_override or question.max_marks
                
                # Validate score
                if score < 0 or score > max_marks:
                    errors.append(f"Row {index + 1}: Invalid score {score}, must be between 0 and {max_marks}")
                    error_count += 1
                    continue
                
                # Update response
                response.teacher_score = score
                response.final_score = score
                if feedback:
                    response.feedback = feedback
                
                # Update audit JSON
                audit_entry = {
                    "bulk_uploaded_by": current_user.id,
                    "bulk_uploaded_at": datetime.utcnow().isoformat(),
                    "upload_filename": file.filename
                }
                
                if response.audit_json:
                    response.audit_json.update(audit_entry)
                else:
                    response.audit_json = audit_entry
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
                error_count += 1
        
        if success_count > 0:
            await db.commit()
            
            # Create grade upload batch record
            from ..models.models import GradeUploadBatch
            batch = GradeUploadBatch(
                exam_id=exam_id,
                uploaded_by=current_user.id,
                notes=f"Bulk upload: {success_count} grades, {error_count} errors"
            )
            db.add(batch)
            await db.commit()
            
            await log_audit_event(
                db=db,
                actor_id=current_user.id,
                entity_type="response",
                entity_id=None,
                action=AUDIT_ACTIONS["BULK_IMPORT"],
                after_json={
                    "exam_id": exam_id,
                    "filename": file.filename,
                    "success_count": success_count,
                    "error_count": error_count,
                    "total_rows": len(df)
                },
                reason="Bulk grade upload"
            )
        
        return BulkOperationResponse(
            success_count=success_count,
            error_count=error_count,
            total_count=len(df),
            errors=errors[:10]  # Limit errors to first 10
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )