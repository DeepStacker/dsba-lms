from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

# Login schemas
class LoginRequest(BaseModel):
    """Login request with flexible username field"""
    username_or_email: str = Field(..., description="Username, email, or phone number")
    password: str = Field(..., min_length=8, description="User password")
    remember_me: bool = Field(False, description="Extended session flag")

class LoginResponse(BaseModel):
    """Authentication response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: "UserAuthResponse" = Field(..., description="User information")

# Password management
class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    username_or_email: str = Field(..., description="Username, email, or phone number for password reset")

class ResetPasswordRequest(BaseModel):
    """Password reset request"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

class PasswordChangedResponse(BaseModel):
    """Password change confirmation"""
    message: str = Field("Password changed successfully", description="Success message")

# First login flow
class FirstLoginResponse(BaseModel):
    """First login response requiring password and profile update"""
    requires_password_change: bool = Field(True, description="Flag indicating password change is required")
    requires_profile_update: bool = Field(True, description="Flag indicating profile update is required")
    message: str = Field("First login detected. Please update your password and complete your profile.", description="Instruction message")

class SetupAccountRequest(BaseModel):
    """Account setup after first login"""
    new_password: str = Field(..., min_length=8, description="New password")
    name: Optional[str] = Field(None, description="Full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")

# MFA support
class EnableMFARequest(BaseModel):
    """Enable MFA request"""
    mfa_type: str = Field("totp", description="MFA type (totp, sms, email)")

class EnableMFAResponse(BaseModel):
    """MFA setup response"""
    secret: str = Field(..., description="TOTP secret for authenticator app")
    qr_code_url: str = Field(..., description="QR code URL for mobile app")
    backup_codes: list[str] = Field(..., description="Backup codes for recovery")

class VerifyMFARequest(BaseModel):
    """Verify MFA token"""
    token: str = Field(..., description="MFA token")

# Token refresh
class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., description="Refresh token")

class RefreshTokenResponse(BaseModel):
    """Token refresh response"""
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")

# User profile in responses
class UserAuthResponse(BaseModel):
    """User information for authentication responses"""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    name: str = Field(..., description="Full name")
    role: str = Field(..., description="User role")
    phone: Optional[str] = Field(None, description="Phone number")
    is_active: bool = Field(True, description="Account active status")
    mfa_enabled: bool = Field(False, description="MFA status")
    first_login: bool = Field(False, description="First login flag")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    department: Optional[str] = Field(None, description="Department name")

class LogoutResponse(BaseModel):
    """Logout confirmation"""
    message: str = Field("Successfully logged out", description="Success message")

# Error responses
class AuthErrorResponse(BaseModel):
    """Authentication error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

# Account lockout
class AccountLockedResponse(BaseModel):
    """Account lockout response"""
    error: str = Field("account_locked", description="Error type")
    message: str = Field("Account is locked due to too many failed login attempts", description="Error message")
    unlock_time: Optional[datetime] = Field(None, description="Account unlock timestamp")

# Security audit
class AuthAuditEvent(BaseModel):
    """Authentication audit event"""
    user_id: Optional[int] = Field(None, description="User ID if applicable")
    event_type: str = Field(..., description="Event type (login, logout, failed_login, etc.)")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    details: Optional[dict] = Field(None, description="Additional event details")

class LoginSuccessResponse(BaseModel):
    """Successful login audit event"""
    user_id: int = Field(..., description="User ID")
    login_time: datetime = Field(..., description="Login timestamp")
    ip_address: str = Field(..., description="Client IP address")
    device_info: Optional[str] = Field(None, description="Device information")

class LoginFailureResponse(BaseModel):
    """Failed login audit event"""
    attempted_username: str = Field(..., description="Attempted username")
    failure_reason: str = Field(..., description="Failure reason")
    ip_address: str = Field(..., description="Client IP address")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Failure timestamp")

# Permission checks
class PermissionCheckRequest(BaseModel):
    """Permission check request"""
    user_id: int = Field(..., description="User ID")
    action: str = Field(..., description="Requested action")
    resource: Optional[str] = Field(None, description="Resource identifier")
    context: Optional[dict] = Field(None, description="Permission context")

class PermissionCheckResponse(BaseModel):
    """Permission check response"""
    allowed: bool = Field(..., description="Permission granted/denied")
    reason: Optional[str] = Field(None, description="Permission denial reason")

# Service health
class AuthServiceHealth(BaseModel):
    """Authentication service health status"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime: Optional[str] = Field(None, description="Service uptime")
    database_connected: bool = Field(..., description="Database connection status")
    active_sessions: Optional[int] = Field(None, description="Number of active sessions")
