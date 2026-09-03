# Free Claude Code - Docker Deployment Guide

This guide explains how to deploy the Free Claude Code server using Docker and Docker Compose.

## Quick Start

### Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ (included with Docker Desktop)
- Port 8000 available (or configure alternative port)

### Local Development (5 minutes)

```bash
# Clone the repository
git clone https://github.com/sjbrenchley89/free-claude-code.git
cd free-claude-code

# Start the server
docker-compose up -d

# Check logs
docker-compose logs -f fcc-server

# Access the Admin UI
# Open http://localhost:8000 in your browser
```

The server will be available at `http://localhost:8000`

### Stop the server

```bash
docker-compose down
```

---

## Configuration

### Using Environment Variables

Create a `.env` file in the project root with your provider API keys:

```bash
# Provider API Keys
NVIDIA_NIM_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here

# Optional: Admin authentication token
ADMIN_TOKEN=your-secure-token-here

# Logging level (INFO, DEBUG, WARNING, ERROR)
LOG_LEVEL=INFO
```

Then start the container:

```bash
docker-compose up -d
```

The environment variables will be automatically loaded from the `.env` file.

### Changing the Port

To run on a different port (e.g., 3000):

```bash
PORT=3000 docker-compose up -d
```

Or edit `docker-compose.yml` and change:
```yaml
ports:
  - "3000:8000"  # Access at port 3000 locally, server runs on 8000 internally
```

---

## Deployment Scenarios

### 1. Local Development

```bash
docker-compose up
```

- Runs in foreground, see all logs
- Auto-restarts on error
- Perfect for testing configuration changes

### 2. Production Server (Linux VPS)

**Setup:**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone and deploy
git clone https://github.com/sjbrenchley89/free-claude-code.git
cd free-claude-code

# Create secure .env file
nano .env  # Add your API keys
chmod 600 .env

# Start the server
docker-compose up -d

# Verify it's running
docker ps
docker-compose logs fcc-server
```

**Access from outside your machine:**

```bash
# Check your server's IP
hostname -I

# Access from another machine at http://<your-server-ip>:8000
```

**Reverse Proxy (Nginx) - Optional but Recommended**

For production, use a reverse proxy to handle HTTPS:

1. Install and configure Nginx:
   ```bash
   sudo apt-get install nginx
   ```

2. Create `/etc/nginx/sites-available/fcc-server`:
   ```nginx
   upstream fcc_backend {
       server localhost:8000;
   }

   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://fcc_backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. Enable and restart:
   ```bash
   sudo ln -s /etc/nginx/sites-available/fcc-server /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### 3. Docker Compose with Custom Resources

Edit `docker-compose.yml` to adjust resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'        # Increase CPU allocation
      memory: 4G       # Increase memory allocation
    reservations:
      cpus: '2'
      memory: 2G
```

Then restart:
```bash
docker-compose up -d
```

### 4. Building Your Own Image

To build a custom Docker image locally:

```bash
docker build -t my-fcc-server:latest .
docker run -d -p 8000:8000 --env-file .env my-fcc-server:latest
```

### 5. Using Docker Hub / GitHub Container Registry

The CI/CD pipeline automatically builds and pushes images to GitHub Container Registry.

**Pull and run pre-built image:**

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  ghcr.io/alishahryar1/free-claude-code:latest
```

---

## Health Checks

The container includes automatic health checks. To verify the server is healthy:

```bash
# Check container health
docker-compose ps

# Manual health check
curl http://localhost:8000/health

# View detailed logs
docker-compose logs fcc-server
```

---

## Updating the Server

### Pull Latest Changes

```bash
git pull origin main
docker-compose pull
docker-compose up -d
```

### Rebuild from Source

```bash
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
PORT=3000 docker-compose up -d
```

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs fcc-server

# Common issues:
# - Port already in use
# - Missing API keys
# - Insufficient disk space
# - Docker daemon not running
```

### Out of Memory

Increase Docker's memory limit:

1. **Docker Desktop (Mac/Windows)**: Settings → Resources → Memory
2. **Linux**: Edit `docker-compose.yml` resource limits

### Slow Performance

- Increase CPU/memory allocation
- Check system resources: `docker stats`
- Monitor logs: `docker-compose logs -f fcc-server`

---

## Production Best Practices

1. **Use Strong Passwords**
   ```bash
   openssl rand -base64 32  # Generate secure token
   ```

2. **Enable HTTPS**
   - Use reverse proxy (Nginx, Caddy)
   - Install SSL certificate (Let's Encrypt)

3. **Backup Configuration**
   ```bash
   cp .env .env.backup
   ```

4. **Monitor Logs**
   ```bash
   docker-compose logs -f --tail=50 fcc-server
   ```

5. **Auto-restart on Reboot**
   ```bash
   docker-compose up -d  # restart_policy is set to unless-stopped
   ```

6. **Resource Limits**
   - Set appropriate CPU/memory in `docker-compose.yml`
   - Monitor with `docker stats`

---

## Docker Commands Reference

```bash
# Start service
docker-compose up -d

# Stop service
docker-compose down

# View logs
docker-compose logs -f fcc-server

# View container status
docker-compose ps

# Restart service
docker-compose restart

# Rebuild and restart
docker-compose up -d --build

# Remove everything (including volumes)
docker-compose down -v

# Access container shell
docker-compose exec fcc-server bash

# View resource usage
docker stats
```

---

## Environment Variables Reference

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address for the server |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ADMIN_TOKEN` | (empty) | Optional bearer token for Admin UI |

### Provider API Keys

Uncomment and set in `.env` file:

```bash
NVIDIA_NIM_API_KEY=
OPENROUTER_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
AZURE_OPENAI_API_KEY=
MISTRAL_API_KEY=
DEEPSEEK_API_KEY=
# ... and many more
```

See `.env.example` for complete list.

---

## Support & Documentation

- **GitHub Repository**: https://github.com/sjbrenchley89/free-claude-code
- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose Reference**: https://docs.docker.com/compose/compose-file/
- **Free Claude Code Docs**: See README.md

---

## Contributing

For issues or improvements to this deployment guide:
1. Open an issue on GitHub
2. Submit a pull request with improvements
3. Follow the project's contribution guidelines

---

Generated by Claude Code - https://claude.ai/code
