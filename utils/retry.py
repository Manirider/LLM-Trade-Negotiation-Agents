from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ParamSpec, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import get_settings
from utils.exceptions import OllamaConnectionError, OllamaError, OllamaTimeoutError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

_settings = get_settings()


def ollama_retry() -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    return retry(
        stop=stop_after_attempt(_settings.ollama_max_retries),
        wait=wait_exponential(
            multiplier=_settings.ollama_retry_base_delay,
            max=_settings.ollama_retry_max_delay,
        ),
        retry=retry_if_exception_type((OllamaTimeoutError, OllamaConnectionError, OllamaError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )


async def async_retry_with_fallback(
    func: Callable[P, Awaitable[T]],
    fallback: Callable[P, Awaitable[T]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    try:
        return await func(*args, **kwargs)
    except (OllamaTimeoutError, OllamaConnectionError, OllamaError) as e:
        logger.warning("All retries exhausted, using fallback: %s", e)
        return await fallback(*args, **kwargs)
