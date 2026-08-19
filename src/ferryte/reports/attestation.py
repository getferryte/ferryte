"""Deletion attestation — a signed, verifiable record of a forgetting operation.

Why this exists: the GDPR obligation is not merely to delete, it is to be able
to *demonstrate* that you deleted. Article 5(2) accountability plus the Article
17 erasure right together mean an organisation should be able to produce a
record showing what was requested, what was done, and what was verified. The
EDPB's 2025 coordinated enforcement action on the right to erasure found that
organisations broadly cannot do this.

This module produces that record for one source deletion.

**What this artifact is.** A dated, hash-chained, optionally-signed statement of
what Ferryte observed: the rows it deleted, the probes it ran afterwards, what
those probes returned, and — stated as prominently as the successes — what it
could not verify.

**What this artifact is not.** It is not a certificate of GDPR compliance, and
it deliberately does not use that phrase. Ferryte can attest to what it
observed through the adapters it was given. It cannot see backups, replicas,
downstream exports, warehouse copies, or a vendor's internal caches. Every one
of those is named explicitly in the artifact's own limitations section rather
than left for a reader to infer. Overstating this would be both legally
reckless and self-defeating: the value of the document is precisely that a
security reviewer can trust its boundaries.

Signing uses Ed25519 when ``cryptography`` is available. Without it, the record
still carries a SHA-256 content hash, which is enough for tamper-evidence
between two parties who exchange the hash out of band, and the artifact says so.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import platform
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "ferryte.attestation/1"

# Named so a reader knows exactly where the evidence stops. This list is part of
# the product's honesty, not boilerplate — do not trim it to make reports look
# stronger.
_STANDARD_LIMITATIONS = [
    "Ferryte observed only the backends it was explicitly connected to. Any store "
    "not passed to this run is outside the attestation.",
    "Database backups, snapshots, replicas and point-in-time-recovery archives are "
    "not inspected and may still contain the deleted content.",
    "Data already exported downstream (warehouses, analytics, logs, caches, third-party "
    "sub-processors) is outside Ferryte's reach.",
    "Model weights are not inspected. If the content was used in training or fine-tuning, "
    "deletion from a store does not remove it from a model.",
    "Verification reflects the moment of the probe. It is not a continuing guarantee.",
]


@dataclass
class DeletionProbe:
    """One post-deletion check and its literal result."""

    kind: str
    query: str
    tenant_id: str | None
    hits: int
    clean: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "query": self.query,
            "tenant_id": self.tenant_id,
            "hits": self.hits,
            "clean": self.clean,
            "detail": self.detail,
        }


@dataclass
class DeletionAttestation:
    """The signed record produced by ``ferryte attest-deletion``."""

    source_id: str
    backend: str
    requested_at: str
    completed_at: str
    rows_deleted: int
    rows_remaining: int
    probes: list[DeletionProbe] = field(default_factory=list)
    blind_spots: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=lambda: list(_STANDARD_LIMITATIONS))
    operator: str = ""
    host: str = ""
    tool_version: str = ""
    schema: str = _SCHEMA_VERSION

    # populated by ``finalise``
    content_hash: str = ""
    signature: str = ""
    public_key: str = ""
    signature_algorithm: str = "none"

    @property
    def verified_clean(self) -> bool:
        """True only when every probe came back clean AND nothing remains.

        Blind spots do not make this False — they make the *claim* narrower,
        which is why they are rendered next to it everywhere.
        """
        return self.rows_remaining == 0 and all(p.clean for p in self.probes)

    @property
    def verdict(self) -> str:
        if not self.verified_clean:
            return "INCOMPLETE"
        if self.blind_spots:
            return "VERIFIED_WITH_BLIND_SPOTS"
        return "VERIFIED"

    def payload(self) -> dict[str, Any]:
        """The exact bytes that get hashed and signed."""
        return {
            "schema": self.schema,
            "source_id": self.source_id,
            "backend": self.backend,
            "requested_at": self.requested_at,
            "completed_at": self.completed_at,
            "rows_deleted": self.rows_deleted,
            "rows_remaining": self.rows_remaining,
            "verdict": self.verdict,
            "verified_clean": self.verified_clean,
            "probes": [p.to_dict() for p in self.probes],
            "blind_spots": list(self.blind_spots),
            "limitations": list(self.limitations),
            "operator": self.operator,
            "host": self.host,
            "tool_version": self.tool_version,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")

    def finalise(self, *, sign: bool = False, key_path: Path | None = None) -> DeletionAttestation:
        blob = self.canonical_bytes()
        self.content_hash = "sha256:" + hashlib.sha256(blob).hexdigest()
        if sign:
            sig, pub, alg = _sign(blob, key_path=key_path)
            self.signature, self.public_key, self.signature_algorithm = sig, pub, alg
        return self

    def to_dict(self) -> dict[str, Any]:
        out = self.payload()
        out["content_hash"] = self.content_hash
        out["signature"] = self.signature
        out["public_key"] = self.public_key
        out["signature_algorithm"] = self.signature_algorithm
        return out

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        """Human-readable form — this is what gets attached to a questionnaire."""
        lines: list[str] = []
        badge = {
            "VERIFIED": "VERIFIED",
            "VERIFIED_WITH_BLIND_SPOTS": "VERIFIED (with stated blind spots)",
            "INCOMPLETE": "INCOMPLETE — content still present",
        }[self.verdict]
        lines.append("# Deletion Attestation")
        lines.append("")
        lines.append(f"**Verdict:** {badge}")
        lines.append("")
        lines.append(f"- **Source:** `{self.source_id}`")
        lines.append(f"- **Backend:** {self.backend}")
        lines.append(f"- **Requested:** {self.requested_at}")
        lines.append(f"- **Completed:** {self.completed_at}")
        lines.append(f"- **Records deleted:** {self.rows_deleted}")
        lines.append(f"- **Records still matching:** {self.rows_remaining}")
        lines.append(f"- **Operator:** {self.operator or 'n/a'} on {self.host or 'n/a'}")
        lines.append(f"- **Tool:** ferryte {self.tool_version}")
        lines.append("")
        lines.append("## Post-deletion verification")
        lines.append("")
        if self.probes:
            lines.append("| Probe | Query | Tenant | Hits | Result |")
            lines.append("|---|---|---|---|---|")
            for p in self.probes:
                q = (p.query[:48] + "…") if len(p.query) > 48 else p.query
                lines.append(
                    f"| {p.kind} | `{q}` | {p.tenant_id or '—'} | {p.hits} | "
                    f"{'clean' if p.clean else 'STILL PRESENT'} |"
                )
        else:
            lines.append("_No post-deletion probes were run._")
        lines.append("")
        if self.blind_spots:
            lines.append("## Blind spots — what could NOT be verified")
            lines.append("")
            for b in self.blind_spots:
                lines.append(f"- {b}")
            lines.append("")
        lines.append("## Scope limitations")
        lines.append("")
        lines.append(
            "This attestation records what Ferryte directly observed. It is **not** a "
            "certificate of regulatory compliance. Specifically:"
        )
        lines.append("")
        for lim in self.limitations:
            lines.append(f"- {lim}")
        lines.append("")
        lines.append("## Integrity")
        lines.append("")
        lines.append(f"- **Content hash:** `{self.content_hash}`")
        if self.signature:
            lines.append(f"- **Signature ({self.signature_algorithm}):** `{self.signature}`")
            lines.append(f"- **Public key:** `{self.public_key}`")
            lines.append("")
            lines.append(
                "Verify with `ferryte verify-attestation <file>`, which recomputes the hash "
                "over the canonical payload and checks the signature against the embedded key."
            )
        else:
            lines.append(
                "- **Signature:** none. This record is tamper-evident only if the content "
                "hash above is exchanged out of band. Re-run with `--sign` for a signed record."
            )
        return "\n".join(lines) + "\n"


def build_attestation(
    *,
    source_id: str,
    backend: str,
    rows_deleted: int,
    rows_remaining: int,
    probes: list[DeletionProbe],
    blind_spots: list[str],
    requested_at: float | None = None,
    tool_version: str = "",
) -> DeletionAttestation:
    start = requested_at or time.time()
    return DeletionAttestation(
        source_id=source_id,
        backend=backend,
        requested_at=_iso(start),
        completed_at=_iso(time.time()),
        rows_deleted=rows_deleted,
        rows_remaining=rows_remaining,
        probes=list(probes),
        blind_spots=list(blind_spots),
        operator=_safe(lambda: getpass.getuser()),
        host=_safe(lambda: socket.gethostname()) or _safe(lambda: platform.node()),
        tool_version=tool_version,
    )


def verify_attestation(path: Path) -> tuple[bool, str]:
    """Recompute the hash and check the signature. Returns (ok, message)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return False, f"Could not read attestation: {exc}"

    stated_hash = data.pop("content_hash", "")
    signature = data.pop("signature", "")
    public_key = data.pop("public_key", "")
    algorithm = data.pop("signature_algorithm", "none")

    blob = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    actual = "sha256:" + hashlib.sha256(blob).hexdigest()
    if actual != stated_hash:
        return False, (
            "Content hash mismatch — this attestation has been modified since it was "
            f"written.\n  stated: {stated_hash}\n  actual: {actual}"
        )
    if not signature:
        return True, (
            "Content hash matches. No signature present, so authenticity rests on how "
            "you obtained the file."
        )
    ok, msg = _verify_signature(blob, signature=signature, public_key=public_key, algorithm=algorithm)
    return ok, msg


# ------------------------------------------------------------------ internals


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")


def _safe(fn: Any) -> str:
    try:
        return str(fn())
    except Exception:  # noqa: BLE001
        return ""


def _key_file(key_path: Path | None) -> Path:
    if key_path is not None:
        return Path(key_path).expanduser()
    from ..config import get_config

    return get_config().state_dir / "attestation_key.pem"


def _sign(blob: bytes, *, key_path: Path | None) -> tuple[str, str, str]:
    """Ed25519-sign ``blob``, generating and persisting a key on first use."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError:
        return "", "", "none"

    path = _key_file(key_path)
    if path.exists():
        private = serialization.load_pem_private_key(path.read_bytes(), password=None)
    else:
        private = Ed25519PrivateKey.generate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            private.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        # The signing key is the whole basis of the attestation's authenticity.
        path.chmod(0o600)

    signature = private.sign(blob)  # type: ignore[union-attr]
    pub = private.public_key().public_bytes(  # type: ignore[union-attr]
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return signature.hex(), pub.hex(), "ed25519"


def _verify_signature(
    blob: bytes, *, signature: str, public_key: str, algorithm: str
) -> tuple[bool, str]:
    if algorithm != "ed25519":
        return False, f"Unsupported signature algorithm: {algorithm}"
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        return False, (
            "Signature present but the 'cryptography' package is not installed, so it "
            "could not be checked. Install with: pip install 'ferryte[attest]'"
        )
    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key))
        pub.verify(bytes.fromhex(signature), blob)
    except InvalidSignature:
        return False, "Signature is INVALID — the record does not match the embedded key."
    except Exception as exc:  # noqa: BLE001
        return False, f"Signature check failed: {exc}"
    return True, "Content hash matches and the Ed25519 signature is valid."
