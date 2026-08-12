#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from method_core import read_json, sha256_bytes, write_json

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "process-contract.v1.json"
RUNTIME = ROOT / "config" / "runtime.json"
OUTPUT = ROOT / "output"


def call(arguments: list[str], log: Path) -> None:
    result = subprocess.run(arguments, text=True, capture_output=True, encoding="utf-8", errors="replace")
    log.write_text(
        "$ " + " ".join(arguments) + "\n\nSTDOUT\n" + result.stdout
        + "\nSTDERR\n" + result.stderr,
        encoding="utf-8",
    )
    if result.returncode not in {0, 2}:
        raise RuntimeError(f"Command failed; see {log}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete independent method comparison.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--provider", choices=["deepseek", "openai"], default="deepseek")
    parser.add_argument("--skip-api", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = sha256_bytes(source.read_bytes())[:12]
    run_dir = OUTPUT / f"{stamp}_{digest}"
    run_dir.mkdir(parents=True, exist_ok=False)
    source_copy = run_dir / ("source" + source.suffix.lower())
    shutil.copy2(source, source_copy)

    packet = run_dir / "method-packet.json"
    local_run = run_dir / "local-nlp.run.json"
    api_run = run_dir / "external-api.run.json"
    comparison = run_dir / "comparison.json"
    py = sys.executable
    scripts = Path(__file__).resolve().parent
    call([py, str(scripts / "build_packet.py"), "--source", str(source_copy),
          "--contract", str(CONTRACT), "--output", str(packet)], run_dir / "01-packet.log")
    call([py, str(scripts / "run_lane.py"), "--packet", str(packet),
          "--contract", str(CONTRACT), "--runtime", str(RUNTIME),
          "--lane", "local_nlp", "--output", str(local_run)], run_dir / "02-local.log")

    status = "local_complete"
    if not args.skip_api:
        call([py, str(scripts / "run_lane.py"), "--packet", str(packet),
              "--contract", str(CONTRACT), "--runtime", str(RUNTIME),
              "--lane", "external_api", "--provider", args.provider,
              "--output", str(api_run), "--raw-dir", str(run_dir / "raw-api")],
             run_dir / "03-api.log")
        call([py, str(scripts / "compare_runs.py"), "--local-run", str(local_run),
              "--api-run", str(api_run), "--contract", str(CONTRACT),
              "--runtime", str(RUNTIME), "--output", str(comparison)],
             run_dir / "04-compare.log")
        status = "comparison_complete"

    manifest = {
        "schema_version": "atlas-method-run-manifest/v1",
        "source": str(source),
        "source_copy": str(source_copy),
        "source_sha256": sha256_bytes(source.read_bytes()),
        "provider": None if args.skip_api else args.provider,
        "status": status,
        "packet": str(packet),
        "local_run": str(local_run),
        "api_run": str(api_run) if api_run.exists() else None,
        "comparison": str(comparison) if comparison.exists() else None,
    }
    write_json(run_dir / "manifest.json", manifest)
    print(run_dir)
    print(status)
    if comparison.exists():
        value = read_json(comparison)
        print(f"agreement={value['overall_agreement']} band={value['agreement_band']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
