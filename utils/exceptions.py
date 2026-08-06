from __future__ import annotations

from typing import Any


class NegotiationError(Exception):
    def __init__(
        self, message: str, code: str = "NEGOTIATION_ERROR", details: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class OllamaError(NegotiationError):
    def __init__(
        self, message: str, status_code: int | None = None, details: dict[str, Any] | None = None
    ):
        super().__init__(message, code="OLLAMA_ERROR", details=details)
        self.status_code = status_code


class OllamaTimeoutError(OllamaError):
    def __init__(
        self, message: str = "Ollama request timed out", details: dict[str, Any] | None = None
    ):
        super().__init__(message, status_code=408, details=details)


class OllamaConnectionError(OllamaError):
    def __init__(
        self, message: str = "Cannot connect to Ollama", details: dict[str, Any] | None = None
    ):
        super().__init__(message, status_code=503, details=details)


class OllamaModelError(OllamaError):
    def __init__(
        self, message: str = "Invalid or unavailable model", details: dict[str, Any] | None = None
    ):
        super().__init__(message, status_code=400, details=details)


class ValidationError(NegotiationError):
    def __init__(
        self, message: str, field: str | None = None, details: dict[str, Any] | None = None
    ):
        super().__init__(message, code="VALIDATION_ERROR", details=details)
        self.field = field


class ConfigurationError(NegotiationError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)


class StateError(NegotiationError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="STATE_ERROR", details=details)
