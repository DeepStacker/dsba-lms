from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.models import QuestionType

class QuestionOptionBase(BaseModel):
    text: str
    is_correct: bool = False

class QuestionOptionCreate(QuestionOptionBase):
    pass

class QuestionOptionUpdate(BaseModel):
    text: Optional[str] = None
    is_correct: Optional[bool] = None

class QuestionOptionResponse(QuestionOptionBase):
    id: int

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    type: QuestionType
    text: str
    max_marks: float
    rubric_json: Optional[Dict[str, Any]] = None
    model_answer: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    @validator('max_marks')
    def validate_max_marks(cls, v):
        if v <= 0:
            raise ValueError('Max marks must be greater than 0')
        return v

class QuestionCreate(QuestionBase):
    co_id: Optional[int] = None
    options: Optional[List[QuestionOptionCreate]] = None

class QuestionUpdate(BaseModel):
    type: Optional[QuestionType] = None
    text: Optional[str] = None
    co_id: Optional[int] = None
    max_marks: Optional[float] = None
    rubric_json: Optional[Dict[str, Any]] = None
    model_answer: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    @validator('max_marks')
    def validate_max_marks(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Max marks must be greater than 0')
        return v

class QuestionResponse(QuestionBase):
    id: int
    co_id: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    options: List[QuestionOptionResponse] = []
    creator_name: Optional[str] = None
    co_code: Optional[str] = None

    class Config:
        from_attributes = True

class QuestionSearchRequest(BaseModel):
    query: Optional[str] = None
    type: Optional[QuestionType] = None
    co_id: Optional[int] = None
    course_id: Optional[int] = None
    created_by: Optional[int] = None
    bloom_level: Optional[str] = None
    difficulty: Optional[str] = None
    max_marks_min: Optional[float] = None
    max_marks_max: Optional[float] = None
    skip: int = 0
    limit: int = 50

class QuestionBulkImportRequest(BaseModel):
    questions: List[QuestionCreate]
    course_id: int
    default_co_id: Optional[int] = None

class QuestionStatsResponse(BaseModel):
    total_questions: int
    by_type: Dict[str, int]
    by_bloom_level: Dict[str, int]
    by_difficulty: Dict[str, int]
    by_co: Dict[str, int]
    avg_marks: float
    recent_additions: int  # Last 7 days

class AIQuestionGenerationRequest(BaseModel):
    course_id: int
    syllabus: str
    topics: List[str]
    question_types: List[QuestionType]
    difficulty_distribution: Dict[str, int]  # easy: 5, medium: 3, hard: 2
    total_questions: int
    marks_per_question: float
    bloom_levels: List[str]
    co_mapping: bool = True

class AIQuestionGenerationResponse(BaseModel):
    generated_questions: List[QuestionResponse]
    generation_metadata: Dict[str, Any]
    success_count: int
    error_count: int
    errors: List[str] = []

class RubricCriterion(BaseModel):
    name: str
    description: str
    max_points: float
    weight: float = 1.0

class RubricCreate(BaseModel):
    question_id: int
    criteria: List[RubricCriterion]
    total_points: float
    strictness: str = "standard"  # lenient, standard, strict

    @validator('strictness')
    def validate_strictness(cls, v):
        if v not in ['lenient', 'standard', 'strict']:
            raise ValueError('Strictness must be lenient, standard, or strict')
        return v

class RubricResponse(BaseModel):
    id: int
    question_id: int
    criteria: List[RubricCriterion]
    total_points: float
    strictness: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True