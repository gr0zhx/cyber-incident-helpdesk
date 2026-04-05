from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM — gunakan OPENAI_API_KEY (produksi) atau GITHUB_TOKEN (development)
    openai_api_key: Optional[str] = None
    github_token: Optional[str] = None
    openai_base_url: Optional[str] = None  # set ke GitHub Models URL saat dev
    openai_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"

    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/helpdesk"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None

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
