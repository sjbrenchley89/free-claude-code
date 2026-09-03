# CI/CD Strategy & Deployment Pipeline

## Overview

This document describes the complete CI/CD and deployment pipeline for Free Claude Code, including automated testing, canary deployments, and automated rollbacks.

## Pipeline Architecture

```
Code Commit
    ↓
[CI: Tests & Linting] ← Tests, Ruff, Type Checking
    ↓ (if main)
[Docker Build & Push] ← Build image, push to ghcr.io
    ↓
[Canary Deployment] ← Deploy to 10% traffic, smoke tests
    ↓
[Health Monitor] ← Every 5 min, all 3 instances
    ↓
[Manual Approval] ← Promote to 50% traffic
    ↓
[Production Rollout] ← 100% traffic
    ↓
[Continuous Monitoring] ← Automated rollback if unhealthy
```

## Workflows

### 1. CI (tests.yml)

Runs on all pull requests targeting `main`.

**Checks:**
- Ban suppressions and legacy annotations
- Ruff format check
- Ruff linter checks
- Type checking (ty)
- Unit tests (pytest)
- E2E tests (playwright)

**Requirements:**
- All checks must pass before merge
- Status checks enforced via branch protection

**Example:**
```bash
# Run locally before pushing
./scripts/ci.sh
```

### 2. Docker Build & Push (docker-build.yml)

Triggered on:
- Push to `main` or `claude/fcc-server-deployment-*` branches
- Changes to: Dockerfile, docker-compose.yml, .dockerignore, src/, pyproject.toml, uv.lock

**Actions:**
- Build Docker image with buildx
- Push to ghcr.io with semantic version tags
- Cache layers for faster rebuilds
- Generate image digest

**Image Tags:**
- `ghcr.io/sjbrenchley89/free-claude-code:5.19.2` (semver)
- `ghcr.io/sjbrenchley89/free-claude-code:5.19` (major.minor)
- `ghcr.io/sjbrenchley89/free-claude-code:abc1234` (commit SHA)
- `ghcr.io/sjbrenchley89/free-claude-code:latest` (if on main)

**Manual Trigger:**
Go to Actions tab → Docker Build & Push → Run workflow

### 3. Canary Deployment (canary-deploy.yml)

Triggered on Docker build success or manual workflow_dispatch.

**Deployment Stages:**

#### Stage 1: 10% Canary (Automatic)
```bash
# Deploys to 1 instance (out of 10 total)
# Run smoke tests
# Monitor health checks
# Wait for manual approval
```

**What happens:**
1. Pull latest Docker image
2. Update docker-compose.yml with new image
3. Scale service: 1 canary, 9 production
4. Run health checks on canary
5. Run smoke tests (basic API tests)
6. Monitor metrics

**Health Checks:**
- Endpoint: `/health`
- Response: `{"status": "healthy"}`
- Frequency: Every 2 seconds
- Timeout: 30 seconds max wait

**Smoke Tests:**
```bash
# Tests run against canary
curl http://localhost:8001/health          # Health check
curl http://localhost:8001/v1/messages     # API availability
curl http://localhost:8001/v1/chat/completions  # Chat API
curl http://localhost:8001/admin/          # Admin UI
```

#### Stage 2: 50% Traffic (Manual Approval)
```bash
# Workflow dispatch with canary_percentage=50
# Deploys to 5 instances
# Requires manual approval to proceed
```

**Approval Process:**
1. Review canary metrics (error rate, latency, CPU, memory)
2. Check application logs for errors
3. Approve via workflow_dispatch: `canary_percentage=50`
4. System promotes 50% of traffic to new version

**Metrics to Review:**
- HTTP error rate (target: <1%)
- P95 latency (target: <2s)
- Health check success (target: >99%)
- Memory usage (target: <80%)
- CPU usage (target: <70%)

#### Stage 3: 100% Production (Manual Approval)
```bash
# Workflow dispatch with canary_percentage=100
# Full production rollout
# All traffic on new version
```

**Rollout Process:**
1. Verify 50% canary metrics healthy
2. Review final checklist
3. Approve via workflow_dispatch: `canary_percentage=100`
4. System routes all traffic to new version

**Post-Rollout:**
- Monitor continuously for 24 hours
- Watch error rates, latency, resource usage
- Be ready for immediate rollback if needed

### 4. Automated Rollback (auto-rollback.yml)

Runs every 5 minutes via scheduled job.

**Rollback Triggers:**
- Health check fails 5+ times consecutively
- Service becomes unresponsive
- Manual trigger via workflow_dispatch

**Rollback Process:**
1. Detect health check failures
2. Fetch previous stable version from registry
3. Pull previous stable Docker image
4. Update docker-compose.yml to use previous version
5. Restart service
6. Verify rollback successful
7. Create incident issue
8. Notify on-call team

**Manual Rollback:**
```bash
# Via workflow dispatch
# Select "Automated Rollback" workflow
# Input: reason (e.g., "Critical bug in v5.19.2")
# System automatically rolls back to last known good
```

**Git Rollback (if needed):**
```bash
git revert <commit-sha>
git push origin main
# Docker pipeline will pick up new commit and rebuild
```

### 5. Production Smoke Tests (smoke-tests-production.yml)

Runs every 30 minutes and after canary deployment.

**Tests:**
- Health endpoint (`/health`)
- Messages API (`/v1/messages`)
- Chat Completions API (`/v1/chat/completions`)
- Admin UI (`/admin`)
- Response time measurement
- Resource usage check
- Failover capability (production only)

**Smoke Test Report:**
Generated and uploaded as artifact after each run.

```bash
# View latest report
# Actions → Smoke Tests Production → Latest run → Artifacts
```

**Failure Response:**
- Trigger incident creation
- Notify on-call team
- Begin root cause analysis
- Prepare rollback if needed

### 6. Deployment Gates (deployment-gates.yml)

Runs on pull requests to `main`.

**Pre-Deployment Checks:**
- CI status passing
- Version bump in pyproject.toml (if production changes)
- No breaking changes detected
- Documentation updated (recommended)
- Tests added (recommended)

**Deployment Readiness Report:**
Comments on PR with:
- Check results
- Deployment strategy (canary)
- Post-deployment monitoring plan
- Rollback procedure

**Approval Label:**
Add `ready-for-deployment` label to trigger approval workflow.

## Deployment Checklist

### Before Merging to Main

- [ ] All CI checks passing (GitHub shows green)
- [ ] Version bumped in pyproject.toml
- [ ] uv.lock updated (run `uv lock`)
- [ ] CHANGELOG.md updated with changes
- [ ] Documentation updated (if applicable)
- [ ] New tests added for new features

### After Merge (Automatic)

- [ ] Docker image builds successfully
- [ ] Image pushes to ghcr.io
- [ ] Canary deployment starts (10% traffic)
- [ ] Smoke tests run and pass
- [ ] On-call team notified of canary deployment

### Manual Promotion Steps

#### Promote to 50% Traffic
1. Go to Actions → Canary Deployment
2. Click "Run workflow"
3. Set `canary_percentage` to `50`
4. Review canary metrics in logs
5. Verify health checks passing
6. Click "Run"

#### Promote to 100% Production
1. Monitor 50% canary for 15-30 minutes
2. Go to Actions → Canary Deployment
3. Click "Run workflow"
4. Set `canary_percentage` to `100`
5. Click "Run"

### Post-Deployment Monitoring

- [ ] Monitor logs for 24 hours: `docker-compose logs -f`
- [ ] Check error rates in monitoring dashboard
- [ ] Verify no alerts triggered
- [ ] Confirm all health checks passing
- [ ] Review resource usage (CPU, memory)

## Emergency Procedures

### Immediate Rollback (Critical Issue)

**Option 1: Automatic Rollback**
- System detects health failures
- Automatically reverts to previous stable version
- Creates incident issue
- Notifies on-call team

**Option 2: Manual Rollback via GitHub**
1. Go to Actions → Automated Rollback
2. Click "Run workflow"
3. Set reason (e.g., "Critical bug in v5.19.2")
4. Click "Run"
5. System rolls back within 2 minutes

**Option 3: Manual Rollback via Git**
```bash
git revert <commit-sha>  # Revert the bad commit
git push origin main     # Push revert
# Docker pipeline automatically builds and deploys
```

**Option 4: Emergency Manual Restart (Last Resort)**
```bash
# On production server
cd /path/to/free-claude-code
docker pull ghcr.io/sjbrenchley89/free-claude-code:5.19.1  # Previous stable
sed -i 's/image:.*/image: ghcr.io\/sjbrenchley89\/free-claude-code:5.19.1/g' docker-compose.yml
docker-compose down && docker-compose up -d
```

## Monitoring & Alerts

### Key Metrics to Monitor

**Availability**
- Health check success rate (target: >99.9%)
- Uptime percentage (target: >99.95%)

**Performance**
- P50 latency (target: <500ms)
- P95 latency (target: <2s)
- P99 latency (target: <5s)

**Reliability**
- Error rate (target: <0.1%)
- 5xx error count (target: 0)
- Timeout count (target: 0)

**Resources**
- CPU usage (target: <70% average)
- Memory usage (target: <80% average)
- Disk usage (target: <80% used)
- Network I/O (monitor for spikes)

### Setting Up Alerts

**Docker Health Checks**
Already configured in docker-compose.yml:
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3 before unhealthy
- Status visible via `docker-compose ps`

**Custom Monitoring (Recommended)**
1. Set up Prometheus to scrape `/health` endpoint
2. Configure Grafana dashboards
3. Set PagerDuty alerts for critical metrics
4. Create incident runbooks for common issues

## Deployment Frequencies

**Production Deployments:**
- Small fixes/patches: As needed (ASAP)
- Minor features: Weekly (Fridays)
- Major changes: Bi-weekly with extended monitoring

**Recommended Deployment Window:**
- Time: 9:00 AM - 5:00 PM (business hours)
- Day: Monday - Friday
- With: On-call engineer available for 2 hours post-deploy

## Configuration for Your Infrastructure

### Local Docker Deployment
```bash
cd /path/to/free-claude-code
docker-compose up -d
# Canary workflows will skip (no load balancer detected)
# Manual promotion steps not needed
```

### Cloud Deployment (DigitalOcean/AWS)
1. Follow DEPLOYMENT_GUIDE_CLOUD.md
2. Set up load balancer to support canary traffic splits
3. Configure health check endpoints
4. Enable workflow approval environments
5. Set up monitoring via cloud provider tools

### Multi-Server Deployment
1. Set up shared docker registry access
2. Configure DNS/load balancer for traffic splitting
3. Synchronize deployment via orchestration (Kubernetes recommended)
4. Enable cross-server health checks

## Troubleshooting

### Canary Deployment Stuck at 10%
**Check:**
- Health checks passing? `curl http://localhost:8001/health`
- Error logs? `docker-compose logs fcc-server`
- Resource usage? `docker stats`

**Solutions:**
1. Review recent code changes
2. Check API key configuration
3. Verify upstream provider connectivity
4. Restart canary: `docker-compose restart fcc-server`

### Automatic Rollback Triggered
**Investigation:**
1. Check what was deployed: `docker-compose logs | tail -100`
2. Review recent commits: `git log -5`
3. Check error logs for root cause
4. Fix the issue and create new PR

### Smoke Tests Failing
**Check:**
1. Service health: `curl http://localhost:8000/health`
2. Service logs: `docker-compose logs fcc-server`
3. Network connectivity: `curl -v http://localhost:8000/health`
4. Port availability: `lsof -i :8000`

### Load Balancer Not Splitting Traffic
**For cloud deployments:**
1. Verify load balancer configuration
2. Check canary service registration
3. Confirm health check endpoint responding
4. Review load balancer logs

## Best Practices

1. **Version Bumping:** Always bump version in pyproject.toml for production changes
2. **Testing:** Add tests for new features before merging
3. **Gradual Rollout:** Never skip canary stage, always wait for approval
4. **Monitoring:** Watch first deployment for 24 hours
5. **Documentation:** Update docs when deployment process changes
6. **Runbooks:** Maintain incident response procedures
7. **Team Communication:** Notify team of deployments via Slack/email
8. **Audit Trail:** GitHub Actions logs provide full audit history

## See Also

- DEPLOYMENT_GUIDE_CLOUD.md — Cloud deployment instructions
- DEPLOYMENT_GUIDE_MANUAL.md — Manual VPS deployment
- DEPLOYMENT_CHECKLIST.md — Pre/post-deployment validation
- docker-compose.yml — Local deployment configuration
- pyproject.toml — Version and dependencies
