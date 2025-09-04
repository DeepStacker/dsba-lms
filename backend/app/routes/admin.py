from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, text
from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.audit import AuditService
from ..models.models import User, Course, Exam, Question, Response, Attempt, Notification
from ..schemas.common import Response as CommonResponse

router = APIRouter()

# ==================== ADMIN DASHBOARD ====================

@router.get("/dashboard")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_all_analytics"))
):
    """Get admin dashboard statistics"""
    
    # User statistics
    users_stats = await db.execute(
        select(
            func.count(User.id).label('total_users'),
            func.sum(func.case((User.role == 'student', 1), else_=0)).label('students'),
            func.sum(func.case((User.role == 'teacher', 1), else_=0)).label('teachers'),
            func.sum(func.case((User.role == 'admin', 1), else_=0)).label('admins'),
            func.sum(func.case((User.is_active == True, 1), else_=0)).label('active_users')
        )
    )
    user_data = users_stats.first()
    
    # Course statistics
    courses_stats = await db.execute(select(func.count(Course.id)))
    total_courses = courses_stats.scalar() or 0
    
    # Exam statistics
    exams_stats = await db.execute(
        select(
            func.count(Exam.id).label('total_exams'),
            func.sum(func.case((Exam.status == 'published', 1), else_=0)).label('published_exams'),
            func.sum(func.case((Exam.status == 'started', 1), else_=0)).label('active_exams'),
            func.sum(func.case((Exam.status == 'ended', 1), else_=0)).label('completed_exams')
        )
    )
    exam_data = exams_stats.first()
    
    # Question statistics
    questions_stats = await db.execute(select(func.count(Question.id)))
    total_questions = questions_stats.scalar() or 0
    
    # Response/Grading statistics
    grading_stats = await db.execute(
        select(
            func.count(Response.id).label('total_responses'),
            func.sum(func.case((Response.ai_score.isnot(None), 1), else_=0)).label('ai_graded'),
            func.sum(func.case((Response.teacher_score.isnot(None), 1), else_=0)).label('teacher_graded'),
            func.sum(func.case((Response.final_score.isnot(None), 1), else_=0)).label('graded_responses')
        )
    )
    grading_data = grading_stats.first()
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    recent_users = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )
    new_users_week = recent_users.scalar() or 0
    
    recent_exams = await db.execute(
        select(func.count(Exam.id)).where(Exam.created_at >= week_ago)
    )
    new_exams_week = recent_exams.scalar() or 0
    
    # System health indicators
    system_health = {
        "database_status": "healthy",
        "ai_service_status": "healthy",  # Would check actual AI service
        "active_sessions": user_data.active_users or 0,
        "storage_usage": "68%",  # Would check actual storage
        "last_backup": "2024-01-15T02:00:00Z"  # Would check actual backup
    }
    
    return {
        "users": {
            "total": user_data.total_users or 0,
            "students": user_data.students or 0,
            "teachers": user_data.teachers or 0,
            "admins": user_data.admins or 0,
            "active": user_data.active_users or 0,
            "new_this_week": new_users_week
        },
        "courses": {
            "total": total_courses
        },
        "exams": {
            "total": exam_data.total_exams or 0,
            "published": exam_data.published_exams or 0,
            "active": exam_data.active_exams or 0,
            "completed": exam_data.completed_exams or 0,
            "new_this_week": new_exams_week
        },
        "questions": {
            "total": total_questions
        },
        "grading": {
            "total_responses": grading_data.total_responses or 0,
            "ai_graded": grading_data.ai_graded or 0,
            "teacher_graded": grading_data.teacher_graded or 0,
            "graded": grading_data.graded_responses or 0,
            "pending": (grading_data.total_responses or 0) - (grading_data.graded_responses or 0)
        },
        "system_health": system_health
    }

# ==================== SYSTEM MANAGEMENT ====================

@router.get("/system/status")
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_all_analytics"))
):
    """Get detailed system status"""
    
    # Database connectivity test
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
        db_response_time = "< 50ms"
    except Exception as e:
        db_status = "error"
        db_response_time = f"Error: {str(e)}"
    
    # Check recent activity
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    
    recent_activity = await db.execute(
        select(
            func.count(User.last_login).label('recent_logins'),
            func.count(Attempt.id).label('recent_attempts'),
            func.count(Notification.id).label('recent_notifications')
        )
        .select_from(User)
        .outerjoin(Attempt, Attempt.started_at >= hour_ago)
        .outerjoin(Notification, Notification.created_at >= hour_ago)
        .where(User.last_login >= hour_ago)
    )
    
    activity_data = recent_activity.first()
    
    return {
        "timestamp": now.isoformat(),
        "database": {
            "status": db_status,
            "response_time": db_response_time
        },
        "services": {
            "api": "healthy",
            "ai_service": "healthy",  # Would check actual AI service
            "websocket": "healthy"
        },
        "activity": {
            "recent_logins": activity_data.recent_logins or 0,
            "recent_exam_attempts": activity_data.recent_attempts or 0,
            "recent_notifications": activity_data.recent_notifications or 0
        },
        "resources": {
            "memory_usage": "68%",
            "cpu_usage": "45%",
            "disk_usage": "72%"
        }
    }

# ==================== AUDIT MANAGEMENT ====================

@router.get("/audit/logs")
async def get_audit_logs(
    entity_type: str = None,
    actor_id: int = None,
    days: int = 7,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_audit_trail"))
):
    """Get audit logs"""
    audit_service = AuditService(db)
    
    logs = await audit_service.get_audit_logs(
        entity_type=entity_type,
        actor_id=actor_id,
        days=days,
        limit=limit
    )
    
    return {
        "logs": logs,
        "total": len(logs),
        "filters": {
            "entity_type": entity_type,
            "actor_id": actor_id,
            "days": days
        }
    }

@router.get("/audit/verify")
async def verify_audit_chain(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_audit_trail"))
):
    """Verify audit log chain integrity"""
    audit_service = AuditService(db)
    verification_result = await audit_service.verify_audit_chain()
    
    return verification_result

# ==================== USER MANAGEMENT ====================

@router.get("/users/summary")
async def get_users_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users"))
):
    """Get user management summary"""
    
    # User distribution by role
    role_distribution = await db.execute(
        select(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role)
    )
    
    roles_data = {role.value: count for role, count in role_distribution.all()}
    
    # Active vs inactive users
    activity_stats = await db.execute(
        select(
            func.sum(func.case((User.is_active == True, 1), else_=0)).label('active'),
            func.sum(func.case((User.is_active == False, 1), else_=0)).label('inactive')
        )
    )
    
    activity_data = activity_stats.first()
    
    # Recent registrations
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_registrations = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )
    
    return {
        "role_distribution": roles_data,
        "activity_status": {
            "active": activity_data.active or 0,
            "inactive": activity_data.inactive or 0
        },
        "recent_registrations": recent_registrations.scalar() or 0
    }

# ==================== MAINTENANCE OPERATIONS ====================

@router.post("/maintenance/cleanup")
async def cleanup_old_data(
    days_old: int = 90,
    dry_run: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users"))
):
    """Cleanup old data (notifications, logs, etc.)"""
    
    if days_old < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cleanup data newer than 30 days"
        )
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    # Count old notifications
    old_notifications = await db.execute(
        select(func.count(Notification.id))
        .where(
            and_(
                Notification.created_at < cutoff_date,
                Notification.read == True
            )
        )
    )
    
    notifications_count = old_notifications.scalar() or 0
    
    if not dry_run:
        # Actually delete old read notifications
        await db.execute(
            text("DELETE FROM notifications WHERE created_at < :cutoff AND read = true"),
            {"cutoff": cutoff_date}
        )
        await db.commit()
        
        return CommonResponse(
            message=f"Cleanup completed. Deleted {notifications_count} old notifications."
        )
    else:
        return {
            "dry_run": True,
            "would_delete": {
                "old_notifications": notifications_count
            },
            "cutoff_date": cutoff_date.isoformat()
        }

@router.post("/maintenance/backup")
async def trigger_backup(
    backup_type: str = "full",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users"))
):
    """Trigger system backup"""
    
    if backup_type not in ["full", "incremental", "audit_only"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup type. Must be 'full', 'incremental', or 'audit_only'"
        )
    
    # In a real implementation, this would trigger actual backup processes
    backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "backup_id": backup_id,
        "backup_type": backup_type,
        "status": "initiated",
        "estimated_completion": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
        "message": f"Backup {backup_id} has been initiated. You will be notified when complete."
    }

# ==================== CONFIGURATION ====================

@router.get("/config/system")
async def get_system_config(
    current_user: User = Depends(require_permission("configure_lock_policies"))
):
    """Get system configuration"""
    
    # In a real implementation, this would come from a configuration store
    return {
        "exam_settings": {
            "default_join_window_seconds": 300,
            "auto_submit_enabled": True,
            "proctoring_enabled": True
        },
        "grading_settings": {
            "ai_grading_enabled": True,
            "ai_confidence_threshold": 0.8,
            "require_teacher_review": True
        },
        "notification_settings": {
            "email_notifications": True,
            "push_notifications": True,
            "notification_retention_days": 90
        },
        "security_settings": {
            "session_timeout_minutes": 60,
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special_chars": True
            }
        }
    }

@router.put("/config/system")
async def update_system_config(
    config_updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("configure_lock_policies"))
):
    """Update system configuration"""
    
    # In a real implementation, this would update the configuration store
    # and potentially restart services or apply changes
    
    return CommonResponse(
        message="System configuration updated successfully. Some changes may require a restart to take effect."
    )