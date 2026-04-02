from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    openai_api_key: str
    openai_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"

    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/helpdesk"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # Telegram
    telegram_bot_token: str = ""
    csirt_chat_id: str = ""

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
