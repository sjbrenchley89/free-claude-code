# CI/CD Pipeline Validation Guide

This guide walks through validating each component of the newly deployed CI/CD pipeline.

## **Prerequisites**

Before starting validation, ensure:
- [ ] PR #14 is merged to `main`
- [ ] You have access to GitHub Actions in the repository
- [ ] Docker image is pushed to `ghcr.io/sjbrenchley89/free-claude-code`
- [ ] Production environment (or test environment) is accessible
- [ ] Load balancer or traffic splitting capability is available (for canary deployment)

---

## **Validation Checklist**

### **Phase 1: Workflow Infrastructure** ✓ Ready to Test

#### 1.1 Verify Workflow Files Exist
```bash
cd /home/user/free-claude-code
ls -la .github/workflows/ | grep -E "canary|rollback|smoke|deployment-gates"
```

**Expected Output:**
- ✓ `canary-deploy.yml` 
- ✓ `auto-rollback.yml`
- ✓ `smoke-tests-production.yml`
- ✓ `deployment-gates.yml`

#### 1.2 Verify Workflow Syntax
Visit: `https://github.com/sjbrenchley89/free-claude-code/actions`

Check that all 4 workflows appear in the Actions tab:
- [ ] Canary Deployment
- [ ] Automated Rollback  
- [ ] Production Smoke Tests
- [ ] Deployment Gates & Approvals

---

### **Phase 2: Manual Canary Deployment Test** 🚀 Next Step

#### 2.1 Trigger Manual Canary Deployment

**Step 1:** Go to GitHub Actions
```
https://github.com/sjbrenchley89/free-claude-code/actions/workflows/canary-deploy.yml
```

**Step 2:** Click "Run workflow" → Fill in parameters:
```
Branch: main
Image tag: latest (or specific SHA)
Canary percentage: 10
```

**Step 3:** Click "Run workflow"

**Step 4:** Monitor workflow execution:
- [ ] Checkout succeeds
- [ ] Image tag determined
- [ ] Docker image pulled and verified
- [ ] Canary deployment step completes
- [ ] Health check passes (http://localhost:8001/health)
- [ ] Smoke tests pass (5/5 tests)

#### 2.2 Expected Workflow Output

```
✓ Image verified: ghcr.io/sjbrenchley89/free-claude-code:abc1234
✓ Canary deployment prepared
✓ Canary health check passed
✓ Smoke test 1 passed
✓ Smoke test 2 passed
✓ Smoke test 3 passed
✓ Smoke test 4 passed
✓ Smoke test 5 passed
```

**Acceptance Criteria:**
- [ ] Workflow completes successfully (no errors)
- [ ] All health checks pass
- [ ] All smoke tests pass
- [ ] Docker container is running the new image

---

### **Phase 3: Traffic Promotion Test** 📊 Manual Gate

#### 3.1 Promote to 50% Traffic

**Step 1:** Go back to Canary Deployment workflow:
```
https://github.com/sjbrenchley89/free-claude-code/actions/workflows/canary-deploy.yml
```

**Step 2:** Click "Run workflow" with parameters:
```
Branch: main
Image tag: latest
Canary percentage: 50  ← Change from 10 to 50
```

**Step 3:** Monitor for:
- [ ] Load balancer splits traffic 50/50
- [ ] Service remains healthy on both versions
- [ ] No errors in logs
- [ ] Response times consistent

#### 3.2 Promote to 100% Traffic

**Step 1:** Run workflow again with:
```
Canary percentage: 100
```

**Step 2:** Verify:
- [ ] All traffic on new version
- [ ] Health checks passing
- [ ] Metrics stable
- [ ] Error rate < 0.1%

---

### **Phase 4: Smoke Tests Validation** 🧪 Automated

#### 4.1 Manual Smoke Test Trigger

Go to: `https://github.com/sjbrenchley89/free-claude-code/actions/workflows/smoke-tests-production.yml`

**Step 1:** Click "Run workflow" with environment: `production`

**Step 2:** Monitor test results:
- [ ] Health endpoint returns 200 OK
- [ ] Messages API responds
- [ ] Chat Completions API responds
- [ ] Admin UI accessible
- [ ] Response times < 2s (P95)

#### 4.2 Scheduled Test Execution

The workflow runs automatically every 30 minutes:
- [ ] Check that tests are scheduled to run
- [ ] Monitor at least 2 automated runs to verify consistency
- [ ] Download and review smoke test report from artifacts

**Report Location:**
```
Actions → Production Smoke Tests → Latest Run → Artifacts
```

---

### **Phase 5: Health Monitoring Test** 📈 Continuous

#### 5.1 Monitor Health Checks

The workflow monitors `/health` endpoint every 5 minutes:

```bash
# Test health endpoint manually
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

#### 5.2 Check Monitoring Dashboard

Set up monitoring to watch:
- [ ] Health check success rate (target: >99.9%)
- [ ] Response time P95 (target: <2s)
- [ ] Error rate (target: <0.1%)
- [ ] Container memory usage (target: <80%)
- [ ] Container CPU usage (target: <70%)

---

### **Phase 6: Automated Rollback Test** 🔄 Failure Scenario

#### 6.1 Manual Rollback Trigger

Go to: `https://github.com/sjbrenchley89/free-claude-code/actions/workflows/auto-rollback.yml`

**Step 1:** Click "Run workflow" with:
```
Reason: "Test rollback procedure"
Rollback to: "previous-stable"
```

**Step 2:** Verify rollback sequence:
- [ ] Health checks detected as failed
- [ ] Previous stable version identified
- [ ] Image pulled successfully
- [ ] docker-compose.yml updated
- [ ] Service restarted
- [ ] Health checks verify new version is healthy

#### 6.2 Verify Rollback Completed

Check that:
- [ ] Service is running previous version
- [ ] Health endpoint responding
- [ ] All tests passing
- [ ] Incident issue created in GitHub

---

### **Phase 7: Deployment Gates Test** 🚪 Pre-Merge

#### 7.1 Create Test PR

**Step 1:** Create a new branch:
```bash
git checkout -b test/ci-validation
```

**Step 2:** Make a small change to a production file:
```bash
echo "# Test change" >> README.md
```

**Step 3:** Bump version (required for production changes):
```bash
# Edit pyproject.toml: 5.19.3 → 5.19.4
uv lock
git add pyproject.toml uv.lock README.md
git commit -m "Test: CI/CD validation"
git push origin test/ci-validation
```

**Step 4:** Open PR to `main`

#### 7.2 Verify Deployment Gates

Check that the PR has:
- [ ] Pre-Deployment Checks workflow runs
- [ ] CI Status shows: ✓ Passing
- [ ] Version Bump shows: ✓ Yes
- [ ] Breaking Changes shows: ✓ None
- [ ] Deployment Readiness comment posted

#### 7.3 Test Deployment Approval

The deployment-gates workflow should:
- [ ] Verify all required CI checks passed
- [ ] Confirm version was bumped
- [ ] Detect no breaking changes
- [ ] Check for documentation updates
- [ ] Check for test coverage

---

## **Test Results Summary**

### Expected Outcomes

| Component | Expected Result | Status |
|-----------|-----------------|--------|
| Workflow files exist | All 4 workflows present | ✓ |
| Canary deployment 10% | Health checks pass, smoke tests pass | ⏳ |
| Traffic promotion 50% | Service splits traffic correctly | ⏳ |
| Traffic promotion 100% | All traffic on new version | ⏳ |
| Smoke tests | All 5 tests pass | ⏳ |
| Health monitoring | Health checks every 5 min | ⏳ |
| Automated rollback | Rollback completes successfully | ⏳ |
| Deployment gates | Pre-merge checks work | ⏳ |

### Performance Targets

- **Health check success rate:** >99.9%
- **P95 latency:** <2 seconds
- **Error rate:** <0.1%
- **Deployment time:** <5 minutes (canary)
- **Rollback time:** <2 minutes
- **Smoke test duration:** <5 minutes

---

## **Troubleshooting**

### Canary Deployment Fails

**Symptom:** Docker image pull fails

**Solution:**
```bash
# Verify image exists in registry
docker pull ghcr.io/sjbrenchley89/free-claude-code:latest

# Check permissions
# Ensure GITHUB_TOKEN has package read permission
```

### Health Checks Fail

**Symptom:** Health endpoint returns 500 or timeout

**Solution:**
```bash
# Check service logs
docker-compose logs fcc-server

# Verify port is accessible
curl -v http://localhost:8000/health

# Check dependencies
docker-compose ps
```

### Smoke Tests Fail

**Symptom:** API tests return errors

**Solution:**
```bash
# Test each endpoint manually
curl http://localhost:8000/health
curl http://localhost:8000/v1/messages
curl http://localhost:8000/v1/chat/completions

# Check API key configuration
env | grep ANTHROPIC
```

### Load Balancer Not Splitting Traffic

**Symptom:** Traffic still goes to old version after promotion

**Solution:**
```bash
# Verify load balancer configuration
# Check that canary service is registered

# For local testing without load balancer:
# Edit docker-compose.yml to manually control instances
# Example: run 1 canary + 9 production replicas
```

---

## **Sign-Off Criteria**

The CI/CD pipeline is validated and ready for production when:

- [ ] Phase 1: All workflow files exist and are syntactically correct
- [ ] Phase 2: Canary deployment succeeds with health checks and smoke tests passing
- [ ] Phase 3: Traffic can be promoted from 10% → 50% → 100% successfully
- [ ] Phase 4: Automated smoke tests pass on schedule
- [ ] Phase 5: Health monitoring works and metrics are collected
- [ ] Phase 6: Automated rollback successfully reverts to previous version
- [ ] Phase 7: Deployment gates prevent merging without proper configuration

**Date Validation Completed:** ________________

**Validated By:** ________________

**Sign-Off:** ________________

---

## **Next Steps**

Once all validation phases pass:

1. **Set up monitoring alerts** - Configure PagerDuty/Slack notifications
2. **Document runbooks** - Create incident response procedures
3. **Schedule first production deployment** - Plan rollout window
4. **Train team** - Brief team on deployment procedures
5. **Enable auto-merge** (optional) - Automate merge workflow after canary approval

