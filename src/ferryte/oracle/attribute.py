"""Answer attribution — the engine behind ``ferryte why``.

The scenarios in this package ask *"did the agent forget?"*. Attribution asks the
inverse, and the more common day-to-day question: *"the agent just said something
wrong — which memory caused it?"*

Given the text of a bad, stale, or leaked answer, we score every memory the agent
holds against that answer and rank the ones most likely to have produced it. Unlike
:func:`ferryte.oracle.detect.detect_leak`, attribution is **marker-free** — it works
on arbitrary real memories, not just planted canaries — because in production nobody
knows the marker in advance; they only have the wrong answer in front of them.

Ranking blends four signals, strongest first:

* **Recorded answer inputs** — if the app called :func:`ferryte.record_answer`
  after the agent's turn, we know *exactly* which memories were in context when
  this answer was produced. That is the retrieval→answer edge; candidates on it
  are anchored, not inferred.
* **Retrieval evidence** — whether the memory was actually pulled into context
  (and whether the retrieving query matches the one being debugged). Retrieval
  is the difference between "plausible" and "live suspect".
* **Content overlap, IDF-weighted** — how much of the memory's text appears in
  the answer, where rare terms count for far more than common ones (a shared
  "7a3f1c" is evidence; a shared "customer" is noise). Contiguous shared spans
  of three or more meaningful tokens add further weight, and the span itself is
  reported as human-readable evidence.
* **Semantic residue** — a pluggable embedder for paraphrase (token-bag by
  default, neural drop-in for true synonym recall).

Each candidate is then traced back through lineage to its source(s) and diagnosed:
a revoked source is a *phantom memory*, a foreign origin tenant is *contamination*,
a soft-deleted artifact retrieved **after** its deletion is a *zombie*, a
supersession edge (or a newer competing memory on the same subject) marks it
*stale*, and an outlier retrieval fan-out across distinct queries — the access
signature of MINJA-style injected records and over-broad summaries — marks it a
*hub memory*.

For confirmation beyond ranking, see :mod:`ferryte.oracle.replay`, which ablates
the suspect from retrieval and shows what the agent's context would have been
without it (retrieval-layer counterfactual, after ContextCite's ablate-and-diff).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

from ..lineage import LineageGraph, get_lineage
from .detect import Embedder, _cosine, _tokens, normalize, token_embedder

# Very common words carry no attribution signal — a memory and an answer sharing
# only "the"/"is" tell us nothing. We ignore these when measuring content overlap
# so generic phrasing can't manufacture a false root cause.
_STOP: frozenset[str] = frozenset(
    """
    a an the this that these those and or but if then else of in on at to from by
    for with without into onto is are was were be been being am do does did done
    have has had having i you he she it we they them us me my your his her its our
    their what which who whom whose when where why how not no yes as so than too
    very can could should would will shall may might must about over under again
    """.split()
)

# Below this many stored memories a full scan is cheaper than the FTS round-trip.
_PREFILTER_THRESHOLD = 512

# Hub-memory (possible poison / over-broad summary) flag: an artifact retrieved
# across at least this many distinct queries AND at 3x the corpus median.
_HUB_MIN_QUERIES = 5

# Score boosts, applied on top of content overlap. Anchor > query-match > retrieval:
# a recorded answer-input edge is direct causal evidence, retrieval is strong
# circumstantial evidence, similarity alone is weakest.
_BOOST_RETRIEVED = 0.12
_BOOST_QUERY_MATCH = 0.15
_BOOST_ANCHORED = 0.30
_SPAN_BONUS = 0.10


def _content_tokens(text: str) -> set[str]:
    """Tokens that actually carry meaning (stopwords + 1-char tokens dropped)."""
    return {t for t in _tokens(text) if t not in _STOP and len(t) > 1}


@dataclass
class MemoryCandidate:
    """One memory ranked as a possible cause of the answer."""

    artifact_id: str
    backend: str
    kind: str
    tenant_id: str | None
    content: str | None
    created_at: float
    deleted_at: float | None
    score: float
    method: str
    retrieved: bool
    retrieval_count: int
    last_retrieved_at: float | None
    sources: list[dict[str, Any]] = field(default_factory=list)
    diagnoses: list[str] = field(default_factory=list)
    # Human-readable proof: shared span text, superseding artifact id, recorded
    # answer id, distinct-query fan-out, ... whatever the signals produced.
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "backend": self.backend,
            "kind": self.kind,
            "tenant_id": self.tenant_id,
            "content": self.content,
            "created_at": self.created_at,
            "deleted_at": self.deleted_at,
            "score": round(self.score, 4),
            "method": self.method,
            "retrieved": self.retrieved,
            "retrieval_count": self.retrieval_count,
            "last_retrieved_at": self.last_retrieved_at,
            "sources": self.sources,
            "diagnoses": self.diagnoses,
            "evidence": self.evidence,
        }


@dataclass
class Attribution:
    """The full result of attributing one answer to the memory behind it."""

    answer: str
    query: str | None
    tenant_id: str | None
    candidates: list[MemoryCandidate] = field(default_factory=list)

    @property
    def top(self) -> MemoryCandidate | None:
        return self.candidates[0] if self.candidates else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "query": self.query,
            "tenant_id": self.tenant_id,
            "candidates": [c.to_dict() for c in self.candidates],
        }


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #
def _idf_weights(artifacts: list[dict[str, Any]], *, corpus_size: int | None = None) -> dict[str, float]:
    """Inverse document frequency over the memory corpus.

    Rare tokens are what make a match evidentiary: two memories sharing "legacy"
    means something when only one memory in five hundred says "legacy"; two
    memories sharing "customer" means nothing. Standard smoothed IDF.
    """
    df: Counter[str] = Counter()
    for art in artifacts:
        for t in _content_tokens(art.get("content") or ""):
            df[t] += 1
    n = max(corpus_size or 0, len(artifacts), 1)
    return {t: math.log1p(n / (0.5 + d)) for t, d in df.items()}


def _weighted_containment(inter: set[str], content_ctokens: set[str], idf: dict[str, float]) -> float:
    """Share of the memory's meaning (IDF mass) that appears in the answer."""
    if not content_ctokens:
        return 0.0
    default = max(idf.values(), default=1.0)
    total = sum(idf.get(t, default) for t in content_ctokens)
    if total <= 0:
        return 0.0
    return sum(idf.get(t, default) for t in inter) / total


def _longest_shared_span(content_tokens: list[str], answer_tokens: list[str]) -> list[str]:
    """Longest contiguous run of tokens the memory and the answer share.

    Contiguity is much stronger evidence than a bag of shared words: "legacy
    free plan" appearing verbatim in both is a quote, not a coincidence.
    """
    if not content_tokens or not answer_tokens:
        return []
    m = SequenceMatcher(None, content_tokens, answer_tokens, autojunk=False).find_longest_match(
        0, len(content_tokens), 0, len(answer_tokens)
    )
    return content_tokens[m.a : m.a + m.size]


def _overlap_score(
    answer_ctokens: set[str],
    answer_tokens_seq: list[str],
    content: str,
    *,
    answer_norm: str,
    embedder: Embedder,
    answer_vec: list[float],
    idf: dict[str, float],
) -> tuple[float, str, dict[str, Any]]:
    """Score how much of ``content`` is present in the answer.

    Returns ``(score in 0..1, method, evidence)`` where method names the
    dominant signal and evidence carries the human-readable proof (e.g. the
    shared span).
    """
    content = content or ""
    content_ctokens = _content_tokens(content)
    if not content_ctokens:
        return 0.0, "none", {}

    norm_content = normalize(content)
    content_tokens_seq = _tokens(content)
    evidence: dict[str, Any] = {}

    # Rung 1/2 — the memory's text (normalized) appears verbatim in the answer.
    # Require a little substance (>= 2 tokens) so trivially short memories don't
    # match everything.
    if norm_content and len(content_tokens_seq) >= 2 and norm_content in answer_norm:
        return 1.0, "exact", {"span": norm_content}

    # IDF-weighted content containment — how much of the memory's *rare* meaning
    # shows up in the answer. Stopword-only overlap scores zero, and common
    # words contribute almost nothing, so generic phrasing can't fabricate a
    # root cause.
    inter = content_ctokens & answer_ctokens
    if not inter:
        return 0.0, "none", {}
    containment = _weighted_containment(inter, content_ctokens, idf)

    # Semantic residue via the injected embedder (token-bag by default; a neural
    # embedder catches true synonym paraphrase with no code change).
    sem = _cosine(answer_vec, list(embedder(content)))

    score = 0.6 * containment + 0.4 * sem

    # Contiguous shared span — quote-level evidence. Three or more meaningful
    # tokens in a row is essentially never coincidence.
    span = _longest_shared_span(content_tokens_seq, answer_tokens_seq)
    span_meaningful = sum(1 for t in span if t not in _STOP and len(t) > 1)
    if span_meaningful >= 2:
        evidence["span"] = " ".join(span)
    has_span_bonus = span_meaningful >= 3
    if has_span_bonus:
        score = min(1.0, score + _SPAN_BONUS)

    if containment >= 0.9:
        return min(1.0, score + 0.1), "normalized", evidence
    if has_span_bonus:
        return score, "span", evidence
    method = "token-overlap" if containment >= sem else "semantic"
    return score, method, evidence


def _norm_answers_match(a: str, b: str) -> bool:
    """Two normalized answer texts refer to the same answer (equal, or one is a
    substantial fragment of the other — users often paste just the wrong part)."""
    if not a or not b:
        return False
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    return len(shorter.split()) >= 3 and shorter in longer


# --------------------------------------------------------------------------- #
# main entry point
# --------------------------------------------------------------------------- #
def attribute_answer(
    answer: str,
    *,
    lineage: LineageGraph | None = None,
    query: str | None = None,
    tenant_id: str | None = None,
    limit: int = 5,
    min_score: float = 0.15,
    embedder: Embedder | None = None,
    since: float | None = None,
    prefilter: bool | None = None,
) -> Attribution:
    """Rank the memories most likely to have caused ``answer``.

    ``query``      the question the agent was answering, if known — used to match
                   retrieval history so an actually-retrieved memory outranks a
                   merely-similar one.
    ``tenant_id``  the tenant/user who saw the answer — enables cross-tenant
                   contamination diagnosis (a memory whose origin tenant differs).
    ``embedder``   pluggable text->vector fn; defaults to the dependency-free
                   token embedder. Pass a neural embedder for paraphrase recall.
    ``since``      unix timestamp: only count retrievals at/after this time
                   (focus the debug on a recent window).
    ``prefilter``  force FTS candidate prefiltering on/off; default auto (on when
                   the corpus exceeds a few hundred memories and FTS is available).
    """
    lin = lineage or get_lineage()
    emb = embedder or token_embedder()

    answer = answer or ""
    answer_ctokens = _content_tokens(answer)
    answer_tokens_seq = _tokens(answer)
    answer_norm = normalize(answer)
    answer_vec = list(emb(answer))

    fingerprinted = bool(getattr(lin.store, "fingerprint_mode", False))
    total_artifacts = lin.counts().get("artifacts", 0)

    # Candidate universe. On large corpora, prefilter by FTS: only memories that
    # share at least one meaningful token with the answer can score > 0, so the
    # full scan is provably redundant. (Fingerprint mode stores hashes, not text —
    # lexical prefiltering and overlap scoring are both degraded there, so scan.)
    use_prefilter = (
        prefilter
        if prefilter is not None
        else (total_artifacts > _PREFILTER_THRESHOLD and not fingerprinted)
    )
    artifacts: list[dict[str, Any]]
    if use_prefilter and answer_ctokens and not fingerprinted:
        ids = lin.candidate_artifact_ids(answer_ctokens)
        artifacts = list(lin.all_artifacts()) if ids is None else lin.artifacts_by_ids(ids)
    else:
        artifacts = list(lin.all_artifacts())

    idf = _idf_weights(artifacts, corpus_size=total_artifacts)

    # Recorded answers — the exact path. If the app recorded this answer (or one
    # containing it), its input memories are anchored candidates: we *know* they
    # were in context when the answer was produced.
    anchored: dict[str, str] = {}  # artifact_id -> answer_id
    answer_fp = lin.store.fingerprint(answer)
    for rec in lin.answers_matching(tenant_id=tenant_id, since=since, limit=100):
        rc = rec.get("content") or ""
        if not rc:
            continue
        matches = rc == answer_fp or (
            not fingerprinted and _norm_answers_match(normalize(rc), answer_norm)
        )
        if matches:
            for aid in lin.artifact_ids_for_answer(rec["answer_id"]):
                anchored.setdefault(aid, rec["answer_id"])

    # Pass 1 — content scoring (no DB access, cheap).
    scored: list[tuple[dict[str, Any], float, str, dict[str, Any]]] = []
    for art in artifacts:
        content = art.get("content") or ""
        base, method, evidence = _overlap_score(
            answer_ctokens,
            answer_tokens_seq,
            content,
            answer_norm=answer_norm,
            embedder=emb,
            answer_vec=answer_vec,
            idf=idf,
        )
        aid = art["artifact_id"]
        if aid in anchored:
            # Direct causal edge: this memory was in context for this answer.
            evidence["recorded_answer_id"] = anchored[aid]
            base = min(1.0, base + _BOOST_ANCHORED)
            method = "recorded-answer"
        elif base <= 0:
            continue
        # Skip candidates that can't reach min_score even with every boost, so
        # pass 2 (per-candidate retrieval lookups) stays small.
        if base + _BOOST_RETRIEVED + _BOOST_QUERY_MATCH < min_score:
            continue
        scored.append((art, base, method, evidence))

    if not scored:
        return Attribution(answer=answer, query=query, tenant_id=tenant_id, candidates=[])

    # Pass 2 — retrieval evidence, lineage trace, diagnosis. Retrievals are
    # fetched per candidate through the artifact index (never a full-table load).
    qcounts = lin.retrieval_query_counts()
    positive = sorted(n for n in qcounts.values() if n > 0)
    median_q = positive[len(positive) // 2] if positive else 0
    q_norm = normalize(query) if query else ""

    sources_cache: dict[str, list[dict[str, Any]]] = {}

    def _sources_of(artifact_id: str) -> list[dict[str, Any]]:
        if artifact_id not in sources_cache:
            sources_cache[artifact_id] = lin.sources_for_artifact(artifact_id)
        return sources_cache[artifact_id]

    candidates: list[MemoryCandidate] = []
    for art, base, method, evidence in scored:
        aid = art["artifact_id"]
        retrievals = lin.retrievals_for_artifact(aid, since=since)
        retrieved = bool(retrievals)

        boost = 0.0
        if retrieved:
            boost += _BOOST_RETRIEVED
            if q_norm and any(q_norm in normalize(str(r.get("query") or "")) for r in retrievals):
                boost += _BOOST_QUERY_MATCH

        score = min(1.0, base + boost)
        if score < min_score:
            continue

        sources = _sources_of(aid)
        diagnoses = _diagnose(
            lineage=lin,
            artifact=art,
            sources=sources,
            retrievals=retrievals,
            viewer_tenant=tenant_id,
            all_artifacts=artifacts,
            answer_tokens=answer_ctokens,
            idf=idf,
            query_fanout=qcounts.get(aid, 0),
            median_fanout=median_q,
            evidence=evidence,
            sources_of=_sources_of,
        )

        last_at = max((r["occurred_at"] for r in retrievals), default=None)
        candidates.append(
            MemoryCandidate(
                artifact_id=aid,
                backend=art["backend"],
                kind=art["kind"],
                tenant_id=art.get("tenant_id"),
                content=(art.get("content") or None),
                created_at=art.get("created_at", 0.0),
                deleted_at=art.get("deleted_at"),
                score=score,
                method=method,
                retrieved=retrieved,
                retrieval_count=len(retrievals),
                last_retrieved_at=last_at,
                sources=sources,
                diagnoses=diagnoses,
                evidence=evidence,
            )
        )

    candidates.sort(key=lambda c: (c.score, c.retrieval_count), reverse=True)
    return Attribution(
        answer=answer,
        query=query,
        tenant_id=tenant_id,
        candidates=candidates[:limit],
    )


# --------------------------------------------------------------------------- #
# diagnosis
# --------------------------------------------------------------------------- #
def _diagnose(
    *,
    lineage: LineageGraph,
    artifact: dict[str, Any],
    sources: list[dict[str, Any]],
    retrievals: list[dict[str, Any]],
    viewer_tenant: str | None,
    all_artifacts: list[dict[str, Any]],
    answer_tokens: set[str],
    idf: dict[str, float],
    query_fanout: int,
    median_fanout: int,
    evidence: dict[str, Any],
    sources_of: Any,
) -> list[str]:
    """Classify *why* this memory is a problem, in the site's taxonomy.

    Structural evidence (revocation, supersession edges, deletion timestamps)
    always outranks inference; the inferential rungs only run when no edge exists.
    """
    out: list[str] = []

    # Phantom memory — its source was revoked but the memory still answers.
    if any(s.get("revoked_at") for s in sources):
        out.append("phantom-memory")

    # Zombie — soft-deleted, yet retrieved *after* the deletion. (A retrieval
    # from before the delete is history, not a bug.)
    deleted_at = artifact.get("deleted_at")
    if deleted_at and any((r.get("occurred_at") or 0.0) > deleted_at for r in retrievals):
        out.append("zombie-memory")

    # Cross-tenant contamination — a memory whose origin tenant differs from the
    # tenant who saw the answer (or from the tenant that retrieved it).
    origin = artifact.get("tenant_id")
    requesters = {r.get("tenant_id") for r in retrievals if r.get("tenant_id")}
    if viewer_tenant and origin and origin != viewer_tenant:
        out.append("cross-tenant")
    elif origin and any(req != origin for req in requesters):
        out.append("cross-tenant")

    # Stale belief, structural rung — a supersession edge says a newer memory
    # replaced this one (bi-temporal invalidation, Zep/Graphiti-style). If this
    # memory still matches the answer, the agent answered from the invalidated fact.
    superseded = lineage.supersessions_for(artifact["artifact_id"])
    if superseded:
        out.append("stale-belief")
        evidence["superseded_by"] = superseded[-1]["new_artifact_id"]
    else:
        # Inferential rung — a *newer* memory on the same subject exists (high
        # IDF-weighted token overlap, later timestamp), so the matched memory is
        # likely an outdated fact still winning retrieval. A newer artifact only
        # counts if it carries information from a source this one doesn't have —
        # a pure re-derivation of the same source (its own summary/copy) is the
        # same belief restated, not a competing newer fact.
        created = artifact.get("created_at") or 0.0
        my_tokens = set(_tokens(artifact.get("content") or "")) & answer_tokens
        if my_tokens:
            default = max(idf.values(), default=1.0)
            my_mass = sum(idf.get(t, default) for t in my_tokens)
            my_sources = {s["source_id"] for s in sources}
            for other in all_artifacts:
                if other["artifact_id"] == artifact["artifact_id"]:
                    continue
                if (other.get("created_at") or 0.0) <= created:
                    continue
                other_tokens = set(_tokens(other.get("content") or ""))
                if not other_tokens:
                    continue
                shared = sum(idf.get(t, default) for t in my_tokens & other_tokens)
                if my_mass <= 0 or shared / my_mass < 0.5:
                    continue
                other_sources = {s["source_id"] for s in sources_of(other["artifact_id"])}
                if other_sources and my_sources and other_sources <= my_sources:
                    continue
                out.append("stale-belief")
                evidence["newer_artifact"] = other["artifact_id"]
                break

    # Hub memory — retrieved across an outlier number of distinct queries. This
    # is the access signature of MINJA-style injected records (engineered to be
    # retrieved for many victim queries) and of over-broad summaries that pollute
    # every context. Deterministic flag from the retrieval trace alone.
    if query_fanout >= _HUB_MIN_QUERIES and query_fanout >= 3 * max(1, median_fanout):
        out.append("hub-memory")
        evidence["distinct_queries"] = query_fanout

    if not out:
        out.append("active-memory")
    return out
