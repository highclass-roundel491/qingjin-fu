import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/qingjin_fu"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
    DASHSCOPE_API_KEY: str = ""
    AI_DEFAULT_MODEL_TIER: str = "plus"
    AI_REQUEST_TIMEOUT_SECONDS: float = 60.0
    AI_MAX_RETRIES: int = 2
    MAX_AVATAR_SIZE: int = 2 * 1024 * 1024
    ALLOWED_AVATAR_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    RATE_LIMIT_PER_MINUTE: int = 300
    RATE_LIMIT_AI_PER_MINUTE: int = 40
    RATE_LIMIT_WRITE_PER_MINUTE: int = 120
    AGENT_MEMORY_EXTRACT_BATCH_SIZE: int = 8
    AGENT_MEMORY_EXTRACT_WORKER_CONCURRENCY: int = 4
    AGENT_MEMORY_EXTRACT_TIMEOUT_SECONDS: float = 12.0
    AGENT_MEMORY_EXTRACT_MAX_RETRIES: int = 3
    AGENT_MEMORY_EXTRACT_RETRY_BASE_SECONDS: int = 20
    AGENT_MEMORY_EXTRACT_TRIGGER_MIN_MESSAGES: int = 3
    AGENT_MEMORY_EXTRACT_TRIGGER_MIN_USER_CHARS: int = 12
    AGENT_MEMORY_EXTRACT_TRIGGER_COOLDOWN_SECONDS: int = 90
    AGENT_MEMORY_EXTRACT_MIN_IMPORTANCE: int = 2
    AGENT_MEMORY_EXTRACT_MAX_CONTENT_LENGTH: int = 120
    AGENT_MEMORY_EXTRACT_MONITOR_WINDOW: int = 200
    
    class Config:
        env_file = BASE_DIR / ".env"

settings = Settings()
