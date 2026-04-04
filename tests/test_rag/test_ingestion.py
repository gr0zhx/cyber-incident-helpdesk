"""Unit tests for MITRE ATT&CK STIX ingestion (ingest_attack_stix)."""
import json
import tempfile
from pathlib import Path

import pytest

from app.rag.ingestion import (
    ingest_attack_stix,
    _get_external_id,
    _strip_html,
    _incident_types_from_tactics,
    _tactics_from_technique,
)


# ---------------------------------------------------------------------------
# Minimal STIX bundle fixture
# ---------------------------------------------------------------------------

_MITIGATION_ID = "course-of-action--m1-user-training"
_TECHNIQUE_ID = "attack-pattern--phishing-t1566"
_SUBTECHNIQUE_ID = "attack-pattern--phishing-sub-t1566-001"

MINI_STIX_BUNDLE = {
    "type": "bundle",
    "id": "bundle--test",
    "objects": [
        # M1017 User Training (mitigasi modern M1xxx)
        {
            "type": "course-of-action",
            "id": _MITIGATION_ID,
            "name": "User Training",
            "description": "Train users to be aware of <code>access</code> or manipulation attempts.",
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "M1017"}
            ],
        },
        # Deprecated mitigation (bukan M1xxx — harus dilewati)
        {
            "type": "course-of-action",
            "id": "course-of-action--deprecated",
            "name": "Old Mitigation",
            "description": "Deprecated mitigation.",
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1566 Mitigation"}
            ],
        },
        # T1566 Phishing (teknik utama)
        {
            "type": "attack-pattern",
            "id": _TECHNIQUE_ID,
            "name": "Phishing",
            "description": "Adversaries may send phishing messages to gain access to victim systems.",
            "kill_chain_phases": [{"phase_name": "initial-access", "kill_chain_name": "mitre-attack"}],
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1566"}
            ],
        },
        # T1566.001 (sub-teknik — harus dilewati)
        {
            "type": "attack-pattern",
            "id": _SUBTECHNIQUE_ID,
            "name": "Spearphishing Attachment",
            "description": "Sub-technique description.",
            "kill_chain_phases": [{"phase_name": "initial-access", "kill_chain_name": "mitre-attack"}],
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1566.001"}
            ],
        },
        # Relationship: M1017 mitigates T1566
        {
            "type": "relationship",
            "id": "relationship--001",
            "relationship_type": "mitigates",
            "source_ref": _MITIGATION_ID,
            "target_ref": _TECHNIQUE_ID,
        },
        # Relationship dengan tipe lain — harus dilewati
        {
            "type": "relationship",
            "id": "relationship--002",
            "relationship_type": "uses",
            "source_ref": "intrusion-set--001",
            "target_ref": _TECHNIQUE_ID,
        },
    ],
}


def _write_stix(data: dict) -> Path:
    """Tulis bundle ke file temp dan kembalikan path-nya."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(data, tmp)
    tmp.flush()
    return Path(tmp.name)


# ---------------------------------------------------------------------------
# Pure helper tests
# ---------------------------------------------------------------------------

def test_get_external_id_mitre():
    obj = {"external_references": [{"source_name": "mitre-attack", "external_id": "M1017"}]}
    assert _get_external_id(obj) == "M1017"


def test_get_external_id_missing():
    assert _get_external_id({}) == ""
    assert _get_external_id({"external_references": []}) == ""


def test_strip_html_removes_tags():
    assert _strip_html("<code>rm -rf</code>") == "rm -rf"
    assert _strip_html("plain text") == "plain text"
    assert _strip_html("<b>bold</b> and <i>italic</i>") == "bold and italic"


def test_tactics_from_technique():
    obj = {
        "kill_chain_phases": [
            {"phase_name": "initial-access", "kill_chain_name": "mitre-attack"},
            {"phase_name": "execution", "kill_chain_name": "mitre-attack"},
        ]
    }
    result = _tactics_from_technique(obj)
    assert "initial-access" in result
    assert "execution" in result


def test_tactics_from_technique_empty():
    assert _tactics_from_technique({}) == []


def test_incident_types_from_tactics_initial_access():
    types = _incident_types_from_tactics(["initial-access"])
    assert "phishing" in types
    assert "akses_tidak_sah" in types


def test_incident_types_from_tactics_impact():
    types = _incident_types_from_tactics(["impact"])
    assert "ransomware" in types
    assert "ddos" in types
    assert "web_defacement" in types


def test_incident_types_from_tactics_unknown_falls_back_to_general():
    types = _incident_types_from_tactics(["unknown-tactic"])
    assert "general" in types


def test_incident_types_from_tactics_empty_falls_back_to_general():
    types = _incident_types_from_tactics([])
    assert "general" in types


# ---------------------------------------------------------------------------
# ingest_attack_stix integration tests
# ---------------------------------------------------------------------------

def test_ingest_returns_documents():
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    assert len(docs) > 0


def test_ingest_includes_m1xxx_mitigation():
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    mitigations = [d for d in docs if d.metadata.get("object_type") == "mitigation"]
    assert len(mitigations) == 1
    assert "M1017" in mitigations[0].page_content
    assert "User Training" in mitigations[0].page_content


def test_ingest_skips_deprecated_mitigation():
    """Mitigasi tanpa ID M1xxx harus dilewati."""
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    mitigations = [d for d in docs if d.metadata.get("object_type") == "mitigation"]
    # Hanya 1 mitigasi valid (M1017), deprecated dilewati
    assert all("M1" in d.metadata["external_id"] for d in mitigations)


def test_ingest_includes_main_technique():
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    techniques = [d for d in docs if d.metadata.get("object_type") == "technique"]
    assert len(techniques) == 1
    assert "T1566" in techniques[0].page_content
    assert "Phishing" in techniques[0].page_content


def test_ingest_skips_subtechniques():
    """Sub-teknik (T1566.001) harus dilewati."""
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    techniques = [d for d in docs if d.metadata.get("object_type") == "technique"]
    ext_ids = [d.metadata["external_id"] for d in techniques]
    assert "T1566.001" not in ext_ids


def test_ingest_mitigation_lists_mitigated_techniques():
    """Dokumen mitigasi harus menyebutkan teknik yang dimitigasi."""
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    mitigation = next(d for d in docs if d.metadata.get("object_type") == "mitigation")
    assert "T1566" in mitigation.page_content
    assert "Phishing" in mitigation.page_content


def test_ingest_strips_html_from_description():
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    mitigation = next(d for d in docs if d.metadata.get("object_type") == "mitigation")
    assert "<code>" not in mitigation.page_content
    assert "access" in mitigation.page_content  # konten tetap ada setelah strip


def test_ingest_metadata_fields_present():
    """Semua metadata field wajib harus ada di setiap dokumen."""
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    required = {"doc_id", "doc_title", "source_framework", "external_id", "object_type", "incident_types"}
    for doc in docs:
        assert required.issubset(doc.metadata.keys()), f"Missing keys in {doc.metadata}"


def test_ingest_incident_types_tagged_correctly():
    """Teknik T1566 (initial-access) → incident_types harus include phishing."""
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    technique = next(d for d in docs if d.metadata.get("external_id") == "T1566")
    assert "phishing" in technique.metadata["incident_types"]


def test_ingest_mitigation_incident_types_from_linked_techniques():
    """Mitigasi M1017 dimitigasi T1566 (initial-access) → harus punya phishing."""
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    mitigation = next(d for d in docs if d.metadata.get("external_id") == "M1017")
    assert "phishing" in mitigation.metadata["incident_types"]


def test_ingest_source_framework_is_mitre():
    path = _write_stix(MINI_STIX_BUNDLE)
    docs = ingest_attack_stix(path)
    for doc in docs:
        assert doc.metadata["source_framework"] == "MITRE"


def test_ingest_empty_bundle_returns_empty():
    empty = {"type": "bundle", "id": "bundle--empty", "objects": []}
    path = _write_stix(empty)
    docs = ingest_attack_stix(path)
    assert docs == []
