#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from method_core import compare_runs, read_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare independent NLP and API runs.")
    parser.add_argument("--local-run", type=Path, required=True)
    parser.add_argument("--api-run", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare_runs(
        read_json(args.local_run), read_json(args.api_run),
        read_json(args.contract), read_json(args.runtime),
    )
    write_json(args.output, report)
    print(args.output)
    print(
        f"agreement={report['overall_agreement']:.4f} "
        f"band={report['agreement_band']} "
        f"material_divergences={len(report['material_divergence_stages'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
