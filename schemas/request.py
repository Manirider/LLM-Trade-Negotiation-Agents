from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

MAX_MODEL_NAME_LENGTH = 100

ERR_EMPTY_ISSUE: str = "Issue cannot be empty or whitespace only"
ERR_UNSAFE_CONTENT: str = "Potentially unsafe content detected: {0}"
ERR_MODEL_TOO_LONG: str = "Model name too long"


class NegotiateRequest(BaseModel):
    issue: str = Field(..., min_length=1, max_length=1000, description="Trade issue to negotiate")
    rounds: int = Field(..., ge=1, le=10, description="Number of negotiation rounds")
    model: str | None = Field(default=None, description="Override default Ollama model")

    @field_validator("issue")
    @classmethod
    def validate_issue(cls, v: str) -> str:
        sanitized = v.strip()
        if not sanitized:
            raise ValueError(ERR_EMPTY_ISSUE)
        forbidden = ["<script", "javascript:", "onclick", "onerror", "eval(", "exec("]
        lower = sanitized.lower()
        for f in forbidden:
            if f in lower:
                raise ValueError(ERR_UNSAFE_CONTENT.format(f))
        return sanitized

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str | None) -> str | None:
        if v is not None:
            sanitized = v.strip()
            if not sanitized:
                return None
            if len(sanitized) > MAX_MODEL_NAME_LENGTH:
                raise ValueError(ERR_MODEL_TOO_LONG)
        return v


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    ollama_connected: bool = False
