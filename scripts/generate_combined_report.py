"""Generate laporan markdown gabungan evaluasi RAGAS dari 3 dataset (BSSN, NIST, MITRE)."""
import json
from datetime import date
from pathlib import Path


def score_label(v):
    if v is None:
        return "N/A"
    if v >= 0.85:
        return f"{v:.2f} ✅"
    if v >= 0.70:
        return f"{v:.2f} 🟡"
    return f"{v:.2f} 🔴"


def strip_sumber(text):
    idx = text.find("\n\nSumber:")
    return text[:idx].strip() if idx != -1 else text.strip()


datasets = [
    ("BSSN", "tests/evaluation/rag_ragas_results_bssn.json",
     "Peraturan BSSN Nomor 1 Tahun 2024 tentang Pengelolaan Insiden Siber"),
    ("NIST", "tests/evaluation/rag_ragas_results_nist.json",
     "NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide"),
    ("MITRE", "tests/evaluation/rag_ragas_results_mitre.json",
     "MITRE ATT&CK Framework — Teknik Serangan dan Mitigasi"),
]

all_data = {name: json.load(open(path, encoding="utf-8")) for name, path, _ in datasets}

metrics = ["faithfulness", "answer_relevancy", "nv_context_relevance"]
avgs = {m: sum(all_data[n]["summary"].get(m, 0) for n, _, __ in datasets) / 3 for m in metrics}

lines = []
lines.append("# Laporan Evaluasi RAGAS — Gabungan 3 Dataset")
lines.append(f"\n**Tanggal evaluasi:** {date.today().strftime('%d %B %Y')}  ")
lines.append("**Model LLM:** GPT-4o (via GitHub Models)  ")
lines.append("**Pipeline:** Agentic RAG + Hybrid Retrieval (Semantic + BM25) + Reranker + query_knowledge intent  ")
lines.append("**Total soal:** 30 (10 per dataset)\n")

lines.append("---\n")
lines.append("## Ringkasan Skor Keseluruhan\n")
lines.append("| Metrik | BSSN | NIST | MITRE | **Rata-rata** |")
lines.append("|---|---|---|---|---|")
metric_labels = {
    "faithfulness": "Faithfulness",
    "answer_relevancy": "Answer Relevancy",
    "nv_context_relevance": "Context Relevance",
}
for m, label in metric_labels.items():
    s = [all_data[n]["summary"].get(m, 0) for n, _, __ in datasets]
    lines.append(f"| {label} | {s[0]:.4f} | {s[1]:.4f} | {s[2]:.4f} | **{avgs[m]:.4f}** |")
lines.append("")

lines.append("---\n")
lines.append("## Skor Per Pertanyaan — Semua Dataset\n")
lines.append("| ID | Dataset | Faithfulness | Answer Relevancy | Context Relevance |")
lines.append("|---|---|---|---|---|")
for name, path, desc in datasets:
    d = all_data[name]
    for qa, pq in zip(d["qa_pairs"], d["per_question"]):
        lines.append(
            f"| {qa['id']} | {name} | {score_label(pq.get('faithfulness'))} | "
            f"{score_label(pq.get('answer_relevancy'))} | {score_label(pq.get('nv_context_relevance'))} |"
        )
lines.append("")

lines.append("---\n")
lines.append("## Detail Per Dataset\n")
sev_map = {"Tinggi": "🔴 Tinggi", "Sedang": "🟡 Sedang", "Rendah": "🟢 Rendah", "Kritis": "🔴 Kritis"}

for name, path, desc in datasets:
    d = all_data[name]
    s = d["summary"]
    lines.append(f"### {name} — {desc}\n")
    lines.append("| Metrik | Skor |")
    lines.append("|---|---|")
    lines.append(f"| Faithfulness | **{s.get('faithfulness', 0):.4f}** |")
    lines.append(f"| Answer Relevancy | **{s.get('answer_relevancy', 0):.4f}** |")
    lines.append(f"| Context Relevance | **{s.get('nv_context_relevance', 0):.4f}** |")
    lines.append("")
    for qa, pq in zip(d["qa_pairs"], d["per_question"]):
        inc = qa.get("incident_type", "-")
        sev = sev_map.get(qa.get("severity", ""), qa.get("severity", "-"))
        answer = strip_sumber(qa.get("candidate_answer", ""))
        lines.append(f"#### {qa['id']}")
        lines.append(f"\n**Tipe Insiden:** {inc} | **Tingkat Keparahan:** {sev}  ")
        lines.append(
            f"**Skor:** F={score_label(pq.get('faithfulness'))} | "
            f"AR={score_label(pq.get('answer_relevancy'))} | CR={score_label(pq.get('nv_context_relevance'))}\n"
        )
        lines.append("**Pertanyaan:**")
        lines.append(f"> {qa.get('question', '')}\n")
        lines.append("**Jawaban Sistem:**")
        lines.append(f"{answer}\n")
        lines.append("**Ground Truth:**")
        lines.append(f"{qa.get('ground_truth', '')}\n")
        lines.append("---\n")

out = Path("tests/evaluation/RAGAS_REPORT_COMBINED.md")
out.write_text("\n".join(lines), encoding="utf-8")
print("Laporan gabungan disimpan:", out)
print("\nRata-rata keseluruhan:")
for m, label in metric_labels.items():
    print(f"  {label}: {avgs[m]:.4f}")
