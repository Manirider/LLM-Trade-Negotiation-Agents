# Contributing Guide

Thank you for your interest in contributing to LLM Trade Negotiation Agents! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.11+
- Ollama (for local LLM inference)
- Docker & Docker Compose (optional)

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/Manirider/LLM-Trade-Negotiation-Agents.git
cd LLM-Trade-Negotiation-Agents

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Start Ollama (if running locally)
ollama serve
ollama pull llama3.1

# Run the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates
- `refactor/*` - Code refactoring

### Making Changes

1. Create a feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the code style guidelines

3. Run quality checks before committing
   ```bash
   # Format code
   black .
   isort .

   # Lint
   ruff check .

   # Type check
   mypy --strict .

   # Run tests
   pytest --cov-fail-under=95
   ```

4. Write tests for new functionality

5. Update documentation if needed

6. Submit a Pull Request

## Code Style

### Python

- **Formatter**: Black (line length 100)
- **Import sorting**: isort (Black profile)
- **Linter**: Ruff (comprehensive rule set)
- **Type checker**: mypy (strict mode)

Run all checks:
```bash
black . && isort . && ruff check . && mypy --strict .
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): brief description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(agents): add EU negotiator agent
fix(scoring): handle edge case with empty history
docs(readme): update Docker setup instructions
test(orchestrator): add integration test for agreement detection
```

### Code Quality Standards

- **Test coverage**: >95% overall, 100% for critical paths
- **Type hints**: Required for all public APIs
- **Documentation**: Docstrings for all public classes/functions
- **Immutability**: Prefer frozen dataclasses and immutable patterns
- **Error handling**: Custom exceptions with structured responses
- **Async**: Use async/await throughout for I/O operations

## Testing

### Running Tests

```bash
# All tests with coverage
pytest --cov=agents --cov=core --cov=config --cov=schemas --cov=models --cov=services --cov=utils --cov=storage --cov-fail-under=95

# Specific test categories
pytest tests/test_all.py::TestHealthEndpoint -v
pytest tests/test_all.py::TestNegotiateEndpoint -v
pytest tests/test_all.py::TestScoringEngine -v
pytest tests/test_all.py::TestStateManager -v
pytest tests/test_all.py::TestAgentFactory -v

# HTML coverage report
pytest --cov=... --cov-report=html
open htmlcov/index.html
```

### Writing Tests

- Place tests in `tests/test_all.py`
- Use pytest fixtures from `conftest.py`
- Mock external dependencies (Ollama, file I/O)
- Test both success and error paths
- Follow AAA pattern (Arrange, Act, Assert)

## Architecture Guidelines

### Clean Architecture Layers

1. **API Layer** (`main.py`, `schemas/`): HTTP concerns only
2. **Application Layer** (`core/orchestrator.py`): Use case orchestration
3. **Domain Layer** (`models/`, `core/scoring.py`, `core/state.py`): Business logic
4. **Infrastructure Layer** (`services/`, `storage/`, `agents/`): External dependencies

### Dependency Rule

Dependencies point inward. Inner layers know nothing about outer layers.

### Key Principles

- **Negotiator Isolation**: Agents have zero knowledge of FastAPI/HTTP
- **Immutable State**: Frozen dataclasses, append-only history
- **Dependency Injection**: AgentFactory for testability
- **Heuristic Scoring**: No LLM calls for scoring (fast, deterministic)
- **Structured Logging**: JSON lines format for observability

## Pull Request Process

1. Ensure all checks pass (CI will verify)
2. Update CHANGELOG.md if applicable
3. Request review from maintainers
4. Address feedback promptly
5. Squash commits before merge if requested

## Reporting Issues

### Bug Reports

Include:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Ollama version)
- Relevant logs/error messages

### Feature Requests

Include:
- Clear title and description
- Use case and motivation
- Proposed solution (if any)
- Alternatives considered

## Security

See [SECURITY.md](SECURITY.md) for reporting security vulnerabilities.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.