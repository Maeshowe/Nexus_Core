# Security Design

> **Project:** OmniData Nexus Core
> **Version:** 1.0
> **Date:** 2026-01-31
> **Status:** Draft
> **Scope:** Personal research tool (single-user, local deployment)

---

## 1. Security Overview

### 1.1 Security Objectives

| Objective | Priority | Description |
|-----------|----------|-------------|
| Confidentiality | HIGH | Protect API keys (FMP, Polygon, FRED) from unauthorized disclosure |
| Integrity | MEDIUM | Ensure data accuracy through schema validation and atomic cache writes |
| Availability | MEDIUM | Maintain service continuity through circuit breaker and rate limit management |

**Key Security Principle:** Proportionate security for a personal research tool. This is NOT an enterprise system requiring OAuth, RBAC, or network segmentation. Focus is on API key protection and safe interaction with external services.

### 1.2 Security Scope

**In Scope:**
- API key protection (storage, transmission, logging)
- Secure communication with external APIs (FMP, Polygon, FRED)
- Cache integrity (atomic writes, no credential leakage)
- Log sanitization (no secrets in logs or error messages)
- Dependency security (vulnerability scanning)

**Out of Scope:**
- User authentication (single-user system)
- Multi-tenancy/authorization
- GDPR/HIPAA compliance (no PII collected)
- Network segmentation (local-only deployment)
- Database security (no database)
- WebSocket security (REST only)

---

## 2. Threat Model

### 2.1 Assets

| Asset | Sensitivity | Location | Protection |
|-------|-------------|----------|------------|
| FMP API Key | CRITICAL | `.env` file (local filesystem) | File permissions (600), gitignored, environment variable |
| Polygon API Key | CRITICAL | `.env` file (local filesystem) | File permissions (600), gitignored, environment variable |
| FRED API Key | CRITICAL | `.env` file (local filesystem) | File permissions (600), gitignored, environment variable |
| Cached API responses | LOW | `data/{provider}_cache/` (JSON files) | Contains only public data, no credentials |
| Source code | LOW | Git repository | Public or private repo, no secrets embedded |
| Log files | LOW | `logs/nexus_core.log` | API keys sanitized before logging |

**Note:** API keys are the ONLY critical assets. Cached financial data is public information with no inherent sensitivity.

### 2.2 Threat Actors

| Actor | Motivation | Capability | Likelihood | Realistic for Personal Tool? |
|-------|------------|------------|------------|------------------------------|
| Opportunistic attacker | API key theft for resale | Low (automated scanners) | Medium | Yes - if keys committed to public repo |
| Malicious script/dependency | Data exfiltration | Medium (supply chain) | Low | Yes - compromised PyPI package |
| Local malware | Credential harvesting | Medium (filesystem access) | Low | Yes - but outside project scope |
| Insider threat | N/A | N/A | N/A | No - single-user system |
| Nation-state actor | N/A | N/A | N/A | No - not a target profile |

**Realistic Threat Focus:** Accidental API key exposure (git commit, log files) and dependency vulnerabilities. NOT nation-state attacks or sophisticated APTs.

### 2.3 Attack Surface

```
┌─────────────────────────────────────────────────────────────┐
│                     ATTACK SURFACE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXTERNAL                    INTERNAL                       │
│  ┌─────────────┐            ┌─────────────┐                │
│  │ FMP API     │            │ .env file   │                │
│  │ HTTPS       │            │ Risk: HIGH  │                │
│  │ Risk: LOW   │            │ Mitigation: │                │
│  │             │            │ - .gitignore│                │
│  └─────────────┘            │ - chmod 600 │                │
│                             └─────────────┘                │
│  ┌─────────────┐            ┌─────────────┐                │
│  │ Polygon API │            │ Dependencies│                │
│  │ HTTPS       │            │ Risk: MEDIUM│                │
│  │ Risk: LOW   │            │ Mitigation: │                │
│  │             │            │ - pip audit │                │
│  └─────────────┘            │ - pinned ver│                │
│                             └─────────────┘                │
│  ┌─────────────┐            ┌─────────────┐                │
│  │ FRED API    │            │ Log files   │                │
│  │ HTTPS       │            │ Risk: MEDIUM│                │
│  │ Risk: LOW   │            │ Mitigation: │                │
│  │             │            │ - key sanit │                │
│  └─────────────┘            └─────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Entry Points:**
1. **External APIs (FMP, Polygon, FRED)** - HTTPS endpoints (LOW risk - TLS protects in transit)
2. **`.env` file** - API key storage (HIGH risk - if committed to git or world-readable)
3. **Dependencies** - PyPI packages (MEDIUM risk - supply chain attack)
4. **Log files** - Error messages (MEDIUM risk - if keys logged)
5. **Cache files** - JSON storage (LOW risk - no credentials stored)

### 2.4 STRIDE Analysis

| Threat | Applies? | Attack Vector | Mitigation |
|--------|----------|---------------|------------|
| **S**poofing | NO | No authentication mechanism to spoof | N/A - single-user, local system |
| **T**ampering | YES | Attacker modifies cache files or code | File permissions (POSIX), code integrity via git |
| **R**epudiation | NO | No audit trail needed for single-user research | N/A - no regulatory requirement |
| **I**nfo Disclosure | YES | API keys exposed in git, logs, or cache | `.gitignore`, log sanitization, no keys in cache |
| **D**enial of Service | YES | Rate limit exhaustion by runaway script | QoS Semaphore Router (FR-005), circuit breaker (FR-007) |
| **E**levation | NO | No privilege levels to elevate | N/A - single-user system |

**Security Focus:** Information Disclosure (API keys) and Denial of Service (rate limits).

---

## 3. Security Architecture

### 3.1 Authentication

**To External APIs:**
- **Method:** API key authentication via query parameters or HTTP headers (provider-specific)
- **Storage:** Environment variables (`FMP_KEY`, `POLYGON_KEY`, `FRED_KEY`) loaded from `.env` file
- **Transmission:** HTTPS only (TLS 1.2+) - enforced by `aiohttp` default configuration
- **Rotation:** Manual - user responsible for key rotation per API provider policy

**No User Authentication:** Single-user system running locally - no login mechanism required.

### 3.2 Authorization

**N/A** - No multi-user access, no role-based permissions. The user running the Python process has full access to all features.

**API Provider Authorization:** Governed by API subscription tier (e.g., FMP Ultimate plan) - handled externally by providers.

### 3.3 Cryptography

| Purpose | Algorithm/Protocol | Implementation | Notes |
|---------|-------------------|----------------|-------|
| Data in transit | TLS 1.2/1.3 | `aiohttp` default (system SSL library) | All API communication encrypted |
| Data at rest | None (unencrypted) | Filesystem JSON cache | Public financial data, no encryption needed |
| API key storage | None (plaintext in .env) | `python-dotenv` | Appropriate for local single-user; file permissions protect |
| Cache key hashing | MD5 | `hashlib.md5()` | Speed prioritized over cryptographic security (collision resistance not critical) |

**Rationale for No Encryption at Rest:**
- Cached data is public financial information (no confidentiality requirement)
- API keys in `.env` protected by filesystem permissions (600) and `.gitignore`
- Full disk encryption (macOS FileVault, Linux LUKS) available at OS level if needed

### 3.4 Network Security

**Architecture:** Local Python process → Internet → External APIs

**Controls:**
- **TLS enforcement:** All HTTP clients configured to use HTTPS (no HTTP fallback)
- **Certificate validation:** `aiohttp` verifies server certificates by default
- **No listening ports:** Framework makes outbound requests only (no server component)
- **Firewall:** Relies on OS firewall for outbound filtering (user-managed)

**Network Diagram:**

```
┌──────────────────────┐
│  Local Python Process│
│  (OmniData Nexus)    │
└──────────┬───────────┘
           │ Outbound HTTPS only
           │ (TLS 1.2+)
           ▼
┌──────────────────────┐
│  Internet            │
│  (Provider APIs)     │
└──────────────────────┘
```

**No Internal Network:** Single process, no service-to-service communication.

---

## 4. Security Controls

### 4.1 Preventive Controls

| Control | Implementation | Priority | Component |
|---------|----------------|----------|-----------|
| **API Key Protection** | `.env` file with `.gitignore`; never hardcoded | CRITICAL | Config Manager |
| **HTTPS Enforcement** | `aiohttp` default TLS; reject HTTP URLs | HIGH | HTTP Client Layer |
| **Input Validation** | Schema validation for API responses (FR-011) | MEDIUM | Providers |
| **Rate Limiting** | QoS Semaphore Router enforces concurrency limits | HIGH | QoS Router |
| **Atomic Cache Writes** | Temp file + rename pattern prevents corruption | MEDIUM | Cache Manager |
| **Dependency Pinning** | `requirements.txt` with exact versions | MEDIUM | Build System |
| **File Permissions** | `.env` should be `chmod 600` (user-only) | HIGH | Setup Documentation |

### 4.2 Detective Controls

| Control | Implementation | Alerting |
|---------|----------------|----------|
| **API Key Sanitization in Logs** | Regex-based redaction in log formatter (FR-014) | Warning logged if key pattern detected |
| **Rate Limit Monitoring** | Warning at 80% consumption (FR-009) | Log entry (no automated alert) |
| **Circuit Breaker Telemetry** | Health report shows error rates (FR-010) | Open state triggers log warning |
| **Dependency Vulnerability Scan** | Manual `pip audit` (developer responsibility) | Console output during CI |
| **Git Pre-commit Hook** | Check for API key patterns before commit | Reject commit if pattern found |

**Monitoring Gaps (Acceptable for Personal Tool):**
- No real-time SIEM alerts (log review is manual)
- No automated incident response
- No intrusion detection system

### 4.3 Corrective Controls

| Threat | Response | Automation |
|--------|----------|------------|
| **API Key Leaked to Git** | Immediate revoke via provider dashboard; rotate keys | Manual (user detects via GitHub scanning or manual review) |
| **Rate Limit Exhausted** | Circuit breaker halts requests; wait for cooldown | Automatic (circuit breaker pattern) |
| **Dependency Vulnerability** | Update package; test compatibility; redeploy | Manual (user runs `pip install -U`) |
| **Cache Corruption** | Delete corrupted file; refetch from API | Automatic (validation fails, cache miss triggers refetch) |

---

## 5. Data Protection

### 5.1 Data Classification

| Data Type | Classification | Rationale | Handling |
|-----------|----------------|-----------|----------|
| API Keys | CRITICAL - Secret | Unauthorized use leads to quota exhaustion or financial cost | `.env` file, chmod 600, never logged |
| Cached API Responses | PUBLIC | Financial data available to any subscriber | Filesystem JSON, no encryption |
| Log Files | INTERNAL | May contain debugging info but no secrets | Sanitized output, local storage only |
| Configuration (non-secrets) | PUBLIC | TTLs, concurrency limits, endpoints | Version controlled in `config.py` |
| Source Code | PUBLIC | Framework logic (can be open-sourced) | Git repository (public or private) |

### 5.2 Secrets Management

| Secret Type | Storage | Access | Rotation | Backup |
|-------------|---------|--------|----------|--------|
| FMP API Key | `.env` file (gitignored) | Environment variable `FMP_KEY` | Manual via FMP dashboard | User responsibility (password manager) |
| Polygon API Key | `.env` file (gitignored) | Environment variable `POLYGON_KEY` | Manual via Polygon dashboard | User responsibility (password manager) |
| FRED API Key | `.env` file (gitignored) | Environment variable `FRED_KEY` | Manual via FRED website | User responsibility (password manager) |

**Secret Lifecycle:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Acquisition: User obtains keys from provider dashboards  │
│                                                             │
│ 2. Storage: User creates .env file (chmod 600)             │
│    Example:                                                 │
│    FMP_KEY=abc123...                                        │
│    POLYGON_KEY=xyz789...                                    │
│    FRED_KEY=def456...                                       │
│                                                             │
│ 3. Loading: python-dotenv reads .env → os.environ          │
│                                                             │
│ 4. Usage: Config Manager retrieves via os.getenv()         │
│                                                             │
│ 5. Transmission: Included in HTTPS requests (TLS encrypted)│
│                                                             │
│ 6. Rotation: User manually updates .env after rotating     │
│             keys in provider dashboards                    │
│                                                             │
│ 7. Revocation: Delete from .env, revoke in provider portal │
└─────────────────────────────────────────────────────────────┘
```

**No Vault/KMS:** For a single-user local tool, `.env` + `.gitignore` + file permissions is proportionate. Enterprise secret management (HashiCorp Vault, AWS Secrets Manager) would be overkill.

### 5.3 Data Retention

| Data Type | Retention | Location | Deletion |
|-----------|-----------|----------|----------|
| Cached responses | 7 days (configurable TTL) | `data/{provider}_cache/` | Manual cleanup or TTL-based script |
| Log files | 10MB max (5 rotating backups) | `logs/nexus_core.log` | Automatic rotation via logging handler |
| API keys | Indefinite (until user rotates) | `.env` file | Manual deletion |

---

## 6. Compliance

### 6.1 API Provider Terms of Service

**This is the ONLY compliance requirement for a personal research tool.**

| Provider | Key ToS Requirements | Compliance Mechanism |
|----------|----------------------|----------------------|
| **FMP Ultimate** | - Respect rate limits<br>- No redistribution of data<br>- Proper attribution | - QoS Semaphore (3 concurrent)<br>- Cache for personal use only<br>- Attribution in documentation |
| **Polygon.io** | - Respect rate limits (5 req/min free tier)<br>- No resale of data<br>- Acceptable use policy | - QoS Semaphore (10 concurrent)<br>- Personal research only<br>- No commercial distribution |
| **FRED** | - Public domain data<br>- Attribution required<br>- Recommended 120 req/min limit | - QoS Semaphore (1 concurrent)<br>- Citation: "Source: Federal Reserve Economic Data"<br>- Conservative rate limiting |

**Verification:** User is responsible for reviewing and adhering to provider ToS. Framework provides technical controls (rate limiting) to prevent violations.

### 6.2 Standards NOT Applicable

| Standard | Reason Not Applicable |
|----------|----------------------|
| **GDPR** | No personal data collected (financial data is public) |
| **HIPAA** | No health information |
| **PCI-DSS** | No payment processing |
| **SOC 2** | No service offering (internal research tool) |
| **ISO 27001** | Personal tool, not enterprise |

---

## 7. Vulnerability Management

### 7.1 Dependency Security

**Process:**

```bash
# 1. Regular scanning (recommended: weekly)
pip audit

# 2. Review output for HIGH/CRITICAL vulnerabilities
# Example output:
# Found 2 known vulnerabilities in 1 package
# aiohttp 3.8.0 -> CVE-2023-XXXXX (HIGH)

# 3. Update affected packages
pip install --upgrade aiohttp

# 4. Test compatibility
pytest tests/

# 5. Update requirements.txt
pip freeze > requirements.txt
```

**Vulnerability Severity Response:**

| Severity | Response Time | Action |
|----------|---------------|--------|
| CRITICAL | Within 24 hours | Immediate update and testing |
| HIGH | Within 1 week | Scheduled update in next maintenance window |
| MEDIUM | Within 1 month | Evaluate during regular dependency review |
| LOW | Next major release | Document and defer unless easy fix |

### 7.2 Code Security

**Practices:**

| Practice | Implementation | Frequency |
|----------|----------------|-----------|
| **Static Analysis** | Linters (pylint, flake8, mypy) | On every commit (pre-commit hook) |
| **Secret Scanning** | `git grep -E "(FMP_KEY\|POLYGON_KEY\|FRED_KEY)" -- ':(exclude).env'` | Pre-commit hook |
| **Dependency Audit** | `pip audit` | Weekly (manual) |
| **Code Review** | Self-review before commit (solo developer) | Every change |

**Pre-commit Hook Example:**

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for API keys in committed files (excluding .env)
if git grep -E "(FMP_KEY|POLYGON_KEY|FRED_KEY|apikey|api_key)" HEAD -- ':(exclude).env' ':(exclude)*.md'; then
    echo "ERROR: Potential API key found in commit"
    exit 1
fi

# Run secret scanning tool (optional)
# pip install detect-secrets
# detect-secrets scan --baseline .secrets.baseline
```

### 7.3 API Security

**Security Measures:**

| Concern | Mitigation | Verification |
|---------|------------|--------------|
| **Key Rotation** | Manual rotation every 90 days (best practice) | Calendar reminder |
| **Key Leakage Detection** | GitHub secret scanning (if public repo) | Automatic (GitHub feature) |
| **Rate Limit Abuse** | QoS Semaphore enforces provider limits | Health monitor tracks usage |
| **Man-in-the-Middle** | TLS certificate validation | `aiohttp` default behavior |

---

## 8. Security Exceptions

| Exception | Rationale | Risk Acceptance | Mitigation |
|-----------|-----------|-----------------|------------|
| **API Keys in Plaintext (.env)** | Single-user local system; encrypted secret store overkill | LOW - file permissions (600) + `.gitignore` sufficient | Recommend OS-level full disk encryption |
| **No Encryption at Rest (Cache)** | Public financial data; no confidentiality requirement | NEGLIGIBLE - data is already public | None needed |
| **No Authentication** | Single-user system; no network exposure | NONE - appropriate for use case | N/A |
| **Manual Dependency Updates** | Automated updates risk breaking changes | LOW - research tool can tolerate brief downtime | Weekly `pip audit` schedule |

**Approval:** Solo developer accepts above exceptions as appropriate for personal research tool.

---

## 9. Security Testing

### 9.1 Test Plan

| Test Type | Scope | Frequency | Tooling |
|-----------|-------|-----------|---------|
| **Secret Scanning** | Git history, code, logs | Every commit (pre-commit hook) | `git grep`, `detect-secrets` |
| **Dependency Audit** | PyPI packages | Weekly | `pip audit` |
| **TLS Verification** | HTTPS connections | Every release | Manual inspection (`openssl s_client`) |
| **Log Sanitization** | API key redaction | Unit tests | pytest (test log output) |
| **Cache Integrity** | Atomic write validation | Unit tests | pytest (concurrent writes) |

### 9.2 Security Test Cases

**Test 1: API Key Sanitization in Logs**

```python
def test_api_key_not_logged():
    """Verify API keys are redacted in log output."""
    with patch('sys.stdout', new=StringIO()) as fake_out:
        logger.error(f"Request failed: {os.getenv('FMP_KEY')}")
        log_output = fake_out.getvalue()
        assert "FMP_KEY" not in log_output
        assert "***REDACTED***" in log_output
```

**Test 2: .env File in .gitignore**

```python
def test_env_file_gitignored():
    """Verify .env is in .gitignore."""
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
        assert '.env' in gitignore_content
```

**Test 3: HTTPS Enforcement**

```python
def test_https_only():
    """Verify HTTP URLs are rejected."""
    with pytest.raises(ValueError):
        DataLoader.validate_url("http://api.example.com")
```

### 9.3 Penetration Testing

**NOT REQUIRED** for a personal research tool. No external attack surface beyond API providers (which are out of scope).

If desired for learning purposes:
- **Scope:** Local filesystem security (file permissions, git history)
- **Tools:** `trufflehog` (secret scanning), `bandit` (Python security linting)
- **Frequency:** One-time during initial development

---

## 10. Incident Response

### 10.1 API Key Compromise

**Detection:**
- GitHub alerts (if public repo)
- Unusual API usage patterns (manual review of provider dashboards)
- Third-party notification

**Response (1-hour playbook):**

```
┌─────────────────────────────────────────────────────────────┐
│ INCIDENT: API Key Compromised                               │
├─────────────────────────────────────────────────────────────┤
│ T+0:00  DETECT   Receive alert or notice unusual usage     │
│                                                             │
│ T+0:05  CONTAIN  Revoke compromised key in provider portal │
│                  FMP: https://site.financialmodelingprep.com│
│                  Polygon: https://polygon.io/dashboard/keys │
│                  FRED: https://fred.stlouisfed.org/api      │
│                                                             │
│ T+0:10  ROTATE   Generate new API key                      │
│                                                             │
│ T+0:15  UPDATE   Update .env with new key                  │
│                                                             │
│ T+0:20  TEST     Verify new key works:                     │
│                  python -c "from src import DataLoader; ..." │
│                                                             │
│ T+0:30  AUDIT    Check git history for leaked key:        │
│                  git log -p -S "OLD_KEY_VALUE"             │
│                                                             │
│ T+0:45  CLEAN    If key in git history:                    │
│                  - git filter-branch (nuclear option)      │
│                  - OR accept history contamination         │
│                  - Force push to remote (if private repo)  │
│                                                             │
│ T+1:00  LEARN    Document how leak occurred; update process│
└─────────────────────────────────────────────────────────────┘
```

**Cost Impact:** FMP/Polygon keys may incur charges if abused. FRED is free (no financial impact).

### 10.2 Dependency Vulnerability

**Response (24-hour playbook):**

1. **Assess:** Check CVE severity and exploitability
2. **Test:** Determine if vulnerability affects this project
3. **Update:** Upgrade to patched version (`pip install --upgrade`)
4. **Verify:** Run test suite (`pytest`)
5. **Deploy:** Update `requirements.txt` and document change

---

## 11. Security Awareness

### 11.1 Secure Development Practices

**For Solo Developer:**

| Practice | Description | Frequency |
|----------|-------------|-----------|
| **Never commit .env** | Always verify `.env` in `.gitignore` before `git add` | Every commit |
| **Review logs before sharing** | Ensure no API keys in logs before posting to forums | Before sharing |
| **Use HTTPS for examples** | Never hardcode HTTP URLs in documentation | During writing |
| **Rotate keys periodically** | Change API keys every 90 days (best practice) | Quarterly |
| **Review dependencies** | Run `pip audit` before major releases | Weekly |

### 11.2 Secure Configuration Checklist

**Initial Setup:**

```bash
# 1. Create .env file with restricted permissions
touch .env
chmod 600 .env

# 2. Verify .env is gitignored
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore

# 3. Add API keys to .env (NOT to version control)
echo "FMP_KEY=your_key_here" >> .env
echo "POLYGON_KEY=your_key_here" >> .env
echo "FRED_KEY=your_key_here" >> .env

# 4. Verify keys load correctly
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('FMP:', bool(os.getenv('FMP_KEY')))"

# 5. Install pre-commit hook for secret scanning
cp scripts/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## 12. Risk Register

| ID | Risk | Likelihood | Impact | Risk Level | Treatment |
|----|------|------------|--------|------------|-----------|
| **SR-001** | API key committed to git | LOW (with .gitignore) | CRITICAL | MEDIUM | `.gitignore` + pre-commit hook |
| **SR-002** | API key in log files | LOW (with sanitization) | HIGH | LOW | Regex-based log sanitization (FR-014) |
| **SR-003** | Dependency vulnerability | MEDIUM (supply chain) | MEDIUM | MEDIUM | Weekly `pip audit` + pinned versions |
| **SR-004** | Rate limit abuse (cost) | LOW (with QoS controls) | MEDIUM | LOW | QoS Semaphore Router (FR-005) |
| **SR-005** | Cache file tampering | LOW (local system) | LOW | NEGLIGIBLE | POSIX file permissions |
| **SR-006** | MITM attack on APIs | LOW (TLS enforced) | MEDIUM | LOW | TLS 1.2+ via `aiohttp` |
| **SR-007** | .env file world-readable | MEDIUM (user error) | CRITICAL | MEDIUM | Document `chmod 600` in setup |

**Overall Risk Posture:** LOW - Appropriate for a personal research tool with no external users or sensitive data (beyond API keys).

---

## 13. Security Metrics

| Metric | Target | Measurement | Frequency |
|--------|--------|-------------|-----------|
| API keys in git history | 0 | `git log -p -S "FMP_KEY\|POLYGON_KEY\|FRED_KEY"` | Monthly |
| API keys in logs | 0 | `grep -r "FMP_KEY\|POLYGON_KEY\|FRED_KEY" logs/` | Weekly |
| Critical vulnerabilities | 0 | `pip audit --severity HIGH` | Weekly |
| .env file permissions | 600 (user-only) | `ls -la .env` | Setup verification |
| HTTPS enforcement | 100% | Code review (all HTTP URLs rejected) | Per commit |

---

## 14. What This Security Design Doesn't Cover (And Why That's OK)

| Enterprise Control | Why Skipped | Alternative |
|--------------------|-------------|-------------|
| **HashiCorp Vault** | Overkill for single-user local tool | `.env` file with OS permissions |
| **OAuth 2.0** | No user authentication needed | N/A (single user) |
| **RBAC** | No multi-user access | N/A (single user) |
| **WAF** | No web application | N/A (CLI framework) |
| **SIEM** | No security operations team | Manual log review |
| **DLP** | No sensitive data (public financials) | N/A (data is public) |
| **Zero Trust** | No network perimeter | OS firewall sufficient |
| **Automated Patching** | Breaking changes risk research continuity | Manual updates with testing |

**Design Philosophy:** Security controls should be proportionate to the threat model and risk tolerance. Personal research tools do not require enterprise-grade security infrastructure.

---

## 15. Security Review Schedule

| Activity | Frequency | Owner | Next Review |
|----------|-----------|-------|-------------|
| Dependency audit (`pip audit`) | Weekly | Developer | [Ongoing] |
| API key rotation | 90 days | Developer | [90 days from setup] |
| .gitignore verification | Per commit | Pre-commit hook | [Automated] |
| Log sanitization testing | Per release | Unit tests | [Automated] |
| Security design review | Annually | Developer | 2027-01-31 |

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Security Agent | 2026-01-31 | ✅ Generated |
| Security Review | Solo Developer | | ☐ Pending Review |
| Risk Acceptance | Solo Developer | | ☐ Pending Approval |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | Security Agent | Initial security design for OmniData Nexus Core |

---

**Security Contact:** For vulnerability reports, contact the project maintainer via GitHub Issues.

**Disclosure Policy:** Personal tool - no formal vulnerability disclosure program. Responsible disclosure appreciated.

---

*Security design scaled appropriately for a personal research tool. Not all enterprise controls apply.*
