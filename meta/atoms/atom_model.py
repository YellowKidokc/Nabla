from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .argument_model import Argument
from .claim_model import Claim
from .component_model import Component
from .proof_model import ProofTest


@dataclass(frozen=True)
class Atom:
    atom_id: str
    label: str
    lifecycle: str = "candidate"
    native_grade: str = "NOT_ESTABLISHED"


@dataclass
class AtomStack:
    atom: Atom
    components: list[Component] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    tests: list[ProofTest] = field(default_factory=list)
    arguments: list[Argument] = field(default_factory=list)
    upstream: list[str] = field(default_factory=list)
    downstream: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
