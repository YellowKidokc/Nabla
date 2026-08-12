#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from method_core import read_json, run_lane, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one isolated method lane.")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--lane", choices=["local_nlp", "external_api"], required=True)
    parser.add_argument("--provider", choices=["deepseek", "openai"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path)
    args = parser.parse_args()
    run, raw = run_lane(
        read_json(args.packet), read_json(args.contract), read_json(args.runtime),
        args.lane, args.provider,
    )
    write_json(args.output, run)
    if args.raw_dir:
        args.raw_dir.mkdir(parents=True, exist_ok=True)
        for stage_id, value in raw.items():
            (args.raw_dir / f"{stage_id}.raw.txt").write_text(value, encoding="utf-8")
    print(args.output)
    print(f"lane={run['lane']} backend={run['backend']} status={run['status']}")
    return 0 if run["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
