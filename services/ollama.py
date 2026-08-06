from __future__ import annotations

import json
import time
from typing import Final

import httpx
import structlog

from config.settings import get_settings
from utils.exceptions import (
    OllamaConnectionError,
    OllamaError,
    OllamaModelError,
    OllamaTimeoutError,
)
from utils.retry import ollama_retry
from utils.validation import sanitize_input

logger = structlog.get_logger(__name__)

DEFAULT_FALLBACK: Final[str] = "I acknowledge your position. Let us find common ground."
HTTP_NOT_FOUND: Final[int] = 404
HTTP_SERVER_ERROR: Final[int] = 500
HTTP_OK: Final[int] = 200

ERR_CLIENT_NOT_INIT: Final[str] = "Client not initialized"
ERR_INVALID_JSON: Final[str] = "Invalid JSON response from Ollama"
ERR_MODEL_NOT_FOUND: Final[str] = "Model '{0}' not found"
ERR_SERVER_ERROR: Final[str] = "Ollama server error: {0}"


class OllamaService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: httpx.AsyncClient | None = None
        self._model = self._settings.ollama_model

    async def startup(self) -> None:
        limits = httpx.Limits(
            max_connections=self._settings.http_client_pool_limit,
            max_keepalive_connections=self._settings.http_client_pool_limit,
        )
        timeout = httpx.Timeout(self._settings.ollama_timeout)
        self._client = httpx.AsyncClient(
            base_url=self._settings.ollama_base_url,
            timeout=timeout,
            limits=limits,
        )
        logger.info("ollama_client_started", base_url=self._settings.ollama_base_url)

    async def shutdown(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("ollama_client_closed")

    @ollama_retry()
    async def generate(
        self,
        prompt: str,
        system: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
    ) -> tuple[str, int | None]:
        if not self._client:
            raise OllamaConnectionError(ERR_CLIENT_NOT_INIT)

        payload = {
            "model": self._model,
            "prompt": sanitize_input(prompt),
            "system": sanitize_input(system),
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,
            "stream": False,
            "options": {
                "num_ctx": 4096,
                "repeat_penalty": 1.1,
            },
        }

        start = time.perf_counter()
        try:
            response = await self._client.post("/api/generate", json=payload)
            latency = time.perf_counter() - start

            if response.status_code == HTTP_NOT_FOUND:
                raise OllamaModelError(ERR_MODEL_NOT_FOUND.format(self._model))
            if response.status_code >= HTTP_SERVER_ERROR:
                raise OllamaError(ERR_SERVER_ERROR.format(response.status_code))
            response.raise_for_status()

            data = response.json()
            text = data.get("response", "").strip()
            tokens = data.get("eval_count")

            if not text:
                logger.warning("ollama_empty_response", latency_ms=int(latency * 1000))
                return DEFAULT_FALLBACK, tokens

            logger.debug(
                "ollama_response",
                latency_ms=int(latency * 1000),
                tokens=tokens,
            )
            return text, tokens  # noqa: TRY300

        except httpx.TimeoutException as e:
            logger.warning("ollama_timeout", error=str(e))
            raise OllamaTimeoutError() from e
        except httpx.ConnectError as e:
            logger.warning("ollama_connection_error", error=str(e))
            raise OllamaConnectionError() from e
        except json.JSONDecodeError as e:
            logger.warning("ollama_invalid_json", error=str(e))
            raise OllamaError(ERR_INVALID_JSON) from e

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            response = await self._client.get("/api/tags", timeout=5.0)
        except Exception:
            return False
        else:
            return response.status_code == HTTP_OK

    def set_model(self, model: str) -> None:
        self._model = sanitize_input(model, max_length=100)

    def get_model(self) -> str:
        return self._model
