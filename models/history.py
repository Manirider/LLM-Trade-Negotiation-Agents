from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class HistoryRoundModel:
    round: int
    timestamp: datetime
    usa_proposal: str
    china_response: str
    tokens: int | None
    latency_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "timestamp": self.timestamp.isoformat(),
            "usa_proposal": self.usa_proposal,
            "china_response": self.china_response,
            "tokens": self.tokens,
            "latency_ms": self.latency_ms,
        }

    @classmethod
    def create(
        cls,
        round_num: int,
        usa_proposal: str,
        china_response: str,
        latency_ms: int,
        tokens: int | None = None,
    ) -> HistoryRoundModel:
        return cls(
            round=round_num,
            timestamp=datetime.now(UTC),
            usa_proposal=usa_proposal,
            china_response=china_response,
            tokens=tokens,
            latency_ms=latency_ms,
        )
