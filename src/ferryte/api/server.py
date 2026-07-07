"""Local HTTP API the Next.js dashboard reads from.

We keep FastAPI as an optional dependency (``pip install ferryte-test[api]``).
The endpoints are minimal and read-only on purpose: the dashboard is a
read-only window onto the local lineage DB and the latest reports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import __version__
from ..config import get_config
from ..lineage import compute_blast_radius, get_lineage


def build_app() -> Any:
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
    except Exception as exc:  # pragma: no cover - optional dep
        raise RuntimeError(
            "FastAPI is not installed. Install with `pip install ferryte-test[api]`."
        ) from exc

    app = FastAPI(title="Ferryte", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"status": "ok"}

    @app.get("/api/lineage/sources")
    def list_sources(tenant_id: str | None = None) -> dict[str, Any]:
        lineage = get_lineage()
        return {"sources": lineage.sources(tenant_id=tenant_id)}

    @app.get("/api/lineage/sources/{source_id}/blast")
    def source_blast(source_id: str) -> dict[str, Any]:
        lineage = get_lineage()
        return compute_blast_radius(lineage, source_id=source_id).to_dict()

    @app.get("/api/lineage/counts")
    def counts() -> dict[str, int]:
        return get_lineage().counts()

    @app.get("/api/lineage/blindspots")
    def blindspots() -> dict[str, Any]:
        return {"blindspots": get_lineage().blindspots()}

    @app.get("/api/lineage/artifacts")
    def artifacts(limit: int = 100) -> dict[str, Any]:
        lineage = get_lineage()
        out: list[dict[str, Any]] = []
        for i, art in enumerate(lineage.all_artifacts()):
            if i >= limit:
                break
            out.append(art)
        return {"artifacts": out}

    @app.get("/api/why")
    def why(
        answer: str,
        query: str | None = None,
        tenant_id: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Attribution over the local lineage DB — the dashboard's `why` view."""
        from ..oracle.attribute import attribute_answer

        result = attribute_answer(
            answer, lineage=get_lineage(), query=query, tenant_id=tenant_id, limit=limit
        )
        return result.to_dict()

    @app.get("/api/reports/latest")
    def latest_report() -> dict[str, Any]:
        cfg = get_config()
        path = cfg.state_dir / "reports" / "latest.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="no report yet — run `ferryte test` first")
        return json.loads(path.read_text(encoding="utf-8"))

    return app


def serve(*, host: str = "127.0.0.1", port: int = 8787) -> None:
    try:
        import uvicorn
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "uvicorn is not installed. Install with `pip install ferryte-test[api]`."
        ) from exc
    uvicorn.run(build_app(), host=host, port=port)


def latest_report_path() -> Path:
    return get_config().state_dir / "reports" / "latest.json"
