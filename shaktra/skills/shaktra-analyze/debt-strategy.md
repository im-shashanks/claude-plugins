# Debt Strategy — Technical Debt Remediation Planning

Transforms D6 (Tech Debt) analysis findings into a prioritized remediation plan with auto-generated story drafts. Executed by CBA Analyzer in `debt-strategy` mode.

---

## Prerequisites

- `.shaktra/analysis/tech-debt.yml` must exist (D6 dimension output)
- If missing, the orchestrator runs D6 first before invoking this workflow

---

## Debt Categorization Framework

Categorize each debt item from `tech-debt.yml` into exactly one category:

### Safety
Security vulnerabilities, data integrity risks, unvalidated inputs reaching sensitive operations. Items that could cause data loss, breaches, or compliance violations.

**Indicators:** CVEs, hardcoded credentials, missing input validation, unencrypted sensitive data, SQL injection vectors, missing auth checks.

### Velocity
Complexity hotspots that slow development — high cyclomatic complexity, tightly coupled modules, missing abstractions that force developers to understand the entire system to make local changes.

**Indicators:** God modules (>500 lines), circular dependencies, high coupling scores, frequently modified files with many dependents, missing interfaces between layers.

### Reliability
Test gaps, flaky test patterns, missing error handling, uncovered critical paths. Items that increase the probability of production incidents.

**Indicators:** Coverage gaps on critical paths, missing negative tests, no timeout on external calls, swallowed exceptions, untested error recovery paths.

### Maintenance
Dead code, outdated patterns, deprecated API usage, inconsistent conventions. Items that increase cognitive load without immediate risk.

**Indicators:** Unreferenced exports, deprecated library usage, mixed naming conventions, commented-out code blocks, outdated configuration patterns.

---

## Scoring Methodology

Score each debt item on two axes:

**Impact (1-5):** How much does this item affect the codebase?
| Score | Meaning |
|---|---|
| 5 | Critical — production incidents likely, security exposure, data loss risk |
| 4 | High — significant development slowdown, reliability concern |
| 3 | Moderate — noticeable friction, occasional issues |
| 2 | Low — minor inconvenience, cosmetic concern |
| 1 | Minimal — negligible effect |

**Effort to fix (1-5, inverted — 5 = easiest):**
| Score | Meaning |
|---|---|
| 5 | Trivial — single file, < 1 hour, no risk |
| 4 | Easy — few files, < half day, low risk |
| 3 | Moderate — multiple files, 1-2 days, some testing needed |
| 2 | Hard — cross-cutting, 3-5 days, significant testing |
| 1 | Very hard — architectural change, > 1 week, high risk |

**Priority score** = `impact` x `effort_to_fix`

Higher score = higher priority (high impact + easy fix = best ROI).

---

## Remediation Tiers

### Urgent (Priority: Immediate)
**Entry criteria:** Category = Safety with impact >= 4, OR priority_score >= 20
**Action:** Generate story drafts — these should enter the next sprint.

### Strategic (Priority: Next 2-3 sprints)
**Entry criteria:** Category = Velocity or Reliability with priority_score >= 12, OR any category with priority_score 15-19
**Action:** Generate story drafts — schedule based on sprint capacity.

### Opportunistic (Priority: When convenient)
**Entry criteria:** priority_score < 12, OR category = Maintenance
**Action:** No dedicated stories — fix when touching nearby code. Document trigger files.

---

## Story Generation Rules

### Title Format
- Safety: `[Security] {specific fix description}`
- Velocity: `[Refactor] {specific simplification}`
- Reliability: `[Reliability] {specific coverage/handling improvement}`
- Maintenance: `[Cleanup] {specific cleanup task}`

### Scope
Describe the bounded area of change — which files, modules, or components are affected. Keep scope small enough for a single story (1-5 story points).

### Acceptance Criteria
Generate 3-5 criteria per story:
1. What must change (the fix itself)
2. What must not break (regression guard)
3. How to verify (test or metric)

For Safety stories, always include:
- "No new security findings in the affected area after fix"
- Specific vulnerability remediation verification

For Velocity stories, always include:
- "Cyclomatic complexity of affected module reduced to <= {target}"
- "Circular dependency between {modules} eliminated"

---

## Metrics

Calculate and include in the output:

- `total_items`: count of all categorized debt items
- `health_score_current`: copy from `tech-debt.yml` summary health score
- `projected_score_after_urgent`: estimate the health score improvement if all Urgent tier items are resolved (increase current score by 2 points per resolved Safety item, 1 point per other Urgent item, capped at 100)

---

## Output Schema

Write to `.shaktra/analysis/debt-strategy.yml` following the schema in `analysis-output-schemas.md`.

The `summary:` section (~400 tokens) must include:
- Total debt items and distribution by category
- Top 3 urgent items with brief descriptions
- Current health score and projected improvement
- Recommended sprint allocation (how many urgent stories per sprint)

---

## CBA Analyzer Prompt Template

```
You are the shaktra-cba-analyzer agent in debt-strategy mode.

Input: .shaktra/analysis/tech-debt.yml
Output: .shaktra/analysis/debt-strategy.yml

1. Read tech-debt.yml — load all findings
2. Read debt-strategy.md — this file, for categorization and scoring rules
3. Read analysis-output-schemas.md — for output schema
4. Categorize each finding into Safety/Velocity/Reliability/Maintenance
5. Score each item: impact (1-5) x effort_to_fix (1-5 inverted)
6. Assign remediation tiers based on entry criteria
7. Generate story drafts for Urgent and Strategic tiers
8. Calculate metrics
9. Write output to .shaktra/analysis/debt-strategy.yml
```
