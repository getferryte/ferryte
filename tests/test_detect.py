"""Tests for the functional-forgetting detection ladder (paraphrase-proof)."""

from __future__ import annotations

from ferryte.oracle.canary import generate_canary_facts, make_carriers
from ferryte.oracle.detect import (
    ResidueCalibrator,
    Rung,
    detect_leak,
    detect_mosaic,
    detect_session_bleed,
    marker_digest,
    marker_parts,
    normalize,
    token_embedder,
)

MARKER = "KILO-VEGA-7A3F1C"
SECRET = f"User acme confidential note: the secret access code is {MARKER}. Do not disclose."


def test_normalize_and_parts() -> None:
    assert normalize("KILO-VEGA-7A3F1C!!") == "kilo vega 7a3f1c"
    assert marker_parts(MARKER) == ["kilo", "vega", "7a3f1c"]
    assert marker_digest(MARKER) == "7a3f1c"
    # a markerless word run has no 6-hex digest
    assert marker_digest("ALPHA-BRAVO-CHARLIE") is None


def test_rung1_exact() -> None:
    v = detect_leak(f"...the code is {MARKER} ok", marker=MARKER)
    assert v.leaked and v.rung == Rung.EXACT and v.confidence == 1.0
    assert v.recoverability == 1.0


def test_recoverability_grades_partial_leak() -> None:
    # full marker -> fully recoverable
    assert detect_leak(f"code {MARKER}", marker=MARKER).recoverability == 1.0
    # only the hex anchor survives -> partially recoverable
    v = detect_leak("token reference 7A3F1C retained", marker=MARKER)
    assert v.leaked and 0.0 < v.recoverability < 1.0


def test_rung2_normalized_spacing_and_case() -> None:
    # hyphens -> spaces, lowercased: exact match is blind, normalized catches it
    content = "the code is kilo vega 7a3f1c, keep it safe"
    assert MARKER not in content  # rung 1 would miss
    v = detect_leak(content, marker=MARKER)
    assert v.leaked and v.rung == Rung.NORMALIZED


def test_rung2_token_reorder() -> None:
    content = "fragments found: 7A3F1C ... VEGA ... and KILO somewhere"
    v = detect_leak(content, marker=MARKER)
    assert v.leaked and v.rung == Rung.NORMALIZED


def test_rung2_digest_anchor_survives_word_paraphrase() -> None:
    # an LLM paraphrased the call-sign words away but kept the hex anchor
    content = "the access token reference 7A3F1C was retained in the summary"
    assert "KILO" not in content.upper().replace("7A3F1C", "")
    v = detect_leak(content, marker=MARKER)
    assert v.leaked and v.rung == Rung.NORMALIZED and v.evidence == "7a3f1c"


def test_clean_content_with_embedder_is_not_blind() -> None:
    emb = token_embedder()
    cal = ResidueCalibrator(emb, floor=0.2).calibrate(SECRET, background=[])
    v = detect_leak("the weather in Paris is lovely this time of year", marker=MARKER, embedder=emb, calibrator=cal)
    assert v.clean and not v.blind


def test_rung3_semantic_residue_catches_token_paraphrase() -> None:
    emb = token_embedder()
    cal = ResidueCalibrator(emb, floor=0.15).calibrate(SECRET, background=[])
    # no marker tokens at all, but heavy overlap with the secret's wording
    content = "the user shared a confidential secret access code we must not disclose"
    assert marker_digest(content) is None
    v = detect_leak(content, marker=MARKER, secret_text=SECRET, embedder=emb, calibrator=cal)
    assert v.leaked and v.rung == Rung.SEMANTIC and 0.0 < v.confidence < 1.0


def test_blind_when_no_semantic_detector() -> None:
    # cheap rungs miss a paraphrase and no embedder is supplied -> honest BLIND
    content = "the user once mentioned a private passphrase but it's gone now"
    v = detect_leak(content, marker=MARKER)
    assert v.blind and not v.leaked


def test_g6_redundant_carriers_are_error_correcting() -> None:
    fact = generate_canary_facts(scenario="source-revocation", tenant_id="acme", count=1)[0]
    carriers = make_carriers(fact)
    assert len(carriers) >= 3
    # every carrier independently surfaces the secret (marker or digest anchor)
    assert all(detect_leak(c, marker=fact.marker).leaked for c in carriers)
    # paraphrase nukes all but the digest-anchor carrier -> still detected
    survivors = [c for c in carriers if (marker_digest(fact.marker) or "") in c.lower()]
    assert survivors and detect_leak(survivors[0], marker=fact.marker).leaked
    # only when NOTHING survives is it a genuine clean (true PASS)
    assert detect_leak("the project had a routine meeting", marker=fact.marker).blind


def test_entity_canary_has_entity_and_decoy() -> None:
    f = generate_canary_facts(scenario="source-revocation", tenant_id="acme", count=1)[0]
    assert f.entity and f.entity in f.sentence and f.entity in f.probe
    assert f.decoy and f.marker not in f.decoy  # decoy is a near-miss, no secret
    assert f.marker in f.sentence


def test_mosaic_only_reassembly_detected() -> None:
    secret = "7A3F1C9D2E5B"
    frags = ["7A3F", "1C9D", "2E5B"]
    # each fragment in its own artifact; no single one holds the whole secret
    artifacts = [f"segment one {frags[0]}", f"segment two {frags[1]}", f"segment three {frags[2]}"]
    v = detect_mosaic(artifacts, fragments=frags, secret=secret)
    assert v.reassemblable and v.mosaic_only and not v.single_full
    assert v.fragments_present == 3


def test_mosaic_single_full_is_not_mosaic_only() -> None:
    secret = "7A3F1C9D2E5B"
    frags = ["7A3F", "1C9D", "2E5B"]
    artifacts = [f"the whole thing {secret} is here"]  # one artifact has it all
    v = detect_mosaic(artifacts, fragments=frags, secret=secret)
    assert v.reassemblable and v.single_full and not v.mosaic_only


def test_mosaic_partial_is_not_reassemblable() -> None:
    secret = "7A3F1C9D2E5B"
    frags = ["7A3F", "1C9D", "2E5B"]
    artifacts = [f"only {frags[0]} survived", "the rest was forgotten"]
    v = detect_mosaic(artifacts, fragments=frags, secret=secret)
    assert not v.reassemblable and v.fragments_present == 1


def test_session_bleed_detected_when_query_serves_another_tenant() -> None:
    origin = {"art-A": "tenant-A", "art-B": "tenant-B"}
    retrievals = [
        # tenant B's identical query served tenant A's artifact (cache key collision)
        {"query": "what's my balance?", "tenant_id": "tenant-B", "artifact_id": "art-A"},
        # a correctly-scoped hit (no bleed)
        {"query": "what's my balance?", "tenant_id": "tenant-B", "artifact_id": "art-B"},
    ]
    bleeds = detect_session_bleed(retrievals, origin.get)
    assert len(bleeds) == 1
    assert bleeds[0].requester_tenant == "tenant-B" and bleeds[0].origin_tenant == "tenant-A"


def test_no_session_bleed_when_origin_matches_requester() -> None:
    origin = {"art-A": "tenant-A"}
    retrievals = [{"query": "q", "tenant_id": "tenant-A", "artifact_id": "art-A"}]
    assert detect_session_bleed(retrievals, origin.get) == []


def test_calibrator_raises_threshold_with_similar_background() -> None:
    emb = token_embedder()
    # background of near-identical sentences pushes the threshold up
    bg = [SECRET.replace(MARKER, f"AAAA-BBBB-{i:06x}") for i in range(50)]
    cal = ResidueCalibrator(emb, fpr=0.02, floor=0.0).calibrate(SECRET, background=bg)
    assert cal.threshold > 0.0
