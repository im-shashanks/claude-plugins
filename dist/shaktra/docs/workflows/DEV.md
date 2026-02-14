# Dev Workflow (`/shaktra:dev`)

The Dev workflow is a TDD state machine that takes a user story from plan to production-ready code. It orchestrates 5 specialized agents through strict phase gates, ensuring every line of code is planned, tested first, implemented to pass those tests, quality-reviewed, and captured in project memory.

## State Machine

```
PLAN  -->  BRANCH  -->  RED  -->  GREEN  -->  QUALITY  -->  MEMORY  -->  COMPLETE
  |                      |          |            |
  v                      v          v            v
[Quality Loop]    [Quality Loop] [Quality Loop] [Quality Loop]
```

Each arrow is a **guarded transition** -- the pipeline cannot advance until the current phase's exit conditions are met. If a gate blocks, the responsible agent fixes findings and the gate is re-evaluated (up to 3 attempts before escalating to the user).

## Pre-Flight Checks

Before entering the state machine, three checks must pass:

| Check | What It Verifies | Failure Action |
|---|---|---|
| Language Config | `settings.yml` has `language`, `test_framework`, `coverage_tool` | "Run `/shaktra:init`" |
| Story Dependencies | All `blocked_by` stories have status `done` | "Complete blocking stories first" |
| Story Quality Guard | Story has required fields for its detected tier | "Run `/shaktra:tpm enrich`" |

All three must pass. Any failure stops the pipeline before work begins.

## Phase Walkthrough

### PLAN

**Agent:** SW Engineer (Opus) | **Output:** `implementation_plan.md` + `handoff.plan_summary`

The SW Engineer reads the story, project settings, prior decisions, and lessons learned. It designs the component structure, maps every acceptance criterion to planned tests, identifies failure modes, orders implementation by dependency (least-coupled first), and documents scope-specific risks with prevention strategies.

**Quality gate (Medium+ tiers):** SW Quality runs a Plan Review focusing on 5 checks (PL-01 through PL-05) that ask: "What would bite us in production?" If the plan has gaps in AC-to-test mapping, missing error handling plans, or unidentified failure modes, it blocks until fixed.

**Exit conditions:**
- `plan_summary` is populated in the handoff
- `test_plan.test_count > 0` (at least one test is planned)
- Trivial tier: this guard is relaxed (plan is minimal)

### BRANCH

**Agent:** Developer (Opus) | **Output:** Feature branch

After the plan passes, the Developer creates a Git branch following the naming convention derived from the story scope:
- `feat/<story-description>` for features
- `fix/<story-description>` for bugfixes
- `chore/<story-description>` for configuration/maintenance

No code is committed at this stage -- branch creation only.

### RED (Write Failing Tests)

**Agent:** Test Agent (Opus) | **Output:** Test files where all tests fail for valid reasons

The Test Agent reads the approved plan and writes tests that will define the implementation contract. Every acceptance criterion gets at least one test. Every error code gets a negative test. Tests are written to fail -- but for the *right* reasons.

**Valid failure reasons** (expected in RED state):
- `ImportError` -- module not yet created
- `AttributeError` -- class/method not yet defined
- `NotImplementedError` -- placeholder raises

**Invalid failure reasons** (Test Agent must fix before proceeding):
- `SyntaxError` -- broken test code
- `TypeError` -- wrong argument types in test setup
- `NameError` -- undefined variables in test

**Quality gate:** SW Quality runs Quick-Check on test files (13 checks, TQ-01 through TQ-13) verifying error path coverage, no mock-only assertions, test isolation, behavioral assertions, and descriptive naming.

**Exit conditions:**
- `test_summary.all_tests_red == true`
- All tests fail for valid reasons only
- Trivial tier: RED is skipped entirely (no tests required before code)

**Guard token:** If the test suite unexpectedly passes (no failures), `TESTS_NOT_RED` is emitted and GREEN is blocked. Tests must fail before implementation begins.

### GREEN (Implement Code)

**Agent:** Developer (Opus) | **Output:** Production code passing all tests + coverage met

The Developer reads the plan, the handoff context, and the failing tests, then implements code following the plan's `implementation_order` exactly. After each component, relevant tests are run to verify incremental progress. The Developer never modifies test files -- the tests are the spec.

Implementation follows coding practices: single responsibility, dependency injection, early returns, explicit error handling with context, input validation at boundaries, timeouts on external calls, no hardcoded credentials.

**Coverage check:** After all tests pass, coverage is measured against the tier-specific threshold (see Coverage Thresholds below). If coverage falls short, the Developer adds implementation to cover untested paths.

**Quality gate:** SW Quality runs Quick-Check on code files (18 checks, CQ-01 through CQ-18) verifying no hallucinated imports, input validation, timeouts, no placeholder logic, proper error handling, and code structure.

**Exit conditions:**
- `code_summary.all_tests_green == true`
- `code_summary.coverage >= tier_threshold`

**Guard tokens:**
- `TESTS_NOT_GREEN` -- tests still failing after implementation, Developer must fix
- `COVERAGE_GATE_FAILED` -- coverage below threshold, Developer must add coverage

### QUALITY (Comprehensive Review)

**Agent:** SW Quality (Sonnet) | **Output:** `QUALITY_PASS` or `QUALITY_BLOCKED`

The final quality gate runs a comprehensive review across 14 dimensions (A-M from quality dimensions plus N: Plan Adherence). SW Quality independently executes the test suite (not trusting self-reported results), verifies coverage, checks cross-story consistency against `decisions.yml`, and consolidates important decisions for promotion.

**Tier behavior:**
- Trivial/Small: QUALITY phase is **skipped entirely**. The Code gate is the final gate.
- Medium: Standard comprehensive review (14 dimensions).
- Large: Comprehensive + expanded review (architecture governance, performance profiling, dependency audit).

**What blocks at this gate:**
- Any P0 finding (zero tolerance)
- P1 count exceeding `settings.quality.p1_threshold`
- Unresolved findings from earlier gates that recur
- Missing plan components or unmitigated scope risks (Dimension N)

**Exit conditions:**
- `QUALITY_PASS` emitted after all dimensions reviewed
- Developer fixes any `QUALITY_BLOCKED` findings (up to 3 iterations)

### MEMORY (Capture Lessons)

**Agent:** Memory Curator (Haiku) | **Output:** Lessons appended to `lessons.yml`

The Memory Curator reads the entire workflow artifact trail -- handoff decisions, quality findings, patterns discovered, risks encountered -- and evaluates each against the capture bar: "Would this materially change future workflow execution?"

Only actionable, generalizable insights are written to `.shaktra/memory/lessons.yml`. Story-specific details are not captured. After capture, `memory_captured: true` is set in the handoff and the phase transitions to COMPLETE.

Memory capture is **mandatory for every tier** -- it is never skipped, even for Trivial stories.

## Coverage Thresholds by Tier

Coverage thresholds are read from `.shaktra/settings.yml` (never hardcoded). Default values:

| Tier | Setting Key | Default |
|---|---|---|
| Trivial (XS) | `tdd.hotfix_coverage_threshold` | 70% |
| Small (S) | `tdd.small_coverage_threshold` | 80% |
| Medium (M) | `tdd.coverage_threshold` | 90% |
| Large (L) | `tdd.large_coverage_threshold` | 95% |

The Developer checks coverage after GREEN. SW Quality independently verifies during QUALITY. Both read from the same settings key for the story's detected tier.

## The 36 Quality Checks

All 36 checks are loaded regardless of tier. What changes is how findings are treated:

**Quick depth (Trivial/Small):** P2+ findings are reported as observations, not blockers.
**Full depth (Medium):** Standard severity enforcement at every gate.
**Thorough depth (Large):** Full enforcement plus expanded architecture and dependency analysis.

### Plan Gate -- 5 Checks (Medium+ Only)

| ID | Check | Severity |
|---|---|---|
| PL-01 | AC-to-test plan mapping -- every AC has a planned test | P1 |
| PL-02 | Error handling test plans -- every error code has a planned test | P1 |
| PL-03 | Failure mode analysis -- plan identifies relevant failure scenarios | P1 |
| PL-04 | Scope-specific risks -- concrete risks with mitigation strategies | P2 |
| PL-05 | Implementation order -- dependency-minimizing build sequence | P2 |

### Test Gate -- 13 Checks

| ID | Check | Severity |
|---|---|---|
| TQ-01 | Error path coverage -- every error code tested | P0 |
| TQ-02 | No mock-only assertions -- tests assert behavior, not wiring | P1 |
| TQ-03 | No over-mocking -- mock count < real assertion count | P1 |
| TQ-04 | Test isolation -- no shared mutable state between tests | P1 |
| TQ-05 | No flickering tests -- no real time, random, or non-deterministic ops | P1 |
| TQ-06 | No empty assertions -- every test has a meaningful assertion | P1 |
| TQ-07 | Mock at boundaries only -- never mock internal project code | P1 |
| TQ-08 | Invariant coverage -- business rules tested both positively and negatively | P1 |
| TQ-09 | Happy path coverage -- `io_examples` from story have matching tests | P1 |
| TQ-10 | Specific exception assertions -- no bare `Exception` catches | P2 |
| TQ-11 | Behavior over structure -- tests survive internal refactoring | P2 |
| TQ-12 | Negative test ratio -- at least 30% negative tests | P2 |
| TQ-13 | Descriptive test names -- given/when/then or behavior-based naming | P2 |

### Code Gate -- 18 Checks

| ID | Check | Severity |
|---|---|---|
| CQ-01 | Hallucinated imports -- all imports resolve to real modules | P0 |
| CQ-02 | Missing input validation -- user input validated before use | P0 |
| CQ-03 | External calls have timeouts -- every network call has explicit timeout | P0 |
| CQ-04 | No hardcoded credentials -- no secrets in source code | P0 |
| CQ-05 | Bounded user input -- no unbounded loops/joins on external input | P0 |
| CQ-06 | Placeholder logic -- no TODO, FIXME, NotImplementedError in execution paths | P1 |
| CQ-07 | Generic error messages -- errors include context for debugging | P1 |
| CQ-08 | No exception swallowing -- every catch block re-raises, logs, or returns error | P1 |
| CQ-09 | Error classification -- retryable vs permanent errors distinguished | P1 |
| CQ-10 | Copy-paste errors -- no duplicated blocks with variable name mismatches | P1 |
| CQ-11 | Code duplication -- no significant duplication (>10% of changed code) | P1 |
| CQ-12 | Nesting depth -- no function exceeds 4 levels of nesting | P1 |
| CQ-13 | Cyclomatic complexity -- no function exceeds 10 branch points | P2 |
| CQ-14 | Generic naming -- no intent-free names like `process()` or `data` | P2 |
| CQ-15 | Magic numbers/strings -- literals in logic must be named constants | P2 |
| CQ-16 | Self-admitted tech debt -- no TODO/FIXME/HACK in production code | P2 |
| CQ-17 | God functions / SRP violations -- single responsibility per function | P2 |
| CQ-18 | Resource lifecycle -- acquired resources are properly released | P1 |

## The Quality Loop

Every gate uses the same fix loop pattern:

1. SW Quality reviews artifacts and emits `CHECK_PASSED` or `CHECK_BLOCKED`
2. If blocked: findings are sent to the responsible agent (SW Engineer, Test Agent, or Developer)
3. The agent fixes findings and re-submits
4. SW Quality re-reviews (with prior findings as context to check for regressions)
5. Up to **3 attempts** per gate
6. If still blocked after 3 attempts: `MAX_LOOPS_REACHED` -- escalated to user with all unresolved findings

## Resuming a Workflow

If a workflow is interrupted (user cancels, session ends), resume with `/shaktra:dev resume ST-001`. The handoff file tracks exactly where the pipeline stopped:

| `completed_phases` | Resumes At |
|---|---|
| `[]` | PLAN |
| `[plan]` | BRANCH (if no branch exists) or RED |
| `[plan, tests]` | GREEN |
| `[plan, tests, code]` | QUALITY |
| `[plan, tests, code, quality]` | MEMORY |

All prior state (plan summary, test summary, code summary) is preserved in the handoff -- no work is repeated.

## Agent Summary

| Phase | Agent | Model | Role |
|---|---|---|---|
| PLAN | SW Engineer | Opus | Creates implementation + test plan |
| BRANCH | Developer | Opus | Creates feature branch |
| RED | Test Agent | Opus | Writes failing tests |
| GREEN | Developer | Opus | Implements code to pass tests |
| QUALITY | SW Quality | Sonnet | Comprehensive quality review |
| MEMORY | Memory Curator | Haiku | Captures reusable lessons |
