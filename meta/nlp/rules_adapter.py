from __future__ import annotations

import re
from typing import Any


class RulesAdapter:
    """Deterministic baseline. It proposes candidates and never admits them."""

    def analyze(self, text: str) -> dict[str, Any]:
        parts = re.split(r"(?<=[.!?])\s+|\n{2,}", text.replace("\r\n", "\n"))
        claims = []
        for index, part in enumerate((p.strip() for p in parts), 1):
            words = re.findall(r"\b\w+\b", part)
            if len(words) < 6:
                continue
            claims.append({
                "claim_id": f"rules:claim:{index:04d}",
                "text": part,
                "source_quote": part,
                "standing": "candidate",
                "mode": self._mode(part),
            })
        return {"lane": "rules", "claims": claims, "refusal_state": None}

    @staticmethod
    def _mode(text: str) -> str:
        lower = text.lower()
        if any(token in lower for token in ("theorem", "proof", "lemma", "qed")):
            return "MATHEMATICAL_PROOF"
        if any(token in lower for token in ("equation", "implies", "therefore", "=")):
            return "FORMAL_DERIVATION"
        if any(token in lower for token in ("measured", "observed", "experiment", "dataset")):
            return "EMPIRICAL_EVENT"
        if any(token in lower for token in ("god", "christ", "grace", "theological")):
            return "THEOLOGICAL_CLAIM"
        return "UNKNOWN"
