# Docker Quick Start - free-claude-code

Get free-claude-code running in Docker in 5 minutes.

## Option 1: Automated Setup (Recommended)

```bash
# 1. Run the setup script
./scripts/docker-deploy.sh setup

# 2. Build the Docker image
./scripts/docker-deploy.sh build

# 3. Start the services
./scripts/docker-deploy.sh start

# 4. Test it
./scripts/docker-deploy.sh test

# 5. View logs
./scripts/docker-deploy.sh logs
```

## Option 2: Manual Setup

### Step 1: Get an API Key

Choose one provider:

**Anthropic** (Recommended)
- Visit: https://console.anthropic.com/account/keys
- Create a key (starts with `sk-ant-...`)

**Groq** (Free tier, fastest)
- Visit: https://console.groq.com/keys
- Create a key

**OpenRouter** (OpenAI models via API)
- Visit: https://openrouter.ai/keys
- Create a key

### Step 2: Configure .env.production

```bash
# Edit the file
nano .env.production

# For Anthropic, uncomment and fill:
ANTHROPIC_API_KEY=sk-ant-your-key-here
FCC_DEFAULT_MODEL=anthropic/claude-3-5-sonnet-20241022

# Or use sed to set automatically:
sed -i 's/# ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=sk-ant-your-key/' .env.production
```

### Step 3: Build Docker Image

```bash
docker build -t free-claude-code:latest .
```

### Step 4: Start the Container

```bash
# Quick start
docker run -d \
  --name fcc-server \
  --env-file .env.production \
  -p 8082:8082 \
  free-claude-code:latest

# Or use docker-compose (includes monitoring)
docker-compose up -d
```

### Step 5: Test It

```bash
# Health check
curl http://localhost:8082/health | jq .

# Chat completion
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}]
  }' | jq .

# Expected: Response with assistant message
```

## Access Points

| Component | URL | Purpose |
|-----------|-----|---------|
| API Server | http://localhost:8082 | REST API endpoint |
| Admin UI | http://localhost:8082/admin | Configuration & monitoring |
| Prometheus | http://localhost:9090 | Metrics (if docker-compose) |
| Grafana | http://localhost:3000 | Dashboards (if docker-compose) |

## Common Commands

```bash
# View logs
docker logs -f fcc-server

# Stop the server
docker stop fcc-server

# Restart the server
docker restart fcc-server

# Remove the container
docker rm fcc-server

# List all containers
docker ps

# Check resource usage
docker stats fcc-server
```

## Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker logs fcc-server

# Check if port 8082 is already in use
lsof -i :8082

# Rebuild image
docker build --no-cache -t free-claude-code:latest .
```

### API key errors

```bash
# Verify key is set
grep ANTHROPIC_API_KEY .env.production

# Make sure there's a value after the =
# Should be: ANTHROPIC_API_KEY=sk-ant-xxx
# NOT: # ANTHROPIC_API_KEY=sk-ant-xxx (commented out)
```

### Connection refused

```bash
# Wait for server to start (takes ~10 seconds)
sleep 5

# Test again
curl http://localhost:8082/health
```

## What's Next?

- **Production Deployment**: See [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- **Configure Multiple Providers**: Add fallback providers in `.env.production`
- **Setup Monitoring**: Enable Prometheus/Grafana in `docker-compose.yml`
- **Enable Authentication**: Add `PROXY_AUTH_ENABLED=true` to `.env.production`
- **Setup Reverse Proxy**: Use NGINX for SSL/TLS termination

## Documentation

- **Full Guide**: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- **Main README**: [README.md](./README.md)
- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md)

## Support

For help:
1. Check logs: `docker logs fcc-server`
2. Test health: `curl http://localhost:8082/health`
3. Read [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) troubleshooting section
4. Open a GitHub issue: https://github.com/sjbrenchley89/free-claude-code/issues
