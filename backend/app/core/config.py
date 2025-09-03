from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Database settings from environment
    database_url: str = "postgresql+asyncpg://postgres:DSBA@postgres/DSBA_lms"

    # Alternative database settings (used when database_url is not set)
    postgres_host: str = "postgres"
    postgres_db: str = "DSBA_lms"
    postgres_user: str = "postgres"
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
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"

    @property
    def async_database_url(self) -> str:
        return self.sync_database_url.replace("postgresql://", "postgresql+asyncpg://")

settings = Settings()
