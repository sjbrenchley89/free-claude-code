# Production Deployment Guide - Cloud Providers

**Date**: September 3, 2026  
**Status**: Step-by-step setup for AWS, DigitalOcean, Azure, and Linode

---

## Table of Contents

1. [AWS Deployment](#aws-deployment)
2. [DigitalOcean Deployment](#digitalocean-deployment)
3. [Azure Deployment](#azure-deployment)
4. [Linode Deployment](#linode-deployment)
5. [Comparison & Recommendations](#comparison--recommendations)

---

## AWS Deployment

### Overview
- **Service**: EC2 (Elastic Compute Cloud)
- **Estimated Cost**: $5-20/month for small instance
- **Setup Time**: 10-15 minutes
- **Best For**: Organizations already using AWS

### Step 1: Create EC2 Instance

1. **Log in to AWS Console**
   - Go to https://console.aws.amazon.com
   - Navigate to EC2 Dashboard

2. **Launch New Instance**
   - Click "Launch Instances"
   - Select "Ubuntu Server 22.04 LTS (Free tier eligible)"
   - Instance type: `t3.small` (2 CPU, 2GB RAM) - minimum recommended
   - For free tier: `t2.micro` (sufficient for testing)

3. **Configure Security Group**
   - Allow inbound traffic:
     - SSH (port 22) from your IP
     - HTTP (port 80) from anywhere
     - HTTPS (port 443) from anywhere

4. **Create/Select Key Pair**
   - Create new key pair: `free-claude-code-prod.pem`
   - Download and secure: `chmod 400 free-claude-code-prod.pem`

5. **Launch Instance**
   - Note the public IP address
   - Wait 2-3 minutes for instance to start

### Step 2: Connect and Configure

```bash
# Connect via SSH
ssh -i free-claude-code-prod.pem ubuntu@your-ec2-public-ip

# Once connected, follow DEPLOYMENT_GUIDE_MANUAL.md steps:
# - Update system packages
# - Install Docker
# - Deploy application

# Or use the automated deployment script:
curl -fsSL https://raw.githubusercontent.com/sjbrenchley89/free-claude-code/main/scripts/deploy.sh | bash
```

### Step 3: Elastic IP (Optional but Recommended)

```bash
# In AWS Console:
# 1. Go to Elastic IPs
# 2. Allocate new address
# 3. Associate with your instance
# Benefits: Static IP that persists if instance restarts
```

### Step 4: Configure Domain

1. **Route 53** (AWS DNS) or **External DNS Provider**
   - Create A record pointing to Elastic IP
   - Wait for propagation (5-30 minutes)

```bash
# Test DNS resolution
nslookup your-domain.com
```

### Step 5: SSL Certificate

```bash
# Once connected to instance:
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Or use nginx plugin (after Nginx installation):
sudo certbot certonly --nginx -d your-domain.com
```

### Step 6: Monitor in AWS Console

- **CloudWatch**: Monitor CPU, memory, network
- **Auto Scaling**: Set up scaling policies (optional)
- **Backup**: Use EBS snapshots for backup

### Cost Estimation

| Item | Cost |
|------|------|
| t3.small EC2 instance | $5-10/month |
| Elastic IP (if unused) | $3/month |
| Data transfer (est. 100GB) | $9/month |
| S3 backup (optional) | $1-5/month |
| **Total** | **$15-25/month** |

---

## DigitalOcean Deployment

### Overview
- **Service**: Droplets (Virtual Private Servers)
- **Estimated Cost**: $4-6/month for basic droplet
- **Setup Time**: 5-10 minutes
- **Best For**: Simple, straightforward deployments

### Step 1: Create Droplet

1. **Create Account** (if needed)
   - Go to https://digitalocean.com
   - Sign up and verify email

2. **Create Droplet**
   - Click "Create" → "Droplets"
   - **Choose Image**: Ubuntu 22.04 LTS
   - **Choose Size**: $6/month (2GB RAM, 2 vCPU, 50GB SSD)
   - **Choose Region**: Closest to your users
   - **Additional Options**:
     - ✓ Enable backups
     - ✓ Enable IPv6
   - **Authentication**: Add SSH key
     - If you don't have one: `ssh-keygen -t rsa -N "" -f ~/.ssh/do_key`
     - Paste public key content (from `~/.ssh/do_key.pub`)

3. **Create Droplet**
   - Note the IP address
   - Wait 1-2 minutes for setup

### Step 2: Initial Connection

```bash
# Connect via SSH
ssh -i ~/.ssh/do_key root@your-droplet-ip

# (If using password) ssh root@your-droplet-ip
```

### Step 3: Automated Deployment

```bash
# Option A: Using deployment script
curl -fsSL https://raw.githubusercontent.com/sjbrenchley89/free-claude-code/main/scripts/deploy.sh | bash

# Option B: Manual deployment
# Follow DEPLOYMENT_GUIDE_MANUAL.md steps
```

### Step 4: Configure Firewall

```bash
# DigitalOcean Firewall (recommended):
# 1. In console, go to Firewalls
# 2. Create new firewall
# 3. Inbound rules:
#    - SSH (port 22) from your IP
#    - HTTP (port 80) from anywhere
#    - HTTPS (port 443) from anywhere
# 4. Outbound: Allow all
# 5. Assign to your Droplet

# Or configure ufw on Droplet:
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Step 5: Configure Domain

```bash
# Option A: Use DigitalOcean DNS
# 1. Add domain in DigitalOcean console
# 2. Update nameservers at registrar
# 3. Create A record → Droplet IP

# Option B: Use existing DNS provider
# Create A record: your-domain.com → Droplet IP
```

### Step 6: SSL Certificate

```bash
# On Droplet:
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com
# Or --standalone if Nginx not running yet

# Auto-renewal:
sudo certbot renew --dry-run
```

### DigitalOcean App Platform (Alternative)

For completely managed deployment (no server management):

```bash
# 1. Go to App Platform
# 2. Connect GitHub repository
# 3. Select branch with Dockerfile
# 4. Configure:
#    - HTTP port: 8000
#    - Environment variables
# 5. Deploy (automatic on git push)
# Cost: ~$12/month for basic tier
```

### Cost Estimation

| Item | Cost |
|------|------|
| $6/month Droplet | $6/month |
| Backups (20%) | $1.20/month |
| Domain (external) | $10-15/year |
| **Total** | **$7-8/month** |

**DigitalOcean Referral**: If interested, referral links give $100 credit

---

## Azure Deployment

### Overview
- **Service**: App Service (managed containers) or VM
- **Estimated Cost**: $10-20/month
- **Setup Time**: 10-15 minutes
- **Best For**: Enterprise environments, hybrid cloud

### Step 1: Using App Service (Easiest)

1. **Create Account**
   - Go to https://portal.azure.com
   - Sign up with Microsoft account

2. **Create Resource Group**
   - Click "Create a resource"
   - Search "Resource Group"
   - Create: `free-claude-code-rg`

3. **Create App Service**
   - Click "Create a resource"
   - Search "Web App"
   - Click "Create"
   - **Basics Tab**:
     - Resource Group: `free-claude-code-rg`
     - Name: `free-claude-code-prod`
     - Publish: Docker Container
     - Operating System: Linux
   - **Docker Tab**:
     - Image Source: Docker Hub (or Azure Container Registry)
     - Image and tag: `ghcr.io/sjbrenchley89/free-claude-code:latest`
     - OR: Build custom image
   - Review and Create

### Step 2: Configure Environment Variables

```bash
# In App Service settings:
# 1. Go to Configuration
# 2. Add Application Settings:
#    - ANTHROPIC_API_KEY = your-key
#    - OPENAI_API_KEY = your-key
#    - etc. (from .env.example)
# 3. Save
```

### Step 3: Configure Domain

```bash
# In App Service:
# 1. Go to Custom domains
# 2. Add custom domain
# 3. Follow DNS validation instructions
# 4. Azure auto-provides SSL
```

### Step 4: Monitor

```bash
# In App Service:
# 1. Go to Monitoring
# 2. View metrics:
#    - CPU/Memory usage
#    - HTTP request count
#    - Response times
# 3. Set up alerts
```

### Step 2 (Alternative): Using Azure VM

If you prefer full control:

```bash
# 1. Create Resource Group
# 2. Create Ubuntu VM (Standard B2s or better)
# 3. Open ports: SSH (22), HTTP (80), HTTPS (443)
# 4. SSH in and follow DEPLOYMENT_GUIDE_MANUAL.md
```

### Cost Estimation

| Item | Cost |
|------|------|
| App Service (Basic tier) | $10-15/month |
| Custom domain | $10-15/year |
| SSL certificate | Free (Azure managed) |
| **Total** | **$10-15/month** |

---

## Linode Deployment

### Overview
- **Service**: Linode (managed Linux cloud)
- **Estimated Cost**: $5-10/month
- **Setup Time**: 5-10 minutes
- **Best For**: Developers, transparent pricing

### Step 1: Create Linode

1. **Create Account**
   - Go to https://linode.com
   - Sign up and verify

2. **Create Linode**
   - Click "Create" → "Linode"
   - **Choose Image**: Ubuntu 22.04 LTS
   - **Choose Region**: Closest to users
   - **Choose Type**: Linode 2GB (2 vCPU, 2GB RAM, 50GB SSD) = $10/month
     - Or: Linode 1GB for $5/month (sufficient for testing)
   - **Linode Label**: `free-claude-code-prod`
   - **Add SSH Key**: Copy public key content
   - **Create Linode**

3. **Boot Linode**
   - Wait 2-3 minutes
   - Note the IP address

### Step 2: Connect via SSH

```bash
# Connect to Linode
ssh root@your-linode-ip

# (Or with key):
ssh -i ~/.ssh/id_rsa root@your-linode-ip
```

### Step 3: Automated Deployment

```bash
# Quick setup with deployment script:
curl -fsSL https://raw.githubusercontent.com/sjbrenchley89/free-claude-code/main/scripts/deploy.sh | bash

# Or manual setup:
# Follow DEPLOYMENT_GUIDE_MANUAL.md
```

### Step 4: Configure Domain (Linode DNS)

```bash
# Option A: Use Linode DNS Manager
# 1. In Linode console: Domains → Create Domain
# 2. Add A record pointing to Linode IP
# 3. Update nameservers at registrar

# Option B: External DNS provider
# Create A record: your-domain.com → Linode IP
```

### Step 5: SSL Certificate

```bash
# On Linode:
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate:
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com
```

### Step 6: Monitoring

```bash
# Linode Manager:
# 1. View graphs for CPU, RAM, I/O
# 2. Set up alerts
# 3. Create backups (automated)

# Command line monitoring:
top
free -h
df -h
```

### Cost Estimation

| Item | Cost |
|------|------|
| Linode 2GB | $10/month |
| Backup (20%) | $2/month |
| Domain (external) | $10-15/year |
| **Total** | **$12-13/month** |

---

## Comparison & Recommendations

### Feature Comparison

| Feature | AWS | DigitalOcean | Azure | Linode |
|---------|-----|--------------|-------|--------|
| **Startup Time** | 5 min | 2 min | 5 min | 2 min |
| **Ease of Use** | Medium | Easy | Medium | Easy |
| **Minimum Cost** | $5/mo | $4/mo | $10/mo | $5/mo |
| **Management** | Requires effort | Easy | Varies | Easy |
| **Free Tier** | Yes (1 year) | Yes ($100) | Yes (12 months) | Yes ($100) |
| **Scalability** | Excellent | Very Good | Excellent | Good |
| **Support** | Good | Excellent | Very Good | Good |
| **Container Support** | Good | Very Good | Excellent | Good |

### Recommendations

**For Budget-Conscious Users**
→ **DigitalOcean** ($4-6/month)
- Simple, straightforward
- Great documentation
- Affordable pricing
- Quick setup

**For Enterprise/Scale**
→ **AWS** ($15-25/month)
- Auto-scaling
- Full ecosystem
- Enterprise support
- Most flexible

**For Managed Simplicity**
→ **Azure App Service** ($10-15/month)
- Completely managed
- No server management
- Auto-SSL
- Easy monitoring

**For Developer-Friendly**
→ **Linode** ($10-12/month)
- Clear pricing
- Excellent documentation
- Good performance
- Transparent resource allocation

---

## General Cloud Deployment Flow

1. **Create Account** with provider
2. **Create Computing Resource** (Droplet/Instance/VM)
3. **Connect via SSH**
4. **Run Deployment Script** OR manually deploy
5. **Configure Domain** (DNS records)
6. **Set Up SSL** (automatic or certbot)
7. **Configure Environment Variables**
8. **Monitor** performance and logs

---

## Deployment Scripts for Cloud Providers

### Fully Automated Setup

```bash
# The deployment script handles:
# ✅ System package updates
# ✅ Docker installation
# ✅ Repository clone
# ✅ Environment setup
# ✅ Application start
# ✅ Nginx configuration
# ✅ SSL setup (if domain configured)

# Works on all Linux providers:
curl -fsSL https://raw.githubusercontent.com/sjbrenchley89/free-claude-code/main/scripts/deploy.sh | bash

# For Windows:
# (From PowerShell as Administrator)
# See: scripts/deploy.ps1 in repository
```

---

## Security Considerations for Cloud

### Before Deploying

- [ ] Set up firewall rules
- [ ] Configure SSH key authentication (disable password)
- [ ] Enable automatic backups
- [ ] Set up monitoring/alerts
- [ ] Use strong API keys
- [ ] Enable SSL/TLS

### On-Going

- [ ] Monitor security advisories
- [ ] Keep system packages updated
- [ ] Review access logs
- [ ] Rotate keys periodically
- [ ] Audit Docker images for vulnerabilities

---

## Disaster Recovery

### Backup Strategy

```bash
# Automated backups (provider-specific):
# - AWS: EBS snapshots
# - DigitalOcean: Automated backups (enabled by default)
# - Azure: Backup policies
# - Linode: Automated backups

# Manual backup of critical data:
docker compose exec free-claude-code tar czf /backup/app-backup.tar.gz /app
```

### Quick Restore

```bash
# Stop application
docker compose down

# Restore from backup
tar xzf /backup/app-backup.tar.gz -C /

# Restart
docker compose up -d
```

---

## Post-Deployment

### Verification Checklist

- [ ] Application running (docker compose ps)
- [ ] Health check passing (curl https://your-domain.com/health)
- [ ] Logs clean (docker compose logs)
- [ ] Resources monitored
- [ ] SSL certificate valid
- [ ] Domain resolving correctly
- [ ] Backups enabled
- [ ] Alerts configured

### Next Steps

1. **Test API Connectivity**
   - Verify configured providers work
   - Test with sample requests

2. **Monitor Performance**
   - CPU/Memory usage
   - Response times
   - Error rates

3. **Set Up Alerts**
   - Health check failures
   - High resource usage
   - Certificate expiration

4. **Document Runbooks**
   - How to restart service
   - How to update image
   - How to troubleshoot issues

---

## Troubleshooting by Provider

### AWS
- Check EC2 console for instance status
- Review CloudWatch logs
- Verify security group rules
- Check Elastic IP association

### DigitalOcean
- Use Droplet console in web browser
- Check resource usage graphs
- Verify firewall rules
- Review networking settings

### Azure
- Check App Service Health Check
- View Application Insights
- Review Application Gateway settings
- Check SSL certificates

### Linode
- Use Linode Manager console
- Check resource graphs
- Verify firewall configuration
- Review DNS settings

---

## Getting Production Deployment Help

| Issue | Resource |
|-------|----------|
| Docker | DEPLOYMENT_GUIDE_MANUAL.md |
| Nginx | nginx.conf.example |
| SSL/TLS | Let's Encrypt setup (certbot) |
| DNS | Provider-specific DNS docs |
| Monitoring | Provider monitoring dashboard |

---

**Cloud Deployment Guide Complete**

Choose your provider above and follow the step-by-step instructions to get production deployment running in 10-15 minutes.

For additional help, see:
- DEPLOYMENT_GUIDE_MANUAL.md (manual server setup)
- DOCKER_DEPLOYMENT_GUIDE.md (Docker-specific)
- ENVIRONMENT_SETUP.md (configuration reference)
