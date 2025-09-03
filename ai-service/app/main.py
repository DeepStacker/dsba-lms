from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from .core.llm_adapter import get_llm_adapter

app = FastAPI(
    title="Apollo AI Service",
    description="AI-powered grading and content generation service",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth dependency
async def verify_token(x_internal_auth: Optional[str] = Header(None)):
    expected_token = "internal_token_change_me"  # In production, get from config
    if not x_internal_auth or x_internal_auth != expected_token:
        raise HTTPException(status_code=401, detail="Invalid internal auth token")
    return True

# Pydantic models for requests/responses
class GradeRequest(BaseModel):
    answer: str
    model_answer: str
    rubric_json: Dict[str, Any]
    strictness: Optional[float] = 0.5

class GradeResponse(BaseModel):
    ai_score: float
    per_criterion: Dict[str, float]
    feedback_bullets: List[str]
    explanations: str

class GenerateRequest(BaseModel):
    syllabus: str
    topics: List[str]
    counts: Dict[str, int]
    difficulty_mix: Dict[str, float]
    types: List[str]

class QuestionItem(BaseModel):
    id: int
    type: str
    text: str
    co_tags: List[int]
    difficulty: str
    confidence: float
    options: Optional[List[Dict[str, Any]]] = None

class GenerateResponse(BaseModel):
    questions: List[QuestionItem]

class AttainmentRequest(BaseModel):
    co_data: List[Dict[str, Any]]
    po_data: List[Dict[str, Any]]

class AttainmentResponse(BaseModel):
    co_attainments: Dict[int, float]
    po_attainments: Dict[int, float]
    insights: List[str]

# Initialize adapter
llm_adapter = get_llm_adapter("mock")  # Default to mock

@app.post("/grade/descriptive", response_model=GradeResponse)
async def grade_descriptive_answer(
    request: GradeRequest,
    authenticated: bool = Depends(verify_token)
):
    """Grade a descriptive answer using AI"""
    try:
        result = await llm_adapter.grade_descriptive_answer(
            answer=request.answer,
            model_answer=request.model_answer,
            rubric=request.rubric_json,
            strictness=request.strictness
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")

@app.post("/generate/questions", response_model=GenerateResponse)
async def generate_questions(
    request: GenerateRequest,
    authenticated: bool = Depends(verify_token)
):
    """Generate questions using AI"""
    try:
        questions = await llm_adapter.generate_questions(
            syllabus=request.syllabus,
            topics=request.topics,
            counts=request.counts,
            difficulty_mix=request.difficulty_mix,
            types=request.types
        )
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/analyze/attainment", response_model=AttainmentResponse)
async def analyze_attainment(
    request: AttainmentRequest,
    authenticated: bool = Depends(verify_token)
):
    """Analyze CO/PO attainment using AI"""
    try:
        result = await llm_adapter.analyze_attainment(
            co_data=request.co_data,
            po_data=request.po_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-service"}