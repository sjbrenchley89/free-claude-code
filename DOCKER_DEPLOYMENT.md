# Docker Deployment Guide for free-claude-code

Complete production deployment guide with Docker, OpenAI configuration, and testing procedures.

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Key Configuration](#api-key-configuration)
3. [Docker Build & Run](#docker-build--run)
4. [Docker Compose Deployment](#docker-compose-deployment)
5. [Testing & Verification](#testing--verification)
6. [Production Best Practices](#production-best-practices)
7. [Monitoring & Logging](#monitoring--logging)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose installed
- An AI provider API key (see [API Key Configuration](#api-key-configuration))
- Linux/macOS terminal or Windows WSL2

### 30-Second Deployment

```bash
# 1. Configure your API key
nano .env.production
# Uncomment and fill in your provider's API key (see section 2 below)

# 2. Build the Docker image
docker build -t free-claude-code:latest .

# 3. Run the container
docker run -d \
  --name fcc-server \
  --env-file .env.production \
  -p 8082:8082 \
  free-claude-code:latest

# 4. Verify it's running
curl http://localhost:8082/health
```

---

## API Key Configuration

### Overview

The server supports **30+ AI providers**. Choose one based on your needs:

| Provider | Type | Setup Cost | Free Tier | Best For |
|----------|------|-----------|-----------|----------|
| **OpenAI** | OAuth | $0 setup | $5 credits | ChatGPT subscription holders |
| **Anthropic** | API Key | $0 setup | $5 credits | Production, reasoning |
| **Groq** | API Key | $0 setup | Unlimited | Fast inference, testing |
| **OpenRouter** | API Key | $0 setup | Yes | Multiple models in one API |
| **DeepSeek** | API Key | $0 setup | $5 credits | Cost-effective, reasoning |
| **Azure OpenAI** | API Key + URL | Pay-as-you-go | Yes | Enterprise deployments |

### Step 1: Get an API Key

**Option A: Anthropic (Recommended for Production)**
```bash
# 1. Visit https://console.anthropic.com/account/keys
# 2. Click "Create Key"
# 3. Copy the key (starts with sk-ant-...)
```

**Option B: Groq (Fastest, Free)**
```bash
# 1. Visit https://console.groq.com/keys
# 2. Sign up with Google/GitHub
# 3. Copy your API key
# 4. Free tier includes unlimited requests
```

**Option C: OpenRouter (Multi-Model Support)**
```bash
# 1. Visit https://openrouter.ai/keys
# 2. Sign up
# 3. Copy your API key
# 4. Access OpenAI models: openai/gpt-4, openai/gpt-3.5-turbo, etc.
```

**Option D: DeepSeek (Cost-Effective)**
```bash
# 1. Visit https://platform.deepseek.com/api_keys
# 2. Create a new key
# 3. Copy your API key
```

**Option E: OpenAI (Requires ChatGPT Subscription)**
```bash
# 1. Already have ChatGPT? This provider uses OAuth.
# 2. After deploying, configure via Admin UI:
#    - Navigate to http://localhost:8082/admin
#    - Go to "Providers → Connected accounts"
#    - Click "Connect OpenAI"
#    - Complete device code flow or browser OAuth
# 3. Restart the server: docker restart fcc-server
```

### Step 2: Add Key to Configuration

Edit `.env.production` and uncomment/fill your provider's setting:

```bash
# For Anthropic (Recommended)
nano .env.production

# Find and uncomment:
# ANTHROPIC_API_KEY=sk-ant-...
# Replace with your actual key

# Or use sed to set it automatically:
sed -i 's/# ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=sk-ant-your-key-here/' .env.production
```

**Common Providers:**

```bash
# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-v0-abc123...

# Groq
GROQ_API_KEY=gsk_abc123...

# OpenRouter
OPENROUTER_API_KEY=sk-or-abc123...

# DeepSeek
DEEPSEEK_API_KEY=sk-abc123...

# Azure OpenAI
AZURE_OPENAI_API_KEY=abc123...
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com

# NVIDIA NIM
NVIDIA_NIM_API_KEY=nvapi-abc123...
```

### Step 3: Verify Configuration

```bash
# Check that your key is set (first 10 chars + "...")
grep "ANTHROPIC_API_KEY\|GROQ_API_KEY\|OPENROUTER_API_KEY\|DEEPSEEK_API_KEY" .env.production | head -1

# Should show something like:
# ANTHROPIC_API_KEY=sk-ant-v0-abc123***
```

### Step 4: Set Default Model (Optional)

```bash
# Add to .env.production to set default model:
# For Anthropic:
FCC_DEFAULT_MODEL=anthropic/claude-3-5-sonnet-20241022

# For Groq:
FCC_DEFAULT_MODEL=groq/llama-3.3-70b-versatile

# For OpenRouter (OpenAI):
FCC_DEFAULT_MODEL=openai/gpt-4-turbo

# For DeepSeek:
FCC_DEFAULT_MODEL=deepseek/deepseek-chat
```

---

## Docker Build & Run

### Build the Image

```bash
# Build from Dockerfile
docker build -t free-claude-code:latest .

# Tag for registry (optional)
docker tag free-claude-code:latest myregistry.azurecr.io/free-claude-code:v1.0.0
```

### Run as a Container

#### Basic Run (Development)

```bash
docker run -it \
  --env-file .env.production \
  -p 8082:8082 \
  --name fcc-server \
  free-claude-code:latest
```

#### Production Run (Detached with Logging)

```bash
docker run -d \
  --env-file .env.production \
  -p 8082:8082 \
  -p 9090:9090 \
  --name fcc-server \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  --memory 2g \
  --cpus 2 \
  -v /var/log/fcc:/app/logs \
  free-claude-code:latest

# View logs
docker logs -f fcc-server

# Stop the container
docker stop fcc-server

# Remove the container
docker rm fcc-server
```

#### With Custom Environment

```bash
docker run -d \
  -e ANTHROPIC_API_KEY="sk-ant-your-key" \
  -e FCC_DEFAULT_MODEL="anthropic/claude-3-5-sonnet-20241022" \
  -e FCC_LOG_LEVEL="INFO" \
  -e PROXY_AUTH_ENABLED="true" \
  -e ANTHROPIC_AUTH_TOKEN="your-secure-token-12345" \
  -p 8082:8082 \
  --name fcc-server \
  --restart unless-stopped \
  free-claude-code:latest
```

### Container Lifecycle

```bash
# View running containers
docker ps | grep fcc

# View container details
docker inspect fcc-server

# Check resource usage
docker stats fcc-server

# View logs
docker logs fcc-server
docker logs -f --tail 50 fcc-server

# Stop the container (graceful)
docker stop -t 30 fcc-server

# Kill the container (forceful)
docker kill fcc-server

# Restart the container
docker restart fcc-server

# Remove the container
docker rm fcc-server
```

---

## Docker Compose Deployment

### Single Provider (Anthropic)

```bash
# 1. Configure .env.production with your API key
nano .env.production

# 2. Start services (server + optional monitoring)
docker-compose up -d

# 3. Verify services are running
docker-compose ps

# 4. View logs
docker-compose logs -f fcc-server

# 5. Stop services
docker-compose down
```

### Multi-Provider Setup

Edit `docker-compose.yml` environment variables:

```yaml
services:
  fcc-server:
    environment:
      # Primary provider
      ANTHROPIC_API_KEY: "sk-ant-your-key"
      # Fallback providers
      GROQ_API_KEY: "gsk-your-key"
      OPENROUTER_API_KEY: "sk-or-your-key"
      # Optional settings
      FCC_DEFAULT_MODEL: "anthropic/claude-3-5-sonnet-20241022"
      FCC_LOG_LEVEL: "INFO"
```

### Monitoring Stack

The included `docker-compose.yml` includes optional Prometheus and Grafana:

```bash
# Access monitoring dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)

# Configure Prometheus to scrape the server
mkdir -p ./prometheus
cat > ./prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'free-claude-code'
    static_configs:
      - targets: ['fcc-server:8082']
EOF

# Create Grafana provisioning (optional)
mkdir -p ./grafana/provisioning/dashboards
mkdir -p ./grafana/provisioning/datasources
```

---

## Testing & Verification

### 1. Health Check

```bash
# Local container
curl -s http://localhost:8082/health | jq .

# Expected response:
# {
#   "status": "healthy",
#   "version": "5.14.0",
#   "providers": {
#     "anthropic": "online",
#     "groq": "online"
#   }
# }
```

### 2. Test Chat Completion (Anthropic)

```bash
# Simple request
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3-5-sonnet-20241022",
    "messages": [
      {
        "role": "user",
        "content": "Say hello!"
      }
    ]
  }'

# Expected response:
# {
#   "id": "chatcmpl-...",
#   "object": "chat.completion",
#   "created": 1234567890,
#   "model": "anthropic/claude-3-5-sonnet-20241022",
#   "choices": [
#     {
#       "index": 0,
#       "message": {
#         "role": "assistant",
#         "content": "Hello! How can I help you today?"
#       },
#       "finish_reason": "end_turn"
#     }
#   ]
# }
```

### 3. Test with Different Models

```bash
# Groq
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "groq/llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }'

# OpenRouter (OpenAI models)
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4-turbo",
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }'

# DeepSeek
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek/deepseek-chat",
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }'
```

### 4. Test Streaming

```bash
# Stream a response
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Write a haiku"}],
    "stream": true
  }'

# Expected: Server-sent events (SSE) with streaming chunks
```

### 5. Test with Python

```python
import httpx

client = httpx.Client(base_url="http://localhost:8082")

response = client.post(
    "/v1/chat/completions",
    json={
        "model": "anthropic/claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "Hello, what is your name?"}
        ]
    }
)

print(response.json())
```

### 6. Load Testing

```bash
# Install Apache Bench (if not installed)
# Ubuntu: sudo apt-get install apache2-utils
# macOS: brew install httpd

# Test 100 requests with 10 concurrent
ab -n 100 -c 10 \
  -p payload.json \
  -T "application/json" \
  http://localhost:8082/v1/chat/completions

# Where payload.json contains:
# {
#   "model": "anthropic/claude-3-5-sonnet-20241022",
#   "messages": [{"role": "user", "content": "test"}]
# }
```

---

## Production Best Practices

### 1. Security

```bash
# Enable authentication
sed -i 's/# PROXY_AUTH_ENABLED=.*/PROXY_AUTH_ENABLED=true/' .env.production
sed -i 's/# ANTHROPIC_AUTH_TOKEN=.*/ANTHROPIC_AUTH_TOKEN=your-secure-random-token-12345/' .env.production

# Use strong tokens (generate with openssl)
openssl rand -base64 32

# Verify in docker-compose.yml
docker-compose up -d

# Test with authentication
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secure-random-token-12345" \
  -d '{
    "model": "anthropic/claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

### 2. Resource Limits

```bash
# Set memory and CPU limits in docker run
docker run -d \
  --env-file .env.production \
  -p 8082:8082 \
  --memory 2g \
  --cpus 2 \
  --memswap 4g \
  free-claude-code:latest

# Or in docker-compose.yml:
# services:
#   fcc-server:
#     deploy:
#       resources:
#         limits:
#           cpus: '2'
#           memory: 2G
#         reservations:
#           cpus: '1'
#           memory: 1G
```

### 3. Logging

```bash
# JSON logging for centralized collection
docker run -d \
  --env-file .env.production \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=5 \
  free-claude-code:latest

# View logs
docker logs fcc-server | tail -20

# Export logs
docker logs fcc-server > fcc-server.log 2>&1
```

### 4. Network Security

```bash
# Use a private network (only expose through reverse proxy)
docker network create fcc-private

docker run -d \
  --env-file .env.production \
  --network fcc-private \
  --name fcc-server \
  free-claude-code:latest

# Reverse proxy (NGINX) configuration
cat > nginx.conf << 'EOF'
upstream fcc_backend {
    server fcc-server:8082;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    
    location / {
        proxy_pass http://fcc_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api_limit burst=100 nodelay;
    }
}

limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
EOF
```

### 5. Automatic Restarts

```bash
# Enable restart policy
docker run -d \
  --restart unless-stopped \
  --env-file .env.production \
  free-claude-code:latest

# Or in docker-compose.yml:
# services:
#   fcc-server:
#     restart: unless-stopped
```

---

## Monitoring & Logging

### 1. Prometheus Metrics

```bash
# Access Prometheus dashboard
open http://localhost:9090

# Query examples:
# - up{job="free-claude-code"}  # Service availability
# - rate(requests_total[5m])     # Request rate
# - http_request_duration_seconds_bucket  # Latency distribution
```

### 2. Grafana Dashboards

```bash
# Access Grafana
open http://localhost:3000

# Login: admin / admin
# Add Prometheus as data source:
# - URL: http://prometheus:9090
# - Access: Server
# Create dashboards to visualize:
#   - Request rate and latency
#   - Error rates by provider
#   - Model usage statistics
#   - Provider health status
```

### 3. Centralized Logging (ELK Stack)

```yaml
# docker-compose-logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
```

### 4. Application Logs

```bash
# View real-time logs
docker logs -f fcc-server

# View last 100 lines
docker logs --tail 100 fcc-server

# View logs from specific time
docker logs --since 10m fcc-server

# Save to file
docker logs fcc-server > logs/fcc-server.log 2>&1
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs fcc-server

# Common issues:
# 1. Port 8082 already in use
docker ps | grep 8082
docker kill <container_id>

# 2. Missing API key
# Ensure .env.production has valid key
grep "ANTHROPIC_API_KEY\|GROQ_API_KEY" .env.production

# 3. Build failed
docker build --no-cache -t free-claude-code:latest .
```

### Slow Responses

```bash
# Check container resources
docker stats fcc-server

# Increase memory/CPU
docker run -d \
  --memory 4g \
  --cpus 4 \
  --env-file .env.production \
  free-claude-code:latest
```

### Provider Connection Issues

```bash
# Check health endpoint
curl http://localhost:8082/health | jq .

# Test specific provider
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "test"}]
  }' | jq .

# If provider is offline, check:
# 1. API key is correct
# 2. API key has credits/quota
# 3. Network connectivity to provider (test with curl)
# 4. Rate limits aren't exceeded
```

---

## Next Steps

1. **Customize Configuration** — Edit `.env.production` for your setup
2. **Deploy with Compose** — Run `docker-compose up -d`
3. **Setup Monitoring** — Configure Prometheus and Grafana
4. **Add Reverse Proxy** — Use NGINX for SSL/TLS and rate limiting
5. **Automate Updates** — Setup CI/CD to rebuild and redeploy on changes
6. **Scale Horizontally** — Use Docker Swarm or Kubernetes for multiple instances

---

## Support

For issues, check:
- GitHub Issues: https://github.com/sjbrenchley89/free-claude-code
- Documentation: https://github.com/sjbrenchley89/free-claude-code/README.md
- Provider API Docs:
  - Anthropic: https://docs.anthropic.com
  - Groq: https://console.groq.com/docs
  - OpenRouter: https://openrouter.ai/docs
  - DeepSeek: https://platform.deepseek.com/api-docs
