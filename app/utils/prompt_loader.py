"""Shared prompt loader — membaca template prompt dari config/prompts/."""
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "config" / "prompts"


def load_prompt(agent_name: str) -> str:
    """Baca template prompt untuk agen tertentu.

    Args:
        agent_name: Nama file prompt tanpa ekstensi, mis. "identifier", "orchestrator".

    Returns:
        Isi file prompt sebagai string.

    Raises:
        FileNotFoundError: Jika file prompt tidak ditemukan.
    """
    path = _PROMPTS_DIR / f"{agent_name}.txt"
    return path.read_text(encoding="utf-8")
