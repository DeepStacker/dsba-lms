from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, validator
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.audit import log_audit_event, AUDIT_ACTIONS
from ..models.models import User, LockWindow, LockStatus
from ..schemas.common import Response as CommonResponse

router = APIRouter()

# ==================== LOCK WINDOW MODELS ====================

class LockWindowBase(BaseModel):
    scope: str
    starts_at: datetime
    ends_at: datetime
    policy_json: Optional[Dict[str, Any]] = None

    @validator('ends_at')
    def validate_end_time(cls, v, values):
        if 'starts_at' in values and v <= values['starts_at']:
            raise ValueError('End time must be after start time')
        return v

class LockWindowCreate(LockWindowBase):
    pass

class LockWindowUpdate(BaseModel):
    scope: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    status: Optional[LockStatus] = None
    policy_json: Optional[Dict[str, Any]] = None

    @validator('ends_at')
    def validate_end_time(cls, v, values):
        if v and 'starts_at' in values and values['starts_at'] and v <= values['starts_at']:
            raise ValueError('End time must be after start time')
        return v

class LockWindowResponse(LockWindowBase):
    id: int
    status: LockStatus
    created_at: datetime
    updated_at: datetime
    is_active: bool
    time_remaining: Optional[int] = None  # seconds

    class Config:
        from_attributes = True

class LockOverrideRequest(BaseModel):
    reason: str
    override_duration_hours: int = 24

    @validator('reason')
    def validate_reason(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters long')
        return v.strip()

    @validator('override_duration_hours')
    def validate_duration(cls, v):
        if v < 1 or v > 168:  # Max 1 week
            raise ValueError('Override duration must be between 1 and 168 hours')
        return v

class LockCheckRequest(BaseModel):
    scope: str
    entity_type: str
    entity_id: int

class LockCheckResponse(BaseModel):
    is_locked: bool
    lock_window_id: Optional[int] = None
    lock_scope: Optional[str] = None
    lock_ends_at: Optional[datetime] = None
    can_override: bool = False
    message: str

# ==================== LOCK WINDOW CRUD ====================

@router.get("/", response_model=List[LockWindowResponse])
async def get_lock_windows(
    scope: Optional[str] = None,
    status: Optional[LockStatus] = None,
    active_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("configure_lock_policies"))
):
    """Get lock windows with filtering"""
    query = select(LockWindow)
    
    filters = []
    
    if scope:
        filters.append(LockWindow.scope.ilike(f"%{scope}%"))
    
    if status:
        filters.append(LockWindow.status == status)
    
    if active_only:
        now = datetime.utcnow()
        filters.append(
            and_(
                LockWindow.starts_at <= now,
                LockWindow.ends_at > now,
                LockWindow.status == LockStatus.ACTIVE
            )
        )
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(LockWindow.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    lock_windows = result.scalars().all()
    
    # Format response with additional data
    response_windows = []
    now = datetime.utcnow()
    
    for window in lock_windows:
        window_dict = LockWindowResponse.from_orm(window).dict()
        
        # Check if currently active
        window_dict['is_active'] = (
            window.starts_at <= now <= window.ends_at and 
            window.status == LockStatus.ACTIVE
        )
        
        # Calculate time remaining
        if window_dict['is_active']:
            window_dict['time_remaining'] = int((window.ends_at - now).total_seconds())
        else:
            window_dict['time_remaining'] = None
        
        response_windows.append(LockWindowResponse(**window_dict))
    
    return response_windows

@router.post("/", response_model=LockWindowResponse, status_code=status.HTTP_201_CREATED)
async def create_lock_window(
    window_data: LockWindowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("configure_lock_policies"))
):
    """Create a new lock window"""
    # Check for overlapping lock windows with the same scope
    overlapping_result = await db.execute(
        select(LockWindow).where(
            and_(
                LockWindow.scope == window_data.scope,
                LockWindow.status == LockStatus.ACTIVE,
                or_(
                    # New window starts during existing window
                    and_(
                        LockWindow.starts_at <= window_data.starts_at,
                        LockWindow.ends_at > window_data.starts_at
                    ),
                    # New window ends during existing window
                    and_(
                        LockWindow.starts_at < window_data.ends_at,
                        LockWindow.ends_at >= window_data.ends_at
                    ),
                    # New window completely contains existing window
                    and_(
                        LockWindow.starts_at >= window_data.starts_at,
                        LockWindow.ends_at <= window_data.ends_at
                    )
                )
            )
        )
    )
    
    if overlapping_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lock window overlaps with existing active lock window for the same scope"
        )
    
    # Create lock window
    lock_window = LockWindow(**window_data.dict())
    db.add(lock_window)
    await db.commit()
    await db.refresh(lock_window)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="lock_window",
        entity_id=lock_window.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=window_data.dict(),
        reason="Created lock window"
    )
    
    # Format response
    now = datetime.utcnow()
    window_dict = LockWindowResponse.from_orm(lock_window).dict()
    window_dict['is_active'] = (
        lock_window.starts_at <= now <= lock_window.ends_at and 
        lock_window.status == LockStatus.ACTIVE
    )
    window_dict['time_remaining'] = (
        int((lock_window.ends_at - now).total_seconds()) 
        if window_dict['is_active'] else None
    )
    
    return LockWindowResponse(**window_dict)

@router.get("/{window_id}", response_model=LockWindowResponse)
async def get_lock_window(
    window_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get lock window by ID"""
    result = await db.execute(select(LockWindow).where(LockWindow.id == window_id))
    lock_window = result.scalar_one_or_none()
    
    if not lock_window:
        raise HTTPException(status_code=404, detail="Lock window not found")
    
    # Format response
    now = datetime.utcnow()
    window_dict = LockWindowResponse.from_orm(lock_window).dict()
    window_dict['is_active'] = (
        lock_window.starts_at <= now <= lock_window.ends_at and 
        lock_window.status == LockStatus.ACTIVE
    )
    window_dict['time_remaining'] = (
        int((lock_window.ends_at - now).total_seconds()) 
        if window_dict['is_active'] else None
    )
    
    return LockWindowResponse(**window_dict)

@router.put("/{window_id}", response_model=LockWindowResponse)
async def update_lock_window(
    window_id: int,
    window_data: LockWindowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("configure_lock_policies"))
):
    """Update lock window"""
    result = await db.execute(select(LockWindow).where(LockWindow.id == window_id))
    lock_window = result.scalar_one_or_none()
    
    if not lock_window:
        raise HTTPException(status_code=404, detail="Lock window not found")
    
    # Check if window is currently active and being modified
    now = datetime.utcnow()
    is_currently_active = (
        lock_window.starts_at <= now <= lock_window.ends_at and 
        lock_window.status == LockStatus.ACTIVE
    )
    
    if is_currently_active and window_data.status == LockStatus.EXPIRED:
        # Allow expiring active windows
        pass
    elif is_currently_active and (window_data.starts_at or window_data.ends_at):
        # Don't allow changing timing of active windows
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify timing of currently active lock window"
        )
    
    before_data = {
        "scope": lock_window.scope,
        "starts_at": lock_window.starts_at.isoformat(),
        "ends_at": lock_window.ends_at.isoformat(),
        "status": lock_window.status.value
    }
    
    update_data = window_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(lock_window, field, value)
    
    await db.commit()
    await db.refresh(lock_window)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="lock_window",
        entity_id=window_id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated lock window"
    )
    
    # Format response
    window_dict = LockWindowResponse.from_orm(lock_window).dict()
    window_dict['is_active'] = (
        lock_window.starts_at <= now <= lock_window.ends_at and 
        lock_window.status == LockStatus.ACTIVE
    )
    window_dict['time_remaining'] = (
        int((lock_window.ends_at - now).total_seconds()) 
        if window_dict['is_active'] else None
    )
    
    return LockWindowResponse(**window_dict)

@router.delete("/{window_id}")
async def delete_lock_window(
    window_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("configure_lock_policies"))
):
    """Delete lock window"""
    result = await db.execute(select(LockWindow).where(LockWindow.id == window_id))
    lock_window = result.scalar_one_or_none()
    
    if not lock_window:
        raise HTTPException(status_code=404, detail="Lock window not found")
    
    # Check if window is currently active
    now = datetime.utcnow()
    is_currently_active = (
        lock_window.starts_at <= now <= lock_window.ends_at and 
        lock_window.status == LockStatus.ACTIVE
    )
    
    if is_currently_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete currently active lock window. Expire it first."
        )
    
    before_data = {
        "scope": lock_window.scope,
        "starts_at": lock_window.starts_at.isoformat(),
        "ends_at": lock_window.ends_at.isoformat(),
        "status": lock_window.status.value
    }
    
    await db.delete(lock_window)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="lock_window",
        entity_id=window_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted lock window"
    )
    
    return CommonResponse(message="Lock window deleted successfully")

# ==================== LOCK OPERATIONS ====================

@router.post("/check", response_model=LockCheckResponse)
async def check_lock_status(
    check_request: LockCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if an entity is currently locked"""
    now = datetime.utcnow()
    
    # Find active lock windows for the scope
    result = await db.execute(
        select(LockWindow).where(
            and_(
                LockWindow.scope == check_request.scope,
                LockWindow.starts_at <= now,
                LockWindow.ends_at > now,
                LockWindow.status == LockStatus.ACTIVE
            )
        ).order_by(LockWindow.ends_at.desc())
    )
    
    active_lock = result.scalar_one_or_none()
    
    if not active_lock:
        return LockCheckResponse(
            is_locked=False,
            can_override=False,
            message="No active lock window found"
        )
    
    # Check if user can override
    can_override = (
        current_user.role.value == "admin" or
        (active_lock.policy_json and 
         current_user.role.value in active_lock.policy_json.get("override_roles", []))
    )
    
    return LockCheckResponse(
        is_locked=True,
        lock_window_id=active_lock.id,
        lock_scope=active_lock.scope,
        lock_ends_at=active_lock.ends_at,
        can_override=can_override,
        message=f"Entity is locked until {active_lock.ends_at.isoformat()}"
    )

@router.post("/{window_id}/override")
async def override_lock_window(
    window_id: int,
    override_request: LockOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("override_lock"))
):
    """Override a lock window"""
    result = await db.execute(select(LockWindow).where(LockWindow.id == window_id))
    lock_window = result.scalar_one_or_none()
    
    if not lock_window:
        raise HTTPException(status_code=404, detail="Lock window not found")
    
    # Check if window is currently active
    now = datetime.utcnow()
    is_currently_active = (
        lock_window.starts_at <= now <= lock_window.ends_at and 
        lock_window.status == LockStatus.ACTIVE
    )
    
    if not is_currently_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lock window is not currently active"
        )
    
    # Check override permissions
    can_override = (
        current_user.role.value == "admin" or
        (lock_window.policy_json and 
         current_user.role.value in lock_window.policy_json.get("override_roles", []))
    )
    
    if not can_override:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to override this lock window"
        )
    
    before_data = {
        "status": lock_window.status.value,
        "ends_at": lock_window.ends_at.isoformat()
    }
    
    # Create override policy
    override_policy = {
        "overridden_by": current_user.id,
        "overridden_at": now.isoformat(),
        "reason": override_request.reason,
        "original_ends_at": lock_window.ends_at.isoformat(),
        "override_duration_hours": override_request.override_duration_hours
    }
    
    # Update lock window
    lock_window.status = LockStatus.OVERRIDDEN
    lock_window.ends_at = now + timedelta(hours=override_request.override_duration_hours)
    
    if lock_window.policy_json:
        lock_window.policy_json.update({"override": override_policy})
    else:
        lock_window.policy_json = {"override": override_policy}
    
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="lock_window",
        entity_id=window_id,
        action=AUDIT_ACTIONS["LOCK_OVERRIDE"],
        before_json=before_data,
        after_json={
            "status": "overridden",
            "new_ends_at": lock_window.ends_at.isoformat(),
            "reason": override_request.reason
        },
        reason=f"Lock window override: {override_request.reason}"
    )
    
    return CommonResponse(
        message=f"Lock window overridden successfully. New expiry: {lock_window.ends_at.isoformat()}"
    )

@router.post("/{window_id}/expire")
async def expire_lock_window(
    window_id: int,
    reason: str = "Manual expiration",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("configure_lock_policies"))
):
    """Manually expire a lock window"""
    result = await db.execute(select(LockWindow).where(LockWindow.id == window_id))
    lock_window = result.scalar_one_or_none()
    
    if not lock_window:
        raise HTTPException(status_code=404, detail="Lock window not found")
    
    if lock_window.status != LockStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lock window is not active"
        )
    
    before_data = {
        "status": lock_window.status.value,
        "ends_at": lock_window.ends_at.isoformat()
    }
    
    # Expire the lock window
    now = datetime.utcnow()
    lock_window.status = LockStatus.EXPIRED
    lock_window.ends_at = now
    
    # Add expiration info to policy
    expiration_policy = {
        "expired_by": current_user.id,
        "expired_at": now.isoformat(),
        "reason": reason,
        "original_ends_at": before_data["ends_at"]
    }
    
    if lock_window.policy_json:
        lock_window.policy_json.update({"expiration": expiration_policy})
    else:
        lock_window.policy_json = {"expiration": expiration_policy}
    
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="lock_window",
        entity_id=window_id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json={
            "status": "expired",
            "expired_at": now.isoformat(),
            "reason": reason
        },
        reason=f"Lock window expired: {reason}"
    )
    
    return CommonResponse(message="Lock window expired successfully")

# ==================== PREDEFINED LOCK POLICIES ====================

@router.post("/policies/weekly-lock")
async def create_weekly_lock_policy(
    scope: str,
    day_of_week: int = 6,  # Saturday = 6
    hour: int = 23,
    duration_hours: int = 48,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("configure_lock_policies"))
):
    """Create a weekly recurring lock policy"""
    if day_of_week < 0 or day_of_week > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Day of week must be between 0 (Monday) and 6 (Sunday)"
        )
    
    if hour < 0 or hour > 23:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hour must be between 0 and 23"
        )
    
    # Calculate next occurrence
    now = datetime.utcnow()
    days_ahead = day_of_week - now.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    start_time = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
    end_time = start_time + timedelta(hours=duration_hours)
    
    # Create lock window
    policy_json = {
        "type": "weekly_recurring",
        "day_of_week": day_of_week,
        "hour": hour,
        "duration_hours": duration_hours,
        "created_by": current_user.id,
        "override_roles": ["admin"]
    }
    
    lock_window = LockWindow(
        scope=scope,
        starts_at=start_time,
        ends_at=end_time,
        policy_json=policy_json
    )
    
    db.add(lock_window)
    await db.commit()
    await db.refresh(lock_window)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="lock_window",
        entity_id=lock_window.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json={
            "scope": scope,
            "policy_type": "weekly_recurring",
            "day_of_week": day_of_week,
            "hour": hour,
            "duration_hours": duration_hours
        },
        reason="Created weekly lock policy"
    )
    
    return CommonResponse(
        message=f"Weekly lock policy created. Next lock: {start_time.isoformat()} to {end_time.isoformat()}"
    )

@router.get("/active")
async def get_active_locks(
    scope: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all currently active lock windows"""
    now = datetime.utcnow()
    
    query = select(LockWindow).where(
        and_(
            LockWindow.starts_at <= now,
            LockWindow.ends_at > now,
            LockWindow.status == LockStatus.ACTIVE
        )
    )
    
    if scope:
        query = query.where(LockWindow.scope.ilike(f"%{scope}%"))
    
    query = query.order_by(LockWindow.ends_at)
    
    result = await db.execute(query)
    active_locks = result.scalars().all()
    
    # Format response
    response_locks = []
    for lock in active_locks:
        lock_dict = LockWindowResponse.from_orm(lock).dict()
        lock_dict['is_active'] = True
        lock_dict['time_remaining'] = int((lock.ends_at - now).total_seconds())
        response_locks.append(lock_dict)
    
    return response_locks