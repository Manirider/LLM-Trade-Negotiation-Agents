from __future__ import annotations

import html
import re
from typing import Any, Final

FORBIDDEN_PATTERNS: Final[list[str]] = [
    r"<script\b[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__",
    r"subprocess",
    r"os\.system",
]

SENSITIVE_KEYS: Final[set[str]] = {
    "password",
    "secret",
    "key",
    "token",
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
}

ERR_NOT_INT: Final[str] = "Rounds must be integer, got {0}"
ERR_MIN_ROUNDS: Final[str] = "Rounds must be >= {0}"
ERR_MAX_ROUNDS: Final[str] = "Rounds must be <= {0}"


def sanitize_input(text: str, max_length: int = 1000) -> str:
    if not text:
        return ""
    sanitized = text.strip()[:max_length]
    sanitized = html.escape(sanitized)
    for pattern in FORBIDDEN_PATTERNS:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    return sanitized


def sanitize_for_log(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    result: dict[str, Any] = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            result[key] = "***REDACTED***"
        elif isinstance(value, dict):
            result[key] = sanitize_for_log(value)
        elif isinstance(value, list):
            result[key] = [sanitize_for_log(v) if isinstance(v, dict) else v for v in value]
        else:
            result[key] = value
    return result


def validate_rounds(rounds: int, min_rounds: int = 1, max_rounds: int = 10) -> int:
    if not isinstance(rounds, int):
        raise TypeError(ERR_NOT_INT.format(type(rounds).__name__))
    if rounds < min_rounds:
        raise ValueError(ERR_MIN_ROUNDS.format(min_rounds))
    if rounds > max_rounds:
        raise ValueError(ERR_MAX_ROUNDS.format(max_rounds))
    return rounds


def extract_keywords(text: str, keywords: list[str]) -> list[str]:
    lower_text = text.lower()
    return [kw for kw in keywords if kw.lower() in lower_text]
