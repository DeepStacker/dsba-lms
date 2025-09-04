from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class LockStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    OVERRIDDEN = "overridden"

class LockWindowBase(BaseModel):
    scope: str
    starts_at: datetime
    ends_at: datetime
    policy_json: Optional[Dict[str, Any]] = None

class LockWindowCreate(LockWindowBase):
    pass

class LockWindowUpdate(BaseModel):
    ends_at: Optional[datetime] = None
    status: Optional[LockStatus] = None
    policy_json: Optional[Dict[str, Any]] = None

class LockWindow(LockWindowBase):
    id: int
    status: LockStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LockOverrideRequest(BaseModel):
    reason: str