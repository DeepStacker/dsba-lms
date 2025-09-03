from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from ..core.database import get_db
from ..core.dependencies import require_permission
from ..models import Program, PO, Course, CO, CO_PO_Map
from ..schemas.program import (
    Program, ProgramCreate, ProgramUpdate,
    PO, POCreate, POUpdate,
    Course, CourseCreate, CourseUpdate,
    CO, COCreate, COUpdate,
    CO_PO_Map, CO_PO_MapCreate, CO_PO_MapUpdate
)

router = APIRouter()

# Program endpoints
@router.get("/programs", response_model=List[Program])
async def get_programs(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_program"))
):
    result = await db.execute(select(Program))
    return result.scalars().all()

@router.post("/programs", response_model=Program)
async def create_program(
    program: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_program"))
):
    db_program = Program(**program.dict())
    db.add(db_program)
    await db.commit()
    await db.refresh(db_program)
    return db_program

@router.get("/programs/{program_id}", response_model=Program)
async def get_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_program"))
):
    result = await db.execute(select(Program).where(Program.id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program

@router.put("/programs/{program_id}", response_model=Program)
async def update_program(
    program_id: int,
    program_update: ProgramUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_program"))
):
    result = await db.execute(select(Program).where(Program.id == program_id))
    db_program = result.scalar_one_or_none()
    if not db_program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    for field, value in program_update.dict(exclude_unset=True).items():
        setattr(db_program, field, value)
    
    await db.commit()
    await db.refresh(db_program)
    return db_program

# PO endpoints
@router.get("/programs/{program_id}/pos", response_model=List[PO])
async def get_pos(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_po"))
):
    result = await db.execute(select(PO).where(PO.program_id == program_id))
    return result.scalars().all()

@router.post("/programs/{program_id}/pos", response_model=PO)
async def create_po(
    program_id: int,
    po: POCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_po"))
):
    # Verify program exists
    result = await db.execute(select(Program).where(Program.id == program_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Program not found")
    
    db_po = PO(**po.dict())
    db.add(db_po)
    await db.commit()
    await db.refresh(db_po)
    return db_po

# Course endpoints
@router.get("/programs/{program_id}/courses", response_model=List[Course])
async def get_courses(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_course"))
):
    result = await db.execute(select(Course).where(Course.program_id == program_id))
    return result.scalars().all()

@router.post("/programs/{program_id}/courses", response_model=Course)
async def create_course(
    program_id: int,
    course: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_course"))
):
    # Verify program exists
    result = await db.execute(select(Program).where(Program.id == program_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Program not found")
    
    db_course = Course(**course.dict())
    db.add(db_course)
    await db.commit()
    await db.refresh(db_course)
    return db_course

# CO endpoints
@router.get("/courses/{course_id}/cos", response_model=List[CO])
async def get_cos(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_co"))
):
    result = await db.execute(select(CO).where(CO.course_id == course_id))
    return result.scalars().all()

@router.post("/courses/{course_id}/cos", response_model=CO)
async def create_co(
    course_id: int,
    co: COCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_co"))
):
    # Verify course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    
    db_co = CO(**co.dict())
    db.add(db_co)
    await db.commit()
    await db.refresh(db_co)
    return db_co

# CO-PO Map endpoints
@router.get("/co_po_maps", response_model=List[CO_PO_Map])
async def get_co_po_maps(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_co_po"))
):
    result = await db.execute(select(CO_PO_Map))
    return result.scalars().all()

@router.post("/co_po_maps", response_model=CO_PO_Map)
async def create_co_po_map(
    co_po_map: CO_PO_MapCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_co_po"))
):
    # Verify CO and PO exist
    co_result = await db.execute(select(CO).where(CO.id == co_po_map.co_id))
    if not co_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="CO not found")
    
    po_result = await db.execute(select(PO).where(PO.id == co_po_map.po_id))
    if not po_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="PO not found")
    
    db_map = CO_PO_Map(**co_po_map.dict())
    db.add(db_map)
    await db.commit()
    await db.refresh(db_map)
    return db_map