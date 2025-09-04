from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from ..core.database import get_db
from ..core.security import verify_password, create_access_token, create_refresh_token, verify_token, get_password_hash
from ..core.dependencies import get_current_user as get_current_user_dependency
from ..models.models import User
from ..schemas.user import UserResponse, ForgotPasswordRequest, ResetPasswordRequest

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class CommonResponse(BaseModel):
    message: str

@router.post("/login")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # Try to find user by username or email
    username_result = await db.execute(
        select(User).where(User.username == request.username)
    )
    user = username_result.scalar_one_or_none()

    if not user:
        # Try to find by email
        email_result = await db.execute(
            select(User).where(User.email == request.username)
        )
        user = email_result.scalar_one_or_none()

    # Proper password verification
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # Update last login
    current_time = datetime.utcnow()
    await db.execute(
        select(User).where(User.id == user.id)
    )
    user.last_login = current_time
    await db.commit()
    await db.refresh(user)

    # Create JWT payload
    access_token = create_access_token(data={
        "sub": user.username,
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,  # Convert enum to string
        "phone": user.phone,
        "is_active": user.is_active,
        "mfa_enabled": user.mfa_enabled,
        "first_login": user.first_login,
    })
    refresh_token = create_refresh_token(data={"sub": user.username})

    # Return user data for frontend
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        phone=user.phone,
        role=user.role.value,
        department=user.department,
        is_active=user.is_active,
        first_login=user.first_login,
        mfa_enabled=user.mfa_enabled,
        created_at=user.created_at,
        last_login=user.last_login
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_response
    }

@router.post("/login-form")
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    payload = verify_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    new_access_token = create_access_token(data={"sub": username})
    new_refresh_token = create_refresh_token(data={"sub": username})
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/forgot-password", response_model=CommonResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Initiates the password reset process. Generates a token and sends it to the user's registered email/phone.
    """
    user_query = select(User).where(
        (User.username == request.username_or_email) |
        (User.email == request.username_or_email)
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        # For security, always return a generic success message even if user not found
        return CommonResponse(message="If a matching user is found, a password reset link will be sent.")

    # Generate a unique, time-limited token
    token = create_access_token(
        data={"sub": user.email, "type": "password_reset"}, 
        expires_delta=timedelta(minutes=30)
    )
    expires_at = datetime.utcnow() + timedelta(minutes=30)

    user.password_reset_token = token
    user.password_reset_expires_at = expires_at
    await db.commit()

    # TODO: Integrate with actual email/SMS service
    print(f"Mock: Sending password reset link to {user.email}: /auth/reset_password?token={token}")

    return CommonResponse(message="If a matching user is found, a password reset link will be sent.")

@router.post("/reset-password", response_model=CommonResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resets the user's password using a valid reset token.
    """
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match"
        )
    
    # Verify the token
    user_query = select(User).where(
        User.password_reset_token == request.token,
        User.password_reset_expires_at > datetime.utcnow(),
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )

    # Hash the new password
    user.hashed_password = get_password_hash(request.new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    await db.commit()

    return CommonResponse(message="Password has been reset successfully.")

@router.post("/logout")
async def logout():
    # In a real implementation, you might want to blacklist tokens
    # For now, just return success
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_current_user(user: User = Depends(get_current_user_dependency)):
    """Get current user information from JWT token"""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        phone=user.phone,
        role=user.role.value,
        department=user.department,
        is_active=user.is_active,
        first_login=user.first_login,
        mfa_enabled=user.mfa_enabled,
        created_at=user.created_at,
        last_login=user.last_login
    )

@router.post("/first-login-update", response_model=UserResponse)
async def first_login_update(
    user_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Update user profile after first login"""
    if not current_user.first_login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already updated"
        )
    
    # Update allowed fields
    if "username" in user_data and user_data["username"]:
        # Check username uniqueness
        existing = await db.execute(
            select(User).where(User.username == user_data["username"], User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_data["username"]
    
    if "phone" in user_data:
        current_user.phone = user_data["phone"]
    
    if "department" in user_data:
        current_user.department = user_data["department"]
    
    if "password" in user_data and user_data["password"]:
        current_user.hashed_password = get_password_hash(user_data["password"])
    
    # Mark first login as complete
    current_user.first_login = False
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        name=current_user.name,
        phone=current_user.phone,
        role=current_user.role.value,
        department=current_user.department,
        is_active=current_user.is_active,
        first_login=current_user.first_login,
        mfa_enabled=current_user.mfa_enabled,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )
