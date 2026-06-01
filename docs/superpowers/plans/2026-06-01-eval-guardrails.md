# Evaluasi Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membuat script `tests/evaluation/eval_guardrails.py` yang mengukur efektivitas guardrails terhadap dataset JailbreakHub (ASR, Block Rate per kategori) dan False Positive Rate terhadap laporan insiden normal dari `rag_qa_dataset.json`.

**Architecture:** Script standalone (tanpa LLM call) — download JailbreakHub CSV dengan caching lokal, jalankan setiap prompt melalui `run_input_guardrails()`, hitung metrik deterministik, simpan ke JSON, cetak laporan terminal. Unit test mengcover fungsi-fungsi pure helper.

**Tech Stack:** Python stdlib (`csv`, `json`, `argparse`, `pathlib`, `datetime`, `io`), `requests` (sudah di requirements.txt), `pytest`, `app.security.guardrails.run_input_guardrails`.

---

## File Structure

| File | Status | Tanggung Jawab |
|------|--------|----------------|
| `tests/evaluation/eval_guardrails.py` | Baru | Script evaluasi utama + semua helper functions |
| `tests/test_evaluation/__init__.py` | Baru | Marker package pytest |
| `tests/test_evaluation/test_eval_guardrails.py` | Baru | Unit test untuk `_find_col`, `compute_metrics`, `load_normal_reports` |
| `.gitignore` | Modifikasi | Tambah `jailbreakhub_cache.csv` dan `guardrails_results.json` |

---

## Task 1: Update .gitignore dan Buat Skeleton Test Package

**Files:**
- Modify: `.gitignore`
- Create: `tests/test_evaluation/__init__.py`

- [ ] **Step 1: Tambahkan entri ke .gitignore**

Tambahkan baris berikut di bagian `# Testing` pada `.gitignore`:

```
# Evaluation artifacts
tests/evaluation/jailbreakhub_cache.csv
tests/evaluation/guardrails_results.json
```

- [ ] **Step 2: Buat `tests/test_evaluation/__init__.py`**

Buat file kosong:

```python
```

(file kosong, hanya sebagai marker package)

- [ ] **Step 3: Verifikasi git tidak track file cache**

```bash
git check-ignore -v tests/evaluation/jailbreakhub_cache.csv
```

Expected output: `../.gitignore:... tests/evaluation/jailbreakhub_cache.csv`

- [ ] **Step 4: Commit**

```bash
git add .gitignore tests/test_evaluation/__init__.py
git commit -m "chore: add gitignore entries for guardrails eval artifacts"
```

---

## Task 2: TDD `_find_col()` dan `compute_metrics()`

**Files:**
- Create: `tests/test_evaluation/test_eval_guardrails.py` (skeleton + Task 2 tests)
- Create: `tests/evaluation/eval_guardrails.py` (stub untuk `_find_col` dan `compute_metrics`)

- [ ] **Step 1: Tulis failing test untuk `_find_col`**

Buat `tests/test_evaluation/test_eval_guardrails.py`:

```python
"""Unit tests untuk helper functions eval_guardrails."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.evaluation.eval_guardrails import _find_col, compute_metrics


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
```

- [ ] **Step 2: Jalankan test, pastikan FAIL**

```bash
pytest tests/test_evaluation/test_eval_guardrails.py::TestFindCol -v
```

Expected: `ImportError` atau `ModuleNotFoundError` karena `eval_guardrails.py` belum ada.

- [ ] **Step 3: Tulis failing test untuk `compute_metrics`**

Tambahkan ke `tests/test_evaluation/test_eval_guardrails.py`:

```python
class TestComputeMetrics:
    # Fixtures
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
```

- [ ] **Step 4: Buat `tests/evaluation/eval_guardrails.py` dengan stub**

Buat file baru `tests/evaluation/eval_guardrails.py` — hanya stub yang cukup agar test bisa diimport:

```python
"""Evaluasi efektivitas guardrails terhadap serangan jailbreak (JailbreakHub)
dan false positive rate terhadap laporan insiden normal.

Cara pakai:
    python tests/evaluation/eval_guardrails.py
    python tests/evaluation/eval_guardrails.py --limit 100
    python tests/evaluation/eval_guardrails.py --refresh-dataset
    python tests/evaluation/eval_guardrails.py --no-fp-test
    python tests/evaluation/eval_guardrails.py --output custom_output.json
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

_JAILBREAKHUB_URL = (
    "https://raw.githubusercontent.com/verazuo/jailbreak_llms/master/data/jailbreak_prompts.csv"
)
_DEFAULT_CACHE = Path(__file__).resolve().parent / "jailbreakhub_cache.csv"
_DEFAULT_QA    = Path(__file__).resolve().parent / "rag_qa_dataset.json"
_DEFAULT_OUTPUT = Path(__file__).resolve().parent / "guardrails_results.json"


def _find_col(fieldnames: list[str], candidates: list[str]) -> str | None:
    raise NotImplementedError


def compute_metrics(adversarial_results: list[dict], normal_results: list[dict]) -> dict:
    raise NotImplementedError


def load_normal_reports(qa_path: Path) -> list[dict]:
    raise NotImplementedError


def download_jailbreakhub(cache_path: Path, refresh: bool = False) -> list[dict]:
    raise NotImplementedError


def run_adversarial_eval(prompts: list[dict]) -> list[dict]:
    raise NotImplementedError


def run_fp_eval(reports: list[dict]) -> list[dict]:
    raise NotImplementedError


def print_report(metrics: dict, dataset_label: str, normal_label: str) -> None:
    raise NotImplementedError


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Jalankan test, pastikan FAIL karena NotImplementedError**

```bash
pytest tests/test_evaluation/test_eval_guardrails.py -v
```

Expected: semua test FAIL dengan `NotImplementedError`.

- [ ] **Step 6: Implementasi `_find_col`**

Ganti stub `_find_col` di `tests/evaluation/eval_guardrails.py`:

```python
def _find_col(fieldnames: list[str], candidates: list[str]) -> str | None:
    """Cari kolom CSV secara case-insensitive. Kembalikan None jika tidak ditemukan."""
    lower = [f.strip().lower() for f in fieldnames]
    for c in candidates:
        if c in lower:
            return fieldnames[lower.index(c)]
    return None
```

- [ ] **Step 7: Implementasi `compute_metrics`**

Ganti stub `compute_metrics`:

```python
def compute_metrics(adversarial_results: list[dict], normal_results: list[dict]) -> dict:
    """Hitung ASR, Block Rate, FP Rate, dan breakdown per kategori."""
    total_adv = len(adversarial_results)
    blocked_adv = sum(1 for r in adversarial_results if r["blocked"])
    block_rate = blocked_adv / total_adv if total_adv else 0.0
    asr = 1.0 - block_rate

    total_normal = len(normal_results)
    false_positives = sum(1 for r in normal_results if r["blocked"])
    fp_rate = false_positives / total_normal if total_normal else 0.0

    categories: dict[str, dict] = {}
    for r in adversarial_results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "blocked": 0}
        categories[cat]["total"] += 1
        if r["blocked"]:
            categories[cat]["blocked"] += 1

    per_category = [
        {
            "category": cat,
            "total": v["total"],
            "blocked": v["blocked"],
            "block_rate": round(v["blocked"] / v["total"], 4) if v["total"] else 0.0,
            "asr": round(1.0 - (v["blocked"] / v["total"]), 4) if v["total"] else 1.0,
        }
        for cat, v in sorted(categories.items(), key=lambda x: x[1]["total"], reverse=True)
    ]

    return {
        "total_adversarial": total_adv,
        "blocked": blocked_adv,
        "block_rate": round(block_rate, 4),
        "asr": round(asr, 4),
        "total_normal": total_normal,
        "false_positives": false_positives,
        "fp_rate": round(fp_rate, 4),
        "per_category": per_category,
    }
```

- [ ] **Step 8: Jalankan test, pastikan semua PASS**

```bash
pytest tests/test_evaluation/test_eval_guardrails.py::TestFindCol tests/test_evaluation/test_eval_guardrails.py::TestComputeMetrics -v
```

Expected: semua test PASS.

- [ ] **Step 9: Commit**

```bash
git add tests/evaluation/eval_guardrails.py tests/test_evaluation/test_eval_guardrails.py
git commit -m "feat: implement _find_col and compute_metrics with tests"
```

---

## Task 3: TDD `load_normal_reports()`

**Files:**
- Modify: `tests/test_evaluation/test_eval_guardrails.py`
- Modify: `tests/evaluation/eval_guardrails.py`

- [ ] **Step 1: Tulis failing test untuk `load_normal_reports`**

Tambahkan import dan class baru ke `tests/test_evaluation/test_eval_guardrails.py`:

```python
import json
import tempfile

from tests.evaluation.eval_guardrails import load_normal_reports


class TestLoadNormalReports:
    def _write_qa(self, data: list[dict]) -> Path:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(data, tmp)
        tmp.close()
        return Path(tmp.name)

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
```

- [ ] **Step 2: Jalankan test, pastikan FAIL**

```bash
pytest tests/test_evaluation/test_eval_guardrails.py::TestLoadNormalReports -v
```

Expected: FAIL dengan `NotImplementedError`.

- [ ] **Step 3: Implementasi `load_normal_reports`**

Ganti stub `load_normal_reports` di `tests/evaluation/eval_guardrails.py`:

```python
def load_normal_reports(qa_path: Path) -> list[dict]:
    """Load pertanyaan normal dari rag_qa_dataset.json.

    Returns list[dict] dengan field: id (str), question (str).
    Melewati entry dengan question kosong.
    """
    data = json.loads(qa_path.read_text(encoding="utf-8"))
    return [
        {"id": item.get("id", ""), "question": item.get("question", "")}
        for item in data
        if item.get("question")
    ]
```

- [ ] **Step 4: Jalankan test, pastikan PASS**

```bash
pytest tests/test_evaluation/test_eval_guardrails.py::TestLoadNormalReports -v
```

Expected: semua PASS.

- [ ] **Step 5: Jalankan semua test evaluasi, pastikan tidak ada regresi**

```bash
pytest tests/test_evaluation/ -v
```

Expected: semua PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/evaluation/eval_guardrails.py tests/test_evaluation/test_eval_guardrails.py
git commit -m "feat: implement load_normal_reports with tests"
```

---

## Task 4: Implementasi `download_jailbreakhub`, `run_adversarial_eval`, `run_fp_eval`

**Files:**
- Modify: `tests/evaluation/eval_guardrails.py`

Fungsi-fungsi ini bergantung pada network dan internal guardrails — tidak di-unit-test secara terpisah. Verifikasi dilakukan via smoke test di Task 6.

- [ ] **Step 1: Implementasi `download_jailbreakhub`**

Ganti stub `download_jailbreakhub` di `tests/evaluation/eval_guardrails.py`:

```python
def download_jailbreakhub(cache_path: Path, refresh: bool = False) -> list[dict]:
    """Download JailbreakHub CSV dan parse ke list of dict.

    Returns list[dict] dengan field: prompt (str), category (str).
    Hanya menyertakan baris dengan kolom jailbreak=True (jika kolom ada).
    Hasil di-cache ke cache_path untuk menghindari download berulang.
    """
    if not refresh and cache_path.exists():
        print(f"Menggunakan cache: {cache_path}")
        raw = cache_path.read_text(encoding="utf-8")
    else:
        print(f"Mengunduh JailbreakHub dari {_JAILBREAKHUB_URL} ...")
        resp = requests.get(_JAILBREAKHUB_URL, timeout=30)
        resp.raise_for_status()
        raw = resp.text
        cache_path.write_text(raw, encoding="utf-8")
        print(f"Dataset disimpan ke cache: {cache_path}")

    reader = csv.DictReader(io.StringIO(raw))
    fieldnames: list[str] = list(reader.fieldnames or [])

    prompt_col   = _find_col(fieldnames, ["prompt", "text", "query", "jailbreak_query"])
    category_col = _find_col(fieldnames, ["type", "category", "attack_type"])
    jailbreak_col = _find_col(fieldnames, ["jailbreak", "is_jailbreak", "label"])

    rows: list[dict] = []
    for row in reader:
        if jailbreak_col:
            val = row.get(jailbreak_col, "").strip().lower()
            if val not in {"true", "1", "yes"}:
                continue
        prompt = (row.get(prompt_col, "") if prompt_col else "").strip()
        if not prompt:
            continue
        category = (row.get(category_col, "Unknown") if category_col else "Unknown").strip()
        rows.append({"prompt": prompt, "category": category})

    print(f"Prompt adversarial dimuat: {len(rows)}")
    return rows
```

- [ ] **Step 2: Implementasi `run_adversarial_eval`**

Ganti stub `run_adversarial_eval`:

```python
def run_adversarial_eval(prompts: list[dict]) -> list[dict]:
    """Jalankan guardrails pada setiap adversarial prompt dan catat hasilnya."""
    from app.security.guardrails import run_input_guardrails
    results = []
    for item in prompts:
        r = run_input_guardrails(item["prompt"])
        results.append({
            "prompt": item["prompt"],
            "category": item["category"],
            "blocked": r.blocked,
            "block_reason": r.block_reason,
        })
    return results
```

- [ ] **Step 3: Implementasi `run_fp_eval`**

Ganti stub `run_fp_eval`:

```python
def run_fp_eval(reports: list[dict]) -> list[dict]:
    """Jalankan guardrails pada laporan insiden normal untuk mendeteksi false positive."""
    from app.security.guardrails import run_input_guardrails
    results = []
    for item in reports:
        r = run_input_guardrails(item["question"])
        results.append({
            "id": item["id"],
            "question": item["question"],
            "blocked": r.blocked,
            "block_reason": r.block_reason,
        })
    return results
```

- [ ] **Step 4: Jalankan unit test untuk memastikan tidak ada regresi**

```bash
pytest tests/test_evaluation/ -v
```

Expected: semua PASS (fungsi baru tidak di-unit-test di sini, dicek di Task 6).

- [ ] **Step 5: Commit**

```bash
git add tests/evaluation/eval_guardrails.py
git commit -m "feat: implement download_jailbreakhub, run_adversarial_eval, run_fp_eval"
```

---

## Task 5: Implementasi `print_report` dan `main()` CLI

**Files:**
- Modify: `tests/evaluation/eval_guardrails.py`

- [ ] **Step 1: Implementasi `print_report`**

Ganti stub `print_report`:

```python
def print_report(metrics: dict, dataset_label: str, normal_label: str) -> None:
    """Cetak ringkasan hasil evaluasi ke terminal."""
    print("\n=== Hasil Evaluasi Guardrails ===")
    print(f"Dataset  : {dataset_label}")
    print(f"Normal   : {normal_label}")
    print(f"Dijalankan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n--- Pengujian Keamanan (Adversarial) ---")
    total    = metrics["total_adversarial"]
    blocked  = metrics["blocked"]
    asr_n    = total - blocked
    print(f"Total Adversarial : {total}")
    print(f"Berhasil Diblokir : {blocked:4d}  ({metrics['block_rate'] * 100:.2f}%)")
    print(f"ASR (Lolos)       : {asr_n:4d}  ({metrics['asr'] * 100:.2f}%)")

    if metrics["per_category"]:
        print("\n--- Breakdown Per Kategori ---")
        col_w = 40
        header = f"{'Kategori':<{col_w}} {'Total':>6}  {'Blocked':>7}  {'Block Rate':>10}  {'ASR':>6}"
        print(header)
        print("-" * len(header))
        for row in metrics["per_category"]:
            cat = row["category"][:col_w]
            print(
                f"{cat:<{col_w}} {row['total']:>6}  {row['blocked']:>7}"
                f"  {row['block_rate'] * 100:>9.1f}%  {row['asr'] * 100:>5.1f}%"
            )

    if metrics["total_normal"] > 0:
        print("\n--- False Positive Rate ---")
        print(f"Total Laporan Normal : {metrics['total_normal']}")
        print(f"Salah Diblokir       : {metrics['false_positives']:3d}  ({metrics['fp_rate'] * 100:.2f}%)")
```

- [ ] **Step 2: Implementasi `main()`**

Ganti stub `main`:

```python
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluasi efektivitas guardrails terhadap JailbreakHub."
    )
    parser.add_argument("--refresh-dataset", action="store_true",
                        help="Force re-download JailbreakHub CSV dari GitHub.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Batasi jumlah adversarial prompt (berguna untuk testing cepat).")
    parser.add_argument("--no-fp-test", action="store_true",
                        help="Skip false positive test terhadap laporan normal.")
    parser.add_argument("--output", default=str(_DEFAULT_OUTPUT),
                        help="Path file output JSON.")
    parser.add_argument("--cache", default=str(_DEFAULT_CACHE),
                        help="Path file cache CSV JailbreakHub.")
    parser.add_argument("--qa-file", default=str(_DEFAULT_QA),
                        help="Path rag_qa_dataset.json untuk false positive test.")
    args = parser.parse_args()

    cache_path  = Path(args.cache)
    output_path = Path(args.output)
    qa_path     = Path(args.qa_file)

    # 1. Download / load dataset adversarial
    jailbreak_prompts = download_jailbreakhub(cache_path, refresh=args.refresh_dataset)
    if args.limit:
        jailbreak_prompts = jailbreak_prompts[: args.limit]

    # 2. Load laporan normal
    normal_reports: list[dict] = []
    if not args.no_fp_test and qa_path.exists():
        normal_reports = load_normal_reports(qa_path)
        print(f"Laporan normal dimuat: {len(normal_reports)}")

    # 3. Run evaluasi
    print("\nMenjalankan pengujian adversarial...")
    adv_results = run_adversarial_eval(jailbreak_prompts)

    fp_results: list[dict] = []
    if normal_reports:
        print("Menjalankan false positive test...")
        fp_results = run_fp_eval(normal_reports)

    # 4. Hitung metrik
    metrics = compute_metrics(adv_results, fp_results)

    # 5. Susun output JSON
    output = {
        "meta": {
            "dataset": "JailbreakHub",
            "dataset_url": _JAILBREAKHUB_URL,
            "total_adversarial": metrics["total_adversarial"],
            "total_normal": metrics["total_normal"],
            "run_at": datetime.now().isoformat(),
        },
        "summary": {
            "blocked": metrics["blocked"],
            "block_rate": metrics["block_rate"],
            "asr": metrics["asr"],
            "false_positives": metrics["false_positives"],
            "fp_rate": metrics["fp_rate"],
        },
        "per_category": metrics["per_category"],
        "bypassed_prompts": [r for r in adv_results if not r["blocked"]],
        "false_positive_cases": [r for r in fp_results if r["blocked"]],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 6. Cetak laporan
    dataset_label = f"JailbreakHub ({metrics['total_adversarial']} prompt)"
    normal_label  = (
        f"{qa_path.name} ({metrics['total_normal']} laporan)"
        if normal_reports
        else "Dilewati (--no-fp-test)"
    )
    print_report(metrics, dataset_label, normal_label)
    print(f"\nHasil disimpan: {output_path}")
```

- [ ] **Step 3: Jalankan unit test untuk memastikan tidak ada regresi**

```bash
pytest tests/test_evaluation/ -v
```

Expected: semua PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/evaluation/eval_guardrails.py
git commit -m "feat: implement print_report and main CLI for eval_guardrails"
```

---

## Task 6: Smoke Test End-to-End dengan `--limit 10`

**Files:** tidak ada perubahan kode — hanya verifikasi.

- [ ] **Step 1: Jalankan smoke test dengan 10 prompt**

```bash
python tests/evaluation/eval_guardrails.py --limit 10
```

Expected output (contoh):
```
Mengunduh JailbreakHub dari https://raw.githubusercontent.com/...
Dataset disimpan ke cache: tests/evaluation/jailbreakhub_cache.csv
Prompt adversarial dimuat: 10
Laporan normal dimuat: 30
Menjalankan pengujian adversarial...
Menjalankan false positive test...

=== Hasil Evaluasi Guardrails ===
Dataset  : JailbreakHub (10 prompt)
...
Hasil disimpan: tests/evaluation/guardrails_results.json
```

- [ ] **Step 2: Verifikasi file output JSON terbentuk**

```bash
python -c "
import json
from pathlib import Path
r = json.loads(Path('tests/evaluation/guardrails_results.json').read_text())
print('Keys:', list(r.keys()))
print('Summary:', r['summary'])
print('Per category count:', len(r['per_category']))
"
```

Expected: semua key ada (`meta`, `summary`, `per_category`, `bypassed_prompts`, `false_positive_cases`).

- [ ] **Step 3: Verifikasi cache tersimpan**

```bash
python -c "from pathlib import Path; p = Path('tests/evaluation/jailbreakhub_cache.csv'); print('Cache size:', p.stat().st_size, 'bytes')"
```

Expected: file ada dan size > 0.

- [ ] **Step 4: Verifikasi cache digunakan pada run kedua (tanpa download ulang)**

```bash
python tests/evaluation/eval_guardrails.py --limit 10
```

Expected: baris pertama output = `Menggunakan cache: ...` (bukan `Mengunduh...`).

- [ ] **Step 5: Jalankan semua unit test sekali lagi**

```bash
pytest tests/test_evaluation/ -v
```

Expected: semua PASS.

- [ ] **Step 6: Commit final**

```bash
git add tests/evaluation/eval_guardrails.py tests/test_evaluation/
git commit -m "feat: eval_guardrails — adversarial + FP evaluation script complete"
```

---

## Cara Menjalankan Evaluasi Penuh (setelah implementasi selesai)

```bash
# Evaluasi penuh — download otomatis, termasuk FP test
python tests/evaluation/eval_guardrails.py

# Jika sudah pernah download dan ingin skip download
python tests/evaluation/eval_guardrails.py

# Jika ingin refresh dataset dari GitHub
python tests/evaluation/eval_guardrails.py --refresh-dataset

# Jika ingin batasi untuk testing cepat
python tests/evaluation/eval_guardrails.py --limit 100
```

Output lengkap tersimpan di `tests/evaluation/guardrails_results.json`.
