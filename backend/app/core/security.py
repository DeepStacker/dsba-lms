from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expires_min)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_expires_days)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except JWTError:
        return None

# RBAC permissions map
PERMISSIONS = {
    "admin": [
        "*", # Full access
        "manage_users", "manage_roles", "manage_permissions",
        "manage_programs", "manage_courses", "manage_cos", "manage_pos", "map_co_po",
        "assign_coordinators", "define_academic_calendar",
        "view_all_analytics", "view_proctor_logs", "accreditation_reports",
        "configure_lock_policies", "override_lock",
        "suspend_user", "reactivate_user", "approve_teacher_proposals",
        "send_notifications", "publish_circulars", "view_audit_trail"
    ],
    "teacher": [
        "read_course_content", "write_course_content",
        "define_cos", "map_co_po_propose",
        "create_questions", "edit_questions", "attach_media_to_questions", "ai_generate_questions",
        "schedule_exams", "manage_exam_settings", "start_end_exam", "monitor_live_exams",
        "grade_students", "ai_propose_grades", "override_grades", "bulk_upload_grades", "add_feedback",
        "view_class_analytics", "view_student_progress", "view_malpractice_flags",
        "create_lesson_plans", "generate_lesson_content",
        "edit_rubrics", "peer_grade", "view_slas"
    ],
    "student": [
        "access_course_content", "attempt_exams", "read_result", "get_ai_feedback",
        "view_personal_analytics", "view_sgpa_cgpa", "view_co_po_attainment_self",
        "view_proctor_logs_self", "practice_quizzes", "ai_doubt_bot",
        "submit_assignments", "request_mentorship", "dispute_resolution"
    ],
    "coordinator": [
        "read_course_content", "view_student_progress",
        "manage_attendance", "send_communications",
        "view_class_analytics",
        "approve_co_po_map"
    ]
}

def has_permission(role: str, action: str) -> bool:
    if role in PERMISSIONS and ("*" in PERMISSIONS[role] or action in PERMISSIONS[role]):
        return True
    return False