# Forge Agent System -- Comprehensive Analysis

**Analyzed from**: `/Users/shashank/workspace/applications/forge-claudify/.claude/agents/`
**Agent count**: 12 agent definition files
**Date**: 2026-02-05

---

## Table of Contents

1. [Agent Inventory](#1-agent-inventory)
2. [Agent Roles & Boundaries](#2-agent-roles--boundaries)
3. [Agent Relationships & Dependency Graph](#3-agent-relationships--dependency-graph)
4. [Orchestration Model](#4-orchestration-model)
5. [Agent Prompt Patterns](#5-agent-prompt-patterns)
6. [Language-Specific Agents](#6-language-specific-agents)
7. [Agent-to-Skill Mapping](#7-agent-to-skill-mapping)
8. [Overlap & Redundancy](#8-overlap--redundancy)
9. [Missing Agents](#9-missing-agents)
10. [Maintainability Assessment](#10-maintainability-assessment)

---

## 1. Agent Inventory

### 1.1 Complete Agent Listing

| # | Agent | Model | Tools | Skills | Hooks | Permission Mode |
|---|-------|-------|-------|--------|-------|-----------------|
| 1 | forge-analyzer | sonnet | Read, Glob, Grep, Bash | forge-analyze, forge-reference | None | default |
| 2 | forge-checker | sonnet | Read, Glob, Grep, Bash | forge-check, forge-reference | None | default |
| 3 | forge-designer | **opus** | Read, Write, Glob, Grep | forge-design, forge-reference | None | default |
| 4 | forge-developer | sonnet | Read, Write, Edit, Bash, Glob, Grep | forge-tdd, forge-reference | PreToolUse (Write/Edit validation) | default |
| 5 | forge-docs-updater | **haiku** | Read, Write, Grep | forge-reference | None | default |
| 6 | forge-learning-analyzer | sonnet | Read, Bash | forge-reference | None | default |
| 7 | forge-planner | sonnet | Read, Write, Glob, Grep | forge-plan, forge-reference | None | default |
| 8 | forge-product-manager | sonnet | Read, Write, Glob, Grep, Bash, **AskUserQuestion** | product-manager-toolkit, forge-reference | None | default |
| 9 | forge-quality | sonnet | Read, Write, Bash, Glob, Grep | forge-quality, forge-reference | **Stop** (check-p0-findings.py) | default |
| 10 | forge-test-engineer | sonnet | Read, Write, Edit, Bash | (none listed) | None | (not specified) |
| 11 | python-pro | sonnet | Read, Write, Edit, Bash | (none listed) | None | (not specified) |
| 12 | typescript-pro | sonnet | Read, Write, Edit, Bash | (none listed) | None | (not specified) |

**Notable model selections:**
- **forge-designer uses `opus`** -- the most expensive model. This is justified because design documents are the highest-leverage artifacts; a bad design cascades into bad stories, tests, and code.
- **forge-docs-updater uses `haiku`** -- the cheapest model. This makes sense because it performs simple YAML updates and does not require deep reasoning.
- All other agents use `sonnet` -- the middle tier, balancing cost and capability.

### 1.2 Individual Agent Details

#### Agent 1: forge-analyzer

**Purpose**: Comprehensive codebase analysis for brownfield projects.

**Responsibilities**:
- Execute 13-phase analysis (Phase 0: static/AST, Phases 1-11: semantic, Phase 12: examples)
- Run `static_analysis.py` for dependency graphs, call graphs, type hierarchies, pattern detection
- Analyze architecture, domain model, coding patterns, tech debt, critical paths
- Generate structured YAML outputs to `forge/.analysis/`

**When Invoked**: At the start of brownfield projects, triggered by "analyze" intent via the auto-router or orchestrator.

**Persona**: "Principal Engineer performing comprehensive codebase analysis"

**Completion Signals**: `ANALYSIS_COMPLETE`, `ANALYSIS_FAILED: {reason}`, `CLARIFICATION_NEEDED`

**Key Quote from definition**:
```
Analyze the existing codebase through 13 phases to understand:
- Architecture and structure
- Domain model and business logic
- Coding patterns and conventions
- Technical debt and complexity
- Critical paths and data flows
```

---

#### Agent 2: forge-checker

**Purpose**: Quality gatekeeper that runs at multiple checkpoints during TDD.

**Responsibilities**:
- **Mode 0 (PLAN_QUALITY)**: After PLAN phase, before RED -- validates plan comprehensiveness (STANDARD/COMPLEX only)
- **Mode 1 (TEST_QUALITY)**: After RED phase, before GREEN -- catches bad tests before implementation
- **Mode 2 (TECH_DEBT)**: After GREEN phase -- identifies reliability risks and maintenance burden
- **Mode 3 (AI_SLOP)**: After GREEN phase -- ensures senior-engineer quality (no hallucinated imports, generic names, over-commenting)
- **Mode 4 (ARTIFACT)**: Before TDD begins -- validates story/design artifacts meet schema requirements

**When Invoked**: At quality gates during the TDD orchestration workflow. Can run in parallel (TECH_DEBT + AI_SLOP run simultaneously).

**Persona**: "Principal Engineer performing independent quality review at FAANG-level standards"

**Critical Design Decision**: "You inspect and report; you NEVER modify artifacts" (read-only).

**Completion Signals**: `PASS`, `WARNING`, `BLOCKED`

**Key Quote**:
```
Bad tests lead to bad implementation. If tests assert on mock calls instead of
behavior, the implementation will be written to satisfy mocks, not real behavior.
```

---

#### Agent 3: forge-designer

**Purpose**: Creates comprehensive 18-section design documents.

**Responsibilities**:
- Gather context from PRD, Architecture docs, analysis artifacts, and memory
- Perform gap analysis (missing requirements, conflicts, edge cases, security, performance)
- Generate 18-section design documents covering contracts, error taxonomy, state machines, threat models, invariants, observability, test strategy, ADRs, data model, dependencies, failure modes, invariant enforcement, state ownership, concurrency, determinism, resource safety, edge case matrix, and tradeoffs

**When Invoked**: When user requests design creation ("design X"), before story planning.

**Persona**: "Principal Engineer creating world-class design documents"

**Completion Signals**: `DESIGN_COMPLETE`, `GAPS_FOUND`

**Notable**: Uses `opus` model -- the only agent that does. The 18-section template with "World-Class Sections (11-18)" including P2 through P18 pattern references suggests this is considered the most intellectually demanding task.

---

#### Agent 4: forge-developer

**Purpose**: TDD implementation engine -- the core code-producing agent.

**Responsibilities**:
- **PLAN phase**: Create implementation plan + test plan from story spec
- **TESTS phase (RED)**: Write failing tests matching story-defined test names exactly
- **CODE phase (GREEN)**: Implement to make tests pass, verify coverage
- **Scaffold mode**: Create stubs without implementation
- **Hotfix mode**: Reduced ceremony, skip plan phase, lower coverage threshold
- **Rollback mode**: Reset handoff to target phase, delete later artifacts
- Runs tests inline (no separate test agent needed for execution)

**When Invoked**: During TDD orchestration for each story. Also invoked by quality gate fix loops when checker finds issues.

**Persona**: "Senior Software Engineer (FAANG-calibre) implementing stories through TDD"

**Hooks**: PreToolUse hook on Write/Edit operations that runs `validate-story-alignment.sh` -- this ensures every file modification stays aligned with the story spec.

**Completion Signals**: `PHASE_COMPLETE: {phase}`, `PHASE_FAILED: {reason}`, `CLARIFICATION_NEEDED`

**Guard Tokens**: `TESTS_NOT_RED`, `TESTS_NOT_GREEN`, `COVERAGE_GATE_FAILED`, `MISSING_STORY_TEST`

**Key Quote**:
```
CRITICAL: Use exact test names from story
Story defines tests.unit[].function_name -> use those EXACT names
```

**Settings Consumption**:
```
Before verifying coverage or applying thresholds, read project settings:
cat forge/settings.yml
Use these values (with fallbacks if not set):
- tdd.coverage_threshold -> default 90 if not set
- tdd.hotfix_coverage_threshold -> default 70 if not set
```

---

#### Agent 5: forge-docs-updater

**Purpose**: Maintains project memory and documentation files.

**Responsibilities**:
- Keep `important_decisions.yml` current
- Capture new decisions when patterns emerge (timeouts, security trade-offs, integration contracts, logging standards, caching strategies, feature flags, data handling rules)
- Update sprint state and story index in `project.yml`
- Avoid duplicate decisions

**When Invoked**: Asynchronously after story completion.

**Persona**: "Documentation and memory updater for Forge projects"

**Completion Signals**: `MEMORY_UPDATED: {n} decisions`

**Notable**: Uses `haiku` model and has the smallest toolset (Read, Write, Grep). Only agent that explicitly runs asynchronously. This is a "background worker" agent.

---

#### Agent 6: forge-learning-analyzer

**Purpose**: Pattern discovery from workflow observability data.

**Responsibilities**:
- Load events from `forge/memory/learning/events.jsonl`
- Detect patterns across 5 categories: clarification predictors, workflow outcome predictors, deviation detectors, success indicators, efficiency patterns
- Calculate confidence scores using configurable thresholds from `forge/settings.yml`
- Generate pattern proposals with auto-approval or manual review classification
- Write proposals to `forge/memory/learning/pattern_proposals.yml`

**When Invoked**: On demand via `/forge learn analyze` or automatically when event threshold is reached.

**Persona**: "Machine Learning Engineer specializing in pattern discovery from workflow observability data"

**Completion Signals**: `ANALYSIS_COMPLETE`, `CLARIFICATION_NEEDED`

**Notable**: This is the only agent focused on meta-learning -- analyzing the workflow itself to improve future runs. It never touches production code.

---

#### Agent 7: forge-planner

**Purpose**: Derives user stories from design documents.

**Responsibilities**:
- Load design document and map sections to story boundaries
- Apply single-scope rule (each story has exactly ONE scope)
- Detect story tier (SIMPLE/STANDARD/COMPLEX) based on points, risk, files
- Generate story YAML with self-validation (tests-first approach for cross-references)
- Sprint assignment and dependency mapping
- Final verification loop across all stories

**When Invoked**: After design document is complete, when "plan" or "create stories" intent is detected.

**Persona**: "Principal Engineer planning story implementation"

**Completion Signals**: `PLANNING_COMPLETE: N stories`, `PLANNING_FAILED: {reason}`, `CLARIFICATION_NEEDED`

**Critical Rules** (quoted verbatim from the agent definition):
```
Rule 1: io_examples MUST Include Error Cases
Rule 2: Test References MUST Match Actual Tests
Rule 3: Define Tests FIRST, Then Reference Them
```

The self-validation protocol is notable:
```
5e. SELF-VALIDATE before writing file
Before writing the story file, verify:
- [ ] io_examples has at least one entry with "error", "fail", "invalid", or similar
- [ ] Every invariants[].test matches a tests.unit[].function_name
- [ ] Every failure_modes[].test matches a tests.unit[].function_name
- [ ] Every edge_case_matrix[].test (non-null) matches a test
```

---

#### Agent 8: forge-product-manager

**Purpose**: Product management activities across the workflow.

**Responsibilities**:
- **Workflow 1: Create PRD** (interactive or from document)
- **Workflow 2: Create Architecture** (derived from PRD)
- **Workflow 3: Story Review** (post-plan validation with RICE prioritization)
- **Workflow 4: Answer Clarifications** (route GAPS_FOUND/CLARIFICATION_NEEDED from other agents)
- **Workflow 5: UAT Checklist** (post-quality acceptance testing checklists)

**When Invoked**: At multiple points -- PRD creation (start of project), architecture creation, post-planning review, during clarification routing, post-quality UAT generation.

**Persona**: "Principal Product Manager working within the Forge framework"

**Notable**: Only agent with `AskUserQuestion` tool -- it is the designated human interaction point for product decisions. Has 5 distinct workflows triggered by `$ARGUMENTS`.

**Completion Signals**: `PRD_COMPLETE`, `ARCHITECTURE_COMPLETE`, `PM_REVIEW_COMPLETE`, `PM_ANSWER`, `PM_ESCALATE`, `UAT_CHECKLIST_COMPLETE`, `PM_FAILED: {reason}`

**Key integration point**: This agent answers clarification questions from other agents by searching PRD, Architecture, prior PM decisions, and important decisions in order.

---

#### Agent 9: forge-quality

**Purpose**: Comprehensive quality review of completed implementations.

**Responsibilities**:
- 13-dimension code review (A through M: Contract/API, Failure Modes, Data Integrity, Concurrency, Security, Observability, Performance, Maintainability, Testing, Deploy/Rollback, Configuration, Dependencies, Compatibility)
- Severity classification (P0-P3)
- Merge gate evaluation
- Independent verification testing (5+ tests not in the test suite)
- Automated QA (pytest, ruff, mypy, coverage)
- Decision consolidation to `important_decisions.yml`
- Final Review mode with 5 dimensions (Architectural Fit, Production Readiness, Evolution/Maintainability, What Was Missed, Challenger Mindset)

**When Invoked**: After GREEN phase in TDD workflow. Also invoked for "final-review" mode as the last gate.

**Persona**: "Principal Engineer performing quality review"

**Hooks**: Stop hook that runs `check-p0-findings.py` -- automatically checks for P0 findings when the agent completes.

**Completion Signals**: `QUALITY_APPROVED`, `QUALITY_APPROVED_WITH_NOTES`, `QUALITY_BLOCKED: P0={n}, P1={n}`, `CLARIFICATION_NEEDED`

**Note**: The description says "14-dimension" but the table in the definition lists 13 dimensions (A through M). This is a minor inconsistency.

---

#### Agent 10: forge-test-engineer

**Purpose**: Test automation and quality assurance specialist.

**Responsibilities**:
- Enforce test pyramid (70% unit, 20% integration, 10% E2E)
- Coverage thresholds by story tier (SIMPLE: 80%, STANDARD: 90%, COMPLEX: 95%)
- TDD compliance verification
- Edge case testing matrix enforcement
- Test quality principles (behavioral testing, isolation, determinism, speed)
- CI/CD testing guidance
- Evidence rule integration (every behavioral claim needs a test)

**When Invoked**: Proactively for test strategy, test automation, coverage analysis, CI/CD testing, and quality engineering. The description says "Use PROACTIVELY".

**Persona**: "Test engineer for the Forge workflow"

**Notable**: This agent has NO skills listed and NO permissionMode specified in its frontmatter, unlike most other agents. It reads more like a reference/knowledge agent than an active workflow participant. Its responsibilities overlap significantly with forge-checker (Mode 1: TEST_QUALITY) and with forge-developer (which runs tests inline).

---

#### Agent 11: python-pro

**Purpose**: Python-specific coding expertise.

**Responsibilities**:
- Write idiomatic Python (PEP 8, PEP 484, PEP 557, PEP 636)
- Advanced patterns: type-safe dataclasses, context managers, typed decorators, generators, async patterns, pattern matching, protocols
- Performance optimization (__slots__, generators, lru_cache, list comprehensions, collections)
- Testing best practices with pytest

**When Invoked**: Proactively for Python refactoring, optimization, or complex Python features. The description says "Use PROACTIVELY".

**Persona**: "Python specialist with deep expertise in Pythonic patterns, performance optimization, and modern Python features"

**Notable**: No Forge-specific skills, no hooks, no permissionMode. This is a pure language expert agent, completely decoupled from the Forge workflow. It contains extensive code examples as inline documentation.

---

#### Agent 12: typescript-pro

**Purpose**: TypeScript-specific coding expertise.

**Responsibilities**:
- Advanced type system (generics, conditional types, mapped types, template literal types, branded types, discriminated unions)
- Modern patterns (Result types, Builder pattern, State machines, DI, Event systems)
- Strict mode enforcement
- Migration patterns (JS to TS)
- Performance optimization at type-level and runtime

**When Invoked**: Proactively for TypeScript optimization, complex types, or migration from JavaScript. The description says "Use PROACTIVELY".

**Persona**: "TypeScript specialist with deep expertise in the type system, modern patterns, and idiomatic TypeScript development"

**Notable**: Same structural pattern as python-pro -- no Forge skills, no hooks, no permissionMode. Pure language expert.

---

## 2. Agent Roles & Boundaries

### 2.1 Role Classification

The 12 agents fall into four functional categories:

**Category A -- Workflow Core Agents** (directly participate in the TDD pipeline):
| Agent | Phase | Creates Artifacts | Modifies Code |
|-------|-------|-------------------|---------------|
| forge-analyzer | Pre-workflow (brownfield) | YAML analysis files | No |
| forge-designer | Pre-workflow | Design documents | No |
| forge-planner | Pre-workflow | Story YAML files | No |
| forge-developer | PLAN/RED/GREEN | Plans, tests, code | Yes |
| forge-checker | Gates (0, 1, 2) | Findings YAML | No (read-only) |
| forge-quality | Post-GREEN | Quality reports | No (verification tests only) |

**Category B -- Support Agents** (augment the workflow but are not in the critical path):
| Agent | Role |
|-------|------|
| forge-product-manager | PRD/Architecture creation, clarification routing, UAT |
| forge-docs-updater | Memory/decision maintenance (async) |
| forge-learning-analyzer | Meta-learning/pattern discovery |

**Category C -- Language Specialists** (orthogonal to the workflow):
| Agent | Role |
|-------|------|
| python-pro | Python-specific coding expertise |
| typescript-pro | TypeScript-specific coding expertise |

**Category D -- Test Specialist** (ambiguous positioning):
| Agent | Role |
|-------|------|
| forge-test-engineer | Test strategy and automation guidance |

### 2.2 Boundary Clarity Assessment

**Clear boundaries:**
- **forge-analyzer** has a well-defined scope: brownfield codebase analysis. It does not overlap with any other agent.
- **forge-designer** is clearly the design document creator. No other agent creates design documents.
- **forge-planner** is clearly the story creator. No other agent creates story YAML files.
- **forge-developer** is clearly the only code-writing agent. No other agent has the mandate to write production or test code (except during fix loops, where it is explicitly delegated back to forge-developer).
- **forge-checker** is explicitly read-only: "You inspect and report; you NEVER modify artifacts."
- **forge-docs-updater** has a clear, narrow scope: updating memory YAML files.
- **forge-learning-analyzer** has a unique scope: pattern discovery from event data.
- **python-pro** and **typescript-pro** are clearly language-specific knowledge agents.

**Unclear/overlapping boundaries:**
- **forge-checker vs. forge-quality**: Both perform quality assessment, but at different stages and with different scopes. See Section 8 for detailed overlap analysis.
- **forge-test-engineer vs. forge-developer**: The developer runs tests inline and enforces coverage. The test engineer provides test strategy guidance. The boundary is fuzzy -- when would you use forge-test-engineer instead of forge-developer?
- **forge-test-engineer vs. forge-checker (Mode 1)**: Both assess test quality. The checker does it at a gate; the test engineer provides general guidance.
- **forge-product-manager architecture workflow vs. forge-designer**: The PM creates Architecture.md; the designer creates design documents. These are conceptually related but the PM's Architecture.md is higher-level (technology choices, component overview) while the designer's document is implementation-specific (contracts, state machines, threat models).

### 2.3 Authority Hierarchy

Based on the definitions, there is an implicit authority hierarchy:

```
forge-product-manager  (defines WHAT to build -- PRD, requirements)
        |
        v
forge-designer         (defines HOW to build -- 18-section design)
        |
        v
forge-planner          (defines WHEN to build -- stories, sprints, priorities)
        |
        v
forge-developer        (BUILDS it -- plan, tests, code)
        |
        v
forge-checker          (GATES it -- plan quality, test quality, code quality)
        |
        v
forge-quality          (REVIEWS it -- 13-dimension review, final approval)
```

The `forge-product-manager` also has cross-cutting authority to answer clarifications from any agent and to review stories post-planning.

---

## 3. Agent Relationships & Dependency Graph

### 3.1 Direct Dependencies

```
                    ┌──────────────────┐
                    │  forge-product-  │
                    │    manager       │
                    │  (PRD, Arch,     │
                    │   Clarifications)│
                    └───────┬──────────┘
                            │ creates PRD.md, Architecture.md
                            │ answers GAPS_FOUND / CLARIFICATION_NEEDED
                            v
                    ┌──────────────────┐
                    │  forge-designer  │
                    │  (Design docs)   │
                    └───────┬──────────┘
                            │ creates designs/{feature}.md
                            v
                    ┌──────────────────┐
                    │  forge-planner   │
                    │  (Stories)       │
                    └───────┬──────────┘
                            │ creates stories/ST-###.yml
                            v
                ┌───────────┴───────────┐
                │                       │
                v                       v
    ┌──────────────────┐    ┌──────────────────────┐
    │  forge-checker   │    │   forge-developer    │
    │  (Mode 0: Plan)  │<-->│   (PLAN phase)       │
    │                  │    │                      │
    └──────────────────┘    └──────────┬───────────┘
                                       │
                                       v
    ┌──────────────────┐    ┌──────────────────────┐
    │  forge-checker   │    │   forge-developer    │
    │  (Mode 1: Test)  │<-->│   (RED phase)        │
    │                  │    │                      │
    └──────────────────┘    └──────────┬───────────┘
                                       │
                                       v
    ┌──────────────────┐    ┌──────────────────────┐
    │  forge-checker   │    │   forge-developer    │
    │  (Mode 2+3:      │<-->│   (GREEN phase)      │
    │   Debt+Slop)     │    │                      │
    └──────────────────┘    └──────────┬───────────┘
                                       │
                                       v
                            ┌──────────────────────┐
                            │   forge-quality      │
                            │   (13-dim review +   │
                            │    final-review)     │
                            └──────────┬───────────┘
                                       │
                                       v
                            ┌──────────────────────┐
                            │   forge-product-     │
                            │   manager (UAT)      │
                            └──────────┬───────────┘
                                       │
                                       v
                            ┌──────────────────────┐
                            │  forge-docs-updater  │
                            │  (async memory)      │
                            └──────────────────────┘
```

**Parallel/Independent agents:**
```
    ┌──────────────────┐        ┌──────────────────┐
    │  forge-analyzer  │        │ forge-learning-  │
    │  (brownfield     │        │   analyzer       │
    │   analysis)      │        │  (meta-learning) │
    └──────────────────┘        └──────────────────┘
    (runs before design)        (runs on-demand)

    ┌──────────────────┐        ┌──────────────────┐
    │   python-pro     │        │  typescript-pro  │
    └──────────────────┘        └──────────────────┘
    (invoked ad-hoc)            (invoked ad-hoc)

    ┌──────────────────┐
    │ forge-test-      │
    │   engineer       │
    └──────────────────┘
    (invoked ad-hoc)
```

### 3.2 Data Flow Dependencies (Artifacts)

Each agent reads from and writes to specific files. The data flow defines the true dependencies:

```
forge-analyzer     --> forge/.analysis/*.yml
forge-product-mgr  --> forge/docs/PRD.md, forge/docs/Architecture.md
forge-designer     --> forge/docs/designs/{feature}.md
                       reads: PRD.md, Architecture.md, forge/.analysis/*, important_decisions.yml
forge-planner      --> forge/stories/ST-###.yml, forge/memory/project.yml
                       reads: forge/docs/designs/{feature}.md
forge-developer    --> forge/.tmp/{story_id}/handoff.yml, implementation_plan.md, source code, tests
                       reads: stories/ST-###.yml, handoff.yml, important_decisions.yml
forge-checker      --> forge/.tmp/check/{story_id}/findings.yml
                       reads: stories, handoff, implementation_plan, source code, test code
forge-quality      --> quality report, important_decisions.yml
                       reads: stories, handoff, source code, test code
forge-docs-updater --> forge/memory/important_decisions.yml, forge/memory/project.yml
                       reads: handoff files
forge-learning-ana --> forge/memory/learning/pattern_proposals.yml
                       reads: forge/memory/learning/events.jsonl
forge-product-mgr  --> forge/memory/pm_review.yml, pm_decisions.yml, quality/uat_checklist.yml
                       reads: stories, PRD, Architecture, important_decisions
```

### 3.3 Clarification Routing Chain

A distinctive pattern is the clarification routing mechanism. Multiple agents can emit `CLARIFICATION_NEEDED` or `GAPS_FOUND`:

```
forge-analyzer       --CLARIFICATION_NEEDED-->  orchestrator --> user
forge-designer       --GAPS_FOUND----------->   orchestrator --> forge-product-manager --> user (if escalated)
forge-planner        --CLARIFICATION_NEEDED-->  orchestrator --> user
forge-developer      --CLARIFICATION_NEEDED-->  orchestrator --> user
forge-quality        --CLARIFICATION_NEEDED-->  orchestrator --> user
forge-learning-ana   --CLARIFICATION_NEEDED-->  orchestrator --> user
```

The `forge-product-manager` sits in the middle as a "first responder" for clarifications -- it searches PRD, Architecture, and prior decisions before escalating to the user. From the PM definition:

```
Search for answer in order:
  a. PRD (forge/docs/PRD.md)
  b. Architecture (forge/docs/Architecture.md)
  c. Prior PM decisions (forge/memory/pm_decisions.yml)
  d. Important decisions (forge/memory/important_decisions.yml)
```

---

## 4. Orchestration Model

### 4.1 The Orchestrator Is Not an Agent

A critical architectural detail: **the orchestrator is NOT defined as an agent**. It exists as a **skill template** (`orchestrate.md` and `orchestrate-parallel.md`) that is loaded into the main Claude Code thread or a sub-agent. The skill template states:

```
You are the TDD Orchestrator. Your job is to run the complete TDD workflow for
story {{story_id}} using sub-agents for each phase.
```

This means the orchestration logic lives in `/Users/shashank/workspace/applications/forge-claudify/.claude/skills/forge-workflow/orchestrate.md` and is invoked via the `forge-workflow` skill, not as a standalone agent.

### 4.2 Sequential Orchestration (Single Story)

The orchestrate.md template (v1.7.0) defines this sequential pipeline:

```
scaffold --> plan --> [Plan Quality Gate*] --> tests (RED) --> [Test Quality Gate]
  --> code (GREEN) --> [Code Quality Gate] --> quality --> final-review

* Plan Quality Gate only runs for STANDARD/COMPLEX tier stories
```

Each phase is executed by spawning a sub-agent via the Task tool. The orchestrator:
1. Reads `handoff.yml` to detect current state
2. Spawns the next phase's sub-agent with a minimal prompt
3. After completion, **explicitly verifies** by reading `handoff.yml` again
4. On failure, retries once with an enhanced prompt
5. On quality gate BLOCKED, triggers a fix loop (developer fixes, checker re-checks, up to 3 attempts)

**Phase-to-Agent/Skill mapping** from orchestrate.md:

| Phase | Skill or Agent | Max Fix Loops |
|-------|---------------|---------------|
| scaffold | `forge:scaffold` | -- |
| plan | `forge:plan-tests` | -- |
| plan_quality_gate | `forge-checker` (PLAN_QUALITY) | 1 |
| tests | `forge:write-tests` | -- |
| test_quality_gate | `forge-checker` (TEST_QUALITY) | 3 |
| code | `forge:implement` | -- |
| code_quality_gate | `forge-checker` (TECH_DEBT + AI_SLOP) | 3 |
| quality | `forge:quality` | -- |
| final-review | Inline (no agent) | -- |

### 4.3 Parallel Orchestration (Multiple Stories)

The `orchestrate-parallel.md` template (v1.6.0) adds multi-story parallelism using git worktrees:

```
Phase 1: ANALYZE       -- sub-agent reads all stories, detects conflicts
Phase 2: PROCESS       -- parse plan, handle blocking conflicts
Phase 2.5: CREATE WORKTREES -- haiku sub-agent creates .forge-worktrees/{story_id}/
Phase 3: EXECUTE       -- all stories run IN PARALLEL in separate worktrees
Phase 4: COLLECT       -- gather results
Phase 4.5: CLEANUP     -- haiku sub-agent removes successful worktrees
Phase 5: REPORT        -- final summary with merge instructions
```

Key design decisions:
- **TRUE filesystem isolation** via git worktrees (not just branches)
- **No lock coordination needed** -- each worktree is independent
- **User handles merging** -- the system does not auto-merge
- **Utility tasks use haiku** -- worktree setup/cleanup uses the cheapest model
- **Each story orchestrator has its own context** -- no shared state

Context management from the template:
```
| Component | Model | Context Usage |
|-----------|-------|---------------|
| Coordinator | default | ~5K tokens |
| Analyzer | default | ~15K tokens |
| Worktree Setup | haiku | ~2K tokens |
| Each Orchestrator | default | Independent |
| Worktree Cleanup | haiku | ~2K tokens |
```

### 4.4 Auto-Routing (Entry Point)

The `forge-auto-router.md` rule file defines how natural language commands get routed to the forge-workflow skill. It uses keyword matching:

```
Does message contain ST-### pattern?  --> Route to /forge-workflow
Does message START with a trigger keyword?  --> Route to /forge-workflow
Does message contain "forge" + action word?  --> Route to /forge-workflow
Otherwise:  --> Normal Claude response
```

High-confidence trigger keywords include: `init`, `analyze`, `design`, `plan`, `develop`, `scaffold`, `quality`, `review`, `orchestrate`, `complete`, `hotfix`, `rollback`, `validate`, `check`, `enrich`, `quick`, `create story`, `create PRD`, `forge status`, `forge help`.

### 4.5 Framework Rules (forge-framework.md)

The `forge-framework.md` rule file establishes the overall architecture:

```
1. Single Entry Point -- /forge-workflow accepts natural language intents
2. Orchestrator Pattern -- Main thread coordinates, never implements directly
3. Specialized Sub-Agents -- Each task delegated to expert sub-agents
```

It lists only 5 "core" agents (from the rule file):
```
- forge-analyzer -- Codebase analysis
- forge-designer -- Design documents
- forge-planner -- Story planning
- forge-developer -- TDD implementation
- forge-quality -- Quality review
```

This is a simplified view. The rule file does not mention forge-checker, forge-product-manager, forge-docs-updater, forge-learning-analyzer, forge-test-engineer, python-pro, or typescript-pro. This creates a documentation gap where the "official" architecture description does not match the actual agent inventory.

---

## 5. Agent Prompt Patterns

### 5.1 Common Structural Patterns

All Forge-specific agents follow a consistent YAML frontmatter + markdown body structure:

**Frontmatter fields** (from the agent definition spec):
```yaml
---
name: <agent-name>
description: >
  <multi-line description>
tools: <comma-separated tool list>
model: <sonnet|opus|haiku>
permissionMode: default
skills:
  - <skill-1>
  - <skill-2>
hooks:
  <hook-type>:
    - matcher: "<pattern>"
      hooks:
        - type: command
          command: "<shell command>"
---
```

**Body structure** (consistent across most agents):
1. **Persona statement**: "You are a [Role] performing [Task]"
2. **Mission section**: "## Your Mission"
3. **Process/Workflow section**: Step-by-step instructions
4. **Context Loading section**: What skills/data are preloaded
5. **Output section**: What files are produced
6. **Clarification Needed section**: How to handle ambiguity
7. **Completion Criteria section**: How to signal done

### 5.2 Persona Patterns

| Agent | Persona |
|-------|---------|
| forge-analyzer | "Principal Engineer performing comprehensive codebase analysis" |
| forge-checker | "Principal Engineer performing independent quality review at FAANG-level standards" |
| forge-designer | "Principal Engineer creating world-class design documents" |
| forge-developer | "Senior Software Engineer (FAANG-calibre) implementing stories through TDD" |
| forge-docs-updater | "Documentation and memory updater for Forge projects" |
| forge-learning-analyzer | "Machine Learning Engineer specializing in pattern discovery" |
| forge-planner | "Principal Engineer planning story implementation" |
| forge-product-manager | "Principal Product Manager working within the Forge framework" |
| forge-quality | "Principal Engineer performing quality review" |
| forge-test-engineer | "Test engineer for the Forge workflow" |
| python-pro | "Python specialist with deep expertise" |
| typescript-pro | "TypeScript specialist with deep expertise" |

**Observations:**
- 5 agents use "Principal Engineer" -- the highest seniority level
- forge-developer is "Senior Software Engineer (FAANG-calibre)" -- one level below Principal, which is interesting given it does the actual coding
- forge-docs-updater has no seniority title, matching its simpler role
- Language-specific agents use "specialist" rather than engineering titles

### 5.3 Clarification Protocol

A standardized clarification protocol is used across 6 agents (forge-analyzer, forge-designer, forge-developer, forge-planner, forge-quality, forge-learning-analyzer):

```
CLARIFICATION_NEEDED

Questions requiring answers before proceeding:

1. [CATEGORY: <domain-specific categories>]
   Question: <clear question text>
   Context: <why this matters>
   Options (if applicable): <option1>, <option2>, <option3>
```

Each agent has domain-specific categories:
- forge-analyzer: `architecture|domain|pattern|scope|toolchain`
- forge-designer: `requirement|architecture|security|performance|edge-case`
- forge-developer: `story-spec|architecture|testing|dependency|toolchain`
- forge-planner: `scope|complexity|dependency|priority|requirement`
- forge-quality: `severity|scope|standard|decision|trade-off`
- forge-learning-analyzer: `data|threshold|interpretation`

### 5.4 Completion Signal Pattern

Every Forge agent has a well-defined completion signal vocabulary. Common patterns:

- `{DOMAIN}_COMPLETE` -- successful completion
- `{DOMAIN}_FAILED: {reason}` -- failure with explanation
- `CLARIFICATION_NEEDED` -- blocked on user input
- `PASS | WARNING | BLOCKED` -- quality gate verdicts

### 5.5 Pattern Inconsistencies

1. **forge-test-engineer, python-pro, typescript-pro** do not follow the standard body structure. They lack: Mission section, Clarification Needed section, Completion Criteria section, Context Loading section.

2. **forge-test-engineer** lacks `skills` and `permissionMode` in frontmatter, unlike all other Forge-specific agents.

3. **python-pro and typescript-pro** are pure knowledge dumps in markdown -- they contain extensive code examples but no workflow integration instructions. Their structure is fundamentally different from the Forge agents.

4. **forge-product-manager** uses `$ARGUMENTS` in its prompt body (`## Task: $ARGUMENTS`), suggesting it receives task instructions dynamically. No other agent uses this pattern.

---

## 6. Language-Specific Agents

### 6.1 python-pro

**Scope**: Python 3.10+ modern features and patterns.

**Content breakdown**:
- **Core Competencies**: Type hints, pattern matching, dataclasses, async/await, context managers, decorators, generators
- **7 Advanced Patterns** with full code examples: Type-safe dataclasses, context managers, typed decorators, generators/iterators, async patterns, pattern matching, protocols
- **5 Performance Optimization** sections: __slots__, generators, lru_cache, list comprehensions, collections
- **Testing Best Practices**: pytest fixtures, parametrized tests, async tests, mocking

**What it does NOT do**:
- No reference to Forge workflow, stories, handoffs, or quality gates
- No reference to forge-developer or any other agent
- No completion signals or clarification protocol
- No notion of story tiers or coverage thresholds

**Integration model**: This agent is invoked ad-hoc when the user or orchestrator needs Python-specific expertise. It is NOT called during the standard TDD workflow. The `description` field says "Use PROACTIVELY for Python refactoring, optimization, or complex Python features" -- suggesting Claude Code should auto-route to it when Python tasks arise outside the Forge pipeline.

### 6.2 typescript-pro

**Scope**: TypeScript type system mastery and modern patterns.

**Content breakdown**:
- **Type System Mastery**: Generics, conditional types, branded types, discriminated unions, template literal types
- **6 Advanced Type Patterns** with full code examples: Branded types, discriminated unions, type-safe event emitters, builder pattern, conditional types, template literal types
- **Best Practices**: Type inference, unknown vs any, exhaustive checks, strict configuration, assertion functions
- **Migration Patterns**: JavaScript to TypeScript step-by-step
- **Performance**: Type-level and runtime optimization

**What it does NOT do**: Same as python-pro -- completely decoupled from Forge.

### 6.3 How They Differ from Generic Agents

| Aspect | Generic Forge Agents | Language Specialists |
|--------|---------------------|---------------------|
| Workflow integration | Deep (read handoffs, write findings) | None |
| Completion signals | Defined vocabulary | None |
| Clarification protocol | Standardized | None |
| Skills loaded | Forge-specific skills | None |
| Content style | Process instructions | Code reference library |
| Model | Varies | sonnet |
| Invocation | By orchestrator | Ad-hoc / proactive |

**Key insight**: The language specialists are essentially "prompt libraries" -- they inject language-specific knowledge into Claude's context when needed. They do not participate in the Forge workflow and could theoretically be replaced by `.claude/rules/` files or skill reference documents.

---

## 7. Agent-to-Skill Mapping

### 7.1 Skill Assignment Table

| Agent | Primary Skill | Reference Skill | External Scripts Used |
|-------|--------------|-----------------|----------------------|
| forge-analyzer | forge-analyze | forge-reference | `static_analysis.py` |
| forge-checker | forge-check | forge-reference | `check_plan_quality.py`, `check_test_quality.py`, `check_tech_debt.py`, `check_ai_slop.py`, `validate_stories.py`, `validate_design.py` |
| forge-designer | forge-design | forge-reference | (none) |
| forge-developer | forge-tdd | forge-reference | (none -- runs test frameworks directly) |
| forge-docs-updater | (none) | forge-reference | (none) |
| forge-learning-analyzer | (none) | forge-reference | `pattern_analysis.py` |
| forge-planner | forge-plan | forge-reference | (none) |
| forge-product-manager | product-manager-toolkit | forge-reference | `rice_prioritizer.py` |
| forge-quality | forge-quality | forge-reference | (none -- runs pytest, ruff, mypy directly) |
| forge-test-engineer | (none) | (none) | (none) |
| python-pro | (none) | (none) | (none) |
| typescript-pro | (none) | (none) | (none) |

### 7.2 Skill Coverage Analysis

**Every Forge workflow agent has `forge-reference`** as a secondary skill. This is presumably a shared reference skill containing the world-class standard, guard tokens, and other common references.

**5 agents have unique primary skills**:
- `forge-analyze`, `forge-check`, `forge-design`, `forge-tdd`, `forge-plan`, `forge-quality`, `product-manager-toolkit`

**3 agents have NO skills at all**:
- forge-test-engineer, python-pro, typescript-pro

### 7.3 Coupling Assessment

**Tight coupling (agent depends heavily on skill for workflow)**:
- forge-checker <-> forge-check: The checker agent's 5 modes each invoke specific Python scripts from the forge-check skill. If any script changes its interface, the agent prompt must be updated.
- forge-developer <-> forge-tdd: The developer agent's entire TDD workflow depends on the forge-tdd skill for workflow rules, coding practices, and handoff schema.
- forge-analyzer <-> forge-analyze: Phase templates are loaded from the skill.

**Moderate coupling**:
- forge-designer <-> forge-design: The 18-section template and gap analysis checklist come from the skill.
- forge-planner <-> forge-plan: Story schema and derivation workflow come from the skill.
- forge-product-manager <-> product-manager-toolkit: RICE prioritizer script and PRD templates come from the skill.

**Loose coupling**:
- All agents <-> forge-reference: This is a read-only reference skill. Agents can function without it, but may miss context.

**No coupling** (agents that are self-contained):
- python-pro, typescript-pro, forge-test-engineer: These agents carry all their knowledge inline.

---

## 8. Overlap & Redundancy

### 8.1 forge-checker vs. forge-quality

This is the most significant overlap in the agent system.

**forge-checker** (Mode 2+3 combined):
- TECH_DEBT: Timeouts, credentials, exception swallowing, complexity
- AI_SLOP: Hallucinated imports, generic naming, over-commenting, error quality
- Runs automated Python scripts
- P0/P1/P2 severity
- Gate logic: P0>0 or P1>2 blocks

**forge-quality**:
- 13-dimension review (A-M): Contract/API, Failure Modes, Data Integrity, Concurrency, Security, Observability, Performance, Maintainability, Testing, Deploy/Rollback, Configuration, Dependencies, Compatibility
- P0/P1/P2/P3 severity
- Merge gate: P0>0 blocks, P1>2 blocks
- Verification testing (5+ independent tests)
- Automated QA (pytest, ruff, mypy, coverage)
- Decision consolidation

**Overlap analysis**:

| Concern | forge-checker | forge-quality |
|---------|--------------|---------------|
| Security (credentials, auth) | Yes (TECH_DEBT P0) | Yes (Dim E: Security) |
| Missing timeouts | Yes (TECH_DEBT P0) | Yes (Dim B: Failure Modes) |
| Exception handling | Yes (TECH_DEBT P1) | Yes (Dim B: Failure Modes) |
| Complexity | Yes (TECH_DEBT P1) | Yes (Dim H: Maintainability) |
| Code naming quality | Yes (AI_SLOP P2) | Yes (Dim H: Maintainability) |
| Hallucinated imports | Yes (AI_SLOP P0) | Yes (Dim L: Dependencies) |

**The same issues could be flagged by both agents.** The key architectural difference is that forge-checker runs at gates DURING the TDD cycle (providing fast feedback), while forge-quality runs AFTER the full implementation (providing comprehensive review). This is defense-in-depth by design, but the duplicated checking creates unnecessary token cost if the checker already caught the issues.

### 8.2 forge-checker (Mode 1) vs. forge-test-engineer

**forge-checker Mode 1 (TEST_QUALITY)**:
- Behavioral assertions focus
- Error coverage verification
- Anti-pattern detection (over-mocking, flickering, giant tests)
- Independence checks
- Automated script: `check_test_quality.py`
- Part of quality gates in orchestration

**forge-test-engineer**:
- Test pyramid enforcement (70/20/10)
- Coverage thresholds by tier
- TDD compliance verification
- Edge case testing matrix
- Evidence rule integration
- NOT part of quality gates

These overlap on test quality assessment. The forge-test-engineer is more comprehensive in scope (pyramid, CI/CD, edge case matrix) but is not integrated into the orchestration workflow. The forge-checker Mode 1 is narrower but is a hard gate in the TDD pipeline.

### 8.3 forge-developer (test execution) vs. forge-test-engineer

The forge-developer explicitly states:

```
Test Execution (Inline)
You run tests directly - no separate test agent needed.
```

This directly overlaps with forge-test-engineer's stated responsibility of test automation. The developer handles: framework detection, running with coverage, parsing results, reporting in handoff. This is exactly what a test engineer would do.

### 8.4 forge-quality (decision consolidation) vs. forge-docs-updater

Both agents update `forge/memory/important_decisions.yml`:
- forge-quality: "Step 7: Decision Consolidation -- Extract important decisions and add to forge/memory/important_decisions.yml"
- forge-docs-updater: "Keep important_decisions.yml and other memory files current"

This creates a potential race condition or duplication if both agents try to update the same file after a story completes.

### 8.5 forge-product-manager (Architecture) vs. forge-designer

Both create architectural artifacts:
- forge-product-manager Workflow 2: Creates `forge/docs/Architecture.md` with technology stack, component architecture, data model, integration points, security, scalability, ADRs
- forge-designer: Creates `forge/docs/designs/{feature-slug}.md` with contracts, error taxonomy, state machines, threat model, invariants, concurrency, etc.

The distinction is abstraction level (system-level architecture vs. feature-level design), but both involve architectural thinking and ADRs. A user could be confused about which to invoke.

---

## 9. Missing Agents

### 9.1 Gaps Identified

**1. No Deployment/Release Agent**
The forge-quality agent reviews deploy/rollback (Dim J), but there is no agent for actually managing deployment, creating release notes, or managing feature flags. The forge-product-manager generates UAT checklists, but actual deployment orchestration is absent.

**2. No Refactoring Agent**
The TDD workflow has RED-GREEN but no explicit REFACTOR phase agent. Refactoring is implied ("GREEN state") but there is no dedicated agent that looks at code structure post-implementation and proposes refactoring opportunities. The forge-developer could handle this, but it is not in its current mandate.

**3. No Migration/Upgrade Agent**
For brownfield projects, there is analysis (forge-analyzer) but no agent for planning or executing migrations (database migrations, API version upgrades, dependency updates).

**4. No Security-Specialized Agent**
Security is scattered across forge-checker (TECH_DEBT), forge-quality (Dim E), and forge-designer (threat model). There is no dedicated security review agent that could run SAST/DAST tools, check OWASP compliance, or perform penetration testing guidance.

**5. No DevOps/Infrastructure Agent**
No agent handles CI/CD configuration, Docker files, Kubernetes manifests, or infrastructure-as-code. The forge-test-engineer mentions CI/CD testing concepts but does not create or manage CI configurations.

**6. No Code Review Agent for PRs**
The existing agents review code within the Forge workflow, but there is no agent for reviewing external pull requests or code changes that originate outside the Forge pipeline.

**7. No Documentation Generator Agent**
forge-docs-updater maintains memory files (YAML), but there is no agent for generating API documentation, user guides, or technical documentation from the implemented code.

### 9.2 Agent Overlap That Suggests Consolidation Rather Than Addition

Before adding new agents, consolidation opportunities exist:
- **Merge forge-test-engineer into forge-developer** or into forge-checker Mode 1 -- the test engineer's responsibilities are already covered by these two agents.
- **Merge forge-docs-updater into forge-quality** -- since forge-quality already does decision consolidation, having it also update project memory would be natural. The haiku model savings might not justify the architectural complexity of a separate agent.

---

## 10. Maintainability Assessment

### 10.1 What Would Break If You Changed One Agent

**forge-developer (HIGHEST RISK)**:
- The entire TDD pipeline depends on forge-developer for plan, test, and code phases
- Quality gate fix loops send findings back to forge-developer to fix
- Changing handoff schema (handoff.yml) would break the orchestrator's verification logic
- Changing guard tokens would break the orchestrator's error handling
- 6+ other agents read artifacts produced by forge-developer
- **Impact**: Changing forge-developer breaks the entire pipeline

**forge-checker (HIGH RISK)**:
- 3 quality gates in the orchestration template reference specific checker modes
- The orchestrate.md template contains hardcoded prompts for each checker mode
- Changing script names or interfaces breaks the gate prompts in orchestrate.md
- Adding/removing modes requires updating orchestrate.md
- **Impact**: Changing forge-checker breaks quality gates

**forge-planner (MEDIUM RISK)**:
- Story YAML format is consumed by forge-developer, forge-checker, forge-quality, forge-product-manager
- Changing the story schema would cascade to all downstream agents
- The self-validation rules are duplicated (planner validates, then checker validates in Mode 4)
- **Impact**: Changing story format breaks downstream agents

**forge-quality (MEDIUM RISK)**:
- The final-review prompt is inlined in orchestrate.md (not in the agent file)
- Decision consolidation overlaps with forge-docs-updater
- Stop hook dependency on check-p0-findings.py
- **Impact**: Changes require updating both the agent and orchestrate.md

**forge-designer (LOW-MEDIUM RISK)**:
- Output format consumed by forge-planner
- 18-section template referenced by forge-design skill
- **Impact**: Changing design format mainly affects forge-planner

**forge-product-manager (LOW-MEDIUM RISK)**:
- Clarification routing is referenced by orchestrator but is loosely coupled
- PRD/Architecture format consumed by forge-designer
- **Impact**: Changing PM output format affects downstream agents but is not in the critical TDD path

**forge-docs-updater, forge-learning-analyzer, forge-test-engineer, python-pro, typescript-pro (LOW RISK)**:
- These agents are loosely coupled or not in the critical path
- **Impact**: Changes are isolated

### 10.2 Duplication of Logic

Several pieces of logic are duplicated across agents and orchestration templates:

1. **Gate logic** (`P0>0 blocks, P1>2 blocks`) appears in:
   - forge-checker (each mode)
   - forge-quality (merge gate)
   - orchestrate.md (verification steps)

2. **Coverage thresholds** appear in:
   - forge-developer (code phase)
   - forge-test-engineer (coverage rules)
   - forge/settings.yml (source of truth)

3. **Story schema validation** appears in:
   - forge-planner (self-validation)
   - forge-checker Mode 4 (ARTIFACT validation)

4. **Important decisions update** appears in:
   - forge-quality (Step 7)
   - forge-docs-updater (primary purpose)

### 10.3 Single Points of Failure

1. **handoff.yml**: Every workflow agent reads/writes this file. If the schema changes or the file gets corrupted, the entire pipeline breaks.

2. **forge/settings.yml**: Coverage thresholds, learning settings, and other configuration. Multiple agents read this independently -- if they interpret it differently, inconsistent behavior results.

3. **orchestrate.md**: The orchestration template contains hardcoded prompts for quality gates, final review, and fix loops. It is the single most complex file in the system and is tightly coupled to 4+ agents.

### 10.4 Version Management

The orchestration templates carry version numbers (`v1.7.0` and `v1.6.0`), but individual agents do not. This creates a risk: if an agent changes incompatibly with the orchestration template, there is no version check to detect the mismatch.

### 10.5 Consistency Score

| Dimension | Score | Notes |
|-----------|-------|-------|
| Naming consistency | 9/10 | All Forge agents use `forge-` prefix; language agents break the pattern |
| Structural consistency | 7/10 | Core agents follow the pattern; test-engineer, python-pro, typescript-pro deviate |
| Persona consistency | 8/10 | Most use "Principal Engineer"; developer is oddly "Senior" not Principal |
| Completion signal consistency | 8/10 | Standardized across core agents; missing from specialist agents |
| Skill assignment consistency | 7/10 | Core agents have 1 primary + forge-reference; 3 agents have none |
| Clarification protocol consistency | 9/10 | Identical format across 6 agents with domain-specific categories |
| Tool assignment consistency | 6/10 | Wide variation -- some have 6 tools, some have 2; no clear rationale for some differences |

### 10.6 Recommendations for Improving Maintainability

1. **Extract gate logic to settings**: The `P0>0 blocks, P1>2 blocks` logic is duplicated everywhere. It should live in `forge/settings.yml` and be read by all agents.

2. **Version agent definitions**: Add version fields to agent frontmatter to enable compatibility checking with orchestration templates.

3. **Consolidate memory updates**: Choose ONE agent (forge-docs-updater or forge-quality) to own `important_decisions.yml` updates. Remove the duplication.

4. **Either integrate or remove forge-test-engineer**: Its responsibilities are covered by forge-developer (inline tests) and forge-checker (Mode 1). Either integrate it into the orchestration pipeline with a clear trigger, or remove it and distribute its knowledge to the agents that need it.

5. **Standardize language agents**: Either give python-pro and typescript-pro the standard Forge agent structure (skills, completion signals, permissionMode) or reclassify them as reference documents rather than agents.

6. **Move final-review out of orchestrate.md**: The final-review prompt is embedded in the orchestration template (100+ lines) rather than in the forge-quality agent definition. This creates maintenance burden. It should be extracted into either a separate agent or a mode of forge-quality.

7. **Document the full agent inventory in forge-framework.md**: The framework rule file only lists 5 agents, but 12 exist. This gap between documentation and reality will confuse contributors.

---

## Appendix A: Raw Frontmatter Comparison

```yaml
# forge-analyzer
name: forge-analyzer
tools: Read, Glob, Grep, Bash
model: sonnet
permissionMode: default
skills: [forge-analyze, forge-reference]
hooks: none

# forge-checker
name: forge-checker
tools: Read, Glob, Grep, Bash
model: sonnet
permissionMode: default
skills: [forge-check, forge-reference]
hooks: none

# forge-designer
name: forge-designer
tools: Read, Write, Glob, Grep
model: opus
permissionMode: default
skills: [forge-design, forge-reference]
hooks: none

# forge-developer
name: forge-developer
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
permissionMode: default
skills: [forge-tdd, forge-reference]
hooks: PreToolUse on Write|Edit -> validate-story-alignment.sh

# forge-docs-updater
name: forge-docs-updater
tools: Read, Write, Grep
model: haiku
permissionMode: default
skills: [forge-reference]
hooks: none

# forge-learning-analyzer
name: forge-learning-analyzer
tools: Read, Bash
model: sonnet
permissionMode: default
skills: [forge-reference]
hooks: none

# forge-planner
name: forge-planner
tools: Read, Write, Glob, Grep
model: sonnet
permissionMode: default
skills: [forge-plan, forge-reference]
hooks: none

# forge-product-manager
name: forge-product-manager
tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
model: sonnet
permissionMode: default
skills: [product-manager-toolkit, forge-reference]
hooks: none

# forge-quality
name: forge-quality
tools: Read, Write, Bash, Glob, Grep
model: sonnet
permissionMode: default
skills: [forge-quality, forge-reference]
hooks: Stop -> check-p0-findings.py

# forge-test-engineer
name: forge-test-engineer
tools: Read, Write, Edit, Bash
model: sonnet
permissionMode: (not specified)
skills: (none)
hooks: none

# python-pro
name: python-pro
tools: Read, Write, Edit, Bash
model: sonnet
permissionMode: (not specified)
skills: (none)
hooks: none

# typescript-pro
name: typescript-pro
tools: Read, Write, Edit, Bash
model: sonnet
permissionMode: (not specified)
skills: (none)
hooks: none
```

## Appendix B: Completion Signal Registry

| Agent | Success | Failure | Clarification | Other |
|-------|---------|---------|---------------|-------|
| forge-analyzer | ANALYSIS_COMPLETE | ANALYSIS_FAILED: {reason} | CLARIFICATION_NEEDED | -- |
| forge-checker | PASS | BLOCKED | -- | WARNING |
| forge-designer | DESIGN_COMPLETE | -- | GAPS_FOUND | -- |
| forge-developer | PHASE_COMPLETE: {phase} | PHASE_FAILED: {reason} | CLARIFICATION_NEEDED | Guard tokens |
| forge-docs-updater | MEMORY_UPDATED: {n} decisions | -- | -- | -- |
| forge-learning-analyzer | ANALYSIS_COMPLETE | -- | CLARIFICATION_NEEDED | -- |
| forge-planner | PLANNING_COMPLETE: N stories | PLANNING_FAILED: {reason} | CLARIFICATION_NEEDED | -- |
| forge-product-manager | PRD_COMPLETE, ARCHITECTURE_COMPLETE, PM_REVIEW_COMPLETE, UAT_CHECKLIST_COMPLETE | PM_FAILED: {reason} | PM_ESCALATE | PM_ANSWER |
| forge-quality | QUALITY_APPROVED, QUALITY_APPROVED_WITH_NOTES | QUALITY_BLOCKED: P0={n}, P1={n} | CLARIFICATION_NEEDED | -- |
| forge-test-engineer | (none defined) | (none defined) | (none defined) | -- |
| python-pro | (none defined) | (none defined) | (none defined) | -- |
| typescript-pro | (none defined) | (none defined) | (none defined) | -- |

## Appendix C: File I/O Map

```
WRITES:
  forge-analyzer     -> forge/.analysis/*.yml, forge/.analysis/_manifest.yml
  forge-checker      -> forge/.tmp/check/{story_id}/findings.yml
  forge-designer     -> forge/docs/designs/{feature-slug}.md
  forge-developer    -> forge/.tmp/{story_id}/handoff.yml, implementation_plan.md, source code, tests
  forge-docs-updater -> forge/memory/important_decisions.yml, forge/memory/project.yml
  forge-learning-ana -> forge/memory/learning/pattern_proposals.yml, analysis_report.md, pattern_statistics.yml
  forge-planner      -> forge/stories/ST-###.yml, forge/memory/project.yml
  forge-product-mgr  -> forge/docs/PRD.md, forge/docs/Architecture.md, forge/memory/pm_review.yml,
                         forge/memory/pm_decisions.yml, forge/quality/uat_checklist.yml
  forge-quality      -> quality report, forge/memory/important_decisions.yml

READS (key dependencies):
  forge-designer     <- forge/docs/PRD.md, forge/docs/Architecture.md, forge/.analysis/*,
                         forge/memory/important_decisions.yml
  forge-planner      <- forge/docs/designs/{feature}.md
  forge-developer    <- forge/stories/ST-###.yml, forge/.tmp/{story_id}/handoff.yml,
                         forge/memory/important_decisions.yml, forge/settings.yml
  forge-checker      <- forge/stories/ST-###.yml, forge/.tmp/{story_id}/*,
                         source code, test code
  forge-quality      <- forge/stories/ST-###.yml, forge/.tmp/{story_id}/handoff.yml,
                         forge/memory/important_decisions.yml, source code, test code
  forge-product-mgr  <- forge/docs/PRD.md, forge/docs/Architecture.md,
                         forge/stories/ST-###.yml, forge/memory/pm_decisions.yml,
                         forge/memory/important_decisions.yml
  forge-docs-updater <- forge/.tmp/*/handoff.yml (scans for patterns)
  forge-learning-ana <- forge/memory/learning/events.jsonl, forge/settings.yml
```
