"""J3 — privacy-preserving lineage: the local DB must never persist raw content."""

from __future__ import annotations

from ferryte.lineage.store import LineageStore

SECRET = "KILO-VEGA-7A3F1C the patient SSN is 078-05-1120"


def _store(tmp_path, **kw) -> LineageStore:
    return LineageStore(tmp_path / "lineage.db", **kw)


def test_fingerprint_mode_never_stores_raw_content(tmp_path) -> None:
    s = _store(tmp_path, fingerprint_mode=True, fingerprint_salt="test-salt")
    s.record_artifact(artifact_id="a1", backend="vector", kind="raw", content=SECRET, tenant_id="acme")
    s.record_retrieval(
        backend="vector", query=SECRET, artifact_id="a1", content=SECRET, score=1.0, tenant_id="acme"
    )
    arts = list(s.all_artifacts())
    assert arts[0]["content"].startswith("fp:sha256:")
    assert SECRET not in arts[0]["content"]
    rets = s.retrievals_matching()
    assert rets[0]["content"].startswith("fp:sha256:") and SECRET not in rets[0]["content"]
    # the query is sensitive too — it must also be fingerprinted
    assert rets[0]["query"].startswith("fp:sha256:") and "078-05-1120" not in rets[0]["query"]
    s.close()


def test_plain_mode_keeps_raw_content(tmp_path) -> None:
    s = _store(tmp_path, fingerprint_mode=False)
    s.record_artifact(artifact_id="a1", backend="vector", kind="raw", content=SECRET)
    assert list(s.all_artifacts())[0]["content"] == SECRET
    s.close()


def test_fingerprint_is_deterministic_per_salt_and_differs_across_salts(tmp_path) -> None:
    s1 = _store(tmp_path / "a", fingerprint_mode=True, fingerprint_salt="salt-A")
    s2 = _store(tmp_path / "b", fingerprint_mode=True, fingerprint_salt="salt-A")
    s3 = _store(tmp_path / "c", fingerprint_mode=True, fingerprint_salt="salt-B")
    for s in (s1, s2, s3):
        s.record_artifact(artifact_id="a1", backend="vector", kind="raw", content=SECRET)
    fp1 = list(s1.all_artifacts())[0]["content"]
    fp2 = list(s2.all_artifacts())[0]["content"]
    fp3 = list(s3.all_artifacts())[0]["content"]
    assert fp1 == fp2  # same salt -> same fingerprint (correlatable within a deployment)
    assert fp1 != fp3  # different salt -> different fingerprint (no cross-deployment linkage)
    for s in (s1, s2, s3):
        s.close()
