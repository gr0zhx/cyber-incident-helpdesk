import json
import re
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

# ---------------------------------------------------------------------------
# Tactic → incident type mapping untuk tagging otomatis MITRE ATT&CK
# ---------------------------------------------------------------------------
_TACTIC_TO_INCIDENT_TYPES: dict[str, list[str]] = {
    "initial-access":       ["phishing", "akses_tidak_sah"],
    "execution":            ["malware", "ransomware"],
    "persistence":          ["malware", "akses_tidak_sah"],
    "privilege-escalation": ["akses_tidak_sah"],
    "defense-evasion":      ["malware"],
    "credential-access":    ["akses_tidak_sah", "phishing"],
    "collection":           ["kebocoran_data"],
    "exfiltration":         ["kebocoran_data"],
    "impact":               ["ransomware", "ddos", "web_defacement"],
    "lateral-movement":     ["malware", "akses_tidak_sah"],
    "command-and-control":  ["malware", "ransomware"],
    "reconnaissance":       ["general"],
    "resource-development": ["general"],
    "discovery":            ["akses_tidak_sah", "malware"],
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", text).strip()


def _get_external_id(obj: dict) -> str:
    for ref in obj.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id", "")
    return ""


def _tactics_from_technique(obj: dict) -> list[str]:
    return [p["phase_name"] for p in obj.get("kill_chain_phases", [])]


def _incident_types_from_tactics(tactics: list[str]) -> list[str]:
    types: set[str] = set()
    for t in tactics:
        types.update(_TACTIC_TO_INCIDENT_TYPES.get(t, []))
    if not types:
        types.add("general")
    return sorted(types)


# ---------------------------------------------------------------------------
# PDF ingestion (existing)
# ---------------------------------------------------------------------------

def load_metadata(metadata_path: str | Path) -> dict:
    with open(metadata_path, encoding="utf-8") as f:
        return json.load(f)


def ingest_document(pdf_path: str | Path, metadata: dict) -> list[Document]:
    """Load a PDF and return one Document per page with enriched metadata."""
    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()

    enriched: list[Document] = []
    for page in pages:
        page.metadata.update(
            {
                "doc_id": metadata["doc_id"],
                "doc_title": metadata["doc_title"],
                "source_framework": metadata["source_framework"],
                "language": metadata.get("language", "en"),
                "incident_types": metadata.get("incident_types", []),
                "version": metadata.get("version", ""),
            }
        )
        enriched.append(page)
    return enriched


def ingest_directory(
    docs_dir: str | Path,
    metadata_dir: str | Path,
) -> list[Document]:
    """Ingest all PDFs in docs_dir whose metadata exists in metadata_dir."""
    docs_dir = Path(docs_dir)
    metadata_dir = Path(metadata_dir)

    all_documents: list[Document] = []

    for meta_file in sorted(metadata_dir.glob("*.json")):
        meta = load_metadata(meta_file)
        pdf_path = docs_dir / meta["filename"]

        if not pdf_path.exists():
            print(f"[SKIP] PDF tidak ditemukan: {pdf_path}")
            continue

        print(f"[READ] {meta['doc_title']} ({pdf_path.name})")
        docs = ingest_document(pdf_path, meta)
        all_documents.extend(docs)

    return all_documents


# ---------------------------------------------------------------------------
# MITRE ATT&CK STIX ingestion
# ---------------------------------------------------------------------------

def ingest_attack_stix(stix_path: str | Path) -> list[Document]:
    """Ekstrak mitigasi (M1xxx) dan teknik serangan dari STIX bundle ATT&CK.

    Menghasilkan dua jenis Document:
    - Mitigation document: setiap course-of-action M1xxx beserta teknik yang dimitigasi
    - Technique document: setiap attack-pattern dengan deskripsi dan taktiknya

    Args:
        stix_path: Path ke file STIX JSON (misal: knowledge_base/enterprise-attack.json)

    Returns:
        List of Document siap dichunk dan diembed.
    """
    stix_path = Path(stix_path)
    bundle = json.loads(stix_path.read_text(encoding="utf-8"))
    objects_by_id: dict[str, dict] = {obj["id"]: obj for obj in bundle["objects"]}

    # --- Kumpulkan relasi mitigates: course-of-action → attack-pattern ---
    coa_to_techniques: dict[str, list[str]] = {}
    for obj in bundle["objects"]:
        if (
            obj.get("type") == "relationship"
            and obj.get("relationship_type") == "mitigates"
        ):
            coa_id = obj["source_ref"]
            tgt_id = obj["target_ref"]
            coa_to_techniques.setdefault(coa_id, []).append(tgt_id)

    documents: list[Document] = []

    # --- 1. Mitigation documents (M1xxx course-of-action) ---
    for obj in bundle["objects"]:
        if obj.get("type") != "course-of-action":
            continue
        ext_id = _get_external_id(obj)
        if not ext_id.startswith("M1"):
            continue  # skip deprecated per-technique mitigations

        name = obj.get("name", "")
        description = _strip_html(obj.get("description", ""))

        # Kumpulkan nama teknik yang dimitigasi
        mitigated_techniques: list[str] = []
        all_tactics: set[str] = set()
        for tech_id in coa_to_techniques.get(obj["id"], []):
            tech = objects_by_id.get(tech_id)
            if not tech:
                continue
            tech_ext_id = _get_external_id(tech)
            tech_name = tech.get("name", "")
            mitigated_techniques.append(f"{tech_ext_id}: {tech_name}")
            all_tactics.update(_tactics_from_technique(tech))

        # Buat content yang informatif untuk RAG
        content_parts = [
            f"Mitigasi MITRE ATT&CK: {name} ({ext_id})",
            "",
            description,
        ]
        if mitigated_techniques:
            content_parts += [
                "",
                f"Teknik yang dimitigasi ({len(mitigated_techniques)}):",
            ] + [f"  - {t}" for t in sorted(mitigated_techniques)[:20]]  # cap 20

        incident_types = _incident_types_from_tactics(list(all_tactics))

        documents.append(
            Document(
                page_content="\n".join(content_parts),
                metadata={
                    "doc_id": "mitre-attack-enterprise",
                    "doc_title": "MITRE ATT&CK Enterprise",
                    "source": f"MITRE ATT&CK, {name} ({ext_id})",
                    "source_framework": "MITRE",
                    "external_id": ext_id,
                    "object_type": "mitigation",
                    "language": "en",
                    "incident_types": incident_types,
                    "section_header": f"{ext_id} {name}",
                },
            )
        )

    # --- 2. Technique documents (attack-pattern) ---
    for obj in bundle["objects"]:
        if obj.get("type") != "attack-pattern":
            continue
        # Skip subtechniques untuk mengurangi noise (fokus ke teknik utama)
        ext_id = _get_external_id(obj)
        if "." in ext_id:
            continue

        name = obj.get("name", "")
        description = _strip_html(obj.get("description", ""))
        if not description:
            continue

        tactics = _tactics_from_technique(obj)
        incident_types = _incident_types_from_tactics(tactics)
        tactics_str = ", ".join(tactics) if tactics else "unknown"

        content = (
            f"Teknik Serangan MITRE ATT&CK: {name} ({ext_id})\n"
            f"Taktik: {tactics_str}\n\n"
            f"{description[:1200]}"  # cap deskripsi panjang
        )

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "doc_id": "mitre-attack-enterprise",
                    "doc_title": "MITRE ATT&CK Enterprise",
                    "source": f"MITRE ATT&CK, {name} ({ext_id})",
                    "source_framework": "MITRE",
                    "external_id": ext_id,
                    "object_type": "technique",
                    "language": "en",
                    "incident_types": incident_types,
                    "section_header": f"{ext_id} {name}",
                },
            )
        )

    mitigations = sum(1 for d in documents if d.metadata.get("object_type") == "mitigation")
    techniques = sum(1 for d in documents if d.metadata.get("object_type") == "technique")
    print(f"[MITRE ATT&CK] {mitigations} mitigasi + {techniques} teknik = {len(documents)} dokumen")
    return documents
