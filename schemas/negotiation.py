from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Country(StrEnum):
    USA = "USA"
    CHINA = "China"


class NegotiatorPersona(BaseModel):
    country: Country
    role: str = Field(..., description="Negotiator role description")
    priorities: list[str] = Field(..., min_length=1, description="Key negotiation priorities")
    flexibility: float = Field(
        ..., ge=0.0, le=1.0, description="Flexibility factor (0=rigid, 1=flexible)"
    )
    red_lines: list[str] = Field(default_factory=list, description="Non-negotiable positions")
    strategy: str = Field(..., description="Negotiation strategy description")


class NegotiatorConfig(BaseModel):
    persona: NegotiatorPersona
    system_prompt: str = Field(..., description="System prompt for LLM")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(default=150, ge=50, le=500)


class TradeIssue(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    usa_priorities: list[str] = Field(default_factory=list)
    china_priorities: list[str] = Field(default_factory=list)
    context: str | None = Field(default=None)


class NegotiationState(BaseModel):
    issue: TradeIssue
    rounds: int
    current_round: int = 0
    history: list[HistoryRound] = Field(default_factory=list)
    agreement_reached: bool = False
    final_score: float | None = None


class HistoryRound(BaseModel):
    model_config = ConfigDict(frozen=True)

    round: int = Field(..., ge=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    usa_proposal: str
    china_response: str
    tokens: int | None = None
    latency_ms: int


class LogEntry(BaseModel):
    request: dict[str, Any]
    history: list[HistoryRound]
    score: float
    agreement: bool
    execution_time_ms: int
    model: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
