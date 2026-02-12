# Threat Modeling Practices

Design-first security practices using the STRIDE framework. Loaded by the architect agent during design doc creation and by tpm-quality during design review. Ensures security is considered before a single line of code is written.

---

## 1. STRIDE Framework

Apply STRIDE to every component in the design. For each component, ask the threat-specific question.

### Spoofing (Identity)

**Question:** Can an attacker pretend to be someone or something else?

| Attack Surface | Check |
|---------------|-------|
| User authentication | Is the auth mechanism specified (OAuth, JWT, session, API key)? |
| Service-to-service | Are services authenticated (mTLS, service tokens, API keys)? |
| Client identity | Can client-side tokens/cookies be forged or replayed? |

### Tampering (Integrity)

**Question:** Can an attacker modify data in transit or at rest?

| Attack Surface | Check |
|---------------|-------|
| API requests | Are inputs validated (type, range, format) at the API boundary? |
| Data at rest | Are critical records protected from unauthorized modification (checksums, signatures)? |
| Configuration | Can config files be modified by unauthorized processes? |

### Repudiation (Accountability)

**Question:** Can a user deny performing an action?

| Attack Surface | Check |
|---------------|-------|
| State changes | Are all state-changing operations logged with actor, action, timestamp? |
| Financial actions | Are payment/transfer operations auditable with tamper-evident logs? |
| Admin actions | Are privileged operations logged separately from regular operations? |

### Information Disclosure (Confidentiality)

**Question:** Can an attacker access data they shouldn't see?

| Attack Surface | Check |
|---------------|-------|
| API responses | Do responses include only the fields the requester is authorized to see? |
| Error messages | Do error messages avoid exposing internal details (SQL, paths, stack traces)? |
| Logs | Are credentials, tokens, PII, and secrets excluded from log output? |
| Storage | Is PII encrypted at rest? Are encryption keys managed properly? |

### Denial of Service (Availability)

**Question:** Can an attacker make the system unavailable?

| Attack Surface | Check |
|---------------|-------|
| Public endpoints | Are rate limits defined? Is there request size limiting? |
| Resource consumption | Are there bounds on memory, connections, queue depth, file uploads? |
| Dependency failure | Does the system degrade gracefully when dependencies are unavailable? |

### Elevation of Privilege (Authorization)

**Question:** Can an attacker gain access beyond their authorization level?

| Attack Surface | Check |
|---------------|-------|
| Horizontal access | Can user A access user B's resources? (IDOR check) |
| Vertical access | Can a regular user access admin functions? |
| Default permissions | Are permissions default-deny? (Must explicitly grant, not explicitly block) |

---

## 2. Trust Boundary Identification

Every boundary between trust levels requires explicit security controls.

### Boundary Map

| Boundary | From → To | Required Controls |
|----------|----------|-------------------|
| User → Server | Untrusted → Application | Authentication, input validation, rate limiting, CORS |
| Server → Server | Service → Service | Service auth (mTLS/tokens), request validation, circuit breaker |
| Server → Database | Application → Data | Connection auth, query parameterization, least-privilege DB user |
| Server → Third-Party | Application → External | API key management, response validation, timeout, error handling |
| Admin → System | Privileged → Application | MFA, audit logging, IP allowlisting, session timeout |

### Boundary Specification

For each trust boundary in the design doc, specify:
- What crosses the boundary (data, commands, events)
- How identity is verified at the boundary
- What validation is performed at the boundary
- How failures at the boundary are handled

---

## 3. Data Sensitivity Classification

### Classification Levels

| Level | Examples | Handling Requirements |
|-------|---------|----------------------|
| **PII** | Name, email, phone, address, date of birth | Encrypt at rest, mask in logs, access-controlled, retention policy |
| **Credentials** | Passwords, API keys, tokens, private keys | Never log, hash (not encrypt) passwords, rotate regularly, vault storage |
| **Financial** | Account numbers, transaction amounts, card numbers | Encrypt in transit + at rest, PCI DSS compliance, audit trail |
| **Health** | Medical records, diagnoses, prescriptions | HIPAA compliance, access logging, minimum necessary principle |
| **Internal** | Business logic, configuration, metrics | Standard access controls, no public exposure |
| **Public** | Marketing content, public API docs | No special handling |

### Classification-Driven Requirements

For each data field in the design:
1. Classify the sensitivity level
2. Apply the handling requirements for that level
3. Document in the design doc's data model section

---

## 4. Threat Model Deliverable

The architect produces a threat model as part of the design doc (Section 6 — Security or a dedicated security section):

```yaml
threat_model:
  components:
    - name: "API Gateway"
      stride:
        spoofing: {threat: "Forged JWT", mitigation: "Signature verification with RS256", verification: "T-SEC-01"}
        tampering: {threat: "Modified request body", mitigation: "Input validation", verification: "T-SEC-02"}
        # ... all 6 STRIDE categories
  trust_boundaries:
    - boundary: "User → API"
      controls: ["JWT auth", "Input validation", "Rate limiting", "CORS whitelist"]
  data_classification:
    - field: "user.email"
      level: PII
      handling: "Encrypted at rest, masked in logs"
```

---

## AI-Enforceable Checks

Applied during design review by tpm-quality agent.

| ID | Check | Severity | Detection |
|----|-------|----------|-----------|
| TM-01 | Every component has all 6 STRIDE categories assessed | P1 | Component with fewer than 6 STRIDE entries |
| TM-02 | Every trust boundary has authentication and validation specified | P0 | Trust boundary without identity verification or input validation |
| TM-03 | PII fields identified and encryption-at-rest specified | P0 | Data field classified as PII without encryption handling |
| TM-04 | Public-facing endpoints have rate limiting specified | P1 | Public endpoint without rate limit configuration |
| TM-05 | State-changing operations have audit trail specified | P2 | Mutating endpoint without logging/audit mention |
