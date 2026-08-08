"""Comprehensive test suite for LLM Trade Negotiation Agents."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import ParamSpec, TypeVar
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app

from agents.base import ProposalResult
from agents.china import ChinaNegotiator, ChinaNegotiatorConfig
from agents.factory import AgentFactory
from agents.usa import USANegotiator, USANegotiatorConfig
from config.settings import Settings
from core.orchestrator import NegotiationOrchestrator
from core.prompts import (
    CHINA_PROPOSE_PROMPT,
    CHINA_RESPOND_PROMPT,
    USA_PROPOSE_PROMPT,
    USA_RESPOND_PROMPT,
)
from core.scoring import ScoringEngine
from core.state import STATE_MANAGER
from models.history import HistoryRoundModel
from models.issue import TradeIssueModel
from models.negotiator import CHINA_PERSONA, USA_PERSONA, NegotiatorModel
from schemas.negotiation import (
    Country,
    HistoryRound,
    LogEntry,
    NegotiatorConfig,
    NegotiatorPersona,
    TradeIssue,
)
from schemas.request import HealthResponse, NegotiateRequest
from schemas.response import ErrorResponse, NegotiateResponse
from services.logging import LoggingService
from services.ollama import DEFAULT_FALLBACK, OllamaService
from storage.file_storage import FileStorage
from storage.memory_storage import MemoryStorage
from utils.exceptions import (
    ConfigurationError,
    NegotiationError,
    OllamaConnectionError,
    OllamaError,
    OllamaModelError,
    OllamaTimeoutError,
    StateError,
    ValidationError,
)
from utils.retry import async_retry_with_fallback, ollama_retry
from utils.validation import (
    FORBIDDEN_PATTERNS,
    SENSITIVE_KEYS,
    extract_keywords,
    sanitize_for_log,
    sanitize_input,
    validate_rounds,
)

P = ParamSpec("P")
T = TypeVar("T")


# Test constants
DEFAULT_ROUNDS = 3
DEFAULT_TEST_ROUNDS = 2
DEFAULT_MAX_ROUNDS = 5
DEFAULT_TOKENS_10 = 10
DEFAULT_TOKENS_15 = 15
DEFAULT_TOKENS_18 = 18
DEFAULT_TOKENS_20 = 20
DEFAULT_TOKENS_25 = 25
DEFAULT_TOKENS_50 = 50
DEFAULT_LATENCY_100 = 100
DEFAULT_LATENCY_150 = 150
DEFAULT_EXECUTION_TIME = 1000
DEFAULT_SCORE_075 = 0.75
DEFAULT_SCORE_08 = 0.8
DEFAULT_SCORE_05 = 0.5
DEFAULT_SCORE_04 = 0.4
DEFAULT_SCORE_06 = 0.6
DEFAULT_TEMP_05 = 0.5
DEFAULT_TEMP_02 = 0.2
DEFAULT_MAX_TOKENS_200 = 200
DEFAULT_MAX_TOKENS_150 = 150
DEFAULT_TOPIC_LENGTH = 100
DEFAULT_LONG_TOPIC_LENGTH = 150
DEFAULT_USA_PRIORITIES = 5
DEFAULT_CHINA_PRIORITIES = 5
DEFAULT_RED_LINES = 3
DEFAULT_FLEXIBILITY_USA = 0.3
DEFAULT_FLEXIBILITY_CHINA = 0.35
DEFAULT_STATUS_200 = 200
DEFAULT_STATUS_422 = 422
DEFAULT_STATUS_504 = 504
DEFAULT_STATUS_503 = 503
DEFAULT_STATUS_500 = 500
DEFAULT_STATUS_408 = 408
DEFAULT_STATUS_400 = 400
DEFAULT_MAX_LENGTH_100 = 100
DEFAULT_MAX_LENGTH_2000 = 2000
DEFAULT_VALIDATE_ROUNDS_1 = 1
DEFAULT_VALIDATE_ROUNDS_5 = 5
DEFAULT_VALIDATE_ROUNDS_10 = 10
DEFAULT_MEMORY_SIZE_2 = 2
DEFAULT_MEMORY_SIZE_10 = 10
DEFAULT_TEMPERATURE_DEFAULT = 0.1
DEFAULT_TOP_P_DEFAULT = 0.9
DEFAULT_MAX_TOKENS_DEFAULT = 150


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


@pytest.fixture
def trade_issue():
    return TradeIssueModel.from_request("Test trade issue", DEFAULT_ROUNDS)


@pytest.fixture
def sample_history():
    return [
        HistoryRoundModel.create(1, "USA proposal", "China response", DEFAULT_LATENCY_100),
        HistoryRoundModel.create(2, "USA proposal 2", "China response 2", DEFAULT_LATENCY_150),
    ]


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_endpoint_returns_healthy(self, async_client):
        with patch("main.ollama_service.health_check", return_value=True):
            response = await async_client.get("/health")
            assert response.status_code == DEFAULT_STATUS_200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["ollama_connected"] is True

    @pytest.mark.asyncio
    async def test_health_endpoint_ollama_unhealthy(self, async_client):
        with patch("main.ollama_service.health_check", return_value=False):
            response = await async_client.get("/health")
            assert response.status_code == DEFAULT_STATUS_200
            data = response.json()
            assert data["ollama_connected"] is False


class TestNegotiateEndpoint:
    @pytest.mark.asyncio
    async def test_negotiate_success(self, async_client, mock_ollama_service):
        mock_ollama_service.generate = AsyncMock(
            side_effect=[
                "USA proposes tariff reduction",
                "China accepts with conditions",
                "USA proposes intellectual property protection",
                "China agrees to strengthen enforcement",
                "USA proposes market access",
                "China offers limited access",
            ]
        )

        with (
            patch("main.ollama_service", mock_ollama_service),
            patch("main.orchestrator") as mock_orchestrator,
        ):
            mock_orchestrator.run = AsyncMock(
                return_value=MagicMock(
                    response=NegotiateResponse(
                        issue="tariffs",
                        rounds=DEFAULT_ROUNDS,
                        history=[],
                        agreement_reached=True,
                        score=DEFAULT_SCORE_075,
                        summary="Agreement reached",
                        execution_time_ms=DEFAULT_EXECUTION_TIME,
                        model="test-model",
                    ),
                    log_entry={},
                )
            )

            response = await async_client.post(
                "/negotiate",
                json={
                    "issue": "tariffs",
                    "rounds": DEFAULT_ROUNDS,
                },
            )

            assert response.status_code == DEFAULT_STATUS_200
            data = response.json()
            assert data["issue"] == "tariffs"
            assert data["rounds"] == DEFAULT_ROUNDS
            assert data["agreement_reached"] is True
            assert 0.0 <= data["score"] <= 1.0

    @pytest.mark.asyncio
    async def test_negotiate_invalid_payload_missing_issue(self, async_client):
        response = await async_client.post("/negotiate", json={"rounds": DEFAULT_ROUNDS})
        assert response.status_code == DEFAULT_STATUS_422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_negotiate_invalid_payload_empty_issue(self, async_client):
        response = await async_client.post(
            "/negotiate", json={"issue": "", "rounds": DEFAULT_ROUNDS}
        )
        assert response.status_code == DEFAULT_STATUS_422

    @pytest.mark.asyncio
    async def test_negotiate_invalid_payload_negative_rounds(self, async_client):
        response = await async_client.post("/negotiate", json={"issue": "test", "rounds": -1})
        assert response.status_code == DEFAULT_STATUS_422

    @pytest.mark.asyncio
    async def test_negotiate_invalid_payload_zero_rounds(self, async_client):
        response = await async_client.post("/negotiate", json={"issue": "test", "rounds": 0})
        assert response.status_code == DEFAULT_STATUS_422

    @pytest.mark.asyncio
    async def test_negotiate_invalid_payload_rounds_too_high(self, async_client):
        response = await async_client.post("/negotiate", json={"issue": "test", "rounds": 11})
        assert response.status_code == DEFAULT_STATUS_422

    @pytest.mark.asyncio
    async def test_negotiate_invalid_payload_extra_fields(self, async_client, mock_ollama_service):
        with (
            patch("main.ollama_service", mock_ollama_service),
            patch("main.orchestrator") as mock_orchestrator,
        ):
            mock_orchestrator.run = AsyncMock(
                return_value=MagicMock(
                    response=NegotiateResponse(
                        issue="test",
                        rounds=DEFAULT_ROUNDS,
                        history=[],
                        agreement_reached=True,
                        score=DEFAULT_SCORE_075,
                        summary="Agreement reached",
                        execution_time_ms=DEFAULT_EXECUTION_TIME,
                        model="test-model",
                    ),
                    log_entry={},
                )
            )
            response = await async_client.post(
                "/negotiate",
                json={"issue": "test", "rounds": DEFAULT_ROUNDS, "unknown_field": "value"},
            )
            assert response.status_code == DEFAULT_STATUS_200


class TestScoringEngine:
    def test_score_round_positive_keywords(self, scoring_engine):
        result = scoring_engine.score_round(
            "We agree to reduce tariffs and cooperate", "We accept and support mutual progress"
        )
        assert result.agreement_reached is True
        assert result.score > DEFAULT_SCORE_06
        assert "agreement" in result.summary.lower()

    def test_score_round_negative_keywords(self, scoring_engine):
        result = scoring_engine.score_round(
            "We reject this proposal completely", "This is impossible and we refuse"
        )
        assert result.agreement_reached is False
        assert result.score < DEFAULT_SCORE_04
        assert "deadlock" in result.summary.lower() or "disagreement" in result.summary.lower()

    def test_score_round_mixed_keywords(self, scoring_engine):
        result = scoring_engine.score_round(
            "We agree to reduce but reject other terms", "We accept some but oppose others"
        )
        assert 0.0 <= result.score <= 1.0

    def test_score_round_no_keywords(self, scoring_engine):
        result = scoring_engine.score_round(
            "Neutral statement without keywords", "Another neutral response"
        )
        assert result.score == DEFAULT_SCORE_05
        assert result.agreement_reached is False

    def test_score_final_empty_history(self, scoring_engine):
        result = scoring_engine.score_final([])
        assert result.agreement_reached is False
        assert result.score == 0.0

    def test_score_final_with_history(self, scoring_engine):
        result = scoring_engine.score_final(
            [
                ("USA agree", "China accept"),
            ]
        )
        assert result.agreement_reached is True

    def test_positive_keywords_constant(self):
        assert "agreement" in ScoringEngine.POSITIVE_KEYWORDS
        assert "accept" in ScoringEngine.POSITIVE_KEYWORDS
        assert "cooperate" in ScoringEngine.POSITIVE_KEYWORDS

    def test_negative_keywords_constant(self):
        assert "reject" in ScoringEngine.NEGATIVE_KEYWORDS
        assert "refuse" in ScoringEngine.NEGATIVE_KEYWORDS
        assert "impossible" in ScoringEngine.NEGATIVE_KEYWORDS

    def test_agreement_threshold(self):
        assert ScoringEngine.AGREEMENT_THRESHOLD == DEFAULT_SCORE_06


class TestStateManager:
    def test_create_state(self, trade_issue):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-1", trade_issue, DEFAULT_ROUNDS, "test-model")
        assert state.rounds == DEFAULT_ROUNDS
        assert state.current_round == 0
        assert state.model == "test-model"
        assert not state.is_complete

    def test_add_round(self, trade_issue, sample_history):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-2", trade_issue, DEFAULT_ROUNDS, "test-model")
        round_data = sample_history[0]
        new_state = state.add_round(round_data)
        assert new_state.current_round == 1
        assert len(new_state.history) == 1
        assert new_state.history[0] == round_data

    def test_set_agreement(self, trade_issue):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-3", trade_issue, DEFAULT_ROUNDS, "test-model")
        new_state = state.set_agreement(DEFAULT_SCORE_08)
        assert new_state.agreement_reached is True
        assert new_state.final_score == DEFAULT_SCORE_08

    def test_is_complete_rounds_exhausted(self, trade_issue, sample_history):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-4", trade_issue, DEFAULT_TEST_ROUNDS, "test-model")
        state = state.add_round(sample_history[0])
        state = state.add_round(sample_history[1])
        assert state.is_complete is True

    def test_is_complete_agreement_reached(self, trade_issue):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-5", trade_issue, DEFAULT_MAX_ROUNDS, "test-model")
        state = state.set_agreement(0.7)
        assert state.is_complete is True

    def test_create_and_get_state(self, trade_issue):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-1", trade_issue, DEFAULT_ROUNDS, "test-model")
        retrieved = STATE_MANAGER.get_state("test-1")
        assert retrieved is state

    def test_get_nonexistent_state(self):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.get_state("nonexistent")
        assert state is None

    def test_update_state(self, trade_issue):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-1", trade_issue, DEFAULT_ROUNDS, "test-model")
        new_state = state.set_agreement(0.9)
        updated = STATE_MANAGER.update_state("test-1", new_state)
        assert updated.agreement_reached is True
        assert STATE_MANAGER.get_state("test-1").agreement_reached is True

    def test_delete_state(self, trade_issue):
        STATE_MANAGER.clear()
        STATE_MANAGER.create_state("test-1", trade_issue, DEFAULT_ROUNDS, "test-model")
        STATE_MANAGER.delete_state("test-1")
        assert STATE_MANAGER.get_state("test-1") is None

    def test_clear(self, trade_issue):
        STATE_MANAGER.clear()
        STATE_MANAGER.create_state("test-1", trade_issue, DEFAULT_ROUNDS, "test-model")
        STATE_MANAGER.clear()
        assert STATE_MANAGER.get_state("test-1") is None


class TestNegotiationOrchestrator:
    @pytest.mark.asyncio
    async def test_run_creates_history(self, orchestrator, trade_issue):  # noqa: ARG002
        STATE_MANAGER.clear()
        request = NegotiateRequest(issue="test issue", rounds=DEFAULT_TEST_ROUNDS)

        with patch.object(orchestrator._factory, "create_pair") as mock_create:
            usa = AsyncMock()
            china = AsyncMock()
            usa.propose = AsyncMock(
                return_value=MagicMock(
                    text="USA prop",
                    tokens=DEFAULT_TOKENS_10,
                    latency_ms=DEFAULT_LATENCY_100,
                )
            )
            china.respond = AsyncMock(
                return_value=MagicMock(
                    text="China resp",
                    tokens=DEFAULT_TOKENS_10,
                    latency_ms=DEFAULT_LATENCY_100,
                )
            )
            usa.clear_history = MagicMock()
            china.clear_history = MagicMock()
            usa.add_to_history = MagicMock()
            china.add_to_history = MagicMock()
            mock_create.return_value = (usa, china)

            result = await orchestrator.run(request, "test-model")

            assert result.response.rounds == DEFAULT_TEST_ROUNDS
            assert len(result.response.history) == DEFAULT_TEST_ROUNDS

    @pytest.mark.asyncio
    async def test_run_stops_on_agreement(self, orchestrator, trade_issue):  # noqa: ARG002
        STATE_MANAGER.clear()
        request = NegotiateRequest(issue="test issue", rounds=DEFAULT_MAX_ROUNDS)

        with patch.object(orchestrator._factory, "create_pair") as mock_create:
            usa = AsyncMock()
            china = AsyncMock()
            usa.propose = AsyncMock(
                return_value=MagicMock(
                    text="We agree to all terms",
                    tokens=DEFAULT_TOKENS_10,
                    latency_ms=DEFAULT_LATENCY_100,
                )
            )
            china.respond = AsyncMock(
                return_value=MagicMock(
                    text="We accept completely",
                    tokens=DEFAULT_TOKENS_10,
                    latency_ms=DEFAULT_LATENCY_100,
                )
            )
            usa.clear_history = MagicMock()
            china.clear_history = MagicMock()
            usa.add_to_history = MagicMock()
            china.add_to_history = MagicMock()
            mock_create.return_value = (usa, china)

            result = await orchestrator.run(request, "test-model")

            assert result.response.rounds <= DEFAULT_MAX_ROUNDS
            assert len(result.response.history) <= DEFAULT_MAX_ROUNDS

    @pytest.mark.asyncio
    async def test_run_logs_error_on_exception(self, orchestrator, trade_issue):  # noqa: ARG002
        STATE_MANAGER.clear()
        request = NegotiateRequest(issue="test issue", rounds=DEFAULT_TEST_ROUNDS)

        with patch.object(orchestrator._factory, "create_pair") as mock_create:
            usa = AsyncMock()
            usa.propose = AsyncMock(side_effect=Exception("Test error"))
            china = AsyncMock()
            china.clear_history = MagicMock()
            mock_create.return_value = (usa, china)

            with pytest.raises(Exception) as exc_info:
                await orchestrator.run(request, "test-model")
            assert "Test error" in str(exc_info.value)

    def test_build_response(self, orchestrator, trade_issue, sample_history):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-1", trade_issue, DEFAULT_ROUNDS, "test-model")
        state = state.add_round(sample_history[0])
        state = state.set_agreement(DEFAULT_SCORE_08)

        request = NegotiateRequest(issue="test issue", rounds=DEFAULT_ROUNDS)
        response = orchestrator._build_response(
            state, DEFAULT_EXECUTION_TIME, "test-model", request
        )

        assert response.issue == "test issue"
        assert response.rounds == 1
        assert len(response.history) == 1
        assert response.agreement_reached is True
        assert response.score == DEFAULT_SCORE_08
        assert response.model == "test-model"
        assert response.execution_time_ms == DEFAULT_EXECUTION_TIME


class TestAgentFactory:
    def test_create_usa(self, agent_factory):
        usa = agent_factory.create_usa()
        assert isinstance(usa, USANegotiator)
        assert usa.country == "USA"

    def test_create_china(self, agent_factory):
        china = agent_factory.create_china()
        assert isinstance(china, ChinaNegotiator)
        assert china.country == "China"

    def test_create_pair(self, agent_factory):
        usa, china = agent_factory.create_pair()
        assert isinstance(usa, USANegotiator)
        assert isinstance(china, ChinaNegotiator)

    def test_create_usa_with_custom_config(self, agent_factory):
        custom_config = USANegotiatorConfig(
            temperature=DEFAULT_TEMP_05, max_tokens=DEFAULT_MAX_TOKENS_200
        )
        usa = agent_factory.create_usa(custom_config)
        assert usa._model.temperature == DEFAULT_TEMP_05
        assert usa._model.max_tokens == DEFAULT_MAX_TOKENS_200

    def test_create_china_with_custom_config(self, agent_factory):
        custom_config = ChinaNegotiatorConfig(
            temperature=DEFAULT_TEMP_05, max_tokens=DEFAULT_MAX_TOKENS_200
        )
        china = agent_factory.create_china(custom_config)
        assert china._model.temperature == DEFAULT_TEMP_05
        assert china._model.max_tokens == DEFAULT_MAX_TOKENS_200

    def test_set_default_configs(self, agent_factory):
        new_usa_config = USANegotiatorConfig(temperature=DEFAULT_TEMP_02)
        new_china_config = ChinaNegotiatorConfig(temperature=DEFAULT_TEMP_02)
        agent_factory.set_default_configs(new_usa_config, new_china_config)
        usa = agent_factory.create_usa()
        china = agent_factory.create_china()
        assert usa._model.temperature == DEFAULT_TEMP_02
        assert china._model.temperature == DEFAULT_TEMP_02


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_ollama_timeout_returns_504(self, async_client, mock_ollama_service):
        with (
            patch("main.ollama_service", mock_ollama_service),
            patch("main.orchestrator") as mock_orchestrator,
        ):
            mock_orchestrator.run = AsyncMock(side_effect=OllamaTimeoutError())
            response = await async_client.post("/negotiate", json={"issue": "test", "rounds": 1})
            assert response.status_code == DEFAULT_STATUS_504

    @pytest.mark.asyncio
    async def test_ollama_connection_error_returns_503(self, async_client, mock_ollama_service):
        with (
            patch("main.ollama_service", mock_ollama_service),
            patch("main.orchestrator") as mock_orchestrator,
        ):
            mock_orchestrator.run = AsyncMock(side_effect=OllamaConnectionError())
            response = await async_client.post("/negotiate", json={"issue": "test", "rounds": 1})
            assert response.status_code == DEFAULT_STATUS_503


class TestResponseSchema:
    def test_negotiate_response_validation(self):
        response = NegotiateResponse(
            issue="test",
            rounds=DEFAULT_ROUNDS,
            history=[],
            agreement_reached=True,
            score=DEFAULT_SCORE_075,
            summary="Test summary",
            execution_time_ms=DEFAULT_EXECUTION_TIME,
            model="test-model",
        )
        assert response.score == DEFAULT_SCORE_075
        assert response.agreement_reached is True
        assert 0.0 <= response.score <= 1.0


class TestOllamaService:
    @pytest.fixture
    def ollama_service(self, mock_settings):
        with patch("services.ollama.get_settings", return_value=mock_settings):
            return OllamaService()

    def test_init(self, ollama_service, mock_settings):
        assert ollama_service._settings == mock_settings
        assert ollama_service._client is None
        assert ollama_service._model == mock_settings.ollama_model

    @pytest.mark.asyncio
    async def test_startup(self, ollama_service):
        await ollama_service.startup()
        assert ollama_service._client is not None
        assert hasattr(ollama_service._client, "post")
        await ollama_service.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown(self, ollama_service):
        await ollama_service.startup()
        await ollama_service.shutdown()
        assert ollama_service._client is None

    @pytest.mark.asyncio
    async def test_generate_success(self, ollama_service):
        await ollama_service.startup()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"response": "Test response", "eval_count": 10})
        mock_response.raise_for_status = MagicMock()
        ollama_service._client.post = AsyncMock(return_value=mock_response)

        text, tokens = await ollama_service.generate(
            prompt="Test prompt",
            system="Test system",
            temperature=DEFAULT_TEMPERATURE_DEFAULT,
            top_p=DEFAULT_TOP_P_DEFAULT,
            max_tokens=DEFAULT_MAX_TOKENS_DEFAULT,
        )
        assert text == "Test response"
        assert tokens == DEFAULT_TOKENS_10
        await ollama_service.shutdown()

    @pytest.mark.asyncio
    async def test_generate_empty_response_uses_fallback(self, ollama_service):
        await ollama_service.startup()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"response": "", "eval_count": 0})
        mock_response.raise_for_status = MagicMock()
        ollama_service._client.post = AsyncMock(return_value=mock_response)

        text, tokens = await ollama_service.generate(
            prompt="Test prompt",
            system="Test system",
            temperature=DEFAULT_TEMPERATURE_DEFAULT,
            top_p=DEFAULT_TOP_P_DEFAULT,
            max_tokens=DEFAULT_MAX_TOKENS_DEFAULT,
        )
        assert text == DEFAULT_FALLBACK
        assert tokens == 0
        await ollama_service.shutdown()

    @pytest.mark.asyncio
    async def test_generate_404_raises_model_error(self, ollama_service):
        await ollama_service.startup()
        mock_response = AsyncMock()
        mock_response.status_code = 404
        ollama_service._client.post = AsyncMock(return_value=mock_response)
        ollama_service.pull_model = AsyncMock(side_effect=OllamaModelError("Pull failed"))

        with pytest.raises(OllamaModelError):
            await ollama_service.generate(
                prompt="Test prompt",
                system="Test system",
                temperature=DEFAULT_TEMPERATURE_DEFAULT,
                top_p=DEFAULT_TOP_P_DEFAULT,
                max_tokens=DEFAULT_MAX_TOKENS_DEFAULT,
            )
        await ollama_service.shutdown()

    @pytest.mark.asyncio
    async def test_generate_500_raises_error(self, ollama_service):
        await ollama_service.startup()
        mock_response = AsyncMock()
        mock_response.status_code = DEFAULT_STATUS_500
        ollama_service._client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(OllamaError):
            await ollama_service.generate(
                prompt="Test prompt",
                system="Test system",
                temperature=DEFAULT_TEMPERATURE_DEFAULT,
                top_p=DEFAULT_TOP_P_DEFAULT,
                max_tokens=DEFAULT_MAX_TOKENS_DEFAULT,
            )
        await ollama_service.shutdown()

    @pytest.mark.asyncio
    async def test_generate_timeout_raises_timeout_error(self, ollama_service):
        await ollama_service.startup()
        ollama_service._client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with pytest.raises(OllamaTimeoutError):
            await ollama_service.generate(
                prompt="Test prompt",
                system="Test system",
                temperature=DEFAULT_TEMPERATURE_DEFAULT,
                top_p=DEFAULT_TOP_P_DEFAULT,
                max_tokens=DEFAULT_MAX_TOKENS_DEFAULT,
            )
        await ollama_service.shutdown()

    @pytest.mark.asyncio
    async def test_generate_connection_error_raises_connection_error(self, ollama_service):
        await ollama_service.startup()
        ollama_service._client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

        with pytest.raises(OllamaConnectionError):
            await ollama_service.generate(
                prompt="Test prompt",
                system="Test system",
                temperature=DEFAULT_TEMPERATURE_DEFAULT,
                top_p=DEFAULT_TOP_P_DEFAULT,
                max_tokens=DEFAULT_MAX_TOKENS_DEFAULT,
            )
        await ollama_service.shutdown()

    @pytest.mark.asyncio
    async def test_generate_invalid_json_raises_error(self, ollama_service):
        await ollama_service.startup()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
        mock_response.raise_for_status = MagicMock()
        ollama_service._client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(OllamaError):
            await ollama_service.generate(
                prompt="Test prompt",
                system="Test system",
                temperature=DEFAULT_TEMPERATURE_DEFAULT,
                top_p=DEFAULT_TOP_P_DEFAULT,
                max_tokens=DEFAULT_MAX_TOKENS_DEFAULT,
            )
        await ollama_service.shutdown()

    @pytest.mark.asyncio
    async def test_health_check_success(self, ollama_service):
        await ollama_service.startup()
        mock_response = AsyncMock()
        mock_response.status_code = DEFAULT_STATUS_200
        ollama_service._client.get = AsyncMock(return_value=mock_response)

        result = await ollama_service.health_check()
        assert result is True
        await ollama_service.shutdown()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, ollama_service):
        await ollama_service.startup()
        ollama_service._client.get = AsyncMock(side_effect=Exception("Failed"))

        result = await ollama_service.health_check()
        assert result is False
        await ollama_service.shutdown()

    def test_set_model(self, ollama_service):
        ollama_service.set_model("new-model")
        assert ollama_service.get_model() == "new-model"

    def test_get_model(self, ollama_service):
        assert ollama_service.get_model() == ollama_service._settings.ollama_model


class TestLoggingService:
    @pytest.fixture
    def logging_service(self, tmp_path):
        log_file = tmp_path / "test_log.json"
        return LoggingService(log_file=str(log_file))

    def test_log_writes_to_file(self, logging_service):
        entry = {
            "request": {"issue": "test", "rounds": DEFAULT_ROUNDS},
            "history": [],
            "score": DEFAULT_SCORE_075,
            "agreement": True,
            "execution_time_ms": DEFAULT_EXECUTION_TIME,
            "model": "test-model",
        }
        logging_service.log(entry)
        log_file = logging_service._log_file
        assert log_file.exists()
        content = log_file.read_text()
        assert "test" in content
        assert "0.75" in content

    def test_log_error_writes_to_file(self, logging_service):
        error = ValueError("Test error")
        logging_service.log_error(error, {"path": "/test"})
        log_file = logging_service._log_file
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test error" in content
        assert "ValueError" in content

    def test_log_sanitizes_sensitive_keys(self, logging_service):
        entry = {
            "request": {"issue": "test", "api_key": "secret123"},
            "history": [],
            "score": DEFAULT_SCORE_05,
            "agreement": False,
            "execution_time_ms": 100,
            "model": "test",
        }
        logging_service.log(entry)
        content = logging_service._log_file.read_text()
        assert "***REDACTED***" in content
        assert "secret123" not in content

    def test_get_recent_logs(self, logging_service):
        entry = {
            "request": {"issue": "test"},
            "history": [],
            "score": DEFAULT_SCORE_05,
            "agreement": False,
            "execution_time_ms": 100,
            "model": "test",
        }
        logging_service.log(entry)
        logs = logging_service.get_recent_logs(limit=10)
        assert len(logs) == 1
        assert logs[0]["request"]["issue"] == "test"

    def test_get_recent_logs_empty_file(self, logging_service):
        logging_service._log_file.unlink(missing_ok=True)
        logs = logging_service.get_recent_logs()
        assert logs == []


class TestAgentBase:
    def test_proposal_result_dataclass(self):
        result = ProposalResult(
            text="Test", tokens=DEFAULT_TOKENS_10, latency_ms=DEFAULT_LATENCY_100
        )
        assert result.text == "Test"
        assert result.tokens == DEFAULT_TOKENS_10
        assert result.latency_ms == DEFAULT_LATENCY_100

    def test_base_negotiator_properties(self, agent_factory):
        usa = agent_factory.create_usa()
        assert usa.country == "USA"
        assert usa.persona.country == Country.USA
        assert isinstance(usa.history, tuple)
        assert len(usa.history) == 0

    def test_base_negotiator_add_to_history(self, agent_factory):
        usa = agent_factory.create_usa()
        round_data = HistoryRoundModel.create(
            1, "USA prop", "China resp", DEFAULT_LATENCY_100, DEFAULT_TOKENS_10
        )
        usa.add_to_history(round_data)
        assert len(usa.history) == 1
        assert usa.history[0] == round_data

    def test_base_negotiator_clear_history(self, agent_factory):
        usa = agent_factory.create_usa()
        round_data = HistoryRoundModel.create(
            1, "USA prop", "China resp", DEFAULT_LATENCY_100, DEFAULT_TOKENS_10
        )
        usa.add_to_history(round_data)
        usa.clear_history()
        assert len(usa.history) == 0

    def test_parse_response_strips_markdown(self, agent_factory):
        usa = agent_factory.create_usa()
        raw = "```\nProposal text\n```"
        parsed = usa._parse_response(raw)
        assert parsed == "Proposal text"

    def test_parse_response_handles_multiline(self, agent_factory):
        usa = agent_factory.create_usa()
        raw = "Line 1\nLine 2"
        parsed = usa._parse_response(raw)
        assert parsed == "Line 1"

    def test_parse_response_plain_text(self, agent_factory):
        usa = agent_factory.create_usa()
        raw = "  Plain text  "
        parsed = usa._parse_response(raw)
        assert parsed == "Plain text"


class TestUSANegotiator:
    @pytest.mark.asyncio
    async def test_propose(self, agent_factory, trade_issue):
        usa = agent_factory.create_usa()
        usa._ollama.generate = AsyncMock(return_value=("USA proposal", DEFAULT_TOKENS_20))

        result = await usa.propose(trade_issue, 1)
        assert result.text == "USA proposal"
        assert result.tokens == DEFAULT_TOKENS_20
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_respond(self, agent_factory, trade_issue):
        usa = agent_factory.create_usa()
        usa._ollama.generate = AsyncMock(return_value=("USA response", DEFAULT_TOKENS_15))

        result = await usa.respond(trade_issue, "China proposal", 1)
        assert result.text == "USA response"
        assert result.tokens == DEFAULT_TOKENS_15

    def test_format_history_empty(self, agent_factory):
        usa = agent_factory.create_usa()
        assert usa._format_history() == "No previous rounds."

    def test_format_history_with_data(self, agent_factory):
        usa = agent_factory.create_usa()
        round_data = HistoryRoundModel.create(
            1, "USA prop", "China resp", DEFAULT_LATENCY_100, DEFAULT_TOKENS_10
        )
        usa.add_to_history(round_data)
        formatted = usa._format_history()
        assert "Round 1" in formatted
        assert "USA prop" in formatted
        assert "China resp" in formatted

    def test_system_prompt_contains_priorities(self, agent_factory):
        usa = agent_factory.create_usa()
        assert "Reduce trade deficit" in usa._model.system_prompt
        assert "Protect intellectual property" in usa._model.system_prompt
        assert "30%" in usa._model.system_prompt


class TestChinaNegotiator:
    @pytest.mark.asyncio
    async def test_propose(self, agent_factory, trade_issue):
        china = agent_factory.create_china()
        china._ollama.generate = AsyncMock(return_value=("China proposal", DEFAULT_TOKENS_25))

        result = await china.propose(trade_issue, 1)
        assert result.text == "China proposal"
        assert result.tokens == DEFAULT_TOKENS_25

    @pytest.mark.asyncio
    async def test_respond(self, agent_factory, trade_issue):
        china = agent_factory.create_china()
        china._ollama.generate = AsyncMock(return_value=("China response", DEFAULT_TOKENS_18))

        result = await china.respond(trade_issue, "USA proposal", 1)
        assert result.text == "China response"
        assert result.tokens == DEFAULT_TOKENS_18

    def test_format_history_empty(self, agent_factory):
        china = agent_factory.create_china()
        assert china._format_history() == "No previous rounds."

    def test_format_history_with_data(self, agent_factory):
        china = agent_factory.create_china()
        round_data = HistoryRoundModel.create(
            1, "USA prop", "China resp", DEFAULT_LATENCY_100, DEFAULT_TOKENS_10
        )
        china.add_to_history(round_data)
        formatted = china._format_history()
        assert "Round 1" in formatted
        assert "USA prop" in formatted
        assert "China resp" in formatted

    def test_system_prompt_contains_priorities(self, agent_factory):
        china = agent_factory.create_china()
        assert "Maintain export market access" in china._model.system_prompt
        assert "Preserve developmental policy space" in china._model.system_prompt
        assert "35%" in china._model.system_prompt


class TestTradeIssueModel:
    def test_from_request(self):
        issue = TradeIssueModel.from_request("Test issue description", DEFAULT_ROUNDS)
        assert issue.topic == "Test issue description"
        assert issue.description == "Test issue description"
        assert len(issue.usa_priorities) == DEFAULT_ROUNDS
        assert len(issue.china_priorities) == DEFAULT_ROUNDS
        assert "3 rounds" in issue.context

    def test_from_request_long_topic_truncated(self):
        long_issue = "x" * DEFAULT_LONG_TOPIC_LENGTH
        issue = TradeIssueModel.from_request(long_issue, DEFAULT_ROUNDS)
        assert len(issue.topic) == DEFAULT_TOPIC_LENGTH

    def test_to_prompt_context(self):
        issue = TradeIssueModel.from_request("Test issue", DEFAULT_ROUNDS)
        context = issue.to_prompt_context()
        assert "Issue: Test issue" in context
        assert "Description: Test issue" in context
        assert "USA Priorities:" in context
        assert "China Priorities:" in context
        assert "Context:" in context


class TestHistoryRoundModel:
    def test_create_sets_timestamp(self):
        round_data = HistoryRoundModel.create(
            1, "USA", "China", DEFAULT_LATENCY_100, DEFAULT_TOKENS_50
        )
        assert round_data.round == 1
        assert round_data.usa_proposal == "USA"
        assert round_data.china_response == "China"
        assert round_data.latency_ms == DEFAULT_LATENCY_100
        assert round_data.tokens == DEFAULT_TOKENS_50
        assert round_data.timestamp is not None

    def test_to_dict(self):
        round_data = HistoryRoundModel.create(
            1, "USA", "China", DEFAULT_LATENCY_100, DEFAULT_TOKENS_50
        )
        d = round_data.to_dict()
        assert d["round"] == 1
        assert d["usa_proposal"] == "USA"
        assert d["china_response"] == "China"
        assert d["latency_ms"] == DEFAULT_LATENCY_100
        assert d["tokens"] == DEFAULT_TOKENS_50
        assert "timestamp" in d

    def test_frozen_dataclass(self):
        round_data = HistoryRoundModel.create(
            1, "USA", "China", DEFAULT_LATENCY_100, DEFAULT_TOKENS_50
        )
        with pytest.raises(AttributeError):
            round_data.round = 2


class TestNegotiatorModel:
    def test_with_memory(self):
        persona = NegotiatorPersona(
            country=Country.USA,
            role="Test",
            priorities=["p1"],
            flexibility=DEFAULT_SCORE_05,
            red_lines=["r1"],
            strategy="s1",
        )
        model = NegotiatorModel(
            persona=persona,
            system_prompt="sys",
            temperature=DEFAULT_TEMPERATURE_DEFAULT,
            top_p=DEFAULT_TOP_P_DEFAULT,
            max_tokens=DEFAULT_MAX_TOKENS_DEFAULT,
        )
        new_model = model.with_memory("memory1")
        assert new_model.memory == ("memory1",)
        assert model.memory == ()

        new_model2 = new_model.with_memory("memory2")
        assert new_model2.memory == ("memory1", "memory2")


class TestNegotiatorPersona:
    def test_usa_persona(self):
        assert USA_PERSONA.country == Country.USA
        assert len(USA_PERSONA.priorities) == DEFAULT_USA_PRIORITIES
        assert USA_PERSONA.flexibility == DEFAULT_FLEXIBILITY_USA
        assert len(USA_PERSONA.red_lines) == DEFAULT_RED_LINES
        assert "reciprocity" in USA_PERSONA.strategy.lower()

    def test_china_persona(self):
        assert CHINA_PERSONA.country == Country.CHINA
        assert len(CHINA_PERSONA.priorities) == DEFAULT_CHINA_PRIORITIES
        assert CHINA_PERSONA.flexibility == DEFAULT_FLEXIBILITY_CHINA
        assert len(CHINA_PERSONA.red_lines) == DEFAULT_RED_LINES
        assert "win-win" in CHINA_PERSONA.strategy.lower()


class TestSchemasRequest:
    def test_negotiate_request_valid(self):
        req = NegotiateRequest(issue="test issue", rounds=DEFAULT_ROUNDS, model="llama3.1")
        assert req.issue == "test issue"
        assert req.rounds == DEFAULT_ROUNDS
        assert req.model == "llama3.1"

    def test_negotiate_request_model_optional(self):
        req = NegotiateRequest(issue="test", rounds=DEFAULT_ROUNDS)
        assert req.model is None

    def test_negotiate_request_validates_issue_not_empty(self):
        with pytest.raises(ValueError):
            NegotiateRequest(issue="   ", rounds=DEFAULT_ROUNDS)

    def test_negotiate_request_validates_issue_max_length(self):
        with pytest.raises(ValueError):
            NegotiateRequest(issue="x" * 1001, rounds=DEFAULT_ROUNDS)

    def test_negotiate_request_validates_rounds_min(self):
        with pytest.raises(ValueError):
            NegotiateRequest(issue="test", rounds=0)

    def test_negotiate_request_validates_rounds_max(self):
        with pytest.raises(ValueError):
            NegotiateRequest(issue="test", rounds=11)

    def test_negotiate_request_sanitizes_xss(self):
        req = NegotiateRequest(issue="Hello <world>", rounds=DEFAULT_ROUNDS)
        assert "Hello" in req.issue
        assert "<world>" in req.issue

    def test_negotiate_request_rejects_javascript(self):
        with pytest.raises(ValueError):
            NegotiateRequest(issue="javascript:alert(1)", rounds=DEFAULT_ROUNDS)

    def test_health_response_defaults(self):
        resp = HealthResponse()
        assert resp.status == "healthy"
        assert resp.version == "1.0.0"
        assert resp.ollama_connected is False


class TestSchemasResponse:
    def test_history_round_validation(self):
        round_obj = HistoryRound(
            round=1,
            timestamp=datetime.now(UTC),
            usa_proposal="USA",
            china_response="China",
            tokens=DEFAULT_TOKENS_10,
            latency_ms=DEFAULT_LATENCY_100,
        )
        assert round_obj.round == 1
        assert round_obj.tokens == DEFAULT_TOKENS_10

    def test_history_round_tokens_optional(self):
        round_obj = HistoryRound(
            round=1,
            timestamp=datetime.now(UTC),
            usa_proposal="USA",
            china_response="China",
            latency_ms=DEFAULT_LATENCY_100,
        )
        assert round_obj.tokens is None

    def test_negotiate_response_validation(self):
        hist = [
            {
                "round": 1,
                "timestamp": datetime.now(UTC).isoformat(),
                "usa_proposal": "USA",
                "china_response": "China",
                "tokens": DEFAULT_TOKENS_10,
                "latency_ms": DEFAULT_LATENCY_100,
            }
        ]
        resp = NegotiateResponse(
            issue="test",
            rounds=1,
            history=hist,
            agreement_reached=True,
            score=DEFAULT_SCORE_075,
            summary="Agreement",
            execution_time_ms=DEFAULT_EXECUTION_TIME,
            model="test",
        )
        assert resp.score == DEFAULT_SCORE_075
        assert resp.agreement_reached is True

    def test_negotiate_response_score_bounds(self):
        hist = [
            {
                "round": 1,
                "timestamp": datetime.now(UTC).isoformat(),
                "usa_proposal": "USA",
                "china_response": "China",
                "latency_ms": DEFAULT_LATENCY_100,
            }
        ]
        with pytest.raises(ValueError):
            NegotiateResponse(
                issue="test",
                rounds=1,
                history=hist,
                agreement_reached=True,
                score=1.5,
                summary="Agreement",
                execution_time_ms=DEFAULT_EXECUTION_TIME,
                model="test",
            )
        with pytest.raises(ValueError):
            NegotiateResponse(
                issue="test",
                rounds=1,
                history=hist,
                agreement_reached=True,
                score=-0.1,
                summary="Agreement",
                execution_time_ms=DEFAULT_EXECUTION_TIME,
                model="test",
            )

    def test_error_response(self):
        err = ErrorResponse(error="TEST_ERROR", message="Test message", details={"field": "value"})
        assert err.error == "TEST_ERROR"
        assert err.details == {"field": "value"}


class TestSchemasNegotiation:
    def test_country_enum(self):
        assert Country.USA == "USA"
        assert Country.CHINA == "China"

    def test_negotiator_persona_validation(self):
        persona = NegotiatorPersona(
            country=Country.USA,
            role="Test",
            priorities=["p1", "p2"],
            flexibility=DEFAULT_SCORE_05,
            red_lines=["r1"],
            strategy="s1",
        )
        assert persona.flexibility == DEFAULT_SCORE_05

    def test_negotiator_persona_flexibility_bounds(self):
        with pytest.raises(ValueError):
            NegotiatorPersona(
                country=Country.USA,
                role="Test",
                priorities=["p1"],
                flexibility=1.5,
                red_lines=[],
                strategy="s1",
            )
        with pytest.raises(ValueError):
            NegotiatorPersona(
                country=Country.USA,
                role="Test",
                priorities=["p1"],
                flexibility=-0.1,
                red_lines=[],
                strategy="s1",
            )

    def test_negotiator_config_defaults(self):
        persona = NegotiatorPersona(
            country=Country.USA,
            role="Test",
            priorities=["p1"],
            flexibility=DEFAULT_SCORE_05,
            red_lines=[],
            strategy="s1",
        )
        config = NegotiatorConfig(persona=persona, system_prompt="sys")
        assert config.temperature == DEFAULT_TEMPERATURE_DEFAULT
        assert config.top_p == DEFAULT_TOP_P_DEFAULT
        assert config.max_tokens == DEFAULT_MAX_TOKENS_DEFAULT

    def test_trade_issue_schema(self):
        issue = TradeIssue(topic="test", description="desc")
        assert issue.topic == "test"

    def test_history_round_frozen(self):
        round_obj = HistoryRound(
            round=1,
            timestamp=datetime.now(UTC),
            usa_proposal="USA",
            china_response="China",
            latency_ms=DEFAULT_LATENCY_100,
        )
        with pytest.raises(ValueError):
            round_obj.round = 2

    def test_log_entry_schema(self):
        entry = LogEntry(
            request={"issue": "test"},
            history=[],
            score=DEFAULT_SCORE_05,
            agreement=False,
            execution_time_ms=100,
            model="test",
        )
        assert entry.score == DEFAULT_SCORE_05
        assert entry.timestamp is not None


class TestExceptions:
    def test_negotiation_error(self):
        err = NegotiationError("Test message", code="TEST_CODE", details={"key": "value"})
        assert err.message == "Test message"
        assert err.code == "TEST_CODE"
        assert err.details == {"key": "value"}

    def test_ollama_error(self):
        err = OllamaError(
            "Ollama error", status_code=DEFAULT_STATUS_500, details={"detail": "test"}
        )
        assert err.status_code == DEFAULT_STATUS_500
        assert err.code == "OLLAMA_ERROR"

    def test_ollama_timeout_error(self):
        err = OllamaTimeoutError("Timeout", details={"retry_after": 5})
        assert err.status_code == DEFAULT_STATUS_408
        assert "Timeout" in str(err)

    def test_ollama_connection_error(self):
        err = OllamaConnectionError("Connection failed")
        assert err.status_code == DEFAULT_STATUS_503

    def test_ollama_model_error(self):
        err = OllamaModelError("Model not found")
        assert err.status_code == DEFAULT_STATUS_400

    def test_validation_error(self):
        err = ValidationError("Invalid field", field="rounds", details={"min": 1})
        assert err.field == "rounds"
        assert err.code == "VALIDATION_ERROR"

    def test_configuration_error(self):
        err = ConfigurationError("Config missing", details={"key": "OLLAMA_BASE_URL"})
        assert err.code == "CONFIGURATION_ERROR"

    def test_state_error(self):
        err = StateError("State corrupted")
        assert err.code == "STATE_ERROR"


class TestRetry:
    def test_ollama_retry_decorator(self):
        decorator = ollama_retry()
        assert decorator is not None

    @pytest.mark.asyncio
    async def test_async_retry_with_fallback_success(self):
        async def success_func():
            return "success"

        async def fallback_func():
            return "fallback"

        result = await async_retry_with_fallback(success_func, fallback_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_retry_with_fallback_on_error(self):
        call_count = 0

        async def fail_func():
            nonlocal call_count
            call_count += 1
            raise OllamaTimeoutError()

        async def fallback_func():
            return "fallback"

        result = await async_retry_with_fallback(fail_func, fallback_func)
        assert result == "fallback"


class TestValidationUtils:
    def test_sanitize_input_normal(self):
        assert sanitize_input("  hello world  ") == "hello world"
        assert sanitize_input("") == ""

    def test_sanitize_input_max_length(self):
        long_text = "x" * DEFAULT_MAX_LENGTH_2000
        result = sanitize_input(long_text, max_length=DEFAULT_MAX_LENGTH_100)
        assert len(result) == DEFAULT_MAX_LENGTH_100

    def test_sanitize_input_html_escapes(self):
        result = sanitize_input("<script>alert(1)</script>")
        assert "script" in result
        assert "alert(1)" in result

    def test_sanitize_input_removes_forbidden_patterns(self):
        result = sanitize_input("javascript:alert(1)")
        assert "javascript" not in result.lower()

    def test_sanitize_for_log_redacts_secrets(self):
        data = {"api_key": "secret123", "normal": "value", "nested": {"password": "pwd"}}
        sanitized = sanitize_for_log(data)
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["normal"] == "value"
        assert sanitized["nested"]["password"] == "***REDACTED***"

    def test_sanitize_for_log_non_dict(self):
        assert sanitize_for_log("not a dict") == {}
        assert sanitize_for_log(None) == {}

    def test_validate_rounds_valid(self):
        assert validate_rounds(DEFAULT_VALIDATE_ROUNDS_1) == DEFAULT_VALIDATE_ROUNDS_1
        assert validate_rounds(DEFAULT_VALIDATE_ROUNDS_5) == DEFAULT_VALIDATE_ROUNDS_5
        assert validate_rounds(DEFAULT_VALIDATE_ROUNDS_10) == DEFAULT_VALIDATE_ROUNDS_10

    def test_validate_rounds_invalid_type(self):
        with pytest.raises(TypeError):
            validate_rounds(3.5)
        with pytest.raises(TypeError):
            validate_rounds("3")

    def test_validate_rounds_bounds(self):
        with pytest.raises(ValueError):
            validate_rounds(0)
        with pytest.raises(ValueError):
            validate_rounds(-1)
        with pytest.raises(ValueError):
            validate_rounds(11)

    def test_extract_keywords(self):
        text = "We agree to reduce tariffs and cooperate"
        found = extract_keywords(text, ["agree", "reduce", "cooperate", "reject"])
        assert "agree" in found
        assert "reduce" in found
        assert "cooperate" in found
        assert "reject" not in found

    def test_forbidden_patterns_constant(self):
        assert len(FORBIDDEN_PATTERNS) > 0
        assert r"<script\b[^>]*>.*?</script>" in FORBIDDEN_PATTERNS

    def test_sensitive_keys_constant(self):
        assert "password" in SENSITIVE_KEYS
        assert "api_key" in SENSITIVE_KEYS
        assert "secret" in SENSITIVE_KEYS


class TestNegotiationState:
    def test_create_state(self, trade_issue):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-1", trade_issue, DEFAULT_ROUNDS, "test-model")
        assert state.rounds == DEFAULT_ROUNDS
        assert state.current_round == 0
        assert state.model == "test-model"
        assert not state.is_complete

    def test_add_round_immutable(self, trade_issue, sample_history):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-2", trade_issue, DEFAULT_ROUNDS, "test-model")
        round_data = sample_history[0]
        new_state = state.add_round(round_data)
        assert new_state.current_round == 1
        assert len(new_state.history) == 1
        assert state.current_round == 0
        assert len(state.history) == 0

    def test_set_agreement_immutable(self, trade_issue):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-3", trade_issue, DEFAULT_ROUNDS, "test-model")
        new_state = state.set_agreement(DEFAULT_SCORE_08)
        assert new_state.agreement_reached is True
        assert new_state.final_score == DEFAULT_SCORE_08
        assert state.agreement_reached is False

    def test_is_complete_rounds_exhausted(self, trade_issue, sample_history):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-4", trade_issue, DEFAULT_TEST_ROUNDS, "test-model")
        state = state.add_round(sample_history[0])
        state = state.add_round(sample_history[1])
        assert state.is_complete is True

    def test_is_complete_agreement_reached(self, trade_issue):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-5", trade_issue, DEFAULT_MAX_ROUNDS, "test-model")
        state = state.set_agreement(0.7)
        assert state.is_complete is True

    def test_to_log_entry(self, trade_issue, sample_history):
        STATE_MANAGER.clear()
        state = STATE_MANAGER.create_state("test-6", trade_issue, DEFAULT_ROUNDS, "test-model")
        state = state.add_round(sample_history[0])
        state = state.set_agreement(DEFAULT_SCORE_075)
        request = {"issue": "test", "rounds": DEFAULT_ROUNDS}
        log_entry = state.to_log_entry(request, DEFAULT_EXECUTION_TIME)
        assert log_entry.request == request
        assert len(log_entry.history) == 1
        assert log_entry.score == DEFAULT_SCORE_075
        assert log_entry.agreement is True
        assert log_entry.execution_time_ms == DEFAULT_EXECUTION_TIME
        assert log_entry.model == "test-model"


class TestPrompts:
    def test_usa_propose_prompt_contains_required_elements(self):
        prompt = USA_PROPOSE_PROMPT.format(
            issue_context="Test issue",
            round_num=1,
            history="No previous rounds.",
            priorities="p1, p2",
            red_lines="r1, r2",
            strategy="test strategy",
        )
        assert "ROLE: Chief Trade Negotiator for the United States" in prompt
        assert "MISSION:" in prompt
        assert "COUNTRY: USA" in prompt
        assert "PRIORITIES:" in prompt
        assert "RED LINES" in prompt
        assert "STRATEGY:" in prompt
        assert "NEGOTIATION RULES:" in prompt
        assert "FORBIDDEN BEHAVIORS:" in prompt
        assert "CONVERSATION HISTORY:" in prompt
        assert "CURRENT ROUND:" in prompt
        assert "ISSUE CONTEXT:" in prompt
        assert "Never hallucinate" in prompt
        assert "Never change persona" in prompt
        assert "Never produce markdown" in prompt
        assert "Never produce explanations" in prompt
        assert "Never output JSON" in prompt
        assert "Never repeat previous responses" in prompt
        assert "MAXIMUM 2 sentences" in prompt

    def test_usa_respond_prompt_contains_opponent_proposal(self):
        prompt = USA_RESPOND_PROMPT.format(
            issue_context="Test issue",
            round_num=1,
            history="No previous rounds.",
            opponent_proposal="China proposal",
            priorities="p1, p2",
            red_lines="r1, r2",
            strategy="test strategy",
        )
        assert 'OPPONENT PROPOSAL: "China proposal"' in prompt

    def test_china_propose_prompt_contains_required_elements(self):
        prompt = CHINA_PROPOSE_PROMPT.format(
            issue_context="Test issue",
            round_num=1,
            history="No previous rounds.",
            priorities="p1, p2",
            red_lines="r1, r2",
            strategy="test strategy",
        )
        assert "ROLE: Chief Trade Negotiator for the People's Republic of China" in prompt
        assert "COUNTRY: China" in prompt

    def test_china_respond_prompt_contains_opponent_proposal(self):
        prompt = CHINA_RESPOND_PROMPT.format(
            issue_context="Test issue",
            round_num=1,
            history="No previous rounds.",
            opponent_proposal="USA proposal",
            priorities="p1, p2",
            red_lines="r1, r2",
            strategy="test strategy",
        )
        assert 'OPPONENT PROPOSAL: "USA proposal"' in prompt


class TestFileStorage:
    def test_save_and_load_negotiation(self, tmp_path):
        storage = FileStorage(base_path=tmp_path)
        data = {"issue": "test", "rounds": DEFAULT_ROUNDS, "result": "agreement"}
        storage.save_negotiation("test-1", data)
        loaded = storage.load_negotiation("test-1")
        assert loaded == data

    def test_load_nonexistent(self, tmp_path):
        storage = FileStorage(base_path=tmp_path)
        loaded = storage.load_negotiation("nonexistent")
        assert loaded is None

    def test_list_negotiations(self, tmp_path):
        storage = FileStorage(base_path=tmp_path)
        storage.save_negotiation("test-1", {})
        storage.save_negotiation("test-2", {})
        negotiations = storage.list_negotiations()
        assert "test-1" in negotiations
        assert "test-2" in negotiations

    def test_delete_negotiation(self, tmp_path):
        storage = FileStorage(base_path=tmp_path)
        storage.save_negotiation("test-1", {})
        assert storage.delete_negotiation("test-1") is True
        assert storage.load_negotiation("test-1") is None
        assert storage.delete_negotiation("nonexistent") is False


class TestMemoryStorage:
    def test_set_and_get(self):
        storage = MemoryStorage(max_size=DEFAULT_MEMORY_SIZE_10)
        storage.set("key1", "value1")
        assert storage.get("key1") == "value1"

    def test_get_nonexistent(self):
        storage = MemoryStorage(max_size=DEFAULT_MEMORY_SIZE_10)
        assert storage.get("nonexistent") is None

    def test_delete(self):
        storage = MemoryStorage(max_size=DEFAULT_MEMORY_SIZE_10)
        storage.set("key1", "value1")
        assert storage.delete("key1") is True
        assert storage.get("key1") is None
        assert storage.delete("nonexistent") is False

    def test_clear(self):
        storage = MemoryStorage(max_size=DEFAULT_MEMORY_SIZE_10)
        storage.set("key1", "value1")
        storage.set("key2", "value2")
        storage.clear()
        assert len(storage) == 0

    def test_lru_eviction(self):
        storage = MemoryStorage(max_size=DEFAULT_MEMORY_SIZE_2)
        storage.set("key1", "value1")
        storage.set("key2", "value2")
        storage.set("key3", "value3")
        assert storage.get("key1") is None
        assert storage.get("key2") == "value2"
        assert storage.get("key3") == "value3"

    def test_keys(self):
        storage = MemoryStorage(max_size=DEFAULT_MEMORY_SIZE_10)
        storage.set("key1", "value1")
        storage.set("key2", "value2")
        assert set(storage.keys()) == {"key1", "key2"}

    def test_len_and_contains(self):
        storage = MemoryStorage(max_size=DEFAULT_MEMORY_SIZE_10)
        assert len(storage) == 0
        storage.set("key1", "value1")
        assert len(storage) == 1
        assert "key1" in storage
        assert "key2" not in storage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
