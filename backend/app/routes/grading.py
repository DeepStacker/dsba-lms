from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..models.models import Response, Attempt, Exam, Question
from ..schemas.grading import AIGradeRequest, GradeResponse, BulkGradeRequest, GradeOverrideRequest
from ..core.ai_client import AIClient
from ..core.audit import log_audit_event, AUDIT_ACTIONS

router = APIRouter(
    prefix="/grading",
    tags=["Grading"]
)

@router.post("/ai/descriptive/{response_id}", summary="AI grade descriptive answer", tags=["Grading"])
async def ai_grade_descriptive(
    response_id: int,
    grading_request: AIGradeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Grade a descriptive answer using AI"""

    # Get the response
    result = await db.execute(
        select(Response, Question, Attempt)
        .join(Question, Response.question_id == Question.id)
        .join(Attempt, Response.attempt_id == Attempt.id)
        .where(Response.id == response_id)
    )
    data = result.first()

    if not data:
        raise HTTPException(status_code=404, detail="Response not found")

    response, question, attempt = data

    # Check permissions
    if not await _can_grade_response(current_user, attempt):
        raise HTTPException(status_code=403, detail="Not authorized to grade this response")

    if question.type not in ["descriptive", "coding"]:
        raise HTTPException(status_code=400, detail="AI grading only supports descriptive and coding questions")

    try:
        ai_client = AIClient()

        # Get model answer from question
        model_answer = question.model_answer or ""
        rubric = question.rubric_json or {"criteria": ["Content", "Accuracy", "Completeness"]}

        # Call AI grading service
        ai_result = await ai_client.grade_descriptive_answer(
            answer=response.answer_json.get("answer", ""),
            model_answer=model_answer,
            rubric=rubric,
            strictness=grading_request.strictness or 0.5
        )

        # Update response with AI scores
        ai_score = ai_result.get("ai_score", 0)
        per_criterion = ai_result.get("per_criterion", {})
        feedback = json.dumps({
            "ai_feedback": ai_result.get("feedback_bullets", []),
            "per_criterion": per_criterion,
            "strictness": grading_request.strictness
        })

        response.ai_score = ai_score
        response.feedback = feedback

        # If no teacher score exists, set final score to AI score
        if response.final_score is None:
            response.final_score = ai_score

        await db.commit()

        # Log AI grading event
        await log_audit_event(
            db=db,
            actor_id=current_user.id,
            entity_type="response",
            entity_id=response_id,
            action=AUDIT_ACTIONS["AI_GRADING"],
            before_json={"ai_score": None},
            after_json={
                "ai_score": ai_score,
                "final_score": response.final_score,
                "strictness": grading_request.strictness
            }
        )

        return GradeResponse(
            response_id=response_id,
            ai_score=ai_score,
            final_score=response.final_score,
            teacher_score=response.teacher_score,
            feedback=ai_result.get("feedback_bullets", []),
            per_criterion=per_criterion
        )

    except Exception as e:
        logger.error(f"AI grading error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI grading failed: {str(e)}")

@router.post("/bulk/ai", summary="Bulk AI grading for exam responses", tags=["Grading"])
async def bulk_ai_grading(
    bulk_request: BulkGradeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("grade"))
):
    """Bulk grade responses using AI for entire exam"""

    # Verify exam exists and user can grade it
    exam_result = await db.execute(select(Exam).where(Exam.id == bulk_request.exam_id))
    exam = exam_result.scalar_one_or_none()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Get all responses for the exam that need grading
    query = select(Response, Question).join(Question).where(
        Response.attempt_id.in_(
            select(Attempt.id).where(Attempt.exam_id == bulk_request.exam_id)
        ),
        Question.type.in_(["descriptive", "coding"]),
        Response.ai_score.is_none()
    )

    result = await db.execute(query)
    responses_to_grade = result.fetchall()

    if not responses_to_grade:
        return {"message": "No ungraded responses found for AI grading"}

    # Grade in background for large numbers
    background_tasks.add_task(_process_bulk_ai_grading,
                            responses_to_grade, bulk_request, current_user, db)

    return {
        "message": f"Started AI grading for {len(responses_to_grade)} responses",
        "responses_to_grade": len(responses_to_grade)
    }

@router.put("/override/{response_id}", summary="Teacher override grade", tags=["Grading"])
async def teacher_grade_override(
    response_id: int,
    override_request: GradeOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("grade"))
):
    """Teacher override of AI/previous grading"""

    # Get the response
    result = await db.execute(
        select(Response, Attempt)
        .join(Attempt, Response.attempt_id == Attempt.id)
        .where(Response.id == response_id)
    )
    data = result.first()

    if not data:
        raise HTTPException(status_code=404, detail="Response not found")

    response, attempt = data

    # Check permissions
    if not await _can_grade_response(current_user, attempt):
        raise HTTPException(status_code=403, detail="Not authorized to grade this response")

    # Validate grades
    teacher_score = float(override_request.teacher_score)
    if teacher_score < 0 or teacher_score > response.question.max_marks:
        raise HTTPException(status_code=400, detail=f"Grade must be between 0 and {response.question.max_marks}")

    # Store previous values for audit
    previous_scores = {
        "teacher_score": response.teacher_score,
        "final_score": response.final_score,
        "ai_score": response.ai_score
    }

    # Update response
    response.teacher_score = teacher_score
    response.final_score = teacher_score
    response.updated_at = datetime.utcnow()

    # Add override metadata
    if response.audit_json:
        audit_data = response.audit_json
        audit_data["overrides"] = audit_data.get("overrides", [])
        audit_data["overrides"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "actor_id": current_user.id,
            "old_final_score": response.final_score,
            "new_final_score": teacher_score,
            "reason": override_request.reason
        })
        response.audit_json = audit_data

    await db.commit()

    # Log grade override
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="response",
        entity_id=response_id,
        action=AUDIT_ACTIONS["GRADE_UPDATE"],
        before_json=previous_scores,
        after_json={
            "teacher_score": teacher_score,
            "final_score": teacher_score,
            "reason": override_request.reason
        }
    )

    return {
        "message": "Grade override successful",
        "response_id": response_id,
        "previous_score": response.final_score,
        "new_score": teacher_score,
        "reason": override_request.reason
    }

@router.post("/bulk/override", summary="Bulk grade overrides", tags=["Grading"])
async def bulk_grade_override(
    bulk_overrides: List[GradeOverrideRequest],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("grade"))
):
    """Bulk apply grade overrides"""

    processed = 0
    errors = []

    for override_req in bulk_overrides:
        try:
            # Reuse the single override logic
            await teacher_grade_override(
                override_req.response_id,
                GradeOverrideRequest(
                    teacher_score=override_req.teacher_score,
                    reason=override_req.reason
                ),
                db, current_user
            )

            override_req.response_id = override_req.response_id
            processed += 1

        except Exception as e:
            errors.append({
                "response_id": override_req.response_id,
                "error": str(e)
            })

    return {
        "message": f"Bulk override completed: {processed} successful, {len(errors)} errors",
        "processed": processed,
        "errors": errors
    }

@router.get("/exam/{exam_id}/progress", summary="Get grading progress for exam", tags=["Grading"])
async def get_grading_progress(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("grade"))
):
    """Get grading progress and statistics for an exam"""

    # Total responses
    total_result = await db.execute("""
        SELECT COUNT(*)
        FROM responses r
        JOIN attempts a ON r.attempt_id = a.id
        WHERE a.exam_id = $1
    """, (exam_id,))

    # AI graded responses
    ai_graded_result = await db.execute("""
        SELECT COUNT(*)
        FROM responses r
        JOIN attempts a ON r.attempt_id = a.id
        WHERE a.exam_id = $1 AND r.ai_score IS NOT NULL
    """, (exam_id,))

    # Manually graded responses
    manual_graded_result = await db.execute("""
        SELECT COUNT(*)
        FROM responses r
        JOIN attempts a ON r.attempt_id = a.id
        WHERE a.exam_id = $1 AND r.teacher_score IS NOT NULL
    """, (exam_id,))

    total = total_result.scalar()
    ai_graded = ai_graded_result.scalar()
    manual_graded = manual_graded_result.scalar()

    return {
        "exam_id": exam_id,
        "total_responses": total,
        "ai_graded": ai_graded,
        "manual_graded": manual_graded,
        "fully_graded": ai_graded + manual_graded,
        "completion_percentage": round(((ai_graded + manual_graded) / total * 100), 1) if total > 0 else 0
    }

# Helper functions
async def _can_grade_response(current_user, attempt) -> bool:
    """Check if user can grade responses for the given attempt"""

    if current_user.role.value == "admin":
        return True

    # For now, teachers can grade all exams
    # In future, implement course-teacher assignment check
    return current_user.role.value == "teacher"

async def _process_bulk_ai_grading(responses_to_grade, bulk_request, current_user, db):
    """Background task to process bulk AI grading"""

    ai_client = AIClient()
    processed = 0

    for response_data, question in responses_to_grade:
        try:
            # Get contextual information
            model_answer = question.model_answer or ""
            rubric = question.rubric_json or {"criteria": ["Quality", "Accuracy", "Completeness"]}

            # Call AI grading
            ai_result = await ai_client.grade_descriptive_answer(
                answer=response_data.answer_json.get("answer", ""),
                model_answer=model_answer,
                rubric=rubric,
                strictness=bulk_request.strictness or 0.5
            )

            # Update response
            response_data.ai_score = ai_result.get("ai_score", 0)
            response_data.feedback = json.dumps({
                "ai_feedback": ai_result.get("feedback_bullets", []),
                "bulk_graded": True,
                "strictness": bulk_request.strictness
            })

            processed += 1

            # Periodic commit
            if processed % 10 == 0:
                await db.commit()

        except Exception as e:
            logger.warning(f"Failed to AI grade response {response_data.id}: {str(e)}")

    await db.commit()

    # Log bulk AI grading completion
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="response",
        entity_id=None,
        action="bulk_ai_grading",
        after_json={
            "processed_count": processed,
            "exam_id": bulk_request.exam_id,
            "strictness": bulk_request.strictness
        }
    )

import json
import logging
logger = logging.getLogger(__name__)
