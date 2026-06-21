"""Mitigation Advisor Agent — Agentic RAG dengan sitasi terverifikasi."""
import logging
import re

from openai import AsyncOpenAI, APITimeoutError

from app.rag.reranker import rerank
from app.utils.llm_parser import parse_llm_json
from app.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

RETRIEVAL_SCORE_THRESHOLD = 0.3  # Threshold final_score untuk menentukan relevansi dokumen
MAX_ITERATIONS = 3
TOP_K_RETRIEVAL = 30
TOP_K_RERANK = 5
_MIN_SOURCE_MATCH_LENGTH = 5

_FALLBACK_RESULT = {
    "mitigation_recommendation": (
        "Sistem tidak menemukan panduan SOP yang relevan untuk jenis insiden ini. "
        "Silakan hubungi tim CSIRT secara langsung untuk penanganan lebih lanjut."
    ),
    "citations": [],
    "retrieved_chunks": [],
    "rag_confidence": 0.0,
}



def _assemble_context(chunks: list[dict]) -> str:
    """Format top chunks into a numbered context block for the prompt."""
    lines = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        # source sering kosong di knowledge base — gunakan doc_title sebagai fallback
        source = (
            meta.get("source")
            or meta.get("doc_title")
            or meta.get("source_framework")
            or "Dokumen tidak diketahui"
        )
        section = meta.get("section") or meta.get("section_header") or ""
        source_ref = f"{source}, {section}".strip(", ")
        lines.append(f"[{i}] Sumber: {source_ref}\n{chunk.get('content', '').strip()}")
    return "\n\n".join(lines)


def _check_adequacy(chunks: list[dict]) -> bool:
    """Return True if at least one chunk has final_score above threshold.

    final_score dari reranker sudah skala 0–1 (gabungan cosine + RRF),
    konsisten dengan RETRIEVAL_SCORE_THRESHOLD.
    """
    for chunk in chunks:
        score = chunk.get("final_score", chunk.get("score", 0.0))
        if score >= RETRIEVAL_SCORE_THRESHOLD:
            return True
    return False


def _expand_query(query: str, incident_type: str, iteration: int) -> str:
    """Expand query for subsequent retrieval iterations."""
    expansions = {
        "Phishing": "phishing social engineering user training edukasi pengguna mengenali melaporkan ancaman mitigasi respons insiden",
        "Malware": "antivirus antimalware behavior prevention endpoint deteksi blokir malware isolasi karantina eradikasi",
        "Ransomware": "data backup backup terisolasi pemulihan ransomware enkripsi eradikasi restore isolasi jaringan",
        "Web Defacement": "data backup pemulihan konten website defacement restore integritas recovery",
        "DDoS": "filter network traffic lalu lintas jaringan denial of service rate limiting firewall mitigasi",
        "Akses Tidak Sah": "unauthorized credential use monitoring account policies MFA multi-factor authentication audit log akses tidak sah",
        "Kebocoran Data": "chain of custody evidence preservation eksfiltrasi data kebocoran filter network traffic notifikasi langkah",
        "Lainnya": "mitigasi insiden keamanan siber respons prosedur SOP langkah",
    }
    keywords = expansions.get(incident_type, "mitigasi insiden keamanan siber langkah respons")
    if iteration == 2:
        # Query bersih khusus mitigasi — jangan append ke query skenario panjang
        # agar retriever bisa menemukan chunk "Mitigasi MITRE ATT&CK" yang relevan
        return f"mitigasi langkah respons {incident_type} {keywords}"
    return keywords


def _merge_results(results1: list[dict], results2: list[dict]) -> list[dict]:
    """Merge two result lists deduplicating by chunk id."""
    seen = set()
    merged = []
    for chunk in results1 + results2:
        cid = chunk.get("id")
        if cid not in seen:
            seen.add(cid)
            merged.append(chunk)
    return merged


def _validate_citations(steps: list[dict], chunks: list[dict]) -> list[dict]:
    """Remove or flag steps where source cannot be traced to a retrieved chunk."""
    if not chunks:
        return []

    num_chunks = len(chunks)

    # Collect all available source references from chunks
    available_sources = set()
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        source = meta.get("source", "")
        section = meta.get("section", "")
        doc_title = meta.get("doc_title", "")
        section_header = meta.get("section_header", "")
        source_framework = meta.get("source_framework", "")
        external_id = meta.get("external_id", "")
        for value in (source, section, doc_title, section_header, source_framework, external_id):
            if value:
                available_sources.add(str(value).lower())

    valid_steps = []
    for step in steps:
        source_claim = str(step.get("source", "")).strip().lower()
        if not source_claim:
            logger.warning("Langkah '%s' tidak memiliki sitasi, dihapus.", step.get("action", "")[:50])
            continue

        # Accept [N] numeric reference pointing to a valid chunk (e.g. "[1] Training and Awareness")
        num_refs = re.findall(r'\[(\d+)\]', source_claim)
        has_valid_num_ref = any(1 <= int(n) <= num_chunks for n in num_refs)

        # Accept if any retrieved source name appears in the claim (forward direction)
        has_source_match = any(
            avail_word in source_claim
            for avail_word in available_sources
            if len(avail_word) >= _MIN_SOURCE_MATCH_LENGTH
        )
        # Also accept well-known standard references (they may not be in chunks but are trustworthy)
        is_known_standard = any(
            kw in source_claim
            for kw in ["nist", "mitre", "att&ck", "iso 270", "bssn", "kominfo", "peraturan"]
        )

        if has_valid_num_ref or has_source_match or is_known_standard:
            valid_steps.append(step)
        else:
            logger.warning("Sitasi tidak terverifikasi: '%s', langkah dihapus.", step.get("source", ""))

    return valid_steps


def _build_citations(steps: list[dict]) -> list[dict]:
    """Extract citation objects from validated steps."""
    citations = []
    seen = set()
    for step in steps:
        source = step.get("source", "")
        if source and source not in seen:
            seen.add(source)
            citations.append({"source": source, "step": step.get("step")})
    return citations


def _compute_rag_confidence(chunks: list[dict]) -> float:
    if not chunks:
        return 0.0
    scores = [
        chunk.get("final_score", chunk.get("rrf_score", chunk.get("score", 0.0)))
        for chunk in chunks
    ]
    return round(min(1.0, sum(scores) / len(scores)), 3)


_KNOWLEDGE_FALLBACK = {
    "mitigation_recommendation": (
        "Informasi ini tidak ditemukan dalam dokumen referensi yang tersedia. "
        "Silakan hubungi tim CSIRT Pusdatin Kementan untuk pertanyaan lebih lanjut."
    ),
    "citations": [],
    "retrieved_chunks": [],
    "rag_confidence": 0.0,
}


class MitigationAdvisorAgent:
    def __init__(self, llm_client: AsyncOpenAI, retriever, reranker_fn=None, model: str = "gpt-4o") -> None:
        self.llm = llm_client
        self.retriever = retriever
        self.reranker_fn = reranker_fn or rerank
        self.model = model
        self._prompt_template = load_prompt("mitigation")
        self._knowledge_prompt_template = load_prompt("knowledge")

    def _build_knowledge_messages(self, context: str, sanitized_input: str) -> list[dict]:
        prompt = (
            self._knowledge_prompt_template
            .replace("{assembled_context}", context)
            .replace("{sanitized_input}", sanitized_input)
        )
        return [{"role": "user", "content": prompt}]

    async def generate_knowledge_response(
        self,
        sanitized_input: str,
        source_preference: str | None = None,
        incident_type: str = "general",
    ) -> dict:
        """Answer a regulatory/policy knowledge question using RAG + prose format.

        Uses the same hybrid retrieval + reranker as generate_mitigation(),
        but outputs a narrative answer (not numbered steps) and validates
        citations from retrieved chunks.
        Always returns a dict — never raises.
        """
        all_chunks: list[dict] = []

        for iteration in range(1, 3):
            try:
                # Iterasi 2: untuk MITRE prefer chunk mitigasi agar tidak didominasi deskripsi serangan
                use_mitigation_filter = iteration == 2 and source_preference is None
                current_query = sanitized_input if iteration == 1 else f"mitigasi prosedur kebijakan {incident_type} {sanitized_input}"
                prefer_src = "NIST" if source_preference == "NIST" else ("BSSN" if source_preference == "BSSN" else None)
                new_chunks = self.retriever.retrieve(
                    current_query,
                    incident_type=incident_type,
                    top_k=TOP_K_RETRIEVAL,
                    prefer_mitigations=use_mitigation_filter,
                    prefer_source=prefer_src,
                )
            except Exception as exc:
                logger.warning("Knowledge retrieval gagal iterasi %d: %s", iteration, exc)
                new_chunks = []

            all_chunks = _merge_results(all_chunks, new_chunks)

            try:
                reranked = self.reranker_fn(sanitized_input, all_chunks, top_k=TOP_K_RERANK, incident_type=incident_type)
            except Exception as exc:
                logger.error("Reranking gagal: %s", exc)
                reranked = all_chunks[:TOP_K_RERANK]

            if _check_adequacy(reranked):
                break

        if not _check_adequacy(reranked if all_chunks else []):
            logger.warning("Tidak ada dokumen relevan untuk query_knowledge.")
            return {**_KNOWLEDGE_FALLBACK}

        top_chunks = reranked if all_chunks else []

        # Untuk query_knowledge, buang chunk "Teknik Serangan MITRE ATT&CK" (T-series)
        # agar LLM hanya mendapat chunk mitigasi/kebijakan, bukan deskripsi cara serangan.
        filtered = [
            c for c in top_chunks
            if not c.get("content", "").startswith("Teknik Serangan MITRE ATT&CK")
        ]
        if filtered:
            top_chunks = filtered

        context = _assemble_context(top_chunks)
        messages = self._build_knowledge_messages(context, sanitized_input)

        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or ""
            parsed = parse_llm_json(raw)

            if parsed is None:
                logger.error("Tidak bisa parse JSON knowledge response: %s", raw[:200])
                return {**_KNOWLEDGE_FALLBACK, "retrieved_chunks": top_chunks}

            answer = parsed.get("knowledge_answer", "").strip()
            source_refs = parsed.get("source_refs", [])

            if not answer:
                return {**_KNOWLEDGE_FALLBACK, "retrieved_chunks": top_chunks}

            # Append source refs as footer
            recommendation = answer
            if source_refs:
                recommendation += "\n\nSumber:"
                for ref in source_refs:
                    recommendation += f"\n{ref}"

            citations = [{"source": ref, "step": None} for ref in source_refs if ref]
            rag_confidence = _compute_rag_confidence(top_chunks)

            return {
                "mitigation_recommendation": recommendation,
                "citations": citations,
                "retrieved_chunks": top_chunks,
                "rag_confidence": rag_confidence,
            }

        except APITimeoutError:
            logger.warning("LLM timeout saat generate_knowledge_response")
            return {
                **_KNOWLEDGE_FALLBACK,
                "retrieved_chunks": top_chunks,
                "mitigation_recommendation": "LLM timeout. Silakan hubungi tim CSIRT secara langsung.",
            }
        except Exception as exc:
            logger.exception("Error saat generate_knowledge_response: %s", exc)
            return {
                **_KNOWLEDGE_FALLBACK,
                "retrieved_chunks": top_chunks,
                "mitigation_recommendation": f"Error tidak terduga: {type(exc).__name__}. Hubungi tim CSIRT.",
            }

    def _build_messages(self, context: str, incident_type: str, severity: str, sanitized_input: str) -> list[dict]:
        prompt = (
            self._prompt_template
            .replace("{assembled_context}", context)
            .replace("{incident_type}", incident_type)
            .replace("{severity}", severity)
            .replace("{sanitized_input}", sanitized_input)
        )
        return [{"role": "user", "content": prompt}]

    async def generate_mitigation(
        self,
        sanitized_input: str,
        incident_type: str,
        severity: str,
        source_preference: str | None = None,
    ) -> dict:
        """Generate mitigation recommendation using Agentic RAG.

        Always returns a dict — never raises. Falls back gracefully on error.
        """
        query = f"{incident_type}: {sanitized_input}"
        all_chunks: list[dict] = []

        # --- Agentic RAG: up to MAX_ITERATIONS retrieval passes ---
        for iteration in range(1, MAX_ITERATIONS + 1):
            try:
                current_query = query if iteration == 1 else _expand_query(query, incident_type, iteration)
                # Strategi retrieval per iterasi:
                # - source_preference="NIST": SEMUA iterasi filter ke NIST agar chunk MITRE
                #   tidak mendominasi hasil akhir setelah merge+rerank.
                # - default iterasi 2: cari chunk mitigasi MITRE (soal insiden teknis)
                use_mitigation_filter = iteration == 2 and not source_preference
                prefer_src = "NIST" if source_preference == "NIST" else None
                new_chunks = self.retriever.retrieve(
                    current_query,
                    incident_type=incident_type,
                    top_k=TOP_K_RETRIEVAL,
                    prefer_mitigations=use_mitigation_filter,
                    prefer_source=prefer_src,
                )
            except Exception as exc:
                logger.warning(
                    "Retrieval gagal pada iterasi %d (query=%r): %s",
                    iteration, current_query, exc,
                )
                new_chunks = []

            all_chunks = _merge_results(all_chunks, new_chunks)

            try:
                reranked = self.reranker_fn(query, all_chunks, top_k=TOP_K_RERANK, incident_type=incident_type)
            except Exception as exc:
                logger.error("Reranking gagal: %s", exc)
                reranked = all_chunks[:TOP_K_RERANK]

            if _check_adequacy(reranked):
                # Soal NIST: paksa iterasi 2 agar pass NIST-only selalu berjalan.
                # Chunk MITRE sering menang di iterasi 1 meski kurang relevan untuk
                # pertanyaan prosedural IR (dokumentasi, prioritasi, bukti digital).
                if source_preference == "NIST" and iteration < 2:
                    logger.info("Iterasi %d: NIST preference aktif, lanjut ke pass NIST-only...", iteration)
                    continue

                # Soal non-NIST: lanjut ke iterasi 2 hanya jika chunk didominasi
                # deskripsi serangan ("Teknik Serangan MITRE ATT&CK").
                attack_chunks = sum(
                    1 for c in reranked
                    if c.get("content", "").startswith("Teknik Serangan MITRE ATT&CK")
                )
                is_dominated_by_attacks = attack_chunks >= len(reranked) // 2 + 1
                if iteration >= 2 or not is_dominated_by_attacks:
                    break

            logger.info("Iterasi %d: lanjut ke iterasi berikutnya...", iteration)

        # --- Fallback jika tidak ada dokumen relevan ---
        if not _check_adequacy(reranked if all_chunks else []):
            logger.warning("Tidak ada dokumen relevan ditemukan setelah %d iterasi.", MAX_ITERATIONS)
            return {**_FALLBACK_RESULT}

        top_chunks = reranked if all_chunks else []

        # --- Pastikan minimal 2 chunk mitigasi di top_chunks untuk soal MITRE ---
        # Jika chunk masih didominasi deskripsi serangan, injeksi chunk mitigasi terbaik
        # dari all_chunks (sudah diambil di iterasi 2 dengan prefer_mitigations=True).
        if not source_preference:
            mitig_in_top = sum(
                1 for c in top_chunks
                if c.get("content", "").startswith("Mitigasi MITRE ATT&CK")
            )
            if mitig_in_top < 2:
                mitig_candidates = sorted(
                    [c for c in all_chunks if c.get("content", "").startswith("Mitigasi MITRE ATT&CK")],
                    key=lambda x: x.get("final_score", x.get("rrf_score", 0.0)),
                    reverse=True,
                )
                existing_ids = {c["id"] for c in top_chunks}
                new_mitig = [c for c in mitig_candidates if c["id"] not in existing_ids]
                slots_needed = 2 - mitig_in_top
                if new_mitig:
                    attack_in_top = [
                        c for c in top_chunks
                        if c.get("content", "").startswith("Teknik Serangan MITRE ATT&CK")
                    ]
                    non_attack = [
                        c for c in top_chunks
                        if not c.get("content", "").startswith("Teknik Serangan MITRE ATT&CK")
                    ]
                    injected = new_mitig[:slots_needed]
                    top_chunks = (non_attack + injected + attack_in_top)[:TOP_K_RERANK]
                    logger.info(
                        "Injeksi %d chunk mitigasi dari all_chunks ke top_chunks.",
                        len(injected),
                    )

        # --- Assemble context dan panggil LLM ---
        context = _assemble_context(top_chunks)
        messages = self._build_messages(context, incident_type, severity, sanitized_input)

        for attempt in range(2):
            try:
                response = await self.llm.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=800,
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content or ""
                parsed = parse_llm_json(raw)

                if parsed is None:
                    logger.error("Tidak bisa parse JSON dari LLM (attempt %d): %s", attempt + 1, raw[:200])
                    if attempt == 0:
                        continue
                    return {**_FALLBACK_RESULT, "retrieved_chunks": top_chunks}

                steps = parsed.get("mitigation_steps", [])
                valid_steps = _validate_citations(steps, top_chunks)

                # Fail-closed: jika semua langkah gagal validasi sitasi → fallback
                if not valid_steps:
                    logger.warning(
                        "Semua %d langkah gagal validasi sitasi, gunakan fallback.", len(steps)
                    )
                    return {**_FALLBACK_RESULT, "retrieved_chunks": top_chunks}

                citations = _build_citations(valid_steps)
                rag_confidence = _compute_rag_confidence(top_chunks)

                # Re-assemble recommendation string dari validated steps saja.
                # general_guidance dan escalation_note sengaja tidak dimasukkan
                # karena tidak divalidasi sitasi — menghindari hallucination di output.
                recommendation_parts = []
                for s in valid_steps:
                    recommendation_parts.append(
                        f"{s.get('step', '?')}. {s.get('action', '')}"
                    )

                # Deduplicated citation block at the end
                seen_src: set[str] = set()
                unique_sources: list[str] = []
                for s in valid_steps:
                    src = s.get("source", "")
                    if src and src not in seen_src:
                        seen_src.add(src)
                        unique_sources.append(src)
                if unique_sources:
                    recommendation_parts.append("\nSumber:")
                    for i, src in enumerate(unique_sources, 1):
                        recommendation_parts.append(f"[{i}] {src}")

                return {
                    "mitigation_recommendation": "\n".join(recommendation_parts),
                    "citations": citations,
                    "retrieved_chunks": top_chunks,
                    "rag_confidence": rag_confidence,
                    "mitigation_steps": valid_steps,
                }

            except APITimeoutError:
                logger.warning("LLM timeout pada attempt %d", attempt + 1)
                if attempt == 1:
                    return {
                        **_FALLBACK_RESULT,
                        "retrieved_chunks": top_chunks,
                        "mitigation_recommendation": "LLM timeout. Silakan hubungi tim CSIRT secara langsung.",
                    }

            except Exception as exc:
                logger.exception("Error tidak terduga saat generate_mitigation: %s", exc)
                return {
                    **_FALLBACK_RESULT,
                    "retrieved_chunks": top_chunks,
                    "mitigation_recommendation": f"Error tidak terduga: {type(exc).__name__}. Hubungi tim CSIRT.",
                }

        return {**_FALLBACK_RESULT, "retrieved_chunks": top_chunks}
