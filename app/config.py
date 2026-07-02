from functools import lru_cache
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM — GitHub Models utama (GITHUB_TOKEN), OpenAI sebagai fallback (OPENAI_API_KEY)
    openai_api_key: Optional[str] = None
    github_token: Optional[str] = None
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

    @model_validator(mode="after")
    def _require_api_key(self) -> "Settings":
        if not self.github_token and not self.openai_api_key:
            raise ValueError(
                "Harus set salah satu: GITHUB_TOKEN (GitHub Models) atau OPENAI_API_KEY (OpenAI)."
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
