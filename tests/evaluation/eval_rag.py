"""Evaluasi RAG menggunakan LLM-as-judge (tanpa library ragas eksternal).

Metrik yang dievaluasi:
  - Context Relevance  : apakah chunks yang diambil relevan dengan pertanyaan?
  - Answer Relevance   : apakah jawaban menjawab pertanyaan?
  - Faithfulness       : apakah jawaban konsisten dengan konteks yang diambil?

Penggunaan:
    python tests/evaluation/eval_rag.py
    python tests/evaluation/eval_rag.py --qa-file tests/evaluation/rag_qa_dataset.json
    python tests/evaluation/eval_rag.py --output results/rag_results.json
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from openai import AsyncOpenAI
from qdrant_client import QdrantClient

from app.agents.mitigation import MitigationAdvisorAgent
from app.rag.retriever import HybridRetriever
from app.rag.reranker import rerank
from app.utils.llm_client import create_embedder, create_llm_client


_JUDGE_SYSTEM = """\
Kamu adalah penilai objektif untuk sistem RAG keamanan siber.
Berikan skor 0.0–1.0 berdasarkan kriteria yang diminta.
Balas HANYA dengan JSON: {"score": <float>, "reason": "<penjelasan singkat>"}"""

_CONTEXT_RELEVANCE_PROMPT = """\
Pertanyaan: {question}

Konteks yang diambil oleh sistem:
{context}

Nilai seberapa relevan konteks di atas dengan pertanyaan (0.0 = tidak relevan, 1.0 = sangat relevan).
Pertimbangkan: apakah konteks mengandung informasi yang dibutuhkan untuk menjawab pertanyaan?"""

_ANSWER_RELEVANCE_PROMPT = """\
Pertanyaan: {question}
Jawaban sistem: {answer}

Nilai seberapa relevan jawaban dengan pertanyaan (0.0 = tidak relevan, 1.0 = menjawab dengan lengkap).
Pertimbangkan: apakah jawaban secara langsung menjawab pertanyaan yang diajukan?"""

_FAITHFULNESS_PROMPT = """\
Konteks yang diambil:
{context}

Jawaban sistem: {answer}

Nilai seberapa faithful/konsisten jawaban dengan konteks (0.0 = banyak halusinasi, 1.0 = sepenuhnya berdasarkan konteks).
Pertimbangkan: apakah klaim dalam jawaban dapat didukung oleh konteks yang tersedia?"""


async def _llm_judge(llm: AsyncOpenAI, prompt: str) -> tuple[float, str]:
    """Minta LLM menilai dengan skor 0–1."""
    try:
        resp = await llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _JUDGE_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=200,
        )
        data = json.loads(resp.choices[0].message.content)
        score = float(data.get("score", 0.0))
        score = max(0.0, min(1.0, score))
        return score, data.get("reason", "")
    except Exception as exc:
        return 0.0, f"Error: {exc}"


async def evaluate_pair(
    llm: AsyncOpenAI,
    mitigation_advisor: MitigationAdvisorAgent,
    qa: dict,
) -> dict:
    """Evaluasi satu pasangan Q&A terhadap 3 metrik."""
    question = qa["question"]
    ground_truth = qa["ground_truth"]

    # Jalankan RAG untuk pertanyaan ini
    try:
        result = await mitigation_advisor.generate_mitigation(
            sanitized_input=question,
            incident_type="",   # kosong = tidak ada filter metadata Qdrant
            severity="Sedang",
        )
        answer = result.get("mitigation_recommendation", "")
        chunks = result.get("retrieved_chunks", [])
        context = "\n\n".join(
            f"[{c.get('metadata', {}).get('source', 'Sumber tidak diketahui')}]\n{c.get('content', '')[:400]}"
            for c in chunks[:5]
        ) or "Tidak ada konteks yang diambil."
    except Exception as exc:
        return {
            "id": qa["id"],
            "question": question,
            "error": str(exc),
            "context_relevance": 0.0,
            "answer_relevance": 0.0,
            "faithfulness": 0.0,
        }

    # Evaluasi 3 metrik secara paralel
    cr_score, cr_reason = await _llm_judge(
        llm, _CONTEXT_RELEVANCE_PROMPT.format(question=question, context=context)
    )
    ar_score, ar_reason = await _llm_judge(
        llm, _ANSWER_RELEVANCE_PROMPT.format(question=question, answer=answer)
    )
    fa_score, fa_reason = await _llm_judge(
        llm, _FAITHFULNESS_PROMPT.format(context=context, answer=answer)
    )

    return {
        "id": qa["id"],
        "question": question,
        "answer_preview": answer[:200] if answer else "",
        "chunks_retrieved": len(chunks),
        "context_relevance": round(cr_score, 3),
        "answer_relevance": round(ar_score, 3),
        "faithfulness": round(fa_score, 3),
        "reasons": {
            "context_relevance": cr_reason,
            "answer_relevance": ar_reason,
            "faithfulness": fa_reason,
        },
    }


async def run_evaluation(qa_path: str, output_path: str | None = None) -> dict:
    load_dotenv()

    try:
        llm = create_llm_client()
        embedder = create_embedder()
    except EnvironmentError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    qdrant = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)
    mitigation_advisor = MitigationAdvisorAgent(
        llm_client=llm, retriever=retriever, reranker_fn=rerank
    )

    with open(qa_path, encoding="utf-8") as f:
        qa_pairs = json.load(f)

    print(f"\n{'='*65}")
    print(f"EVALUASI RAG (LLM-as-Judge) — {len(qa_pairs)} pasangan Q&A")
    print(f"{'='*65}\n")

    results = []
    for i, qa in enumerate(qa_pairs, 1):
        print(f"[{i:02d}/{len(qa_pairs)}] {qa['id']}: {qa['question'][:55]}...")
        result = await evaluate_pair(llm, mitigation_advisor, qa)
        results.append(result)
        if "error" not in result:
            print(f"       CR={result['context_relevance']:.2f}  "
                  f"AR={result['answer_relevance']:.2f}  "
                  f"FA={result['faithfulness']:.2f}")
        else:
            print(f"       ❌ Error: {result['error']}")

    # Hitung rata-rata (abaikan error)
    valid = [r for r in results if "error" not in r]
    n = len(valid) or 1
    avg_cr = sum(r["context_relevance"] for r in valid) / n
    avg_ar = sum(r["answer_relevance"] for r in valid) / n
    avg_fa = sum(r["faithfulness"] for r in valid) / n

    targets = {"context_relevance": 0.75, "answer_relevance": 0.80, "faithfulness": 0.85}

    print(f"\n{'='*65}")
    print("HASIL EVALUASI RAG")
    print(f"{'='*65}")
    print(f"Pasangan dievaluasi: {len(valid)}/{len(qa_pairs)}")
    print(f"\nContext Relevance : {avg_cr:.3f} {'[PASS]' if avg_cr >= targets['context_relevance'] else '[FAIL]'} (target: >= {targets['context_relevance']})")
    print(f"Answer Relevance  : {avg_ar:.3f} {'[PASS]' if avg_ar >= targets['answer_relevance'] else '[FAIL]'} (target: >= {targets['answer_relevance']})")
    print(f"Faithfulness      : {avg_fa:.3f} {'[PASS]' if avg_fa >= targets['faithfulness'] else '[FAIL]'} (target: >= {targets['faithfulness']})")

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_pairs": len(qa_pairs),
        "valid_pairs": len(valid),
        "metrics": {
            "context_relevance": round(avg_cr, 3),
            "answer_relevance": round(avg_ar, 3),
            "faithfulness": round(avg_fa, 3),
        },
        "targets": targets,
        "targets_met": {
            "context_relevance": avg_cr >= targets["context_relevance"],
            "answer_relevance": avg_ar >= targets["answer_relevance"],
            "faithfulness": avg_fa >= targets["faithfulness"],
        },
        "details": results,
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nHasil disimpan: {output_path}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-file",
                        default=str(Path(__file__).parent / "rag_qa_dataset.json"))
    parser.add_argument("--output",
                        default=str(Path(__file__).parent / "rag_results.json"))
    args = parser.parse_args()
    asyncio.run(run_evaluation(args.qa_file, args.output))
