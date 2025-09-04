from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI API Key
    OPENAI_API_KEY: str = None
    
    # App Settings
    APP_TITLE: str = "AI Service API"
    APP_DESCRIPTION: str = "AI-powered microservice for LMS"
    APP_VERSION: str = "1.0.0"

    # Uvicorn Settings
    UVICORN_HOST: str = "0.0.0.0"
    UVICORN_PORT: int = 8001


settings = Settings()