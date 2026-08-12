from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Component:
    component_id: str
    type: str
    content: Any
    label: str = ""
    standing: str = "candidate"
    source_span_ids: tuple[str, ...] = ()
    meta_criteria_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
