#!/usr/bin/env python3
"""Local HTTP bridge for the Consilience Atlas Workbench.

This server intentionally owns orchestration only. It does not classify claims or
compute epistemic grades itself. It delegates semantic work to the existing
method-comparison lanes and returns their receipts to the GUI.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
GUI_DIST = REPO_ROOT / "gui" / "dist"
GUI_PUBLIC = REPO_ROOT / "gui"
METHOD_RUNNER = REPO_ROOT / "method_comparison" / "scripts" / "run_comparison.py"
METHOD_OUTPUT = REPO_ROOT / "method_comparison" / "output"
GOLD_MASTER = REPO_ROOT / "gold" / "master-equation" / "atlas-record-v1.master-equation.trilemma.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_suffix(name: str) -> str:
    suffix = Path(name).suffix.lower()
    return suffix if suffix in {".md", ".txt", ".html", ".htm", ".json"} else ".txt"


def newest_run(before: set[Path]) -> Path | None:
    current = {p for p in METHOD_OUTPUT.glob("*") if p.is_dir()}
    created = current - before
    if created:
        return max(created, key=lambda p: p.stat().st_mtime)
    return None


def run_analysis(filename: str, text: str, provider: str, local_only: bool) -> dict[str, Any]:
    if provider not in {"deepseek", "openai"}:
        raise ValueError("provider must be deepseek or openai")
    if not text.strip():
        raise ValueError("document text is empty")

    METHOD_OUTPUT.mkdir(parents=True, exist_ok=True)
    before = {p for p in METHOD_OUTPUT.glob("*") if p.is_dir()}
    with tempfile.TemporaryDirectory(prefix="atlas-workbench-") as tmp:
        source = Path(tmp) / (Path(filename).stem[:80] + safe_suffix(filename))
        source.write_text(text, encoding="utf-8")
        cmd = [sys.executable, str(METHOD_RUNNER), "--source", str(source), "--provider", provider]
        if local_only:
            cmd.append("--skip-api")
        result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")

    run_dir = newest_run(before)
    if result.returncode != 0 or run_dir is None:
        raise RuntimeError((result.stderr or result.stdout or "analysis failed")[-8000:])

    manifest_path = run_dir / "manifest.json"
    manifest = read_json(manifest_path)
    payload: dict[str, Any] = {
        "status": manifest.get("status"),
        "run_dir": str(run_dir.relative_to(REPO_ROOT)).replace("\\", "/"),
        "manifest": manifest,
        "local_run": read_json(run_dir / "local-nlp.run.json") if (run_dir / "local-nlp.run.json").exists() else None,
        "api_run": read_json(run_dir / "external-api.run.json") if (run_dir / "external-api.run.json").exists() else None,
        "comparison": read_json(run_dir / "comparison.json") if (run_dir / "comparison.json").exists() else None,
        "stdout": result.stdout[-4000:],
    }
    return payload


class Handler(BaseHTTPRequestHandler):
    server_version = "AtlasWorkbench/0.1"

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._json(HTTPStatus.NO_CONTENT, {})

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(HTTPStatus.OK, {
                "status": "ok",
                "service": "atlas-workbench",
                "method_runner": METHOD_RUNNER.exists(),
                "gold_master_equation": GOLD_MASTER.exists(),
            })
            return
        if path == "/api/gold/master-equation":
            if not GOLD_MASTER.exists():
                self._json(HTTPStatus.NOT_FOUND, {"error": "gold specimen not found"})
            else:
                self._json(HTTPStatus.OK, read_json(GOLD_MASTER))
            return
        self._serve_static(path)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/analyze":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            payload = run_analysis(
                filename=str(body.get("filename") or "document.md"),
                text=str(body.get("text") or ""),
                provider=str(body.get("provider") or "deepseek"),
                local_only=bool(body.get("local_only", False)),
            )
            self._json(HTTPStatus.OK, payload)
        except Exception as exc:  # keep UI receipt explicit
            self._json(HTTPStatus.BAD_REQUEST, {"status": "refused", "error": str(exc)})

    def _serve_static(self, path: str) -> None:
        root = GUI_DIST if (GUI_DIST / "index.html").exists() else GUI_PUBLIC
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        target = (root / relative).resolve()
        if root.resolve() not in target.parents and target != root.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not target.exists() or target.is_dir():
            target = root / "index.html"
        if not target.exists():
            self._json(HTTPStatus.NOT_FOUND, {"error": "GUI not built; run npm install && npm run dev in gui/"})
            return
        body = target.read_bytes()
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        print("[workbench] " + (fmt % args))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local Consilience Atlas Workbench bridge.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Atlas Workbench API: http://{args.host}:{args.port}")
    print("React dev UI:       http://localhost:5173")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
