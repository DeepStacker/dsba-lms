from celery import Celery
from ..core.config import settings
from datetime import timedelta

celery_app = Celery(
    "lms_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.exam_tasks", "app.tasks.lock_window_tasks"] # Include new lock window tasks
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "monitor-exam-starts": {
            "task": "exam_tasks.monitor_exam_starts",
            "schedule": timedelta(seconds=30), # Run every 30 seconds
        },
        "monitor-exam-ends": {
            "task": "exam_tasks.monitor_exam_ends",
            "schedule": timedelta(seconds=30), # Run every 30 seconds
        },
        "monitor-auto-submit-near-end": {
            "task": "exam_tasks.monitor_auto_submit_near_end",
            "schedule": timedelta(seconds=15), # Run more frequently for timely auto-submission
        },
        "create-weekly-grades-lock": {
            "task": "lock_window_tasks.create_weekly_grades_lock",
            "schedule": timedelta(days=7), # Run once a week
            "options": {"expires": 3600} # Task expires after 1 hour if not processed
        },
        "expire-old-lock-windows": {
            "task": "lock_window_tasks.expire_old_lock_windows",
            "schedule": timedelta(hours=1), # Run hourly to expire old locks
        },
    },
    timezone="UTC",
)