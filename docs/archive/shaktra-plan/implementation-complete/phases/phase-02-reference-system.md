# Phase 2 — Shared Reference System [COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) before starting.
> **Depends on:** Phase 1 (Foundation)
> **Blocks:** Phase 3

---

## Objective

Create the **single source of truth** that ALL agents and skills reference. This phase establishes the quality taxonomy, principles, guard tokens, and tier definitions. After this phase, no other file may redefine these concepts — they must reference this skill.

## Deliverables

| File | Lines | Purpose |
|------|-------|---------|
| `skills/shaktra-reference/SKILL.md` | ~30 | Skill manifest |
| `skills/shaktra-reference/severity-taxonomy.md` | ~70 | P0-P3 definitions, merge gate logic |
| `skills/shaktra-reference/quality-principles.md` | ~50 | 10 Shaktra quality principles |
| `skills/shaktra-reference/guard-tokens.md` | ~50 | 15 guard tokens with usage rules |
| `skills/shaktra-reference/story-tiers.md` | ~70 | 4 tier definitions with fields and thresholds |
| `skills/shaktra-reference/quality-dimensions.md` | ~80 | 13 review dimensions (A-M) |

## File Content Outlines

**SKILL.md:**
```yaml
---
name: shaktra-reference
description: Shared constants and quality standards for all Shaktra agents
user-invocable: false
---
```
Brief intro pointing to sub-files. This skill is loaded by every agent.

**severity-taxonomy.md (THE canonical source — no other file may define these):**

| Level | Name | Definition | Examples | Merge Gate |
|-------|------|-----------|----------|------------|
| P0 | Critical | Security vulnerabilities, data loss, race conditions, missing timeouts, hardcoded credentials, unbounded operations | SQL injection, `except: pass` hiding crash, no timeout on HTTP call | Any P0 = BLOCKED |
| P1 | Significant | Missing error path coverage, over-mocking, placeholder logic, generic error messages, behavioral test gaps | `raise Exception("Failed")`, `mock.called` assertions, TODO in critical path | > threshold = BLOCKED |
| P2 | Quality | Generic naming, over-commenting, missing types, high complexity, dead code | `data` variable name, `# Import os` above `import os`, cyclomatic > 10 | Logged, not blocking |
| P3 | Cosmetic | Style, naming conventions, comment formatting | Inconsistent quotes, trailing whitespace | Logged, not blocking |

Merge gate logic (pseudocode):
```
if p0_count > 0: BLOCKED
if p1_count > settings.quality.p1_threshold: BLOCKED
if p1_count > 0: WARNING
else: PASS
```

**quality-principles.md (10 principles, replacing Forge's 31):**
1. Correct before fast
2. Fail explicitly (no silent swallowing)
3. Test behavior, not implementation
4. One responsibility per unit
5. Inject dependencies, own state
6. Handle every error path
7. Log structured, trace distributed
8. Bound all resources (timeouts, pools, queues)
9. Make it work, make it right, make it fast (in order)
10. Every tradeoff documented in code comment

**guard-tokens.md (15 tokens, down from Forge's 40+):**
- Phase progression: `TESTS_NOT_RED`, `TESTS_NOT_GREEN`, `PHASE_GATE_FAILED`, `COVERAGE_GATE_FAILED`
- Quality gates: `CHECK_PASSED`, `CHECK_BLOCKED`, `QUALITY_PASS`, `QUALITY_BLOCKED`
- Workflow: `STORY_COMPLETE`, `STORY_FAILED`, `WORKFLOW_STEP_SKIPPED`, `MAX_LOOPS_REACHED`
- Communication: `GAPS_FOUND`, `CLARIFICATION_NEEDED`, `VALIDATION_FAILED`

Each token includes: when to emit, who emits it, what happens next.

**story-tiers.md:**

| Tier | Fields | Auto-Detection | Coverage | Plan Gate | Test Gate | Code Gate |
|------|--------|----------------|----------|-----------|-----------|-----------|
| Trivial | 3 (title, description, files) — minimum viable story | Hotfix, or user explicitly chooses | hotfix_coverage_threshold (70%) | Skip | Quick | Quick |
| Small | 5 (title, description, scope, acceptance_criteria, files) | points <= 2, risk low, 1 file | 80% | Skip | Quick | Quick |
| Medium | 10 (+ interfaces, io_examples, error_handling, test_specs, invariants) | Default | 90% | Yes | Yes | Yes |
| Large | 15+ (+ failure_modes, edge_cases, feature_flags, concurrency, resource_safety) | points >= 8, risk high, security scope | 95% | Yes (thorough) | Yes (thorough) | Yes (thorough) |

**quality-dimensions.md (13 dimensions A-M):**

| Dim | Name | What It Covers |
|-----|------|---------------|
| A | Contract & API | Interface contracts, input validation, backward compatibility |
| B | Failure Modes | Error handling, recovery, degradation paths |
| C | Data Integrity | Validation, consistency, migration safety |
| D | Concurrency | Thread safety, race conditions, deadlock prevention |
| E | Security | Auth, injection, secrets, input sanitization |
| F | Observability | Logging, metrics, tracing, alerting |
| G | Performance | Complexity, resource usage, caching, batching |
| H | Maintainability | SRP, naming, complexity, coupling |
| I | Testing | Coverage, behavior-focus, isolation, edge cases |
| J | Deployment | Rollback safety, feature flags, config management |
| K | Configuration | Environment handling, secrets management, validation |
| L | Dependencies | Version pinning, vulnerability scanning, import validity |
| M | Compatibility | Cross-platform, backward compat, migration paths |

Each dimension includes 2-3 key checks (not exhaustive — details live in shaktra-quality skill).

## Validation

- [ ] `grep -r "P0.*Critical" skills/` returns results ONLY in `shaktra-reference/severity-taxonomy.md`
- [ ] All files under 300 lines
- [ ] No overlap between files (each has a distinct, non-overlapping purpose)
- [ ] Guard tokens list is exactly 15
- [ ] Story tiers match the 4-tier model from architecture

## Forge Reference

| Forge Source | What to Port | What to Change |
|-------------|-------------|----------------|
| 6 files defining P0-P3 | Severity definitions | Consolidate into ONE file |
| forge-reference skill (6 files) | Guard tokens | Reduce from 40+ to 15 |
| world-class-standard.md (31 principles) | Quality principles | Distill to 10 |
| quality-standards.md rule | 14 dimensions | Trim to 13, brief descriptions only |
| story-schema.md (1060 lines) | Tier definitions | Reduce to ~70 lines with 4 tiers |
