# LLM-Trade-Negotiation-Agents - Architecture Design

## Overview
Clean Architecture implementation with strict separation of concerns for a trade negotiation system between USA and China agents using LLM (Ollama).

## Folder Structure
```
LLM-Trade-Negotiation-Agents/
├── agents/                 # Negotiation agents (USA, China)
│   ├── __init__.py
│   ├── base.py            # Base Negotiator abstract class
│   ├── usa.py             # USA negotiator implementation
│   ├── china.py           # China negotiator implementation
│   └── factory.py         # Agent factory for DI
├── core/                   # Core business logic
│   ├── __init__.py
│   ├── orchestrator.py    # Negotiation orchestrator (<100 lines)
│   ├── scoring.py         # Heuristic scoring engine
│   ├── state.py           # Immutable state management
│   └── prompts.py         # Prompt engineering templates
├── config/                 # Configuration management
│   ├── __init__.py
│   ├── settings.py        # Pydantic settings (env vars)
│   └── ollama.py          # Ollama client config
├── schemas/                # Pydantic schemas (API contracts)
│   ├── __init__.py
│   ├── request.py         # Request schemas
│   ├── response.py        # Response schemas
│   └── negotiation.py     # Negotiation domain schemas
├── models/                 # Domain models
│   ├── __init__.py
│   ├── negotiator.py      # Negotiator domain model
│   ├── history.py         # History round model
│   └── issue.py           # Trade issue model
├── services/               # External services
│   ├── __init__.py
│   ├── ollama.py          # Ollama async client with retry
│   └── logging.py         # Structured logging service
├── utils/                  # Utilities
│   ├── __init__.py
│   ├── exceptions.py      # Custom exceptions
│   ├── retry.py           # Retry logic with exponential backoff
│   └── validation.py      # Input validation helpers
├── storage/                # Persistence layer
│   ├── __init__.py
│   ├── file_storage.py    # File-based storage for logs/history
│   └── memory_storage.py  # In-memory storage for state
├── tests/                  # Test suite (>95% coverage)
│   ├── __init__.py
│   ├── conftest.py        # Pytest fixtures
│   ├── test_health.py
│   ├── test_negotiate.py
│   ├── test_scoring.py
│   ├── test_orchestrator.py
│   ├── test_ollama.py
│   ├── test_state.py
│   └── test_integration.py
├── main.py                 # FastAPI application entry point
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── README.md
└── REQUIREMENTS_CHECKLIST.md
```

## Layer Responsibilities

### 1. Agents Layer (`agents/`)
- **Purpose**: Pure negotiation logic, zero FastAPI knowledge
- **BaseNegotiator**: Abstract class defining negotiator interface
- **USANegotiator/ChinaNegotiator**: Concrete implementations with country-specific personas
- **AgentFactory**: Dependency injection for negotiator creation

### 2. Core Layer (`core/`)
- **Orchestrator**: Coordinates negotiation flow (<100 lines)
- **ScoringEngine**: Heuristic scoring with keyword analysis
- **StateManager**: Immutable append-only history management
- **PromptTemplates**: World-class prompt engineering

### 3. Config Layer (`config/`)
- **Settings**: Pydantic BaseSettings for all env vars
- **OllamaConfig**: Ollama-specific configuration

### 4. Schemas Layer (`schemas/`)
- **Request/Response**: API contract validation
- **Negotiation**: Domain schemas for negotiation data

### 5. Models Layer (`models/`)
- **Domain Models**: Rich domain objects with behavior
- **Immutable History**: Round-based immutable records

### 6. Services Layer (`services/`)
- **OllamaService**: Async HTTP client with retry/timeout
- **LoggingService**: Structured JSON logging

### 7. Utils Layer (`utils/`)
- **Exceptions**: Custom exception hierarchy
- **Retry**: Exponential backoff decorator
- **Validation**: Input sanitization

### 8. Storage Layer (`storage/`)
- **FileStorage**: Persistent logging to negotiation_log.json
- **MemoryStorage**: In-memory state for active negotiations

## Data Flow

```
POST /negotiate
    │
    ▼
FastAPI Route (main.py)
    │
    ▼
Orchestrator (core/orchestrator.py)
    │
    ├─► Load Issue & Config
    ├─► AgentFactory.create_agents() → agents/
    ├─► Loop rounds:
    │     ├─► USA Negotiator.propose() → agents/usa.py
    │     ├─► China Negotiator.respond() → agents/china.py
    │     ├─► StateManager.append_round() → core/state.py
    │     └─► ScoringEngine.score() → core/scoring.py
    ├─► Generate final outcome
    ├─► LoggingService.log() → services/logging.py
    └─► Return NegotiationResponse
```

## Key Design Decisions

1. **Negotiator Isolation**: Negotiators know nothing about HTTP, FastAPI, or infrastructure
2. **Immutable State**: History rounds are frozen dataclasses, append-only
3. **Dependency Injection**: AgentFactory provides negotiators, enabling testing
4. **Async Throughout**: httpx.AsyncClient, async lifespan, async endpoints
5. **Configuration Once**: Settings loaded at startup, cached
6. **Structured Logging**: Every negotiation logged to JSON with full context
7. **Heuristic Scoring**: Keyword-based with normalization, no LLM calls for scoring
8. **Retry with Backoff**: Ollama calls wrapped with exponential backoff
9. **Prompt Engineering**: Templates with strict output constraints
10. **Security**: Input validation, prompt injection prevention, log sanitization

## API Contract

### POST /negotiate
**Request**:
```json
{
  "issue": "string",
  "rounds": "int (1-10)",
  "model": "string (optional)"
}
```

**Response**:
```json
{
  "issue": "string",
  "rounds": "int",
  "history": [
    {
      "round": "int",
      "timestamp": "ISO8601",
      "usa_proposal": "string",
      "china_response": "string",
      "tokens": "int|null",
      "latency_ms": "int"
    }
  ],
  "agreement_reached": "boolean",
  "score": "float (0.0-1.0)",
  "summary": "string",
  "execution_time_ms": "int",
  "model": "string"
}
```

## Environment Variables
- `OLLAMA_BASE_URL` (required): Ollama server URL
- `OLLAMA_MODEL` (default: "llama3.1"): Model to use
- `OLLAMA_TIMEOUT` (default: 30): Request timeout seconds
- `OLLAMA_MAX_RETRIES` (default: 3): Max retry attempts
- `LOG_FILE` (default: "negotiation_log.json"): Log file path
- `HOST` (default: "0.0.0.0"): Server host
- `PORT` (default: 8000): Server port

## Error Handling Strategy
- Custom exception hierarchy in `utils/exceptions.py`
- Global exception handlers in `main.py`
- Ollama-specific: retry with exponential backoff, fallback response
- Validation errors: 422 with details
- Internal errors: 500 with sanitized message

## Testing Strategy
- Unit tests for each layer (agents, core, services, utils)
- Integration tests for full negotiation flow
- Mock Ollama service for deterministic tests
- Coverage target: >95%
- Test fixtures in `tests/conftest.py`

## Docker Strategy
- Multi-stage build: builder → runtime
- python:3.11-slim base
- Non-root user
- Healthcheck on /health
- Pinned dependencies via uv/poetry
- docker-compose for orchestration

## Security Measures
- Input validation on all schemas
- Prompt injection prevention via strict templates
- Log sanitization (no secrets in logs)
- No hardcoded secrets
- Environment-based configuration