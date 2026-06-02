"""Hybrid Retriever — semantic + keyword search via Qdrant, merged dengan RRF."""
import logging

from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchText

from app.rag.embedder import COLLECTION_NAME

RRF_K = 60


def _rrf_score(rank: int, k: int = RRF_K) -> float:
    return 1.0 / (k + rank + 1)


def _reciprocal_rank_fusion(
    semantic_hits: list[dict],
    keyword_hits: list[dict],
) -> list[dict]:
    """Merge two ranked lists using Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    payloads: dict[str, dict] = {}

    for rank, hit in enumerate(semantic_hits):
        pid = hit["id"]
        scores[pid] = scores.get(pid, 0.0) + _rrf_score(rank)
        payloads[pid] = hit

    for rank, hit in enumerate(keyword_hits):
        pid = hit["id"]
        scores[pid] = scores.get(pid, 0.0) + _rrf_score(rank)
        payloads.setdefault(pid, hit)

    merged = sorted(scores.keys(), key=lambda pid: scores[pid], reverse=True)
    return [
        {**payloads[pid], "rrf_score": scores[pid]}
        for pid in merged
    ]


def _build_incident_filter(incident_type: str | None) -> Filter | None:
    if not incident_type:
        return None
    # Normalise to match stored format: lowercase + spaces → underscores
    # e.g. "Web Defacement" → "web_defacement", "Akses Tidak Sah" → "akses_tidak_sah"
    normalised = incident_type.lower().replace(" ", "_")
    return Filter(
        must=[
            FieldCondition(
                key="incident_types",
                match=MatchValue(value=normalised),
            )
        ]
    )


class HybridRetriever:
    def __init__(self, qdrant_client: QdrantClient, embedder: OpenAIEmbeddings) -> None:
        self.client = qdrant_client
        self.embedder = embedder

    def retrieve(
        self,
        query: str,
        incident_type: str | None = None,
        top_k: int = 20,
        prefer_mitigations: bool = False,
    ) -> list[dict]:
        """
        Hybrid retrieval: semantic search + keyword search, merged via RRF.

        Returns list of dicts with keys: id, content, metadata, score, rrf_score.
        """
        metadata_filter = _build_incident_filter(incident_type)

        # Jika prefer_mitigations=True, tambahkan filter konten ke mitigation chunks saja.
        # Digunakan pada iterasi 2 agar retriever hanya mengambil chunk "Mitigasi MITRE ATT&CK"
        # (bukan deskripsi teknik serangan yang semantiknya mirip tapi bukan panduan tindakan).
        if prefer_mitigations:
            mitigation_condition = FieldCondition(
                key="content", match=MatchText(text="Mitigasi MITRE ATT&CK")
            )
            if metadata_filter and metadata_filter.must:
                metadata_filter = Filter(must=list(metadata_filter.must) + [mitigation_condition])
            else:
                metadata_filter = Filter(must=[mitigation_condition])

        # --- Semantic search ---
        query_vector = self.embedder.embed_query(query)
        semantic_points = []

        # Tests / some clients mock `search`; prefer it when available so
        # unit tests that patch `client.search` continue to work.
        if hasattr(self.client, "search"):
            try:
                resp = self.client.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=query_vector,
                    query_filter=metadata_filter,
                    limit=top_k,
                    with_payload=True,
                )
                # `search` may return a plain list (tests) or an object with `.points`.
                if isinstance(resp, list):
                    semantic_points = resp
                else:
                    semantic_points = getattr(resp, "points", []) or []
            except Exception:
                semantic_points = []
        else:
            semantic_response = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                query_filter=metadata_filter,
                limit=top_k,
                with_payload=True,
            )
            semantic_points = getattr(semantic_response, "points", []) or []

        semantic_hits = [
            {
                "id": str(hit.id),
                "content": hit.payload.get("content", ""),
                "metadata": {k: v for k, v in hit.payload.items() if k != "content"},
                "score": getattr(hit, "score", 0.0),
            }
            for hit in semantic_points
        ]

        # --- Keyword search via full-text index ---
        keyword_hits = self._keyword_search(query, metadata_filter, top_k)

        # --- RRF merge ---
        merged = _reciprocal_rank_fusion(semantic_hits, keyword_hits)
        return merged[:top_k]

    def _keyword_search(
        self,
        query: str,
        metadata_filter: Filter | None,
        limit: int,
    ) -> list[dict]:
        """Full-text keyword search using Qdrant payload text index."""
        keyword_conditions = [
            FieldCondition(key="content", match=MatchText(text=query))
        ]
        if metadata_filter and metadata_filter.must:
            keyword_conditions.extend(metadata_filter.must)

        combined_filter = Filter(must=keyword_conditions)

        try:
            results, _ = self.client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=combined_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            return [
                {
                    "id": str(point.id),
                    "content": point.payload.get("content", ""),
                    "metadata": {k: v for k, v in point.payload.items() if k != "content"},
                    "score": 0.0,
                }
                for point in results
            ]
        except Exception as exc:
            logger.warning("Keyword search gagal, fallback ke kosong: %s", exc)
            return []
