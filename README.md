# LLM Trade Negotiation Agents

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](https://github.com/Manirider/LLM-Trade-Negotiation-Agents/actions)
[![Coverage](https://img.shields.io/badge/Coverage->95%25-brightgreen.svg)](https://github.com/Manirider/LLM-Trade-Negotiation-Agents/actions)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://github.com/Manirider/LLM-Trade-Negotiation-Agents/pkgs/container/llm-trade-negotiation-agents)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)
[![Type Checking](https://img.shields.io/badge/Type%20Checking-mypy%20strict-blue.svg)](https://github.com/microsoft/pyright)

A production-grade FastAPI service simulating trade negotiations between USA and China agents using LLMs via Ollama. Built with Clean Architecture, comprehensive testing (>95% coverage), and FAANG-level engineering standards.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Docker Setup](#docker-setup)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Example Requests](#example-requests)
- [Example Responses](#example-responses)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Security](#security)
- [Performance](#performance)
- [Design Decisions](#design-decisions)
- [Future Improvements](#future-improvements)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contributing](#contributing)
- [Author](#author)

## Features

- **Dual-Agent Negotiation**: USA and China agents with distinct personas, priorities, and red lines
- **Ollama Integration**: Async client with exponential backoff retry, timeout handling, and fallback responses
- **Heuristic Scoring**: Keyword-based scoring engine (0.0-1.0) with configurable thresholds
- **Immutable State**: Frozen dataclasses with append-only history for thread safety
- **Clean Architecture**: Strict layer separation with dependencies pointing inward
- **Comprehensive Testing**: >95% coverage with unit, integration, and edge case tests
- **Production-Ready Docker**: Multi-stage build (~150MB runtime), health checks, non-root user
- **Structured Logging**: JSON Lines format with automatic secret redaction
- **Input Sanitization**: XSS prevention, prompt injection protection, HTML escaping
- **Type Safety**: Full mypy strict mode compliance with Pydantic v2 validation

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Layer                            │
│  POST /negotiate  │  GET /health  │  Exception Handlers        │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator (<100 lines)                  │
│  Load Issue → Initialize Agents → Run Rounds → Score → Log     │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│   USA Agent     │ │   China Agent   │ │    Scoring Engine       │
│  (Negotiator)   │ │  (Negotiator)   │ │  (Heuristic Keywords)   │
└─────────────────┘ └─────────────────┘ └─────────────────────────┘
           │                    │                    │
           └────────────────────┼────────────────────┘
                                ▼
                     ┌─────────────────────┐
                     │   Ollama Service    │
                     │  (Async, Retry,     │
                     │   Timeout, Fallback)│
                     └─────────────────────┘
```

### Flow Diagram

```
Client Request
      │
      ▼
POST /negotiate {issue, rounds, model?}
      │
      ▼
Validate Request (Pydantic)
      │
      ▼
Create Negotiation State
      │
      ▼
Initialize USA & China Agents
      │
      ▼
┌─────────────────────────────┐
│     For each round:         │
│  1. USA proposes            │
│  2. China responds          │
│  3. Store history (immutable)│
│  4. Score round             │
│  5. Check agreement (≥0.6)  │
└─────────────────────────────┘
      │
      ▼
Generate Final Score & Summary
      │
      ▼
Log to negotiation_log.json
      │
      ▼
Return JSON Response
```

## Folder Structure

```
LLM-Trade-Negotiation-Agents/
├── .github/
│   ├── workflows/           # GitHub Actions CI/CD
│   │   ├── ci.yml          # Lint, type-check, test, Docker build
│   │   └── docker-publish.yml # Release publishing
│   └── dependabot.yml      # Automated dependency updates
├── agents/                 # Negotiation agents (zero FastAPI coupling)
│   ├── base.py            # Abstract BaseNegotiator
│   ├── usa.py             # USANegotiator implementation
│   ├── china.py           # ChinaNegotiator implementation
│   └── factory.py         # AgentFactory for DI
├── core/                   # Core business logic
│   ├── prompts.py         # World-class prompt templates
│   ├── scoring.py         # Heuristic scoring engine
│   ├── state.py           # Immutable state management
│   └── orchestrator.py    # Negotiation orchestrator
├── config/                 # Configuration management
│   └── settings.py        # Pydantic BaseSettings
├── schemas/                # API contracts (Pydantic)
│   ├── request.py         # Request validation
│   ├── response.py        # Response schemas
│   └── negotiation.py     # Domain schemas
├── models/                 # Domain models
│   ├── negotiator.py      # Negotiator personas & config
│   ├── history.py         # Immutable history rounds
│   └── issue.py           # Trade issue model
├── services/               # External services
│   ├── ollama.py          # Async Ollama client with retry
│   └── logging.py         # Structured JSON logging
├── utils/                  # Cross-cutting concerns
│   ├── exceptions.py      # Custom exception hierarchy
│   ├── retry.py           # Exponential backoff
│   └── validation.py      # Input sanitization
├── storage/                # Persistence layer
│   ├── file_storage.py    # File-based storage
│   └── memory_storage.py  # In-memory LRU cache
├── tests/                  # Test suite (>95% coverage)
│   ├── conftest.py        # Pytest fixtures
│   └── test_all.py        # Comprehensive tests
├── main.py                 # FastAPI application
├── Dockerfile              # Multi-stage build
├── docker-compose.yml      # Orchestration
├── pyproject.toml          # Dependencies & tool config
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── LICENSE                 # MIT License
├── CHANGELOG.md            # Version history
├── CONTRIBUTING.md         # Contribution guide
├── SECURITY.md             # Security policy
├── CODE_OF_CONDUCT.md      # Community standards
└── README.md               # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- Ollama running locally or remotely
- Docker & Docker Compose (optional, recommended)

### Local Development

```bash
# Clone and navigate
git clone https://github.com/Manirider/LLM-Trade-Negotiation-Agents.git
cd LLM-Trade-Negotiation-Agents

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Edit .env with your Ollama URL
# OLLAMA_BASE_URL=http://localhost:11434

# Start Ollama (if local)
ollama serve
ollama pull llama3.1

# Run the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Or detached
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

## Installation

### From Source

```bash
git clone https://github.com/Manirider/LLM-Trade-Negotiation-Agents.git
cd LLM-Trade-Negotiation-Agents
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

### Docker Image

```bash
docker pull ghcr.io/manirider/llm-trade-negotiation-agents:latest
```

## Docker Setup

### Dockerfile (Multi-stage)

```dockerfile
# Build stage
FROM python:3.11-slim as builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# Runtime stage
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: "3.8"
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: negotiation-api
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3.1
      - OLLAMA_TIMEOUT=30
      - OLLAMA_MAX_RETRIES=3
      - LOG_FILE=/app/negotiation_log.json
      - LOG_LEVEL=INFO
    volumes:
      - ./negotiation_log.json:/app/negotiation_log.json
      - ./data:/app/data
    depends_on:
      ollama:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  ollama:
    image: ollama/ollama:latest
    container_name: negotiation-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_KEEP_ALIVE=5m
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

volumes:
  ollama_data:
    driver: local
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OLLAMA_BASE_URL` | Yes | - | Ollama server URL (http://host:port) |
| `OLLAMA_MODEL` | No | llama3.1 | Model name to use |
| `OLLAMA_TIMEOUT` | No | 30 | Request timeout in seconds |
| `OLLAMA_MAX_RETRIES` | No | 3 | Max retry attempts |
| `OLLAMA_RETRY_BASE_DELAY` | No | 1.0 | Base delay for exponential backoff |
| `OLLAMA_RETRY_MAX_DELAY` | No | 10.0 | Max delay for retries |
| `HOST` | No | 0.0.0.0 | Server host |
| `PORT` | No | 8000 | Server port |
| `WORKERS` | No | 1 | Number of workers |
| `LOG_FILE` | No | negotiation_log.json | Log file path |
| `LOG_LEVEL` | No | INFO | Log level |
| `LOG_FORMAT` | No | json | Log format (json/text) |
| `DEFAULT_ROUNDS` | No | 5 | Default negotiation rounds |
| `MAX_ROUNDS` | No | 10 | Maximum allowed rounds |
| `MIN_ROUNDS` | No | 1 | Minimum allowed rounds |
| `SECRET_KEY` | No | change-me-in-production | API secret key |
| `API_KEY_ENABLED` | No | false | Enable API key auth |
| `HTTP_CLIENT_POOL_LIMIT` | No | 10 | HTTP connection pool limit |
| `HTTP_CLIENT_KEEPALIVE` | No | 30 | HTTP keepalive seconds |

## API Documentation

### POST /negotiate

Start a trade negotiation between USA and China agents.

**Request Body:**

```json
{
  "issue": "Reduce tariffs on semiconductor exports while protecting IP rights",
  "rounds": 5,
  "model": "llama3.1"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issue` | string | Yes | Trade issue to negotiate (1-1000 chars) |
| `rounds` | integer | Yes | Number of negotiation rounds (1-10) |
| `model` | string | No | Override default Ollama model |

### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ollama_connected": true
}
```

## Example Requests

### Basic Negotiation

```bash
curl -X POST http://localhost:8000/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "issue": "Reduce tariffs on semiconductor exports while protecting IP rights",
    "rounds": 5
  }'
```

### With Custom Model

```bash
curl -X POST http://localhost:8000/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "issue": "Establish fair market access for agricultural products",
    "rounds": 3,
    "model": "llama3.1:8b"
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Example Responses

### Successful Negotiation (Agreement Reached)

```json
{
  "issue": "Reduce tariffs on semiconductor exports while protecting IP rights",
  "rounds": 3,
  "history": [
    {
      "round": 1,
      "timestamp": "2024-01-15T10:30:00.000Z",
      "usa_proposal": "We propose reducing tariffs on semiconductors by 50% in exchange for stronger IP enforcement.",
      "china_response": "We accept tariff reduction but require reciprocal market access for Chinese tech firms.",
      "tokens": 45,
      "latency_ms": 234
    },
    {
      "round": 2,
      "timestamp": "2024-01-15T10:30:01.000Z",
      "usa_proposal": "We can offer phased market access tied to verifiable IP protection milestones.",
      "china_response": "We agree to phased approach with joint verification mechanism.",
      "tokens": 52,
      "latency_ms": 198
    },
    {
      "round": 3,
      "timestamp": "2024-01-15T10:30:02.000Z",
      "usa_proposal": "Final proposal: 50% tariff cut over 3 years with quarterly IP compliance reviews.",
      "china_response": "We accept the final terms. Agreement reached.",
      "tokens": 38,
      "latency_ms": 167
    }
  ],
  "agreement_reached": true,
  "score": 0.72,
  "summary": "Agreement reached with moderate compromise",
  "execution_time_ms": 1250,
  "model": "llama3.1"
}
```

### Negotiation Without Agreement (Deadlock)

```json
{
  "issue": "Complete removal of all tariffs without conditions",
  "rounds": 5,
  "history": [
    {
      "round": 1,
      "timestamp": "2024-01-15T10:30:00.000Z",
      "usa_proposal": "We demand complete tariff removal as a prerequisite for further talks.",
      "china_response": "We reject unilateral demands. Negotiations require mutual concessions.",
      "tokens": 42,
      "latency_ms": 245
    },
    {
      "round": 2,
      "timestamp": "2024-01-15T10:30:01.000Z",
      "usa_proposal": "Our position remains firm. No agreement without full tariff elimination.",
      "china_response": "We cannot accept ultimatums. This violates our red lines.",
      "tokens": 39,
      "latency_ms": 189
    }
  ],
  "agreement_reached": false,
  "score": 0.25,
  "summary": "Deadlock: fundamental disagreements persist",
  "execution_time_ms": 980,
  "model": "llama3.1"
}
```

### Error Responses

**Validation Error (422):**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "errors": [
      {"field": "issue", "message": "Issue cannot be empty or whitespace only"},
      {"field": "rounds", "message": "Input should be greater than or equal to 1"}
    ]
  }
}
```

**Ollama Timeout (504):**
```json
{
  "error": "OLLAMA_TIMEOUT",
  "message": "LLM service timed out. Please try again.",
  "details": {"retry_after": 10.0}
}
```

**Ollama Unavailable (503):**
```json
{
  "error": "OLLAMA_UNAVAILABLE",
  "message": "LLM service is currently unavailable.",
  "details": {}
}
```

**Invalid Model (400):**
```json
{
  "error": "INVALID_MODEL",
  "message": "Model 'invalid-model' not found",
  "details": {}
}
```

## Testing

```bash
# Run all tests with coverage
pytest --cov=agents --cov=core --cov=config --cov=schemas --cov=models --cov=services --cov=utils --cov=storage --cov-fail-under=95

# Run specific test categories
pytest tests/test_all.py::TestHealthEndpoint -v
pytest tests/test_all.py::TestNegotiateEndpoint -v
pytest tests/test_all.py::TestScoringEngine -v
pytest tests/test_all.py::TestStateManager -v
pytest tests/test_all.py::TestAgentFactory -v
pytest tests/test_all.py::TestOllamaService -v
pytest tests/test_all.py::TestLoggingService -v

# Run with HTML coverage report
pytest --cov=... --cov-report=html
open htmlcov/index.html
```

### Test Coverage Targets

- **Overall**: >95%
- **Critical paths**: 100% (orchestrator, scoring, state, agents)
- **Error handling**: All exception types tested
- **Edge cases**: Invalid inputs, timeouts, malformed responses

## Code Quality

```bash
# Format code
black .
isort .

# Lint
ruff check .

# Type check
mypy --strict .

# Pre-commit (install first: pip install pre-commit)
pre-commit run --all-files
```

### Configuration

**pyproject.toml** includes:
- Ruff (linting) with comprehensive rule set
- Black (formatting) with 100-char line length
- isort (import sorting) with Black profile
- mypy (type checking) in strict mode
- pytest with coverage requirements

## Security

- **Input Validation**: All endpoints validate and sanitize inputs
- **Prompt Injection Prevention**: Strict templates with forbidden behaviors
- **HTML Escaping**: User inputs escaped before processing
- **Pattern Filtering**: XSS, code injection patterns blocked
- **Log Sanitization**: Secrets automatically redacted from logs
- **No Hardcoded Secrets**: All configuration via environment variables
- **Structured Error Responses**: No stack traces exposed to clients

## Performance

- **Async Throughout**: httpx.AsyncClient, async endpoints
- **Connection Pooling**: Configurable limits via `HTTP_CLIENT_POOL_LIMIT`
- **Configuration Caching**: Loaded once at startup via `@lru_cache`
- **Immutable State**: No locking needed, thread-safe
- **Optimized Prompts**: Pre-compiled templates, constrained output
- **Fallback Responses**: Resilience when Ollama unavailable
- **Multi-stage Docker**: ~150MB runtime image

## Design Decisions

1. **Clean Architecture**: Strict layer separation, dependencies point inward
2. **Negotiator Isolation**: Zero knowledge of FastAPI/HTTP
3. **Immutable State**: Frozen dataclasses, append-only history
4. **Dependency Injection**: AgentFactory for testability
5. **Heuristic Scoring**: No LLM calls for scoring (fast, deterministic)
6. **Structured Logging**: JSON lines format for observability
7. **Multi-stage Docker**: Small runtime image (~150MB)
8. **Health Checks**: Both API and Ollama monitored

## Future Improvements

- [ ] WebSocket support for real-time negotiation streaming
- [ ] Multiple negotiation strategies (competitive, collaborative, compromise)
- [ ] Persistent negotiation history with query API
- [ ] Rate limiting & authentication
- [ ] Multi-model ensemble for robustness
- [ ] Prompt optimization via A/B testing
- [ ] Metrics export (Prometheus/OpenTelemetry)
- [ ] Horizontal scaling with Redis state backend

## Troubleshooting

### Ollama Connection Failed

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify model exists
ollama list

# Check network (Docker)
docker-compose logs ollama
```

### Low Score/Agreement Issues

- Adjust agent flexibility in `models/negotiator.py`
- Modify prompt templates in `core/prompts.py`
- Tune scoring keywords in `core/scoring.py`

### High Latency

- Reduce `OLLAMA_TIMEOUT`
- Lower `max_tokens` in agent config
- Use smaller model (e.g., `llama3.1:8b`)

### Memory Growth

- Check `MAX_ROUNDS` limit
- Verify history immutability
- Monitor `STATE_MANAGER` cleanup

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run quality checks (`black . && isort . && ruff check . && mypy --strict .`)
4. Run tests (`pytest --cov-fail-under=95`)
5. Submit PR with description

## Author

**MANIKANTA SURYASAI**  
AIML DEVELOPER | ENGINEER

- GitHub: [@Manirider](https://github.com/Manirider)
- Repository: [LLM-Trade-Negotiation-Agents](https://github.com/Manirider/LLM-Trade-Negotiation-Agents)