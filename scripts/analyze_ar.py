"""Diagnosa kenapa AnswerRelevancy rendah di dataset BSSN."""
import json, re

with open("tests/evaluation/rag_ragas_results_bssn.json", encoding="utf-8") as f:
    data = json.load(f)

LOW_AR_THRESHOLD = 0.75

print("=" * 70)
print("ANALISIS ANSWER RELEVANCY RENDAH")
print("=" * 70)

for i, row in enumerate(data["per_question"]):
    ar = row.get("answer_relevancy")
    if ar is None or ar >= LOW_AR_THRESHOLD:
        continue
    qa = data["qa_pairs"][i]
    answer = qa.get("candidate_answer", "")

    # Pisah bagian konten dan sumber
    sumber_match = re.search(r"\n\nSumber:", answer)
    content_part = answer[:sumber_match.start()] if sumber_match else answer
    sumber_part  = answer[sumber_match.start():] if sumber_match else ""

    print(f"\n[{qa['id']}] AR = {ar:.2f}")
    print(f"QUESTION : {qa['question']}")
    print(f"\nANSWER CONTENT ({len(content_part)} chars):")
    print(content_part)
    if sumber_part:
        print(f"\nSOURCE FOOTER ({len(sumber_part)} chars) — TIDAK relevan untuk RAGAS:")
        print(sumber_part)
    print("-" * 70)
