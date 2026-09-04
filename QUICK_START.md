# Quick Start Guide

Get Free Claude Code running in 5 minutes.

## One-Command Start (Docker Compose)

```bash
git clone https://github.com/sjbrenchley89/free-claude-code.git
cd free-claude-code
cp .env.example .env
docker-compose up -d
```

Then open **http://localhost:8000** in your browser.

---

## Common Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs -f fcc-server
```

### Restart Service
```bash
docker-compose restart fcc-server
```

### Execute Command in Container
```bash
docker-compose exec fcc-server python -c "print('hello')"
```

### Check Health
```bash
curl http://localhost:8000/health
```

---

## Configuration

### Edit Environment Variables
```bash
nano .env
docker-compose restart  # Apply changes
```

### Key Variables
```
ANTHROPIC_API_KEY=sk-...          # For Anthropic
OPENAI_API_KEY=sk-...              # For OpenAI
OPENROUTER_API_KEY=sk-...          # For OpenRouter
NVIDIA_NIM_API_KEY=...             # For NVIDIA NIM
LOG_LEVEL=info                     # Logging level
```

---

## Troubleshooting

### Container won't start
```bash
docker-compose logs
docker-compose down
docker-compose pull
docker-compose up -d
```

### Can't connect to port 8000
```bash
lsof -i :8000  # Check what's using port 8000
```

### Clear everything and restart
```bash
docker-compose down -v           # Remove volumes
docker system prune -a --volumes # Clean up everything
docker-compose up -d
```

---

## Using Pre-Built Images

Instead of building locally, pull from GitHub Container Registry:

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  ghcr.io/sjbrenchley89/free-claude-code:latest
```

---

## Automated Installation (One Script)

### Linux/macOS
```bash
bash scripts/deploy.sh
```

### Windows PowerShell
```powershell
.\scripts\deploy.ps1
```

---

## Full Guides

- **Docker Deployment**: See [DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md)
- **Advanced Setup**: See [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Validation**: See [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)

---

## Need Help?

1. Check logs: `docker-compose logs`
2. Verify health: `curl http://localhost:8000/health`
3. Check environment: Edit `.env` and verify API keys
4. Restart: `docker-compose down && docker-compose up -d`

