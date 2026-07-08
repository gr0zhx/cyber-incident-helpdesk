"""Unit tests untuk helper functions eval_guardrails."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json
import os
import tempfile
from pathlib import Path

from tests.evaluation.eval_guardrails import _find_col, compute_metrics, load_normal_reports


class TestFindCol:
    def test_exact_match(self):
        assert _find_col(["prompt", "type", "jailbreak"], ["prompt"]) == "prompt"

    def test_case_insensitive(self):
        assert _find_col(["Prompt", "Type", "Jailbreak"], ["prompt"]) == "Prompt"

    def test_first_candidate_wins(self):
        assert _find_col(["text", "prompt", "query"], ["prompt", "text"]) == "text"

    def test_returns_none_if_no_match(self):
        assert _find_col(["foo", "bar"], ["prompt", "text"]) is None

    def test_empty_fieldnames(self):
        assert _find_col([], ["prompt"]) is None


class TestComputeMetrics:
    _adv = [
        {"prompt": "p1", "category": "CatA", "blocked": True,  "block_reason": "injection"},
        {"prompt": "p2", "category": "CatA", "blocked": False, "block_reason": ""},
        {"prompt": "p3", "category": "CatB", "blocked": True,  "block_reason": "injection"},
    ]
    _normal = [
        {"id": "n1", "question": "q1", "blocked": False, "block_reason": ""},
        {"id": "n2", "question": "q2", "blocked": True,  "block_reason": "override_instruction"},
    ]

    def test_total_adversarial(self):
        m = compute_metrics(self._adv, self._normal)
        assert m["total_adversarial"] == 3

    def test_blocked_count(self):
        m = compute_metrics(self._adv, self._normal)
        assert m["blocked"] == 2

    def test_block_rate(self):
        m = compute_metrics(self._adv, self._normal)
        assert abs(m["block_rate"] - round(2/3, 4)) < 0.001

    def test_asr_equals_one_minus_block_rate(self):
        m = compute_metrics(self._adv, self._normal)
        assert abs(m["asr"] - (1.0 - m["block_rate"])) < 0.001

    def test_false_positives(self):
        m = compute_metrics(self._adv, self._normal)
        assert m["false_positives"] == 1

    def test_fp_rate(self):
        m = compute_metrics(self._adv, self._normal)
        assert m["fp_rate"] == 0.5

    def test_per_category_count(self):
        m = compute_metrics(self._adv, self._normal)
        assert len(m["per_category"]) == 2

    def test_per_category_sorted_by_total_desc(self):
        m = compute_metrics(self._adv, self._normal)
        totals = [c["total"] for c in m["per_category"]]
        assert totals == sorted(totals, reverse=True)

    def test_per_category_fields(self):
        m = compute_metrics(self._adv, self._normal)
        cat_a = next(c for c in m["per_category"] if c["category"] == "CatA")
        assert cat_a["total"] == 2
        assert cat_a["blocked"] == 1
        assert cat_a["block_rate"] == 0.5
        assert cat_a["asr"] == 0.5

    def test_empty_adversarial(self):
        m = compute_metrics([], [])
        assert m["block_rate"] == 0.0
        assert m["asr"] == 0.0
        assert m["fp_rate"] == 0.0


class TestLoadNormalReports:
    def _write_qa(self, data: list[dict]) -> Path:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(data, tmp)
        tmp.close()
        self._tmp_path = Path(tmp.name)
        return self._tmp_path

    def teardown_method(self, method):
        if hasattr(self, "_tmp_path") and self._tmp_path.exists():
            self._tmp_path.unlink()

    def test_loads_questions(self):
        qa = self._write_qa([
            {"id": "QA-001", "question": "Apa itu phishing?", "ground_truth": "..."},
            {"id": "QA-002", "question": "Bagaimana cara mitigasi ransomware?", "ground_truth": "..."},
        ])
        result = load_normal_reports(qa)
        assert len(result) == 2
        assert result[0]["id"] == "QA-001"
        assert result[0]["question"] == "Apa itu phishing?"

    def test_skips_empty_questions(self):
        qa = self._write_qa([
            {"id": "QA-001", "question": "valid"},
            {"id": "QA-002", "question": ""},
            {"id": "QA-003"},
        ])
        result = load_normal_reports(qa)
        assert len(result) == 1
        assert result[0]["id"] == "QA-001"

    def test_returns_empty_list_for_empty_file(self):
        qa = self._write_qa([])
        assert load_normal_reports(qa) == []
