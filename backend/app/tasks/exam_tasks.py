from celery import shared_task
from sqlalchemy.future import select
from datetime import datetime, timedelta
import asyncio
import logging

from ..core.database import async_session
from ..models.models import Exam, ExamStatus, Attempt, AttemptStatus

logger = logging.getLogger(__name__)

async def _get_db_session():
    """Helper to get an async session within a Celery task context."""
    async with async_session() as session:
        yield session

@shared_task(name="exam_tasks.monitor_exam_starts")
def monitor_exam_starts_task():
    logger.info("Monitoring for exams to start...")
    asyncio.run(_monitor_exam_starts())

async def _monitor_exam_starts():
    async for db in _get_db_session():
        now = datetime.utcnow()
        # Find exams that are published and should have started
        result = await db.execute(
            select(Exam).where(
                Exam.status == ExamStatus.PUBLISHED,
                Exam.start_at <= now
            )
        )
        exams_to_start = result.scalars().all()

        for exam in exams_to_start:
            logger.info(f"Automatically starting exam: {exam.id} - {exam.title}")
            exam.status = ExamStatus.STARTED
            exam.updated_at = now
            db.add(exam)
        
        if exams_to_start:
            await db.commit()
            logger.info(f"Started {len(exams_to_start)} exams.")
        else:
            logger.info("No exams to start.")

@shared_task(name="exam_tasks.monitor_exam_ends")
def monitor_exam_ends_task():
    logger.info("Monitoring for exams to end and attempts to auto-submit...")
    asyncio.run(_monitor_exam_ends())

async def _monitor_exam_ends():
    async for db in _get_db_session():
        now = datetime.utcnow()
        # Find exams that are started and should have ended
        result = await db.execute(
            select(Exam).where(
                Exam.status == ExamStatus.STARTED,
                Exam.end_at <= now
            )
        )
        exams_to_end = result.scalars().all()

        for exam in exams_to_end:
            logger.info(f"Automatically ending exam: {exam.id} - {exam.title}")
            exam.status = ExamStatus.ENDED
            exam.updated_at = now
            db.add(exam)
            
            # Auto-submit any in-progress attempts for this exam
            attempts_to_auto_submit_result = await db.execute(
                select(Attempt).where(
                    Attempt.exam_id == exam.id,
                    Attempt.status == AttemptStatus.IN_PROGRESS
                )
            )
            attempts_to_auto_submit = attempts_to_auto_submit_result.scalars().all()
            for attempt in attempts_to_auto_submit:
                logger.info(f"Auto-submitting attempt {attempt.id} for student {attempt.student_id}")
                attempt.status = AttemptStatus.AUTO_SUBMITTED
                attempt.submitted_at = now
                attempt.autosubmitted = True
                attempt.updated_at = now
                db.add(attempt)
        
        if exams_to_end or attempts_to_auto_submit: # Check both if there are any updates
            await db.commit()
            logger.info(f"Ended {len(exams_to_end)} exams and auto-submitted {len(attempts_to_auto_submit)} attempts.")
        else:
            logger.info("No exams to end or attempts to auto-submit.")

@shared_task(name="exam_tasks.monitor_auto_submit_near_end")
def monitor_auto_submit_near_end_task():
    logger.info("Monitoring for attempts approaching auto-submit time...")
    asyncio.run(_monitor_auto_submit_near_end())

async def _monitor_auto_submit_near_end():
    async for db in _get_db_session():
        now = datetime.utcnow()
        
        # Find in-progress attempts for exams that are STARTED
        # And where the current time is beyond (end_at - auto_submit_time_remaining)
        result = await db.execute(
            select(Attempt)
            .join(Attempt.exam)
            .where(
                Attempt.status == AttemptStatus.IN_PROGRESS,
                Exam.status == ExamStatus.STARTED,
                Exam.end_at - timedelta(seconds=Exam.settings_json.cast(Dict[str, Any])["auto_submit_time_remaining"]) <= now # Accessing JSON field
            )
        )
        attempts_to_auto_submit_early = result.scalars().all()

        for attempt in attempts_to_auto_submit_early:
            logger.info(f"Auto-submitting attempt {attempt.id} (early) for student {attempt.student_id} for exam {attempt.exam_id}")
            attempt.status = AttemptStatus.AUTO_SUBMITTED
            attempt.submitted_at = now
            attempt.autosubmitted = True
            attempt.updated_at = now
            db.add(attempt)
        
        if attempts_to_auto_submit_early:
            await db.commit()
            logger.info(f"Auto-submitted {len(attempts_to_auto_submit_early)} attempts near end time.")
        else:
            logger.info("No attempts to auto-submit early.")