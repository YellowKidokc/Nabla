from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Edge:
    edge_id: str
    source: str
    target: str
    relation: str
    standing: str = "candidate"
    warrant: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
