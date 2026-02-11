# Forge Core Skills Analysis (Part 2): forge-quality, forge-reference, forge-tdd, forge-workflow, brainstorming, error-resolver, product-manager-toolkit, subagent-driven-development

---

## 1. forge-quality

### Purpose

Performs FAANG-level comprehensive code review (CCR) with 14 review dimensions (A-N), a P0-P3 severity taxonomy, and independent verification testing. This is the post-development quality gate -- it reviews code that has already passed TDD phases and automated checks (lint, type check, coverage). It also consolidates important decisions from TDD into project memory and marks design documents as IMPLEMENTED when all stories complete.

**Trigger**: Not user-invocable (`user-invocable: false`). Loaded by the orchestrator when the `quality` intent is detected or after the GREEN phase completes during orchestration.

### Sub-components

| File | Lines | Role |
|------|-------|------|
| `SKILL.md` | ~60 | Skill manifest. Defines the 14 review dimensions (A-N), P0-P3 severity taxonomy, merge gate logic, and output format. References quality-review.md and quality-workflow.md as sub-templates. |
| `quality-review.md` | 688 | The CCR guide. 7 parts: severity taxonomy with examples, Evidence Rule ("where is the proof?"), 14 review dimensions each with checklist + reviewer deliverable + template, edge-case matrix (10 categories), independent verification testing (min 5 tests), review anti-patterns, and output templates for small PR and full application. |
| `quality-workflow.md` | 950 | The execution workflow. Step 0: tool verification (pytest, coverage, ruff, mypy, bandit). Step 0b: coverage gate pre-CCR. Mode 1: 13-dimension code review. Mode 1b: independent verification testing. Mode 2: automated QA. Decision consolidation. Design doc completion check. |

### Invocation Flow

1. **Tool Verification** (Step 0): Check that pytest, coverage, ruff, mypy, bandit are installed. If missing, emit `TOOLS_MISSING` guard token.
2. **Coverage Gate** (Step 0b): Read threshold from `forge/settings.yml`. Run coverage. If below threshold, emit `COVERAGE_GATE_FAILED`. This is a pre-CCR gate -- no point reviewing code that lacks test coverage.
3. **CCR Execution** (Mode 1): Run the 14-dimension review. For each dimension, produce findings with severity, evidence, and fix guidance. Apply the Evidence Rule: every behavioral claim must be backed by a test, benchmark, or demonstration.
4. **Verification Testing** (Mode 1b): Write 5+ independent tests that the implementation author did not write. These test edge cases, boundary conditions, and cross-cutting concerns. Persist or discard each test based on whether it adds genuine value beyond existing coverage.
5. **Automated QA** (Mode 2): Run the full test suite, coverage, ruff (lint), mypy (type check), bandit (security). Collect all results.
6. **Decision Consolidation**: Promote `important_decisions` from the story's `handoff.yml` to `forge/memory/important_decisions.yml` for future reuse.
7. **Design Doc Completion Check**: If all stories derived from a design document are now `done`, update the design document status to `IMPLEMENTED`.
8. **Merge Gate**: Apply the gate logic: `if P0 > 0: BLOCKED; elif P1 > 2: BLOCKED; elif P1 > 0: WARNING; else: PASS`.

### Dependencies

- Requires tool chain: pytest, coverage, ruff, mypy, bandit
- Reads `forge/settings.yml` for coverage thresholds
- Reads `forge/.tmp/{story_id}/handoff.yml` for important decisions
- Writes verification tests to test files
- Updates `forge/memory/important_decisions.yml`
- Updates design documents at `forge/docs/designs/*.md`
- References `forge-reference/world-class-standard.md` for principles and dimensions

### Content Summary

The CCR review dimensions (A-N) are:

| Dim | Name | Focus |
|-----|------|-------|
| A | Contract Fidelity | Public API matches spec, type signatures correct |
| B | Failure Modes | Error paths handled, exceptions meaningful |
| C | Data Integrity | Validation, sanitization, boundary checks |
| D | Concurrency Safety | Race conditions, deadlocks, thread safety |
| E | Security | Input validation, injection, auth, secrets |
| F | Observability | Logging, metrics, tracing |
| G | Performance | Time complexity, memory, I/O patterns |
| H | Maintainability | Naming, structure, DRY, coupling |
| I | Testing Adequacy | Coverage, edge cases, mocking quality |
| J | Deploy Safety | Migrations, rollback, feature flags |
| K | Configuration | Hardcoded values, env handling |
| L | Dependencies | Version pinning, vulnerability |
| M | Compatibility | API versioning, backward compat |
| N | Plan Adherence | Implementation matches plan from story |

The Evidence Rule is a distinctive design choice:

> "A reviewer must ask: Where is the proof? ... Every finding of P0 or P1 severity MUST include evidence -- either a failing test, a reproducible scenario, or a code path trace."

The anti-patterns section lists 7 common review failures: Rubber-Stamp Review, Nit-Pick Only, Severity Inflation, Missing Context, Copy-Paste Findings, Tool-Only Review, and Review Without Running Code.

### Complexity Assessment

**Comprehensive but extremely heavy.** The 688-line review guide and 950-line workflow template total nearly 1,650 lines of instruction that an LLM must internalize. The 14 review dimensions are thorough but the per-dimension checklists (each with 3-5 items) mean the reviewer must consider ~60 individual checks. The verification testing requirement (5+ independent tests with persistence decisions) adds meaningful value but also significant execution time. The decision consolidation and design-doc completion check feel like they belong in the orchestrator rather than the quality skill -- they are workflow state management, not quality review.

---

## 2. forge-reference

### Purpose

Shared reference content loaded by other skills. Contains the canonical definitions for quality standards, guard tokens, scopes, decision schemas, and practice mappings. Not a skill in the traditional sense -- it is a library of shared constants and schemas.

**Trigger**: Not user-invocable (`user-invocable: false`). Never invoked directly. Files are referenced by other skills via relative paths or loaded by agents that need shared definitions.

### Sub-components

| File | Lines | Role |
|------|-------|------|
| `SKILL.md` | ~20 | Manifest. States this is shared reference content, not user-invocable. Lists sub-files. |
| `world-class-standard.md` | 224 | The foundational reference. 31 principles organized in 4 parts: Core Pillars (P1-P5), Developer Disciplines (P6-P20), Excellence Multipliers (P21-P28), Context-Dependent (P29-P31). Includes severity taxonomy, Evidence Rule, CCR dimensions A-M, edge-case matrix, developer checklist, and 10 testing principles. |
| `guard-tokens.md` | 117 | Complete guard token reference. 9 categories: Universal (3), Story (4), TDD Phase (5), Analysis (2), Design (3), Quality (3), Orchestration (4), Scaffold (3), Merge (4), Checker Loop (5). Each token has condition and resolution. |
| `scopes.md` | ~80 | 10 valid scopes (skeleton, validation, diff, data, response, integration, observability, coverage, perf, security) with purpose, typical artifacts, and selection guidelines. Single-scope rule enforcement. Scope-to-tier correlations. |
| `decisions-schema.md` | ~100 | Schema for `important_decisions.yml`. 14 allowed categories. Lifecycle: CAPTURE -> CONSOLIDATE -> APPLY -> SUPERSEDE. Validation rules for entries (required fields, value constraints). |
| `practices-index.yml` | ~120 | Practice definitions mapping practice files to sections and applicable scopes. 6 architecture types (hexagonal, layered, feature-based, mvc, clean, event-driven). Archetype-to-architecture defaults. Scope-to-practice mapping. |

### Invocation Flow

No invocation flow -- this is a passive reference library. Other skills read specific files as needed:
- `world-class-standard.md` is loaded by forge-quality, forge-check, forge-design, and forge-tdd
- `guard-tokens.md` is loaded by forge-workflow (intent handlers)
- `scopes.md` is loaded by forge-plan (story derivation)
- `decisions-schema.md` is loaded by forge-quality (consolidation) and forge-tdd (capture)
- `practices-index.yml` is loaded by forge-tdd (architecture selection) and forge-plan (scope mapping)

### Dependencies

- No upstream dependencies (pure reference material)
- Downstream: nearly every other forge skill references at least one file from forge-reference

### Content Summary

The `world-class-standard.md` is the philosophical core of Forge. The 31 principles form a hierarchy:

**Part 1 - Core Pillars (P1-P5)**: Correct (before fast), Failure-aware (expect and handle), Intrinsically testable, Observable (structured logging + metrics), Evolutionary (change is normal).

**Part 2 - Developer Disciplines (P6-P20)**: Single responsibility, State ownership, Invariant-driven, Contract-first, Separation of concerns, Deterministic paths, Resource safety, Concurrency strategy, Error strategy, DRY, Layer isolation, Minimal coupling, Explicit tradeoffs, Smallest viable solution, Incremental delivery.

**Part 3 - Excellence Multipliers (P21-P28)**: Composable, Discoverable, Self-documenting, Performance-aware, Operationally ready, Backward compatible, Security by default, Configuration over code.

**Part 4 - Context-Dependent (P29-P31)**: Feature flags for rollout, Idempotent operations, Graceful degradation.

The `practices-index.yml` provides actionable mappings from architecture types to specific practices, which is consumed during TDD planning to ensure generated code follows the detected or selected architecture.

### Complexity Assessment

**Well-scoped as a reference library.** The world-class-standard.md is ambitious in codifying 31 principles but each is stated concisely. The guard-tokens.md provides a single reference point for all error conditions across the system, which is valuable for consistency. The practices-index.yml is the most actionable file -- it directly maps to code generation decisions. The decisions-schema.md lifecycle (CAPTURE -> CONSOLIDATE -> APPLY -> SUPERSEDE) is well-designed for knowledge accumulation. The main risk is drift: if skills evolve their understanding of these references without updating the canonical files, inconsistencies will emerge.

---

## 3. forge-tdd

### Purpose

Implements the core Test-Driven Development workflow: PLAN -> TESTS (RED) -> CODE (GREEN). Manages the complete lifecycle from story analysis through implementation, including scaffolding, phase transitions, state persistence via handoff.yml, and emergency hotfix handling.

**Trigger**: Not user-invocable (`user-invocable: false`). Loaded by the orchestrator (forge-workflow) during the `develop` intent or specific sub-intents (`develop-plan`, `develop-tests`, `develop-code`).

### Sub-components

| File | Lines | Role |
|------|-------|------|
| `SKILL.md` | ~120 | Skill manifest. TDD workflow overview, coverage requirements per tier (SIMPLE 80%, STANDARD 90%, COMPLEX 95%, HOTFIX 70%), test framework detection (pytest, jest, vitest, go test, cargo test, rspec), guard tokens, and references to sub-templates. |
| `tdd-workflow.md` | 1142 | The primary execution template. Three phases: PLAN (story analysis, implementation planning, test planning), TESTS/RED (write failing tests, behavioral naming, enforced fields), CODE/GREEN (follow plan, pre-GREEN validation, architecture rules). Includes phase rollback support and important decisions capture. |
| `handoff-schema.md` | 468 | Complete handoff.yml schema v1.3.0. State machine for phase transitions (plan -> tests -> test_quality_gate -> code -> code_quality_gate -> complete). 14 validation rules. Phase advancement checklists. Sections: Identity, Timestamps, Plan Output, Plan Quality Gate, Tests Output, Test Quality Gate, Code Output, Code Quality Gate, Generated Artifacts, Important Decisions, Verification Tests, Rollback History, Error State. |
| `scaffold.md` | 428 | File stub generation from story specs. Steps: extract requirements, generate Protocol stubs, Implementation stubs, Test stubs, Timeout wrappers, Error codes. Branch setup with worktree-aware detection. |
| `hotfix.md` | ~150 | Emergency hotfix workflow with reduced ceremony. Critical path detection (auth, payment, security require --force). Fix -> Test guardrail -> Commit -> Retroactive story generation -> Project memory update. |

### Invocation Flow

**Full TDD flow** (via `tdd-workflow.md`):

1. **PLAN Phase**:
   - Read story YAML from `forge/stories/{story_id}.yml`
   - Read prior decisions from `forge/memory/important_decisions.yml`
   - For brownfield: load analysis artifacts (static.yml, examples.yml, conventions.yml)
   - Story analysis: extract requirements, scope, tier, acceptance criteria
   - Implementation planning: identify components, select patterns (P6-P20), assess scope risks, determine implementation order
   - Test planning: map acceptance criteria to test cases, plan edge cases from story's edge_case_matrix
   - Write plan to `handoff.yml` under `plan_phase_output`
   - **[Plan Quality Gate]**: Orchestrator runs forge-check plan-quality-checklist (STANDARD/COMPLEX only, max 1 fix loop)

2. **TESTS Phase (RED)**:
   - Write failing tests using Given-When-Then naming convention
   - Must cover: acceptance criteria, failure_modes, edge_case_matrix entries, invariants, concurrency scenarios
   - Enforced field tests: if the story has `failure_modes`, tests MUST exist for each mode. Same for `edge_case_matrix`, `invariants`, `concurrency`
   - Run tests -- they MUST FAIL (guard: `TESTS_NOT_RED`)
   - Record test output to `handoff.yml`
   - **[Test Quality Gate]**: Orchestrator runs forge-check test-quality-checklist (max 3 fix loops)

3. **CODE Phase (GREEN)**:
   - Follow the plan from PLAN phase (MANDATORY -- deviation is a finding)
   - Implement code to make all tests pass
   - Apply architecture rules (6 types: hexagonal, layered, feature-based, mvc, clean, event-driven)
   - Pre-GREEN validation: all tests green, coverage meets tier threshold, lint passes, types pass
   - Guard: `TESTS_NOT_GREEN` if tests still fail
   - Production readiness checklist: error handling, logging, configuration, resource cleanup
   - Record code output to `handoff.yml`
   - **[Code Quality Gate]**: Orchestrator runs forge-check tech-debt + ai-slop checklists (max 3 fix loops)

**Scaffold flow** (via `scaffold.md`):
1. Read story YAML
2. Detect or create feature branch (worktree-aware)
3. Generate file stubs: Protocol/Interface stubs with docstrings, Implementation class stubs, Test file stubs with test function signatures, Timeout wrappers for external calls, Error code enums
4. All stubs are empty/raise NotImplementedError -- implementation happens in CODE phase

**Hotfix flow** (via `hotfix.md`):
1. Check if fix targets critical path (auth, payment, security)
2. If critical path and no --force: ABORT
3. Implement fix with minimal test guardrail
4. Commit with `hotfix:` prefix
5. Generate retroactive SIMPLE story for audit trail
6. Update project memory

### Dependencies

- Reads story files from `forge/stories/`
- Reads `forge/memory/important_decisions.yml` and `forge/memory/project.yml`
- For brownfield: reads `forge/.analysis/` artifacts
- References `forge-reference/world-class-standard.md` (P6-P20 principles)
- References `forge-reference/practices-index.yml` (architecture selection)
- State managed via `forge/.tmp/{story_id}/handoff.yml`
- Quality gates delegated to forge-check via orchestrator
- Scaffold writes to source and test directories

### Content Summary

The `tdd-workflow.md` is the largest single file at 1,142 lines. Key structural elements:

**PLAN phase** includes a detailed implementation planning section that requires identifying:
- Components to create/modify with rationale
- Patterns from P6-P20 to apply, with specific mapping to story requirements
- Scope risks and mitigations
- Implementation order with dependency justification

**TESTS phase** enforces behavioral naming:
```
test_{given}_{when}_{then}
# Example: test_valid_email_when_submitted_then_returns_success
```

The enforced field test mapping is strict:
- Each `failure_modes` entry -> at least one test
- Each `edge_case_matrix` entry -> at least one test
- Each `invariants` entry -> at least one test
- Each `concurrency` scenario -> at least one test

**CODE phase** has a pre-GREEN validation checklist that must pass before declaring the phase complete:
1. All tests pass
2. Coverage meets tier threshold
3. Lint passes (ruff)
4. Type check passes (mypy)
5. No new warnings introduced

The `handoff-schema.md` defines a state machine with explicit transitions:
```
plan -> tests -> test_quality_gate -> code -> code_quality_gate -> complete
```

Each transition has validation rules (e.g., "Cannot enter `tests` unless `plan_phase_output.implementation_plan` exists"). The schema supports rollback with history tracking -- if a quality gate fails and requires re-doing a phase, the previous attempt's data is preserved in `rollback_history`.

### Complexity Assessment

**Core engine, appropriately detailed but monolithic.** The 1,142-line tdd-workflow.md is doing the work of three separate templates (one per phase) crammed into a single file. The enforced field testing is a strong design choice that ensures story specifications are not ignored during implementation. The handoff schema is well-designed as a state machine with explicit validation rules -- it prevents phase skipping and preserves rollback history. The scaffold template is practical but tightly coupled to Python patterns (Protocol stubs, type hints) despite the SKILL.md claiming multi-language support. The hotfix flow is a pragmatic escape hatch that maintains audit trails.

---

## 4. forge-workflow

### Purpose

The central orchestrator and the ONLY user-invocable forge skill. Receives natural language commands, classifies intents, delegates work to sub-agents, enforces quality gates, manages workflow state, and coordinates the entire SDLC lifecycle from analysis through merge. Also manages PM integration, self-learning, and parallel execution.

**Trigger**: User-invocable. Activated by `/forge` commands. Uses model: sonnet. Allowed tools: Read, Glob, Grep, Task, Write, Bash, AskUserQuestion.

### Sub-components

| File | Lines | Role |
|------|-------|------|
| `SKILL.md` | 1482 | The master orchestrator document. Intent classification (20+ intents), orchestrator boundaries ("coordinates only, never implements"), mandatory post-completion gates, pre-TDD validation gate, Create-Check-Fix loop pattern (max 3 attempts), PM integration, self-learning system (event logging, pattern discovery, auto-trigger analysis). |
| `intent-patterns.md` | ~100 | NLP classification patterns for 20+ intents with example phrases. Classification priority: exact command > story ID > feature name > keyword > default to help. Feature name slugification rules. |
| `intent-handlers.md` | 463 | Mandatory step-by-step handlers for: design, plan, analyze, develop, develop-plan, develop-tests, develop-code, quality. Each handler lists exact steps and sub-agent invocations. Guard token WORKFLOW_STEP_SKIPPED for skipped mandatory steps. Quick reference table for check loops and PM integration per intent. |
| `orchestrate.md` | 963 | Single story TDD orchestration v1.7.0. Workflow: scaffold -> plan -> [Plan Quality Gate] -> tests (RED) -> [Test Quality Gate] -> code (GREEN) -> [Code Quality Gate] -> quality -> final-review. Three quality gates with fix loops. Principal Engineer Review as final gate. Worktree support. |
| `orchestrate-parallel.md` | 562 | Parallel execution coordinator. 5 phases: Analyze -> Process conflicts -> Create worktrees -> Execute in parallel -> Report + Cleanup. Git worktree isolation. Conflict detection: blocking (both CREATE same file) vs shared (both MODIFY). Utility tasks use haiku model. |
| `dashboard.md` | ~80 | Dashboard template. Mandatory output: header, sprint progress bar (block characters), story status table, velocity metrics, quality metrics, blockers, recent activity. |
| `help.md` | 515 | Full help content for Forge v1.4.0/1.5.0. Workflow phases, complete command reference, quick start guides (greenfield, brownfield, quick fix, emergency hotfix). |
| `init.md` | ~120 | Project initialization. Check prerequisites, gather info (name, architecture), create directory structure, copy templates from `.claude/templates/forge/`, update settings, optional stub documents. |
| `pm-touchpoints.md` | 452 | Product Manager integration. 6 touchpoints: PRD creation, Architecture creation, Design clarifications, Story review (post-plan), Development clarifications, UAT generation (post-quality). RICE score calculation. UAT checklist format. Decision logging to `forge/memory/pm_decisions.yml`. |
| `workflow-schema.md` | ~60 | Workflow state at `forge/.tmp/workflow.yml`. Schema: active_workflow (id, type, trigger, phase, progress, sub_agents), blockers, history, parallel_state. State transitions: NONE -> ACTIVE -> BLOCKED/COMPLETED. |

### Invocation Flow

The SKILL.md defines a multi-stage processing pipeline:

**Step 1 - Intent Classification** (using intent-patterns.md):
1. Parse user input against 20+ intent patterns
2. Classification priority: exact command match > story ID detection > feature name detection > keyword matching > fallback to help
3. Map to canonical intent (e.g., "build the auth feature" -> `develop` intent with feature="auth")

**Step 2 - Intent Handler Execution** (using intent-handlers.md):
Each intent has a mandatory handler with explicit steps. Example for `develop` intent:
1. Find story file in `forge/stories/`
2. Check story status (must be `planned` or `in_progress`)
3. Load story and validate schema
4. Pre-TDD validation gate (auto-fix option for missing fields)
5. Delegate to forge-tdd via sub-agent
6. Run quality gate after completion
7. Update story status

**Step 3 - Quality Gates** (per orchestrate.md):
Three gates embedded in the TDD flow:
- Plan Quality Gate: After PLAN, before RED (STANDARD/COMPLEX only, max 1 fix loop)
- Test Quality Gate: After RED, before GREEN (max 3 fix loops)
- Code Quality Gate: After GREEN (max 3 fix loops)

**Step 4 - Create-Check-Fix Loop** (defined in SKILL.md):
A generic pattern used across the workflow:
1. Creator agent produces an artifact
2. Checker agent validates the artifact
3. If gaps found: creator fixes, checker re-validates (max 3 iterations)
4. If max iterations reached: escalate to user

**Step 5 - Post-Completion**:
The SKILL.md defines a mandatory post-completion gates table listing which intents require which follow-up actions (quality review, PM touchpoint, status update, etc.).

**Parallel Execution** (via orchestrate-parallel.md):
1. Analyzer sub-agent reads all story files, detects conflicts, builds execution plan
2. Process conflicts: blocking conflicts (both CREATE) need resolution, shared files (both MODIFY) are informational only
3. Create worktrees: `git worktree add .forge-worktrees/{story_id} -b feat/{story_id}-{slug}`
4. Execute: spawn sub-agents per story, each running in its own worktree
5. Report + Cleanup: remove successful worktrees, retain failed ones for debugging

### Dependencies

- Coordinates ALL other forge skills (forge-tdd, forge-quality, forge-check, forge-plan, forge-design, forge-analyze)
- Reads/writes `forge/.tmp/workflow.yml` for state
- Reads story files, design docs, analysis artifacts
- Uses Task tool for sub-agent delegation
- Uses AskUserQuestion for user interaction
- Uses Bash for git operations (worktrees, branches)
- PM integration reads/writes `forge/memory/pm_decisions.yml`
- Self-learning reads/writes `forge/memory/events.yml` and `forge/memory/patterns.yml`

### Content Summary

The SKILL.md at 1,482 lines is the largest file in the entire Forge framework. Key sections:

**Orchestrator Boundaries**: "The orchestrator coordinates but NEVER implements directly. It delegates to specialized agents (forge-tdd for development, forge-quality for review, forge-check for validation)."

**Self-Learning System**: Four components:
1. Event logging: record outcomes of each workflow execution
2. Pattern querying: search events for recurring patterns
3. Pattern application: use discovered patterns to improve future executions
4. Auto-trigger analysis: periodically analyze event logs for insights

**PM Integration**: Six touchpoints mapped to workflow phases:
1. PRD creation (pre-design)
2. Architecture creation (pre-design)
3. Design clarifications (during design gap analysis)
4. Story review (post-plan)
5. Development clarifications (during TDD)
6. UAT generation (post-quality)

The `orchestrate.md` (963 lines) adds a **Principal Engineer Review** as the final gate after all quality checks pass. This review evaluates 5 dimensions:
1. Architectural Fit: Does the implementation fit the broader system?
2. Production Readiness: Is it deployment-safe?
3. Evolution & Maintainability: Will this age well?
4. What Was Missed: Gaps not caught by automated checks
5. Challenger Mindset: Devil's advocate critique

The `pm-touchpoints.md` maps story fields to RICE scores:
- Reach: from story priority + scope breadth
- Impact: from acceptance criteria + affected components
- Confidence: from test coverage + design completeness
- Effort: from story points + tier

### Complexity Assessment

**The most complex component in the entire framework -- and dangerously so.** The 1,482-line SKILL.md alone exceeds the context capacity that an LLM can reliably follow in a single execution. Combined with the 963-line orchestrate.md, 562-line orchestrate-parallel.md, 463-line intent-handlers.md, and other files, forge-workflow totals approximately 4,200 lines of instructions. This creates several risks:

1. **Context window saturation**: An LLM processing all forge-workflow files would consume a significant portion of its context window before doing any actual work.
2. **Instruction following degradation**: With thousands of instructions, the probability of skipping or misinterpreting any single instruction increases.
3. **Responsibility overload**: forge-workflow handles intent classification, workflow state management, sub-agent coordination, quality gate enforcement, PM integration, self-learning, parallel execution, and dashboard reporting. This violates the framework's own P6 (Single Responsibility) principle.
4. **The Principal Engineer Review** in orchestrate.md is an LLM reviewing its own output using subjective criteria -- the "Challenger Mindset" dimension essentially asks the LLM to argue against itself, which is architecturally questionable.

---

## 5. brainstorming

### Purpose

User-invocable skill for collaborative design exploration through structured dialogue. Intended for use before any creative work (design, architecture decisions) to ensure requirements are well-understood and multiple approaches are considered.

**Trigger**: User-invocable. Activated by `/brainstorm` or similar commands.

### Sub-components

| File | Lines | Role |
|------|-------|------|
| `SKILL.md` | 233 | The complete skill definition. Process: load brownfield context -> understand idea (one question at a time) -> explore approaches (2-3 with tradeoffs) -> present design (200-300 word sections). Uses CLARIFICATION_NEEDED format with 7 categories. |

### Invocation Flow

1. **Context Loading**: If brownfield (analysis artifacts exist), load relevant context. If greenfield, proceed with user input only.
2. **Idea Understanding**: Ask ONE question at a time. Do not front-load multiple questions. Categories: requirements, behavior, scope, priority, technical, security, performance.
3. **Approach Exploration**: Present 2-3 distinct approaches with explicit tradeoffs. Each approach gets: description, pros, cons, and recommended scenarios.
4. **Design Presentation**: Write design in 200-300 word sections. Practical and actionable, not abstract.

### Dependencies

- Optionally reads `forge/.analysis/` artifacts for brownfield context
- Output feeds into forge-design or direct implementation
- No persistent state or file outputs

### Content Summary

The CLARIFICATION_NEEDED format structures questions:
```
CLARIFICATION_NEEDED
Category: {requirements|behavior|scope|priority|technical|security|performance}
Question: {specific question}
Context: {why this matters}
Default: {reasonable default if user skips}
```

The skill emphasizes conversational flow over form-filling: "Ask ONE question at a time. Wait for the answer before asking the next."

### Complexity Assessment

**Lightweight and well-scoped.** At 233 lines in a single file, this is one of the simplest skills. The one-question-at-a-time pattern is a good UX choice for conversational interaction. The 7 clarification categories provide structure without rigidity. The 200-300 word section limit for design presentation is a practical constraint that prevents verbose output. The main weakness is the vague integration point -- "before any creative work" does not specify when the orchestrator should suggest or invoke brainstorming.

---

## 6. error-resolver

### Purpose

Systematic error diagnosis and resolution skill. Classifies errors into 10 categories, applies structured debugging patterns, and maintains a replay system for reusing solutions to previously-seen errors.

**Trigger**: User-invocable. Activated when users report errors or stack traces.

### Sub-components

| File | Lines | Role |
|------|-------|------|
| `SKILL.md` | 327 | The complete skill definition. 5-step process (CLASSIFY -> PARSE -> MATCH -> ANALYZE -> RESOLVE), 10 error categories, replay system, 4 debugging patterns. |

### Invocation Flow

1. **CLASSIFY**: Categorize the error into one of 10 types: Syntax, Type, Reference, Runtime, Network, Permission, Dependency, Configuration, Database, Memory.
2. **PARSE**: Extract structured information: error message, stack trace, file/line, relevant code context.
3. **MATCH**: Check `.claude/error-solutions/` for previously-seen errors with matching signatures. If match found, apply known solution.
4. **ANALYZE**: If no match, apply debugging patterns: Binary Search (narrow the problem space), Minimal Reproduction (smallest failing case), Rubber Duck (explain the problem step by step), Git Bisect (find the commit that introduced the error).
5. **RESOLVE**: Implement the fix. Record the solution to `.claude/error-solutions/` for future replay.

### Dependencies

- Reads/writes `.claude/error-solutions/` for replay system
- No dependencies on other forge skills
- Standalone tool that works independently of the forge workflow

### Content Summary

The replay system is the distinctive feature. Solutions are stored with:
- Error signature (pattern that identifies this class of error)
- Root cause
- Fix applied
- Files modified
- Verification steps

This creates an accumulating knowledge base of error resolutions specific to the project.

The debugging patterns are ordered by cost:
1. Binary Search: cheapest, narrows problem space
2. Minimal Reproduction: medium cost, isolates the issue
3. Rubber Duck: free, often reveals the answer through explanation
4. Git Bisect: higher cost, useful when the error is a regression

### Complexity Assessment

**Practical and self-contained.** The 5-step process is clear and actionable. The replay system is a genuinely useful feature for projects with recurring error patterns. The 10 error categories are comprehensive for typical software development. The main limitation is that the MATCH step relies on pattern matching against stored signatures, which may miss similar-but-not-identical errors. At 327 lines in a single file, the complexity is appropriate for the scope.

---

## 7. product-manager-toolkit

### Purpose

Standalone PM toolkit providing RICE prioritization, customer interview analysis, PRD templates, and strategic frameworks. Distinct from the forge-workflow PM integration (pm-touchpoints.md) -- this is a set of independent tools rather than workflow-embedded touchpoints.

**Trigger**: User-invocable. Activated by PM-related commands.

### Sub-components

| File | Lines | Role |
|------|-------|------|
| `SKILL.md` | 352 | Complete skill definition. References two Python scripts (rice_prioritizer.py, customer_interview_analyzer.py), 4 PRD templates (Standard, One-Page, Agile Epic, Feature Brief), and 5 strategic frameworks (RICE, Value vs Effort Matrix, MoSCoW, North Star Metric, Funnel Analysis). |

### Invocation Flow

**RICE Prioritization**:
1. Input: list of features/stories with estimated Reach, Impact, Confidence, Effort
2. Calculate RICE score: (Reach * Impact * Confidence) / Effort
3. Generate prioritized backlog
4. Optional: portfolio analysis (category distribution), roadmap generation

**Customer Interview Analysis**:
1. Input: interview transcripts or notes
2. NLP-based insight extraction: pain points, feature requests, satisfaction drivers
3. Pattern clustering across multiple interviews
4. Output: structured insights with confidence levels

**PRD Templates**:
- Standard: full-featured PRD for significant initiatives
- One-Page: lightweight for small features
- Agile Epic: epic-level specification
- Feature Brief: single-feature detailed specification

### Dependencies

- References Python scripts: `rice_prioritizer.py`, `customer_interview_analyzer.py`
- No dependencies on other forge skills
- Standalone toolkit

### Content Summary

The RICE framework application maps well to forge story fields:
- Reach: how many users affected (maps to story priority)
- Impact: degree of effect per user (maps to acceptance criteria scope)
- Confidence: certainty of estimates (maps to story tier -- COMPLEX = lower confidence)
- Effort: development cost (maps to story points)

The 5 strategic frameworks provide different lenses:
- RICE: quantitative prioritization
- Value vs Effort Matrix: 2x2 quadrant visualization
- MoSCoW: categorical (Must/Should/Could/Won't)
- North Star Metric: alignment check against single key metric
- Funnel Analysis: conversion-focused prioritization

### Complexity Assessment

**Moderately scoped but disconnected.** The toolkit provides useful PM capabilities but feels disconnected from the core forge workflow. The Python scripts (rice_prioritizer.py, customer_interview_analyzer.py) are referenced but not included in the skill files -- their implementation quality is unknown. The overlap with pm-touchpoints.md in forge-workflow (which also calculates RICE scores from story fields) creates confusion about which PM tool to use when. The PRD templates add value for greenfield projects but are not referenced by forge-design, which expects PRD input but does not specify a template.

---

## 8. subagent-driven-development

### Purpose

Executes implementation plans using fresh sub-agents per task, with a two-stage review process (spec compliance then code quality). Designed for parallel task execution where each task gets an isolated agent context to prevent cross-contamination.

**Trigger**: User-invocable. Activated when an implementation plan exists and tasks need execution.

### Sub-components

| File | Lines | Role |
|------|-------|------|
| `SKILL.md` | 246 | Skill overview. Per-task flow: dispatch implementer -> spec review -> code quality review -> mark complete. Fresh agent per task. Two-stage review requirement. |
| `implementer-prompt.md` | ~150 | Template for implementer sub-agent. Includes: full task text, project context, TDD mandatory instruction, self-review checklist, evidence checklist. |
| `spec-reviewer-prompt.md` | ~120 | Template for spec compliance review sub-agent. Skeptical verification approach: "DO NOT trust the report." Line-by-line requirement comparison. Flags both missing features AND extra/unauthorized features. |
| `code-quality-reviewer-prompt.md` | ~130 | Template for code quality review sub-agent. Applies Evidence Rule. 6 review areas: evidence, code quality, testing quality, error handling, security, performance. P0-P3 severity classification. |

### Invocation Flow

For each task in the implementation plan:

1. **Dispatch Implementer**: Spawn a fresh sub-agent with the implementer prompt. The agent receives the full task specification, project context, and instructions to follow TDD. The agent implements the task and produces a completion report.

2. **Spec Review**: Spawn a fresh sub-agent with the spec reviewer prompt. This agent receives the task specification AND the implementer's output. It performs line-by-line verification:
   - Does the implementation satisfy every requirement?
   - Are there unauthorized additions (scope creep)?
   - Does the test coverage match the specified scenarios?

3. **Code Quality Review**: Spawn a fresh sub-agent with the code quality reviewer prompt. This agent reviews the actual code:
   - Evidence Rule: are behavioral claims backed by tests?
   - Code quality: naming, structure, patterns
   - Testing quality: coverage, edge cases, isolation
   - Error handling, security, performance

4. **Decision Gate**: If both reviews pass, mark task complete. If either review fails, loop back to implementer with feedback.

### Dependencies

- Requires an implementation plan (from brainstorming or forge-plan)
- Integrates with: brainstorming (plan creation), forge-plan (story specs), forge-quality (quality standards), forge-tdd (TDD methodology)
- Uses Task tool for sub-agent spawning
- Fresh agent per task prevents context pollution

### Content Summary

The spec reviewer prompt is notably adversarial:

> "DO NOT trust the report. The implementer may claim completion without actually meeting all requirements. Verify EVERY claim against the actual code."

The two-stage review ensures orthogonal coverage:
- Stage 1 (spec compliance): Did you build the right thing?
- Stage 2 (code quality): Did you build the thing right?

The implementer prompt includes a self-review checklist that the implementer must complete before declaring done:
- All acceptance criteria met
- All tests passing
- No hardcoded values
- Error handling complete
- Logging present

The code quality reviewer uses the same P0-P3 severity taxonomy as forge-quality, ensuring consistency across review contexts.

### Complexity Assessment

**Well-designed separation of concerns.** The three-agent pattern (implementer + spec reviewer + code quality reviewer) is architecturally clean. Fresh agents per task prevent the context accumulation problem that plagues long-running development sessions. The adversarial spec reviewer is a strong design choice. The main concern is cost and latency -- every task requires three separate agent invocations, which triples the API cost and execution time. The relationship with forge-workflow's orchestrate.md (which also coordinates TDD execution with quality gates) is unclear -- these appear to be parallel approaches to the same problem.

---

## 9. Cross-Cutting Analysis

### forge-workflow as Central Orchestrator

forge-workflow is the hub of a hub-and-spoke architecture where all other forge skills are spokes:

```
                    User
                      |
                      v
              [forge-workflow]  <-- SKILL.md (intent classification)
               /    |    \     <-- intent-handlers.md (delegation)
              /     |     \    <-- orchestrate.md (TDD coordination)
             v      v      v
     forge-tdd  forge-quality  forge-check
        |           |             |
        v           v             v
  (implementation) (CCR review) (validation checklists)
        |
        v
  forge-reference (shared definitions)
```

The orchestrator enforces several critical boundaries:

1. **Never implements directly**: All code changes happen through forge-tdd
2. **Never reviews directly**: All quality reviews happen through forge-quality and forge-check
3. **Owns workflow state**: Only forge-workflow reads/writes workflow.yml
4. **Owns user interaction**: Only forge-workflow uses AskUserQuestion (except brainstorming)
5. **Owns PM integration**: PM touchpoints are embedded in the orchestrator, not in individual skills

The quality gate pattern is the primary control mechanism:
- Plan Quality Gate: forge-check's plan-quality-checklist (max 1 fix loop)
- Test Quality Gate: forge-check's test-quality-checklist (max 3 fix loops)
- Code Quality Gate: forge-check's tech-debt + ai-slop checklists (max 3 fix loops)
- CCR Gate: forge-quality's 14-dimension review (merge gate: P0>0 = BLOCKED)

This creates a layered defense:
- Layer 1: forge-tdd's built-in validation (tests pass, coverage meets threshold)
- Layer 2: forge-check's automated checklists (structural quality)
- Layer 3: forge-quality's CCR review (behavioral quality)
- Layer 4: orchestrate.md's Principal Engineer Review (architectural quality)

### Standalone vs Integrated Skills

The 8 skills in Part 2 fall into three categories:

**Deeply Integrated (core pipeline)**:
- `forge-tdd`: Implements the TDD phases. Cannot function without forge-workflow orchestration and forge-check validation.
- `forge-quality`: Performs post-development review. Requires handoff.yml from forge-tdd and is invoked by forge-workflow.
- `forge-reference`: Passive library consumed by all other forge skills. Defines the shared vocabulary.

**Loosely Integrated (workflow-aware but independent)**:
- `forge-workflow`: The hub. Integrates with everything but could theoretically be replaced with manual invocation of individual skills.
- `brainstorming`: Optionally invoked before design. Reads analysis artifacts if available but works without them.
- `product-manager-toolkit`: Provides PM capabilities that overlap with forge-workflow's pm-touchpoints but operates independently.

**Standalone (no forge dependencies)**:
- `error-resolver`: Completely independent. No references to forge stories, handoffs, or workflow state. Works on any project.
- `subagent-driven-development`: References forge concepts (TDD, P0-P3) but operates independently with its own orchestration pattern. Could replace forge-workflow's orchestrate.md for implementation tasks.

### Overall Skills Architecture Assessment

**Strengths**:

1. **Consistent quality taxonomy**: P0-P3 severity is used uniformly across forge-quality, forge-check, and subagent-driven-development. Guard tokens are centrally defined in forge-reference.

2. **Defense in depth**: Four layers of quality validation (TDD self-validation, check checklists, CCR review, PE review) catch different classes of issues at different stages.

3. **State machine discipline**: The handoff.yml schema in forge-tdd provides a well-defined state machine with explicit transitions and validation rules, preventing phase skipping.

4. **Escape hatches**: The hotfix flow and quick-story template acknowledge that not everything fits the full ceremony. The tier system (SIMPLE/STANDARD/COMPLEX) scales ceremony to risk.

5. **Knowledge accumulation**: The decisions lifecycle (CAPTURE -> CONSOLIDATE -> APPLY -> SUPERSEDE), error-resolver's replay system, and the self-learning system all build project-specific knowledge over time.

**Weaknesses**:

1. **Instruction volume**: The 8 skills in Part 2 total approximately 7,500 lines of markdown instructions. Combined with Part 1's skills, the full forge framework likely exceeds 12,000 lines. This is far more than any LLM can reliably follow in a single context window.

2. **Duplicate orchestration patterns**: forge-workflow's orchestrate.md and subagent-driven-development both coordinate task execution with quality gates. The relationship between them is undefined -- when should each be used?

3. **Duplicate quality review**: forge-quality's CCR (14 dimensions), forge-check's checklists (tech-debt + ai-slop), orchestrate.md's Principal Engineer Review, and subagent-driven-development's code-quality-reviewer all review code quality with overlapping criteria.

4. **PM tool confusion**: product-manager-toolkit provides RICE scoring and PRD templates. forge-workflow's pm-touchpoints.md also calculates RICE scores. The relationship and division of responsibility is unclear.

5. **Python bias**: forge-tdd's scaffold.md generates Python-specific stubs (Protocol, type hints, pytest fixtures) despite claiming multi-language support. The quality tools (ruff, mypy, bandit, pytest) are all Python-specific.

6. **Circular quality concerns**: The Principal Engineer Review asks an LLM to critically evaluate its own output (or another LLM's output) using subjective criteria like "Challenger Mindset." This is architecturally questionable -- LLMs tend to validate rather than challenge their own reasoning patterns.

### Overlap with Part 1 Skills

The Part 2 skills interact with and overlap with Part 1 skills (forge-analyze, forge-check, forge-design, forge-plan) in several ways:

| Overlap Area | Part 1 Skill | Part 2 Skill | Nature |
|---|---|---|---|
| **Quality validation** | forge-check (6 checklists, 150+ checks) | forge-quality (14 CCR dimensions, ~60 checks) | Complementary but overlapping. forge-check runs during TDD (gates), forge-quality runs after TDD (review). Both use P0-P3 severity. Some checks overlap: error handling is evaluated by forge-check's tech-debt-checklist AND forge-quality's dimension B (Failure Modes). |
| **Story validation** | forge-check (story-checklist, 47 checks) | forge-tdd (handoff schema validation, 14 rules) | Complementary. forge-check validates story YAML structure pre-TDD. forge-tdd validates story content is implementable during PLAN phase. |
| **Plan quality** | forge-check (plan-quality-checklist, 13 checks) | forge-tdd (PLAN phase output requirements) | Sequential. forge-tdd generates the plan, forge-check validates it. But the validation criteria in forge-check overlap with the generation criteria in forge-tdd -- both reference P6-P20 principles. |
| **Design validation** | forge-check (design-checklist, 35 checks) | forge-workflow (pre-TDD validation gate) | Sequential. forge-check validates the design document structure. forge-workflow validates the story derived from the design meets pre-TDD requirements. |
| **Brownfield context loading** | forge-analyze (generates artifacts), forge-design (loads artifacts), forge-plan (loads artifacts) | forge-tdd (loads static.yml, examples.yml, conventions.yml) | Pipeline. forge-analyze produces, all others consume. The artifact-loading pattern is duplicated in every consumer. |
| **Edge case matrix** | forge-check (validates), forge-design (defines), forge-plan (story schema) | forge-tdd (enforces tests per entry), forge-quality (reviews coverage) | Full pipeline. The 10-category matrix flows from design through stories to implementation to review, validated at each stage. |
| **Scope definitions** | forge-plan (uses scopes for story derivation) | forge-reference (canonical scope definitions), forge-tdd (scope-aware planning) | forge-reference is canonical, forge-plan and forge-tdd both consume. |
| **Guard tokens** | forge-check (defines some), forge-analyze (defines some), forge-design (defines some), forge-plan (defines some) | forge-reference (canonical list), forge-workflow (enforces all) | forge-reference centralizes definitions, forge-workflow enforces them, individual skills emit them. Some guard tokens are defined in individual skills that are not listed in forge-reference's canonical list. |
| **PM integration** | forge-plan (story review touchpoint) | forge-workflow (6 PM touchpoints), product-manager-toolkit (standalone RICE + PRD) | Three layers of PM integration with unclear boundaries. forge-workflow's pm-touchpoints is the most integrated. product-manager-toolkit is standalone. forge-plan's story review is embedded in the plan handler. |

**Key Architectural Observation**: The Part 1 skills (forge-analyze, forge-check, forge-design, forge-plan) represent the "what to build" pipeline (analysis -> design -> plan -> validation). The Part 2 skills (forge-tdd, forge-quality, forge-workflow) represent the "how to build it" pipeline (orchestration -> implementation -> review). forge-reference bridges both pipelines with shared definitions. The standalone skills (brainstorming, error-resolver, product-manager-toolkit, subagent-driven-development) are utility tools that augment but do not participate in either pipeline.

---

## 10. Summary Statistics

| Skill | Files | Total Lines (approx) | User-Invocable | Category |
|-------|-------|---------------------|----------------|----------|
| forge-quality | 3 | 1,700 | No | Core pipeline |
| forge-reference | 6 | 660 | No | Shared library |
| forge-tdd | 5 | 2,300 | No | Core pipeline |
| forge-workflow | 10 | 4,200 | Yes | Central orchestrator |
| brainstorming | 1 | 233 | Yes | Utility |
| error-resolver | 1 | 327 | Yes | Utility (standalone) |
| product-manager-toolkit | 1 | 352 | Yes | Utility (standalone) |
| subagent-driven-development | 4 | 650 | Yes | Utility |
| **Total** | **31** | **~10,400** | -- | -- |

The forge-workflow skill alone accounts for approximately 40% of the total instruction volume in Part 2, reflecting its role as the central orchestrator but also highlighting its outsized complexity.
