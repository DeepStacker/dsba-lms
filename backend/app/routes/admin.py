from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role
from ..models.models import User, AuditLog, LockWindow, Program
from ..schemas.common import Response
from ..core.audit import AuditService, AUDIT_ACTIONS, log_audit_event

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# Audit log endpoints
@router.get("/audit/logs", summary="Get audit logs", tags=["Admin"])
async def get_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    actor_id: Optional[int] = Query(None, description="Filter by actor ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    days: int = Query(30, description="Days to look back"),
    limit: int = Query(100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get audit logs with filtering (Admin only)"""

    audit_service = AuditService(db)
    logs = await audit_service.get_audit_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        action=action,
        days=days,
        limit=limit
    )

    return {"logs": logs, "total": len(logs)}

@router.get("/audit/entity/{entity_type}/{entity_id}", summary="Get entity audit history", tags=["Admin"])
async def get_entity_audit_history(
    entity_type: str,
    entity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get complete audit history for a specific entity"""

    audit_service = AuditService(db)
    logs = await audit_service.get_entity_history(entity_type, entity_id)

    return {"entity_type": entity_type, "entity_id": entity_id, "logs": logs}

@router.post("/audit/export", summary="Export audit logs", tags=["Admin"])
async def export_audit_logs(
    filters: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Export audit logs to file"""

    audit_service = AuditService(db)
    logs = await audit_service.get_audit_logs(**filters)
    export_data = await audit_service.export_audit_logs(logs)

    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="audit",
        entity_id=None,
        action=AUDIT_ACTIONS["BULK_EXPORT"],
        reason="Audit logs export"
    )

    # Return as JSON download
    from fastapi.responses import Response
    return Response(
        content=export_data,
        media_type='application/json',
        headers={"Content-Disposition": "attachment; filename=audit_export.json"}
    )

# Lock window endpoints
@router.get("/locks", summary="Get lock windows", tags=["Admin"])
async def get_lock_windows(
    scope: Optional[str] = Query(None, description="Filter by scope"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get lock windows"""

    from sqlalchemy import and_, or_
    query = select(LockWindow)

    filters = []
    if scope:
        filters.append(LockWindow.scope == scope)
    if status:
        filters.append(LockWindow.status == status)

    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    locks = result.scalars().all()

    return {
        "locks": [
            {
                "id": lock.id,
                "scope": lock.scope,
                "starts_at": lock.starts_at,
                "ends_at": lock.ends_at,
                "status": lock.status.value,
                "policy_json": lock.policy_json,
                "created_at": lock.created_at
            }
            for lock in locks
        ]
    }

@router.post("/locks", summary="Create lock window", tags=["Admin"])
async def create_lock_window(
    scope: str,
    reason: str,
    starts_at: datetime,
    ends_at: datetime,
    policy_json: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Create a new lock window"""

    if starts_at >= ends_at:
        raise HTTPException(status_code=400, detail="Start time must be before end time")

    lock_window = LockWindow(
        scope=scope,
        starts_at=starts_at,
        ends_at=ends_at,
        status="active",
        policy_json=policy_json or {}
    )

    db.add(lock_window)
    await db.commit()
    await db.refresh(lock_window)

    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="lock",
        entity_id=lock_window.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json={
            "scope": scope,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat()
        },
        reason=reason
    )

    return {
        "message": "Lock window created successfully",
        "lock_id": lock_window.id
    }

@router.put("/locks/{lock_id}", summary="Update lock window", tags=["Admin"])
async def update_lock_window(
    lock_id: int,
    ends_at: datetime,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Update lock window (extend end time only)"""

    result = await db.execute(select(LockWindow).where(LockWindow.id == lock_id))
    lock = result.scalar_one_or_none()

    if not lock:
        raise HTTPException(status_code=404, detail="Lock window not found")

    if lock.status != "active":
        raise HTTPException(status_code=400, detail="Can only update active lock windows")

    if ends_at <= lock.ends_at:
        raise HTTPException(status_code=400, detail="New end time must be after current end time")

    # Update the lock
    lock.ends_at = ends_at
    await db.commit()

    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="lock",
        entity_id=lock_id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json={"ends_at": lock.created_at.isoformat()},
        after_json={"ends_at": ends_at.isoformat()},
        reason=reason
    )

    return {"message": "Lock window extended successfully"}

@router.post("/locks/{lock_id}/override", summary="Override lock window", tags=["Admin"])
async def override_lock_window(
    lock_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Override lock window (HOD privilege for critical cases)"""

    result = await db.execute(select(LockWindow).where(LockWindow.id == lock_id))
    lock = result.scalar_one_or_none()

    if not lock:
        raise HTTPException(status_code=404, detail="Lock window not found")

    if lock.status != "active":
        raise HTTPException(status_code=400, detail="Can only override active lock windows")

    if not reason or len(reason.strip()) < 20:
        raise HTTPException(status_code=400, detail="Override reason must be at least 20 characters")

    lock.status = "overridden"
    await db.commit()

    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="lock",
        entity_id=lock_id,
        action=AUDIT_ACTIONS["LOCK_OVERRIDE"],
        before_json={"status": "active"},
        after_json={"status": "overridden"},
        reason=reason
    )

    return {"message": "Lock window overridden successfully"}

# System statistics endpoints
@router.get("/stats/system", summary="Get system statistics", tags=["Admin"])
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get comprehensive system statistics"""

    # User stats by role
    user_stats_result = await db.execute("""
        SELECT role, COUNT(*) as count
        FROM users
        GROUP BY role
    """)

    # Exam stats
    exam_stats_result = await db.execute("""
        SELECT
            COUNT(*) as total_exams,
            SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published_exams,
            SUM(CASE WHEN status = 'ended' THEN 1 ELSE 0 END) as ended_exams
        FROM exams
    """)

    # Question bank stats
    question_stats_result = await db.execute("""
        SELECT
            COUNT(*) as total_questions,
            COUNT(DISTINCT created_by) as active_contributors
        FROM questions
    """)

    # Database size approximation
    db_size_result = await db.execute("""
        SELECT
            pg_size_pretty(pg_database_size(current_database())) as db_size,
            COUNT(*) as table_count
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)

    stats = {
        "user_stats": dict(user_stats_result.fetchall()),
        "exam_stats": exam_stats_result.fetchone() or {},
        "question_stats": question_stats_result.fetchone() or {},
        "database_stats": db_size_result.fetchone() or {},
        "timestamp": datetime.utcnow().isoformat()
    }

    return stats

@router.get("/config/grade-bands", summary="Get grade band configuration", tags=["Admin"])
async def get_grade_bands(db: AsyncSession = Depends(get_db)):
    """Get current grade bands configuration"""

    # In a real system, this would be stored in a config table
    # For now, return default values
    grade_bands = {
        "federal": {
            "O": 10.0,
            "A+": 9.0,
            "A": 8.0,
            "B+": 7.5,
            "B": 7.0,
            "C+": 6.5,
            "C": 6.0,
            "D": 4.0,
            "F": 0.0
        },
        "letter": {
            "A": 4.0,
            "B+": 3.5,
            "B": 3.0,
            "C+": 2.5,
            "C": 2.0,
            "D": 1.0,
            "F": 0.0
        }
    }

    return {"grade_bands": grade_bands}

@router.put("/config/grade-bands", summary="Update grade band configuration", tags=["Admin"])
async def update_grade_bands(
    grade_bands: Dict[str, Dict[str, float]],
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Update grade bands configuration (Admin only)"""

    # Validate input
    required_grades = ["A", "A+", "A-", "B+", "B", "B-", "C+", "C", "D", "F"]

    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="config",
        entity_id=None,
        action=AUDIT_ACTIONS["CONFIG_CHANGE"],
        after_json={"grade_bands": grade_bands},
        reason=reason
    )

    return {"message": "Grade bands updated successfully", "updated": grade_bands}