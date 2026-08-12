#!/usr/bin/env python3
"""Zero-dependency local server for paper-to-AtlasRecord analysis."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "method_comparison" / "scripts"))

from method_core import build_packet, read_json, run_lane  # noqa: E402
from meta.rails.atlas_api_rails import validate  # noqa: E402
from meta.rails.method_adapter import adapt_method_run  # noqa: E402
from meta.store import AtlasStore  # noqa: E402

CONTRACT = read_json(ROOT / "method_comparison/config/process-contract.v1.json")
RUNTIME = read_json(ROOT / "method_comparison/config/runtime.json")
SCHEMA = ROOT / "meta/schemas/atlas_record.schema.json"
TEMPLATE = ROOT / "templates/atlas-workbench.html"
# Local D1-shaped SQLite mirror; the same db/schema.sql runs against Cloudflare
# D1 in deployment. See docs/d1-architecture.md.
WORKBENCH_DB = ROOT / "meta/_state/workbench.db"


def open_store() -> AtlasStore:
    """Open the local store, one connection per request (SQLite is not shared
    across the server's request threads)."""
    WORKBENCH_DB.parent.mkdir(parents=True, exist_ok=True)
    return AtlasStore(WORKBENCH_DB)


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/records":
            query = parse_qs(parsed.query)
            with open_store() as store:
                records = store.list_records(
                    document_id=(query.get("document_id") or [None])[0],
                    state=(query.get("state") or [None])[0],
                )
            self._json(200, {"records": records}); return
        if parsed.path.startswith("/api/records/"):
            with open_store() as store:
                record = store.get_record(parsed.path[len("/api/records/"):])
            self._json(200, record) if record else self._json(404, {"error": "record not found"})
            return
        if parsed.path not in {"/", "/index.html"}:
            self.send_error(404); return
        body = TEMPLATE.read_bytes()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/records": self._save_record(); return
        if parsed.path != "/api/analyze": self.send_error(404); return
        provider = parse_qs(parsed.query).get("provider", ["local"])[0]
        if provider not in {"local", "deepseek", "openai"}:
            self._json(400, {"error": "unsupported provider"}); return
        size = int(self.headers.get("Content-Length", "0"))
        if size <= 0 or size > 10_000_000:
            self._json(400, {"error": "source must be between 1 byte and 10 MB"}); return
        filename = Path(self.headers.get("X-Filename", "paper.txt")).name
        if Path(filename).suffix.lower() not in {".md", ".txt", ".html", ".htm"}:
            self._json(400, {"error": "only Markdown, TXT, and HTML are accepted"}); return
        inbox = ROOT / ".workbench"; inbox.mkdir(exist_ok=True)
        source = inbox / filename; source.write_bytes(self.rfile.read(size))
        try:
            packet = build_packet(source, CONTRACT)
            lane = "local_nlp" if provider == "local" else "external_api"
            run, _ = run_lane(packet, CONTRACT, RUNTIME, lane, None if lane == "local_nlp" else provider)
            if run["status"] != "complete": self._json(422, {"error": "analysis lane failed", "run": run}); return
            record = adapt_method_run(packet, run)
            errors = validate(record, SCHEMA)
            if errors: self._json(422, {"error": "AtlasRecord validation failed", "validation_errors": errors}); return
            self._json(200, {"record": record, "validation_errors": [], "run_id": run["run_id"]})
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def _save_record(self) -> None:
        """Persist a Candidate AtlasRecord to the local D1-shaped store.

        Durability only: the record's audit state is stored verbatim; saving
        never promotes a Candidate to Admitted.
        """
        size = int(self.headers.get("Content-Length", "0"))
        if size <= 0 or size > 10_000_000:
            self._json(400, {"error": "body must be between 1 byte and 10 MB"}); return
        try:
            body = json.loads(self.rfile.read(size).decode("utf-8"))
            record = body.get("record")
            if not isinstance(record, dict) or "id" not in record:
                self._json(400, {"error": "body.record must be an AtlasRecord object"}); return
            errors = validate(record, SCHEMA)
            if errors:
                self._json(422, {"error": "AtlasRecord validation failed", "validation_errors": errors}); return
            with open_store() as store:
                record_id = store.save_record(
                    record, document_id=body.get("document_id"),
                    run_id=body.get("run_id"), timestamp=str(body.get("timestamp") or ""),
                )
            self._json(200, {"status": "saved", "record_id": record_id})
        except Exception as exc:
            self._json(500, {"error": str(exc)})


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Atlas Workbench: http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
