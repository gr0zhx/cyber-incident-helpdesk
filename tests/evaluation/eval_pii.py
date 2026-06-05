"""Evaluasi kuantitatif mekanisme perlindungan PII.

Metodologi mengacu pada Text Anonymization Benchmark (TAB) — Pilán et al. (2022),
dengan kategori PII bersumber dari UU PDP No. 27 Tahun 2022 Pasal 4.

Metrik:
  - Detection Rate (Recall) per kategori: TP / (TP + FN)
  - False Positive Rate             : FP / (FP + TN)
  - Precision per kategori          : TP / (TP + FP)
  - F1 Score per kategori           : 2 * P * R / (P + R)

Cara pakai:
    python tests/evaluation/eval_pii.py
    python tests/evaluation/eval_pii.py --dataset tests/evaluation/pii_test_dataset.json
    python tests/evaluation/eval_pii.py --output tests/evaluation/pii_eval_results.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.security.pii_redactor import PIIRedactor

_DEFAULT_DATASET = Path(__file__).resolve().parent / "pii_test_dataset.json"
_DEFAULT_OUTPUT  = Path(__file__).resolve().parent / "pii_eval_results.json"

_REDACTOR = PIIRedactor()

# Mapping kategori PII ke prefix placeholder
_TYPE_TO_PREFIX = {
    "IP":    "IP_DISUNTING",
    "EMAIL": "EMAIL_DISUNTING",
    "NIK":   "NIK_DISUNTING",
    "PHONE": "TELP_DISUNTING",
}


def _evaluate_case(case: dict) -> dict:
    """Jalankan redaksi dan evaluasi satu kasus uji."""
    text          = case["text"]
    pii_present   = case["pii_present"]
    expected_list = case["expected_pii"]

    redacted, mapping = _REDACTOR.redact(text)
    detected_values   = set(mapping.values())

    tp_items: list[str] = []
    fn_items: list[str] = []
    fp_items: list[str] = []

    if pii_present:
        expected_values = {item["value"] for item in expected_list}
        tp_items = [v for v in expected_values if v in detected_values]
        fn_items = [v for v in expected_values if v not in detected_values]
        # Nilai terdeteksi yang tidak ada dalam daftar expected
        fp_items = [v for v in detected_values if v not in expected_values]
    else:
        # Kasus negatif: apapun yang terdeteksi adalah False Positive
        fp_items = list(detected_values)

    return {
        "id":           case["id"],
        "category":     case["category"],
        "pii_present":  pii_present,
        "pii_types":    case.get("pii_types", []),
        "redacted_text": redacted,
        "detected_values": list(detected_values),
        "tp": tp_items,
        "fn": fn_items,
        "fp": fp_items,
        "correct": len(fn_items) == 0 and len(fp_items) == 0,
        "justification": case.get("justification", ""),
    }


def _compute_metrics(results: list[dict]) -> dict:
    """Hitung metrik agregat per kategori dan keseluruhan."""
    per_type: dict[str, dict] = {t: {"tp": 0, "fn": 0, "fp": 0} for t in _TYPE_TO_PREFIX}
    global_tp = global_fn = global_fp = 0
    total_negative = total_fp_neg = 0

    for r in results:
        for ptype in r["pii_types"]:
            if ptype not in per_type:
                per_type[ptype] = {"tp": 0, "fn": 0, "fp": 0}
            # TP dan FN berdasarkan nilai yang diharapkan per tipe
            for item in r["tp"]:
                per_type[ptype]["tp"] += 1
                global_tp += 1
            for item in r["fn"]:
                per_type[ptype]["fn"] += 1
                global_fn += 1

        # FP global
        global_fp += len(r["fp"])

        # Hitung FPR dari kasus negatif
        if not r["pii_present"]:
            total_negative += 1
            if r["fp"]:
                total_fp_neg += 1

    def _safe_div(a: int, b: int) -> float:
        return round(a / b, 4) if b > 0 else 0.0

    def _f1(p: float, r: float) -> float:
        return round(2 * p * r / (p + r), 4) if (p + r) > 0 else 0.0

    # Per-type metrics — hitung dari results per tipe
    type_stats: dict[str, dict] = {}
    for ptype in _TYPE_TO_PREFIX:
        tp = fn = fp = 0
        for r in results:
            if ptype in r.get("pii_types", []):
                # Cek TP dan FN berdasarkan expected_pii tipe ini
                pass  # akan dihitung di bawah

        # Re-count per type dari raw results
        tp_vals: list[str] = []
        fn_vals: list[str] = []
        fp_vals: list[str] = []
        for r in results:
            if ptype in r.get("pii_types", []):
                tp_vals.extend(r["tp"])
                fn_vals.extend(r["fn"])
        # FP per type: semua FP yang mengandung prefix tipe ini
        for r in results:
            prefix = _TYPE_TO_PREFIX[ptype]
            fp_vals.extend([v for v in r["fp"] if _guess_type(v) == ptype])

        tp = len(tp_vals)
        fn = len(fn_vals)
        fp = len(fp_vals)
        precision = _safe_div(tp, tp + fp)
        recall    = _safe_div(tp, tp + fn)
        type_stats[ptype] = {
            "tp": tp, "fn": fn, "fp": fp,
            "precision":       precision,
            "detection_rate":  recall,
            "f1":              _f1(precision, recall),
        }

    # Global precision & recall
    g_precision = _safe_div(global_tp, global_tp + global_fp)
    g_recall    = _safe_div(global_tp, global_tp + global_fn)
    fpr = _safe_div(total_fp_neg, total_negative) if total_negative else 0.0

    return {
        "per_type":          type_stats,
        "global_tp":         global_tp,
        "global_fn":         global_fn,
        "global_fp":         global_fp,
        "global_precision":  g_precision,
        "global_recall":     g_recall,
        "global_f1":         _f1(g_precision, g_recall),
        "total_negative_cases": total_negative,
        "fp_negative_cases":    total_fp_neg,
        "false_positive_rate":  fpr,
    }


def _guess_type(value: str) -> str | None:
    """Tebak tipe PII dari nilai string (untuk klasifikasi FP)."""
    import re
    if re.match(r"^\d{16}$", value):
        return "NIK"
    if "@" in value:
        return "EMAIL"
    if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", value):
        return "IP"
    if re.match(r"^(\+62|62|0)\d+", value):
        return "PHONE"
    return None


def print_report(metrics: dict, total_cases: int, positive_cases: int) -> None:
    """Cetak laporan evaluasi ke terminal."""
    print("\n=== Hasil Evaluasi Perlindungan PII ===")
    print(f"Metodologi : Text Anonymization Benchmark (Pilán et al., 2022)")
    print(f"Kategori   : UU PDP No. 27 Tahun 2022 Pasal 4")
    print(f"Total Kasus: {total_cases}  (positif: {positive_cases}, negatif: {total_cases - positive_cases})")
    print(f"Dijalankan : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n--- Detection Rate per Kategori PII ---")
    header = f"{'Kategori':<10} {'TP':>4} {'FN':>4} {'FP':>4} {'Precision':>10} {'Recall':>10} {'F1':>8}"
    print(header)
    print("-" * len(header))
    labels = {"IP": "IP", "EMAIL": "Email", "NIK": "NIK", "PHONE": "Telepon"}
    for ptype, label in labels.items():
        s = metrics["per_type"][ptype]
        print(
            f"{label:<10} {s['tp']:>4} {s['fn']:>4} {s['fp']:>4}"
            f" {s['precision']*100:>9.1f}%"
            f" {s['detection_rate']*100:>9.1f}%"
            f" {s['f1']:>8.4f}"
        )

    print("\n--- Hasil Global ---")
    print(f"Global Precision  : {metrics['global_precision']*100:.2f}%")
    print(f"Global Recall     : {metrics['global_recall']*100:.2f}%")
    print(f"Global F1 Score   : {metrics['global_f1']:.4f}")

    print("\n--- False Positive Rate (Kasus Negatif) ---")
    print(f"Total Kasus Negatif  : {metrics['total_negative_cases']}")
    print(f"Kasus FP Terdeteksi  : {metrics['fp_negative_cases']}")
    print(f"False Positive Rate  : {metrics['false_positive_rate']*100:.2f}%")

    if metrics["fp_negative_cases"] > 0:
        print("\n  [!] Catatan: False Positive pada kasus negatif merupakan")
        print("      keterbatasan yang diakui dari pendekatan berbasis regex.")
        print("      (Lihat kasus PII-047, PII-048, PII-049 pada dataset)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluasi kuantitatif perlindungan PII menggunakan dataset domain-spesifik."
    )
    parser.add_argument("--dataset", default=str(_DEFAULT_DATASET),
                        help="Path file dataset JSON.")
    parser.add_argument("--output", default=str(_DEFAULT_OUTPUT),
                        help="Path file output JSON.")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_path  = Path(args.output)

    print(f"Memuat dataset: {dataset_path}")
    cases = json.loads(dataset_path.read_text(encoding="utf-8"))
    print(f"Total kasus   : {len(cases)}")

    # Jalankan evaluasi
    results = [_evaluate_case(c) for c in cases]

    # Hitung metrik
    metrics = _compute_metrics(results)

    # Statistik dasar
    total_cases    = len(cases)
    positive_cases = sum(1 for c in cases if c["pii_present"])
    correct_cases  = sum(1 for r in results if r["correct"])

    # Susun output
    output = {
        "meta": {
            "dataset":      str(dataset_path),
            "total_cases":  total_cases,
            "positive_cases": positive_cases,
            "negative_cases": total_cases - positive_cases,
            "correct_cases":  correct_cases,
            "accuracy":       round(correct_cases / total_cases, 4),
            "methodology":    "Text Anonymization Benchmark (Pilán et al., 2022)",
            "pii_categories": "UU PDP No. 27 Tahun 2022 Pasal 4",
            "run_at":         datetime.now().isoformat(),
        },
        "summary": metrics,
        "per_case": results,
        "false_positive_cases": [r for r in results if not r["pii_present"] and r["fp"]],
        "missed_cases":         [r for r in results if r["fn"]],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print_report(metrics, total_cases, positive_cases)
    print(f"\nHasil disimpan: {output_path}")


if __name__ == "__main__":
    main()
