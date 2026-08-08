import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

# Set test environment variables BEFORE any imports
os.environ.setdefault("OLLAMA_BASE_URL", "http://test:11434")
os.environ.setdefault("OLLAMA_MODEL", "test-model")
os.environ.setdefault("OLLAMA_TIMEOUT", "5.0")
os.environ.setdefault("OLLAMA_MAX_RETRIES", "1")
os.environ.setdefault("LOG_FILE", "/tmp/test_negotiation_log.json")

import pytest
import pytest_asyncio
from httpx import AsyncClient
from main import app

from agents.factory import AgentFactory
from config.settings import Settings
from core.orchestrator import NegotiationOrchestrator
from core.scoring import ScoringEngine
from core.state import STATE_MANAGER
from services.logging import LoggingService
from services.ollama import OllamaService


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    return Settings(
        ollama_base_url="http://test:11434",
        ollama_model="test-model",
        ollama_timeout=5.0,
        ollama_max_retries=1,
    )


@pytest.fixture
def mock_ollama_service():
    service = MagicMock(spec=OllamaService)
    service.generate = AsyncMock(return_value="Test proposal")
    service.health_check = AsyncMock(return_value=True)
    service.get_model = MagicMock(return_value="test-model")
    service.set_model = MagicMock()
    service.ensure_model = AsyncMock(return_value="test-model")
    service.pull_model = AsyncMock()
    return service


@pytest.fixture
def agent_factory(mock_ollama_service):
    return AgentFactory(mock_ollama_service)


@pytest.fixture
def scoring_engine():
    return ScoringEngine()


@pytest.fixture
def orchestrator(agent_factory, scoring_engine):
    logging_service = LoggingService(log_file="/tmp/test_log.json")
    return NegotiationOrchestrator(agent_factory, scoring_engine, logging_service)


@pytest.fixture(autouse=True)
def clear_state():
    STATE_MANAGER.clear()
    yield
    STATE_MANAGER.clear()


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
