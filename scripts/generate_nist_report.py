"""Generate laporan markdown evaluasi RAGAS dataset NIST."""
import json, re
from datetime import date
from pathlib import Path

results_path = Path("tests/evaluation/rag_ragas_results_nist.json")
with open(results_path, encoding="utf-8") as f:
    data = json.load(f)

summary = data["summary"]
per_q   = data["per_question"]
qa_pairs = data["qa_pairs"]

dataset_path = Path("tests/evaluation/rag_qa_dataset_nist.json")
with open(dataset_path, encoding="utf-8") as f:
    dataset_meta = {item["id"]: item for item in json.load(f)}
for qa in qa_pairs:
    meta = dataset_meta.get(qa.get("id"), {})
    if "incident_type" not in qa:
        qa["incident_type"] = meta.get("incident_type", "-")
    if "severity" not in qa:
        qa["severity"] = meta.get("severity", "")

def strip_sumber(text: str) -> str:
    idx = text.find("\n\nSumber:")
    return text[:idx].strip() if idx != -1 else text.strip()

def score_label(v):
    if v is None: return "N/A"
    if v >= 0.85: return f"{v:.2f} ✅"
    if v >= 0.70: return f"{v:.2f} 🟡"
    return f"{v:.2f} 🔴"

lines = []
lines.append("# Laporan Evaluasi RAGAS — Dataset NIST")
lines.append(f"\n**Dokumen sumber:** NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide  ")
lines.append(f"**Tanggal evaluasi:** {date.today().strftime('%d %B %Y')}  ")
lines.append(f"**Jumlah soal:** {len(qa_pairs)}  ")
lines.append(f"**Model LLM:** GPT-4o (via GitHub Models)  ")
lines.append(f"**Pipeline:** Agentic RAG + Hybrid Retrieval (Semantic + BM25) + Reranker + query_knowledge intent\n")

lines.append("---\n")
lines.append("## Ringkasan Skor RAGAS\n")
lines.append("| Metrik | Skor Dataset Ini | Rata-rata 3 Dataset | Keterangan |")
lines.append("|---|---|---|---|")

_all = {}
for _f in ["tests/evaluation/rag_ragas_results_bssn.json",
           "tests/evaluation/rag_ragas_results_nist.json",
           "tests/evaluation/rag_ragas_results_mitre.json"]:
    _d = json.load(open(_f, encoding="utf-8"))["summary"]
    for k in ["faithfulness", "answer_relevancy", "nv_context_relevance"]:
        _all.setdefault(k, []).append(_d.get(k, 0))
avg = {k: sum(v)/len(v) for k, v in _all.items()}

lines.append(f"| Faithfulness | **{summary.get('faithfulness', 0):.4f}** | {avg['faithfulness']:.4f} | Jawaban grounded dalam konteks yang di-retrieve |")
lines.append(f"| Answer Relevancy | **{summary.get('answer_relevancy', 0):.4f}** | {avg['answer_relevancy']:.4f} | Jawaban relevan dan fokus terhadap pertanyaan |")
lines.append(f"| Context Relevance | **{summary.get('nv_context_relevance', 0):.4f}** | {avg['nv_context_relevance']:.4f} | Konteks yang diambil relevan dengan pertanyaan |")
lines.append("")

lines.append("---\n")
lines.append("## Skor Per Pertanyaan\n")
lines.append("| ID | Faithfulness | Answer Relevancy | Context Relevance |")
lines.append("|---|---|---|---|")
for i, row in enumerate(per_q):
    qid = qa_pairs[i].get("id", "?")
    f   = row.get("faithfulness")
    ar  = row.get("answer_relevancy")
    cr  = row.get("nv_context_relevance")
    lines.append(f"| {qid} | {score_label(f)} | {score_label(ar)} | {score_label(cr)} |")
lines.append("")

lines.append("---\n")
lines.append("## Detail Pertanyaan, Jawaban Sistem, dan Ground Truth\n")

sev_map = {"Tinggi": "🔴 Tinggi", "Sedang": "🟡 Sedang", "Rendah": "🟢 Rendah", "Kritis": "🔴 Kritis"}

for i, qa in enumerate(qa_pairs):
    row = per_q[i]
    qid  = qa.get("id", "?")
    inc  = qa.get("incident_type", "-")
    sev  = sev_map.get(qa.get("severity", ""), qa.get("severity", "-"))
    f    = row.get("faithfulness")
    ar   = row.get("answer_relevancy")
    cr   = row.get("nv_context_relevance")
    answer = strip_sumber(qa.get("candidate_answer", ""))
    gt     = qa.get("ground_truth", "")

    lines.append(f"### {qid}")
    lines.append(f"\n**Tipe Insiden:** {inc} | **Tingkat Keparahan:** {sev}  ")
    lines.append(f"**Skor:** Faithfulness={score_label(f)} | Answer Relevancy={score_label(ar)} | Context Relevance={score_label(cr)}\n")
    lines.append(f"**Pertanyaan:**")
    lines.append(f"> {qa.get('question', '')}\n")
    lines.append(f"**Jawaban Sistem (Kandidat):**")
    lines.append(f"{answer}\n")
    lines.append(f"**Ground Truth:**")
    lines.append(f"{gt}\n")
    lines.append("---\n")

report = "\n".join(lines)
out = Path("tests/evaluation/RAGAS_REPORT_NIST.md")
out.write_text(report, encoding="utf-8")
print(f"Laporan disimpan: {out}")
print(f"\nPreview summary:")
print(f"  Faithfulness     : {summary.get('faithfulness', 0):.4f}")
print(f"  Answer Relevancy : {summary.get('answer_relevancy', 0):.4f}")
print(f"  Context Relevance: {summary.get('nv_context_relevance', 0):.4f}")
