from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ProofTest:
    test_id: str
    claim_id: str
    condition: str
    type: str = "kill_condition"
    status: str = "candidate_untested"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
