from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
import httpx
from pydantic import BaseModel
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.config import settings
from ..models.models import User, Course, CO, Question, Response, Attempt
from ..schemas.common import Response as CommonResponse

router = APIRouter()

# ==================== AI SERVICE MODELS ====================

class AIQuestionGenerationRequest(BaseModel):
    course_id: int
    syllabus: str
    topics: List[str]
    question_types: List[str]  # mcq, descriptive, coding, etc.
    difficulty_distribution: Dict[str, int]  # easy: 5, medium: 3, hard: 2
    total_questions: int
    marks_per_question: float
    bloom_levels: List[str]
    co_mapping: bool = True

class AIContentGenerationRequest(BaseModel):
    course_id: int
    topic: str
    content_type: str  # lesson_plan, notes, slides, quiz
    length: str  # short, medium, long
    difficulty: str  # beginner, intermediate, advanced
    include_examples: bool = True
    include_exercises: bool = True

class AIStudyPlanRequest(BaseModel):
    student_id: int
    weak_topics: List[str]
    available_time_hours: int
    learning_style: str  # visual, auditory, kinesthetic, reading
    target_improvement: float  # percentage improvement target

class AIDoubtBotRequest(BaseModel):
    query: str
    course_id: int
    context: Optional[Dict[str, Any]] = None  # Previous conversation, current topic, etc.

class AIPerformanceAnalysisRequest(BaseModel):
    student_id: int
    exam_ids: List[int]
    analysis_type: str  # strengths_weaknesses, learning_gaps, prediction

# ==================== AI QUESTION GENERATION ====================

@router.post("/generate-questions")
async def generate_questions(
    request: AIQuestionGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("ai_generate_questions"))
):
    """Generate questions using AI"""
    # Verify course exists and get course details
    course_result = await db.execute(
        select(Course).options(selectinload(Course.cos)).where(Course.id == request.course_id)
    )
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Prepare AI service request
    ai_request = {
        "course_id": request.course_id,
        "course_name": course.title,
        "course_code": course.code,
        "syllabus": request.syllabus,
        "topics": request.topics,
        "question_types": request.question_types,
        "difficulty_distribution": request.difficulty_distribution,
        "total_questions": request.total_questions,
        "marks_per_question": request.marks_per_question,
        "bloom_levels": request.bloom_levels,
        "co_mapping": request.co_mapping,
        "available_cos": [
            {
                "id": co.id,
                "code": co.code,
                "title": co.title,
                "bloom": co.bloom
            } for co in course.cos
        ] if request.co_mapping else []
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ai_service_url}/api/generate-questions",
                json=ai_request,
                headers={
                    "Authorization": f"Bearer {settings.ai_service_token}",
                    "Content-Type": "application/json"
                },
                timeout=300  # 5 minutes timeout
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI service error: {response.text}"
                )
            
            ai_response = response.json()
            
            return {
                "success": True,
                "questions": ai_response.get("questions", []),
                "metadata": ai_response.get("metadata", {}),
                "generation_stats": ai_response.get("stats", {})
            }
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )

# ==================== AI CONTENT GENERATION ====================

@router.post("/generate-content")
async def generate_content(
    request: AIContentGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("generate_lesson_content"))
):
    """Generate educational content using AI"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == request.course_id))
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Prepare AI service request
    ai_request = {
        "course_id": request.course_id,
        "course_name": course.title,
        "course_code": course.code,
        "topic": request.topic,
        "content_type": request.content_type,
        "length": request.length,
        "difficulty": request.difficulty,
        "include_examples": request.include_examples,
        "include_exercises": request.include_exercises,
        "teacher_id": current_user.id
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ai_service_url}/api/generate-content",
                json=ai_request,
                headers={
                    "Authorization": f"Bearer {settings.ai_service_token}",
                    "Content-Type": "application/json"
                },
                timeout=180  # 3 minutes timeout
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI service error: {response.text}"
                )
            
            ai_response = response.json()
            
            return {
                "success": True,
                "content": ai_response.get("content", ""),
                "content_type": request.content_type,
                "metadata": ai_response.get("metadata", {}),
                "suggestions": ai_response.get("suggestions", [])
            }
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )

# ==================== AI STUDY PLAN ====================

@router.post("/create-study-plan")
async def create_study_plan(
    request: AIStudyPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create personalized study plan using AI"""
    # Verify student exists (or current user is the student)
    if current_user.role.value == "student":
        if request.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create study plan for yourself"
            )
    else:
        # Teachers/Admins can create study plans for any student
        student_result = await db.execute(select(User).where(User.id == request.student_id))
        if not student_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Student not found")
    
    # Get student's recent performance data
    recent_attempts_result = await db.execute(
        select(Attempt, Response)
        .join(Response, Response.attempt_id == Attempt.id)
        .where(Attempt.student_id == request.student_id)
        .order_by(Attempt.submitted_at.desc())
        .limit(100)  # Last 100 responses
    )
    
    performance_data = []
    for attempt, response in recent_attempts_result.all():
        if response.final_score is not None:
            performance_data.append({
                "exam_id": attempt.exam_id,
                "question_id": response.question_id,
                "score": response.final_score,
                "max_marks": response.question.max_marks if hasattr(response, 'question') else 0,
                "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None
            })
    
    # Prepare AI service request
    ai_request = {
        "student_id": request.student_id,
        "weak_topics": request.weak_topics,
        "available_time_hours": request.available_time_hours,
        "learning_style": request.learning_style,
        "target_improvement": request.target_improvement,
        "performance_data": performance_data
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ai_service_url}/api/create-study-plan",
                json=ai_request,
                headers={
                    "Authorization": f"Bearer {settings.ai_service_token}",
                    "Content-Type": "application/json"
                },
                timeout=120  # 2 minutes timeout
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI service error: {response.text}"
                )
            
            ai_response = response.json()
            
            return {
                "success": True,
                "study_plan": ai_response.get("study_plan", {}),
                "recommendations": ai_response.get("recommendations", []),
                "timeline": ai_response.get("timeline", []),
                "resources": ai_response.get("resources", [])
            }
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )

# ==================== AI DOUBT BOT ====================

@router.post("/doubt-bot")
async def query_doubt_bot(
    request: AIDoubtBotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Query AI doubt bot for course-related questions"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == request.course_id))
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if user has access to this course
    if current_user.role.value == "student":
        # Check if student is enrolled
        from ..models.models import Enrollment, ClassSection
        enrollment_result = await db.execute(
            select(Enrollment)
            .join(ClassSection, Enrollment.class_id == ClassSection.id)
            .where(
                and_(
                    ClassSection.course_id == request.course_id,
                    Enrollment.student_id == current_user.id
                )
            )
        )
        if not enrollment_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
    
    # Prepare AI service request
    ai_request = {
        "query": request.query,
        "course_id": request.course_id,
        "course_name": course.title,
        "course_code": course.code,
        "user_id": current_user.id,
        "user_role": current_user.role.value,
        "context": request.context or {}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ai_service_url}/api/doubt-bot",
                json=ai_request,
                headers={
                    "Authorization": f"Bearer {settings.ai_service_token}",
                    "Content-Type": "application/json"
                },
                timeout=60  # 1 minute timeout
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI service error: {response.text}"
                )
            
            ai_response = response.json()
            
            return {
                "success": True,
                "answer": ai_response.get("answer", ""),
                "confidence": ai_response.get("confidence", 0),
                "sources": ai_response.get("sources", []),
                "follow_up_questions": ai_response.get("follow_up_questions", []),
                "context": ai_response.get("context", {})
            }
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )

# ==================== AI PERFORMANCE ANALYSIS ====================

@router.post("/analyze-performance")
async def analyze_performance(
    request: AIPerformanceAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_student_progress"))
):
    """Analyze student performance using AI"""
    # Verify student exists
    student_result = await db.execute(select(User).where(User.id == request.student_id))
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get performance data for specified exams
    performance_result = await db.execute(
        select(Attempt, Response, Question, CO)
        .join(Response, Response.attempt_id == Attempt.id)
        .join(Question, Response.question_id == Question.id)
        .outerjoin(CO, Question.co_id == CO.id)
        .where(
            and_(
                Attempt.student_id == request.student_id,
                Attempt.exam_id.in_(request.exam_ids),
                Response.final_score.isnot(None)
            )
        )
        .order_by(Attempt.submitted_at)
    )
    
    performance_data = []
    for attempt, response, question, co in performance_result.all():
        performance_data.append({
            "exam_id": attempt.exam_id,
            "question_id": question.id,
            "question_type": question.type.value,
            "co_id": co.id if co else None,
            "co_code": co.code if co else None,
            "bloom_level": co.bloom if co else None,
            "score": response.final_score,
            "max_marks": question.max_marks,
            "percentage": (response.final_score / question.max_marks) * 100,
            "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None
        })
    
    if not performance_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No performance data found for the specified exams"
        )
    
    # Prepare AI service request
    ai_request = {
        "student_id": request.student_id,
        "student_name": student.name,
        "exam_ids": request.exam_ids,
        "analysis_type": request.analysis_type,
        "performance_data": performance_data
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ai_service_url}/api/analyze-performance",
                json=ai_request,
                headers={
                    "Authorization": f"Bearer {settings.ai_service_token}",
                    "Content-Type": "application/json"
                },
                timeout=120  # 2 minutes timeout
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI service error: {response.text}"
                )
            
            ai_response = response.json()
            
            return {
                "success": True,
                "analysis": ai_response.get("analysis", {}),
                "strengths": ai_response.get("strengths", []),
                "weaknesses": ai_response.get("weaknesses", []),
                "recommendations": ai_response.get("recommendations", []),
                "predictions": ai_response.get("predictions", {}),
                "learning_gaps": ai_response.get("learning_gaps", [])
            }
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )

# ==================== AI SERVICE HEALTH CHECK ====================

@router.get("/health")
async def check_ai_service_health():
    """Check AI service health"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ai_service_url}/health",
                headers={"Authorization": f"Bearer {settings.ai_service_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "ai_service": "available",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "degraded",
                    "ai_service": "error",
                    "error": response.text
                }
    
    except httpx.RequestError as e:
        return {
            "status": "unhealthy",
            "ai_service": "unavailable",
            "error": str(e)
        }