"""Generate ringkasan laporan evaluasi dari hasil TCR dan RAG.

Penggunaan:
    python tests/evaluation/eval_report.py
    python tests/evaluation/eval_report.py --tcr-file tcr_results.json --rag-file rag_results.json
    python tests/evaluation/eval_report.py --run-all   # Jalankan evaluasi + buat laporan
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

EVAL_DIR = Path(__file__).parent
TCR_DEFAULT = EVAL_DIR / "tcr_results.json"
RAG_DEFAULT = EVAL_DIR / "rag_results.json"
REPORT_DEFAULT = EVAL_DIR / "evaluation_report.txt"


def _load_json(path: Path) -> dict | None:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def _format_report(tcr: dict | None, rag: dict | None) -> str:
    lines = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append("=" * 65)
    lines.append("RINGKASAN EVALUASI SISTEM HELPDESK KEAMANAN SIBER PUSDATIN")
    lines.append(f"Dibuat: {ts}")
    lines.append("=" * 65)
    lines.append("")

    # --- TCR ---
    lines.append("1. TASK COMPLETION RATE (TCR)")
    lines.append("-" * 40)
    if tcr:
        tcr_val = tcr.get("tcr_percent", 0.0)
        target_met = tcr.get("target_met", False)
        lines.append(f"   TCR         : {tcr_val:.1f}% {'✅ MEMENUHI TARGET' if target_met else '❌ BELUM MEMENUHI TARGET'}")
        lines.append(f"   Target      : ≥ 80%")
        lines.append(f"   Total       : {tcr['total']} skenario")
        lines.append(f"   Lengkap     : {tcr['complete']}")
        lines.append(f"   Parsial     : {tcr['partial']}")
        lines.append(f"   Gagal       : {tcr['fail']}")
        lines.append("")
        lines.append("   Breakdown per kategori:")
        for cat, v in tcr.get("breakdown_by_category", {}).items():
            lines.append(f"     {cat:<22}: {v['complete']}/{v['total']} ({v['rate_percent']:.0f}%)")
        if tcr.get("failed_scenarios"):
            lines.append("")
            lines.append(f"   Skenario gagal: {', '.join(tcr['failed_scenarios'])}")
    else:
        lines.append("   [Data TCR tidak tersedia — jalankan eval_tcr.py terlebih dahulu]")
    lines.append("")

    # --- RAG ---
    lines.append("2. EVALUASI RAG (LLM-as-Judge)")
    lines.append("-" * 40)
    if rag:
        metrics = rag.get("metrics", {})
        targets_met = rag.get("targets_met", {})
        lines.append(f"   Context Relevance : {metrics.get('context_relevance', 0):.3f} "
                     f"{'✅' if targets_met.get('context_relevance') else '❌'} (target: ≥ 0.75)")
        lines.append(f"   Answer Relevance  : {metrics.get('answer_relevance', 0):.3f} "
                     f"{'✅' if targets_met.get('answer_relevance') else '❌'} (target: ≥ 0.80)")
        lines.append(f"   Faithfulness      : {metrics.get('faithfulness', 0):.3f} "
                     f"{'✅' if targets_met.get('faithfulness') else '❌'} (target: ≥ 0.85)")
        lines.append(f"   Pasangan dievaluasi: {rag.get('valid_pairs', 0)}/{rag.get('total_pairs', 0)}")
    else:
        lines.append("   [Data RAG tidak tersedia — jalankan eval_rag.py terlebih dahulu]")
    lines.append("")

    # --- SUS ---
    lines.append("3. SYSTEM USABILITY SCALE (SUS)")
    lines.append("-" * 40)
    lines.append("   Target      : SUS ≥ 68 (di atas rata-rata industri)")
    lines.append("   Status      : [Menunggu pengisian kuesioner oleh pengguna]")
    lines.append("   Kuesioner   : docs/sus_questionnaire.md")
    lines.append("")

    # --- Kesimpulan ---
    lines.append("4. KESIMPULAN")
    lines.append("-" * 40)
    all_ok = []
    if tcr:
        all_ok.append(tcr.get("target_met", False))
    if rag:
        all_ok.append(all(rag.get("targets_met", {}).values()))

    if all_ok and all(all_ok):
        lines.append("   ✅ Sistem memenuhi semua kriteria evaluasi teknis.")
    elif all_ok:
        lines.append("   ⚠️  Beberapa kriteria evaluasi belum terpenuhi.")
        if tcr and not tcr.get("target_met"):
            lines.append("      - TCR masih di bawah 80%. Perlu perbaikan klasifikasi.")
        if rag and not all(rag.get("targets_met", {}).values()):
            unmet = [k for k, v in rag.get("targets_met", {}).items() if not v]
            lines.append(f"      - Metrik RAG belum memenuhi target: {', '.join(unmet)}")
    else:
        lines.append("   ℹ️  Belum ada data evaluasi. Jalankan eval_tcr.py dan eval_rag.py.")
    lines.append("")
    lines.append("=" * 65)
    return "\n".join(lines)


def generate_report(tcr_path: Path, rag_path: Path, report_path: Path) -> str:
    tcr = _load_json(tcr_path)
    rag = _load_json(rag_path)
    report = _format_report(tcr, rag)
    report_path.write_text(report, encoding="utf-8")
    return report


async def run_all_and_report(report_path: Path) -> None:
    """Jalankan TCR + RAG evaluasi lalu buat laporan."""
    from tests.evaluation.eval_tcr import run_evaluation as run_tcr
    from tests.evaluation.eval_rag import run_evaluation as run_rag

    tcr_out = str(EVAL_DIR / "tcr_results.json")
    rag_out = str(EVAL_DIR / "rag_results.json")

    print("\n[1/2] Menjalankan evaluasi TCR...")
    await run_tcr(str(EVAL_DIR / "scenarios.json"), tcr_out)

    print("\n[2/2] Menjalankan evaluasi RAG...")
    await run_rag(str(EVAL_DIR / "rag_qa_dataset.json"), rag_out)

    report = generate_report(Path(tcr_out), Path(rag_out), report_path)
    print(f"\n{'='*65}")
    print(report)
    print(f"Laporan disimpan: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tcr-file", default=str(TCR_DEFAULT))
    parser.add_argument("--rag-file", default=str(RAG_DEFAULT))
    parser.add_argument("--output", default=str(REPORT_DEFAULT))
    parser.add_argument("--run-all", action="store_true",
                        help="Jalankan evaluasi TCR+RAG terlebih dahulu lalu buat laporan")
    args = parser.parse_args()

    if args.run_all:
        asyncio.run(run_all_and_report(Path(args.output)))
    else:
        report = generate_report(Path(args.tcr_file), Path(args.rag_file), Path(args.output))
        print(report)
