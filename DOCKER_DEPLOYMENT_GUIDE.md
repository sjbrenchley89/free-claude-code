# Docker Deployment Guide

Complete guide for deploying Free Claude Code using Docker.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Deployment Methods](#deployment-methods)
3. [Using Pre-built Docker Images](#using-pre-built-docker-images)
4. [Local Development](#local-development)
5. [Production Deployment](#production-deployment)
6. [Monitoring and Health Checks](#monitoring-and-health-checks)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

---

## Quick Start

### Option 1: Using Docker Compose (Recommended for Most Users)

**Prerequisites:**
- Docker and Docker Compose installed
- 2GB RAM and 1 CPU minimum

**Steps:**

```bash
# Clone the repository
git clone https://github.com/sjbrenchley89/free-claude-code.git
cd free-claude-code

# Copy and configure environment
cp .env.example .env
nano .env  # or edit in your favorite editor

# Build and start the server
docker-compose up -d

# Verify it's running
docker-compose ps
curl http://localhost:8000/health

# View logs
docker-compose logs -f
```

Access the Admin UI at: **http://localhost:8000**

### Option 2: Automated Deployment Script

For **Linux/macOS**:
```bash
bash scripts/deploy.sh
```

For **Windows PowerShell**:
```powershell
.\scripts\deploy.ps1
```

These scripts automate Docker installation, repository setup, and configuration.

---

## Deployment Methods

### Method 1: Docker Compose (Development & Small Deployments)

**Best for:** Local development, small VPS, testing

```bash
docker-compose up -d
```

**Features:**
- Single command startup
- Automatic restart on failure
- Integrated logging
- Resource limits configured

**Configuration:**
Edit `docker-compose.yml` to adjust:
- Port mapping (line 12: `8000:8000`)
- Environment variables (line 14+)
- Resource limits (lines 20-21)
- Restart policy (line 22)

### Method 2: Direct Docker Run

**Best for:** Custom configurations, CI/CD pipelines

```bash
# Using pre-built image from GitHub Container Registry
docker run -d \
  --name free-claude-code \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  --health-cmd='curl -f http://localhost:8000/health || exit 1' \
  --health-interval=30s \
  --health-timeout=10s \
  --health-start-period=10s \
  --health-retries=3 \
  -m 2g \
  --cpus 2 \
  ghcr.io/sjbrenchley89/free-claude-code:latest
```

### Method 3: Kubernetes Deployment

**Best for:** Large scale, high availability, managed infrastructure

See [Kubernetes Deployment](./DEPLOYMENT.md#kubernetes-deployment) section in DEPLOYMENT.md.

---

## Using Pre-built Docker Images

### Image Availability

Images are built automatically for:
- **Every push** to `claude/fcc-server-deployment-*` branches
- **Every push** to `main` branch
- **All tags** (semantic versions, SHA commits, `latest`)

### Available Image Tags

From GitHub Container Registry (`ghcr.io/sjbrenchley89/free-claude-code`):

```bash
# Latest version (main branch only)
ghcr.io/sjbrenchley89/free-claude-code:latest

# Semantic versions (when released)
ghcr.io/sjbrenchley89/free-claude-code:1.0.0
ghcr.io/sjbrenchley89/free-claude-code:1.0

# Short commit SHA
ghcr.io/sjbrenchley89/free-claude-code:bc6bba1

# Pull and run
docker pull ghcr.io/sjbrenchley89/free-claude-code:latest
docker run -d -p 8000:8000 --env-file .env \
  ghcr.io/sjbrenchley89/free-claude-code:latest
```

### Authentication (Private Registry)

For private repositories, authenticate before pulling:

```bash
# GitHub Personal Access Token (PAT) with read:packages scope
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Now pull/run the image
docker pull ghcr.io/sjbrenchley89/free-claude-code:latest
```

---

## Local Development

### Building Custom Image

```bash
# Clone repository
git clone https://github.com/sjbrenchley89/free-claude-code.git
cd free-claude-code

# Build image
docker build -t free-claude-code:dev .

# Run with environment variables
docker run -d \
  --name fcc-dev \
  -p 8000:8000 \
  --env-file .env \
  free-claude-code:dev
```

### Interactive Development

```bash
# Start container with shell access
docker run -it \
  --rm \
  -v $(pwd):/app \
  -p 8000:8000 \
  --env-file .env \
  free-claude-code:dev /bin/bash

# Inside container
python -c "from free_claude_code.cli.commands import serve; serve()"
```

---

## Production Deployment

### Prerequisites

- **OS**: Ubuntu 22.04+ LTS, Debian 12+, CentOS 8+, or equivalent
- **Resources**: 2+ CPU, 4GB+ RAM, 20GB+ disk
- **Network**: Outbound HTTPS (443) for API calls
- **SSL/TLS**: For HTTPS reverse proxy (recommended)

### Deployment Steps

#### 1. Install Docker & Docker Compose

```bash
# On Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo bash get-docker.sh
sudo usermod -aG docker $USER
```

#### 2. Clone Repository

```bash
sudo mkdir -p /opt/free-claude-code
sudo chown $USER:$USER /opt/free-claude-code
cd /opt/free-claude-code

git clone https://github.com/sjbrenchley89/free-claude-code.git .
```

#### 3. Configure Environment

```bash
cp .env.example .env
nano .env

# Essential variables to set:
# - ANTHROPIC_API_KEY (if using Anthropic)
# - OPENAI_API_KEY (if using OpenAI)
# - OPENROUTER_API_KEY (if using OpenRouter)
# - NVIDIA_NIM_API_KEY (if using NVIDIA)
# - LOG_LEVEL (debug, info, warning, error)
```

#### 4. Start Services

```bash
docker-compose up -d

# Verify
docker-compose ps
sleep 5  # Wait for startup
curl http://localhost:8000/health
```

#### 5. Configure Reverse Proxy (Nginx)

```bash
# Copy example configuration
sudo cp nginx.conf.example /etc/nginx/sites-available/free-claude-code

# Edit for your domain
sudo nano /etc/nginx/sites-available/free-claude-code

# Enable site
sudo ln -s /etc/nginx/sites-available/free-claude-code \
           /etc/nginx/sites-enabled/free-claude-code

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
```

**Example nginx.conf snippet:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

#### 6. Enable SSL (Optional but Recommended)

```bash
# Using Let's Encrypt (certbot)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

---

## Monitoring and Health Checks

### Health Check Endpoint

The server exposes a health check endpoint:

```bash
# Check if server is healthy
curl http://localhost:8000/health

# Expected response:
# {"status": "ok"}
```

### Docker Health Status

```bash
# View container health status
docker-compose ps

# Output shows: (healthy) or (unhealthy)
```

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail 100

# Specific service logs
docker-compose logs -f fcc-server
```

### Monitoring Checklist

- [ ] Health endpoint responds within 2 seconds
- [ ] No error logs every 5 minutes
- [ ] CPU usage < 80%
- [ ] Memory usage < 80% of limit
- [ ] Container uptime > 24 hours
- [ ] API response times < 5 seconds

### Log Rotation

Logs are automatically rotated by docker-compose configuration:
- Maximum file size: 10MB
- Maximum files: 3
- Driver: json-file

---

## Troubleshooting

### Container Won't Start

**Error:** `docker-compose up` fails immediately

**Solutions:**
1. Check logs: `docker-compose logs`
2. Verify image exists: `docker images | grep free-claude-code`
3. Check port 8000 is available: `lsof -i :8000`
4. Increase startup wait: `docker-compose up --wait`

### Health Check Failing

**Error:** Container shows `(unhealthy)`

**Solutions:**
1. Check if server is running: `curl http://localhost:8000/health`
2. Check logs: `docker-compose logs fcc-server`
3. Verify API keys are set: `docker-compose exec fcc-server env | grep API`
4. Wait for startup (can take 30s on slow systems)

### Can't Connect to Server

**Error:** `Connection refused` or timeout

**Solutions:**
1. Verify container is running: `docker-compose ps`
2. Check port mapping: `docker-compose port fcc-server 8000`
3. If using Nginx, check it's running: `sudo systemctl status nginx`
4. Check firewall: `sudo ufw status` (if using UFW)

### High Memory Usage

**Error:** Container memory approaches limit

**Solutions:**
1. Increase memory limit in `docker-compose.yml`:
   ```yaml
   services:
     fcc-server:
       deploy:
         resources:
           limits:
             memory: 4G  # Increase from 2G
   ```
2. Restart: `docker-compose restart`
3. Check for memory leaks in logs

### API Key Not Found

**Error:** "API key not configured" in logs

**Solutions:**
1. Verify .env file exists: `ls -la .env`
2. Check API key is set: `cat .env | grep API_KEY`
3. Reload configuration: `docker-compose restart`
4. Verify key format is correct (no quotes in .env)

---

## Rollback Procedures

### Rollback to Previous Image

**If current version has issues:**

```bash
# Stop current container
docker-compose down

# Modify docker-compose.yml to use previous tag
nano docker-compose.yml

# Change image from:
#   image: ghcr.io/sjbrenchley89/free-claude-code:latest
# To:
#   image: ghcr.io/sjbrenchley89/free-claude-code:abc1234  # Previous SHA

# Restart with previous version
docker-compose pull
docker-compose up -d

# Verify
docker-compose ps
curl http://localhost:8000/health
```

### Restore from Backup

**If database/configuration was backed up:**

```bash
# Stop services
docker-compose down

# Restore from backup
tar -xzf backup-2024-09-03.tar.gz -C /opt/free-claude-code

# Restart
docker-compose up -d
```

### Emergency Downgrade

**Quick rollback to known working version:**

```bash
# Create rollback script
cat > /opt/free-claude-code/rollback.sh << 'EOF'
#!/bin/bash
set -e
echo "Rolling back to last known working version..."
cd /opt/free-claude-code
docker-compose down
git checkout main  # Or specific tag
docker-compose pull
docker-compose up -d
docker-compose exec -T fcc-server curl http://localhost:8000/health
echo "Rollback complete"
EOF

chmod +x /opt/free-claude-code/rollback.sh

# Run when needed
./rollback.sh
```

---

## Advanced Configuration

### Custom Environment Variables

**In .env file:**
```bash
# Application
LOG_LEVEL=info
PORT=8000
HOST=0.0.0.0

# API Keys
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...

# Providers
ENABLE_ANTHROPIC=true
ENABLE_OPENAI=true
ENABLE_OPENROUTER=false

# Performance
WORKER_PROCESSES=4
TIMEOUT_SECONDS=300
MAX_RETRIES=3
```

### Volume Mounts

**For persistent data:**

```yaml
volumes:
  - ./data:/app/data      # Logs, cache
  - ./config:/app/config  # User configuration
```

### Network Configuration

**Custom network (bridge mode):**

```yaml
networks:
  fcc-network:
    driver: bridge

services:
  fcc-server:
    networks:
      - fcc-network
```

### Resource Limits

**Modify in docker-compose.yml:**

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

---

## Support & Debugging

### Collect Debug Information

```bash
# Create debug report
cat > debug-report.txt << 'EOF'
=== System Info ===
$(uname -a)

=== Docker Version ===
$(docker --version)

=== Running Containers ===
$(docker-compose ps)

=== Recent Logs ===
$(docker-compose logs --tail 50)

=== Environment ===
$(docker-compose exec -T fcc-server env | grep -E 'PYTHONPATH|PATH|ENABLE')

=== Health Check ===
$(curl -s http://localhost:8000/health)
EOF

# Share for support
```

### Common Issues Matrix

| Issue | Cause | Solution |
|-------|-------|----------|
| Port already in use | Another service on 8000 | Change port in docker-compose.yml |
| Image pull fails | Network issue | Check internet, try `docker pull` directly |
| OOM killed | Memory limit too low | Increase memory limit |
| Slow startup | System load | Increase CPU or wait longer |
| API calls timeout | Network/API issue | Check API key, increase timeout |

---

## Next Steps

1. **Local Testing**: Start with `docker-compose up` locally
2. **Verify Functionality**: Access Admin UI and test configuration
3. **Deploy to Production**: Use deployment scripts or manual steps above
4. **Configure Monitoring**: Set up health check monitoring
5. **Document Changes**: Record any customizations
6. **Plan Backup**: Set up data backup procedures
7. **Review Security**: Ensure API keys and secrets are properly protected

---

## See Also

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Comprehensive deployment guide
- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) - Validation checklist
- [README.md](./README.md) - Project overview
- `.env.example` - Configuration template
- `nginx.conf.example` - Reverse proxy template

