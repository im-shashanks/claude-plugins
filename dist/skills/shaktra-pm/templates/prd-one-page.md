# PRD Template — One Page

Abbreviated PRD template for 2-4 week features. Use for Small tier work or well-understood enhancements that don't require full design docs.

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

## Problem

[2-3 sentences: What problem? Who has it? Why does it matter?]

## Solution

[2-3 sentences: What are we building? How does it solve the problem?]

## Users

**Primary:** [Who is this for?]

**Not for:** [Who is this explicitly NOT for?]

## Requirements

### Must Have

| ID | Requirement | Acceptance Test |
|---|---|---|
| REQ-001 | [Requirement] | [How to verify] |
| REQ-002 | [Requirement] | [How to verify] |

### Should Have

| ID | Requirement | Acceptance Test |
|---|---|---|
| REQ-003 | [Requirement] | [How to verify] |

### Out of Scope

- [What this does NOT include]

## Success Metrics

| Metric | Target |
|---|---|
| [Metric 1] | [Target value] |
| [Metric 2] | [Target value] |

## Constraints

- **Timeline:** [Delivery date]
- **Technical:** [Key technical constraint, if any]
- **Dependency:** [Key dependency, if any]

## Risks

| Risk | Mitigation |
|---|---|
| [Risk 1] | [Mitigation] |
```

---

## When to Use One-Page vs Standard

| Criteria | One-Page | Standard |
|---|---|---|
| Timeline | 2-4 weeks | 6-8+ weeks |
| Story tier | Small, some Medium | Medium, Large |
| Complexity | Single component | Multi-component |
| Stakeholders | 1-2 | 3+ |
| Integration | Minimal | External APIs, new data models |
| Design doc needed | No | Yes |

If uncertain, start with one-page. Expand to standard if complexity emerges during design.
