from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from meta.atlas.atlas_record import validate_record


def validate(record: dict[str, Any], schema_path: Path | None = None) -> list[str]:
    errors = validate_record(record)
    if schema_path:
        try:
            import jsonschema
        except ImportError:
            return errors
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(record, schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"schema: {exc.message}")
    return errors


def admission_state(errors: list[str], unresolved: list[Any]) -> str:
    if errors:
        return "Refused"
    return "Candidate" if unresolved else "Admitted"
