from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.base import BaseNegotiator, ProposalResult
from core.prompts import USA_PROPOSE_PROMPT, USA_RESPOND_PROMPT
from models.negotiator import NegotiatorModel, get_usa_persona

if TYPE_CHECKING:
    from models.issue import TradeIssueModel
    from schemas.negotiation import NegotiatorPersona
    from services.ollama import OllamaService


@dataclass(frozen=True, slots=True)
class USANegotiatorConfig:
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 150
    persona: NegotiatorPersona | None = None


class USANegotiator(BaseNegotiator):
    def __init__(
        self,
        ollama_service: OllamaService,
        config: USANegotiatorConfig | None = None,
    ):
        cfg = config or USANegotiatorConfig()
        persona = cfg.persona or get_usa_persona()
        system_prompt = self._build_system_prompt(persona)
        model = NegotiatorModel(
            persona=persona,
            system_prompt=system_prompt,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            max_tokens=cfg.max_tokens,
        )
        super().__init__(model, ollama_service)

    @staticmethod
    def _build_system_prompt(persona: NegotiatorPersona | None = None) -> str:
        p = persona or get_usa_persona()
        return (
            f"You are {p.role}. "
            f"Your priorities: {', '.join(p.priorities)}. "
            f"Your red lines: {', '.join(p.red_lines)}. "
            f"Your strategy: {p.strategy}. "
            f"Flexibility: {p.flexibility:.0%}. "
            "Rules: Never hallucinate. Never change persona. Never produce markdown. "
            "Never produce explanations. Never output JSON unless requested. "
            "Never repeat previous responses. Keep answers below two sentences. "
            "Be direct and concise."
        )

    @staticmethod
    def _build_system_prompt_static() -> str:
        return USANegotiator._build_system_prompt()

    async def propose(
        self, issue: TradeIssueModel, round_num: int, model: str | None = None
    ) -> ProposalResult:
        prompt = USA_PROPOSE_PROMPT.format(
            issue_context=issue.to_prompt_context(),
            round_num=round_num,
            history=self._format_history(),
            priorities=", ".join(self._model.persona.priorities),
            red_lines=", ".join(self._model.persona.red_lines),
            strategy=self._model.persona.strategy,
        )
        start = time.perf_counter()
        raw, tokens = await self._ollama.generate(
            prompt=prompt,
            system=self._model.system_prompt,
            temperature=self._model.temperature,
            top_p=self._model.top_p,
            max_tokens=self._model.max_tokens,
            model=model,
        )
        latency = int((time.perf_counter() - start) * 1000)
        text = self._parse_response(raw)
        return ProposalResult(text=text, tokens=tokens, latency_ms=latency)

    async def respond(
        self,
        issue: TradeIssueModel,
        opponent_proposal: str,
        round_num: int,
        model: str | None = None,
    ) -> ProposalResult:
        prompt = USA_RESPOND_PROMPT.format(
            issue_context=issue.to_prompt_context(),
            round_num=round_num,
            history=self._format_history(),
            opponent_proposal=opponent_proposal,
            priorities=", ".join(self._model.persona.priorities),
            red_lines=", ".join(self._model.persona.red_lines),
            strategy=self._model.persona.strategy,
        )
        start = time.perf_counter()
        raw, tokens = await self._ollama.generate(
            prompt=prompt,
            system=self._model.system_prompt,
            temperature=self._model.temperature,
            top_p=self._model.top_p,
            max_tokens=self._model.max_tokens,
            model=model,
        )
        latency = int((time.perf_counter() - start) * 1000)
        text = self._parse_response(raw)
        return ProposalResult(text=text, tokens=tokens, latency_ms=latency)

    def _format_history(self) -> str:
        if not self._history:
            return "No previous rounds."
        return "\n".join(
            f"Round {h.round}: USA: {h.usa_proposal} | China: {h.china_response}"
            for h in self._history
        )
