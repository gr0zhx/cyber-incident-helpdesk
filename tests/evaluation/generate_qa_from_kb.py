"""Generate Q&A dataset dari konten knowledge base asli.

Strategi reverse engineering:
1. Sample chunk mitigasi MITRE dan chunk prosedur NIST dari Qdrant
2. Gunakan GPT untuk generate pertanyaan skenario yang bisa dijawab chunk tersebut
3. Ground truth = distilasi konten chunk asli (bukan tulisan manual)
4. Output: kandidat Q&A JSON untuk dievaluasi RAGAS

Usage:
    python tests/evaluation/generate_qa_from_kb.py
    python tests/evaluation/generate_qa_from_kb.py --n-mitre 15 --n-nist 15 --output candidate_qa.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Fix Unicode output di Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_QUESTION_SYSTEM = """\
Kamu adalah ahli keamanan siber yang membantu merancang dataset evaluasi sistem RAG.
Tugasmu: berdasarkan potongan dokumen keamanan siber yang diberikan, buat SATU pasangan Q&A.

Aturan:
1. Pertanyaan harus berupa SKENARIO realistis dari sudut pandang pegawai non-teknis yang mengalami insiden
   Contoh: "Tiba-tiba muncul pesan di layar saya bahwa file terenkripsi. Apa yang harus saya lakukan?"
2. Ground truth harus LANGSUNG berasal dari isi dokumen — jangan tambahkan informasi luar
3. Ground truth: ringkas, 2-4 kalimat, bahasa Indonesia, berupa langkah/jawaban konkret
4. Format output JSON: {"question": "...", "ground_truth": "..."}
5. Pastikan pertanyaan dan ground truth bisa diverifikasi dari teks dokumen yang diberikan"""

_QUESTION_PROMPT = """\
Dokumen referensi:
{chunk_content}

Buat satu pasangan Q&A sesuai instruksi di atas. Output HANYA JSON."""


async def _generate_qa_pair(llm, chunk_content: str) -> dict | None:
    try:
        resp = await llm.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": _QUESTION_SYSTEM},
                {"role": "user", "content": _QUESTION_PROMPT.format(chunk_content=chunk_content[:1200])},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=400,
        )
        raw = resp.choices[0].message.content or ""
        data = json.loads(raw)
        if data.get("question") and data.get("ground_truth"):
            return data
        return None
    except Exception as exc:
        print(f"  [WARN] Gagal generate: {exc}")
        return None


def _sample_mitre_mitigation_chunks(client, n: int) -> list[dict]:
    """Ambil sample chunk MITRE yang merupakan panduan mitigasi."""
    from qdrant_client.models import Filter, FieldCondition, MatchText

    results, _ = client.scroll(
        collection_name="cybersecurity_knowledge",
        scroll_filter=Filter(must=[
            FieldCondition(key="content", match=MatchText(text="Mitigasi MITRE ATT&CK"))
        ]),
        limit=200,
        with_payload=True,
        with_vectors=False,
    )
    # Filter yang punya deskripsi cukup panjang (> 200 karakter) agar Q&A bermakna
    good = [p for p in results if len(p.payload.get("content", "")) > 200]
    sampled = random.sample(good, min(n, len(good)))
    return [
        {
            "id": str(p.id),
            "content": p.payload.get("content", ""),
            "doc_title": p.payload.get("doc_title", ""),
            "source_framework": "MITRE ATT&CK",
            "incident_types": p.payload.get("incident_types", []),
        }
        for p in sampled
    ]


def _sample_nist_chunks(client, n: int) -> list[dict]:
    """Ambil sample chunk NIST berisi prosedur incident response."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    results, _ = client.scroll(
        collection_name="cybersecurity_knowledge",
        scroll_filter=Filter(must=[
            FieldCondition(key="source_framework", match=MatchValue(value="NIST"))
        ]),
        limit=500,
        with_payload=True,
        with_vectors=False,
    )
    # Filter chunk yang panjang dan berisi keyword prosedur
    keywords = ["should", "must", "recommend", "procedure", "step", "contain",
                "isolat", "report", "evidence", "backup", "restore", "notif"]
    good = [
        p for p in results
        if len(p.payload.get("content", "")) > 250
        and any(kw in p.payload.get("content", "").lower() for kw in keywords)
    ]
    sampled = random.sample(good, min(n, len(good)))
    return [
        {
            "id": str(p.id),
            "content": p.payload.get("content", ""),
            "doc_title": p.payload.get("doc_title", ""),
            "source_framework": "NIST SP 800-61",
            "incident_types": p.payload.get("incident_types", []),
        }
        for p in sampled
    ]


async def main(n_mitre: int, n_nist: int, output_path: str) -> None:
    from qdrant_client import QdrantClient
    from openai import AsyncOpenAI

    qdrant = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    llm = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print(f"Sampling {n_mitre} MITRE mitigation chunks + {n_nist} NIST chunks...")
    mitre_chunks = _sample_mitre_mitigation_chunks(qdrant, n_mitre)
    nist_chunks = _sample_nist_chunks(qdrant, n_nist)
    all_chunks = mitre_chunks + nist_chunks

    print(f"Total chunks: {len(all_chunks)} (MITRE={len(mitre_chunks)}, NIST={len(nist_chunks)})")
    print("Generating Q&A pairs via GPT...\n")

    results = []
    for i, chunk in enumerate(all_chunks, 1):
        print(f"[{i}/{len(all_chunks)}] {chunk['source_framework']} | {chunk['content'][:60]}...")
        qa = await _generate_qa_pair(llm, chunk["content"])
        if qa:
            results.append({
                "id": f"CAND-{i:03d}",
                "question": qa["question"],
                "ground_truth": qa["ground_truth"],
                "context_source": chunk["source_framework"],
                "incident_types": chunk["incident_types"],
                "source_chunk_preview": chunk["content"][:200],
            })
            print(f"  Q: {qa['question'][:80]}")
        await asyncio.sleep(1.5)  # hindari rate limit

    out = Path(output_path)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(results)} kandidat Q&A disimpan ke: {out}")
    print("Langkah selanjutnya:")
    print("  python tests/evaluation/eval_ragas.py --qa-file", output_path, "--limit 30")
    print("  Lalu pilih Q&A dengan faithfulness > 0.75 sebagai dataset final.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-mitre", type=int, default=15, help="Jumlah chunk MITRE mitigation")
    parser.add_argument("--n-nist", type=int, default=15, help="Jumlah chunk NIST procedure")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent / "candidate_qa.json"),
        help="Path output JSON kandidat Q&A",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    asyncio.run(main(args.n_mitre, args.n_nist, args.output))
