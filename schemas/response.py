from __future__ import annotations

from typing import Any, Final

from pydantic import BaseModel, Field, model_validator

from schemas.negotiation import HistoryRound as HistoryRound  # noqa: PLC0414, TC001

ERR_INVALID_SCORE: Final[str] = "score must be between 0.0 and 1.0"


class OutcomeModel(BaseModel):
    agreement_reached: bool = Field(..., description="Whether agreement was reached")
    final_terms: str = Field(..., description="Final negotiated terms and conditions")
    compromise_score: float = Field(..., ge=0.0, le=1.0, description="Compromise score (0.0-1.0)")


class NegotiateResponse(BaseModel):
    issue: str = Field(..., description="The negotiated issue")
    rounds: list[HistoryRound] = Field(..., description="List of completed negotiation rounds")
    outcome: OutcomeModel = Field(..., description="Negotiation outcome")
    history: list[HistoryRound] = Field(
        default_factory=list, description="Complete negotiation history"
    )
    summary: str = Field(default="", description="Negotiation outcome summary")
    execution_time_ms: int = Field(default=0, ge=0, description="Total execution time")
    model: str = Field(default="", description="Model used for negotiation")
    agreement_reached: bool | None = Field(
        default=None, description="Top-level compatibility field"
    )
    score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Top-level compatibility field"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_response(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Check bounds on top-level score if provided
        if (
            "score" in data
            and data["score"] is not None
            and not (0.0 <= float(data["score"]) <= 1.0)
        ):
            raise ValueError(ERR_INVALID_SCORE)

        # Resolve outcome
        if "outcome" not in data:
            agreement = data.get("agreement_reached", False)
            score_val = data.get("score", 0.0)
            summary_val = data.get("summary", "")
            final_terms_val = data.get(
                "final_terms",
                summary_val or "Negotiation completed.",
            )
            data["outcome"] = {
                "agreement_reached": agreement,
                "final_terms": final_terms_val,
                "compromise_score": score_val,
            }
        elif isinstance(data["outcome"], dict):
            data.setdefault("agreement_reached", data["outcome"].get("agreement_reached"))
            data.setdefault("score", data["outcome"].get("compromise_score"))

        # Resolve rounds and history
        rounds_val = data.get("rounds")
        history_val = data.get("history")

        if isinstance(rounds_val, list):
            if not history_val:
                data["history"] = rounds_val
        elif isinstance(rounds_val, int):
            # If rounds is given as an int count, use history list as rounds
            if isinstance(history_val, list):
                data["rounds"] = history_val
            else:
                data["rounds"] = []

        return data


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
