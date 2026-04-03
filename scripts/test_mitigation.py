"""Script uji manual untuk MitigationAdvisorAgent.

Penggunaan:
    python scripts/test_mitigation.py "<laporan>" "<jenis_insiden>" "<severity>"

Contoh:
    python scripts/test_mitigation.py "Email phishing dari CEO" "Phishing" "Tinggi"

Memerlukan variabel lingkungan:
    OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY (opsional)
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Tambahkan root proyek ke PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
from qdrant_client import QdrantClient

from app.agents.mitigation import MitigationAdvisorAgent
from app.rag.retriever import HybridRetriever
from app.rag.reranker import rerank


def _check_env() -> None:
    missing = [k for k in ("OPENAI_API_KEY",) if not os.getenv(k)]
    if missing:
        print(f"[ERROR] Variabel lingkungan tidak ditemukan: {', '.join(missing)}")
        sys.exit(1)


async def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    report = sys.argv[1]
    incident_type = sys.argv[2]
    severity = sys.argv[3]

    _check_env()

    print(f"\n{'='*60}")
    print(f"Laporan    : {report}")
    print(f"Jenis      : {incident_type}")
    print(f"Keparahan  : {severity}")
    print(f"{'='*60}\n")

    # --- Init klien ---
    llm = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    embedder = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_key = os.getenv("QDRANT_API_KEY")
    qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_key)

    retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)
    agent = MitigationAdvisorAgent(
        llm_client=llm,
        retriever=retriever,
        reranker_fn=rerank,
    )

    print("Menjalankan MitigationAdvisorAgent...")
    result = await agent.generate_mitigation(
        sanitized_input=report,
        incident_type=incident_type,
        severity=severity,
    )

    print("\n--- HASIL ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n--- RINGKASAN ---")
    print(f"RAG Confidence : {result.get('rag_confidence', 0.0):.3f}")
    print(f"Jumlah sitasi  : {len(result.get('citations', []))}")
    print(f"Chunk diambil  : {len(result.get('retrieved_chunks', []))}")
    print(f"\nRekomendasi:\n{result.get('mitigation_recommendation', '-')}")


if __name__ == "__main__":
    asyncio.run(main())
