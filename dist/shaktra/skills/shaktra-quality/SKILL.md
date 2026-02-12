---
name: shaktra-quality
description: >
  Quality engine for the TDD pipeline — provides quick-check (36 checks) for gate reviews
  and comprehensive review (14 dimensions) for final quality assessment. Loaded by sw-quality agent.
user-invocable: false
---

# Shaktra Quality — Quality Engine

This skill provides the review checklists and processes used by the sw-quality agent during TDD pipeline gates. It operates in two modes: quick-check for gate reviews and comprehensive for final assessment.

## Boundary

**This skill defines:** HOW to evaluate code and tests (check procedures, gate logic, review processes).

**shaktra-reference defines:** WHAT severity levels mean (`severity-taxonomy.md`), WHAT quality dimensions exist (`quality-dimensions.md`), and WHAT the merge gate logic is.

**shaktra-tdd defines:** HOW to write tests and code (practices, patterns). This skill evaluates adherence to those practices.

This skill never restates severity definitions or quality dimension frameworks — it references them.

## Modes

### QUICK_CHECK (TDD Gate Reviews)

- 36 checks organized by gate (Plan, Test, Code)
- All checks loaded regardless of tier (check depth controls severity enforcement, not loading)
- Gate-specific focus: sw-quality applies the subset relevant to the current gate
- Max 3 fix loops per gate
- Defined in `quick-check.md`

### COMPREHENSIVE (Final Quality Review)

- Full 14-dimension review (A-M from `quality-dimensions.md` + Dimension N: Plan Adherence)
- Coverage verification via actual test execution
- Decision consolidation: extract `important_decisions` from handoff, promote to `decisions.yml`
- Cross-story consistency: compare decisions against existing `decisions.yml`
- Defined in `comprehensive-review.md`

### REFACTOR_VERIFY (Refactoring Verification)

- Confirms refactoring preserved behavior and improved quality
- Verifies: all tests green, coverage not decreased, no new P0/P1, smell count reduced
- For structural tier: additionally checks architecture boundaries and circular dependencies
- Emits `REFACTOR_PASS` or `REFACTOR_BLOCKED`

## Gate Logic

Read from `shaktra-reference/severity-taxonomy.md` — restated here as operational reference:

```
p0_count = count findings where severity == P0
p1_count = count findings where severity == P1
p1_max   = read settings.quality.p1_threshold

if p0_count > 0:
    emit CHECK_BLOCKED
else if p1_count > p1_max:
    emit CHECK_BLOCKED
else:
    emit CHECK_PASSED
```

Max fix loops: 3 per gate. After 3 failed attempts, emit `MAX_LOOPS_REACHED` and escalate to user with all unresolved findings.

## Sub-Files

| File | Purpose |
|---|---|
| `quick-check.md` | 36 checks with IDs, severities, gates, detection guidance, and examples |
| `comprehensive-review.md` | Full 14-dimension review process with plan adherence and decision consolidation |
| `performance-data-checks.md` | Performance and data layer checks (PG-01 through PG-08, DL-01 through DL-08) |
| `security-checks.md` | Security checks aligned with OWASP Top 10 (SE-01 through SE-12, ST-01 through ST-03) |
| `architecture-checks.md` | Architecture governance checks enforcing `settings.project.architecture` (ARC-01 through ARC-06) |

## References

- `shaktra-reference/severity-taxonomy.md` — P0-P3 definitions and merge gate logic
- `shaktra-reference/quality-dimensions.md` — 13 dimensions (A-M) framework
- `shaktra-reference/quality-principles.md` — 10 core principles
- `shaktra-reference/guard-tokens.md` — tokens emitted during reviews
- `shaktra-reference/story-tiers.md` — tier-based check depth behavior
