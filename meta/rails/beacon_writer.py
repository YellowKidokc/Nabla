from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_beacon(path: Path, payload: dict[str, Any]) -> Path:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    receipt = {"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(), "payload": payload}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
