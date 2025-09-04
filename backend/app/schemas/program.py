from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class ProgramBase(BaseModel):
    name: str
    year: int

    @validator('year')
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v < 2000 or v > current_year + 10:
            raise ValueError('Year must be between 2000 and current year + 10')
        return v

class ProgramCreate(ProgramBase):
    pass

class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None

    @validator('year')
    def validate_year(cls, v):
        if v is not None:
            current_year = datetime.now().year
            if v < 2000 or v > current_year + 10:
                raise ValueError('Year must be between 2000 and current year + 10')
        return v

class ProgramResponse(ProgramBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class POBase(BaseModel):
    code: str
    title: str
    version: int = 1

class POCreate(POBase):
    program_id: int

class POUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    version: Optional[int] = None

class POResponse(POBase):
    id: int
    program_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    code: str
    title: str
    credits: float

    @validator('credits')
    def validate_credits(cls, v):
        if v <= 0 or v > 10:
            raise ValueError('Credits must be between 0 and 10')
        return v

class CourseCreate(CourseBase):
    program_id: int

class CourseUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    credits: Optional[float] = None
    program_id: Optional[int] = None

    @validator('credits')
    def validate_credits(cls, v):
        if v is not None and (v <= 0 or v > 10):
            raise ValueError('Credits must be between 0 and 10')
        return v

class CourseResponse(CourseBase):
    id: int
    program_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class COBase(BaseModel):
    code: str
    title: str
    bloom: str
    version: int = 1

    @validator('bloom')
    def validate_bloom(cls, v):
        valid_levels = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
        if v.lower() not in valid_levels:
            raise ValueError(f'Bloom level must be one of: {", ".join(valid_levels)}')
        return v.lower()

class COCreate(COBase):
    course_id: int

class COUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    bloom: Optional[str] = None
    version: Optional[int] = None

    @validator('bloom')
    def validate_bloom(cls, v):
        if v is not None:
            valid_levels = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
            if v.lower() not in valid_levels:
                raise ValueError(f'Bloom level must be one of: {", ".join(valid_levels)}')
            return v.lower()
        return v

class COResponse(COBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class COPOMappingBase(BaseModel):
    weight: float

    @validator('weight')
    def validate_weight(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Weight must be between 0 and 1')
        return v

class COPOMappingCreate(COPOMappingBase):
    co_id: int
    po_id: int

class COPOMappingUpdate(BaseModel):
    weight: Optional[float] = None

    @validator('weight')
    def validate_weight(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Weight must be between 0 and 1')
        return v

class COPOMappingResponse(COPOMappingBase):
    id: int
    co_id: int
    po_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class COPOMatrixResponse(BaseModel):
    course_id: int
    course_name: str
    cos: List[COResponse]
    pos: List[POResponse]
    mappings: List[COPOMappingResponse]
    matrix: List[List[float]]  # 2D matrix of weights

class ClassSectionBase(BaseModel):
    name: str
    term: str
    year: int

class ClassSectionCreate(ClassSectionBase):
    course_id: int
    coordinator_id: Optional[int] = None

class ClassSectionUpdate(BaseModel):
    name: Optional[str] = None
    term: Optional[str] = None
    year: Optional[int] = None
    coordinator_id: Optional[int] = None

class ClassSectionResponse(ClassSectionBase):
    id: int
    course_id: int
    coordinator_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EnrollmentCreate(BaseModel):
    class_id: int
    student_id: int

class EnrollmentResponse(BaseModel):
    id: int
    class_id: int
    student_id: int
    enrolled_at: datetime
    student_name: Optional[str] = None
    student_email: Optional[str] = None

    class Config:
        from_attributes = True