from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from datetime import datetime
from ..core.database import get_db
from ..core.dependencies import require_permission
from ..models import Exam, Attempt, Response, ProctorLog
from ..schemas.exam import (
    Exam, ExamCreate, ExamUpdate,
    Attempt, AttemptCreate, AttemptUpdate,
    Response, ResponseCreate, ResponseUpdate,
    ProctorLog, ProctorLogCreate
)

router = APIRouter()

# Exam endpoints
@router.get("/exams", response_model=List[Exam])
async def get_exams(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_exam"))
):
    result = await db.execute(select(Exam))
    return result.scalars().all()

@router.post("/exams", response_model=Exam)
async def create_exam(
    exam: ExamCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_exam"))
):
    db_exam = Exam(**exam.dict())
    db.add(db_exam)
    await db.commit()
    await db.refresh(db_exam)
    return db_exam

@router.get("/exams/{exam_id}", response_model=Exam)
async def get_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_exam"))
):
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam

@router.put("/exams/{exam_id}", response_model=Exam)
async def update_exam(
    exam_id: int,
    exam_update: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("write_exam"))
):
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    db_exam = result.scalar_one_or_none()
    if not db_exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    for field, value in exam_update.dict(exclude_unset=True).items():
        setattr(db_exam, field, value)
    
    await db.commit()
    await db.refresh(db_exam)
    return db_exam

# Attempt endpoints
@router.get("/exams/{exam_id}/attempts", response_model=List[Attempt])
async def get_exam_attempts(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_exam"))
):
    result = await db.execute(select(Attempt).where(Attempt.exam_id == exam_id))
    return result.scalars().all()

@router.post("/attempts", response_model=Attempt)
async def create_attempt(
    attempt: AttemptCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("attempt_exam"))
):
    # Verify exam exists and is active
    result = await db.execute(select(Exam).where(Exam.id == attempt.exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    now = datetime.utcnow()
    if now < exam.start_at or now > exam.end_at:
        raise HTTPException(status_code=400, detail="Exam not active")
    
    db_attempt = Attempt(**attempt.dict(), started_at=now)
    db.add(db_attempt)
    await db.commit()
    await db.refresh(db_attempt)
    return db_attempt

@router.put("/attempts/{attempt_id}", response_model=Attempt)
async def update_attempt(
    attempt_id: int,
    attempt_update: AttemptUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("attempt_exam"))
):
    result = await db.execute(select(Attempt).where(Attempt.id == attempt_id))
    db_attempt = result.scalar_one_or_none()
    if not db_attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    for field, value in attempt_update.dict(exclude_unset=True).items():
        setattr(db_attempt, field, value)
    
    await db.commit()
    await db.refresh(db_attempt)
    return db_attempt

# Response endpoints
@router.get("/attempts/{attempt_id}/responses", response_model=List[Response])
async def get_attempt_responses(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_exam"))
):
    result = await db.execute(select(Response).where(Response.attempt_id == attempt_id))
    return result.scalars().all()

@router.post("/responses", response_model=Response)
async def create_response(
    response: ResponseCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("attempt_exam"))
):
    # Verify attempt exists
    result = await db.execute(select(Attempt).where(Attempt.id == response.attempt_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    db_response = Response(**response.dict())
    db.add(db_response)
    await db.commit()
    await db.refresh(db_response)
    return db_response

@router.put("/responses/{response_id}", response_model=Response)
async def update_response(
    response_id: int,
    response_update: ResponseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("grade"))
):
    result = await db.execute(select(Response).where(Response.id == response_id))
    db_response = result.scalar_one_or_none()
    if not db_response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    for field, value in response_update.dict(exclude_unset=True).items():
        setattr(db_response, field, value)
    
    await db.commit()
    await db.refresh(db_response)
    return db_response

# Proctor log endpoints
@router.get("/attempts/{attempt_id}/proctor_logs", response_model=List[ProctorLog])
async def get_proctor_logs(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("read_exam"))
):
    result = await db.execute(select(ProctorLog).where(ProctorLog.attempt_id == attempt_id))
    return result.scalars().all()

@router.post("/proctor_logs", response_model=ProctorLog)
async def create_proctor_log(
    proctor_log: ProctorLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("attempt_exam"))
):
    # Verify attempt exists
    result = await db.execute(select(Attempt).where(Attempt.id == proctor_log.attempt_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    db_log = ProctorLog(**proctor_log.dict())
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log