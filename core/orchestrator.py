from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agents.factory import AgentFactory
    from core.scoring import ScoringEngine
    from schemas.request import NegotiateRequest
    from services.logging import LoggingService

from core.state import STATE_MANAGER, NegotiationState
from models.history import HistoryRoundModel
from models.issue import TradeIssueModel
from schemas.response import HistoryRound, NegotiateResponse


@dataclass(frozen=True, slots=True)
class OrchestratorResult:
    response: NegotiateResponse
    log_entry: dict[str, Any]


class NegotiationOrchestrator:
    def __init__(self, factory: AgentFactory, scorer: ScoringEngine, logger: LoggingService):
        self._factory = factory
        self._scorer = scorer
        self._logger = logger

    async def run(self, request: NegotiateRequest, model: str) -> OrchestratorResult:
        start = time.perf_counter()
        nid = str(uuid.uuid4())[:8]
        issue = TradeIssueModel.from_request(request.issue, request.rounds)
        state = STATE_MANAGER.create_state(nid, issue, request.rounds, model)
        usa, china = self._factory.create_pair()
        usa.clear_history()
        china.clear_history()
        try:
            for r in range(1, request.rounds + 1):
                usa_prop = await usa.propose(issue, r)
                china_resp = await china.respond(issue, usa_prop.text, r)
                rd = HistoryRoundModel.create(
                    r,
                    usa_prop.text,
                    china_resp.text,
                    usa_prop.latency_ms + china_resp.latency_ms,
                    usa_prop.tokens,
                )
                usa.add_to_history(rd)
                china.add_to_history(rd)
                state = STATE_MANAGER.update_state(nid, state.add_round(rd))
                score = self._scorer.score_round(usa_prop.text, china_resp.text)
                if score.agreement_reached:
                    state = STATE_MANAGER.update_state(nid, state.set_agreement(score.score))
                    break
            final_score = self._scorer.score_final(
                [(h.usa_proposal, h.china_response) for h in state.history]
            )
            state = STATE_MANAGER.update_state(nid, state.set_agreement(final_score.score))
            exec_ms = int((time.perf_counter() - start) * 1000)
            resp = self._build_response(state, exec_ms, model, request)
            self._logger.log(state.to_log_entry(request.model_dump(), exec_ms).model_dump())
            return OrchestratorResult(response=resp, log_entry={})
        except Exception as e:
            exec_ms = int((time.perf_counter() - start) * 1000)
            self._logger.log(
                {
                    "request": request.model_dump(),
                    "history": [],
                    "score": 0.0,
                    "agreement": False,
                    "execution_time_ms": exec_ms,
                    "model": model,
                    "error": str(e),
                }
            )
            raise

    def _build_response(
        self, state: NegotiationState, exec_ms: int, model: str, request: NegotiateRequest
    ) -> NegotiateResponse:
        hist = [
            HistoryRound(
                round=h.round,
                timestamp=h.timestamp,
                usa_proposal=h.usa_proposal,
                china_response=h.china_response,
                tokens=h.tokens,
                latency_ms=h.latency_ms,
            )
            for h in state.history
        ]
        return NegotiateResponse(
            issue=request.issue,
            rounds=state.current_round,
            history=hist,
            agreement_reached=state.agreement_reached,
            score=state.final_score or 0.0,
            summary=self._scorer._generate_summary(
                state.final_score or 0.0, state.agreement_reached
            ),
            execution_time_ms=exec_ms,
            model=model,
        )
