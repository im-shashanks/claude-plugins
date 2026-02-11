# Forge Framework Analysis: Workflow & Process Flow

## Document Purpose

This document provides a comprehensive analysis of how work moves through the Forge framework -- from initial user request through planning, design, implementation, testing, quality review, and completion. It is intended to serve as the definitive reference for rebuilding the framework from scratch.

---

## Table of Contents

1. [End-to-End Workflow](#1-end-to-end-workflow)
2. [Intent Routing](#2-intent-routing)
3. [Story-Driven Development](#3-story-driven-development)
4. [Orchestration Model](#4-orchestration-model)
5. [Phase Transitions](#5-phase-transitions)
6. [Dashboard & Visibility](#6-dashboard--visibility)
7. [Product Manager Role](#7-product-manager-role)
8. [Init & Bootstrap](#8-init--bootstrap)
9. [Workflow Variants](#9-workflow-variants)
10. [Pain Points & Critique](#10-pain-points--critique)
11. [Agile Alignment](#11-agile-alignment)

---

## 1. End-to-End Workflow

### 1.1 The Complete Lifecycle

The Forge framework defines a strict, sequential lifecycle for feature development. At the highest level, work flows through these macro-phases:

```
INIT --> ANALYZE* --> CREATE PRD* --> CREATE ARCHITECTURE* --> DESIGN --> PLAN --> DEVELOP (TDD) --> QUALITY --> DONE

* = Optional depending on project type (greenfield vs brownfield)
```

### 1.2 Detailed Flow (Greenfield Project)

```
User: "init"
    |
    v
[INIT] Create forge/ directory structure, settings.yml, project.yml, templates
    |
    v
User: "create PRD"
    |
    v
[PRD CREATION] PM agent asks structured questions or reads discovery doc
    |                --> Output: forge/docs/PRD.md
    v
User: "create architecture"
    |
    v
[ARCHITECTURE] PM reads PRD, asks tech questions
    |                --> Output: forge/docs/Architecture.md
    v
User: "design user-auth"
    |
    v
[DESIGN] Designer agent performs gap analysis on PRD/Architecture
    |   |
    |   +--> GAPS_FOUND? --> PM tries to answer from PRD --> escalate unknowns to user
    |   |                    --> resume designer with answers
    |   |
    |   +--> DESIGN_COMPLETE --> Checker validates (3 attempts max)
    |                            --> Create-Check-Fix loop
    |                            --> Output: forge/docs/designs/user-auth.md
    v
User: "plan stories for user-auth"
    |
    v
[PLAN] Planner agent reads design doc, derives stories
    |   |
    |   +--> PLANNING_COMPLETE --> Checker validates EACH story (3 attempts max)
    |                              --> PM performs story review (RICE prioritization)
    |                              --> Output: forge/stories/ST-001.yml ... ST-00N.yml
    |                              --> Output: forge/memory/pm_review.yml
    |                              --> Updated: forge/memory/project.yml (sprint assignments)
    v
User: "develop ST-001" (or "orchestrate ST-001" for full autonomous)
    |
    v
[PRE-TDD VALIDATION] Run validate_stories.py
    |   |
    |   +--> Errors? --> Ask user: auto-fix / manual fix / show details
    |                    --> Loop until validation passes
    v
[SCAFFOLD] Create file stubs, branches (feat/ST-001-slug)
    |
    v
[PLAN PHASE] Developer agent creates unified implementation + test plan
    |   |        --> Output: forge/.tmp/ST-001/implementation_plan.md
    |   |        --> Output: forge/.tmp/ST-001/handoff.yml (plan_summary)
    |   v
    |   [PLAN QUALITY GATE] (STANDARD/COMPLEX only, skip for SIMPLE)
    |        --> forge-checker validates plan (1 fix loop max)
    v
[TESTS PHASE (RED)] Developer writes failing tests
    |   |        --> All tests must FAIL (not pass)
    |   |        --> Lint + type checks on test files
    |   |        --> Output: handoff.yml updated with test_summary
    |   v
    |   [TEST QUALITY GATE] (never skip)
    |        --> forge-checker: behavioral assertions? coverage? anti-patterns?
    |        --> Fix loop: up to 3 attempts (developer fixes, re-check)
    |        --> P0 > 0 OR P1 > 2 --> BLOCKED
    v
[CODE PHASE (GREEN)] Developer implements minimal code to pass tests
    |   |        --> Coverage must meet threshold (SIMPLE: 80%, STANDARD: 90%, COMPLEX: 95%)
    |   |        --> All tests must PASS
    |   |        --> Lint + type + security checks
    |   |        --> Output: handoff.yml updated with code_summary
    |   v
    |   [CODE QUALITY GATE] (never skip)
    |        --> forge-checker: TECH_DEBT + AI_SLOP checks (parallel)
    |        --> Fix loop: up to 3 attempts
    |        --> P0 > 0 OR P1 > 2 --> BLOCKED
    v
[QUALITY REVIEW] Quality agent performs 14-dimension CCR review
    |        --> Output: quality report
    v
[PM UAT GENERATION] PM generates user acceptance test checklist
    |        --> Output: forge/quality/uat_checklist.yml
    |        --> Release recommendation: PROCEED / HOLD / CONDITIONAL
    v
[FINAL REVIEW] Principal Engineer review (5 dimensions)
    |        --> Architectural fit, production readiness, evolution, missed items, challenger
    |        --> Verdict: APPROVED / APPROVED_WITH_NOTES / NEEDS_WORK
    v
[DONE] Story complete. User handles commit, PR, merge.
```

### 1.3 Detailed Flow (Brownfield Project)

```
[INIT] --> [ANALYZE] (13-phase codebase analysis)
               |
               +--> Phase 0: AST-based static analysis (zero LLM tokens)
               |     Output: forge/.analysis/static.yml (dependency graph, call graph, types)
               |
               +--> Phases 1-11: Semantic LLM analysis
               |     Output: overview.yml, structure.yml, domain-model.yml, entry-points.yml,
               |             practices.yml, conventions.yml, tech-debt.yml, data-flows.yml,
               |             critical-paths.yml
               |
               +--> Phase 12: Pattern examples with canonical code snippets
                     Output: forge/.analysis/examples.yml

Then: DESIGN --> PLAN --> DEVELOP --> QUALITY (same as greenfield, but all agents
      consume analysis artifacts for pattern matching, naming conventions, etc.)
```

### 1.4 The Orchestration Complete Flow (Autonomous)

When the user issues `orchestrate ST-001` or `complete ST-001`, the entire TDD pipeline runs end-to-end:

```
validate --> scaffold --> plan --> [Plan Quality Gate*] --> tests (RED) --> [Test Quality Gate]
         --> code (GREEN) --> [Code Quality Gate] --> quality --> PM-UAT --> final-review

* Plan Quality Gate only for STANDARD/COMPLEX tier stories
```

Each phase is executed by spawning a sub-agent via the `Task` tool. After each sub-agent returns, the orchestrator reads `handoff.yml` to verify completion before proceeding.

---

## 2. Intent Routing

### 2.1 The Two-Layer Routing System

Forge uses a two-layer routing architecture:

**Layer 1: Auto-Router (Rule File)**
File: `.claude/rules/forge-auto-router.md`

This is a Claude Code rule that activates on every user message. It pattern-matches the user's natural language input against known Forge keywords and automatically invokes `/forge-workflow` without asking for confirmation.

**Decision tree:**
```
1. Does message contain ST-### pattern?
   --> YES: Route to /forge-workflow

2. Does message START with a trigger keyword?
   (init, analyze, design, plan, develop, scaffold, quality, review,
    orchestrate, complete, hotfix, rollback, validate, check, enrich,
    quick, create story, create stories, create PRD, create architecture)
   --> YES: Route to /forge-workflow

3. Does message contain "forge" + action word?
   --> YES: Route to /forge-workflow

4. Otherwise:
   --> Normal Claude response (no routing)
```

**Layer 2: Intent Classifier (Skill Orchestrator)**
File: `.claude/skills/forge-workflow/SKILL.md`

Once the auto-router sends the message to `/forge-workflow`, the orchestrator classifies the natural language into one of 22+ discrete intents:

| Intent | Example Triggers | Sub-Agent |
|--------|-----------------|-----------|
| `help` | "help", "what can you do" | (inline) |
| `init` | "initialize", "setup forge" | (inline) |
| `status` | "status", "dashboard", "where are we" | (inline) |
| `scope` | "show scopes", "list scopes" | (inline) |
| `learn` | "learn status", "learn analyze" | (inline / forge-learning-analyzer) |
| `create-prd` | "create PRD", "PRD for X" | forge-product-manager |
| `create-architecture` | "create architecture" | forge-product-manager |
| `analyze` | "analyze codebase" | forge-analyzer |
| `design` | "design user-auth" | forge-designer |
| `plan` | "create stories for X" | forge-planner --> forge-product-manager |
| `enrich` | "enrich story from: ..." | forge-planner |
| `quick` | "quick story for ..." | forge-planner |
| `validate` | "validate ST-001" | (inline - script) |
| `check` | "check ST-001", "check design X" | forge-checker |
| `scaffold` | "scaffold ST-001" | forge-developer |
| `develop` | "develop ST-001" | forge-developer |
| `develop-plan` | "plan tests for ST-001" | forge-developer |
| `develop-tests` | "write tests for ST-001" | forge-developer |
| `develop-code` | "implement code for ST-001" | forge-developer |
| `quality` | "review ST-001" | forge-quality --> forge-product-manager |
| `hotfix` | "hotfix: fix null pointer" | forge-developer |
| `rollback` | "rollback ST-001 to plan" | forge-developer |
| `orchestrate` | "complete ST-001", "auto ST-001" | forge-developer + forge-quality + forge-product-manager |
| `parallel` | "develop ST-001 ST-002 in parallel" | Multiple forge-developer |
| `merge` | "merge completed stories" | (inline) |

### 2.2 Classification Priority

When multiple patterns could match, the system follows this priority order:

1. **Exact command matches** (highest priority)
2. **Story ID presence** (`ST-###` pattern) -- assumes story-related operation
3. **Feature name presence** -- assumes design/plan operation
4. **Keyword matching** -- matches against intent keyword lists
5. **Default to `help`** (lowest priority)

### 2.3 Ambiguity Resolution

Defined in `intent-patterns.md`:

- **Story ID present, no other keywords** --> `develop`
- **Story ID + "review"/"quality"/"verify"** --> `quality`
- **Story ID + "plan tests"** --> `develop-plan`
- **Feature name present, no design doc exists** --> `design`
- **Feature name present, design doc exists** --> `plan`
- **Neither story ID nor feature name** --> check for analysis/status keywords, else `help`

### 2.4 Routing Critique

The auto-router is aggressive. Phrases like "review the PR" will trigger forge routing even when the user might mean a simple code review. The keyword-based approach has no awareness of conversational context. If you say "analyze this function" meaning "explain it to me," the auto-router will invoke the full 13-phase codebase analysis.

---

## 3. Story-Driven Development

### 3.1 The Story as Central Artifact

In Forge, the story YAML file (`forge/stories/ST-###.yml`) is the single source of truth that drives all downstream work. Stories are designed to contain "everything needed for 90-95% automated code generation."

### 3.2 Story Creation Pathways

There are five distinct ways a story can come into existence:

```
                    +-----------------------------+
                    |     STORY CREATION PATHS     |
                    +-----------------------------+
                              |
        +----------+----------+----------+----------+
        |          |          |          |          |
        v          v          v          v          v
    [DERIVE]   [ENRICH]  [QUICK]   [HOTFIX]  [RETROACTIVE]
    from       from NL    minimal   emergency  from commit
    design     input      SIMPLE    fix path   after-the-fact
    doc                   tier
```

**Path 1: Derive from Design Doc** (`plan` intent)
- Source: `forge/docs/designs/{feature}.md`
- Process: Planner reads all 18 design sections, maps to story fields
- Output: Multiple stories, each with exactly ONE scope, sprint-assigned
- Tier: Auto-detected (SIMPLE/STANDARD/COMPLEX)

**Path 2: Enrich from Natural Language** (`enrich` intent)
- Source: User description, external document, or interactive Q&A
- Process: Clarification questions to fill required fields
- Output: Single complete story with all fields populated
- Brownfield-aware: Uses analysis artifacts to infer scope, file paths, naming

**Path 3: Quick Story** (`quick` intent)
- Source: One-line description (e.g., "Fix typo in error message")
- Process: Auto-infers scope from keywords, file from entity names
- Output: SIMPLE tier story with 8 fields
- Guard: Rejects if description contains security/payment/auth keywords

**Path 4: Hotfix** (`hotfix` intent)
- Source: Emergency description
- Process: Skip story creation entirely, apply fix, run tests, commit
- Output: Code changes committed immediately
- Post-process: Generates retroactive story for audit trail

**Path 5: Retroactive Story** (created by hotfix path)
- Source: Git commit hash and metadata
- Process: Infers scope from commit subject keywords
- Output: SIMPLE tier story marked as "done" with `workflow: retroactive`
- Purpose: Audit compliance only

### 3.3 Story Schema (Tiered Complexity)

Stories use a tiered schema that matches ceremony to complexity:

**SIMPLE Tier (8 required fields):**
- Triggers: points <= 2 AND risk == low AND len(files) == 1
- Fields: id, title, description, scope, files, acceptance_criteria, tests, risk_assessment
- Coverage threshold: 80%

**STANDARD Tier (16 required fields):**
- Triggers: Default (not SIMPLE, not COMPLEX)
- Adds: interfaces, io_examples, error_handling, logging_rules, observability_rules, concurrency, invariants, metadata
- Minimum 3 acceptance criteria, 1+ io_examples
- Coverage threshold: 90%

**COMPLEX Tier (20+ required fields):**
- Triggers: points >= 8 OR risk == high OR scope includes security/integration
- Adds: failure_modes, determinism, resource_safety, edge_case_matrix, feature_flags (MANDATORY)
- Coverage threshold: 95%

### 3.4 Story Validation

Stories are validated at multiple points:

1. **Pre-TDD Validation Gate** (mandatory before any development):
   - Python script: `validate_stories.py`
   - Checks: tier detection, required fields per tier, single-scope rule, test reference integrity, feature flag requirements
   - On failure: user gets options (auto-fix / manual / details)

2. **Post-Plan Checker** (via forge-checker ARTIFACT mode):
   - Create-Check-Fix loop (3 attempts max)
   - Checks: completeness, cross-references, world-class principle compliance

3. **PM Story Review** (via forge-product-manager):
   - Requirement coverage (PRD --> stories mapping)
   - RICE prioritization
   - Sprint goal assignment

### 3.5 Key Story Fields and Their Role

```
STORY FILE (ST-###.yml)
|
+-- Identity: id, title, description, scope
|
+-- What to Build:
|   +-- interfaces.implements (new contracts)
|   +-- interfaces.uses (dependencies to inject)
|   +-- files (paths, actions: create/modify)
|   +-- implementation_hints (code patterns, library choices)
|
+-- How to Test:
|   +-- acceptance_criteria (Given/When/Then, min 3 for STANDARD+)
|   +-- io_examples (concrete input/output data)
|   +-- tests (unit/contract/integration specs with assertions)
|   +-- edge_case_matrix (10 categories, min 5 covered)
|
+-- Error Handling:
|   +-- error_handling (code, condition, http_status, message, log_level)
|
+-- Observability:
|   +-- logging_rules (events, levels, fields)
|   +-- observability_rules (metrics, logs, traces)
|
+-- World-Class Standard:
|   +-- failure_modes (per-dependency failure behavior + test name)
|   +-- invariants (business rules + enforcement + test name)
|   +-- concurrency (idempotency pattern + tests)
|   +-- determinism (injection points for time/random/IDs)
|   +-- resource_safety (timeouts, bounded resources)
|
+-- Metadata:
    +-- risk_assessment (level, notes, mitigations)
    +-- metadata (story_points, priority, dependencies, design_doc ref)
    +-- feature_flags (mandatory for COMPLEX)
```

### 3.6 Story Tracking

Story status is NOT tracked in the story file itself. Status lives in:
- `forge/memory/project.yml` -- sprint assignments, story status (planned/in_progress/done)
- `forge/.tmp/{story_id}/handoff.yml` -- TDD phase state (plan/tests/code/complete)

---

## 4. Orchestration Model

### 4.1 The Orchestrator Pattern

Forge uses a strict orchestrator pattern. The orchestrator (`forge-workflow` skill) coordinates but NEVER implements. It has explicit boundaries:

**Allowed (orchestrator tools):**
- `Read` -- ONLY `workflow.yml` and `handoff.yml` (to check phase/state)
- `Task` -- Spawn sub-agents
- `AskUserQuestion` -- Clarify requirements

**Forbidden (sub-agent territory):**
- `Read` -- Story YAML, implementation plans, test files, source code
- `Write` / `Edit` -- Any file
- `Bash` -- Running tests, scripts

### 4.2 Sub-Agent Architecture

```
                    ORCHESTRATOR (forge-workflow)
                    |
    +-------+-------+-------+-------+-------+-------+-------+
    |       |       |       |       |       |       |       |
    v       v       v       v       v       v       v       v
 forge-  forge-  forge-  forge-  forge-  forge-  forge-  forge-
analyzer designer planner developer quality checker product  learning-
                                                   manager  analyzer
```

Each sub-agent:
- Runs in its own context (via `Task` tool)
- Has its own skills preloaded
- Returns completion signals (e.g., `DESIGN_COMPLETE`, `PHASE_COMPLETE: tests`)
- Can return clarification requests (`GAPS_FOUND`, `CLARIFICATION_NEEDED`)

### 4.3 Sequential Orchestration (Single Story)

For a single story TDD flow, phases execute strictly sequentially. After each phase, the orchestrator:

1. Reads `handoff.yml` to verify the phase completed
2. Checks for `blocked: true`
3. Verifies phase-specific success criteria
4. Runs the required quality gate (if any)
5. Spawns the next sub-agent

```
orchestrator: Task(forge-developer, "scaffold ST-001")
    <-- "PHASE_COMPLETE: scaffold"
orchestrator: Read handoff.yml --> verify scaffold done
orchestrator: Task(forge-developer, "plan ST-001")
    <-- "PHASE_COMPLETE: plan"
orchestrator: Read handoff.yml --> verify plan_summary.test_count > 0
orchestrator: Task(forge-checker, "check ST-001 plan-quality")   [STANDARD/COMPLEX only]
    <-- "GATE_PASSED"
orchestrator: Task(forge-developer, "tests ST-001")
    <-- "PHASE_COMPLETE: tests"
orchestrator: Read handoff.yml --> verify test_summary.all_tests_red == true
orchestrator: Task(forge-checker, "check ST-001 test-quality")
    <-- "GATE_PASSED" / "GATE_BLOCKED"
    [if BLOCKED: fix loop up to 3 times]
orchestrator: Task(forge-developer, "code ST-001")
    <-- "PHASE_COMPLETE: code"
orchestrator: Read handoff.yml --> verify code_summary.all_tests_green == true
orchestrator: Task(forge-checker, "check ST-001 code-quality")
    <-- "GATE_PASSED" / "GATE_BLOCKED"
    [if BLOCKED: fix loop up to 3 times]
orchestrator: Task(forge-quality, "review ST-001")
    <-- "QUALITY_COMPLETE"
orchestrator: Task(forge-product-manager, "UAT for ST-001")
    <-- "UAT_CHECKLIST_COMPLETE"
orchestrator: (inline) final-review as Principal Engineer
    <-- APPROVED / APPROVED_WITH_NOTES / NEEDS_WORK
```

### 4.4 Parallel Orchestration (Multiple Stories)

File: `orchestrate-parallel.md`

Parallel execution uses git worktrees for TRUE filesystem isolation:

```
Phase 1: ANALYZE
    Spawn analyzer sub-agent to read all stories
    Detect conflicts:
      - BLOCKING: Same file, both CREATE --> cannot parallelize
      - SHARED: Same file, both MODIFY --> can parallelize (merge later)
    Detect dependencies (blocked_by fields)
    Output: Execution plan with groups

Phase 2: PROCESS
    Parse execution plan
    Handle blocking conflicts (ask user or auto-serialize with --force)
    Finalize execution groups

Phase 2.5: CREATE WORKTREES
    For each story: git worktree add .forge-worktrees/{story_id} -b feat/{story_id}-{slug}
    Each worktree = independent filesystem + branch
    Delegated to haiku model sub-agent (lightweight)

Phase 3: EXECUTE
    For parallel groups: spawn ALL story orchestrators in ONE message (multiple Task calls)
    For sequential groups: wait for dependencies, then spawn
    Each story runs full TDD in its own worktree

Phase 4: COLLECT RESULTS
    Check each Task result for STORY_COMPLETE or STORY_FAILED
    Verify quality gates in each worktree's handoff.yml

Phase 4.5: CLEANUP WORKTREES
    Remove worktrees for successful stories
    Retain worktrees for failed stories (for debugging)
    Delegated to haiku model sub-agent

Phase 5: FINAL REPORT
    Summary table with branch names, quality gate status, coverage
    Shared files that need merge attention
    Merge order suggestions
```

**Context management for parallel execution:**

| Component | Model | Context Usage |
|-----------|-------|---------------|
| Coordinator | default | ~5K tokens |
| Analyzer | default | ~15K tokens (reads all stories) |
| Worktree Setup | haiku | ~2K tokens (shell commands only) |
| Each Orchestrator | default | Independent context via Skill |
| Worktree Cleanup | haiku | ~2K tokens |

### 4.5 The Create-Check-Fix Loop

This is a recurring pattern used for designs and stories:

```python
def orchestrate_with_check(creator_agent, artifact_path, max_attempts=3):
    attempt = 0
    previous_gap_count = None

    while attempt < max_attempts:
        attempt += 1
        result = Task(forge-checker, f"Check: {artifact_path}")

        if result.verdict == "CHECK_PASSED":
            return SUCCESS

        if result.verdict == "CHECK_PASSED_WITH_WARNINGS":
            log_warnings(result.warnings)
            return SUCCESS

        gap_report = read_yaml(f"forge/.tmp/check/{artifact_id}/gap_report.yml")

        if gap_report.escalation.needed:
            return escalate_to_user(gap_report)

        if attempt > 1 and gap_report.summary.total_gaps >= previous_gap_count:
            return escalate_to_user(gap_report, reason="no_progress")

        previous_gap_count = gap_report.summary.total_gaps

        Task(creator_agent, f"Fix these gaps: {format_gaps(gap_report.gaps)}")

    return escalate_to_user(gap_report, reason="max_attempts")
```

**Termination conditions:**

| Condition | Action |
|-----------|--------|
| CHECK_PASSED | Proceed to next phase |
| CHECK_PASSED_WITH_WARNINGS | Proceed, log warnings |
| attempts >= 3 AND still_gaps | Escalate to user |
| gap_count_unchanged for 2 attempts | Escalate (creator can't fix) |
| requires_user_decision | Escalate immediately |

---

## 5. Phase Transitions

### 5.1 Handoff File as State Machine

The handoff file (`forge/.tmp/{story_id}/handoff.yml`) is the core state tracking mechanism for TDD phases. It acts as a state machine:

```
[START] --> plan --> plan_quality_gate* --> tests --> test_quality_gate
        --> code --> code_quality_gate --> complete

* plan_quality_gate only for STANDARD/COMPLEX (auto-skipped for SIMPLE)
```

### 5.2 Phase Advancement Checklists

Each phase transition has mandatory verification:

**plan --> tests:**
- `plan_summary.test_count` > 0
- `plan_summary.test_types` non-empty
- `plan_summary.edge_cases` has 2+ entries
- `plan_summary.components` has 1+ entry
- `implementation_plan.md` file exists

**tests --> test_quality_gate:**
- `test_summary.files` has 1+ entry
- `test_summary.all_tests_red` == true (tests fail without implementation)
- Test count reconciled with plan (10% variance threshold)

**test_quality_gate --> code:**
- Checker has run
- `test_quality_gate.verdict` is PASS or WARNING
- If BLOCKED: fix loop ran (up to 3 attempts)

**code --> code_quality_gate:**
- `code_summary.all_tests_green` == true
- `code_summary.test_coverage` >= threshold

**code_quality_gate --> complete:**
- Both TECH_DEBT and AI_SLOP checkers have run
- `code_quality_gate.verdict` is PASS or WARNING
- `important_decisions` is present

### 5.3 Mandatory Post-Completion Gates

The orchestrator enforces gates after sub-agent returns. Skipping any gate triggers `WORKFLOW_STEP_SKIPPED` guard token:

| Intent | Gate Required | Agent | Skip If |
|--------|---------------|-------|---------|
| `design` | ARTIFACT check (3 attempts max) | forge-checker | Never |
| `plan` | ARTIFACT check per story + PM review | forge-checker --> forge-product-manager | Never |
| `develop-plan` | PLAN_QUALITY check | forge-checker | SIMPLE tier |
| `develop-tests` | TEST_QUALITY check | forge-checker | Never |
| `develop-code` | CODE_QUALITY check | forge-checker | Never |
| `quality` | PM UAT generation | forge-product-manager | Never |

### 5.4 Handoff Data Flow

The handoff file accumulates data as phases complete:

```yaml
# After PLAN phase:
plan_summary:
  test_count: 8
  components: [{name, file, responsibility}]
  patterns_applied: [{pattern, principle, guidance}]
  scope_risks: [{risk, likelihood, prevention}]
  implementation_order: [file1, file2, ...]

# After TESTS phase (added to above):
test_summary:
  files: [{path, tests: [test_names]}]
  all_tests_red: true
  test_count: 8

# After CODE phase (added to above):
code_summary:
  files_created: [paths]
  files_modified: [paths]
  test_coverage: 94
  all_tests_green: true

# After quality gates (added at each gate):
plan_quality_gate: {verdict, attempts, findings_file}
test_quality_gate: {verdict, p0_count, p1_count, attempts}
code_quality_gate: {verdict, tech_debt_findings, ai_slop_findings, attempts}
```

### 5.5 Important Decisions as Cross-Story Memory

A unique handoff mechanism is the `important_decisions` field. Decisions made during any TDD phase (library choices, security patterns, API conventions) are captured in the handoff and then "promoted" to `forge/memory/important_decisions.yml` by the quality gate. Future stories load these decisions to maintain project-wide consistency.

### 5.6 Clarification Handling (Cross-Cutting)

All sub-agents can request clarification, creating a pause-resume flow:

```
Orchestrator: Task(forge-designer, "design user-auth")
    <-- "GAPS_FOUND: [question1, question2]"

Orchestrator: Task(forge-product-manager, "Answer: [question1, question2]")
    <-- "PM_ANSWER: [answer1]" + "PM_ESCALATE: [question2]"

Orchestrator: AskUserQuestion(question2)
    <-- user answer

Orchestrator: Task(forge-designer, resume=designer_agent_id, "Answers: [answer1, user_answer]")
    <-- "DESIGN_COMPLETE"
```

This is a three-tier resolution: (1) PM tries from existing docs, (2) unanswered questions go to user, (3) agent resumes with combined answers.

### 5.7 Rollback Mechanism

Stories support phase rollback:

- **code --> tests**: Clears `code_summary`, keeps test files, implementation files may need manual cleanup
- **tests --> plan**: Clears `test_summary`, deletes test files created for the story
- **plan --> (start over)**: Deletes handoff.yml and implementation_plan.md entirely

Rollbacks are logged in `rollback_history` (append-only) within the handoff file.

---

## 6. Dashboard & Visibility

### 6.1 Dashboard Data Sources

The dashboard (invoked via `/forge status`, `/forge dashboard`) aggregates from three sources:

1. **`forge/memory/project.yml`** -- Sprint planning, story index, velocity targets
2. **`forge/.tmp/*/handoff.yml`** -- Phase status for in-progress stories
3. **`forge/memory/important_decisions.yml`** -- Decision count

### 6.2 Dashboard Output Format

The dashboard renders a fixed-format display:

```
# Forge Dashboard: {project_name}
Generated: {timestamp}
Current Sprint: {N} of {total}

## Sprint {N} Progress
+-----------------------------------------------------+
| ################........................ XX% (N/M stories)
+-----------------------------------------------------+

## Stories
| Story  | Title           | Status         | Points | Phase | Sprint |
|--------|-----------------|----------------|--------|-------|--------|
| ST-001 | Project skeleton | Done           | 5      | complete | 1   |
| ST-002 | Email syntax     | In Progress    | 3      | code     | 1   |
| ST-003 | MX validation    | Planned        | 5      | -        | 2   |

## Velocity
| Metric         | Value    |
|----------------|----------|
| Sprint Capacity| 15 pts   |
| Completed      | 5 pts    |
| In Progress    | 3 pts    |
| Remaining      | 7 pts    |

## Quality Metrics
| Metric              | Value |
|---------------------|-------|
| Stories Approved     | 1/3   |
| Test Coverage (avg)  | 94%   |
| Decisions Captured   | 5     |

## Blockers
(list or "No blockers.")

## Recent Activity
| Time   | Event                          |
|--------|--------------------------------|
| 2h ago | ST-002 passed quality gate     |
| 4h ago | ST-003 entered code phase      |
```

### 6.3 Workflow State Tracking

Global workflow state is in `forge/.tmp/workflow.yml`:

```yaml
active_workflow:
  id: "WF-001"
  type: "feature_development"  # analyze | design | plan | develop | quality | parallel
  trigger:
    intent: "implement user authentication"
    parsed_as:
      category: "orchestrate"
      targets: ["ST-001"]
  phase:
    name: "develop"
    sub_phase: "code"
    target: "ST-001"
  progress:
    total_steps: 6
    completed_steps: 3
    current_step: "ST-001 code phase"
  sub_agents:
    - id: "SA-001"
      type: "forge-developer"
      status: "running"

history:
  - event: "workflow_started"
    timestamp: "..."
  - event: "phase_completed"
    phase: "design"
    ...
```

### 6.4 State Transitions (Workflow Level)

```
[NONE] --> [ACTIVE] --> [BLOCKED] --> [ACTIVE]
              |              |            |
              |              v            |
              |          [RESOLVED] ------+
              v
          [COMPLETED]
```

Phase transitions at the workflow level:
```
analyze --> design --> plan --> develop --> quality --> done
                                 |
                        +--------+--------+
                        |                 |
                   [sequential]     [parallel]
                        |                 |
                   plan->tests->code  [worktrees]
                                         |
                               +---------+---------+
                               |         |         |
                            ST-001    ST-002    ST-003
```

---

## 7. Product Manager Role

### 7.1 The PM Agent

File: `.claude/agents/forge-product-manager.md`

The PM agent is a `sonnet` model sub-agent with access to `Read`, `Write`, `Glob`, `Grep`, `Bash`, `AskUserQuestion` tools. It loads the `product-manager-toolkit` and `forge-reference` skills.

### 7.2 PM Touchpoints in the Workflow

The PM integrates at 6 specific workflow gates:

```
[create PRD] --> analyze --> design --> plan --> develop --> quality
     |               |         |        |         |          |
     v               v         v        v         v          v
+--------------------------------------------------------------------+
|                     PM TOUCHPOINTS                                   |
|                                                                      |
| 1. Create PRD      | User-initiated (interactive or from document)  |
| 2. Create Arch     | User-initiated (derives from PRD)              |
| 3. Design Review   | Automatic: answers GAPS_FOUND from PRD         |
| 4. Story Review    | Automatic: post-plan RICE + coverage check     |
| 5. Clarifications  | On-demand: answers developer questions          |
| 6. UAT/Release     | Automatic: post-quality UAT checklist           |
+--------------------------------------------------------------------+
```

### 7.3 PM Touchpoint Details

**Touchpoint 1: PRD Creation** (user-initiated)
- Interactive mode: 5 structured questions, then template choice (Standard/One-Page/Epic/Brief)
- From-document mode: Extract pain points, feature requests, JTBD from source file, ask for gaps
- Output: `forge/docs/PRD.md`

**Touchpoint 2: Architecture Creation** (user-initiated)
- Prerequisite: PRD must exist
- Reads PRD, asks tech stack questions, checks for brownfield analysis
- Output: `forge/docs/Architecture.md`

**Touchpoint 3: Design Clarifications** (automatic)
- Trigger: Designer returns `GAPS_FOUND`
- PM searches: PRD, Architecture, prior PM decisions, important_decisions.yml
- Can answer: Performance requirements, security requirements, scope questions, tech decisions
- Escalates to user: Novel architectural decisions, business trade-offs, cost/timeline trade-offs
- All answers logged to `forge/memory/pm_decisions.yml`

**Touchpoint 4: Story Review** (automatic, post-plan)
- Trigger: Planner returns `PLANNING_COMPLETE`
- Actions:
  - Requirements coverage check (PRD requirement --> story mapping)
  - RICE prioritization (Reach x Impact x Confidence / Effort)
  - Quick wins and big bets identification
  - Priority adjustment in story files
  - Sprint goal assignment
- Output: `forge/memory/pm_review.yml`, updated `project.yml`

**Touchpoint 5: Development Clarifications** (on-demand)
- Trigger: Developer returns `CLARIFICATION_NEEDED`
- Same search-and-answer pattern as Touchpoint 3
- Answers logged to `forge/memory/pm_decisions.yml`

**Touchpoint 6: UAT Generation** (automatic, post-quality)
- Trigger: Quality review completes
- Reads story acceptance criteria and quality report
- Generates: acceptance criteria test steps, edge case scenarios, error handling scenarios
- Assesses release readiness: P0 findings --> HOLD, P1 > 2 --> HOLD, otherwise PROCEED/CONDITIONAL
- Output: `forge/quality/uat_checklist.yml`

### 7.4 RICE Score Calculation

The PM maps story data to RICE components:

| Story Field | RICE Component | Mapping |
|-------------|----------------|---------|
| scope | Reach | integration=10000, security=8000, data=6000, validation=4000, other=2000 |
| risk_assessment.level | Impact (inverse) | low=massive(3x), medium=high(2x), high=medium(1x) |
| tier | Confidence | SIMPLE=100%, STANDARD=80%, COMPLEX=50% |
| metadata.story_points | Effort | 1-2=xs, 3=s, 5=m, 8=l, 10=xl |

### 7.5 PM Memory Files

| File | Purpose | Created By |
|------|---------|------------|
| `forge/docs/PRD.md` | Product requirements | create-prd |
| `forge/docs/Architecture.md` | Architecture decisions | create-architecture |
| `forge/memory/pm_review.yml` | Story alignment report | post-plan review |
| `forge/memory/pm_decisions.yml` | PM decision audit log | clarifications |
| `forge/quality/uat_checklist.yml` | UAT test cases | post-quality |

---

## 8. Init & Bootstrap

### 8.1 Initialization Process

File: `.claude/skills/forge-workflow/init.md`

The `init` command creates the workspace structure from framework templates:

**Step 1: Check prerequisites**
- If `forge/settings.yml` already has `project.name` set, ask before reinitializing

**Step 2: Gather project information**
- Project name (required)
- Architecture style (optional, from: hexagonal, layered, feature-based, mvc, clean, event-driven, auto)

**Step 3: Create directory structure**
```
forge/
  memory/           # Sprint tracking, decisions
    learning/       # Self-learning system
  stories/          # Story specifications
  docs/             # PRD, Architecture, designs
    designs/        # Design documents
  .analysis/        # Codebase analysis artifacts
  .tmp/             # Temporary handoff files
```

**Step 4: Copy templates from `.claude/templates/forge/`**
- `settings.yml.template` --> `forge/settings.yml`
- `memory/project.yml.template` --> `forge/memory/project.yml`
- `memory/important_decisions.yml.template` --> `forge/memory/important_decisions.yml`
- `memory/learning/README.md` --> `forge/memory/learning/README.md`
- `memory/learning/patterns.yml.template` --> `forge/memory/learning/patterns.yml`
- `memory/learning/pattern_performance.yml.template` --> `forge/memory/learning/pattern_performance.yml`

**Step 5: Update settings with project info**

**Step 6: Optional stub documents** (PRD.md, Architecture.md for greenfield)

**Step 7: Display success** with next-steps guidance (brownfield vs greenfield paths)

### 8.2 Post-Init: Greenfield Path
```
init --> create PRD --> create architecture --> design <feature> --> plan stories --> develop
```

### 8.3 Post-Init: Brownfield Path
```
init --> analyze (13-phase) --> design <feature> --> plan stories --> develop
```

### 8.4 Portability Model

The framework is portable via the `.claude/` directory:
- Copy `.claude/` to any project
- Run `/forge init` to create project-specific `forge/` workspace
- All framework templates, skills, and agents travel with `.claude/`

---

## 9. Workflow Variants

### 9.1 Full Feature Development (Default)

```
init --> [PRD] --> [Architecture] --> design --> plan --> orchestrate ST-001 --> done
```

This is the "gold standard" path with maximum ceremony and quality gates.

### 9.2 Individual Phase Execution

Users can run each phase independently:

```
/forge develop ST-001 plan      # Just the plan phase
/forge develop ST-001 tests     # Just the tests phase
/forge develop ST-001 code      # Just the code phase
/forge quality ST-001           # Just the quality review
```

Each has its own prerequisites (e.g., code phase requires tests to be RED).

### 9.3 Quick Story (Minimal Ceremony)

```
/forge quick "Fix typo in error message"
    --> Auto-infer scope, file, story ID
    --> Generate SIMPLE tier story (8 fields)
    --> User runs develop manually
```

Rejection criteria: Descriptions mentioning security, auth, payment, database migration, new API/endpoint are rejected with "Use `/forge enrich` instead."

### 9.4 Hotfix (Emergency Path)

```
/forge hotfix "Fix null pointer in payment handler"
    --> Skip story creation
    --> Apply fix directly
    --> Run tests (70% coverage threshold)
    --> Commit changes
    --> Auto-generate retroactive story for audit trail
```

### 9.5 Enrich (External Input)

```
/forge enrich "story from: Add rate limiting to all API endpoints"
    --> Detect input type (natural language / existing story / external doc / interactive)
    --> Clarification questions for missing fields
    --> Generate complete story
```

### 9.6 Parallel Development

```
/forge parallel: ST-001 ST-002 ST-003
    --> Analyze conflicts
    --> Create worktrees
    --> Run all stories simultaneously
    --> Collect results + cleanup
```

### 9.7 Skip Options in Orchestration

- `--skip-scaffold`: Start from plan (assumes files exist)
- `--skip-quality`: Stop after code phase
- `--skip-final-review`: Stop after quality phase

### 9.8 Rollback

```
/forge rollback ST-001 to plan
    --> Reset handoff to plan phase
    --> Clear downstream summaries
    --> Log in rollback_history
```

### 9.9 Design Doc Status Lifecycle

```
Draft --> APPROVED (when stories are created) --> IMPLEMENTED (when all stories done)
```

---

## 10. Pain Points & Critique

### 10.1 Over-Prescribed Workflow

The framework enforces an extremely rigid sequential workflow. Even a simple feature modification requires: design document (18 sections) --> story YAML (up to 20+ fields for COMPLEX) --> scaffold --> plan --> tests --> code --> quality --> UAT --> final review. This is a lot of ceremony for changes that might take 15 minutes to hand-code.

While the tier system (SIMPLE/STANDARD/COMPLEX) attempts to scale ceremony, even the SIMPLE tier requires 8 structured fields and goes through the full TDD pipeline.

### 10.2 Massive Context Requirements

The story schema is enormous. A COMPLEX tier story requires 20+ structured YAML sections including failure_modes, determinism, resource_safety, edge_case_matrix (10 categories), invariants, concurrency, and feature_flags. The design document has 18 sections. This represents thousands of tokens of context that must be loaded, parsed, and acted upon by every sub-agent.

The framework attempts to manage this with "context-efficient" sub-agent prompts, but the fundamental data volume is high.

### 10.3 Fragile State Management

State is distributed across multiple YAML files:
- `forge/.tmp/workflow.yml` (global workflow)
- `forge/.tmp/{story_id}/handoff.yml` (per-story TDD state)
- `forge/memory/project.yml` (sprint/story index)
- `forge/.tmp/check/{story_id}/` (checker findings)

There is no transactional integrity. If a phase completes but the handoff file fails to update, the system gets into an inconsistent state. The orchestrator has to read and verify handoff files after every sub-agent return, which is itself error-prone.

### 10.4 Quality Gate Fatigue

The number of mandatory quality gates is substantial:
1. Pre-TDD validation (story schema)
2. Plan quality gate (STANDARD/COMPLEX)
3. Test quality gate
4. Code quality gate (TECH_DEBT + AI_SLOP)
5. Quality review (14-dimension CCR)
6. PM UAT generation
7. Principal Engineer final review

Each gate can trigger fix loops (up to 3 attempts), meaning a single story could theoretically go through dozens of sub-agent invocations. This is thorough but potentially very slow and token-expensive.

### 10.5 Aggressive Auto-Routing

The auto-router pattern-matches common English words (e.g., "analyze", "design", "review", "plan") and automatically invokes Forge workflows. This can intercept legitimate non-Forge requests. There is no confirmation step. A user saying "review this function" gets routed to the full quality review pipeline.

### 10.6 The Orchestrator Boundary Problem

The orchestrator is explicitly forbidden from reading story files, implementation plans, or source code. This means it cannot make intelligent decisions about what sub-agent needs or whether a phase actually succeeded beyond checking a few handoff fields. It is flying blind, relying entirely on sub-agent self-reporting and a handful of YAML fields.

### 10.7 Missing Feedback Loops

- No mechanism for the user to say "this quality gate finding is a false positive, skip it"
- No way to mark a gate check as "accepted risk" and proceed
- The override option exists in escalation but is described as "NOT RECOMMENDED"
- No retrospective mechanism to feed back whether all this ceremony actually produced better code

### 10.8 Self-Learning System Complexity

The self-learning system (pattern analysis, event logging, auto-triggers) adds significant complexity:
- Events logged at 8+ workflow checkpoints
- Pattern queries before every sub-agent spawn
- Auto-trigger analysis after every workflow completion
- Pattern application with guidance injection into sub-agent prompts

This is ambitious but adds a lot of surface area for bugs and confusion. The pattern matching relies on Python scripts that need to be installed and functional.

### 10.9 Handoff File Bloat

The handoff schema (v1.3.0) is very large, encompassing:
- Identity and timestamps
- Plan summary (test planning + implementation planning)
- Plan quality gate results
- Test summary
- Test quality gate results
- Code summary
- Code quality gate results
- Generated artifacts
- Important decisions
- Verification tests
- Rollback history
- Error state

This single file becomes a kitchen-sink state container that grows monotonically through the workflow.

### 10.10 PM Integration Feels Bolted On

The PM agent was clearly added in v1.5.0 as an overlay on the existing workflow. It intercepts at workflow gates rather than being a first-class participant. The RICE prioritization maps story fields to RICE components using fairly arbitrary mappings (e.g., scope "integration" = reach 10000). The PM answers questions by searching PRD text, which is pattern-matching on markdown documents.

### 10.11 No Real-Time Collaboration

The clarification flow (GAPS_FOUND/CLARIFICATION_NEEDED --> PM tries --> user answers --> resume agent) is synchronous and blocking. There is no way for the user to observe the work in progress and provide feedback mid-phase. The user waits for the agent to finish (or fail), then gets involved.

### 10.12 Missing: Version Control Integration

While the framework mentions branch naming (`feat/ST-###-slug`) and creates worktrees for parallel execution, there is no built-in PR creation, code review integration, or CI/CD pipeline awareness. The workflow ends at "commit and create PR" as a manual step.

### 10.13 Missing: Iteration/Refinement Loop

There is no mechanism for "I looked at the implementation and want to change the approach." The only option is rollback (which destroys work) or creating a new story. Real development involves iteration within phases, not just sequential progression.

---

## 11. Agile Alignment

### 11.1 What Forge Gets Right About Agile

**Story-driven development:** Work is organized into user stories with acceptance criteria, story points, and sprint assignments. This is core agile.

**Iterative delivery in sprints:** Stories are assigned to sprints based on velocity targets and dependencies. Sprint goals have business value descriptions.

**Vertical slicing via scopes:** The single-scope rule forces stories to be narrow, which aligns with the agile principle of small, deliverable increments. Each scope (validation, data, integration, etc.) represents a vertical slice.

**Working software as the measure:** The TDD pipeline ensures that every story produces tested, running code before it is considered done.

**Prioritization:** RICE prioritization and the quick-wins vs big-bets analysis map to agile backlog grooming.

### 11.2 Where Forge Deviates from Agile

**Waterfall within the story:** While the overall process is iterative (sprint-based), within each story the workflow is strictly sequential: design --> plan --> develop --> quality. This is mini-waterfall. Agile prefers emergent design and iterative refinement.

**Big Upfront Design:** The 18-section design document and 20-field story schema represent significant upfront planning. Agile's principle of "just enough documentation" is not well served by requiring failure modes, determinism injection points, and edge case matrices across 10 categories before writing any code.

**Ceremony over responsiveness:** The framework optimizes for thoroughness and consistency at the expense of speed. An agile team responding to changing requirements would find the rigid phase gates (plan quality gate --> test quality gate --> code quality gate --> quality review --> UAT --> final review) to be impediments.

**No true continuous integration:** Stories are developed on feature branches with independent worktrees. There is no concept of trunk-based development or continuous integration. Merge happens after all quality gates pass, which could be hours or days later.

**Missing retrospective mechanism:** Agile's emphasis on inspect-and-adapt is not well supported. While the self-learning system attempts to capture patterns, there is no structured retrospective process or mechanism for the team to decide "we should skip the design doc for this type of work."

**Missing user feedback loop:** Agile emphasizes frequent user feedback. The PM generates a UAT checklist at the END of the process, but there is no mechanism for showing work-in-progress to stakeholders or incorporating user feedback during development.

**Over-specification of stories:** Agile stories are intentionally brief ("As a user, I want X so that Y") with details emerging through conversation. Forge stories are the opposite: they are exhaustive specifications with exact method signatures, error codes, test assertions, metrics definitions, and failure modes. This is more akin to detailed design specifications than agile user stories.

### 11.3 Forge's Actual Methodology

Forge is best described as **Spec-Driven TDD with Agile Trappings**. It uses agile terminology (sprints, stories, velocity) but the actual process is closer to:

1. Requirements specification (PRD)
2. Architectural design (Architecture doc)
3. Detailed design (18-section design document)
4. Story specification (detailed YAML with test cases pre-defined)
5. Test-driven implementation (strict RED-GREEN with quality gates)
6. Quality assurance (automated + PM review)

This is a disciplined, specification-first approach that uses AI agents to automate the tedious parts of the specification and implementation process. The agile elements (sprints, prioritization, iterative planning) provide the outer loop, but within each story the execution is highly prescribed and sequential.

### 11.4 The Fundamental Trade-Off

Forge makes a deliberate trade-off: **it sacrifices agility for consistency and quality in AI-generated code.** Without this level of specification, AI agents tend to produce inconsistent, under-tested, poorly structured code. The ceremony exists because the "developers" are AI agents that need explicit instructions rather than human developers who can exercise judgment.

This is a reasonable trade-off for AI-assisted development, but it means Forge should not be evaluated as a pure agile methodology. It is a framework for getting reliable output from AI coding agents, using agile-inspired project management as the organizational layer.

---

## Appendix A: File Map

### State Files (Runtime)

| File | Purpose | Created By | Read By |
|------|---------|------------|---------|
| `forge/.tmp/workflow.yml` | Global workflow state | Orchestrator | Orchestrator |
| `forge/.tmp/{story_id}/handoff.yml` | Per-story TDD state | Developer | Orchestrator, Developer, Checker |
| `forge/.tmp/{story_id}/implementation_plan.md` | Implementation blueprint | Developer (plan phase) | Developer (code phase) |
| `forge/.tmp/check/{id}/findings.yml` | Checker findings | Checker | Orchestrator |
| `forge/.tmp/check/{id}/gap_report.yml` | Checker gaps for fix loop | Checker | Orchestrator |

### Memory Files (Persistent)

| File | Purpose | Created By | Read By |
|------|---------|------------|---------|
| `forge/settings.yml` | Project configuration | Init | All agents |
| `forge/memory/project.yml` | Sprint tracking, story index | Init, Planner | Dashboard, All |
| `forge/memory/important_decisions.yml` | Cross-story decisions | Quality gate (promoted from handoff) | Developer, Planner |
| `forge/memory/pm_review.yml` | PM story alignment report | PM (post-plan) | User |
| `forge/memory/pm_decisions.yml` | PM decision audit log | PM (clarifications) | PM, Designer |
| `forge/memory/learning/patterns.yml` | Self-learning patterns | Pattern analyzer | Orchestrator |
| `forge/memory/learning/events.jsonl` | Workflow events log | Orchestrator (auto) | Pattern analyzer |

### Artifact Files (Output)

| File | Purpose | Created By |
|------|---------|------------|
| `forge/docs/PRD.md` | Product requirements | PM agent |
| `forge/docs/Architecture.md` | Architecture decisions | PM agent |
| `forge/docs/designs/{feature}.md` | Feature design doc | Designer agent |
| `forge/stories/ST-###.yml` | Story specifications | Planner agent |
| `forge/quality/uat_checklist.yml` | UAT test cases | PM agent (post-quality) |
| `forge/.analysis/*.yml` | Codebase analysis (brownfield) | Analyzer agent |

### Analysis Files (Brownfield Only)

| File | Content |
|------|---------|
| `forge/.analysis/static.yml` | AST-based dependency graph, call graph, type hierarchy |
| `forge/.analysis/examples.yml` | Canonical pattern implementations with code snippets |
| `forge/.analysis/overview.yml` | Tech stack, build commands |
| `forge/.analysis/structure.yml` | Layer organization, module summaries |
| `forge/.analysis/domain-model.yml` | Business entities, aggregates |
| `forge/.analysis/entry-points.yml` | APIs, events, scheduled jobs |
| `forge/.analysis/practices.yml` | Detected coding patterns |
| `forge/.analysis/conventions.yml` | Naming standards |
| `forge/.analysis/tech-debt.yml` | Known issues, complexity hotspots |
| `forge/.analysis/data-flows.yml` | Side effects, event chains |
| `forge/.analysis/critical-paths.yml` | Revenue/security/performance critical code |

---

## Appendix B: Guard Tokens

Guard tokens are sentinel values that halt workflow execution:

| Token | Trigger | Phase |
|-------|---------|-------|
| `WORKFLOW_STEP_SKIPPED` | Mandatory step skipped by orchestrator | Any |
| `TESTS_NOT_RED` | Tests pass before implementation | Tests |
| `TESTS_NOT_GREEN` | Tests still failing after implementation | Code |
| `COVERAGE_GATE_FAILED` | Coverage below tier threshold | Code |
| `PHASE_GATE_FAILED` | Phase exit checks failed | Any |
| `MISSING_DESIGN_DOC` | Design doc not found | Plan |
| `SCOPE_VIOLATION` | Story has multiple scopes | Plan, Develop |
| `SIZE_VIOLATION` | Story exceeds 10 points or 3 files | Plan |
| `FIX_STORY_SCHEMA` | Story missing required fields | Develop |
| `VALIDATION_FAILED` | File doesn't match story spec | Code |
| `BRANCH_MISSING` | Story branch not found after scaffold | Orchestrate |
| `ANALYSIS_INCOMPLETE` | Brownfield analysis not finished | Design |
| `DESIGN_INPUT_MISSING` | Neither analysis nor PRD+Arch exist | Design |
| `QUICK_MODE_REJECTED` | Quick story too complex | Quick |

---

## Appendix C: Completion Signals

Sub-agents return these signals to the orchestrator:

| Signal | Agent | Meaning |
|--------|-------|---------|
| `DESIGN_COMPLETE` | forge-designer | Design doc created |
| `GAPS_FOUND` | forge-designer | Questions need answers before design |
| `PLANNING_COMPLETE` | forge-planner | Stories created |
| `CLARIFICATION_NEEDED` | Any agent | Ambiguity encountered |
| `PHASE_COMPLETE: {phase}` | forge-developer | TDD phase done |
| `PHASE_FAILED: {reason}` | forge-developer | TDD phase failed |
| `DEVELOPMENT_COMPLETE` | forge-developer | Full TDD done |
| `QUALITY_COMPLETE` | forge-quality | Quality review done |
| `CHECK_PASSED` | forge-checker | Artifact passed validation |
| `CHECK_PASSED_WITH_WARNINGS` | forge-checker | Passed with notes |
| `CHECK_GAPS_FOUND` | forge-checker | Gaps found, fix needed |
| `GATE_PASSED` | forge-checker | Quality gate passed |
| `GATE_BLOCKED` | forge-checker | Quality gate blocked |
| `PRD_COMPLETE` | forge-product-manager | PRD created |
| `ARCHITECTURE_COMPLETE` | forge-product-manager | Architecture created |
| `PM_REVIEW_COMPLETE` | forge-product-manager | Story review done |
| `PM_ANSWER` | forge-product-manager | Clarification answered |
| `PM_ESCALATE` | forge-product-manager | Question needs user |
| `UAT_CHECKLIST_COMPLETE` | forge-product-manager | UAT generated |
| `PM_FAILED: {reason}` | forge-product-manager | PM workflow failed |
| `STORY_COMPLETE: {id}` | parallel orchestrator | Parallel story done |
| `STORY_FAILED: {id}` | parallel orchestrator | Parallel story failed |
| `FIX_COMPLETE` | forge-developer | Quality fix applied |
| `RETRY_SUCCESS: {phase}` | forge-developer | Retry succeeded |
| `RETRY_FAILED: {reason}` | forge-developer | Retry failed |
