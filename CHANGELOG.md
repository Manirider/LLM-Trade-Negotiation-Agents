# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added
- Initial release of LLM Trade Negotiation Agents
- FastAPI-based REST API for trade negotiation simulation
- USA and China negotiator agents with distinct personas
- Ollama integration with async client, retry logic, and fallback responses
- Heuristic keyword-based scoring engine (0.0-1.0)
- Immutable state management with append-only history
- Structured JSON logging to file
- Comprehensive test suite (>95% coverage)
- Multi-stage Docker build (~150MB runtime image)
- Docker Compose orchestration with health checks
- Clean Architecture with strict layer separation
- Dependency injection via AgentFactory
- Pydantic v2 validation and settings management
- Custom exception hierarchy with structured error responses
- Input sanitization and prompt injection prevention
- Configuration via environment variables (.env.example provided)

### Architecture
- **agents/**: Negotiation agents (zero FastAPI coupling)
- **core/**: Business logic (orchestrator, scoring, state, prompts)
- **config/**: Pydantic settings management
- **schemas/**: API contracts and domain models
- **models/**: Domain models (negotiator, history, issue)
- **services/**: External services (Ollama, logging)
- **utils/**: Cross-cutting concerns (exceptions, retry, validation)
- **storage/**: Persistence layer (file and memory)

### Testing
- Unit tests for all core components
- Integration tests for API endpoints
- Mock-based testing for Ollama service
- Coverage targets: >95% overall, 100% critical paths
- HTML coverage reports

### Security
- No hardcoded secrets
- Environment-based configuration
- Input validation on all endpoints
- Prompt injection prevention
- Log sanitization (secrets redacted)
- HTML escaping and pattern filtering

### Performance
- Async throughout (httpx.AsyncClient, async endpoints)
- Connection pooling with configurable limits
- Configuration loaded once at startup
- Immutable state (no locking needed)
- Optimized prompt templates
- Fallback responses for resilience

## [Unreleased]

### Planned
- WebSocket support for real-time negotiation streaming
- Multiple negotiation strategies (competitive, collaborative, compromise)
- Persistent negotiation history with query API
- Rate limiting & authentication
- Multi-model ensemble for robustness
- Prompt optimization via A/B testing
- Metrics export (Prometheus/OpenTelemetry)
- Horizontal scaling with Redis state backend