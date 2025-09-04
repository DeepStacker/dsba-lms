from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class GradeRequest(BaseModel):
    score: float = Field(..., ge=0)
    feedback: Optional[str] = None

class GradeResponse(BaseModel):
    response_id: int
    score: float
    feedback: Optional[str] = None
    graded_by: int
    graded_at: datetime

class AIGradingRequest(BaseModel):
    strictness: str = Field("standard", regex="^(lenient|standard|strict)$")

class AIGradingResponse(BaseModel):
    response_id: int
    ai_score: float
    feedback: List[str]
    confidence: float
    model_used: str
    processing_time: float
    success: bool

class BulkGradeRequest(BaseModel):
    grades: List[Dict[str, Any]]

class BulkGradeResponse(BaseModel):
    batch_id: int
    success_count: int
    error_count: int
    errors: List[str]
    total_processed: int