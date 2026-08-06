from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class HistoryRound(BaseModel):
    round: int = Field(..., ge=1, description="Round number (1-indexed)")
    timestamp: datetime = Field(..., description="ISO 8601 timestamp")
    usa_proposal: str = Field(..., description="USA proposal text")
    china_response: str = Field(..., description="China response text")
    tokens: int | None = Field(default=None, ge=0, description="Tokens used (if available)")
    latency_ms: int = Field(..., ge=0, description="Round latency in milliseconds")


class NegotiateResponse(BaseModel):
    issue: str = Field(..., description="The negotiated issue")
    rounds: int = Field(..., ge=1, description="Number of rounds executed")
    history: list[HistoryRound] = Field(..., description="Complete negotiation history")
    agreement_reached: bool = Field(..., description="Whether agreement was reached")
    score: float = Field(..., ge=0.0, le=1.0, description="Compromise score (0.0-1.0)")
    summary: str = Field(..., min_length=1, description="Negotiation outcome summary")
    execution_time_ms: int = Field(..., ge=0, description="Total execution time")
    model: str = Field(..., description="Model used for negotiation")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
