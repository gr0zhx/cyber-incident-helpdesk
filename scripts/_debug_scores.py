import json

def fmt(v):
    return f"{v:.2f}" if v is not None else "N/A"

for name, path in [("NIST", "tests/evaluation/rag_ragas_results_nist.json"),
                   ("MITRE", "tests/evaluation/rag_ragas_results_mitre.json")]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(f"=== {name} per-question ===")
    for qa, row in zip(data["qa_pairs"], data["per_question"]):
        qid = qa.get("id", "?")
        f_s = fmt(row.get("faithfulness"))
        ar = fmt(row.get("answer_relevancy"))
        cr = fmt(row.get("nv_context_relevance"))
        print(f"{qid}: F={f_s} AR={ar} CR={cr}")
        print(f"  Q: {qa['question'][:90]}")
        print(f"  A: {qa['candidate_answer'][:150]}")
    print()
