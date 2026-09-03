# Environment Setup Guide

Complete reference for configuring Free Claude Code via environment variables.

## Quick Setup

1. Copy the example configuration:
```bash
cp .env.example .env
```

2. Edit with your API keys:
```bash
nano .env
```

3. Restart the server:
```bash
docker-compose restart
```

---

## API Provider Configuration

### Anthropic (Claude)

**Required for:** Using Claude models

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

- **Get API Key**: https://console.anthropic.com/account/keys
- **Scope**: Full access to Claude models
- **Cost**: Pay-per-token pricing
- **Rate Limits**: Depends on plan
- **Models Available**: claude-3-opus, claude-3-sonnet, etc.

### OpenAI (GPT)

**Required for:** Using OpenAI models (GPT-4, GPT-3.5)

```bash
OPENAI_API_KEY=sk-...
```

- **Get API Key**: https://platform.openai.com/account/api-keys
- **Scope**: Read access to models and engines
- **Cost**: Pay-per-token pricing
- **Rate Limits**: Based on organization plan
- **Models Available**: gpt-4, gpt-4-turbo, gpt-3.5-turbo

### OpenRouter

**Required for:** Using OpenRouter (multi-model access)

```bash
OPENROUTER_API_KEY=sk-or-...
```

- **Get API Key**: https://openrouter.ai/account/api-keys
- **Scope**: Access to 100+ models
- **Cost**: Pay-per-token routing
- **Rate Limits**: Shared across all routed models
- **Models Available**: All OpenRouter-supported models

### Google (Gemini, Vertex AI)

**Required for:** Using Google's generative models

```bash
GOOGLE_API_KEY=AIzaSy...
# OR for Vertex AI:
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_LOCATION=us-central1
GOOGLE_CREDENTIALS_JSON=/path/to/service-account-key.json
```

- **Get API Key**: https://ai.google.dev/
- **Service Account**: https://cloud.google.com/docs/authentication/getting-started
- **Cost**: Free tier available, then pay-per-token
- **Rate Limits**: Quota-based
- **Models Available**: gemini-pro, PaLM, etc.

### NVIDIA NIM (Local/Optimized Models)

**Required for:** Using NVIDIA optimized models

```bash
NVIDIA_NIM_API_KEY=nvapi-...
NVIDIA_NIM_ENDPOINT=https://integrate.api.nvidia.com/v1
```

- **Get API Key**: https://build.nvidia.com/nim
- **Scope**: NVIDIA cloud endpoints
- **Cost**: Credits-based (free tier available)
- **Rate Limits**: Model-dependent
- **Models Available**: LLAMA-2, Mixtral, Phi, etc.

### Mistral AI

**Required for:** Using Mistral models

```bash
MISTRAL_API_KEY=...
```

- **Get API Key**: https://console.mistral.ai/api-keys
- **Scope**: Access to Mistral's model family
- **Cost**: Pay-per-token
- **Rate Limits**: Based on plan
- **Models Available**: mistral-7b, mistral-medium, mistral-large

### AWS (Bedrock)

**Required for:** Using AWS Bedrock models

```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

- **Get Credentials**: https://console.aws.amazon.com/iam/
- **Setup**: Enable Bedrock in AWS console
- **Cost**: Pay-per-token + API calls
- **Rate Limits**: Account-based
- **Models Available**: Claude, Titan, Llama, etc.

---

## Application Configuration

### Server Port & Host

```bash
# Port the server listens on
PORT=8000

# Host to bind to (0.0.0.0 = all interfaces)
HOST=0.0.0.0
```

### Logging

```bash
# Log level (debug, info, warning, error, critical)
LOG_LEVEL=info

# Log file location (optional)
LOG_FILE=/var/log/fcc-server.log

# Enable structured logging
LOG_FORMAT=json  # or 'text' (default)
```

### Feature Flags

```bash
# Enable specific providers
ENABLE_ANTHROPIC=true
ENABLE_OPENAI=true
ENABLE_OPENROUTER=false
ENABLE_GOOGLE=false
ENABLE_NVIDIA_NIM=false
ENABLE_MISTRAL=false
ENABLE_AWS=false

# Enable features
ENABLE_CACHING=true
ENABLE_RETRY_LOGIC=true
ENABLE_RATE_LIMITING=true
```

---

## Performance Tuning

### Concurrency

```bash
# Number of worker processes
WORKER_PROCESSES=4

# Max connections per worker
MAX_CONNECTIONS=100

# Connection pool size
POOL_SIZE=50
```

### Timeouts

```bash
# Request timeout in seconds
REQUEST_TIMEOUT=300

# Connection timeout in seconds
CONNECT_TIMEOUT=30

# Read timeout for streaming responses
READ_TIMEOUT=600
```

### Retry Policy

```bash
# Maximum number of retries for failed requests
MAX_RETRIES=3

# Initial retry delay in seconds
RETRY_DELAY=1

# Maximum retry delay in seconds
MAX_RETRY_DELAY=60

# Retry backoff multiplier
RETRY_BACKOFF=2.0
```

### Caching

```bash
# Enable response caching
ENABLE_CACHE=true

# Cache TTL in seconds
CACHE_TTL=3600

# Cache size in MB
CACHE_SIZE=100
```

---

## Security Configuration

### API Key Management

```bash
# Rotate API keys regularly
API_KEY_ROTATION_DAYS=90

# Store keys securely (use .env or Docker secrets)
# NEVER commit keys to version control
# NEVER share keys in logs

# Use read-only .env file permissions
# chmod 600 .env
```

### Authentication

```bash
# Admin authentication token (if required)
ADMIN_TOKEN=your-secure-token-here

# Enable authentication
REQUIRE_AUTH=false  # Change to true in production
```

### CORS & Security Headers

```bash
# Allowed origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Enable HTTPS redirect
FORCE_HTTPS=true

# Security headers
ENABLE_SECURITY_HEADERS=true
```

---

## Monitoring & Metrics

### Health Checks

```bash
# Health check path
HEALTH_CHECK_PATH=/health

# Health check interval (seconds)
HEALTH_CHECK_INTERVAL=30

# Health check timeout (seconds)
HEALTH_CHECK_TIMEOUT=10
```

### Metrics

```bash
# Enable Prometheus metrics
ENABLE_METRICS=true

# Metrics port
METRICS_PORT=8001

# Enable detailed metrics
DETAILED_METRICS=false
```

---

## Advanced Configuration

### Database (if applicable)

```bash
# Database URL
DATABASE_URL=postgresql://user:pass@localhost/fcc

# Connection pool size
DB_POOL_SIZE=20

# Enable connection pool recycling
DB_POOL_RECYCLE=3600
```

### Message Queue (if applicable)

```bash
# Redis for caching/sessions
REDIS_URL=redis://localhost:6379/0

# Message queue backend
QUEUE_BACKEND=redis  # or 'memory'
```

### Proxy & Network

```bash
# HTTP proxy (if needed for outbound requests)
HTTP_PROXY=http://proxy.example.com:8080

# HTTPS proxy
HTTPS_PROXY=http://proxy.example.com:8080

# No proxy for these hosts
NO_PROXY=localhost,127.0.0.1,internal.example.com
```

---

## Configuration Validation

### Check Your Configuration

```bash
# View current configuration (sanitized)
docker-compose exec fcc-server python -c \
  "from free_claude_code.config import settings; print(settings.dict())"

# Check specific variable
docker-compose exec fcc-server python -c \
  "import os; print('ANTHROPIC_API_KEY:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET')"
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "API key not found" | Variable not set in .env | Add API_KEY=value to .env |
| "Authentication failed" | Invalid API key | Check key is correct |
| "Rate limited" | Too many requests | Increase RETRY_DELAY or MAX_RETRY_DELAY |
| "Connection timeout" | Slow network | Increase CONNECT_TIMEOUT |
| "Out of memory" | Cache too large | Reduce CACHE_SIZE or disable ENABLE_CACHE |

---

## Environment by Deployment Type

### Local Development
```bash
LOG_LEVEL=debug
ENABLE_CACHING=false
PORT=8000
ENABLE_SECURITY_HEADERS=false
```

### Staging
```bash
LOG_LEVEL=info
ENABLE_CACHING=true
ENABLE_METRICS=true
REQUIRE_AUTH=true
FORCE_HTTPS=false
```

### Production
```bash
LOG_LEVEL=warning
ENABLE_CACHING=true
ENABLE_METRICS=true
REQUIRE_AUTH=true
FORCE_HTTPS=true
ENABLE_SECURITY_HEADERS=true
MAX_RETRIES=5
```

---

## Safe Environment Management

### Do's ✅
- Store secrets in `.env` (git-ignored)
- Use strong, unique API keys
- Rotate keys regularly
- Use read-only file permissions (`chmod 600`)
- Monitor API usage
- Keep `.env.example` with dummy values

### Don'ts ❌
- Commit `.env` to version control
- Share API keys via email or chat
- Hardcode secrets in code
- Use weak API keys
- Log sensitive information
- Store keys in plain text files

### Secure Storage Alternatives

```bash
# Docker Secrets (Swarm/K8s)
docker secret create api_key /path/to/key

# Environment variables from systemd
# /etc/systemd/system/fcc-server.service.d/override.conf
[Service]
Environment="ANTHROPIC_API_KEY=sk-..."

# AWS Secrets Manager
AWS_REGION=us-east-1
USE_AWS_SECRETS=true

# HashiCorp Vault
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=...
```

---

## Migration from Old Config

If migrating from a previous configuration:

```bash
# Backup current .env
cp .env .env.backup

# Copy new template
cp .env.example .env

# Restore your customizations
# (Manually copy only the values you need)
```

---

## Support

For issues with configuration:

1. Check `.env` file exists and is readable: `ls -la .env`
2. Verify API keys are set: `grep -E '^[A-Z_]+=.*' .env | head -5`
3. Check server logs: `docker-compose logs -f fcc-server`
4. Test API key: `curl -H "Authorization: Bearer $API_KEY" https://api.example.com/v1/status`

For API provider-specific help:
- **Anthropic**: https://docs.anthropic.com
- **OpenAI**: https://platform.openai.com/docs
- **OpenRouter**: https://openrouter.ai/docs
- **Google**: https://ai.google.dev/docs
- **NVIDIA**: https://build.nvidia.com/docs

