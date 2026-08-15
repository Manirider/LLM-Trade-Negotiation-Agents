from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Final

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from agents.factory import AgentFactory
from config.settings import get_settings
from core.orchestrator import NegotiationOrchestrator
from core.scoring import ScoringEngine
from schemas.request import HealthResponse, NegotiateRequest
from schemas.response import ErrorResponse, NegotiateResponse
from services.logging import LoggingService
from services.ollama import OllamaService
from utils.exceptions import (
    NegotiationError,
    OllamaConnectionError,
    OllamaModelError,
    OllamaTimeoutError,
)
from utils.exceptions import ValidationError as AppValidationError

settings = get_settings()

ollama_service: Final[OllamaService] = OllamaService()
logging_service: Final[LoggingService] = LoggingService()
agent_factory: Final[AgentFactory] = AgentFactory(ollama_service)
scoring_engine: Final[ScoringEngine] = ScoringEngine()
orchestrator: Final[NegotiationOrchestrator] = NegotiationOrchestrator(
    agent_factory, scoring_engine, logging_service
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(settings.log_level),
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await ollama_service.startup()
    structlog.get_logger().info("application_startup", version="1.0.0")
    yield
    await ollama_service.shutdown()
    structlog.get_logger().info("application_shutdown")


app = FastAPI(
    title="LLM Trade Negotiation Agents",
    description="USA-China trade negotiation simulation using LLMs",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(NegotiationError)
async def negotiation_error_handler(_request: Request, exc: NegotiationError) -> JSONResponse:
    logging_service.log_error(exc, {"path": str(_request.url)})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=exc.code,
            message=exc.message,
            details=exc.details,
        ).model_dump(),
    )


@app.exception_handler(OllamaTimeoutError)
async def ollama_timeout_handler(_request: Request, exc: OllamaTimeoutError) -> JSONResponse:
    logging_service.log_error(exc, {"path": str(_request.url)})
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content=ErrorResponse(
            error="OLLAMA_TIMEOUT",
            message="LLM service timed out. Please try again.",
            details={"retry_after": settings.ollama_retry_max_delay},
        ).model_dump(),
    )


@app.exception_handler(OllamaConnectionError)
async def ollama_connection_handler(_request: Request, exc: OllamaConnectionError) -> JSONResponse:
    logging_service.log_error(exc, {"path": str(_request.url)})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse(
            error="OLLAMA_UNAVAILABLE",
            message="LLM service is currently unavailable.",
            details={},
        ).model_dump(),
    )


@app.exception_handler(OllamaModelError)
async def ollama_model_handler(_request: Request, exc: OllamaModelError) -> JSONResponse:
    logging_service.log_error(exc, {"path": str(_request.url)})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="INVALID_MODEL",
            message=str(exc),
            details=exc.details,
        ).model_dump(),
    )


@app.exception_handler(AppValidationError)
async def validation_error_handler(_request: Request, exc: AppValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message=exc.message,
            details=exc.details,
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def pydantic_validation_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": errors},
        ).model_dump(),
    )


@app.exception_handler(ValidationError)
async def pydantic_model_validation_handler(
    _request: Request, exc: ValidationError
) -> JSONResponse:
    errors = [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="Data validation failed",
            details={"errors": errors},
        ).model_dump(),
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    ollama_connected = await ollama_service.health_check()
    return HealthResponse(ollama_connected=ollama_connected)


@app.post("/negotiate", response_model=NegotiateResponse)
async def negotiate(request: NegotiateRequest) -> NegotiateResponse:
    model = request.model or settings.ollama_model

    # Ensure model is available locally; pulls if missing
    await ollama_service.ensure_model(model)

    result = await orchestrator.run(request, model)
    return result.response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
