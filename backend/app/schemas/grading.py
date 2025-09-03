from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class AIGradeRequest(BaseModel):
    strictness: Optional[float] = Field(0.5, description="Strictness level for AI grading (0.1 to 1.0)", ge=0.1, le=1.0)
    custom_prompt: Optional[str] = Field(None, description="Custom grading prompt for AI")
    criteria_weights: Optional[Dict[str, float]] = Field(None, description="Custom weights for grading criteria")

    class Config:
        json_schema_extra = {
            "example": {
                "strictness": 0.5,
                "custom_prompt": "Grade this response based on content quality",
                "criteria_weights": {"content": 0.4, "accuracy": 0.3, "clarity": 0.3}
            }
        }

class GradeResponse(BaseModel):
    response_id: int
    ai_score: Optional[float] = None
    final_score: Optional[float] = None
    teacher_score: Optional[float] = None
    feedback: List[str] = []
    per_criterion: Dict[str, Any] = {}
    graded_at: datetime = Field(default_factory=datetime.utcnow)
    graded_by: str = "ai"

    class Config:
        json_schema_extra = {
            "example": {
                "response_id": 123,
                "ai_score": 8.5,
                "final_score": 8.5,
                "teacher_score": None,
                "feedback": ["Good understanding", "Could improve examples"],
                "per_criterion": {"content": 85, "accuracy": 90, "clarity": 80},
                "graded_at": "2024-09-04T10:30:00Z",
                "graded_by": "ai"
            }
        }

class BulkGradeRequest(BaseModel):
    exam_id: int = Field(..., description="ID of the exam to grade responses")
    strictness: Optional[float] = Field(0.5, description="Default strictness for AI grading")
    question_types: Optional[List[str]] = Field(["descriptive", "coding"], description="Types of questions to grade")
    max_responses_per_batch: Optional[int] = Field(50, description="Maximum responses to grade in one batch")
    skip_already_graded: bool = Field(True, description="Skip responses that already have AI scores")

    class Config:
        json_schema_extra = {
            "example": {
                "exam_id": 123,
                "strictness": 0.5,
                "question_types": ["descriptive"],
                "max_responses_per_batch": 50,
                "skip_already_graded": True
            }
        }

class GradeOverrideRequest(BaseModel):
    response_id: int
    teacher_score: float = Field(..., description="Teacher-assigned score", ge=0)
    reason: str = Field(..., description="Reason for override", min_length=1, max_length=500)
    override_type: Optional[str] = Field("manual", description="Type of override (manual, review, etc)")
    additional_feedback: Optional[str] = Field(None, description="Additional feedback from teacher")

    class Config:
        json_schema_extra = {
            "example": {
                "response_id": 123,
                "teacher_score": 9.5,
                "reason": "Question interpretation was good despite minor calculation error",
                "override_type": "manual",
                "additional_feedback": "Excellent conceptual understanding, just minor calculation mistakes that can be corrected."
            }
        }

class GradingProgressResponse(BaseModel):
    exam_id: int
    total_responses: int
    ai_graded: int
    manual_graded: int
    fully_graded: int
    completion_percentage: float
    last_update: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "exam_id": 123,
                "total_responses": 100,
                "ai_graded": 75,
                "manual_graded": 15,
                "fully_graded": 85,
                "completion_percentage": 85.0,
                "last_update": "2024-09-04T10:30:00Z"
            }
        }

class AIConfigRequest(BaseModel):
    model: Optional[str] = Field("gpt-4", description="AI model to use (gpt-4, gpt-3.5-turbo, etc.)")
    temperature: Optional[float] = Field(0.1, description="AI temperature setting", ge=0, le=1)
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens for AI response")
    timeout: Optional[int] = Field(30, description="Timeout in seconds for AI request", ge=10, le=300)

    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 1000,
                "timeout": 30
            }
        }
