"""Disable LLM judge selama unit test — hindari API call nyata."""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def disable_llm_judge_in_tests():
    with patch("app.security.guardrails._judge") as mock_judge:
        mock_judge.is_available.return_value = False
        mock_judge.is_jailbreak.return_value = False
        yield
