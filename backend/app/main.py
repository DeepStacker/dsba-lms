from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from .core.database import create_tables
from .core.config import settings
from .routes import auth, exams, programs, questions, users, reports  # admin, grading commented out
import sentry_sdk

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, integrations=[])

app = FastAPI(
    title="Apollo LMS API",
    description="""
    AI-powered Learning Management System for educational institutions.

    Features:
    - Role-based authentication (Admin, Teacher, Student)
    - Comprehensive exam management with AI assistance
    - Program and course management with CO/PO mapping
    - Real-time grading and analytics
    - Automated assessment generation
    - Proctoring and anti-cheating mechanisms
    """,
    version="1.0.0",
    docs_url=None,
    redoc_url="/docs",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware for security
if settings.environment == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Apollo LMS API",
        version="1.0.0",
        description="""
        AI-powered Learning Management System.

        ## Authentication
        Most endpoints require authentication via JWT token in Authorization header: `Bearer <token>`

        ## Roles
        - **Admin**: Full system access and management
        - **Teacher**: Course and exam management, grading
        - **Student**: Take exams, view results
        """,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.on_event("startup")
async def startup_event():
    await create_tables()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Include routers
# app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
# app.include_router(grading.router, prefix="/api/v1", tags=["Grading"])  # Commented out - schemas missing
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(programs.router, prefix="/programs", tags=["Programs"])
app.include_router(exams.router, prefix="/exams", tags=["Examinations"])
app.include_router(questions.router, prefix="/questions", tags=["Questions"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Apollo LMS API Docs",
        oauth2_redirect_url=None,
        swagger_ui_parameters={"deepLinking": True, "presets": "[]", "docExpansion": "list"}
    )
