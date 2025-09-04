"""
Notification Service for LMS
Handles creation and management of system notifications
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.models import Notification, User
from app.schemas.notification import NotificationCreate


class NotificationService:
    """Service class for handling notification operations"""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        notification_data: NotificationCreate,
        commit: bool = True
    ) -> Notification:
        """
        Create a new notification for a user
        
        Args:
            db: Database session
            notification_data: Notification creation data
            commit: Whether to commit the transaction immediately
            
        Returns:
            Created notification object
        """
        # Verify recipient exists
        result = await db.execute(
            select(User).where(User.id == notification_data.recipient_id)
        )
        recipient = result.scalar_one_or_none()
        
        if not recipient:
            raise ValueError(f"Recipient with ID {notification_data.recipient_id} not found")
        
        notification = Notification(
            recipient_id=notification_data.recipient_id,
            title=notification_data.title,
            message=notification_data.message
        )
        
        db.add(notification)
        if commit:
            await db.commit()
            await db.refresh(notification)
        
        return notification

    @staticmethod
    async def create_bulk_notifications(
        db: AsyncSession,
        notifications_data: List[NotificationCreate],
        commit: bool = True
    ) -> List[Notification]:
        """
        Create multiple notifications for different users
        
        Args:
            db: Database session
            notifications_data: List of notification creation data
            commit: Whether to commit the transaction immediately
            
        Returns:
            List of created notification objects
        """
        notifications = []
        
        for notification_data in notifications_data:
            notification = await NotificationService.create_notification(
                db, notification_data, commit=False
            )
            notifications.append(notification)
        
        if commit:
            await db.commit()
            for notification in notifications:
                await db.refresh(notification)
        
        return notifications

    @staticmethod
    async def create_notification_for_user(
        db: AsyncSession,
        user_id: int,
        title: str,
        message: str,
        commit: bool = True
    ) -> Notification:
        """
        Convenience method to create a notification for a specific user
        
        Args:
            db: Database session
            user_id: ID of the recipient user
            title: Notification title
            message: Notification message
            commit: Whether to commit the transaction immediately
            
        Returns:
            Created notification object
        """
        notification_data = NotificationCreate(
            recipient_id=user_id,
            title=title,
            message=message
        )
        
        return await NotificationService.create_notification(db, notification_data, commit)

    @staticmethod
    async def create_exam_completion_notification(
        db: AsyncSession,
        user_id: int,
        exam_name: str,
        commit: bool = True
    ) -> Notification:
        """
        Create a notification for exam completion
        
        Args:
            db: Database session
            user_id: ID of the student who completed the exam
            exam_name: Name of the completed exam
            commit: Whether to commit the transaction immediately
            
        Returns:
            Created notification object
        """
        title = "Exam Submission Complete"
        message = f"Your submission for '{exam_name}' has been received successfully."
        
        return await NotificationService.create_notification_for_user(
            db, user_id, title, message, commit
        )

    @staticmethod
    async def create_grading_complete_notification(
        db: AsyncSession,
        user_id: int,
        exam_name: str,
        commit: bool = True
    ) -> Notification:
        """
        Create a notification for grading completion
        
        Args:
            db: Database session
            user_id: ID of the student
            exam_name: Name of the exam that was graded
            commit: Whether to commit the transaction immediately
            
        Returns:
            Created notification object
        """
        title = "Grading Complete"
        message = f"Grading for '{exam_name}' has been completed. Check your results."
        
        return await NotificationService.create_notification_for_user(
            db, user_id, title, message, commit
        )

    @staticmethod
    async def create_teacher_grading_complete_notification(
        db: AsyncSession,
        teacher_id: int,
        exam_name: str,
        student_count: int,
        commit: bool = True
    ) -> Notification:
        """
        Create a notification for teachers when grading is complete
        
        Args:
            db: Database session
            teacher_id: ID of the teacher
            exam_name: Name of the exam that was graded
            student_count: Number of students graded
            commit: Whether to commit the transaction immediately
            
        Returns:
            Created notification object
        """
        title = "Grading Task Complete"
        message = f"Grading for '{exam_name}' has been completed for {student_count} students."
        
        return await NotificationService.create_notification_for_user(
            db, teacher_id, title, message, commit
        )

    @staticmethod
    async def create_results_published_notification(
        db: AsyncSession,
        user_id: int,
        exam_name: str,
        commit: bool = True
    ) -> Notification:
        """
        Create a notification for results publication
        
        Args:
            db: Database session
            user_id: ID of the student
            exam_name: Name of the exam
            commit: Whether to commit the transaction immediately
            
        Returns:
            Created notification object
        """
        title = "Results Published"
        message = f"Results for '{exam_name}' have been published. Check your marks and feedback."
        
        return await NotificationService.create_notification_for_user(
            db, user_id, title, message, commit
        )

    @staticmethod
    async def create_system_announcement(
        db: AsyncSession,
        user_ids: List[int],
        title: str,
        message: str,
        commit: bool = True
    ) -> List[Notification]:
        """
        Create system announcements for multiple users
        
        Args:
            db: Database session
            user_ids: List of user IDs to receive the announcement
            title: Announcement title
            message: Announcement message
            commit: Whether to commit the transaction immediately
            
        Returns:
            List of created notification objects
        """
        notifications_data = [
            NotificationCreate(
                recipient_id=user_id,
                title=title,
                message=message
            )
            for user_id in user_ids
        ]
        
        return await NotificationService.create_bulk_notifications(
            db, notifications_data, commit
        )


# Create a singleton instance for easy import
notification_service = NotificationService()