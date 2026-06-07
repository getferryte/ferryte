"""Functional-forgetting detection ladder (paraphrase-proof leak detection).

The original oracle detected a leak with a single test: is the high-entropy
marker present as an *exact substring*? That honestly reports ``BLIND`` the
moment an LLM paraphrases or summarises the secret — the *information* survives
but the *literal token* is gone, so an exact match can't see it.

This module replaces that one test with a **cheap → expensive ladder** that
escalates only when a cheaper rung can't decide:

  Rung 1 — EXACT       verbatim marker substring (fast, zero-FP).
  Rung 2 — NORMALIZED  case / hyphen / spacing / token-reorder folding, plus the
                       high-entropy digest anchor — catches "kilo vega 7a3f1c",
                       "Vega/Kilo (7A3F1C)", etc. Still zero model dependency.
  Rung 3 — SEMANTIC    lineage-targeted *semantic residue*: embed the suspect
                       artifact and compare to the secret; fire only on a
                       statistical outlier against a **null distribution** of
                       unrelated memories, at a chosen false-positive rate.
  Rung 4 — BEHAVIORAL  ask the agent a question only the secret answers and let
                       an LLM-judge (holding the answer key) rule. Interface only
                       here — the judge spend lives in Cloud (see ``Rung4Probe``).

Design rules:
  * Cheaper rungs win first; we only climb when the current rung is inconclusive.
  * Rungs 1–2 are deterministic and dependency-free (ship in Core).
  * Rung 3 takes a *pluggable* embedder; with the built-in token embedder it
    catches token-overlap paraphrase, with a neural embedder injected it catches
    true synonym paraphrase. No rung 3 verdict is a hard FAIL unless confidence
    is high — a suspected residue is a WARN, never silent.
  * "Can't tell" is reported as BLIND, never as a clean PASS.
"""

from __future__ import annotations

import enum
import hashlib
import math
import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

# An embedder maps text -> a fixed-length vector. Injected so Core stays
# dependency-free; tests and the benchmark can pass a neural one.
Embedder = Callable[[str], Sequence[float]]

_TOKEN_RE = re.compile(r"[a-z0-9]+")
# the 6-hex digest tail of a marker (KILO-VEGA-7A3F1C) is the high-entropy anchor
_DIGEST_RE = re.compile(r"\b[0-9a-f]{6}\b")


class Rung(str, enum.Enum):
    EXACT = "exact"
    NORMALIZED = "normalized"
    SEMANTIC = "semantic_residue"
    BEHAVIORAL = "behavioral"


@dataclass(frozen=True)
class LeakVerdict:
    """Outcome of running the ladder on one (content, secret) pair.

    ``leaked`` True  => we found the secret (see ``rung`` / ``confidence``).
    ``blind``  True  => we could not decide (no rung could confirm or clear it);
                        callers must surface this as BLIND, not PASS.
    ``leaked``/``blind`` both False => clean (the secret is genuinely absent).
    """

    leaked: bool
    blind: bool = False
    rung: Rung | None = None
    confidence: float = 0.0  # 0..1; 1.0 for deterministic rungs 1–2
    score: float | None = None  # raw similarity for rung 3, for debugging
    evidence: str = ""
    # J4: graded recoverability 0..1 — *how much* of the original secret this
    # surviving artifact still lets you reconstruct (not just a yes/no leak).
    # 1.0 = the secret is fully present; lower = only partially recoverable.
    recoverability: float = 0.0

    @property
    def clean(self) -> bool:
        return not self.leaked and not self.blind


# --------------------------------------------------------------------------- #
# normalization helpers (Rungs 1–2, deterministic, dependency-free)
# --------------------------------------------------------------------------- #
def normalize(text: str) -> str:
    """Lowercase, collapse any non-alphanumeric run to a single space."""
    return " ".join(_TOKEN_RE.findall((text or "").lower()))


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def marker_parts(marker: str) -> list[str]:
    """The component tokens of a canary marker (e.g. KILO-VEGA-7A3F1C ->
    ['kilo', 'vega', '7a3f1c'])."""
    return _tokens(marker)


def marker_digest(marker: str) -> str | None:
    """The high-entropy hex anchor of a marker, if present. This is the part an
    LLM is least able to 'paraphrase' into something else while keeping meaning."""
    for tok in reversed(marker_parts(marker)):
        if _DIGEST_RE.fullmatch(tok):
            return tok
    return None


# --------------------------------------------------------------------------- #
# Rung 3 calibration: a null distribution of "unrelated memory" similarities,
# so we fire on a statistical outlier at a chosen false-positive rate rather
# than an arbitrary cosine threshold.
# --------------------------------------------------------------------------- #
@dataclass
class ResidueCalibrator:
    """Builds a similarity threshold from unrelated (decoy/background) memories.

    Fire Rung 3 only when a suspect artifact's similarity to the secret exceeds
    what we'd expect from unrelated memory at the chosen ``fpr``.
    """

    embedder: Embedder
    fpr: float = 0.001  # 0.1% false-positive rate
    floor: float = 0.30  # never fire below this absolute similarity
    _threshold: float = field(default=0.0, init=False)
    _calibrated: bool = field(default=False, init=False)

    def calibrate(self, secret_text: str, background: Iterable[str]) -> ResidueCalibrator:
        sv = self.embedder(secret_text)
        sims = sorted((_cosine(sv, self.embedder(b)) for b in background), reverse=True)
        if sims:
            # threshold = the (fpr)-quantile from the top of the null distribution
            k = max(0, min(len(sims) - 1, int(self.fpr * len(sims))))
            self._threshold = max(self.floor, sims[k])
        else:
            self._threshold = self.floor
        self._calibrated = True
        return self

    @property
    def threshold(self) -> float:
        return self._threshold if self._calibrated else self.floor


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return num / (na * nb)


def token_embedder(dim: int = 256) -> Embedder:
    """Deterministic hash-bag-of-tokens embedder (no model dependency).

    Captures token overlap (so a paraphrase that keeps some of the secret's
    words is still flagged). Inject a neural embedder for true synonym
    paraphrase resistance; the ladder is identical either way.
    """

    def _embed(text: str) -> list[float]:
        vec = [0.0] * dim
        for tok in _tokens(text):
            h = int(hashlib.sha1(tok.encode("utf-8")).hexdigest(), 16)
            vec[h % dim] += 1.0
        return vec

    return _embed


# --------------------------------------------------------------------------- #
# Rung 4 interface (behavioral probe + LLM judge). Implemented in Cloud; here we
# only define the seam so scenarios can opt in when a judge is provided.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MosaicVerdict:
    """J1 — outcome of a triangulation/mosaic check across many artifacts.

    ``reassemblable`` : every fragment of the secret survives *somewhere* in the
                        artifact set, so the whole secret can be reconstructed.
    ``single_full``   : some single artifact already contains the whole secret
                        (then it's a plain leak, not a mosaic).
    ``mosaic_only``   : reassemblable AND no single artifact leaked it — the
                        dangerous case a per-artifact detector misses.
    """

    reassemblable: bool
    single_full: bool
    fragments_present: int
    fragments_total: int

    @property
    def mosaic_only(self) -> bool:
        return self.reassemblable and not self.single_full


def detect_mosaic(
    artifacts: Iterable[str], *, fragments: Sequence[str], secret: str
) -> MosaicVerdict:
    """Can the secret be triangulated from fragments spread across artifacts?

    No single fragment is the secret, so a per-artifact leak check clears each
    one — but if every fragment survives somewhere, an attacker (or the agent)
    can concatenate them back into the secret. That recombination is the leak.
    """
    blobs = [normalize(a) for a in artifacts]
    union = " ".join(blobs)
    norm_secret = normalize(secret)
    norm_frags = [normalize(f) for f in fragments]
    single_full = any(norm_secret and norm_secret in b for b in blobs)
    present = sum(1 for f in norm_frags if f and f in union)
    reassemblable = present == len(norm_frags) and len(norm_frags) > 0
    return MosaicVerdict(
        reassemblable=reassemblable,
        single_full=single_full,
        fragments_present=present,
        fragments_total=len(norm_frags),
    )


@dataclass(frozen=True)
class SessionBleed:
    query: str
    requester_tenant: str
    origin_tenant: str
    artifact_id: str


def detect_session_bleed(
    retrievals: Iterable[dict], origin_tenant_of: Callable[[str], str | None]
) -> list[SessionBleed]:
    """J5 — detect cache/session bleed in the plumbing layer.

    The 2023 ChatGPT incident wasn't a memory-backend bug: a request cache keyed
    by query (not by user/session) served one user's data to another. Ferryte
    already captures every retrieval with its requesting tenant; cross-referencing
    each served artifact against the tenant that *originally wrote* it surfaces the
    bleed — a served result whose origin tenant differs from the requester, which
    is exactly the signature of a mis-keyed shared cache.

    ``origin_tenant_of(artifact_id)`` resolves who wrote an artifact (from lineage).
    """
    out: list[SessionBleed] = []
    for r in retrievals:
        requester = r.get("tenant_id")
        aid = r.get("artifact_id")
        if not aid or requester is None:
            continue
        origin = origin_tenant_of(aid)
        if origin is not None and origin != requester:
            out.append(
                SessionBleed(
                    query=str(r.get("query") or ""),
                    requester_tenant=str(requester),
                    origin_tenant=str(origin),
                    artifact_id=str(aid),
                )
            )
    return out


class Rung4Probe:
    """Pluggable behavioral judge: given the agent's answer to a probe question
    and the secret answer key, decide whether the answer functionally reveals the
    secret. Returns (revealed: bool, confidence: float). Core ships no judge."""

    def judge(self, *, answer: str, secret: str, probe: str) -> tuple[bool, float]:  # noqa: D401
        raise NotImplementedError("Rung 4 (LLM-judge) is a Cloud capability.")


# --------------------------------------------------------------------------- #
# the ladder
# --------------------------------------------------------------------------- #
def detect_leak(
    content: str,
    *,
    marker: str,
    secret_text: str | None = None,
    embedder: Embedder | None = None,
    calibrator: ResidueCalibrator | None = None,
) -> LeakVerdict:
    """Run the detection ladder on one retrieved/derived ``content`` blob.

    ``marker``      the canary's high-entropy marker (e.g. ``KILO-VEGA-7A3F1C``).
    ``secret_text`` the full secret sentence (used by Rung 3 semantic residue);
                    defaults to the marker if not given.
    ``embedder``    enables Rung 3 when provided (with ``calibrator`` for the
                    null-distribution threshold). If absent, Rung 3 is skipped.
    """
    content = content or ""

    # Rung 1 — exact substring (fast, zero-FP). Fully recoverable.
    if marker and marker in content:
        return LeakVerdict(
            leaked=True, rung=Rung.EXACT, confidence=1.0, recoverability=1.0, evidence=marker
        )

    # Rung 2 — normalized / reordered / digest-anchor (deterministic).
    norm_content = normalize(content)
    parts = marker_parts(marker)
    digest = marker_digest(marker)
    if parts:
        norm_marker = " ".join(parts)
        if norm_marker and norm_marker in norm_content:
            return LeakVerdict(
                leaked=True, rung=Rung.NORMALIZED, confidence=1.0, recoverability=1.0,
                evidence=norm_marker,
            )
        content_tokens = set(_tokens(content))
        # all components present (any order) — catches token reordering / respacing
        if all(p in content_tokens for p in parts):
            return LeakVerdict(
                leaked=True, rung=Rung.NORMALIZED, confidence=0.98, recoverability=0.95,
                evidence=" ".join(parts),
            )
        # the high-entropy digest alone is a strong anchor (6 hex chars ~ 16M space)
        if digest and digest in content_tokens:
            # only the anchor survives — the secret is identifiable but only
            # partially reconstructable from this artifact alone
            return LeakVerdict(
                leaked=True, rung=Rung.NORMALIZED, confidence=0.9, recoverability=0.6,
                evidence=digest,
            )

    # Rung 3 — lineage-targeted semantic residue (needs an embedder).
    if embedder is not None:
        secret = secret_text or marker
        sim = _cosine(embedder(secret), embedder(content))
        threshold = calibrator.threshold if calibrator is not None else 0.30
        if sim >= threshold:
            # suspected functional residue — confidence scales with how far over
            conf = min(0.85, 0.5 + (sim - threshold))
            return LeakVerdict(
                leaked=True,
                rung=Rung.SEMANTIC,
                confidence=conf,
                recoverability=round(sim, 3),  # similarity ~ how much is recoverable
                score=sim,
                evidence=f"semantic residue sim={sim:.3f} >= thr={threshold:.3f}",
            )
        # embedder ran and the content is clearly unrelated -> genuinely clean
        return LeakVerdict(leaked=False, score=sim, recoverability=round(sim, 3))

    # No semantic rung available and the cheap rungs didn't fire: we cannot rule
    # out a paraphrase. Honest BLIND, never a silent PASS.
    return LeakVerdict(leaked=False, blind=True, evidence="no semantic detector; paraphrase unchecked")
