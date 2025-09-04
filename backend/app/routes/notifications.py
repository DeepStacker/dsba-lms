from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, text, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.audit import log_audit_event, AUDIT_ACTIONS
from ..models.models import User, Notification, ClassSection, Enrollment
from ..schemas.common import Response as CommonResponse, BulkOperationResponse

router = APIRouter()

# ==================== NOTIFICATION MODELS ====================

class NotificationBase(BaseModel):
    title: str
    message: str

    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Title must be at least 3 characters long')
        return v.strip()

    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters long')
        return v.strip()

class NotificationCreate(NotificationBase):
    recipient_id: int

class NotificationUpdate(BaseModel):
    read: bool

class NotificationResponse(NotificationBase):
    id: int
    recipient_id: int
    read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BulkNotificationCreate(BaseModel):
    title: str
    message: str
    recipient_ids: List[int]

    @validator('recipient_ids')
    def validate_recipients(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one recipient is required')
        if len(v) > 1000:
            raise ValueError('Cannot send to more than 1000 recipients at once')
        return list(set(v))  # Remove duplicates

class NotificationBroadcast(BaseModel):
    title: str
    message: str
    target_roles: Optional[List[str]] = None  # admin, teacher, student, coordinator
    target_classes: Optional[List[int]] = None  # class section IDs
    target_courses: Optional[List[int]] = None  # course IDs

    @validator('target_roles')
    def validate_roles(cls, v):
        if v:
            valid_roles = ['admin', 'teacher', 'student', 'coordinator']
            invalid_roles = [role for role in v if role not in valid_roles]
            if invalid_roles:
                raise ValueError(f'Invalid roles: {invalid_roles}')
        return v

class NotificationTemplate(BaseModel):
    name: str
    title: str
    message: str
    variables: List[str] = []  # Variables that can be replaced in the template

class NotificationStats(BaseModel):
    total_notifications: int
    unread_notifications: int
    notifications_today: int
    notifications_this_week: int

# ==================== NOTIFICATIONS CRUD ====================

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for current user"""
    query = select(Notification).where(Notification.recipient_id == current_user.id)
    
    if unread_only:
        query = query.where(Notification.read == False)
    
    query = query.order_by(desc(Notification.created_at))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [NotificationResponse.from_orm(notification) for notification in notifications]

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification statistics for current user"""
    # Total notifications
    total_result = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.recipient_id == current_user.id)
    )
    total_notifications = total_result.scalar() or 0
    
    # Unread notifications
    unread_result = await db.execute(
        select(func.count(Notification.id))
        .where(
            and_(
                Notification.recipient_id == current_user.id,
                Notification.read == False
            )
        )
    )
    unread_notifications = unread_result.scalar() or 0
    
    # Notifications today
    today = datetime.utcnow().date()
    today_result = await db.execute(
        select(func.count(Notification.id))
        .where(
            and_(
                Notification.recipient_id == current_user.id,
                func.date(Notification.created_at) == today
            )
        )
    )
    notifications_today = today_result.scalar() or 0
    
    # Notifications this week
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_result = await db.execute(
        select(func.count(Notification.id))
        .where(
            and_(
                Notification.recipient_id == current_user.id,
                Notification.created_at >= week_ago
            )
        )
    )
    notifications_this_week = week_result.scalar() or 0
    
    return NotificationStats(
        total_notifications=total_notifications,
        unread_notifications=unread_notifications,
        notifications_today=notifications_today,
        notifications_this_week=notifications_this_week
    )

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific notification"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.recipient_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return NotificationResponse.from_orm(notification)

@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_data: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update notification (mark as read/unread)"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.recipient_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = notification_data.read
    await db.commit()
    await db.refresh(notification)
    
    return NotificationResponse.from_orm(notification)

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for current user"""
    await db.execute(
        text("UPDATE notifications SET read = true WHERE recipient_id = :user_id AND read = false"),
        {"user_id": current_user.id}
    )
    await db.commit()
    
    return CommonResponse(message="All notifications marked as read")

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete notification"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.recipient_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await db.delete(notification)
    await db.commit()
    
    return CommonResponse(message="Notification deleted successfully")

# ==================== SENDING NOTIFICATIONS ====================

@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("send_notifications"))
):
    """Send notification to a specific user"""
    # Verify recipient exists
    recipient_result = await db.execute(select(User).where(User.id == notification_data.recipient_id))
    recipient = recipient_result.scalar_one_or_none()
    
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # Create notification
    notification = Notification(**notification_data.dict())
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="notification",
        entity_id=notification.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json={
            "recipient_id": notification_data.recipient_id,
            "title": notification_data.title
        },
        reason="Sent notification"
    )
    
    return NotificationResponse.from_orm(notification)

@router.post("/send-bulk", response_model=BulkOperationResponse)
async def send_bulk_notifications(
    bulk_data: BulkNotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("send_notifications"))
):
    """Send notification to multiple users"""
    # Verify all recipients exist
    recipients_result = await db.execute(
        select(User.id).where(User.id.in_(bulk_data.recipient_ids))
    )
    valid_recipient_ids = [row[0] for row in recipients_result.fetchall()]
    
    invalid_ids = set(bulk_data.recipient_ids) - set(valid_recipient_ids)
    
    success_count = 0
    error_count = len(invalid_ids)
    errors = [f"Invalid recipient ID: {id}" for id in invalid_ids]
    
    # Create notifications for valid recipients
    for recipient_id in valid_recipient_ids:
        try:
            notification = Notification(
                recipient_id=recipient_id,
                title=bulk_data.title,
                message=bulk_data.message
            )
            db.add(notification)
            success_count += 1
        except Exception as e:
            errors.append(f"Error sending to recipient {recipient_id}: {str(e)}")
            error_count += 1
    
    if success_count > 0:
        await db.commit()
        
        await log_audit_event(
            db=db,
            actor_id=current_user.id,
            entity_type="notification",
            entity_id=None,
            action=AUDIT_ACTIONS["BULK_IMPORT"],
            after_json={
                "title": bulk_data.title,
                "recipient_count": success_count,
                "total_requested": len(bulk_data.recipient_ids)
            },
            reason="Sent bulk notifications"
        )
    
    return BulkOperationResponse(
        success_count=success_count,
        error_count=error_count,
        total_count=len(bulk_data.recipient_ids),
        errors=errors
    )

@router.post("/broadcast", response_model=BulkOperationResponse)
async def broadcast_notification(
    broadcast_data: NotificationBroadcast,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("publish_circulars"))
):
    """Broadcast notification to users based on roles, classes, or courses"""
    recipient_ids = set()
    
    # Get recipients by roles
    if broadcast_data.target_roles:
        roles_result = await db.execute(
            select(User.id).where(
                and_(
                    User.role.in_(broadcast_data.target_roles),
                    User.is_active == True
                )
            )
        )
        role_recipients = [row[0] for row in roles_result.fetchall()]
        recipient_ids.update(role_recipients)
    
    # Get recipients by classes
    if broadcast_data.target_classes:
        classes_result = await db.execute(
            select(User.id)
            .join(Enrollment, User.id == Enrollment.student_id)
            .where(
                and_(
                    Enrollment.class_id.in_(broadcast_data.target_classes),
                    User.is_active == True
                )
            )
        )
        class_recipients = [row[0] for row in classes_result.fetchall()]
        recipient_ids.update(class_recipients)
    
    # Get recipients by courses
    if broadcast_data.target_courses:
        courses_result = await db.execute(
            select(User.id)
            .join(Enrollment, User.id == Enrollment.student_id)
            .join(ClassSection, Enrollment.class_id == ClassSection.id)
            .where(
                and_(
                    ClassSection.course_id.in_(broadcast_data.target_courses),
                    User.is_active == True
                )
            )
        )
        course_recipients = [row[0] for row in courses_result.fetchall()]
        recipient_ids.update(course_recipients)
    
    # If no specific targets, send to all active users (admin only)
    if not any([broadcast_data.target_roles, broadcast_data.target_classes, broadcast_data.target_courses]):
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can broadcast to all users"
            )
        
        all_users_result = await db.execute(
            select(User.id).where(User.is_active == True)
        )
        all_recipients = [row[0] for row in all_users_result.fetchall()]
        recipient_ids.update(all_recipients)
    
    if not recipient_ids:
        return BulkOperationResponse(
            success_count=0,
            error_count=0,
            total_count=0,
            errors=["No recipients found matching the criteria"]
        )
    
    # Create notifications
    success_count = 0
    error_count = 0
    errors = []
    
    for recipient_id in recipient_ids:
        try:
            notification = Notification(
                recipient_id=recipient_id,
                title=broadcast_data.title,
                message=broadcast_data.message
            )
            db.add(notification)
            success_count += 1
        except Exception as e:
            errors.append(f"Error sending to recipient {recipient_id}: {str(e)}")
            error_count += 1
    
    if success_count > 0:
        await db.commit()
        
        await log_audit_event(
            db=db,
            actor_id=current_user.id,
            entity_type="notification",
            entity_id=None,
            action=AUDIT_ACTIONS["BULK_IMPORT"],
            after_json={
                "title": broadcast_data.title,
                "broadcast_type": "targeted",
                "target_roles": broadcast_data.target_roles,
                "target_classes": broadcast_data.target_classes,
                "target_courses": broadcast_data.target_courses,
                "recipient_count": success_count
            },
            reason="Broadcast notification"
        )
    
    return BulkOperationResponse(
        success_count=success_count,
        error_count=error_count,
        total_count=len(recipient_ids),
        errors=errors[:10]  # Limit to first 10 errors
    )

# ==================== NOTIFICATION TEMPLATES ====================

# In a real implementation, you would store templates in the database
# For now, we'll provide some predefined templates

NOTIFICATION_TEMPLATES = {
    "exam_published": NotificationTemplate(
        name="Exam Published",
        title="New Exam: {exam_title}",
        message="A new exam '{exam_title}' has been published for {course_name}. Exam starts at {start_time}. Please prepare accordingly.",
        variables=["exam_title", "course_name", "start_time"]
    ),
    "exam_reminder": NotificationTemplate(
        name="Exam Reminder",
        title="Exam Reminder: {exam_title}",
        message="Reminder: Your exam '{exam_title}' for {course_name} is scheduled to start in {time_remaining}. Please be ready to join on time.",
        variables=["exam_title", "course_name", "time_remaining"]
    ),
    "results_published": NotificationTemplate(
        name="Results Published",
        title="Results Available: {exam_title}",
        message="Results for '{exam_title}' are now available. You scored {score}/{total_marks}. Check your detailed results in the student portal.",
        variables=["exam_title", "score", "total_marks"]
    ),
    "assignment_due": NotificationTemplate(
        name="Assignment Due",
        title="Assignment Due: {assignment_title}",
        message="Reminder: Assignment '{assignment_title}' for {course_name} is due on {due_date}. Please submit before the deadline.",
        variables=["assignment_title", "course_name", "due_date"]
    ),
    "grade_updated": NotificationTemplate(
        name="Grade Updated",
        title="Grade Updated: {course_name}",
        message="Your grade for {component_name} in {course_name} has been updated. New score: {score}/{max_score}.",
        variables=["course_name", "component_name", "score", "max_score"]
    )
}

@router.get("/templates")
async def get_notification_templates(
    current_user: User = Depends(require_permission("send_notifications"))
):
    """Get available notification templates"""
    return {
        "templates": list(NOTIFICATION_TEMPLATES.values())
    }

@router.post("/send-template")
async def send_template_notification(
    template_name: str,
    recipient_id: int,
    variables: Dict[str, str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("send_notifications"))
):
    """Send notification using a template"""
    if template_name not in NOTIFICATION_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = NOTIFICATION_TEMPLATES[template_name]
    
    # Verify all required variables are provided
    missing_vars = [var for var in template.variables if var not in variables]
    if missing_vars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing template variables: {missing_vars}"
        )
    
    # Replace variables in title and message
    title = template.title
    message = template.message
    
    for var, value in variables.items():
        title = title.replace(f"{{{var}}}", str(value))
        message = message.replace(f"{{{var}}}", str(value))
    
    # Send notification
    notification_data = NotificationCreate(
        recipient_id=recipient_id,
        title=title,
        message=message
    )
    
    return await send_notification(notification_data, db, current_user)

# ==================== ADMIN NOTIFICATION MANAGEMENT ====================

@router.get("/admin/all", response_model=List[NotificationResponse])
async def get_all_notifications_admin(
    recipient_id: Optional[int] = None,
    unread_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_all_analytics"))
):
    """Get all notifications (admin only)"""
    query = select(Notification, User.name.label('recipient_name')).join(
        User, Notification.recipient_id == User.id
    )
    
    if recipient_id:
        query = query.where(Notification.recipient_id == recipient_id)
    
    if unread_only:
        query = query.where(Notification.read == False)
    
    query = query.order_by(desc(Notification.created_at))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    notifications_data = result.all()
    
    # Format response with recipient names
    notifications = []
    for notification, recipient_name in notifications_data:
        notification_dict = NotificationResponse.from_orm(notification).dict()
        notification_dict['recipient_name'] = recipient_name
        notifications.append(notification_dict)
    
    return notifications

@router.delete("/admin/{notification_id}")
async def delete_notification_admin(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users"))
):
    """Delete any notification (admin only)"""
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await db.delete(notification)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="notification",
        entity_id=notification_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json={
            "recipient_id": notification.recipient_id,
            "title": notification.title
        },
        reason="Admin deleted notification"
    )
    
    return CommonResponse(message="Notification deleted successfully")