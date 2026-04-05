"""Factory untuk membuat LLM client dan embedder.

Mendukung dua mode:
  - GitHub Models (development): set GITHUB_TOKEN + OPENAI_BASE_URL
  - OpenAI langsung (evaluasi akhir): set OPENAI_API_KEY (tanpa OPENAI_BASE_URL)

Contoh .env untuk development:
    GITHUB_TOKEN=ghp_xxxxxxxxxxxx
    OPENAI_BASE_URL=https://models.inference.ai.azure.com

Contoh .env untuk evaluasi akhir:
    OPENAI_API_KEY=sk-xxxxxxxxxxxx
"""
import os

from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI


def _resolve_api_key() -> str:
    """Kembalikan API key yang tersedia: OPENAI_API_KEY atau GITHUB_TOKEN."""
    key = os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN")
    if not key:
        raise EnvironmentError(
            "API key tidak ditemukan. Set OPENAI_API_KEY (OpenAI) "
            "atau GITHUB_TOKEN (GitHub Models)."
        )
    return key


def create_llm_client() -> AsyncOpenAI:
    """Buat AsyncOpenAI client — otomatis pilih GitHub Models atau OpenAI."""
    api_key = _resolve_api_key()
    base_url = os.getenv("OPENAI_BASE_URL")  # None = pakai OpenAI langsung
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


def create_embedder() -> OpenAIEmbeddings:
    """Buat embedder text-embedding-3-small — mendukung GitHub Models & OpenAI."""
    api_key = _resolve_api_key()
    base_url = os.getenv("OPENAI_BASE_URL")
    kwargs = {
        "model": "text-embedding-3-small",
        "openai_api_key": api_key,
    }
    if base_url:
        kwargs["openai_api_base"] = base_url
    return OpenAIEmbeddings(**kwargs)
