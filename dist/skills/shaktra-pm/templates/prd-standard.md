# PRD Template — Standard

Full PRD template for 6-8 week features. Use for Medium and Large tier work requiring design docs.

---

```markdown
---
id: PRD-XXX
title: "[Feature Name]"
version: "1.0.0"
status: draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: "[Author Name]"
stakeholders:
  - name: "[Name]"
    role: "[Role]"
---

# [Feature Name]

## 1. Problem Statement

### What problem are we solving?

[Describe the core problem in 2-3 sentences. Be specific about who has this problem and the impact.]

### Why now?

[Business or market driver that makes this urgent. What happens if we don't solve it?]

### Evidence

- [Data point or user feedback supporting the problem]
- [Second evidence point]

---

## 2. Users & Personas

### Target Users

| Segment | Description | % of Users |
|---|---|---|
| [Primary] | [Description] | [%] |
| [Secondary] | [Description] | [%] |

### Persona References

<!-- If personas exist in .shaktra/personas/, reference them here -->
- Primary: [P-001 — Persona Name]
- Secondary: [P-002 — Persona Name]

---

## 3. Goals & Success Metrics

### Goals

1. **[Goal 1]** — [Measurable outcome]
2. **[Goal 2]** — [Measurable outcome]

### Success Metrics

| Metric | Current | Target | Measurement |
|---|---|---|---|
| [Metric 1] | [Baseline] | [Target] | [How measured] |
| [Metric 2] | [Baseline] | [Target] | [How measured] |

### Anti-Goals

- [What we are explicitly NOT trying to achieve]

---

## 4. Functional Requirements

### Must Have (P0)

| ID | Requirement | Acceptance Test |
|---|---|---|
| REQ-001 | [Requirement description] | [How to verify] |
| REQ-002 | [Requirement description] | [How to verify] |

### Should Have (P1)

| ID | Requirement | Acceptance Test |
|---|---|---|
| REQ-003 | [Requirement description] | [How to verify] |

### Could Have (P2)

| ID | Requirement | Acceptance Test |
|---|---|---|
| REQ-004 | [Requirement description] | [How to verify] |

### Won't Have (Out of Scope)

- [Explicitly excluded for this release]

---

## 5. Non-Functional Requirements

| Category | Requirement | Target |
|---|---|---|
| Performance | [Latency requirement] | [e.g., < 200ms p95] |
| Scalability | [Throughput requirement] | [e.g., 1000 RPS] |
| Reliability | [Availability requirement] | [e.g., 99.9% uptime] |
| Security | [Security requirement] | [e.g., SOC2 compliant] |

---

## 6. Scope

### In Scope

- [What this PRD covers]
- [Second in-scope item]

### Out of Scope

- [What this PRD does NOT cover]
- [Second out-of-scope item]

### Future Considerations

- [Potential future enhancements not in this release]

---

## 7. Assumptions & Constraints

### Assumptions

- [Assumption 1 — what we believe to be true]
- [Assumption 2]

### Constraints

| Type | Constraint |
|---|---|
| Technical | [Technical limitation] |
| Business | [Business constraint] |
| Timeline | [Delivery deadline] |
| Resource | [Team/budget constraint] |

---

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| [Risk 1] | High/Med/Low | High/Med/Low | [Mitigation strategy] |
| [Risk 2] | High/Med/Low | High/Med/Low | [Mitigation strategy] |

---

## 9. Dependencies

| Dependency | Type | Owner | Status |
|---|---|---|---|
| [Dependency 1] | External/Internal | [Team/Person] | [Status] |

---

## 10. Timeline

| Milestone | Target Date | Description |
|---|---|---|
| PRD Approved | [Date] | Requirements locked |
| Design Complete | [Date] | Architecture finalized |
| Development Complete | [Date] | Feature code complete |
| Launch | [Date] | Available to users |
```
