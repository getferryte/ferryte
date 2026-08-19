"""Tests for deletion attestations.

The properties that matter here are integrity properties, not formatting ones:
a tampered record must fail verification, an incomplete deletion must never
render as VERIFIED, and the scope limitations must always be present — they are
what make the artifact safe to hand to a security reviewer.
"""

from __future__ import annotations

import json
from pathlib import Path

from ferryte.reports.attestation import (
    DeletionProbe,
    build_attestation,
    verify_attestation,
)


def _clean_attestation() -> object:
    return build_attestation(
        source_id="user_8813",
        backend="pgvector:public.memories",
        rows_deleted=4,
        rows_remaining=0,
        probes=[
            DeletionProbe(
                kind="retrieval", query="ALPHA-VEGA-1A2B3C", tenant_id="acme", hits=0, clean=True
            ),
            DeletionProbe(
                kind="raw_store_scan", query="ALPHA-VEGA-1A2B3C", tenant_id=None, hits=0, clean=True
            ),
        ],
        blind_spots=[],
        tool_version="0.3.0",
    )


def test_clean_deletion_is_verified() -> None:
    att = _clean_attestation().finalise()  # type: ignore[attr-defined]
    assert att.verified_clean is True
    assert att.verdict == "VERIFIED"
    assert att.content_hash.startswith("sha256:")


def test_remaining_rows_force_incomplete() -> None:
    att = build_attestation(
        source_id="user_1",
        backend="fake",
        rows_deleted=2,
        rows_remaining=1,
        probes=[],
        blind_spots=[],
    ).finalise()
    assert att.verdict == "INCOMPLETE"
    assert att.verified_clean is False


def test_dirty_probe_forces_incomplete() -> None:
    att = build_attestation(
        source_id="user_1",
        backend="fake",
        rows_deleted=3,
        rows_remaining=0,
        probes=[
            DeletionProbe(
                kind="raw_store_scan",
                query="secret",
                tenant_id=None,
                hits=2,
                clean=False,
                detail="still present",
            )
        ],
        blind_spots=[],
    ).finalise()
    assert att.verdict == "INCOMPLETE"


def test_blind_spots_narrow_the_claim_without_faking_failure() -> None:
    att = build_attestation(
        source_id="user_1",
        backend="fake",
        rows_deleted=1,
        rows_remaining=0,
        probes=[DeletionProbe(kind="retrieval", query="x", tenant_id=None, hits=0, clean=True)],
        blind_spots=["Backend exposes no raw-scan path."],
    ).finalise()
    assert att.verdict == "VERIFIED_WITH_BLIND_SPOTS"
    assert att.verified_clean is True


def test_limitations_are_always_present_and_named() -> None:
    att = _clean_attestation().finalise()  # type: ignore[attr-defined]
    text = att.to_markdown()
    assert "not** a certificate of regulatory compliance" in text.replace("*", "*")
    # The specific gaps a reviewer must know about:
    for needle in ("backups", "Model weights", "sub-processors"):
        assert needle.lower() in text.lower()


def test_tampering_is_detected(tmp_path: Path) -> None:
    att = _clean_attestation().finalise()  # type: ignore[attr-defined]
    path = tmp_path / "att.json"
    path.write_text(att.to_json(), encoding="utf-8")

    ok, message = verify_attestation(path)
    assert ok, message

    data = json.loads(path.read_text(encoding="utf-8"))
    data["rows_remaining"] = 0
    data["rows_deleted"] = 999  # someone inflates the number after the fact
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    ok, message = verify_attestation(path)
    assert not ok
    assert "hash mismatch" in message.lower()


def test_unsigned_record_says_so_rather_than_implying_authenticity(tmp_path: Path) -> None:
    att = _clean_attestation().finalise(sign=False)  # type: ignore[attr-defined]
    text = att.to_markdown()
    assert "Signature:** none" in text or "none." in text
    path = tmp_path / "att.json"
    path.write_text(att.to_json(), encoding="utf-8")
    ok, message = verify_attestation(path)
    assert ok
    assert "no signature" in message.lower()


def test_signing_roundtrip_when_cryptography_available(tmp_path: Path) -> None:
    try:
        import cryptography  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("cryptography not installed")

    key = tmp_path / "key.pem"
    att = _clean_attestation().finalise(sign=True, key_path=key)  # type: ignore[attr-defined]
    assert att.signature_algorithm == "ed25519"
    assert att.signature and att.public_key

    path = tmp_path / "att.json"
    path.write_text(att.to_json(), encoding="utf-8")
    ok, message = verify_attestation(path)
    assert ok, message
    assert "valid" in message.lower()
