from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class InternalComponentBase(BaseModel):
    name: str
    weight_percent: float = Field(..., ge=0, le=100)

class InternalComponentCreate(InternalComponentBase):
    course_id: int

class InternalComponentUpdate(BaseModel):
    name: Optional[str] = None
    weight_percent: Optional[float] = Field(None, ge=0, le=100)

class InternalComponent(InternalComponentBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class InternalScoreBase(BaseModel):
    raw_score: float = Field(..., ge=0)
    max_score: float = Field(..., gt=0)

class InternalScoreCreate(InternalScoreBase):
    student_id: int
    course_id: int
    component_id: int

class InternalScoreUpdate(BaseModel):
    raw_score: Optional[float] = Field(None, ge=0)
    max_score: Optional[float] = Field(None, gt=0)

class InternalScore(InternalScoreBase):
    id: int
    student_id: int
    course_id: int
    component_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class StudentInternalMarks(BaseModel):
    student_id: int
    student_name: str
    course_code: str
    course_title: str
    components: List[Dict[str, Any]]
    total_internal_percentage: float
    grade: str

class InternalMarksReport(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    students: List[StudentInternalMarks]
    component_weights: Dict[str, float]
    generated_at: datetime