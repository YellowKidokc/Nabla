from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    claim_id: str
    statement: str
    relation: str = "supports"
    strength: str = "UNKNOWN"
    independent: bool = False
    source: str = ""
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
