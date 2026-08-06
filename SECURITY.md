# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly:

### Private Disclosure

**Do not** create a public GitHub issue for security vulnerabilities.

Instead, email: **security@manirider.example.com** (replace with actual email)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will:
- Acknowledge receipt within 48 hours
- Provide a timeline for fix
- Credit you in the fix (if desired)

## Security Measures

### Implemented

- **Input Validation**: All API endpoints validate and sanitize inputs
- **Prompt Injection Prevention**: Strict prompt templates with forbidden behavior rules
- **Log Sanitization**: Secrets automatically redacted from logs
- **No Hardcoded Secrets**: All configuration via environment variables
- **HTML Escaping**: User inputs escaped before processing
- **Pattern Filtering**: Forbidden patterns (XSS, code injection) blocked
- **Structured Error Responses**: No stack traces exposed to clients

### Configuration Security

Required environment variables:
- `OLLAMA_BASE_URL` - Ollama server URL
- `SECRET_KEY` - Change in production (default: `change-me-in-production`)

Optional security settings:
- `API_KEY_ENABLED` - Enable API key authentication (default: false)
- `LOG_LEVEL` - Set to WARNING/ERROR in production

### Docker Security

- Non-root user in container (`appuser`)
- Minimal base image (`python:3.11-slim`)
- No unnecessary packages
- Health checks for both API and Ollama
- Read-only volumes where possible

### Network Security

- Ollama only accessible within Docker network
- API exposed on configurable host/port
- Connection pooling with limits
- Request timeouts enforced

## Known Considerations

### LLM-Specific Risks

- **Prompt Injection**: Mitigated via strict templates and input sanitization
- **Hallucination**: Low temperature (0.1), constrained output format
- **Data Leakage**: No sensitive data sent to LLM; logs sanitized
- **Model Availability**: Fallback responses when Ollama unavailable

### Operational Security

- Rotate `SECRET_KEY` in production
- Enable `API_KEY_ENABLED` for public deployments
- Monitor `negotiation_log.json` for anomalies
- Keep Ollama and dependencies updated
- Use HTTPS in production (reverse proxy recommended)

## Security Checklist for Deployments

- [ ] Change `SECRET_KEY` from default
- [ ] Enable `API_KEY_ENABLED=true`
- [ ] Use HTTPS (nginx/traefik reverse proxy)
- [ ] Restrict network access to Ollama
- [ ] Set `LOG_LEVEL=WARNING`
- [ ] Configure log rotation
- [ ] Monitor for unusual negotiation patterns
- [ ] Regular dependency updates (`pip-audit`, `docker scan`)

## Responsible Disclosure Timeline

| Phase | Timeline |
|-------|----------|
| Acknowledgment | 48 hours |
| Initial Assessment | 5 business days |
| Fix Development | 30 days (critical), 90 days (non-critical) |
| Release | Next patch version |
| Public Disclosure | After fix released |

## Contact

Security Team: **security@manirider.example.com**

For non-security issues, use [GitHub Issues](https://github.com/Manirider/LLM-Trade-Negotiation-Agents/issues).