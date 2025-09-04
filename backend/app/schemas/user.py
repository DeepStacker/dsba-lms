from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from typing import Union

class UserBase(BaseModel):
    username: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    role: str = "student"
    department: Optional[str] = None
    is_active: bool = True
    mfa_enabled: bool = False

class UserCreate(UserBase):
    password: str
    first_login: bool = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    mfa_enabled: Optional[bool] = None

class UserUpdateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    first_login: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    name: str
    phone: Optional[str] = None
    role: str
    department: Optional[str] = None
    is_active: bool
    first_login: bool
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserList(BaseModel):
    users: list[UserResponse]
    total: int
    skip: int
    limit: int

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    username_or_email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str
