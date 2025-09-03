from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Database settings from environment
    # Default to a local dev-friendly postgres config expected by tests
    database_url: str = "postgresql+asyncpg://DSBA:DSBA@localhost/DSBA"

    # Alternative database settings (used when database_url is not set)
    postgres_host: str = "localhost"
    postgres_db: str = "DSBA"
    postgres_user: str = "DSBA"
    postgres_password: str = "DSBA"

    # Redis
    redis_url: str = "redis://redis:6379"

    # JWT
    jwt_secret: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_expires_min: int = 15
    refresh_expires_days: int = 7

    # Environment
    environment: str = "development"

    # CORS settings - split into individual origins to handle docker env vars
    allow_origins_0: str = "http://localhost:3000"
    allow_origins_1: str = "http://localhost:3001"
    allow_origins_2: str = "http://localhost"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # AI Service
    ai_service_url: str = "http://ai-service:8001"
    # Internal token used to authenticate backend -> ai-service calls
    ai_service_token: str = os.environ.get("AI_SERVICE_TOKEN", "internal_token_change_me")

    # Feature flags
    feature_ai: bool = True
    feature_analytics: bool = True
    feature_telemetry: bool = True

    # Security - Trusted hosts (optional)
    allowed_hosts: List[str] = ["*"]

    # Sentry (optional)
    sentry_dsn: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra environment variables without validation errors

    @property
    def allow_origins(self) -> List[str]:
        """Build CORS origins list from individual environment variables"""
        origins = []
        i = 0
        while True:
            env_var = f"allow_origins_{i}"
            value = getattr(self, env_var, None)
            if value is None or value == "":
                break
            origins.append(value)
            i += 1

        # If no custom origins found, use defaults
        if not origins:
            origins = ["http://localhost:3000", "http://localhost:3001"]

        return origins

    @property
    def sync_database_url(self) -> str:
        # Normalize and return a sync (psycopg2-style) DB URL
        if self.database_url:
            if self.database_url.startswith("postgresql+asyncpg://"):
                return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
            return self.database_url

        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"

    @property
    def async_database_url(self) -> str:
        # Ensure asyncpg prefix is present
        if self.database_url:
            if self.database_url.startswith("postgresql+asyncpg://"):
                return self.database_url
            if self.database_url.startswith("postgresql://"):
                return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return self.sync_database_url.replace("postgresql://", "postgresql+asyncpg://")

settings = Settings()
