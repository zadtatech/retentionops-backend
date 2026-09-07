from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration using environment variables."""
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # API Authentication
    API_AUTH_TOKEN: str
    
    # Application Settings
    APP_NAME: str = "RetentionOps API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS Settings
    ALLOWED_ORIGINS: list[str] = [
        "chrome-extension://*",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    # OpenAI Vision Settings
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.3
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
