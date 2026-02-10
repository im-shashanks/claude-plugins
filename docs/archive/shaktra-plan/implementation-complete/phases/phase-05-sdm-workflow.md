# Phase 5 — SDM Workflow & TDD Pipeline[COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) before starting.
> **Depends on:** Phase 2 (Reference System), Phase 3 (State Schemas)
> **Blocks:** Phase 11 (Workflow Router)
> **Critical path phase** — this is the backbone of code quality.

---

## Objective

Build the core development workflow: Software Development Manager orchestrating TDD. Covers: planning, test writing (RED), code implementation (GREEN), and quality gates at each transition.

## Deliverables — Skills

| File | Lines | Purpose |
|------|-------|---------|
| `skills/shaktra-dev/SKILL.md` | ~250 | SDM orchestrator — TDD pipeline dispatch |
| `skills/shaktra-dev/tdd-pipeline.md` | ~200 | Step-by-step TDD orchestration template |
| `skills/shaktra-tdd/SKILL.md` | ~100 | TDD knowledge manifest |
| `skills/shaktra-tdd/testing-practices.md` | ~200 | Test writing guide, behavioral testing, patterns |
| `skills/shaktra-tdd/coding-practices.md` | ~200 | Implementation guide, patterns, anti-patterns, security/observability/resilience essentials |
| `skills/shaktra-quality/SKILL.md` | ~100 | Quality engine manifest |
| `skills/shaktra-quality/quick-check.md` | ~200 | ~35 high-impact checks for TDD gates |
| `skills/shaktra-quality/comprehensive-review.md` | ~200 | Full 13-dimension (A-M) + Dimension N (plan adherence) review template |

## Deliverables — Agents

| File | Lines | Purpose |
|------|-------|---------|
| `agents/shaktra-sw-engineer.md` | ~100 | Unified planning (implementation + tests) |
| `agents/shaktra-test-agent.md` | ~100 | Test writing — RED phase |
| `agents/shaktra-developer.md` | ~100 | Code implementation — GREEN phase |
| `agents/shaktra-sw-quality.md` | ~80 | SW quality review per story |

## Workflow

```
User: /shaktra:dev "Develop story ST-001"

SDM Skill (main thread):
  1. Read .shaktra/settings.yml (coverage thresholds — NEVER hardcode)
  2. Read .shaktra/stories/ST-001.yml (story spec)
  3. Read .shaktra/.tmp/ST-001/handoff.yml (if exists — for resume)
  4. Read .shaktra/memory/decisions.yml (prior decisions)
  5. Read .shaktra/memory/lessons.yml (prior lessons)

  PRE-FLIGHT CHECKS (before any TDD work):

    Language config check:
    - Verify .shaktra/settings.yml has language, test_framework, coverage_tool set
    - If missing → prompt user: "Project language config not set. Run /shaktra:init
      or update .shaktra/settings.yml with language, test_framework, coverage_tool"
    - Do not proceed until language config is present

    Story dependency check:
    - If story has blocked_by field → check if blocking stories are complete
    - If dependencies unresolved → block with: "Story ST-001 is blocked by ST-000
      (status: in_progress). Complete blocking stories first."

    Story quality guard:
    - Auto-detect tier based on story complexity and scope
    - Check: does story have all tier-required fields?
    - If sparse (missing required fields for detected tier):
      → Block TDD pipeline
      → Report to user: "Story ST-001 is sparse (X of Y required fields for [tier] tier).
         Missing: test_specs, io_examples, error_handling, ...
         Run: /shaktra:tpm enrich ST-001"
      → Exit (do not proceed with incomplete story)
    - If Trivial tier → apply hotfix_coverage_threshold from settings
    - If sufficient → proceed

  5. Detect current phase from handoff (or start fresh)

  GUARD TOKEN ENFORCEMENT:
    The SDM orchestrator and sw-quality agent emit guard tokens from
    shaktra-reference/guard-tokens.md at phase transitions:
    - TESTS_NOT_RED — if test suite passes before implementation begins → block GREEN
    - TESTS_NOT_GREEN — if tests still failing after implementation → block QUALITY
    - COVERAGE_GATE_FAILED — if coverage below tier threshold → block QUALITY
    - PHASE_GATE_FAILED — if a phase transition guard fails → block next phase
    - CHECK_PASSED / CHECK_BLOCKED — after each quality gate
    - MAX_LOOPS_REACHED — if fix loop exhausted → escalate to user

  Phase: PLAN
    a. Spawn shaktra-sw-engineer → Implementation Plan + Test Plan (unified)
       - Engineer reads story, creates comprehensive plan
       - Output: implementation_plan.md + handoff.plan_summary
    b. If tier >= Medium:
       Spawn shaktra-sw-quality → Review Plan (max 3 loops)
       - Quality: "What would bite us in production?"
       - Focus: top 3-5 critical gaps, not laundry list
    c. Update handoff: completed_phases: [plan]

  BRANCH CREATION (after PLAN, before RED):
    - Spawn shaktra-developer → Create feature branch
      - Convention: feat/{story-description} | fix/{story-description} | chore/{story-description}
      - Derived from story scope and title
      - No commits — staging only throughout TDD pipeline
      - Commits and PRs are user-managed (never automated by framework)

  Phase: RED (Tests)
    a. Spawn shaktra-test-agent → Write Failing Tests
       - MUST use exact test names from story's test_specs
       - Tests must be behavioral (assert outcomes, not mock.called)
       - All tests must fail initially (RED state)
       - RED validation: Tests must fail for VALID reasons —
         ImportError, AttributeError, NotImplementedError (code doesn't exist yet).
         If tests fail for INVALID reasons (SyntaxError, TypeError, NameError in
         test file itself), the test is broken and must be fixed before proceeding.
         The test agent verifies failure reasons before reporting all_tests_red: true.
       - Update handoff: test_summary.all_tests_red = true
    b. Spawn shaktra-sw-quality → Review Tests (max 3 loops)
       - Check: behavioral assertions, error path coverage, no over-mocking
       - Gate: P0 > 0 OR P1 > threshold = BLOCKED
    c. Update handoff: completed_phases: [plan, tests]

  Phase: GREEN (Code)
    a. Spawn shaktra-developer → Implement Code
       - Follow implementation_order from plan
       - Apply patterns from plan_summary
       - Avoid scope_risks from plan
       - Make all tests pass, hit coverage threshold
       - Update handoff: code_summary.all_tests_green = true, coverage = X%
    b. Spawn shaktra-sw-quality → Review Code (max 3 loops)
       - Quick-check mode: ~35 checks, P0/P1 focus
       - Gate: P0 > 0 OR P1 > threshold = BLOCKED
    c. Update handoff: completed_phases: [plan, tests, code]

  Phase: QUALITY (Final)
    a. Spawn shaktra-sw-quality → Comprehensive Review
       - Full 13-dimension review (A-M) + Dimension N: Plan Adherence
       - Dimension N verifies implementation matches the plan:
         * Components built match plan_summary.components
         * Patterns applied as plan_summary.patterns_applied
         * Scope risks from plan_summary.scope_risks were mitigated
         * Deviations documented in code_summary with justification
         * Missing risk prevention → P0; Pattern not applied → P1; Component differs → P2
       - Verification: run actual tests, check coverage
       - Decision consolidation: promote important_decisions to decisions.yml
    b. Update handoff: completed_phases: [plan, tests, code, quality]

  MEMORY CAPTURE (mandatory final step — orchestrator must not skip):
    a. Spawn shaktra-memory-curator
       - Reads handoff.yml (decisions, findings, patterns applied, scope risks)
       - Reads code changes (diff summary from files_modified)
       - Reads quality findings from comprehensive review
       - Evaluates: "Would this materially change how a future workflow step executes?"
       - Writes actionable insights to .shaktra/memory/lessons.yml (if any clear the bar)
       - Note: decisions.yml already updated during QUALITY phase (decision consolidation)
    b. Update handoff: memory_captured = true, current_phase = complete

  6. Report completion summary to user
```

## Quality Engine Design (shaktra-quality skill)

Two modes, one engine — solving Forge's quadruple overlap:

**QUICK_CHECK (during TDD gates):**
- ~35 highest-impact checks organized by severity
- Always load ALL ~35 checks regardless of tier. Check depth controls REVIEW SCOPE, not check loading:
  - Quick (Trivial/Small): sw-quality runs quick-check only. All ~35 checks loaded, but P2+ findings are observations, not blockers.
  - Full (Medium): sw-quality runs quick-check at gates + comprehensive review at QUALITY phase.
  - Thorough (Large): Full + expanded comprehensive review with architecture impact analysis, performance profiling review, dependency audit.
- Max 3 fix loops per gate
- Focus areas by gate:
  - Plan gate: Architecture soundness, test strategy quality, missed edge cases
  - Test gate: Behavioral assertions, error path coverage, no over-mocking, test isolation
  - Code gate: Timeouts, credentials, exception handling, hallucinated imports, bounded operations

**COMPREHENSIVE REVIEW (final gate):**
- Full 13-dimension review (A-M from shaktra-reference)
- Coverage verification (actual test execution, not self-reported)
- Decision consolidation (extract decisions from development, promote to memory)
- Cross-story consistency check (does this fit with prior decisions?)

**Complete ~35 Checks by Gate:**

**Plan Gate (5 checks — Medium+ tiers only):**

| # | Check | Sev | Why |
|---|---|---|---|
| PL-01 | AC ↔ test plan mapping complete | P1 | Every acceptance criterion must have planned tests |
| PL-02 | Error handling codes all have test plans | P1 | LLMs skip error paths entirely if not planned |
| PL-03 | Failure mode analysis present (integration/security/data scope) | P1 | External call resilience, partial failure, concurrent access |
| PL-04 | Scope-specific risks identified | P2 | Integration: timeouts/retry; Security: validation/auth; Data: transactions |
| PL-05 | Implementation order minimizes coupling | P2 | Wrong order = cascading rework |

**Test Gate (13 checks):**

| # | Check | Sev | Why |
|---|---|---|---|
| TQ-01 | Error path coverage — all error codes from story have tests | P0 | LLMs skip error paths entirely |
| TQ-02 | No mock-only assertions (`mock.called` proves nothing) | P1 | Tests prove behavior, not wiring |
| TQ-03 | No over-mocking — mock count < real assertion count | P1 | 5+ mocks = testing nothing real |
| TQ-04 | Test isolation — no shared mutable state between tests | P1 | Shared state = flaky suites |
| TQ-05 | No flickering tests — no real `time`/`random`/`datetime.now()` | P1 | Non-deterministic = unreliable CI |
| TQ-06 | No empty assertions — every test has >= 1 meaningful assert | P1 | LLMs generate assertion-free tests frequently |
| TQ-07 | Mock at boundaries only — external APIs/DBs/filesystems, not internals | P1 | Internal mocks break on every refactor |
| TQ-08 | Invariant coverage — business invariants tested positive + negative | P1 | Invariants are the contract; untested = unverified |
| TQ-09 | Happy path coverage — AC scenarios from io_examples have tests | P1 | Core behavior must be tested, not just edges |
| TQ-10 | Specific exception assertions (not bare `pytest.raises(Exception)`) | P2 | Generic catches verify nothing useful |
| TQ-11 | Tests verify behavior, not structure (refactor-safe) | P2 | Tests coupling to internals break on any change |
| TQ-12 | Negative test ratio >= 30% of total | P2 | LLMs bias toward happy paths |
| TQ-13 | Descriptive test names (given/when/then or behavior-based) | P2 | Tests are documentation; names must convey intent |

**Code Gate (17 checks):**

| # | Check | Sev | Why |
|---|---|---|---|
| CQ-01 | Hallucinated imports — all imports exist in stdlib/deps/project | P0 | Code won't run |
| CQ-02 | Missing input validation — user input to queries/commands/eval | P0 | Injection vulnerability |
| CQ-03 | External calls have timeouts | P0 | Missing timeout = cascading production failure |
| CQ-04 | No hardcoded credentials/secrets | P0 | Security incident if shipped |
| CQ-05 | Bounded user input operations — no unbounded loops/joins on input | P0 | DoS via resource exhaustion |
| CQ-06 | Placeholder logic — TODO/NotImplementedError in execution paths | P1 | Incomplete code shipped as if complete |
| CQ-07 | Generic error messages — `raise Exception("Failed")` | P1 | Undebuggable in production |
| CQ-08 | No exception swallowing — `except: pass` hides real failures | P1 | Silent failures = corrupt state |
| CQ-09 | Error classification — retryable vs permanent distinguished | P1 | Without classification, no retry logic is possible |
| CQ-10 | Copy-paste errors — duplicated blocks with variable name mismatches | P1 | LLMs duplicate with subtle name bugs |
| CQ-11 | Code duplication > 10% — DRY violations | P1 | Duplicated logic = duplicated bugs |
| CQ-12 | Nesting depth > 4 levels | P1 | Deep nesting = untestable, unreadable code |
| CQ-13 | Cyclomatic complexity > 10 per function | P2 | High-branch functions are untestable |
| CQ-14 | Generic naming — `process()`, `handle()`, `data`, `result` | P2 | LLM defaults; reveals no intent |
| CQ-15 | Magic numbers/strings without named constants | P2 | Hardcoded values obscure meaning |
| CQ-16 | SATD — TODO/FIXME/HACK/"temporary"/"quick fix" in code | P2 | Self-admitted tech debt left in production |
| CQ-17 | God functions / SRP violations | P2 | If name contains "and", split it |

## Memory Curator Agent Usage

Shared across all main workflows. Agent file delivered in Phase 3; detailed usage here because SDM has the richest memory flow.

- **Capture bar:** "Would this materially change how a future workflow step executes?" Zero entries is valid.
- **Process:** Read handoff → Read existing lessons → Identify actionable, reusable, non-duplicate insights → Write to lessons.yml
- **Note:** Decisions captured separately by sw-quality during QUALITY phase. Memory curator focuses on *lessons* — gotchas, surprising behaviors, process insights.

## Validation

- [ ] Language config check blocks SDM if settings.yml missing language/test_framework
- [ ] Story dependency check blocks if blocked_by stories are incomplete
- [ ] Story quality guard catches sparse stories and blocks with actionable recommendation
- [ ] Developer creates feature branch after PLAN phase (feat/fix/chore convention)
- [ ] No automated commits — staging only
- [ ] Trivial tier stories use hotfix_coverage_threshold
- [ ] Full TDD cycle completes: plan → red (tests fail) → green (tests pass)
- [ ] Handoff state machine tracks phases correctly
- [ ] Phase resume works: stop mid-cycle, `/shaktra:dev "Resume ST-001"` continues from last phase
- [ ] Quality gates catch real issues (test with intentionally bad code)
- [ ] Coverage threshold enforcement from settings.yml (not hardcoded)
- [ ] Important decisions captured and persisted to decisions.yml
- [ ] Memory curator invoked as mandatory final step (memory_captured = true in handoff)
- [ ] Lessons.yml entries are actionable (insight + action, not just observations)
- [ ] Memory curator captures nothing for routine sessions (zero entries is valid)
- [ ] Fix loops cap at 3 per gate
- [ ] Gate activation varies by tier (Small skips plan gate) but all checks always loaded
- [ ] Guard tokens emitted at every phase transition
- [ ] RED phase validates failure reasons (valid vs invalid)
- [ ] Plan adherence (Dimension N) checked in comprehensive review
- [ ] Coding practices include security, observability, resilience sections
- [ ] Quick-check has exactly ~35 checks with IDs, severities, and gates
- [ ] AI Slop checks explicitly represented: CQ-01, CQ-06, CQ-14, CQ-16, CQ-17
- [ ] Tech Debt checks explicitly represented: CQ-03-05, CQ-08-12, CQ-13
- [ ] Maintainability checks explicitly represented: CQ-13-17, TQ-11-13
- [ ] No content duplication between quality skill and reference skill
- [ ] All files under 300 lines (check every file)

## Forge Reference

| Forge Source | What to Port | What to Change |
|-------------|-------------|----------------|
| forge-developer agent (205 lines) | TDD phase execution, settings consumption | Split into 3 agents (engineer, test, developer) |
| forge-checker agent (329 lines) | 4 checker modes | Merge into sw-quality with modes |
| forge-quality agent (163 lines) | 13-dim review | Comprehensive mode of unified quality |
| forge-tdd skill (1142 lines) | Handoff state machine, RED/GREEN phases | **Split into testing-practices + coding-practices** |
| forge-check skill (417 lines) | Test quality, tech debt, AI slop checklists | **Merge into quick-check.md (~35 checks)** |
| forge-quality skill (88 lines) | Severity taxonomy reference | Reference shaktra-reference, don't redefine |
