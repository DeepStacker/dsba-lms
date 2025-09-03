from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Optional
from ..core.database import get_db
from ..core.dependencies import require_permission
from ..models import Question, QuestionOption, User
from ..schemas.question import (
    Question, QuestionCreate, QuestionUpdate,
    QuestionOption, QuestionOptionCreate, QuestionOptionUpdate
)

router = APIRouter()

# Question endpoints
@router.get("/questions", response_model=List[Question])
async def get_questions(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_question"))
):
    result = await db.execute(select(Question))
    return result.scalars().all()

@router.post("/questions", response_model=Question)
async def create_question(
    question: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_question"))
):
    db_question = Question(**question.dict())
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)
    return db_question

@router.get("/questions/{question_id}", response_model=Question)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_question"))
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.put("/questions/{question_id}", response_model=Question)
async def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_question"))
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    db_question = result.scalar_one_or_none()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    for field, value in question_update.dict(exclude_unset=True).items():
        setattr(db_question, field, value)
    
    await db.commit()
    await db.refresh(db_question)
    return db_question

@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_question"))
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    db_question = result.scalar_one_or_none()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    await db.delete(db_question)
    await db.commit()
    return {"message": "Question deleted"}

# Question Option endpoints
@router.get("/questions/{question_id}/options", response_model=List[QuestionOption])
async def get_question_options(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_question"))
):
    result = await db.execute(select(QuestionOption).where(QuestionOption.question_id == question_id))
    return result.scalars().all()

@router.post("/questions/{question_id}/options", response_model=QuestionOption)
async def create_question_option(
    question_id: int,
    option: QuestionOptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_question"))
):
    # Verify question exists
    result = await db.execute(select(Question).where(Question.id == question_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Question not found")
    
    db_option = QuestionOption(**option.dict())
    db.add(db_option)
    await db.commit()
    await db.refresh(db_option)
    return db_option

@router.put("/options/{option_id}", response_model=QuestionOption)
async def update_question_option(
    option_id: int,
    option_update: QuestionOptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_question"))
):
    result = await db.execute(select(QuestionOption).where(QuestionOption.id == option_id))
    db_option = result.scalar_one_or_none()
    if not db_option:
        raise HTTPException(status_code=404, detail="Question option not found")
    
    for field, value in option_update.dict(exclude_unset=True).items():
        setattr(db_option, field, value)
    
    await db.commit()
    await db.refresh(db_option)
    return db_option

@router.delete("/options/{option_id}")
async def delete_question_option(
    option_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_question"))
):
    result = await db.execute(select(QuestionOption).where(QuestionOption.id == option_id))
    db_option = result.scalar_one_or_none()
    if not db_option:
        raise HTTPException(status_code=404, detail="Question option not found")
    
    await db.delete(db_option)
    await db.commit()
    return {"message": "Question option deleted"}
    return {"message": "Question option deleted"}

# AI-powered question generation endpoints
@router.post("/ai/generate", summary="Generate questions using AI", tags=["Questions"])
async def generate_questions_ai(
    syllabus: str,
    topics: List[str],
    counts: Dict[str, int],
    difficulty_mix: Dict[str, float],
    types: List[str],
    course_id: int,
    co_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("write_question"))
):
    """Generate questions using AI for the question bank"""

    try:
        from ..core.ai_client import AIClient
        ai_client = AIClient()

        # Generate questions using AI
        generated_questions = await ai_client.generate_questions(
            syllabus=syllabus,
            topics=topics,
            counts=counts,
            difficulty_mix=difficulty_mix,
            types=types
        )

        # Save generated questions to database
        saved_questions = []
        for q_data in generated_questions:
            # Create the question
            question = Question(
                text=q_data["text"],
                type=q_data["type"],
                max_marks=10,  # Default marks
                co_id=co_id,
                created_by=current_user.id,
                meta={
                    "generated": True,
                    "ai_source": "ai_generate_endpoint",
                    "difficulty": q_data.get("difficulty", "medium"),
                    "topics": topics,
                    "estimated_time": q_data.get("estimated_time", 60)
                }
            )

            db.add(question)

            # Add options for MCQ/MSQ if present
            if "options" in q_data and q_data["options"]:
                for i, option_text in enumerate(q_data["options"]):
                    is_correct = False
                    if q_data["type"] in ["mcq", "msq"]:
                        # Simple logic - first option is correct if no correct_option specified
                        is_correct = (i == 0) if "correct_option" not in q_data else (i in q_data["correct_option"])

                    option = QuestionOption(
                        question=question,
                        text=option_text,
                        is_correct=is_correct
                    )
                    db.add(option)

            saved_questions.append({
                "id": question.id,
                "text": question.text,
                "type": question.type,
                "difficulty": q_data.get("difficulty"),
                "co_tags": q_data.get("co_tags", [])
            })

        await db.commit()

        # Log the AI generation
        await log_audit_event(
            db=db,
            actor_id=current_user.id,
            entity_type="question",
            entity_id=None,
            action=AUDIT_ACTIONS["QUESTION_GENERATION"],
            after_json={
                "course_id": course_id,
                "co_id": co_id,
                "generated_count": len(saved_questions),
                "ai_source": "generated"
            },
            reason="AI-powered question generation"
        )

        return {
            "message": f"Generated and saved {len(saved_questions)} questions",
            "questions": saved_questions
        }

    except Exception as e:
        logger.error(f"AI question generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

# Question bank analytics endpoints
@router.get("/stats/course/{course_id}", summary="Get question bank stats for course", tags=["Questions"])
async def get_course_question_stats(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("read_question"))
):
    """Get comprehensive question bank statistics for a course"""

    # Total questions by type and difficulty
    type_stats_result = await db.execute("""
        SELECT
            type,
            COUNT(*) as count,
            AVG(max_marks) as avg_marks
        FROM questions q
        JOIN cos c ON q.co_id = c.id AND c.course_id = $1
        GROUP BY type
    """, (course_id,))

    # Difficulty distribution
    difficulty_stats_result = await db.execute("""
        SELECT
            q.meta->>'difficulty' as difficulty,
            COUNT(*) as count
        FROM questions q
        JOIN cos c ON q.co_id = c.id AND c.course_id = $1
        WHERE q.meta IS NOT NULL AND q.meta->>'difficulty' IS NOT NULL
        GROUP BY q.meta->>'difficulty'
    """, (course_id,))

    # CO mapping stats
    co_stats_result = await db.execute("""
        SELECT
            c.code as co_code,
            c.title as co_title,
            COUNT(q.id) as question_count
        FROM cos c
        LEFT JOIN questions q ON q.co_id = c.id
        WHERE c.course_id = $1
        GROUP BY c.id, c.code, c.title
        ORDER BY c.code
    """, (course_id,))

    # AI generation stats
    ai_stats_result = await db.execute("""
        SELECT
            COUNT(*) as ai_generated_count,
            COUNT(CASE WHEN q.meta->>'generated' = 'true' THEN 1 END) as total_questions,
            AVG(CASE WHEN q.meta->>'estimated_time' IS NOT NULL
                    THEN (q.meta->>'estimated_time')::float END) as avg_time_minutes
        FROM questions q
        JOIN cos c ON q.co_id = c.id AND c.course_id = $1
    """, (course_id,))

    return {
        "course_id": course_id,
        "question_types": dict(type_stats_result.fetchall()),
        "difficulty_distribution": dict(difficulty_stats_result.fetchall()),
        "co_mapping": [dict(row) for row in co_stats_result.fetchall()],
        "ai_stats": ai_stats_result.fetchone(),
        "contributing_teachers": 0,  # To be implemented with user-course mapping
        "last_updated": datetime.utcnow().isoformat()
    }

@router.get("/search", summary="Search questions in bank", tags=["Questions"])
async def search_questions(
    query: str,
    course_id: Optional[int] = None,
    co_id: Optional[int] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("read_question"))
):
    """Advanced search for questions in the question bank"""

    from sqlalchemy import text
    conditions = ["1=1"]
    params = {}

    # Basic text search in question text, options, and meta
    if query:
        conditions.append("""
            (q.text ILIKE :query
             OR q.meta->>'topics' ILIKE :query
             OR EXISTS (
                 SELECT 1 FROM question_options qo
                 WHERE qo.question_id = q.id AND qo.text ILIKE :query
             ))
        """)
        params["query"] = f"%{query}%"

    if course_id:
        conditions.append("c.course_id = :course_id")
        params["course_id"] = course_id

    if co_id:
        conditions.append("q.co_id = :co_id")
        params["co_id"] = co_id

    if question_type:
        conditions.append("q.type = :question_type")
        params["question_type"] = question_type

    if difficulty:
        conditions.append("q.meta->>'difficulty' = :difficulty")
        params["difficulty"] = difficulty

    where_clause = " AND ".join(conditions)

    # Get total count
    count_query = f"""
        SELECT COUNT(*)
        FROM questions q
        LEFT JOIN cos c ON q.co_id = c.id
        WHERE {where_clause}
    """

    count_result = await db.execute(text(count_query), params)
    total = count_result.scalar()

    # Get results with pagination
    search_query = f"""
        SELECT
            q.id, q.text, q.type, q.max_marks, q.co_id, q.created_at,
            q.meta, c.code as co_code, u.name as creator_name,
            (SELECT COUNT(*) FROM question_options qo WHERE qo.question_id = q.id) as option_count
        FROM questions q
        LEFT JOIN cos c ON q.co_id = c.id
        LEFT JOIN users u ON q.created_by = u.id
        WHERE {where_clause}
        ORDER BY q.created_at DESC
        LIMIT :limit OFFSET :skip
    """

    params.update({"limit": limit, "skip": skip})
    result = await db.execute(text(search_query), params)
    questions = result.fetchall()

    return {
        "query": query,
        "total": total,
        "questions": [dict(q) for q in questions],
        "skip": skip,
        "limit": limit
    }

from datetime import datetime  # Import needed for timestamp
from ..core.dependencies import require_permission
from ..core.audit import log_audit_event, AUDIT_ACTIONS
import logging

logger = logging.getLogger(__name__)
