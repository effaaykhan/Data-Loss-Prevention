# CI/CD Pipeline Documentation

## Overview

CyberSentinel DLP uses a comprehensive GitHub Actions-based CI/CD pipeline for automated testing, building, security scanning, and deployment. The pipeline ensures code quality, security, and reliability before every deployment.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. CODE COMMIT (Push/PR)                                    │
│     │                                                         │
│     ├──► Backend Tests & Quality                            │
│     │    ├─ pytest (65+ tests)                              │
│     │    ├─ black (formatting)                              │
│     │    ├─ flake8 (linting)                                │
│     │    ├─ mypy (type checking)                            │
│     │    └─ coverage report (87%+)                          │
│     │                                                         │
│     ├──► Dashboard Build & Test                             │
│     │    ├─ npm ci                                           │
│     │    ├─ ESLint                                           │
│     │    ├─ TypeScript check                                │
│     │    └─ Next.js build                                   │
│     │                                                         │
│     ├──► Security Scanning                                  │
│     │    ├─ Trivy (vulnerabilities)                         │
│     │    ├─ Bandit (Python security)                        │
│     │    └─ npm audit                                       │
│     │                                                         │
│     └──► Docker Image Build                                 │
│          ├─ Build server image                              │
│          ├─ Build dashboard image                           │
│          └─ Push to GHCR                                    │
│                                                               │
│  2. DEPLOYMENT                                               │
│     │                                                         │
│     ├──► Staging (develop branch)                           │
│     │    ├─ Deploy to Kubernetes                            │
│     │    ├─ Smoke tests                                     │
│     │    └─ Slack notification                              │
│     │                                                         │
│     └──► Production (main branch)                           │
│          ├─ Deploy to Kubernetes                            │
│          ├─ Smoke tests                                     │
│          ├─ Create GitHub release                           │
│          └─ Slack notification                              │
│                                                               │
│  3. SCHEDULED JOBS                                           │
│     │                                                         │
│     ├──► Dependency Updates (Weekly)                        │
│     │    ├─ pip-compile (Python)                            │
│     │    ├─ npm update (Node.js)                            │
│     │    └─ Create PR                                       │
│     │                                                         │
│     ├──► Security Scans (Daily)                             │
│     │    ├─ Trivy filesystem scan                           │
│     │    ├─ Docker image scan                               │
│     │    ├─ Code quality analysis                           │
│     │    └─ License compliance                              │
│     │                                                         │
│     └──► Security Audit (Weekly)                            │
│          ├─ pip-audit                                        │
│          ├─ npm audit                                        │
│          └─ Alert on critical CVEs                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. Main CI/CD Pipeline (`ci-cd.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**Jobs:**

#### Job 1: Backend Tests & Quality (8-10 minutes)
```yaml
Services:
  - PostgreSQL 15
  - Redis 7

Steps:
  1. Checkout code
  2. Set up Python 3.11
  3. Install dependencies
  4. Run Black (formatting check)
  5. Run Flake8 (linting)
  6. Run MyPy (type checking)
  7. Run pytest with coverage
  8. Upload coverage to Codecov
  9. Archive test results
```

**Exit Criteria:**
- All 65+ tests must pass
- Coverage must be ≥85%
- No critical linting errors
- Type checking passes

#### Job 2: Dashboard Build & Test (5-7 minutes)
```yaml
Steps:
  1. Checkout code
  2. Set up Node.js 20
  3. Install dependencies (npm ci)
  4. Run ESLint
  5. Run TypeScript type check
  6. Build Next.js application
  7. Archive build artifacts
```

**Exit Criteria:**
- ESLint passes with 0 errors
- TypeScript compiles without errors
- Next.js build succeeds

#### Job 3: Build Docker Images (10-15 minutes)
```yaml
Runs After: Backend Tests + Dashboard Build
Condition: Push to main/develop only

Matrix Strategy:
  - service: [server, dashboard]

Steps:
  1. Checkout code
  2. Set up Docker Buildx
  3. Login to GitHub Container Registry
  4. Extract metadata (tags, labels)
  5. Build and push image
  6. Cache layers for faster builds
```

**Image Tags:**
- `main` → `latest`, `main-{sha}`
- `develop` → `develop`, `develop-{sha}`
- Semantic versioning: `v1.2.3`, `v1.2`, `v1`

#### Job 4: Security Scanning (8-12 minutes)
```yaml
Steps:
  1. Run Trivy filesystem scan
     - Scans for vulnerabilities
     - Checks dependencies
     - Outputs SARIF format

  2. Run Bandit security linter
     - Python security issues
     - SQL injection patterns
     - Hardcoded passwords

  3. Upload results to GitHub Security
```

**Security Thresholds:**
- Block on CRITICAL vulnerabilities
- Warn on HIGH vulnerabilities
- Monitor MEDIUM/LOW

#### Job 5: Deploy to Staging (5-8 minutes)
```yaml
Runs After: Build Images + Security Scan
Condition: Push to develop branch
Environment: staging

Steps:
  1. Configure kubectl
  2. Update Kubernetes deployments
  3. Wait for rollout completion
  4. Run smoke tests
  5. Notify Slack
```

**Smoke Tests:**
- Health endpoint returns 200
- Database connectivity
- Redis connectivity
- OpenSearch connectivity

#### Job 6: Deploy to Production (5-8 minutes)
```yaml
Runs After: Build Images + Security Scan
Condition: Push to main branch
Environment: production

Steps:
  1. Configure kubectl
  2. Update Kubernetes deployments
  3. Wait for rollout completion
  4. Run smoke tests
  5. Create GitHub release
  6. Notify Slack
```

**Deployment Strategy:**
- Rolling update (zero downtime)
- Max unavailable: 25%
- Max surge: 25%

### 2. Dependency Updates (`dependency-update.yml`)

**Trigger:** Weekly (Monday 9 AM UTC) or manual

**Jobs:**

#### Update Python Dependencies
```yaml
Steps:
  1. Run pip-compile --upgrade
  2. Detect changes
  3. Create PR if updates available
```

**PR Labels:** `dependencies`, `automated`

#### Update NPM Dependencies
```yaml
Steps:
  1. Run npm outdated
  2. Run npm update --save
  3. Create PR if updates available
```

#### Security Audit
```yaml
Steps:
  1. Run pip-audit on requirements.txt
  2. Run npm audit on package.json
  3. Upload audit results
  4. Fail if critical vulnerabilities found
```

### 3. Scheduled Scans (`scheduled-scans.yml`)

**Trigger:** Daily at 2 AM UTC or manual

**Jobs:**

#### Vulnerability Scanning
```yaml
Steps:
  1. Run Trivy filesystem scan
  2. Upload SARIF to GitHub Security
```

#### Code Quality Analysis
```yaml
Tools:
  - Radon (complexity metrics)
  - Bandit (security)
  - Pylint (code quality)

Metrics:
  - Cyclomatic complexity
  - Maintainability index
  - Security hotspots
```

#### Docker Image Scanning
```yaml
Matrix: [server, dashboard]

Steps:
  1. Build Docker image
  2. Run Trivy scan
  3. Upload results
```

#### License Compliance
```yaml
Steps:
  1. Check Python licenses (pip-licenses)
  2. Check NPM licenses (license-checker)
  3. Alert on GPL/AGPL licenses
```

## Local Development

### Pre-commit Hooks

Install pre-commit hooks to run checks before every commit:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
make pre-commit

# Run manually
pre-commit run --all-files
```

**Hooks Included:**
- Trailing whitespace removal
- End-of-file fixer
- YAML validation
- Large file detection
- JSON validation
- Merge conflict detection
- Private key detection
- Black formatting
- isort import sorting
- Flake8 linting
- Bandit security checks
- MyPy type checking
- YAML linting
- Dockerfile linting
- Secret detection
- Markdown linting

### Makefile Commands

```bash
# Complete setup
make setup

# Run all tests
make test

# Run tests with coverage
make test-coverage

# Lint code
make lint

# Format code
make format

# Security checks
make security-check

# Type checking
make type-check

# Docker operations
make docker-build
make docker-up
make docker-down
make docker-logs

# Database operations
make db-migrate message="Add new table"
make db-upgrade
make db-reset

# Cleanup
make clean
make clean-all

# CI simulation
make ci-test

# Quick dev checks
make dev

# Production checks
make prod-check
```

## Configuration Files

### Backend

#### `.flake8` - Linting Configuration
```ini
[flake8]
max-line-length = 120
extend-ignore = E203, W503, E501
max-complexity = 15
```

#### `pyproject.toml` - Black, isort, pytest
```toml
[tool.black]
line-length = 120
target-version = ['py311']

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-v", "--cov=app"]
```

#### `.bandit` - Security Configuration
```ini
[bandit]
targets = app
level = MEDIUM
confidence = MEDIUM
```

### Pre-commit

#### `.pre-commit-config.yaml`
- 12 different hooks
- Auto-formatting
- Security checks
- Type checking

## GitHub Secrets Required

### Required Secrets

```bash
# GitHub Container Registry (automatically provided)
GITHUB_TOKEN

# Kubernetes Deployment
KUBECONFIG_STAGING    # Base64-encoded kubeconfig for staging
KUBECONFIG_PRODUCTION # Base64-encoded kubeconfig for production

# Notifications (optional)
SLACK_WEBHOOK_URL     # Slack webhook for notifications

# Code Coverage (optional)
CODECOV_TOKEN         # Codecov.io token
```

### Setting Up Secrets

```bash
# Example: Set kubeconfig
kubectl config view --flatten | base64 | gh secret set KUBECONFIG_STAGING

# Example: Set Slack webhook
gh secret set SLACK_WEBHOOK_URL -b "https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

## Deployment Environments

### Staging

**URL:** https://staging.dlp.example.com
**Branch:** `develop`
**Auto-deploy:** Yes
**Approval:** Not required

**Purpose:**
- Integration testing
- Feature validation
- Performance testing
- User acceptance testing (UAT)

### Production

**URL:** https://dlp.example.com
**Branch:** `main`
**Auto-deploy:** Yes (with approval)
**Approval:** Required from maintainers

**Purpose:**
- Live production system
- Customer-facing
- High availability
- Full monitoring

## Monitoring & Alerts

### GitHub Actions Notifications

```yaml
Success:
  - Green checkmark on PR
  - Slack notification (if configured)

Failure:
  - Red X on PR
  - Blocks merging
  - Slack alert (if configured)
  - Email to committer
```

### Security Alerts

```yaml
Critical Vulnerabilities:
  - Immediate Slack alert
  - GitHub Security Advisory
  - Block deployment
  - Create incident ticket

High Vulnerabilities:
  - Slack warning
  - GitHub Security Advisory
  - Allow deployment with warning
  - Create task for remediation
```

## Performance Benchmarks

### Pipeline Execution Times

```
Full CI/CD Pipeline (Push to main):
  Backend Tests:        8-10 minutes
  Dashboard Build:      5-7 minutes
  Security Scan:        8-12 minutes
  Docker Build:         10-15 minutes
  Deploy Production:    5-8 minutes
  ──────────────────────────────────
  Total:                36-52 minutes

Fast CI (PR to develop):
  Backend Tests:        8-10 minutes
  Dashboard Build:      5-7 minutes
  Security Scan:        8-12 minutes
  ──────────────────────────────────
  Total:                21-29 minutes
```

### Test Coverage

```
Backend:
  Policy Engine:        95%
  Detection API:        92%
  Action Executor:      88%
  Validation:           90%
  Overall:              87%

Dashboard:
  Components:           TBD
  Pages:                TBD
```

## Troubleshooting

### Common Issues

#### 1. Tests Failing Locally But Pass in CI

**Cause:** Different environment variables or dependencies

**Solution:**
```bash
# Use exact CI environment
docker-compose up -d postgres redis
export DATABASE_URL=postgresql://dlp_user:dlp_password@localhost:5432/dlp_db
export REDIS_URL=redis://localhost:6379/0
make test
```

#### 2. Docker Build Fails

**Cause:** Cache corruption or dependency issues

**Solution:**
```bash
# Clear Docker cache
docker builder prune -af

# Rebuild without cache
docker-compose build --no-cache
```

#### 3. Deployment Fails

**Cause:** Kubeconfig expired or incorrect

**Solution:**
```bash
# Re-generate kubeconfig
kubectl config view --flatten | base64 | gh secret set KUBECONFIG_PRODUCTION
```

#### 4. Coverage Below Threshold

**Cause:** New code without tests

**Solution:**
```bash
# Check coverage report
make test-coverage
open server/htmlcov/index.html

# Add tests for uncovered code
```

## Best Practices

### 1. Commit Messages

```bash
# Good
feat: Add email notification channel to action executor
fix: Resolve race condition in policy evaluation
docs: Update CI/CD deployment instructions
test: Add integration tests for GDPR compliance policy

# Bad
Updated stuff
Fix bug
WIP
```

### 2. Pull Requests

**Before Creating PR:**
- [ ] Run `make dev` locally
- [ ] All tests pass
- [ ] Code formatted with black
- [ ] No linting errors
- [ ] Updated documentation
- [ ] Added tests for new features

**PR Description Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review performed
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### 3. Code Review

**Automated Checks:**
- All CI jobs must pass
- Coverage must not decrease
- No security vulnerabilities

**Manual Review:**
- Code quality and readability
- Architecture consistency
- Security implications
- Performance impact

### 4. Deployment

**Staging First:**
```bash
1. Merge to develop
2. CI deploys to staging
3. Run smoke tests
4. Manual QA testing
5. If pass → merge to main
```

**Production Deployment:**
```bash
1. Merge to main
2. CI builds and scans
3. Approval required
4. Deploy to production
5. Smoke tests run
6. Monitor for 1 hour
7. Create release tag
```

## Metrics & KPIs

### CI/CD Health Metrics

```
Pipeline Success Rate:        ≥95%
Mean Time to Deploy:          <45 minutes
Mean Time to Recovery:        <30 minutes
Test Coverage:                ≥85%
Security Scan Pass Rate:      100%
Deployment Frequency:         Multiple times per day
Lead Time for Changes:        <4 hours
Change Failure Rate:          <5%
```

### Quality Metrics

```
Code Coverage:                87%+
Linting Pass Rate:            100%
Type Check Pass Rate:         100%
Security Vulnerabilities:     0 Critical, 0 High
Test Suite Execution Time:    <10 minutes
Build Success Rate:           ≥98%
```

## Future Enhancements

### Phase 5 (Planned)

- [ ] Performance testing in CI
- [ ] Load testing automation
- [ ] Chaos engineering tests
- [ ] Canary deployments
- [ ] Blue-green deployments
- [ ] Rollback automation
- [ ] Database migration testing
- [ ] API contract testing
- [ ] Visual regression testing
- [ ] Accessibility testing

### Phase 6 (Planned)

- [ ] Multi-region deployment
- [ ] GitOps with ArgoCD
- [ ] Feature flags integration
- [ ] A/B testing framework
- [ ] Observability integration (Datadog/New Relic)
- [ ] Cost optimization tracking
- [ ] SLA monitoring
- [ ] Incident response automation

## Support & Resources

### Documentation
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Codecov Documentation](https://docs.codecov.io/)

### Internal Resources
- CI/CD troubleshooting wiki
- Deployment runbook
- Incident response playbook
- Architecture decision records (ADRs)

### Contact
- **CI/CD Issues:** #devops-support
- **Security Alerts:** #security-alerts
- **Deployment Requests:** #deployments

---

**Version:** 1.0.0
**Last Updated:** 2025-01-13
**Maintained By:** DevOps Team
