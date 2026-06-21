import json

with open("tests/evaluation/rag_ragas_results_bssn.json", encoding="utf-8") as f:
    data = json.load(f)

print("=== SUMMARY ===")
for k, v in data["summary"].items():
    val = f"{v:.4f}" if v is not None else "N/A"
    print(f"  {k}: {val}")

print()
print("=== PER QUESTION ===")
print(f"{'ID':<12} {'Faithfulness':>14} {'AnswerRelev':>12} {'CtxRelev':>10}")
print("-" * 52)

prev = {
    "BSSN-001": (0.75, 0.69, 1.00),
    "BSSN-002": (1.00, 0.74, 1.00),
    "BSSN-003": (0.00, 0.56, 1.00),
    "BSSN-004": (1.00, 0.73, 1.00),
    "BSSN-005": (1.00, 0.65, 1.00),
    "BSSN-006": (1.00, 0.80, 1.00),
    "BSSN-007": (0.50, 0.88, 1.00),
    "BSSN-008": (1.00, 0.76, 1.00),
    "BSSN-009": (1.00, 0.77, 1.00),
    "BSSN-010": (1.00, 0.60, 1.00),
}

for i, row in enumerate(data["per_question"]):
    fai = row.get("faithfulness")
    ar  = row.get("answer_relevancy")
    cr  = row.get("nv_context_relevance")
    qa  = data["qa_pairs"][i]
    qid = qa.get("id", "?")
    fai_s = f"{fai:.2f}" if fai is not None else " N/A"
    ar_s  = f"{ar:.2f}"  if ar  is not None else " N/A"
    cr_s  = f"{cr:.2f}"  if cr  is not None else " N/A"

    pf, pa, pc = prev.get(qid, (None, None, None))
    def delta(new, old):
        if new is None or old is None:
            return ""
        d = new - old
        return f"(+{d:.2f})" if d > 0 else f"({d:.2f})" if d < 0 else "(=)"

    print(
        f"{qid:<12} {fai_s:>8} {delta(fai, pf):>6}  "
        f"{ar_s:>6} {delta(ar, pa):>6}  "
        f"{cr_s:>5} {delta(cr, pc):>4}"
    )
