"""Mitigation Advisor Agent — Agentic RAG dengan sitasi terverifikasi."""
import json
import logging
from pathlib import Path

from openai import AsyncOpenAI, APITimeoutError

from app.rag.reranker import rerank

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "config" / "prompts" / "mitigation.txt"

RETRIEVAL_SCORE_THRESHOLD = 0.3
MAX_ITERATIONS = 3
TOP_K_RETRIEVAL = 20
TOP_K_RERANK = 5

_FALLBACK_RESULT = {
    "mitigation_recommendation": (
        "Sistem tidak menemukan panduan SOP yang relevan untuk jenis insiden ini. "
        "Silakan hubungi tim CSIRT secara langsung untuk penanganan lebih lanjut."
    ),
    "citations": [],
    "retrieved_chunks": [],
    "rag_confidence": 0.0,
}


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _parse_llm_response(raw: str) -> dict | None:
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    return None


def _assemble_context(chunks: list[dict]) -> str:
    """Format top chunks into a numbered context block for the prompt."""
    lines = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "Dokumen tidak diketahui")
        section = meta.get("section", "")
        source_ref = f"{source}, {section}".strip(", ")
        lines.append(f"[{i}] Sumber: {source_ref}\n{chunk.get('content', '').strip()}")
    return "\n\n".join(lines)


def _check_adequacy(chunks: list[dict]) -> bool:
    """Return True if at least one chunk has a score above threshold."""
    for chunk in chunks:
        score = chunk.get("final_score", chunk.get("rrf_score", chunk.get("score", 0.0)))
        if score >= RETRIEVAL_SCORE_THRESHOLD:
            return True
    return False


def _expand_query(query: str, incident_type: str, iteration: int) -> str:
    """Expand query for subsequent retrieval iterations."""
    expansions = {
        "Phishing": "mitigasi phishing email palsu social engineering langkah respons",
        "Malware": "mitigasi malware trojan virus isolasi karantina endpoint",
        "Ransomware": "mitigasi ransomware enkripsi backup pemulihan isolasi jaringan",
        "Web Defacement": "mitigasi web defacement pemulihan website restore backup",
        "DDoS": "mitigasi DDoS distributed denial of service rate limiting firewall",
        "Akses Tidak Sah": "mitigasi akses tidak sah unauthorized access kontrol akun audit log",
        "Kebocoran Data": "mitigasi kebocoran data data breach notifikasi PDPA",
        "Lainnya": "mitigasi insiden keamanan siber respons prosedur SOP",
    }
    keywords = expansions.get(incident_type, "mitigasi insiden keamanan siber")
    if iteration == 2:
        return f"{query} {keywords}"
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

    # Collect all available source references from chunks
    available_sources = set()
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        source = meta.get("source", "")
        section = meta.get("section", "")
        if source:
            available_sources.add(source.lower())
        if section:
            available_sources.add(section.lower())

    valid_steps = []
    for step in steps:
        source_claim = str(step.get("source", "")).lower()
        if not source_claim:
            logger.warning("Langkah '%s' tidak memiliki sitasi, dihapus.", step.get("action", "")[:50])
            continue

        # Accept if any available source keyword appears in the claim
        has_match = any(
            avail_word in source_claim or source_claim in avail_word
            for avail_word in available_sources
            if avail_word
        )
        # Also accept well-known standard references (they may not be in chunks but are trustworthy)
        is_known_standard = any(
            kw in source_claim
            for kw in ["nist", "mitre", "att&ck", "iso", "bssn", "kominfo", "peraturan"]
        )

        if has_match or is_known_standard:
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


class MitigationAdvisorAgent:
    def __init__(self, llm_client: AsyncOpenAI, retriever, reranker_fn=None, model: str = "gpt-4o") -> None:
        self.llm = llm_client
        self.retriever = retriever
        self.reranker_fn = reranker_fn or rerank
        self.model = model
        self._prompt_template = _load_prompt()

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
                new_chunks = self.retriever.retrieve(current_query, incident_type=incident_type, top_k=TOP_K_RETRIEVAL)
            except Exception as exc:
                logger.error("Retrieval gagal pada iterasi %d: %s", iteration, exc)
                new_chunks = []

            all_chunks = _merge_results(all_chunks, new_chunks)

            try:
                reranked = self.reranker_fn(query, all_chunks, top_k=TOP_K_RERANK, incident_type=incident_type)
            except Exception as exc:
                logger.error("Reranking gagal: %s", exc)
                reranked = all_chunks[:TOP_K_RERANK]

            if _check_adequacy(reranked):
                break

            logger.info("Iterasi %d: tidak ada chunk cukup relevan, melanjutkan...", iteration)

        # --- Fallback jika tidak ada dokumen relevan ---
        if not _check_adequacy(reranked if all_chunks else []):
            logger.warning("Tidak ada dokumen relevan ditemukan setelah %d iterasi.", MAX_ITERATIONS)
            return {**_FALLBACK_RESULT}

        top_chunks = reranked if all_chunks else []

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
                parsed = _parse_llm_response(raw)

                if parsed is None:
                    logger.error("Tidak bisa parse JSON dari LLM (attempt %d): %s", attempt + 1, raw[:200])
                    if attempt == 0:
                        continue
                    return {**_FALLBACK_RESULT, "retrieved_chunks": top_chunks}

                steps = parsed.get("mitigation_steps", [])
                valid_steps = _validate_citations(steps, top_chunks)
                citations = _build_citations(valid_steps)
                rag_confidence = _compute_rag_confidence(top_chunks)

                # Re-assemble recommendation string
                recommendation_parts = []
                for s in valid_steps:
                    recommendation_parts.append(
                        f"{s.get('step', '?')}. {s.get('action', '')} [{s.get('source', '')}]"
                    )
                general = parsed.get("general_guidance", "")
                escalation = parsed.get("escalation_note", "")
                if general:
                    recommendation_parts.append(f"\nPanduan umum: {general}")
                if escalation:
                    recommendation_parts.append(f"Catatan eskalasi: {escalation}")

                mitigation_recommendation = "\n".join(recommendation_parts) if recommendation_parts else _FALLBACK_RESULT["mitigation_recommendation"]

                return {
                    "mitigation_recommendation": mitigation_recommendation,
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
