import json

with open("tests/evaluation/rag_ragas_results_bssn.json", encoding="utf-8") as f:
    data = json.load(f)

targets = {"BSSN-001", "BSSN-003", "BSSN-005", "BSSN-007", "BSSN-010"}
for qa in data["qa_pairs"]:
    if qa["id"] not in targets:
        continue
    print(f"=== {qa['id']} ===")
    print(f"QUESTION: {qa['question']}")
    print()
    print(f"ANSWER: {qa['candidate_answer'][:700]}")
    print()
    print("RETRIEVED CHUNKS (top 3):")
    for i, chunk in enumerate(qa.get("retrieved_chunks", [])[:3]):
        src = chunk.get("metadata", {}).get("source_framework", "?")
        doc = chunk.get("metadata", {}).get("doc_id", "?")
        content = chunk.get("content", "")[:250]
        print(f"  [{i+1}] [{src}/{doc}] {content}")
    print()
    print("-" * 80)
    print()
