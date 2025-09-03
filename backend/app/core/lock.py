from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .config import settings
from .audit import log_audit_event
from ..models import LockWindow

async def check_lock_status(
    db: AsyncSession,
    entity_type: str,
    entity_id: int
) -> bool:
    """Check if an entity is currently locked"""
    now = datetime.utcnow()

    result = await db.execute(
        select(LockWindow).where(
            LockWindow.scope == f"{entity_type}:{entity_id}",
            LockWindow.status == "active",
            LockWindow.starts_at <= now,
            LockWindow.ends_at >= now
        )
    )

    lock = result.scalar_one_or_none()
    return lock is not None

async def create_lock_window(
    db: AsyncSession,
    scope: str,
    policy_json: Optional[dict] = None
) -> LockWindow:
    """Create a lock window for an entity"""
    default_days = settings.lock_default_days
    starts_at = datetime.utcnow()
    ends_at = starts_at + timedelta(days=default_days)

    # Check for weekly Saturday lock
    if settings.weekly_lock_saturday and starts_at.weekday() == 5:  # Saturday
        # Lock until next Sunday 23:59
        days_until_sunday = (6 - starts_at.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        ends_at = starts_at.replace(hour=23, minute=59, second=59) + timedelta(days=days_until_sunday)

    lock_window = LockWindow(
        scope=scope,
        starts_at=starts_at,
        ends_at=ends_at,
        status="active",
        policy_json=policy_json
    )

    db.add(lock_window)
    await db.commit()
    await db.refresh(lock_window)
    return lock_window

async def override_lock(
    db: AsyncSession,
    lock_id: int,
    actor_id: int,
    reason: str
) -> bool:
    """Override a lock window with audit logging"""
    result = await db.execute(select(LockWindow).where(LockWindow.id == lock_id))
    lock = result.scalar_one_or_none()

    if not lock:
        return False

    # Log the override
    await log_audit_event(
        db=db,
        actor_id=actor_id,
        entity_type="lock_window",
        entity_id=lock_id,
        action="override",
        before_json={"status": lock.status, "ends_at": lock.ends_at.isoformat()},
        after_json={"status": "overridden"},
        reason=reason
    )

    lock.status = "overridden"
    await db.commit()
    return True

async def extend_lock(
    db: AsyncSession,
    lock_id: int,
    additional_days: int,
    actor_id: int,
    reason: str
) -> bool:
    """Extend a lock window"""
    result = await db.execute(select(LockWindow).where(LockWindow.id == lock_id))
    lock = result.scalar_one_or_none()

    if not lock:
        return False

    old_end = lock.ends_at
    lock.ends_at = lock.ends_at + timedelta(days=additional_days)

    # Log the extension
    await log_audit_event(
        db=db,
        actor_id=actor_id,
        entity_type="lock_window",
        entity_id=lock_id,
        action="extend",
        before_json={"ends_at": old_end.isoformat()},
        after_json={"ends_at": lock.ends_at.isoformat()},
        reason=reason
    )

    await db.commit()
    return True

def is_weekly_lock_day() -> bool:
    """Check if today is a weekly lock day (Saturday)"""
    return settings.weekly_lock_saturday and datetime.utcnow().weekday() == 5