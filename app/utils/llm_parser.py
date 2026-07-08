"""Shared JSON parser untuk output LLM."""
import json


def parse_llm_json(raw: str) -> dict | None:
    """Ekstrak JSON object dari teks respons LLM.

    Mencoba dua strategi:
    1. Parse langsung (jika LLM mengembalikan JSON murni)
    2. Ekstrak substring {...} pertama (jika ada teks di luar JSON)

    Returns:
        dict jika berhasil, None jika tidak ada JSON yang valid.
    """
    if not raw:
        return None

    # Strategi 1: parse langsung
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Strategi 2: ekstrak substring JSON
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    return None
