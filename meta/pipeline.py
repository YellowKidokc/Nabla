#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from meta.rails.atlas_api_rails import validate
from meta.rails.ingest import DEFAULT_ATOM, DEFAULT_OUT, build_record


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = REPO_ROOT / "meta" / "schemas" / "atlas_record.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate one canonical AtlasRecord from an Atom source.")
    parser.add_argument("--atom", type=Path, default=DEFAULT_ATOM)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-jsonschema", action="store_true")
    args = parser.parse_args()

    record = build_record(args.atom)
    errors = validate(record, None if args.no_jsonschema else SCHEMA)
    if errors:
        print(json.dumps({"status": "refused", "errors": errors}, indent=2))
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "candidate_record_written", "output": str(args.out),
                      "record_id": record["id"]["record_id"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
