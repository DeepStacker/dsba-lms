from celery import shared_task
from sqlalchemy.future import select
from datetime import datetime, timedelta
import asyncio
import logging
import json

from ..core.database import async_session
from ..models.models import LockWindow, LockStatus
from ..core.audit import log_audit_event, AUDIT_ACTIONS
from ..schemas.lock_window import LockWindowCreate # Reusing schema for consistency

logger = logging.getLogger(__name__)

async def _get_db_session():
    """Helper to get an async session within a Celery task context."""
    async with async_session() as session:
        yield session

@shared_task(name="lock_window_tasks.create_weekly_grades_lock")
def create_weekly_grades_lock_task():
    logger.info("Checking for weekly grades lock window to create/update...")
    asyncio.run(_create_weekly_grades_lock())

async def _create_weekly_grades_lock():
    async for db in _get_db_session():
        now = datetime.utcnow()
        # Define the weekly lock window: e.g., starts Sunday 00:00 UTC, ends 7 days later
        # For simplicity, let's say it starts every Monday 00:00 UTC for 7 days.
        today_weekday = now.weekday() # Monday is 0
        
        # Calculate start of this week (Monday)
        start_of_week = now - timedelta(days=today_weekday)
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        lock_start_time = start_of_week
        lock_end_time = start_of_week + timedelta(days=7)

        # Check if an active 'grades' lock window already exists for this period or overlaps
        existing_lock_query = select(LockWindow).where(
            LockWindow.scope == "grades",
            LockWindow.starts_at == lock_start_time,
            LockWindow.ends_at == lock_end_time,
            LockWindow.status == LockStatus.ACTIVE
        )
        existing_lock = await db.execute(existing_lock_query)
        if existing_lock.scalars().first():
            logger.info("Active weekly grades lock already exists for this period. No action needed.")
            return

        # If an overlapping active lock (different start/end but same scope) exists, expire it
        overlapping_active_locks_query = select(LockWindow).where(
            LockWindow.scope == "grades",
            LockWindow.status == LockStatus.ACTIVE,
            LockWindow.ends_at > now,
            LockWindow.starts_at < lock_end_time # Check for any overlap
        )
        overlapping_active_locks = (await db.execute(overlapping_active_locks_query)).scalars().all()
        for lock in overlapping_active_locks:
            logger.info(f"Expiring overlapping active grades lock {lock.id} (scope: {lock.scope}).")
            old_data = lock.model_dump_json()
            lock.status = LockStatus.EXPIRED
            lock.updated_at = now
            db.add(lock)
            await log_audit_event(
                db=db,
                actor_id=0, # System actor
                entity_type="lock_window",
                entity_id=lock.id,
                action=AUDIT_ACTIONS["UPDATE"],
                before_json=old_data,
                after_json=lock.model_dump_json(),
                reason="Automatic expiration of overlapping grades lock window"
            )

        # Create a new weekly lock window
        new_lock_data = LockWindowCreate(
            scope="grades",
            starts_at=lock_start_time,
            ends_at=lock_end_time,
            policy_json={"description": "System-generated weekly lock for grades/marks."}
        )
        db_lock_window = LockWindow(**new_lock_data.model_dump())
        db.add(db_lock_window)
        await db.commit()
        await db.refresh(db_lock_window)
        
        await log_audit_event(
            db=db,
            actor_id=0, # System actor
            entity_type="lock_window",
            entity_id=db_lock_window.id,
            action=AUDIT_ACTIONS["CREATE"],
            after_json=db_lock_window.model_dump_json(),
            reason="System-generated weekly grades lock window created"
        )
        logger.info(f"Created new weekly grades lock window (ID: {db_lock_window.id}) from {db_lock_window.starts_at} to {db_lock_window.ends_at}.")

@shared_task(name="lock_window_tasks.expire_old_lock_windows")
def expire_old_lock_windows_task():
    logger.info("Monitoring for old lock windows to expire...")
    asyncio.run(_expire_old_lock_windows())

async def _expire_old_lock_windows():
    async for db in _get_db_session():
        now = datetime.utcnow()
        result = await db.execute(
            select(LockWindow).where(
                LockWindow.status == LockStatus.ACTIVE,
                LockWindow.ends_at < now
            )
        )
        expired_locks = result.scalars().all()

        for lock in expired_locks:
            logger.info(f"Expiring lock window: {lock.id} (scope: {lock.scope})")
            old_data = lock.model_dump_json()
            lock.status = LockStatus.EXPIRED
            lock.updated_at = now
            db.add(lock)
            await log_audit_event(
                db=db,
                actor_id=0, # System actor
                entity_type="lock_window",
                entity_id=lock.id,
                action=AUDIT_ACTIONS["UPDATE"],
                before_json=old_data,
                after_json=lock.model_dump_json(),
                reason="Automatic expiration of lock window"
            )
        
        if expired_locks:
            await db.commit()
            logger.info(f"Expired {len(expired_locks)} lock windows.")
        else:
            logger.info("No lock windows to expire.")