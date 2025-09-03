from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from .program import CO

# Question schemas
class QuestionBase(BaseModel):
    type: str  # Use str for enum to avoid import issues
    text: str
    max_marks: float
    rubric_json: Optional[Dict[str, Any]] = None
    model_answer: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class QuestionCreate(QuestionBase):
    co_id: Optional[int] = None
    created_by: int

class QuestionUpdate(BaseModel):
    type: Optional[str] = None
    text: Optional[str] = None
    max_marks: Optional[float] = None
    rubric_json: Optional[Dict[str, Any]] = None
    model_answer: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class Question(QuestionBase):
    id: int
    co_id: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    co: Optional[CO] = None

    class Config:
        from_attributes = True

# QuestionOption schemas
class QuestionOptionBase(BaseModel):
    text: str
    is_correct: bool = False

class QuestionOptionCreate(QuestionOptionBase):
    question_id: int

class QuestionOptionUpdate(BaseModel):
    text: Optional[str] = None
    is_correct: Optional[bool] = None

class QuestionOption(QuestionOptionBase):
    id: int
    question_id: int

    class Config:
        from_attributes = True