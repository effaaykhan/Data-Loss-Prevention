# CyberSentinel DLP - Policy Templates

This directory contains pre-built, production-ready DLP policy templates for major compliance frameworks.

## Available Templates

### 1. GDPR Compliance (`gdpr_compliance.yml`)
**Regulation:** EU General Data Protection Regulation
**Scope:** Personal data of EU residents

**Coverage:**
- ✅ Personal identifiers (email, phone, name, address, IP)
- ✅ Special category data (Article 9)
- ✅ Cross-border data transfers (Chapter V)
- ✅ Encryption requirements (Article 32)
- ✅ Data minimization (Article 5)
- ✅ Right to be forgotten (Article 17)
- ✅ Breach notification (Article 33)
- ✅ Consent verification (Article 7)

**Rules:** 8 comprehensive rules
**Retention:** 7 years (2,555 days)

### 2. HIPAA Compliance (`hipaa_compliance.yml`)
**Regulation:** Health Insurance Portability and Accountability Act
**Scope:** Protected Health Information (PHI)

**Coverage:**
- ✅ PHI detection (18 identifiers)
- ✅ Minimum necessary standard (§164.502(b))
- ✅ Unauthorized access prevention
- ✅ Encryption requirements (§164.312)
- ✅ Breach notification assessment (§164.402)
- ✅ De-identification verification (§164.514)
- ✅ Business Associate Agreements (§164.502(e))
- ✅ Comprehensive audit logging (§164.312(b))
- ✅ Psychotherapy notes protection (§164.508)
- ✅ Marketing restrictions (§164.508(a)(3))
- ✅ Patient access rights (§164.524)
- ✅ Research use compliance (§164.512(i))

**Rules:** 12 comprehensive rules
**Retention:** 7 years minimum (2,555 days)

### 3. PCI-DSS Compliance (`pci_dss_compliance.yml`)
**Standard:** Payment Card Industry Data Security Standard v4.0
**Scope:** Cardholder data and sensitive authentication data

**Coverage:**
- ✅ Primary Account Number (PAN) detection with Luhn validation
- ✅ Sensitive Authentication Data (CVV, PIN) - **PROHIBITED**
- ✅ Encryption in transit (Requirement 4)
- ✅ PAN in email blocking
- ✅ Storage protection (Requirement 3.4)
- ✅ Retention policy enforcement
- ✅ Test/dev environment protection
- ✅ Access control monitoring
- ✅ Comprehensive audit logging
- ✅ Wireless transmission security
- ✅ Third-party service provider monitoring
- ✅ PAN disclosure tracking

**Rules:** 12 comprehensive rules
**Retention:** 1 year minimum (365 days)

### 4. SOX Compliance (`sox_compliance.yml`)
**Act:** Sarbanes-Oxley Act
**Scope:** Financial data and records

**Coverage:**
- ✅ Financial statements and reports protection
- ✅ Document destruction prevention (Section 802)
- ✅ Audit trail requirements (Section 404)
- ✅ Segregation of duties enforcement
- ✅ Change management controls
- ✅ Access control reviews (quarterly)
- ✅ Insider trading risk monitoring
- ✅ Whistleblower protection (Section 806)
- ✅ Auditor independence monitoring
- ✅ Retention policy compliance (7 years)
- ✅ Executive certification tracking (Section 302)
- ✅ IT General Controls (ITGC) monitoring

**Rules:** 12 comprehensive rules
**Retention:** 7 years (2,555 days)

---

## Quick Start

### 1. Choose a Template

Select the template(s) that match your compliance requirements:

```bash
# View available templates
ls -la config/policies/templates/

# Read template content
cat config/policies/templates/gdpr_compliance.yml
```

### 2. Copy to Active Policies Directory

```bash
# Copy template to active policies
cp config/policies/templates/gdpr_compliance.yml /etc/cybersentinel/policies/

# Or copy multiple templates
cp config/policies/templates/*.yml /etc/cybersentinel/policies/
```

### 3. Customize for Your Organization

Edit the copied policy file:

```bash
nano /etc/cybersentinel/policies/gdpr_compliance.yml
```

**Required Customizations:**
- ✅ Update notification recipients (DPO, compliance officers, etc.)
- ✅ Adjust retention periods if needed
- ✅ Configure quarantine locations
- ✅ Set encryption settings
- ✅ Define authorized roles
- ✅ Enable/disable rules based on your operations

### 4. Validate the Policy

```bash
# Validate YAML syntax
yamllint /etc/cybersentinel/policies/gdpr_compliance.yml

# Test policy loading
python -m app.services.policy_engine --validate /etc/cybersentinel/policies/
```

### 5. Deploy and Monitor

```bash
# Restart manager to load new policies
docker-compose restart manager

# Check policy loading in logs
docker-compose logs manager | grep "Policy loaded"

# Monitor policy violations
tail -f /var/log/cybersentinel/policy_violations.log
```

---

## Customization Guide

### Update Notification Recipients

```yaml
# Find sections like this:
actions:
  - type: "notify"
    channel: "email"
    recipients:
      - "dpo@company.com"       # ← Change this
      - "compliance@company.com" # ← Change this
```

**Replace with your organization's addresses:**
- Data Protection Officer (DPO)
- Compliance team
- Security team
- Legal team
- Audit committee

### Adjust Retention Periods

```yaml
actions:
  - type: "audit"
    log_level: "detailed"
    retention_days: 2555  # ← 7 years, adjust if needed
```

**Common retention requirements:**
- GDPR: 7 years (varies by country)
- HIPAA: 7 years minimum
- PCI-DSS: 1 year minimum (3 months immediately available)
- SOX: 7 years for audit records

### Configure Quarantine Storage

```yaml
actions:
  - type: "quarantine"
    location: "/quarantine/gdpr/special"  # ← Change path
    encrypt: true
```

**Best practices:**
- Use encrypted storage
- Implement access controls
- Regular backup
- Separate by compliance type

### Define Authorized Roles

```yaml
conditions:
  - field: "user.role"
    operator: "in"
    value:
      - "physician"     # ← Add your roles
      - "nurse"         # ← Add your roles
      - "admin"         # ← Add your roles
```

**For each template:**
- GDPR: Data processors, DPO, authorized staff
- HIPAA: Physicians, nurses, billing staff, authorized personnel
- PCI-DSS: Payment processors, authorized payment staff
- SOX: Finance team, auditors, executives

### Enable/Disable Rules

```yaml
rules:
  - id: "gdpr-rule-001"
    name: "Detect Personal Identifiers"
    enabled: true  # ← Set to false to disable
```

**When to disable rules:**
- Not applicable to your operations
- Implementing in phases
- Testing specific rules
- Temporary exceptions (document!)

---

## Testing

### Test Policy Syntax

```bash
# YAML syntax validation
yamllint config/policies/templates/*.yml

# Policy structure validation
python -c "
import yaml
with open('config/policies/templates/gdpr_compliance.yml') as f:
    policy = yaml.safe_load(f)
    assert 'policy' in policy
    assert 'rules' in policy
    print('✓ Policy structure valid')
"
```

### Test Policy Loading

```python
# Test script
from app.services.policy_engine import PolicyEngine

engine = PolicyEngine(policies_directory="/etc/cybersentinel/policies")
engine.load_policies()

print(f"Loaded {len(engine.policies)} policies")
for policy in engine.policies:
    print(f"  - {policy['policy']['id']}: {policy['policy']['name']}")
```

### Test Policy Evaluation

```python
# Test event against policy
import asyncio
from app.services.policy_engine import PolicyEngine

async def test_policy():
    engine = PolicyEngine(policies_directory="/etc/cybersentinel/policies")
    engine.load_policies()

    # Test event with credit card
    event = {
        "event_id": "test-001",
        "classification": [
            {"type": "credit_card", "confidence": 0.95, "luhn_valid": True}
        ]
    }

    result = await engine.evaluate_event(event)
    print(f"Matched policies: {len(result.get('policy_matches', []))}")
    for match in result.get('policy_matches', []):
        print(f"  - {match['policy_id']}: {match['policy_name']}")

asyncio.run(test_policy())
```

---

## Integration

### With Existing Infrastructure

**SIEM Integration:**
```yaml
actions:
  - type: "notify"
    channel: "siem"
    destination: "siem.company.com:514"
    format: "CEF"  # or "JSON", "LEEF"
```

**Email Notifications:**
```yaml
actions:
  - type: "notify"
    channel: "email"
    smtp_server: "smtp.company.com"
    smtp_port: 587
    use_tls: true
    recipients:
      - "alerts@company.com"
```

**Webhook Integration:**
```yaml
actions:
  - type: "webhook"
    url: "https://your-system.com/api/dlp-alerts"
    method: "POST"
    headers:
      Authorization: "Bearer ${WEBHOOK_TOKEN}"
```

### With Compliance Tools

**GRC Platforms:**
- ServiceNow GRC
- RSA Archer
- MetricStream
- LogicGate

**Configuration:**
```yaml
actions:
  - type: "create_incident"
    system: "servicenow"
    api_endpoint: "https://instance.service-now.com/api"
    category: "compliance_violation"
```

---

## Compliance Mapping

### Multi-Framework Compliance

Many organizations need to comply with multiple frameworks. Templates can be combined:

```bash
# Deploy multiple templates
cp config/policies/templates/gdpr_compliance.yml /etc/cybersentinel/policies/
cp config/policies/templates/hipaa_compliance.yml /etc/cybersentinel/policies/
cp config/policies/templates/pci_dss_compliance.yml /etc/cybersentinel/policies/
```

### Framework Overlap

Some requirements overlap across frameworks:

| Requirement | GDPR | HIPAA | PCI-DSS | SOX |
|-------------|------|-------|---------|-----|
| Encryption | ✓ | ✓ | ✓ | ✓ |
| Access Control | ✓ | ✓ | ✓ | ✓ |
| Audit Logging | ✓ | ✓ | ✓ | ✓ |
| Data Retention | ✓ | ✓ | ✓ | ✓ |
| Breach Notification | ✓ | ✓ | ✓ | - |

**Optimization:** Shared controls can reduce compliance burden.

---

## Maintenance

### Regular Reviews

**Quarterly:**
- Review policy violations
- Update authorized user lists
- Test policy effectiveness
- Adjust thresholds if needed

**Annually:**
- Full compliance audit
- Update for regulation changes
- Review and update retention policies
- Train staff on changes

### Version Control

```bash
# Track policy changes in git
cd /etc/cybersentinel/policies
git init
git add *.yml
git commit -m "Initial policy deployment"

# Update policy
nano gdpr_compliance.yml
git diff gdpr_compliance.yml  # Review changes
git commit -am "Update GDPR recipients"
```

### Audit Trail

```bash
# Log all policy changes
echo "$(date) - Updated GDPR policy v1.1 - Changed recipients" >> /var/log/cybersentinel/policy_changes.log
```

---

## Support

### Documentation
- **GDPR:** https://gdpr.eu/
- **HIPAA:** https://www.hhs.gov/hipaa/
- **PCI-DSS:** https://www.pcisecuritystandards.org/
- **SOX:** https://www.sec.gov/spotlight/sarbanes-oxley.htm

### Getting Help
- Review template metadata section for customization notes
- Check deployment checklist before going live
- Consult with legal/compliance team
- Contact your DLP implementation team

### Contributing
To contribute improvements to these templates:
1. Test thoroughly in non-production
2. Document changes
3. Submit pull request with rationale
4. Include compliance verification

---

## License

These templates are provided as examples and should be customized for your organization's specific requirements. Always consult with legal and compliance professionals before deploying to production.

**Last Updated:** 2025-01-13
**Template Version:** 1.0
