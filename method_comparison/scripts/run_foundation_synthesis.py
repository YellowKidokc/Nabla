#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from method_core import call_api, extract_json, now, read_json, sha256_bytes, write_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "config" / "foundation-synthesis-profile.v1.json"
DEFAULT_RUNTIME = ROOT / "config" / "runtime.json"


def parse_source(value: str) -> tuple[str, Path]:
    source_id, separator, raw_path = value.partition("=")
    if not separator or not source_id.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("sources must be SOURCE_ID=PATH")
    return source_id.strip(), Path(raw_path.strip()).resolve()


def build_foundation_packet(sources: list[tuple[str, Path]], profile: dict[str, Any]) -> dict[str, Any]:
    if not sources:
        raise ValueError("at least one source is required")
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    total = 0
    for source_id, path in sources:
        if source_id in seen:
            raise ValueError(f"duplicate source id: {source_id}")
        seen.add(source_id)
        if not path.is_file():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        total += len(text)
        records.append({
            "source_id": source_id,
            "path": str(path),
            "filename": path.name,
            "sha256": sha256_bytes(path.read_bytes()),
            "text": text,
        })
    if total > int(profile["max_source_chars"]):
        raise ValueError(
            f"source packet is {total} characters; profile maximum is {profile['max_source_chars']}. "
            "Use smaller source excerpts or raise the profile limit deliberately."
        )
    material = "\n\n".join(
        f"===== BEGIN SOURCE {row['source_id']} | {row['filename']} | sha256={row['sha256']} =====\n"
        f"{row['text']}\n===== END SOURCE {row['source_id']} ====="
        for row in records
    )
    return {
        "schema_version": "atlas-foundation-packet/v1",
        "packet_id": f"foundation:{sha256_bytes(material.encode('utf-8'))[:16]}",
        "created_at": now(),
        "profile_sha256": sha256_bytes(json.dumps(profile, sort_keys=True).encode("utf-8")),
        "sources": records,
        "material": material,
    }


def foundation_prompt(packet: dict[str, Any], profile: dict[str, Any]) -> str:
    return f"""Build one conservative Consilience Atlas foundational synthesis from the immutable source packet below.

Required lenses: {json.dumps(profile['required_lenses'])}
Required JSON output contract: {json.dumps(profile['output_contract'], ensure_ascii=False)}
Rules: {json.dumps(profile['rules'], ensure_ascii=False)}

Return exactly one JSON object using every top-level key in the output contract. Keep candidate_atoms to at most 12 high-value, separable claims. Keep strings short. A source_ref must include a source_id exactly as named below and an exact quote from that source. Do not cite a source that does not contain the quoted text.

Immutable source packet id: {packet['packet_id']}
---
{packet['material']}
---"""


def validate_result(result: dict[str, Any], profile: dict[str, Any], source_ids: set[str]) -> list[str]:
    errors: list[str] = []
    for key in profile["output_contract"]:
        if key not in result:
            errors.append(f"missing top-level key: {key}")
    for assessment in result.get("lens_assessments", []):
        if assessment.get("lens") not in profile["required_lenses"]:
            errors.append(f"unexpected lens: {assessment.get('lens')}")
        for ref in assessment.get("source_refs", []):
            if ref.get("source_id") not in source_ids or not ref.get("source_quote"):
                errors.append("invalid lens source reference")
    for atom in result.get("candidate_atoms", []):
        if atom.get("standing") != "candidate":
            errors.append(f"atom {atom.get('atom_id')} must remain candidate")
        for ref in atom.get("source_refs", []):
            if ref.get("source_id") not in source_ids or not ref.get("source_quote"):
                errors.append(f"invalid source reference for atom {atom.get('atom_id')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the one-call DeepSeek foundational synthesis.")
    parser.add_argument("--source", action="append", required=True, type=parse_source, metavar="SOURCE_ID=PATH")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--provider", choices=["deepseek"], default="deepseek")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--packet-output", type=Path)
    parser.add_argument("--raw-output", type=Path)
    args = parser.parse_args()

    profile = read_json(args.profile.resolve())
    runtime = read_json(args.runtime.resolve())
    runtime["api"] = dict(runtime["api"])
    runtime["api"]["max_tokens_per_stage"] = int(profile.get("max_output_tokens", runtime["api"]["max_tokens_per_stage"]))
    packet = build_foundation_packet(args.source, profile)
    if args.packet_output:
        write_json(args.packet_output, packet)
    raw, model = call_api(args.provider, foundation_prompt(packet, profile), runtime)
    if args.raw_output:
        args.raw_output.parent.mkdir(parents=True, exist_ok=True)
        args.raw_output.write_text(raw, encoding="utf-8")
    try:
        result = extract_json(raw)
    except Exception as exc:
        receipt = {
            "schema_version": "atlas-foundation-synthesis/v1",
            "created_at": now(),
            "provider": args.provider,
            "model": model,
            "packet_id": packet["packet_id"],
            "packet_sha256": sha256_bytes(json.dumps(packet, sort_keys=True).encode("utf-8")),
            "profile_sha256": packet["profile_sha256"],
            "status": "failed_response_validation",
            "validation_errors": [f"response JSON could not be parsed: {exc}"],
            "result": None,
        }
        write_json(args.output, receipt)
        print(args.output)
        print(f"status={receipt['status']} provider={args.provider} model={model} packet={packet['packet_id']}")
        return 2
    errors = validate_result(result, profile, {source_id for source_id, _ in args.source})
    receipt = {
        "schema_version": "atlas-foundation-synthesis/v1",
        "created_at": now(),
        "provider": args.provider,
        "model": model,
        "packet_id": packet["packet_id"],
        "packet_sha256": sha256_bytes(json.dumps(packet, sort_keys=True).encode("utf-8")),
        "profile_sha256": packet["profile_sha256"],
        "status": "complete" if not errors else "complete_with_validation_errors",
        "validation_errors": errors,
        "result": result,
    }
    write_json(args.output, receipt)
    print(args.output)
    print(f"status={receipt['status']} provider={args.provider} model={model} packet={packet['packet_id']}")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
