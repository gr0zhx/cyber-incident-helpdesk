"""Factory untuk membuat LLM client dan embedder.

Prioritas API: GITHUB_TOKEN (GitHub Models) → OPENAI_API_KEY (OpenAI).
"""
import os

from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI

_GITHUB_MODELS_URL = "https://models.inference.ai.azure.com"


def _resolve_key_and_base() -> tuple[str, str | None]:
    """Return (api_key, base_url). GitHub Models diutamakan, OpenAI sebagai fallback."""
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        return github_token, _GITHUB_MODELS_URL
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key, None
    raise EnvironmentError(
        "API key tidak ditemukan. Set GITHUB_TOKEN (GitHub Models) atau OPENAI_API_KEY (OpenAI)."
    )


def create_llm_client() -> AsyncOpenAI:
    """Buat AsyncOpenAI client — GitHub Models utama, OpenAI fallback."""
    api_key, base_url = _resolve_key_and_base()
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


def create_embedder() -> OpenAIEmbeddings:
    """Buat embedder text-embedding-3-small — GitHub Models utama, OpenAI fallback."""
    api_key, base_url = _resolve_key_and_base()
    kwargs: dict = {"model": "text-embedding-3-small", "openai_api_key": api_key}
    if base_url:
        kwargs["openai_api_base"] = base_url
    return OpenAIEmbeddings(**kwargs)
