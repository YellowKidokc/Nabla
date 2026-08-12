#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from method_core import build_packet, read_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an immutable Atlas method packet.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packet = build_packet(args.source.resolve(), read_json(args.contract))
    write_json(args.output, packet)
    print(args.output)
    print(f"packet={packet['packet_id']} source_sha256={packet['source']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
