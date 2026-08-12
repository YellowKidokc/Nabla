from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    mode: str = "UNKNOWN"
    mode_native: str = ""
    standing: str = "candidate"
    source_span_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
