# Production Deployment Guide - Manual Setup

**Date**: September 3, 2026  
**Status**: Step-by-step deployment instructions for Linux/macOS servers

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Docker Installation](#docker-installation)
4. [Application Deployment](#application-deployment)
5. [Reverse Proxy Setup](#reverse-proxy-setup)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Health Checks & Monitoring](#health-checks--monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required
- Linux server (Ubuntu 20.04+ or similar) or macOS
- SSH access to the server
- sudo/root privileges for package installation
- Domain name (optional, but recommended for SSL)
- API keys for configured providers (Anthropic, OpenAI, etc.)

### Recommended
- 2+ CPU cores
- 2GB+ RAM
- 10GB+ disk space
- Firewall configured (ports 80, 443 open)

---

## Server Setup

### Step 1: SSH into Your Server

```bash
ssh user@your-server-ip
# or
ssh -i /path/to/key.pem user@your-server-ip
```

### Step 2: Update System Packages

```bash
# Update package lists
sudo apt-get update
sudo apt-get upgrade -y

# Install essential tools
sudo apt-get install -y \
  curl \
  wget \
  git \
  build-essential \
  apt-transport-https \
  ca-certificates \
  gnupg \
  lsb-release
```

### Step 3: Create Application User (Optional but Recommended)

```bash
# Create non-root user for app
sudo useradd -m -s /bin/bash fcc-user

# Add to sudo group (optional)
sudo usermod -aG sudo fcc-user

# Switch to app user
sudo su - fcc-user
```

### Step 4: Create Application Directory

```bash
# Create app directory
sudo mkdir -p /opt/free-claude-code
sudo chown -R $USER:$USER /opt/free-claude-code
cd /opt/free-claude-code
```

---

## Docker Installation

### Step 1: Add Docker Repository

```bash
# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### Step 2: Install Docker

```bash
# Update package lists
sudo apt-get update

# Install Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Step 3: Configure Docker Permissions

```bash
# Add current user to docker group
sudo usermod -aG docker $USER

# Apply group changes (logout and login, or run:)
newgrp docker

# Verify (should work without sudo)
docker ps
```

### Step 4: Enable Docker Service

```bash
# Start Docker service
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker

# Verify service status
sudo systemctl status docker
```

---

## Application Deployment

### Step 1: Clone Repository

```bash
cd /opt/free-claude-code

# Clone the repository
git clone https://github.com/sjbrenchley89/free-claude-code.git .

# Verify files
ls -la
```

### Step 2: Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit environment file with your settings
nano .env
# or
vi .env
```

**Key environment variables to set:**

```env
# API Provider Configuration
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here
OPENROUTER_API_KEY=your-openrouter-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=300
CONNECTION_POOL_SIZE=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Optional: Monitoring
SENTRY_DSN=your-sentry-dsn-if-using
```

### Step 3: Configure docker-compose

```bash
# Verify docker-compose.yml exists
cat docker-compose.yml

# Key configurations in docker-compose.yml:
# - Port: 8000 (internal)
# - Health check: Every 30 seconds
# - Restart: unless-stopped
# - Resource limits: 2 CPUs, 2GB RAM
```

### Step 4: Start Application with Docker Compose

```bash
# Build and start services
docker compose up -d

# Check if container started
docker compose ps

# View logs
docker compose logs -f

# Wait for health check to pass (check logs)
```

### Step 5: Verify Application is Running

```bash
# Check health endpoint (internal)
curl http://localhost:8000/health

# Should return:
# {"status": "healthy"}

# Check container status
docker compose ps

# Check resource usage
docker stats free-claude-code
```

---

## Reverse Proxy Setup

### Step 1: Install Nginx

```bash
# Install Nginx
sudo apt-get install -y nginx

# Start Nginx
sudo systemctl start nginx

# Enable on boot
sudo systemctl enable nginx

# Verify
sudo systemctl status nginx
```

### Step 2: Configure Nginx

```bash
# Copy example configuration
sudo cp nginx.conf.example /etc/nginx/sites-available/free-claude-code

# Enable the site
sudo ln -s /etc/nginx/sites-available/free-claude-code /etc/nginx/sites-enabled/

# Disable default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t
```

### Step 3: Customize Nginx Configuration

```bash
# Edit the configuration
sudo nano /etc/nginx/sites-available/free-claude-code
```

**Required changes:**
1. Replace `your-domain.com` with your actual domain
2. Update upstream backend address if needed (default: localhost:8000)
3. Configure SSL paths (in SSL section)

### Step 4: Reload Nginx

```bash
# Reload configuration
sudo systemctl reload nginx

# Verify
sudo systemctl status nginx

# Test connectivity
curl -H "Host: your-domain.com" http://localhost/health
```

---

## SSL/TLS Configuration

### Option 1: Using Let's Encrypt with Certbot (Recommended)

#### Step 1: Install Certbot

```bash
# Install certbot and Nginx plugin
sudo apt-get install -y certbot python3-certbot-nginx

# Verify installation
certbot --version
```

#### Step 2: Obtain Certificate

```bash
# Get certificate for your domain
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Follow prompts:
# - Enter email
# - Accept terms
# - Choose redirect option (recommend HTTPS redirect)
```

#### Step 3: Update Nginx Configuration

The Nginx configuration already includes SSL directives. Certbot will auto-update paths to:
- Certificate: `/etc/letsencrypt/live/your-domain.com/fullchain.pem`
- Key: `/etc/letsencrypt/live/your-domain.com/privkey.pem`

#### Step 4: Test SSL

```bash
# Test HTTPS connection
curl https://your-domain.com/health

# Should return:
# {"status": "healthy"}
```

#### Step 5: Auto-Renewal Setup

```bash
# Certbot automatically sets up renewal with systemd timer
# Verify renewal timer
sudo systemctl status certbot.timer

# Test renewal (dry-run)
sudo certbot renew --dry-run
```

### Option 2: Manual Certificate Management

```bash
# Place your certificate and key in:
/etc/ssl/certs/your-domain.com.crt
/etc/ssl/private/your-domain.com.key

# Update Nginx configuration paths
# Reload Nginx
sudo systemctl reload nginx
```

---

## Health Checks & Monitoring

### Step 1: Verify Health Endpoint

```bash
# Check health status
curl https://your-domain.com/health

# Should return 200 OK with:
# {"status": "healthy"}
```

### Step 2: Monitor Application Logs

```bash
# View Docker logs
docker compose logs -f free-claude-code

# Follow errors
docker compose logs -f free-claude-code | grep -i error

# Check specific time range
docker compose logs --since 10m free-claude-code
```

### Step 3: Monitor System Resources

```bash
# Check container resources
docker stats free-claude-code

# Check disk usage
df -h /opt/free-claude-code

# Check memory
free -h

# Check CPU
top
```

### Step 4: Set Up Automated Monitoring (Optional)

#### Health Check Script

```bash
# Create health check script
sudo tee /usr/local/bin/fcc-health-check.sh > /dev/null <<'EOF'
#!/bin/bash

HEALTH_URL="https://your-domain.com/health"
TIMEOUT=10
ALERT_EMAIL="your-email@example.com"

# Check health endpoint
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT $HEALTH_URL)

if [ "$STATUS" != "200" ]; then
    echo "Health check failed: HTTP $STATUS" >&2
    # Send alert (example with mail)
    echo "Free Claude Code health check failed at $(date)" | \
        mail -s "FCC Health Alert" "$ALERT_EMAIL"
    exit 1
fi

exit 0
EOF

# Make executable
sudo chmod +x /usr/local/bin/fcc-health-check.sh

# Test
/usr/local/bin/fcc-health-check.sh
```

#### Add to Cron

```bash
# Edit crontab
sudo crontab -e

# Add health check every 5 minutes
*/5 * * * * /usr/local/bin/fcc-health-check.sh
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs free-claude-code

# Common issues:
# 1. Port already in use
sudo lsof -i :8000
# Kill conflicting process or change port

# 2. Insufficient resources
docker stats

# 3. Corrupted image
docker compose down
docker rmi ghcr.io/sjbrenchley89/free-claude-code:latest
docker compose up -d
```

### Health Check Failing

```bash
# Test health endpoint directly
curl -v http://localhost:8000/health

# Test through proxy
curl -v -H "Host: your-domain.com" http://localhost/health

# Check container logs
docker compose logs free-claude-code | tail -20
```

### High Memory Usage

```bash
# Check current usage
docker stats free-claude-code

# Check for memory leaks
docker compose logs free-claude-code | grep -i memory

# Restart if needed
docker compose restart free-claude-code

# Reduce resource limit if necessary
# Edit docker-compose.yml and restart
```

### SSL Certificate Issues

```bash
# Check certificate expiration
openssl x509 -in /etc/letsencrypt/live/your-domain.com/fullchain.pem -text -noout | grep -i "not after"

# Renew certificate
sudo certbot renew -d your-domain.com

# Test renewal
sudo certbot renew --dry-run
```

### Nginx Connection Issues

```bash
# Check Nginx syntax
sudo nginx -t

# Check Nginx status
sudo systemctl status nginx

# View Nginx error log
sudo tail -f /var/log/nginx/error.log

# View access log
sudo tail -f /var/log/nginx/access.log
```

---

## Rollback Procedures

### Rollback to Previous Version

```bash
# Stop current container
docker compose down

# Pull previous image version
docker pull ghcr.io/sjbrenchley89/free-claude-code:previous-version-tag

# Update docker-compose.yml with previous version
# Then restart
docker compose up -d

# Verify rollback
curl https://your-domain.com/health
```

### Restore from Backup

```bash
# If you have backed up .env and data
# Stop application
docker compose down

# Restore files
cp /backup/path/.env .env

# Restart
docker compose up -d
```

### Quick Restart

```bash
# Restart application without stopping
docker compose restart free-claude-code

# Verify
curl https://your-domain.com/health
```

---

## Maintenance Tasks

### Weekly

- [ ] Check health endpoint
- [ ] Review logs for errors
- [ ] Monitor resource usage
- [ ] Backup .env file (if changes made)

### Monthly

- [ ] Check certificate expiration
- [ ] Update Docker images
- [ ] Review error logs for patterns
- [ ] Update dependencies if needed

### Quarterly

- [ ] Full system update
- [ ] Security audit
- [ ] Performance analysis
- [ ] Disaster recovery test

---

## Post-Deployment Verification

```bash
# 1. Health check
curl https://your-domain.com/health

# 2. Container status
docker compose ps

# 3. System resources
docker stats free-claude-code

# 4. Logs for errors
docker compose logs --tail=50

# 5. Network connectivity
curl -v https://your-domain.com/health

# 6. SSL certificate
openssl s_client -connect your-domain.com:443

# 7. API functionality
# Test with one of your configured providers
```

---

## Production Deployment Checklist

- [ ] Server prerequisites met (2+ CPU, 2GB+ RAM, 10GB+ disk)
- [ ] SSH access configured and tested
- [ ] System packages updated
- [ ] Docker and docker-compose installed
- [ ] Application directory created
- [ ] Repository cloned
- [ ] Environment variables configured (.env file)
- [ ] docker-compose.yml reviewed and customized
- [ ] Docker containers started and verified
- [ ] Health check passing
- [ ] Nginx installed and configured
- [ ] SSL certificate obtained (Let's Encrypt)
- [ ] Nginx SSL configuration completed
- [ ] HTTPS health check passing
- [ ] Monitoring script set up (optional)
- [ ] Logs reviewed for errors
- [ ] Resource usage monitored
- [ ] Backup procedures documented
- [ ] On-call procedures documented
- [ ] Team trained on deployment

---

## Quick Reference Commands

```bash
# Status
docker compose ps                    # Container status
docker compose logs -f               # View logs
docker stats                         # Resource usage
curl https://your-domain.com/health  # Health check

# Start/Stop/Restart
docker compose up -d                 # Start
docker compose down                  # Stop
docker compose restart               # Restart

# Updates
docker compose pull                  # Pull latest images
docker compose up -d                 # Restart with new images

# Maintenance
docker compose exec -it free-claude-code bash  # Shell access
docker compose logs --since 1h       # Logs from last hour
docker compose exec free-claude-code ps aux    # Container processes
```

---

## Getting Help

If deployment issues arise:

1. Check logs: `docker compose logs -f`
2. Check health: `curl http://localhost:8000/health`
3. Review nginx errors: `sudo tail -f /var/log/nginx/error.log`
4. Check resources: `docker stats`
5. Review documentation: `DOCKER_DEPLOYMENT_GUIDE.md`

---

**Deployment Guide Complete**

Your production deployment should now be:
- ✅ Running on Docker
- ✅ Accessible via your domain with SSL
- ✅ Protected by Nginx reverse proxy
- ✅ Health checks configured
- ✅ Monitoring set up

For cloud provider-specific setup, see DEPLOYMENT_GUIDE_CLOUD.md
