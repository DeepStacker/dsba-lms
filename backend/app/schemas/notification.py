from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NotificationBase(BaseModel):
    title: str
    message: str

class NotificationCreate(NotificationBase):
    recipient_id: int

class NotificationUpdate(BaseModel):
    read: Optional[bool] = None

class Notification(NotificationBase):
    id: int
    recipient_id: int
    read: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BulkNotificationCreate(BaseModel):
    title: str
    message: str
    recipient_ids: List[int]
    role_filter: Optional[str] = None  # Send to all users with specific role

class NotificationResponse(BaseModel):
    notifications: List[Notification]
    unread_count: int
    total_count: int