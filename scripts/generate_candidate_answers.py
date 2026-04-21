"""Generate candidate answers dari RAG system untuk lembar validasi ke lokus penelitian.

Script ini menjalankan setiap pertanyaan di rag_qa_dataset.json melalui RAG pipeline,
menyimpan hasil (jawaban + konteks) ke JSON, dan menghasilkan lembar validasi HTML
yang bisa dicetak / dibawa ke Pusdatin Kementan.

Penggunaan:
    python scripts/generate_candidate_answers.py
    python scripts/generate_candidate_answers.py --qa-file tests/evaluation/rag_qa_dataset.json
    python scripts/generate_candidate_answers.py --output-dir results/validasi
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from qdrant_client import QdrantClient

from app.agents.mitigation import MitigationAdvisorAgent
from app.rag.retriever import HybridRetriever
from app.rag.reranker import rerank
from app.utils.llm_client import create_embedder, create_llm_client


async def generate_one(advisor: MitigationAdvisorAgent, qa: dict) -> dict:
    """Jalankan RAG untuk satu pertanyaan, kembalikan kandidat jawaban + konteks."""
    question = qa["question"]
    try:
        result = await advisor.generate_mitigation(
            sanitized_input=question,
            incident_type="",   # kosong = tidak ada filter metadata Qdrant
            severity="Sedang",
        )
        answer = result.get("mitigation_recommendation", "")
        chunks = result.get("retrieved_chunks", [])
        contexts = [
            {
                "source": c.get("metadata", {}).get("source", ""),
                "content_preview": c.get("content", "")[:300],
            }
            for c in chunks[:5]
        ]
        return {
            "id": qa["id"],
            "question": question,
            "ground_truth": qa.get("ground_truth", ""),
            "context_source": qa.get("context_source", ""),
            "candidate_answer": answer,
            "retrieved_contexts": contexts,
            "chunks_retrieved": len(chunks),
            "status": "ok",
        }
    except Exception as exc:
        return {
            "id": qa["id"],
            "question": question,
            "ground_truth": qa.get("ground_truth", ""),
            "context_source": qa.get("context_source", ""),
            "candidate_answer": f"[ERROR: {exc}]",
            "retrieved_contexts": [],
            "chunks_retrieved": 0,
            "status": "error",
        }


def _render_html(entries: list[dict], output_path: str) -> None:
    """Hasilkan lembar validasi HTML yang siap cetak."""
    tanggal = datetime.now().strftime("%d %B %Y")
    rows = ""
    for i, e in enumerate(entries, 1):
        contexts_html = ""
        for ctx in e.get("retrieved_contexts", []):
            src = ctx.get("source", "-")
            preview = ctx.get("content_preview", "").replace("<", "&lt;").replace(">", "&gt;")
            contexts_html += f"<li><b>{src}</b>: {preview}…</li>"
        if not contexts_html:
            contexts_html = "<li><i>Tidak ada konteks yang diambil</i></li>"

        answer_text = e.get("candidate_answer", "").replace("<", "&lt;").replace(">", "&gt;")
        gt_text = e.get("ground_truth", "").replace("<", "&lt;").replace(">", "&gt;")

        rows += f"""
        <tr>
          <td class="no">{i}</td>
          <td>
            <b>{e['id']}</b><br>
            <span class="question">{e['question']}</span>
            <div class="label">Sumber referensi: <em>{e.get('context_source','–')}</em></div>
          </td>
          <td>
            <div class="candidate">{answer_text}</div>
            <details>
              <summary>Konteks yang diambil sistem ({e['chunks_retrieved']} chunk)</summary>
              <ul class="ctx">{contexts_html}</ul>
            </details>
          </td>
          <td class="gt">{gt_text}</td>
          <td class="rating">
            <label><input type="radio" name="r{i}" value="benar"> Benar</label><br>
            <label><input type="radio" name="r{i}" value="kurang"> Kurang Tepat</label><br>
            <label><input type="radio" name="r{i}" value="salah"> Salah</label>
          </td>
          <td class="note"><textarea rows="3" placeholder="Koreksi / catatan…"></textarea></td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Lembar Validasi Ground Truth — RAG Helpdesk Pusdatin</title>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 11pt; margin: 20px; }}
  h1 {{ font-size: 14pt; text-align: center; }}
  h2 {{ font-size: 12pt; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th, td {{ border: 1px solid #aaa; padding: 8px; vertical-align: top; }}
  th {{ background: #2c5f8a; color: white; text-align: center; }}
  .no {{ text-align: center; width: 3%; }}
  .question {{ font-weight: bold; }}
  .candidate {{ background: #f0f7ff; padding: 6px; border-radius: 4px; margin-bottom: 6px; white-space: pre-wrap; }}
  .gt {{ background: #fff8e1; white-space: pre-wrap; }}
  .rating {{ text-align: center; width: 10%; }}
  .note {{ width: 18%; }}
  .note textarea {{ width: 98%; }}
  .ctx {{ font-size: 9pt; color: #555; }}
  .label {{ font-size: 9pt; color: #777; margin-top: 4px; }}
  details summary {{ cursor: pointer; font-size: 9pt; color: #2c5f8a; }}
  .footer {{ margin-top: 30px; border-top: 1px solid #ccc; padding-top: 12px; font-size: 10pt; }}
  .sig-box {{ display: inline-block; width: 220px; margin: 0 20px; text-align: center; }}
  .sig-line {{ border-top: 1px solid #333; margin-top: 60px; }}
  @media print {{ details {{ display: none; }} }}
</style>
</head>
<body>
<h1>LEMBAR VALIDASI GROUND TRUTH</h1>
<h2>Evaluasi Sistem RAG Helpdesk Keamanan Siber — Pusdatin Kementan</h2>
<p>
  <b>Tanggal:</b> {tanggal} &nbsp;|&nbsp;
  <b>Peneliti:</b> Agry Zharfa &nbsp;|&nbsp;
  <b>Total Pertanyaan:</b> {len(entries)}
</p>

<p><b>Petunjuk Pengisian:</b></p>
<ol>
  <li>Kolom <b>"Jawaban Sistem (RAG)"</b> adalah jawaban yang dihasilkan sistem AI secara otomatis.</li>
  <li>Kolom <b>"Ground Truth Referensi"</b> adalah jawaban awal yang mengacu pada literatur standar. Mohon dikoreksi/dilengkapi sesuai SOP internal Pusdatin.</li>
  <li>Kolom <b>"Penilaian"</b>: beri tanda pada <em>Benar</em>, <em>Kurang Tepat</em>, atau <em>Salah</em>.</li>
  <li>Kolom <b>"Koreksi/Catatan"</b>: isi koreksi jika jawaban sistem kurang tepat atau salah.</li>
</ol>

<table>
  <thead>
    <tr>
      <th class="no">No</th>
      <th style="width:22%">ID &amp; Pertanyaan</th>
      <th style="width:30%">Jawaban Sistem (RAG)</th>
      <th style="width:20%">Ground Truth Referensi</th>
      <th>Penilaian</th>
      <th>Koreksi / Catatan Validator</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>

<div class="footer">
  <p>Dengan ini menyatakan bahwa validasi di atas dilakukan secara objektif berdasarkan pengetahuan dan SOP yang berlaku.</p>
  <div style="margin-top: 20px;">
    <div class="sig-box">
      <div class="sig-line">Peneliti</div>
      <div>Agry Zharfa</div>
    </div>
    <div class="sig-box">
      <div class="sig-line">Validator</div>
      <div>( _________________ )</div>
      <div style="font-size:9pt">Tim Keamanan Siber Pusdatin Kementan</div>
    </div>
  </div>
</div>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")


async def main(qa_file: str, output_dir: str) -> None:
    load_dotenv()

    try:
        llm = create_llm_client()
        embedder = create_embedder()
    except EnvironmentError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
    retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)
    advisor = MitigationAdvisorAgent(llm_client=llm, retriever=retriever, reranker_fn=rerank)

    with open(qa_file, encoding="utf-8") as f:
        qa_pairs = json.load(f)

    print(f"\n{'='*60}")
    print(f"Generate Candidate Answers — {len(qa_pairs)} pertanyaan")
    print(f"{'='*60}\n")

    results = []
    for i, qa in enumerate(qa_pairs, 1):
        print(f"[{i:02d}/{len(qa_pairs)}] {qa['id']}: {qa['question'][:60]}...")
        entry = await generate_one(advisor, qa)
        results.append(entry)
        status_icon = "[OK]" if entry["status"] == "ok" else "[ERR]"
        print(f"       {status_icon}  chunks={entry['chunks_retrieved']}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Simpan JSON lengkap (untuk eval_rag.py dan debugging)
    json_path = out_dir / "candidate_answers.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # Hasilkan lembar validasi HTML
    html_path = out_dir / "lembar_validasi_pusdatin.html"
    _render_html(results, str(html_path))

    ok_count = sum(1 for r in results if r["status"] == "ok")
    print(f"\n{'='*60}")
    print(f"Selesai: {ok_count}/{len(results)} berhasil")
    print(f"JSON tersimpan : {json_path}")
    print(f"Lembar validasi: {html_path}")
    print(f"\nBuka {html_path} di browser lalu cetak (Ctrl+P) untuk dibawa ke Pusdatin.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--qa-file",
        default=str(Path(__file__).resolve().parent.parent / "tests/evaluation/rag_qa_dataset.json"),
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent.parent / "results/validasi"),
    )
    args = parser.parse_args()
    asyncio.run(main(args.qa_file, args.output_dir))
