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
    ids: list[str] | None = None,
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

        import warnings as _warnings
        _warnings.filterwarnings("ignore", category=DeprecationWarning, module="ragas")

        from langchain_openai import ChatOpenAI, OpenAIEmbeddings as LCOAIEmbeddings
        from ragas import evaluate as _ragas_evaluate
        from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import AnswerRelevancy, Faithfulness
        from ragas.metrics._nv_metrics import ContextRelevance as _ContextRelevance

        from app.agents.mitigation import MitigationAdvisorAgent
        from app.rag.reranker import rerank
        from app.rag.retriever import HybridRetriever
        from app.utils.llm_client import create_embedder, create_llm_client
        from qdrant_client import QdrantClient

        _base_url = os.getenv("OPENAI_BASE_URL")
        _api_key = os.getenv("OPENAI_API_KEY")
        _model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # max_tokens=4096: Faithfulness generates long NLI-statement JSON;
        # GitHub Models defaults to 1024 output tokens which causes truncation.
        _lc_llm = ChatOpenAI(
            model=_model,
            temperature=0.0,
            openai_api_key=_api_key,
            max_tokens=4096,
            **({"base_url": _base_url} if _base_url else {}),
        )
        _ragas_llm = LangchainLLMWrapper(_lc_llm)
        # AnswerRelevancy calls embed_query() — requires LangChain embeddings interface
        _lc_embed = LCOAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=_api_key,
            **({"openai_api_base": _base_url} if _base_url else {}),
        )
        _ragas_embed = LangchainEmbeddingsWrapper(_lc_embed)

        llm = create_llm_client()
        embedder = create_embedder()
        qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)
        advisor = MitigationAdvisorAgent(llm_client=llm, retriever=retriever, reranker_fn=rerank)

        selected_pairs = qa_pairs[:limit] if limit else qa_pairs
        if ids:
            selected_pairs = [q for q in selected_pairs if q.get("id") in ids]
        results = []

        for index, qa in enumerate(selected_pairs, 1):
            print(f"[{index}/{len(selected_pairs)}] Generating answer for: {qa.get('id', '?')}")
            try:
                # Handle both incident_type (string) dan incident_types (list)
                inc_type = qa.get("incident_type") or ""
                if not inc_type:
                    inc_list = qa.get("incident_types", [])
                    inc_type = inc_list[0] if inc_list else ""
                # Map context_source ke source_preference untuk retrieval
                ctx_src = qa.get("context_source", "")
                src_pref = "NIST" if "NIST" in ctx_src else None
                res = await advisor.generate_mitigation(
                    sanitized_input=qa["question"],
                    incident_type=inc_type,
                    severity=qa.get("severity", "Sedang"),
                    source_preference=src_pref,
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

        out_path = Path(output_path or Path(__file__).resolve().parent / "rag_ragas_results.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Candidate answers disimpan sementara: {out_path}")

        # Bangun EvaluationDataset RAGAS 0.4 (field: user_input, response, retrieved_contexts, reference)
        samples = []
        for row in results:
            contexts = [
                chunk.get("content", "")
                for chunk in row.get("retrieved_chunks", [])[:5]
                if chunk.get("content")
            ]
            samples.append(
                SingleTurnSample(
                    user_input=row.get("question", ""),
                    response=row.get("candidate_answer", ""),
                    retrieved_contexts=contexts,
                    reference=row.get("ground_truth", ""),
                )
            )
        ragas_dataset = EvaluationDataset(samples=samples)

        # 3 metrik sesuai paper asli Es et al. (2023) — semuanya reference-free
        # AnswerRelevancy: prompt internal RAGAS default men-generate pertanyaan dalam
        # Bahasa Inggris, sementara korpus (pertanyaan & jawaban) Bahasa Indonesia.
        # Membandingkan Q-asli (ID) vs Q-generated (EN) memberi penalti cross-lingual
        # ~0.2 pada cosine similarity yang tidak merefleksikan relevansi sebenarnya.
        # Kami paksa generate dalam Bahasa Indonesia agar perbandingan konsisten satu bahasa.
        _answer_relevancy = AnswerRelevancy(llm=_ragas_llm, embeddings=_ragas_embed)
        _answer_relevancy.question_generation.instruction += (
            " PENTING: Tulis 'question' yang dihasilkan dalam Bahasa Indonesia."
        )
        _metrics = [
            Faithfulness(llm=_ragas_llm),
            _answer_relevancy,
            _ContextRelevance(llm=_ragas_llm),
        ]
        from ragas.run_config import RunConfig as _RunConfig
        # max_workers=1: GitHub Models rate limit tidak tahan 16 parallel request default RAGAS
        _run_cfg = _RunConfig(max_workers=1, max_retries=3, timeout=120)
        print(f"\nMenjalankan ragas.evaluate() dengan {len(_metrics)} metrik pada {len(samples)} sampel ...")
        ragas_result = _ragas_evaluate(
            dataset=ragas_dataset,
            metrics=_metrics,
            run_config=_run_cfg,
            raise_exceptions=False,
            show_progress=True,
        )

        _df = ragas_result.to_pandas()
        _summary = {}
        for m in _metrics:
            col = m.name
            if col in _df.columns:
                _summary[col] = float(_df[col].dropna().mean()) if not _df[col].dropna().empty else None
            else:
                _summary[col] = None

        _detail = ragas_result.to_pandas().to_dict(orient="records")
        out_path.write_text(
            json.dumps(
                {"summary": _summary, "per_question": _detail, "qa_pairs": results},
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )
        print(f"\nHasil RAGAS disimpan: {out_path}")
        print("\n=== Ringkasan RAGAS ===")
        for _k, _v in _summary.items():
            _disp = f"{_v:.4f}" if _v is not None else "N/A"
            print(f"  {_k}: {_disp}")

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
    parser.add_argument("--ids", nargs="+", default=None, help="Jalankan hanya soal dengan ID tertentu, contoh: --ids QA-004 QA-013 QA-005")
    args = parser.parse_args()

    asyncio.run(main(args.qa_file, args.output, args.limit, args.pause_seconds, args.ids))
