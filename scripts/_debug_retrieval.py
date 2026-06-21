"""Debug retrieval scores untuk pertanyaan yang masih fallback."""
import asyncio, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

github_token = os.getenv("GITHUB_TOKEN")
if github_token and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = github_token

from app.rag.reranker import rerank
from app.rag.retriever import HybridRetriever
from app.utils.llm_client import create_embedder
from qdrant_client import QdrantClient

qdrant = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"), api_key=os.getenv("QDRANT_API_KEY"))
embedder = create_embedder()
retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)

THRESHOLD = 0.3

queries = [
    ("QA-015", "Kebijakan akun apa yang harus diterapkan untuk mencegah akses tidak sah pada sistem — seperti penguncian akun, pembatasan waktu login, dan Multi-Factor Authentication?", "Akses Tidak Sah"),
    ("QA-018", "Bagaimana cara memfilter lalu lintas jaringan untuk mencegah eksfiltrasi data dari sistem organisasi ke layanan eksternal yang tidak diotorisasi?", "Kebocoran Data"),
    ("QA-011", "Saya menerima email phishing yang mengatasnamakan atasan dengan nada mendesak dan tautan login palsu. Apa langkah mitigasi phishing spearphishing via tautan yang tepat?", "Phishing"),
]

for qid, question, inc_type in queries:
    print(f"\n{'='*60}")
    print(f"{qid} | incident_type={inc_type}")
    print(f"Q: {question[:80]}")
    chunks = retriever.retrieve(question, incident_type=inc_type, top_k=30, prefer_mitigations=False, prefer_source=None)
    reranked = rerank(question, chunks, top_k=5, incident_type=inc_type)
    print(f"Retrieved: {len(chunks)} chunks, Top-5 after rerank:")
    for i, c in enumerate(reranked, 1):
        score = c.get("final_score", c.get("score", 0))
        src = c.get("metadata", {}).get("source_framework", c.get("metadata", {}).get("doc_title", "?"))
        content_preview = c.get("content", "")[:80].replace("\n", " ")
        above = "OK" if score >= THRESHOLD else "NO"
        print(f"  [{i}] score={score:.3f} {above} [{src}] {content_preview}")
    above_threshold = [c for c in reranked if c.get("final_score", c.get("score", 0)) >= THRESHOLD]
    print(f"  >> {len(above_threshold)}/{len(reranked)} chunk di atas threshold {THRESHOLD}")
