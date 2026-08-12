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

CONTRACT = read_json(ROOT / "method_comparison/config/process-contract.v1.json")
RUNTIME = read_json(ROOT / "method_comparison/config/runtime.json")
SCHEMA = ROOT / "meta/schemas/atlas_record.schema.json"
TEMPLATE = ROOT / "templates/atlas-workbench.html"


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path not in {"/", "/index.html"}:
            self.send_error(404); return
        body = TEMPLATE.read_bytes()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
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


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Atlas Workbench: http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
