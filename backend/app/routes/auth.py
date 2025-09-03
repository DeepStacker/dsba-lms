from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import datetime
from ..core.database import get_db
from ..core.security import verify_password, create_access_token, create_refresh_token, verify_token, get_password_hash
from ..core.dependencies import get_current_user as get_current_user_dependency
from ..models import User

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    name: str
    role: str
    is_active: bool

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
        # last_login handling removed for now to avoid serialization issues
        "first_login": False  # Default for now, can be extended later
    })
    refresh_token = create_refresh_token(data={"sub": user.username})

    # Return user data for frontend
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role.value,  # Convert enum to string
        is_active=user.is_active
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_response
    }

# Keep the old OAuth2PasswordRequestForm endpoint for backward compatibility
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
        role=user.role.value,
        is_active=user.is_active
    )
