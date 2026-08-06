# LLM-Trade-Negotiation-Agents - Comprehensive Requirements Checklist

## 1. PROJECT STRUCTURE & ARCHITECTURE
- [ ] Clean Architecture with layers: agents/, core/, config/, schemas/, models/, services/, utils/, storage/, tests/
- [ ] SOLID principles applied throughout
- [ ] Dependency Injection where appropriate
- [ ] No tight coupling between layers
- [ ] Separation of concerns: business logic, routing, configuration, LLM interaction, state management, logging, scoring, prompt generation, history management, response parsing, retry logic, error handling

## 2. FASTAPI BACKEND
- [ ] Async everywhere (async/await)
- [ ] Never block event loop
- [ ] Use httpx.AsyncClient for HTTP calls
- [ ] Lifespan startup/shutdown events
- [ ] Load configuration once at startup
- [ ] Environment variables for all config
- [ ] Strong Pydantic validation on all inputs/outputs
- [ ] Custom exception handlers
- [ ] Typed responses with proper HTTP status codes
- [ ] Request validation
- [ ] Graceful failures with proper error responses

## 3. NEGOTIATION ENGINE (Negotiator Class)
- [ ] Negotiator class with:
  - [ ] persona
  - [ ] country
  - [ ] priorities
  - [ ] flexibility
  - [ ] red lines
  - [ ] strategy
  - [ ] memory
  - [ ] conversation history
  - [ ] prompt builder
  - [ ] response parser
  - [ ] proposal generator
- [ ] Negotiator knows NOTHING about FastAPI
- [ ] Pure negotiation logic only

## 4. PROMPT ENGINEERING
- [ ] World-class prompts including:
  - [ ] Role
  - [ ] Mission
  - [ ] Country
  - [ ] Priorities
  - [ ] Flexibility
  - [ ] Negotiation Rules
  - [ ] Forbidden Behaviors
  - [ ] Conversation History
  - [ ] Opponent Proposal
  - [ ] Current Round
  - [ ] Desired Output Format
- [ ] LLM constraints enforced:
  - [ ] Never hallucinate
  - [ ] Never change persona
  - [ ] Never produce markdown
  - [ ] Never produce explanations
  - [ ] Never output JSON unless requested
  - [ ] Never repeat previous responses
  - [ ] Keep answers below two sentences
  - [ ] Deterministic generation (temperature 0.1, top_p 0.9)

## 5. ORCHESTRATOR
- [ ] FastAPI endpoint acts as negotiation orchestrator
- [ ] Flow: Load issue → Load rounds → Initialize agents → Run loop
- [ ] Loop: USA Proposal → China Response → Store history → Update memory → Calculate compromise → Generate final outcome → Persist logs → Return JSON
- [ ] Orchestrator under 100 lines

## 6. STATE MANAGEMENT
- [ ] History is immutable
- [ ] Each round stores: round, timestamp, USA proposal, China response, tokens (if available), latency
- [ ] History is append-only

## 7. LOGGING
- [ ] Structured logging to negotiation_log.json
- [ ] Each log contains: request, history, score, agreement, execution time, model, timestamp

## 8. SCORING ENGINE
- [ ] Heuristic engine (not toy)
- [ ] Positive keywords: agreement, accept, reduce, lower, support, cooperate, shared, mutual
- [ ] Negative keywords: reject, deny, refuse, oppose, impossible, never, conflict, deadlock
- [ ] Normalize score 0.0–1.0
- [ ] Return: agreement_reached, score, summary

## 9. ERROR HANDLING
- [ ] Retry Ollama automatically with exponential backoff
- [ ] Timeout protection
- [ ] Connection errors handled
- [ ] Malformed JSON handled
- [ ] Empty response handled
- [ ] Invalid model handled
- [ ] Fallback response provided
- [ ] No crashes ever

## 10. OLLAMA INTEGRATION
- [ ] Read OLLAMA_BASE_URL from environment
- [ ] Never hardcode URLs
- [ ] Support model override via env
- [ ] Configurable timeout

## 11. DOCKER
- [ ] python:3.11-slim base image
- [ ] Multi-stage build
- [ ] Small final image
- [ ] Healthcheck endpoint
- [ ] Proper cache layers
- [ ] Pinned dependencies
- [ ] docker-compose up works with no manual steps

## 12. TESTING
- [ ] Pytest coverage >95%
- [ ] Tests for:
  - [ ] Health endpoint
  - [ ] Startup
  - [ ] POST /negotiate
  - [ ] Invalid payload
  - [ ] Missing issue
  - [ ] Negative rounds
  - [ ] Round count validation
  - [ ] History length validation
  - [ ] Score range (0.0-1.0)
  - [ ] Agreement boolean
  - [ ] Logging verification
  - [ ] Priority references in responses
  - [ ] Error handling
  - [ ] Mock Ollama
  - [ ] Timeout handling
  - [ ] Malformed responses

## 13. DOCUMENTATION
- [ ] Portfolio-quality README with:
  - [ ] Architecture Diagram
  - [ ] Flow Diagram
  - [ ] Folder Structure
  - [ ] Setup instructions
  - [ ] Docker usage
  - [ ] API documentation
  - [ ] Environment variables
  - [ ] Testing guide
  - [ ] Troubleshooting
  - [ ] Design Decisions
  - [ ] Future Improvements
  - [ ] Performance considerations

## 14. CODE QUALITY
- [ ] Black formatting
- [ ] isort import sorting
- [ ] ruff linting
- [ ] mypy compatible typing
- [ ] Docstrings on all public APIs
- [ ] Comments only where needed
- [ ] Meaningful variable names
- [ ] No duplicated code
- [ ] No magic numbers
- [ ] No dead code

## 15. PERFORMANCE
- [ ] Avoid repeated JSON loading
- [ ] Reuse HTTP client (connection pooling)
- [ ] Reuse configuration
- [ ] Avoid unnecessary allocations
- [ ] Optimize loops

## 16. SECURITY
- [ ] Never commit secrets
- [ ] Validate all input
- [ ] Prevent prompt injection
- [ ] Escape user content
- [ ] Sanitize logs

## 17. FINAL VALIDATION
- [ ] All tests pass mentally
- [ ] Every evaluator requirement verified
- [ ] Every response schema checked
- [ ] Docker build works
- [ ] Docker Compose works
- [ ] README complete
- [ ] .env.example present
- [ ] API contract verified
- [ ] Logging verified
- [ ] Tests pass
- [ ] Folder structure correct
- [ ] Trade positions work
- [ ] Negotiator works
- [ ] Compromise score works
- [ ] State management works

## 18. SELF-REVIEW
- [ ] Architecture flaws identified and fixed
- [ ] Performance issues identified and fixed
- [ ] Security issues identified and fixed
- [ ] Edge cases handled
- [ ] Race conditions prevented
- [ ] Style issues fixed
- [ ] Maintainability problems fixed
- [ ] Test gaps filled
- [ ] Documentation gaps filled
- [ ] Zero major issues remaining