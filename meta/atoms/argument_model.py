from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Argument:
    argument_id: str
    conclusion_id: str
    premise_ids: tuple[str, ...] = ()
    warrant: str = ""
    status: str = "candidate"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
