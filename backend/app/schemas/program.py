from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Program schemas
class ProgramBase(BaseModel):
    name: str
    year: int

class ProgramCreate(ProgramBase):
    pass

class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None

class Program(ProgramBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# PO schemas
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

class PO(POBase):
    id: int
    program_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Course schemas
class CourseBase(BaseModel):
    code: str
    title: str
    credits: float

class CourseCreate(CourseBase):
    program_id: int

class CourseUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    credits: Optional[float] = None

class Course(CourseBase):
    id: int
    program_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# CO schemas
class COBase(BaseModel):
    code: str
    title: str
    bloom: str
    version: int = 1

class COCreate(COBase):
    course_id: int

class COUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    bloom: Optional[str] = None
    version: Optional[int] = None

class CO(COBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# CO_PO_Map schemas
class CO_PO_MapBase(BaseModel):
    weight: float

class CO_PO_MapCreate(CO_PO_MapBase):
    co_id: int
    po_id: int

class CO_PO_MapUpdate(BaseModel):
    weight: Optional[float] = None

class CO_PO_Map(CO_PO_MapBase):
    id: int
    co_id: int
    po_id: int
    created_at: datetime

    class Config:
        from_attributes = True