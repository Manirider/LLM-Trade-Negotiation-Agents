# LLM-Trade-Negotiation-Agents - Edge Cases & Evaluation Criteria

## Edge Cases

### 1. Input Validation Edge Cases
- [ ] Empty issue string
- [ ] Issue string > 1000 characters
- [ ] Rounds = 0 or negative
- [ ] Rounds > 10 (max limit)
- [ ] Rounds as float (e.g., 3.5)
- [ ] Missing issue field in request
- [ ] Extra unknown fields in request
- [ ] Invalid model name (not in Ollama)
- [ ] Unicode/emoji in issue
- [ ] SQL injection attempts in issue
- [ ] Prompt injection attempts in issue

### 2. Ollama/LLM Edge Cases
- [ ] Ollama server unavailable (connection refused)
- [ ] Ollama timeout (request exceeds timeout)
- [ ] Ollama returns empty response
- [ ] Ollama returns malformed JSON
- [ ] Ollama returns markdown despite instructions
- [ ] Ollama returns explanation text
- [ ] Ollama returns >2 sentences
- [ ] Ollama changes persona mid-conversation
- [ ] Ollama hallucinates facts
- [ ] Ollama repeats previous response
- [ ] Model not loaded in Ollama
- [ ] Ollama returns 500/503
- [ ] Network partition during streaming
- [ ] Token limit exceeded

### 3. Negotiation Logic Edge Cases
- [ ] USA proposes, China responds with exact same text
- [ ] Immediate agreement in round 1
- [ ] Deadlock: both parties refuse all proposals
- [ ] Red line violation by either party
- [ ] Flexibility = 0 (completely rigid)
- [ ] Flexibility = 1 (completely flexible)
- [ ] Priority conflict: USA priority contradicts China priority
- [ ] Round limit reached without agreement
- [ ] History grows beyond memory limits
- [ ] Tokens not returned by Ollama
- [ ] Latency measurement failure

### 4. State Management Edge Cases
- [ ] Concurrent negotiations (race conditions)
- [ ] History mutation attempt
- [ ] Round number mismatch
- [ ] Timestamp precision issues
- [ ] Memory storage vs file storage sync
- [ ] Large history serialization
- [ ] Corrupted log file

### 5. Scoring Edge Cases
- [ ] All positive keywords, no negative
- [ ] All negative keywords, no positive
- [ ] Equal positive and negative keywords
- [ ] Keywords in different languages
- [ ] Keywords as substrings (e.g., "disagreement" contains "agreement")
- [ ] Case sensitivity
- [ ] Empty response scoring
- [ ] Score exactly 0.0 or 1.0

### 6. Logging Edge Cases
- [ ] Log file permission denied
- [ ] Disk full during logging
- [ ] Log file corruption
- [ ] Concurrent log writes
- [ ] Log rotation needed
- [ ] Sensitive data in logs (sanitization)

### 7. Docker/Deployment Edge Cases
- [ ] Healthcheck fails
- [ ] Container OOM kill
- [ ] Port already in use
- [ ] Environment variable missing
- [ ] Volume mount permission issues
- [ ] Network connectivity to Ollama

### 8. Performance Edge Cases
- [ ] 10 rounds with max tokens
- [ ] Rapid sequential requests
- [ ] Memory leak in history accumulation
- [ ] HTTP client connection pool exhaustion
- [ ] Configuration reload on each request

## Evaluation Criteria (Must Pass All)

### Functional Requirements
- [ ] POST /negotiate accepts valid request, returns valid response
- [ ] Response matches exact schema (all fields, correct types)
- [ ] History contains exactly `rounds` entries
- [ ] Each history entry has: round, timestamp, usa_proposal, china_response, tokens, latency_ms
- [ ] agreement_reached is boolean
- [ ] score is float 0.0-1.0
- [ ] summary is non-empty string
- [ ] execution_time_ms is positive integer
- [ ] model matches requested or default
- [ ] USA always proposes first in each round
- [ ] China always responds to USA proposal
- [ ] Negotiation completes within reasonable time

### Non-Functional Requirements
- [ ] All endpoints async, no blocking calls
- [ ] Pydantic validation on all inputs/outputs
- [ ] Custom exception handlers return proper HTTP codes
- [ ] Structured logging to negotiation_log.json
- [ ] Each log entry has: request, history, score, agreement, execution_time, model, timestamp
- [ ] Ollama config from environment variables only
- [ ] Retry with exponential backoff (3 retries default)
- [ ] Timeout configurable, enforced
- [ ] Fallback response on total failure
- [ ] No crashes on any input

### Architecture Requirements
- [ ] Clean Architecture layers separated
- [ ] Negotiator classes know nothing about FastAPI
- [ ] Orchestrator < 100 lines
- [ ] Dependency Injection via AgentFactory
- [ ] Immutable history (frozen dataclasses)
- [ ] Append-only history storage
- [ ] Prompt templates in core/prompts.py
- [ ] Scoring engine in core/scoring.py
- [ ] Ollama service in services/ollama.py
- [ ] Logging service in services/logging.py

### Code Quality Requirements
- [ ] Black formatted
- [ ] isort organized imports
- [ ] ruff clean (no lint errors)
- [ ] mypy strict mode passes
- [ ] Docstrings on all public classes/methods
- [ ] No TODO comments
- [ ] No placeholder code
- [ ] No magic numbers (constants in config)
- [ ] No dead code
- [ ] Meaningful variable names

### Testing Requirements
- [ ] Coverage > 95%
- [ ] Health endpoint test
- [ ] Startup test
- [ ] POST /negotiate success test
- [ ] Invalid payload test (422)
- [ ] Missing issue test (422)
- [ ] Negative rounds test (422)
- [ ] Round count validation test
- [ ] History length = rounds test
- [ ] Score range 0.0-1.0 test
- [ ] Agreement bool test
- [ ] Logging verification test
- [ ] Priority references in responses test
- [ ] Error handling tests
- [ ] Mock Ollama test
- [ ] Timeout test
- [ ] Malformed response test

### Docker Requirements
- [ ] docker-compose up starts all services
- [ ] Healthcheck passes
- [ ] Image size < 500MB
- [ ] Multi-stage build
- [ ] Pinned dependencies
- [ ] Non-root user
- [ ] .env.example present

### Documentation Requirements
- [ ] README with all required sections
- [ ] Architecture diagram
- [ ] Flow diagram
- [ ] Setup instructions
- [ ] Docker usage
- [ ] API documentation
- [ ] Environment variables
- [ ] Testing guide
- [ ] Troubleshooting
- [ ] Design decisions
- [ ] Future improvements
- [ ] Performance notes

## Perfect Score Guarantee Strategy

### 1. Automated Validation Pipeline
```bash
# Pre-commit checks
ruff check .
black --check .
isort --check .
mypy --strict .
pytest --cov=agents --cov=core --cov=services --cov=utils --cov=storage --cov=config --cov=schemas --cov=models --cov-fail-under=95

# Docker validation
docker build -t negotiation-api .
docker run --rm negotiation-api python -m pytest
docker-compose up -d
curl -f http://localhost:8000/health
curl -X POST http://localhost:8000/negotiate -d '{"issue": "tariffs", "rounds": 3}'
docker-compose down
```

### 2. Contract Testing
- Schema validation on every request/response
- Property-based testing for scoring engine
- Mutation testing for critical paths

### 3. Chaos Testing
- Simulate Ollama failures
- Network latency injection
- Concurrent request load testing
- Memory pressure testing

### 4. Security Validation
- Bandit security scan
- Dependency vulnerability scan (safety/audit)
- Prompt injection test suite
- Log sanitization verification

### 5. Performance Benchmarks
- Latency p50, p95, p99 < 500ms per round
- Memory growth < 10MB per negotiation
- CPU usage < 50% under load
- Connection pool reuse verified

### 6. Documentation Completeness Check
- All public APIs documented
- Architecture diagrams current
- README matches implementation
- Environment variables documented
- Troubleshooting covers common issues

## Self-Review Checklist (Pre-Submission)

### Architecture
- [ ] No circular dependencies
- [ ] Each layer only depends on inner layers
- [ ] Interfaces defined in core, implemented in outer layers
- [ ] No God classes
- [ ] Single Responsibility Principle throughout

### Performance
- [ ] HTTP client reused (not created per request)
- [ ] Config loaded once at startup
- [ ] No repeated file I/O in hot path
- [ ] Async throughout, no sync blocking
- [ ] Connection pooling configured

### Security
- [ ] No secrets in code or logs
- [ ] Input validation at boundary
- [ ] Output encoding for logs
- [ ] Prompt templates prevent injection
- [ ] Error messages don't leak internals

### Maintainability
- [ ] Clear module boundaries
- [ ] Descriptive names
- [ ] Consistent patterns
- [ ] Easy to add new negotiator
- [ ] Easy to swap LLM provider
- [ ] Easy to change storage backend

### Testing
- [ ] Unit tests isolated (mocked dependencies)
- [ ] Integration tests real dependencies
- [ ] Fixtures reusable
- [ ] Tests deterministic
- [ ] Tests fast (< 30s total)
- [ ] Edge cases covered

## Definition of Done
All checklist items ✅ + All tests pass + Docker works + Documentation complete + Zero ruff/mypy/black errors + Coverage > 95%