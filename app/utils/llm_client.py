"""Factory untuk membuat LLM client dan embedder.

Prioritas API diatur via env var LLM_PROVIDER:
  - "auto" (default): GITHUB_TOKEN diutamakan, OPENAI_API_KEY sebagai fallback
  - "github": paksa pakai GitHub Models (error jika GITHUB_TOKEN kosong)
  - "openai": paksa pakai OpenAI (error jika OPENAI_API_KEY kosong)
"""
import os

from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI

_GITHUB_MODELS_URL = "https://models.inference.ai.azure.com"


def _resolve_key_and_base() -> tuple[str, str | None]:
    """Return (api_key, base_url) sesuai LLM_PROVIDER."""
    provider = os.getenv("LLM_PROVIDER", "auto").lower()
    github_token = os.getenv("GITHUB_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")

    if provider == "github":
        if not github_token:
            raise EnvironmentError("LLM_PROVIDER=github tapi GITHUB_TOKEN tidak diset.")
        return github_token, _GITHUB_MODELS_URL

    if provider == "openai":
        if not openai_key:
            raise EnvironmentError("LLM_PROVIDER=openai tapi OPENAI_API_KEY tidak diset.")
        return openai_key, None

    if github_token:
        return github_token, _GITHUB_MODELS_URL
    if openai_key:
        return openai_key, None
    raise EnvironmentError(
        "API key tidak ditemukan. Set GITHUB_TOKEN (GitHub Models) atau OPENAI_API_KEY (OpenAI)."
    )


def create_llm_client() -> AsyncOpenAI:
    """Buat AsyncOpenAI client — GitHub Models utama, OpenAI fallback."""
    api_key, base_url = _resolve_key_and_base()
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


def create_embedder() -> OpenAIEmbeddings:
    """Buat embedder text-embedding-3-small.

    Selalu menggunakan endpoint OpenAI standar (base_url=None) karena
    GitHub Models tidak menyediakan endpoint text-embedding-3-small.
    Jika OPENAI_API_KEY tersedia diutamakan; jika tidak, GITHUB_TOKEN digunakan
    tetapi perlu dipastikan akun GitHub memiliki akses ke OpenAI embedding.
    """
    # Embeddings hanya tersedia di OpenAI — jangan teruskan base_url GitHub Models
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN")
    if not api_key:
        raise EnvironmentError(
            "API key tidak ditemukan untuk embeddings. "
            "Set OPENAI_API_KEY (diperlukan untuk text-embedding-3-small)."
        )
    return OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
