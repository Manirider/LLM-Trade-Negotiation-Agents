from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.history import HistoryRoundModel
    from models.issue import TradeIssueModel
    from models.negotiator import NegotiatorModel
    from schemas.negotiation import NegotiatorPersona
    from services.ollama import OllamaService


MARKDOWN_FENCE_LINES = 3  # Opening fence, content, closing fence


@dataclass(frozen=True, slots=True)
class ProposalResult:
    text: str
    tokens: int | None
    latency_ms: int


class BaseNegotiator(ABC):
    def __init__(self, model: NegotiatorModel, ollama_service: OllamaService):
        self._model = model
        self._ollama = ollama_service
        self._history: list[HistoryRoundModel] = []

    @property
    def country(self) -> str:
        return self._model.persona.country.value

    @property
    def persona(self) -> NegotiatorPersona:
        return self._model.persona

    @property
    def history(self) -> tuple[HistoryRoundModel, ...]:
        return tuple(self._history)

    def add_to_history(self, round_data: HistoryRoundModel) -> None:
        self._history.append(round_data)

    def clear_history(self) -> None:
        self._history.clear()

    @abstractmethod
    async def propose(self, issue: TradeIssueModel, round_num: int) -> ProposalResult:
        pass

    @abstractmethod
    async def respond(
        self, issue: TradeIssueModel, opponent_proposal: str, round_num: int
    ) -> ProposalResult:
        pass

    def _build_prompt(self, template: str, **kwargs: str) -> str:
        return template.format(**kwargs)

    def _parse_response(self, raw: str) -> str:
        cleaned = raw.strip()
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.split("\n")
            if len(lines) >= MARKDOWN_FENCE_LINES:  # Opening fence, content, closing fence
                cleaned = "\n".join(lines[1:-1])
        return cleaned.split("\n")[0].strip() if "\n" in cleaned else cleaned
