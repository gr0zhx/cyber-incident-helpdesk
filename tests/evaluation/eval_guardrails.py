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
_DEFAULT_CACHE  = Path(__file__).resolve().parent / "jailbreakhub_cache.csv"
_DEFAULT_QA     = Path(__file__).resolve().parent / "rag_qa_dataset.json"
_DEFAULT_OUTPUT = Path(__file__).resolve().parent / "guardrails_results.json"


def _find_col(fieldnames: list[str], candidates: list[str]) -> str | None:
    """Cari kolom CSV secara case-insensitive. Kembalikan None jika tidak ditemukan.

    Mencari candidate pertama yang muncul dalam fieldnames (berdasarkan urutan fieldnames).
    """
    lower = [f.strip().lower() for f in fieldnames]
    lower_candidates = [c.lower() for c in candidates]

    for i, field in enumerate(lower):
        if field in lower_candidates:
            return fieldnames[i]
    return None


def compute_metrics(adversarial_results: list[dict], normal_results: list[dict]) -> dict:
    """Hitung ASR, Block Rate, FP Rate, dan breakdown per kategori."""
    total_adv = len(adversarial_results)
    blocked_adv = sum(1 for r in adversarial_results if r["blocked"])
    block_rate = blocked_adv / total_adv if total_adv else 0.0
    asr = (1.0 - block_rate) if total_adv else 0.0

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

    prompt_col    = _find_col(fieldnames, ["prompt", "text", "query", "jailbreak_query"])
    category_col  = _find_col(fieldnames, ["type", "category", "attack_type"])
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


def print_report(metrics: dict, dataset_label: str, normal_label: str) -> None:
    """Cetak ringkasan hasil evaluasi ke terminal."""
    print("\n=== Hasil Evaluasi Guardrails ===")
    print(f"Dataset  : {dataset_label}")
    print(f"Normal   : {normal_label}")
    print(f"Dijalankan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n--- Pengujian Keamanan (Adversarial) ---")
    total   = metrics["total_adversarial"]
    blocked = metrics["blocked"]
    asr_n   = total - blocked
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


if __name__ == "__main__":
    main()
