from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from models.history import HistoryRoundModel
    from models.issue import TradeIssueModel

from schemas.negotiation import HistoryRound, LogEntry


@dataclass(frozen=True, slots=True)
class NegotiationState:
    issue: TradeIssueModel
    rounds: int
    current_round: int = 0
    history: tuple[HistoryRoundModel, ...] = field(default_factory=tuple)
    agreement_reached: bool = False
    final_score: float | None = None
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    model: str = ""

    def add_round(self, round_data: HistoryRoundModel) -> NegotiationState:
        return NegotiationState(
            issue=self.issue,
            rounds=self.rounds,
            current_round=self.current_round + 1,
            history=(*self.history, round_data),
            agreement_reached=self.agreement_reached,
            final_score=self.final_score,
            start_time=self.start_time,
            model=self.model,
        )

    def set_agreement(self, score: float) -> NegotiationState:
        return NegotiationState(
            issue=self.issue,
            rounds=self.rounds,
            current_round=self.current_round,
            history=self.history,
            agreement_reached=True,
            final_score=score,
            start_time=self.start_time,
            model=self.model,
        )

    def to_log_entry(self, request: dict[str, Any], execution_time_ms: int) -> LogEntry:
        history_schema = [
            HistoryRound(
                round=h.round,
                timestamp=h.timestamp,
                usa_proposal=h.usa_proposal,
                china_response=h.china_response,
                tokens=h.tokens,
                latency_ms=h.latency_ms,
            )
            for h in self.history
        ]
        return LogEntry(
            request=request,
            history=history_schema,
            score=self.final_score or 0.0,
            agreement=self.agreement_reached,
            execution_time_ms=execution_time_ms,
            model=self.model,
        )

    @property
    def is_complete(self) -> bool:
        return self.current_round >= self.rounds or self.agreement_reached


class StateManager:
    def __init__(self) -> None:
        self._states: dict[str, NegotiationState] = {}

    def create_state(
        self,
        negotiation_id: str,
        issue: TradeIssueModel,
        rounds: int,
        model: str,
    ) -> NegotiationState:
        state = NegotiationState(issue=issue, rounds=rounds, model=model)
        self._states[negotiation_id] = state
        return state

    def get_state(self, negotiation_id: str) -> NegotiationState | None:
        return self._states.get(negotiation_id)

    def update_state(self, negotiation_id: str, state: NegotiationState) -> NegotiationState:
        self._states[negotiation_id] = state
        return state

    def delete_state(self, negotiation_id: str) -> None:
        self._states.pop(negotiation_id, None)

    def clear(self) -> None:
        self._states.clear()


STATE_MANAGER: Final[StateManager] = StateManager()
