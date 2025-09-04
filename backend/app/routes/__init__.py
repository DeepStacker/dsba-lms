from .auth import router as auth
from .users import router as users
from .programs import router as programs
from .questions import router as questions
from .exams import router as exams
from .grading import router as grading
from .reports import router as reports
from .internal_marks import router as internal_marks
from .lock_windows import router as lock_windows
from .notifications import router as notifications
from .ai_service import router as ai_service
from .websocket_routes import router as websocket_routes

# Admin route (placeholder - you may need to create this)
try:
    from .admin import router as admin
except ImportError:
    # Create a simple admin router if it doesn't exist
    from fastapi import APIRouter
    admin = APIRouter()
    
    @admin.get("/health")
    async def admin_health():
        return {"status": "Admin routes not yet implemented"}

__all__ = [
    "auth", "users", "programs", "questions", "exams", "grading", 
    "reports", "internal_marks", "lock_windows", "notifications", 
    "ai_service", "websocket_routes", "admin"
]