"""Evaluasi RAG dengan jalur RAGAS atau fallback LLM-as-judge.

Skrip ini memprioritaskan GitHub Models yang dikonfigurasi lewat `.env`.
Token `GITHUB_TOKEN` dipetakan ke `OPENAI_API_KEY` agar client OpenAI-compatible
dan `ragas` bisa memakainya tanpa set manual di shell.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import site
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _prioritize_venv_site_packages() -> None:
    """Ensure venv site-packages are preferred over system site-packages."""
    for venv_path in reversed(site.getsitepackages()):
        if venv_path in sys.path:
            sys.path.remove(venv_path)
        sys.path.insert(0, venv_path)


def _bootstrap_github_models_env() -> None:
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = github_token


def _print_ragas_import_failure(reason: str) -> None:
    print("Gagal memuat `ragas` di environment ini.")
    print(f"Alasan: {reason}")
    print("Coba upgrade dependency: pip install -U ragas langchain-community langchain-core")
    print("Skrip akan menjalankan fallback LLM-as-judge (eval_rag.py).")


def _extract_retry_seconds(message: str) -> int | None:
    match = re.search(r"Please wait (\d+) seconds before retrying", message)
    if match:
        return int(match.group(1))
    return None


async def main(
    qa_file: str,
    output_path: str | None = None,
    limit: int | None = None,
    pause_seconds: float = 7.0,
) -> None:
    _prioritize_venv_site_packages()
    _bootstrap_github_models_env()

    try:
        import ragas  # type: ignore
        print("Detected installed package: ragas")
    except Exception as exc:
        _print_ragas_import_failure(str(exc))
        try:
            from tests.evaluation.eval_rag import run_evaluation as run_llm_judge
        except Exception as exc:
            print(f"Fallback eval_rag import failed: {exc}")
            sys.exit(1)

        summary = await run_llm_judge(qa_file, output_path)
        print("Fallback evaluation (LLM-as-judge) complete.")
        if output_path:
            print(f"Hasil disimpan: {output_path}")
        else:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    try:
        print("Running evaluation via ragas (GitHub Models path)...")
        with open(qa_file, encoding="utf-8") as f:
            qa_pairs = json.load(f)

        from datasets import Dataset
        from langchain_openai import ChatOpenAI

        from app.agents.mitigation import MitigationAdvisorAgent
        from app.rag.reranker import rerank
        from app.rag.retriever import HybridRetriever
        from app.utils.llm_client import create_embedder, create_llm_client
        from qdrant_client import QdrantClient

        llm = create_llm_client()
        embedder = create_embedder()
        qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)
        advisor = MitigationAdvisorAgent(llm_client=llm, retriever=retriever, reranker_fn=rerank)

        selected_pairs = qa_pairs[:limit] if limit else qa_pairs
        results = []

        for index, qa in enumerate(selected_pairs, 1):
            try:
                res = await advisor.generate_mitigation(
                    sanitized_input=qa["question"],
                    incident_type=qa.get("incident_type", ""),
                    severity=qa.get("severity", "Sedang"),
                )
            except Exception as exc:
                message = str(exc)
                if "RateLimitReached" in message or "429" in message:
                    retry_after = _extract_retry_seconds(message)
                    if retry_after is not None and retry_after <= 60:
                        print(f"Rate limit singkat terdeteksi, tunggu {retry_after} detik lalu lanjut...")
                        await asyncio.sleep(retry_after)
                        res = await advisor.generate_mitigation(
                            sanitized_input=qa["question"],
                            incident_type=qa.get("incident_type", ""),
                            severity=qa.get("severity", "Sedang"),
                        )
                    else:
                        print(f"Rate limit provider terlalu besar untuk dilanjutkan sekarang: {message}")
                        print("Hasil parsial akan disimpan dan evaluasi dihentikan agar patuh batas provider.")
                        break
                else:
                    raise

            results.append(
                {
                    "id": qa.get("id"),
                    "question": qa.get("question"),
                    "ground_truth": qa.get("ground_truth"),
                    "candidate_answer": res.get("mitigation_recommendation", ""),
                    "retrieved_chunks": res.get("retrieved_chunks", []),
                }
            )

            if pause_seconds > 0 and index < len(selected_pairs):
                await asyncio.sleep(pause_seconds)

        out_path = Path(output_path or Path(__file__).resolve().parent / "ragas_results.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Candidate answers saved to: {out_path}")

        ragas_rows = []
        for row in results:
            ragas_rows.append(
                {
                    "question": row.get("question", ""),
                    "ground_truth": row.get("ground_truth", ""),
                    "answer": row.get("candidate_answer", ""),
                    "contexts": [
                        chunk.get("content", "")
                        for chunk in row.get("retrieved_chunks", [])[:5]
                        if chunk.get("content")
                    ],
                }
            )

        ragas_dataset = Dataset.from_list(ragas_rows)
        ragas_llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.0,
        )

        try:
            if hasattr(ragas, "evaluate"):
                print("Calling ragas.evaluate(...) — adapt arguments if needed.")
                ragas_result = ragas.evaluate(
                    dataset=ragas_dataset,
                    llm=ragas_llm,
                    embeddings=embedder,
                )
                print(ragas_result)
            else:
                print("`ragas` installed but no `evaluate` helper detected.")
                print("Please run ragas CLI or adapt this script to your ragas API.")
        except Exception as exc:
            print(f"ragas evaluation call failed (non-fatal): {exc}")

    except Exception as exc:
        print(f"Error running RAGAS path: {exc}")
        print("Falling back to LLM-as-judge (eval_rag.py)")
        from tests.evaluation.eval_rag import run_evaluation as run_llm_judge

        summary = await run_llm_judge(qa_file, output_path)
        if output_path:
            print(f"Hasil fallback disimpan: {output_path}")
        else:
            print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    default_qa = str(Path(__file__).resolve().parent / "rag_qa_dataset.json")
    parser.add_argument("--qa-file", default=default_qa)
    parser.add_argument("--output", default=str(Path(__file__).resolve().parent / "rag_ragas_results.json"))
    parser.add_argument("--limit", type=int, default=None, help="Batasi jumlah pertanyaan agar lebih aman terhadap rate limit.")
    parser.add_argument("--pause-seconds", type=float, default=7.0, help="Jeda antar item untuk menahan laju request GitHub Models.")
    args = parser.parse_args()

    asyncio.run(main(args.qa_file, args.output, args.limit, args.pause_seconds))
