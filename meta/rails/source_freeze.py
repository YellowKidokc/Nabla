from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def freeze(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "schema_version": "document-packet/v1",
        "source": {"filename": path.name, "path": str(path.resolve()),
                   "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                   "text": raw.decode("utf-8", errors="replace")},
        "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
