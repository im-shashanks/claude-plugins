# Forge Framework Analysis Report

> **Purpose:** Reference document for building Shaktra — distilled from 7,875 lines of raw analysis across 9 documents.
> **Source:** `~/workspace/applications/forge-claudify` (Forge v2.1.0)
> **Date:** 2026-02-05
> **Raw files:** `docs/Forge-analysis/raw-files/`

---

## Table of Contents

- [1. Forge at a Glance](#1-forge-at-a-glance)
- [2. Architecture & Configuration](#2-architecture--configuration)
  - [2.1 Configuration Layers](#21-configuration-layers)
  - [2.2 Rules System](#22-rules-system)
  - [2.3 Configuration Anti-Patterns](#23-configuration-anti-patterns)
- [3. Agent System](#3-agent-system)
  - [3.1 Agent Inventory](#31-agent-inventory)
  - [3.2 Orchestration Model](#32-orchestration-model)
- [4. Skills System](#4-skills-system)
  - [4.1 Skills Inventory](#41-skills-inventory)
  - [4.2 Skill Architecture Patterns](#42-skill-architecture-patterns)
  - [4.3 forge-workflow: The Central Orchestrator](#43-forge-workflow-the-central-orchestrator)
  - [4.4 Skills Anti-Patterns](#44-skills-anti-patterns)
- [5. Workflow & Process Flow](#5-workflow--process-flow)
  - [5.1 End-to-End Lifecycle](#51-end-to-end-lifecycle)
  - [5.2 Parallel Execution](#52-parallel-execution)
  - [5.3 Quality Gates](#53-quality-gates)
  - [5.4 Workflow Variants](#54-workflow-variants)
  - [5.5 Story-Driven Development Model](#55-story-driven-development-model)
- [6. Quality & Validation System](#6-quality--validation-system)
  - [6.1 P0-P3 Severity Model](#61-p0-p3-severity-model)
  - [6.2 Checklist Inventory](#62-checklist-inventory)
  - [6.3 High-Value Checks Worth Porting](#63-high-value-checks-worth-porting)
  - [6.4 TDD Implementation](#64-tdd-implementation)
  - [6.5 Quality System Redundancy](#65-quality-system-redundancy)
- [7. State, Memory & Tooling](#7-state-memory--tooling)
  - [7.1 State Files](#71-state-files)
  - [7.2 Learning System Assessment](#72-learning-system-assessment)
  - [7.3 Hooks & Tooling Inventory](#73-hooks--tooling-inventory)
  - [7.4 MCP Servers](#74-mcp-servers)
- [8. Problems: Redundancy, Bloat & Gaps](#8-problems-redundancy-bloat--gaps)
  - [8.1 Redundancy Map](#81-redundancy-map)
  - [8.2 Bloat Assessment](#82-bloat-assessment)
  - [8.3 Architecture Anti-Patterns](#83-architecture-anti-patterns)
  - [8.4 Missing Capabilities](#84-missing-capabilities)
  - [8.5 Maintainability Scorecard](#85-maintainability-scorecard)
- [9. Shaktra Design Guidance](#9-shaktra-design-guidance)
  - [9.1 Architecture Lessons](#91-architecture-lessons)
  - [9.2 Workflow & Skills Lessons](#92-workflow--skills-lessons)
  - [9.3 Quality & Tooling Lessons](#93-quality--tooling-lessons)
  - [9.4 Top 20 Recommendations](#94-top-20-recommendations)
  - [9.5 Must Not Repeat Checklist](#95-must-not-repeat-checklist)

---

## 1. Forge at a Glance

Forge is a Claude Code framework that orchestrates agile-inspired software development using Claude Code primitives (rules, skills, agents, hooks, MCP). It guides AI through: **Plan -> Design -> Test (TDD) -> Implement -> Quality Review -> Ship**.

| Metric | Count |
|--------|-------|
| Total files (non-vendor) | 271 |
| Total lines | 91,546 |
| Dead code (`_to_be_deleted/`) | 97 files / 37,057 lines (40%) |
| Active agents | 12 |
| Skills | 12 (with ~53 sub-files) |
| Rules | 5 |
| Hooks | 7 (only 2 wired up) |
| MCP servers | 2 (both non-functional stubs) |
| Python scripts | 6 (~1,500 lines) |
| Instruction content | ~22,000+ lines of markdown (82% of framework) |
| Weighted maintainability | 4.5/10 |

---

## 2. Architecture & Configuration

### 2.1 Configuration Layers

| # | Layer | File | Loaded When | What It Does |
|---|-------|------|-------------|--------------|
| 0 | Project Identity | `CLAUDE.md` (44 lines) | Always, first | Declares project name, points to `/forge-workflow`. Minimal stub. |
| 1 | Project Settings | `.claude/settings.json` (47 lines) | Always | Permissions (deny .env/credentials/secrets), hooks (story-alignment, branch-block), env vars (`FORGE_MODE`, `FORGE_MIN_COVERAGE=90`, `FORGE_ENFORCE_TDD=1`). |
| 2 | Local Overrides | `.claude/settings.local.json` (16 lines) | Always (local) | Adds broad `Bash(python:*)` — undermines Layer 1 restrictions. |
| 3 | Always-On Rule | `rules/forge-auto-router.md` (85 lines) | Always | Keyword-based intent router: ~20 trigger words redirect to `/forge-workflow`. |
| 4 | Always-On Rule | `rules/forge-framework.md` (88 lines) | Always | Framework reference card: architecture, scopes, intent table, file locations. |
| 5 | Contextual Rule | `rules/quality-standards.md` (122 lines) | Glob: `forge/.tmp/**/quality_report.yml` | 14-dimension quality review, P0-P3 severity, merge gate logic. |
| 6 | Contextual Rule | `rules/story-validation.md` (128 lines) | Glob: `forge/stories/**/*.yml` | Story schema validation, tier detection, required fields per tier. |
| 7 | Contextual Rule | `rules/tdd-workflow.md` (122 lines) | Glob: `forge/.tmp/**` | TDD phase sequence, handoff state schema, phase guard tokens. |
| 8 | On-Demand Skill | `skills/forge-workflow/SKILL.md` (1,481 lines) | Via `/forge-workflow` | Central orchestrator: intent classification, sub-agent dispatch, gate enforcement. |
| 9 | On-Demand Agents | `agents/forge-*.md` (12 files) | Via Task tool | Phase-specific sub-agents. |
| 10 | Runtime Config | `forge/settings.yml` (30 lines) | Read by agents | Coverage thresholds, quality gates, learning config. |

**Interaction flow:**
```
User message -> Layer 3 (auto-router) intercepts keywords -> Layer 8 (forge-workflow) classifies intent
  -> spawns Layer 9 (agent) -> agent reads Layer 10 (settings.yml)
    -> agent creates/modifies files -> Layers 5-7 (contextual rules) activate via globs
```

**Key redundancy/conflicts:**
1. Coverage threshold defined 3x (env var, YAML, hardcoded in rule) — no precedence rule
2. Quality dimensions: Layer 5 says 14, README says 13 — already drifted
3. Valid scopes repeated 4x across rule, rule, README, skill
4. Live CLAUDE.md missing 4 critical behavioral sections present in the template
5. Local settings `Bash(python:*)` undermines project settings' narrow allow-list
6. Always-on rules cost 173 lines on every turn, even for non-Forge interactions

### 2.2 Rules System

| Rule File | Lines | Purpose | Always? | Key Problem |
|-----------|-------|---------|---------|-------------|
| `forge-auto-router.md` | 85 | Keyword-based middleware redirecting to `/forge-workflow` | Yes | Over-broad capture (e.g., "plan my weekend" triggers Forge) |
| `forge-framework.md` | 88 | Canonical reference card (entry point, agents, scopes, intents) | Yes | Lists only 5 of 12 agents. Duplicates auto-router's intent table. |
| `quality-standards.md` | 122 | 14-dim quality review, P0-P3, merge gate logic | No (glob) | Dimension count contradicts README (14 vs 13) |
| `story-validation.md` | 128 | Schema rules for story YAML by tier | No (glob) | Valid scopes duplicated from framework rule. Schema rules duplicated by checker. |
| `tdd-workflow.md` | 122 | TDD phases, handoff schema, guard tokens | No (glob) | Glob too broad — activates for ANY file in `forge/.tmp/` |

**Context window cost:** 173 lines always-on + up to 244 more when working in `forge/.tmp/` = **~417 lines** of rules before any skill or agent loads.

### 2.3 Configuration Anti-Patterns

1. **Same value in multiple sources** — Coverage threshold in 5 places with no precedence
2. **Local settings negate project settings** — `Bash(python:*)` bypasses narrow allow-list
3. **Always-on rules for non-framework use** — 173 lines load even for "what does this function do?"
4. **Globs too broad** — `forge/.tmp/**` activates TDD rule for any temp file
5. **Template not applied to live config** — Live CLAUDE.md lacks 4 critical sections from template
6. **Keyword routing with no escape hatch** — Common words ("plan", "review") collide with non-Forge intents
7. **Duplicated content across layers** — Valid scopes in 4 places, TDD phases in 4 places, P0-P3 in 6 places
8. **Hooks registered but not wired** — 5 of 7 hooks effectively dead
9. **Agents duplicate loaded skill content** — Double context cost, double maintenance
10. **No schema versioning** — Orchestrator v1.7.0 but agents have no version field
11. **Placeholder MCP servers in config** — Disabled stubs suggest non-existent capabilities
12. **God file orchestrator** — 1,481 lines, repeats POST-COMPLETION GATES 4x internally
13. **macOS incompatibility** — `grep -oP` (GNU Perl regex) breaks on macOS BSD grep
14. **No template re-sync** — Runtime settings never get new template fields after framework updates

---

## 3. Agent System

### 3.1 Agent Inventory

| Agent | Purpose | Model | When Invoked | Problems |
|-------|---------|-------|--------------|----------|
| **forge-analyzer** | 13-phase brownfield codebase analysis | sonnet | Start of brownfield projects | Well-scoped. No issues. |
| **forge-checker** | Quality gates: 5 modes (plan, test, tech debt, AI slop, artifact) | sonnet | At gates during TDD | Heavy overlap with forge-quality on security, timeouts, exception handling |
| **forge-designer** | 18-section design documents | **opus** | "design X" intent | Only opus agent. Justified by high leverage of design artifacts. |
| **forge-developer** | TDD engine: PLAN, RED, GREEN, scaffold, hotfix, rollback | sonnet | During TDD per story | Highest-risk: entire pipeline depends on it. Changing handoff schema breaks everything. |
| **forge-docs-updater** | Maintains project memory (decisions.yml, project.yml) | **haiku** | Async, after story completion | Race condition: forge-quality also writes to decisions.yml |
| **forge-learning-analyzer** | Pattern discovery from event data | sonnet | On-demand / auto-threshold | Dead code: zero events processed, invalid imports, undocumented |
| **forge-planner** | Derives stories from design docs, tiers, sprints | sonnet | "plan" intent, after design | Schema consumed by 4+ downstream agents. Self-validation duplicates checker. |
| **forge-product-manager** | PRDs, architecture, RICE, clarification routing, UAT | sonnet | Multiple workflow points | Only agent with `AskUserQuestion`. 5 workflows via `$ARGUMENTS`. Overlaps with designer. |
| **forge-quality** | 13-dim code review, severity, merge gate, verification tests | sonnet | After GREEN phase | Says "14-dimension" but lists 13 (A-M). Overlaps heavily with checker. Stop hook not wired. |
| **forge-test-engineer** | Test strategy guidance, pyramid, coverage | sonnet | Ad-hoc / "proactive" | No skills, no completion signals. Overlaps with developer + checker. **Never invoked by orchestrator.** |
| **python-pro** | Python 3.10+ patterns, pytest best practices | sonnet | Ad-hoc | Not part of Forge workflow. No integration. Essentially a prompt library. |
| **typescript-pro** | TypeScript type system, strict mode, migration | sonnet | Ad-hoc | Same as python-pro: decoupled, no integration. |

**Categories:** Workflow Core (6: analyzer, designer, planner, developer, checker, quality) | Support (3: PM, docs-updater, learning-analyzer) | Language Specialists (2: python-pro, typescript-pro) | Ambiguous (1: test-engineer)

### 3.2 Orchestration Model

The orchestrator is **not an agent** — it's a skill template (`orchestrate.md`) loaded into forge-workflow, executed in the main thread. It spawns sub-agents via the Task tool.

**Sequential pipeline (single story):**
```
scaffold -> plan -> [Plan Quality Gate*] -> tests (RED) -> [Test Quality Gate]
  -> code (GREEN) -> [Code Quality Gate] -> quality -> final-review

* Plan Quality Gate runs only for STANDARD/COMPLEX
```

**Phase-to-agent mapping:**

| Phase | Agent | Max Fix Loops |
|-------|-------|---------------|
| scaffold | forge-developer (scaffold mode) | — |
| plan | forge-developer (plan phase) | — |
| plan_quality_gate | forge-checker (PLAN_QUALITY) | 1 |
| tests | forge-developer (RED phase) | — |
| test_quality_gate | forge-checker (TEST_QUALITY) | 3 |
| code | forge-developer (GREEN phase) | — |
| code_quality_gate | forge-checker (TECH_DEBT + AI_SLOP parallel) | 3 |
| quality | forge-quality agent | — |
| final-review | Inline in orchestrate.md (not agent) | — |

**Fix loop pattern:** On BLOCKED → send findings to forge-developer → developer fixes → checker re-checks. Max 3 attempts, then fail.

**Dependency graph:**
```
forge-product-manager -> PRD, Architecture
  -> forge-analyzer -> analysis artifacts (brownfield only)
    -> forge-designer -> design docs
      -> forge-planner -> stories (ST-###.yml)
        -> forge-developer -> handoff.yml, source, tests
           |    ^
           +----+--- forge-checker (gates)
                -> forge-quality -> quality report, decisions
                  -> forge-product-manager (UAT)
                    -> forge-docs-updater -> decisions.yml, project.yml (async)
```

**What works:** Clear sequential pipeline, sub-agent isolation via Task tool, parallel multi-story via worktrees, model tiering (opus/haiku/sonnet), clarification routing through PM before user.

**What's broken:** God file orchestrator (1,481 lines, 4x repetition), checker/quality duplicate checks, test-engineer never invoked, learning-analyzer dead, no version compatibility checks, handoff.yml is single point of failure, ~150K+ tokens per story.

---

## 4. Skills System

### 4.1 Skills Inventory

| Skill | Command | Purpose | Sub-files | Complexity | Key Problems |
|-------|---------|---------|-----------|------------|--------------|
| forge-analyze | internal | 13-phase brownfield analysis | 4 | Heavy | Over-engineered resumability; dead migration file |
| forge-check | internal | 6 checklists, 150+ checks, P0-P3, 3 gates | 9 | Heavy | Tech-debt & ai-slop overlap; lock.py is no-op |
| forge-design | internal | 18-section design docs with gap analysis | 3 | Medium | Gap-analysis.md too thin for own file |
| forge-plan | internal | Story derivation from design docs, tiered schema | 6 | Heavy | 1060-line story schema; sprint planning is scope creep |
| forge-quality | internal | 14-dim CCR review, verification testing, decisions | 3 | Heavy | 1650 lines of instructions; overlaps with forge-check |
| forge-reference | passive | Shared constants: 31 principles, guard tokens, scopes | 6 | Simple | Drift risk if skills evolve without update |
| forge-tdd | internal | TDD engine: PLAN->RED->GREEN, handoff state machine | 5 | Heavy | 1142-line monolith; scaffold is Python-biased |
| forge-workflow | `/forge` | Central orchestrator: intents, delegation, gates, state | 10 | Heavy | 4200 lines; god-file; violates own single-responsibility |
| brainstorming | `/brainstorm` | One-question-at-a-time design exploration | 1 | Simple | Well-scoped |
| error-resolver | user-invocable | 5-step error diagnosis with replay system | 1 | Simple | Standalone, no forge deps. Good template. |
| product-manager-toolkit | user-invocable | RICE, interview analysis, PRD templates | 1 | Medium | Disconnected from core; overlaps with pm-touchpoints |
| subagent-driven-development | user-invocable | Fresh agent per task with 2-stage adversarial review | 4 | Medium | 3x API cost; unclear relation to orchestrate.md |

**Totals:** 12 skills, ~53 sub-files, ~22,000+ lines of markdown instructions

### 4.2 Skill Architecture Patterns

**SKILL.md structure:** metadata (name, version, user-invocable, model, tools) -> purpose -> process overview -> sub-file references -> guard tokens -> dependencies.

**Sub-files:** Execution templates loaded on-demand. Naming inconsistent across skills: numbered (`00-static.md`), descriptive (`story-derivation.md`), domain-typed (`tech-debt-checklist.md`).

**What works:** Clear entry point (SKILL.md as manifest), YAML-as-contract between skills, guard tokens for halt conditions, separation of reference vs execution (forge-reference as passive library).

**What doesn't:** Sub-files too large (1142, 963, 950 lines), brownfield artifact-loading duplicated across 4 skills, no partial loading mechanism, schema files double as documentation.

### 4.3 forge-workflow: The Central Orchestrator

At 4,200 lines across 10 files, it handles: intent classification, workflow state management, sub-agent coordination, quality gate enforcement, PM integration, self-learning, parallel execution, dashboard rendering, project initialization, and help system. Violates its own P6 (Single Responsibility) principle.

**25 intents:** help, init, status/dashboard, scope, learn, create-prd, create-architecture, analyze, design, plan, enrich, quick, validate, check, scaffold, develop, develop-plan, develop-tests, develop-code, quality, hotfix, rollback, orchestrate/complete, parallel, merge.

**What should be split out:** Intent routing (stateless router), state management (dedicated service), dashboard (read-only skill), PM integration (PM skill owns touchpoints), self-learning (remove entirely), help (static file), init (one-time bootstrap, separate from orchestration).

### 4.4 Skills Anti-Patterns

1. **God-file orchestrator** — 1,482 lines handling 10+ responsibilities
2. **Spec-as-instructions** — story-schema.md (1060 lines) serves as both spec AND execution instructions
3. **Duplicated artifact-loading** — every brownfield skill copy-pastes the "load these YAML files" table
4. **Overlapping quality checks** — 4 different skills review code quality with overlapping criteria
5. **Premature abstraction** — lock.py (8-line no-op), self-learning system (500+ lines for speculative value)
6. **Dead files retained** — analyze-codebase.md is just a deprecation notice
7. **Inconsistent naming** — no unified file naming convention across skills
8. **Circular self-review** — PE Review asks LLM to argue against its own output
9. **Aggressive auto-routing** — common English words trigger full pipelines with no confirmation
10. **Ceremony floor too high** — SIMPLE tier still requires 8 fields + full TDD pipeline
11. **Context saturation** — 22,000+ lines; loading one skill (4200 lines) consumes major context
12. **State fragmentation** — state across 5+ files with no transactional integrity
13. **No escape hatches** — can't mark quality findings as "accepted risk"
14. **PM bolted on** — added as workflow intercepts, not first-class participant
15. **No iteration within phases** — only forward progression or destructive rollback

---

## 5. Workflow & Process Flow

### 5.1 End-to-End Lifecycle

```
                      USER INPUT
                          |
                [INTENT CLASSIFICATION]
                          |
      +-------------------+-------------------+
      |                   |                   |
 [GREENFIELD]       [BROWNFIELD]         [QUICK PATH]
      |                   |                   |
 Create PRD          Analyze (13          Quick Story
      |              phases)               (8 fields)
 Create Arch              |                   |
      |                   |                   v
      +--------+----------+              [DEVELOP]
               |
          [DESIGN] (18 sections)
               |
       GAPS_FOUND? --yes--> PM/User answers
               |
        [PLAN STORIES] (single-scope rule)
               |
        Validate ----fail----> Auto-fix
               |
  ======= TDD PIPELINE (per story) =======
  |  SCAFFOLD -> PLAN -> [PLAN GATE*]     |
  |  -> TESTS/RED -> [TEST GATE]          |
  |  -> CODE/GREEN -> [CODE GATE]         |
  =========================================
               |
      [QUALITY REVIEW] (14-dim CCR)
               |
      [PM UAT GENERATION]
               |
      [FINAL REVIEW] (PE Review)
               |
           [DONE]

  * Plan Quality Gate skipped for SIMPLE tier
```

### 5.2 Parallel Execution

Uses git worktrees for filesystem isolation:
```
[PARALLEL REQUEST: ST-001, ST-002, ST-003]
  -> ANALYZE (detect conflicts)
    -> BLOCKING: both CREATE same file -> serialize
    -> SHARED: both MODIFY same file -> parallelize, merge later
    -> DEPENDENCY: respect blocked_by fields
  -> CREATE WORKTREES (lightweight model)
  -> EXECUTE (all stories in parallel, isolated TDD)
  -> COLLECT (check STORY_COMPLETE/STORY_FAILED)
  -> CLEANUP (remove successful worktrees)
  -> REPORT (branch names, gate status, coverage, merge order)
```

### 5.3 Quality Gates

| Gate | When | Blocking Threshold | Max Fix Loops | Skip? |
|------|------|--------------------|---------------|-------|
| Pre-TDD Validation | Before scaffold | Any error | Until clean | Never |
| Plan Quality | After PLAN | HIGH gaps > 0 | 1 | SIMPLE tier |
| Test Quality | After RED | P0 > 0 or P1 > 2 | 3 | Never |
| Code Quality | After GREEN | P0 > 0 or P1 > 2 | 3 | Never |
| CCR Review | After code quality | P0 > 0 = BLOCKED | N/A (report) | Never |
| PM UAT | After CCR | P0 = HOLD | N/A | Never |
| Final Review | After UAT | NEEDS_WORK | N/A | Never |

**Create-Check-Fix loop pattern:**
```
attempt = 0
while attempt < max_attempts:
    attempt++
    result = checker.validate(artifact)
    if PASSED: return SUCCESS
    if no_progress after 2 attempts: escalate to user
    creator.fix(gaps)
return escalate(max_attempts)
```

### 5.4 Workflow Variants

| Variant | Description | Trigger |
|---------|-------------|---------|
| **Greenfield** | PRD -> Arch -> Design -> Plan -> Develop -> Quality | New project, `init` |
| **Brownfield** | Analyze -> Design -> Plan -> Develop -> Quality | Existing codebase |
| **Individual Phase** | Run single TDD phase independently | `develop ST-001 plan` |
| **Quick Story** | Auto-infer scope, SIMPLE 8-field, skip design | `quick "Fix typo..."` |
| **Hotfix** | Skip story, fix directly, 70% coverage, retroactive story | `hotfix "Fix null pointer..."` |
| **Enrich** | Interactive story creation from NL/existing/external | `enrich "Add rate limiting..."` |
| **Retroactive** | SIMPLE story generated post-hoc from hotfix | Auto-created by hotfix |
| **Parallel** | Multiple stories via git worktrees | `parallel: ST-001 ST-002` |
| **Orchestrate** | Full TDD pipeline end-to-end, autonomous | `orchestrate ST-001` |
| **Rollback** | Reset story to earlier phase | `rollback ST-001 to plan` (advertised but unimplemented) |

### 5.5 Story-Driven Development Model

**Tiers:**

| Tier | Fields | Auto-Detection | Coverage |
|------|--------|----------------|----------|
| SIMPLE | 8 | points <= 2, risk low, 1 file | 80% |
| STANDARD | 16 | Default | 90% |
| COMPLEX | 20+ | points >= 8, risk high, security/integration scope | 95% |

**SIMPLE fields:** id, title, description, scope, files, acceptance_criteria, tests, risk_assessment

**STANDARD adds:** interfaces, io_examples (min 1 error case), error_handling, logging_rules, observability_rules, concurrency, invariants, metadata

**COMPLEX adds:** failure_modes, determinism, resource_safety, edge_case_matrix (10 categories), feature_flags (mandatory)

**Single-scope rule:** Every story has exactly one scope from: skeleton, validation, diff, data, response, integration, observability, coverage, perf, security. Multi-scope features split into multiple stories. Max 10 points, max 3 files per story.

**Over-engineering:** STANDARD at 16 fields is excessive for "normal features". 1060-line story schema is too large for LLM internalization. Sprint planning/velocity targets are scope creep. Edge case matrix duplicated in design, plan, AND check.

---

## 6. Quality & Validation System

### 6.1 P0-P3 Severity Model

| Level | Name | Definition | Merge Gate |
|-------|------|------------|------------|
| P0 | Critical | Security vulns, data loss, race conditions, missing timeouts, hardcoded creds, unbounded ops | Any P0 = BLOCKED |
| P1 | Significant | Missing error coverage, over-mocking, placeholder logic, generic errors, behavioral test gaps | > 2 P1s = BLOCKED |
| P2 | Quality | Generic names, over-commenting, missing types, complexity, dead code | Logged only |
| P3 | Cosmetic | Style, naming conventions, comment formatting | Logged only |

### 6.2 Checklist Inventory

| Checklist | Checks | When Used | Assessment |
|-----------|--------|-----------|------------|
| Plan Quality | ~15 qualitative | After PLAN (STANDARD/COMPLEX) | Best-designed: limits to 3-5 gaps, qualitative |
| Test Quality | 20 | After RED | High-value; targets real AI coding failures |
| Tech Debt | 17 | After GREEN | P0 checks critical; P2/P3 noise |
| AI Slop | 18 | After GREEN | Overlaps Tech Debt on 2 checks. Merge. |
| Story Validation | 47 | Pre-TDD | Over-engineered. Replace with JSON Schema + 10 content checks. |
| Design Validation | 35 | Pre-TDD | Requires 18 sections for everything. Scale by tier. |
| Gap Report Format | N/A (spec) | N/A | Well-designed machine-to-machine format. Keep. |

**Total: ~152 checks.** Shaktra target: ~40-50 covering 80% of real issues.

### 6.3 High-Value Checks Worth Porting

| Check | Severity | Why It Matters |
|-------|----------|----------------|
| Error path coverage | P0 | LLMs frequently skip error paths entirely |
| External calls have timeouts | P0 | Missing timeouts cause cascading production failures |
| No hardcoded credentials | P0 | Security incident if shipped |
| Bounded user input operations | P0 | Prevents DoS via unbounded loops/allocations |
| Hallucinated imports | P0 | LLMs invent library names; code won't even import |
| Missing input validation | P0 | User input flowing to eval/SQL/system calls |
| No mock assertions | P1 | `mock.called` tests prove nothing about behavior |
| Placeholder logic | P1 | TODO/NotImplementedError left in critical paths |
| Generic error messages | P1 | `raise Exception("Failed")` is undebuggable |
| No over-mocking | P1 | Tests with 5+ mocks test nothing real |
| Test isolation | P1 | Shared state causes flaky suites |
| No exception swallowing | P1 | `except: pass` hides real failures |
| Cyclomatic complexity | P2 | Functions with 10+ branches are untestable |
| Over-commenting | P2 | `# Import requests` above `import requests` |
| Tests mirror implementation | P2 | Tests that copy code structure break on refactor |

### 6.4 TDD Implementation

**Flow:** PLAN (test + impl planning) -> RED (write failing tests, guard: `all_tests_red`) -> GREEN (implement to pass, coverage threshold) -> QUALITY REVIEW

**Handoff state machine** (`handoff.yml`): Tracks `current_phase`, `plan_summary`, `test_summary.all_tests_red`, `code_summary.all_tests_green`. Orchestrator reads after every sub-agent return to verify before proceeding.

**Guard tokens:** `TESTS_NOT_RED`, `TESTS_NOT_GREEN`, `PHASE_GATE_FAILED`, `COVERAGE_GATE_FAILED`, `VALIDATION_FAILED` — prompt conventions, not runtime mechanisms. Only hooks provide actual exit-code enforcement.

**What works:** TDD phase ordering via handoff state machine is the single most impactful quality mechanism. Guards prevent the common AI pattern of writing code first.

**What's fragile:** Enforcement entirely within LLM context. Agent self-reports phase completion. No external CI verifies `all_tests_green: true` is actually true. Agent is both developer and quality checker.

### 6.5 Quality System Redundancy

Four components with massive overlap:

| Component | Type | Lines | Role |
|-----------|------|-------|------|
| forge-checker | Agent | 329 | TDD-phase quality gates |
| forge-quality | Agent | 163 | Post-implementation 14-dim review |
| forge-check | Skill | 417 | Gate logic, checklists |
| forge-quality | Skill | 88 | Review severity taxonomy |

A single timeout issue can be flagged **4 times** across different components.

**Unified system for Shaktra:**
```
Single Quality Engine with 2 modes:
  QUICK CHECK (during TDD phases):
    - ~30 highest-impact checks (P0/P1 only)
    - Tier-aware: SIMPLE=10, STANDARD=20, COMPLEX=30
    - Max fix loops: 2
  COMPREHENSIVE REVIEW (final gate):
    - Full check suite, tier-aware dimensions
    - Coverage verification, decision consolidation
    - Skip: independent verification tests (same-model bias)
```

---

## 7. State, Memory & Tooling

### 7.1 State Files

| File | Format | Purpose | Useful? |
|------|--------|---------|---------|
| `forge/settings.yml` | YAML | Coverage thresholds, quality toggles, learning config | Yes |
| `forge/memory/project.yml` | YAML | Sprint tracking, story registry, velocity | Yes (drop sprint/velocity) |
| `forge/memory/important_decisions.yml` | YAML | Architectural decisions log | Yes |
| `forge/.tmp/{story}/handoff.yml` | YAML | Per-story TDD state machine | Yes — essential |
| `forge/memory/learning/events.jsonl` | JSONL | Raw workflow event stream | No — file doesn't exist |
| `forge/memory/learning/patterns.yml` | YAML | Discovered patterns library | No — empty |
| `forge/memory/learning/pattern_performance.yml` | YAML | Pattern accuracy tracking | No — empty |

**decisions.yml schema (summarized):**
```yaml
decisions:
  - id: ID-001
    story_id: ST-001
    title: "Email validation timeout"
    summary: "DNS lookups must timeout..."
    categories: [reliability, performance]    # 1-3 from 14 allowed
    guidance: ["DNS lookups MUST have 5s timeout"]  # 1-5 rules
    status: active    # active | superseded (append-only, never delete)
```

**Lifecycle:** CAPTURE (during TDD) -> CONSOLIDATE (quality gate promotes to decisions.yml) -> APPLY (future stories reference) -> SUPERSEDE (new decision replaces old).

### 7.2 Learning System Assessment

**What it tried:** 3-layer pipeline (event logging -> pattern analysis -> guidance injection). 6 Python scripts (~1,500 lines), dedicated agent, 20+ event types, 5 pattern categories, auto-approval thresholds, accuracy tracking.

**Why it failed:** Zero usage (all data files empty). Threshold mismatch (needs 15+ events for auto-approve). Premature complexity (built gzip archival and trend detection with zero data). Import bugs. Only 3 of 5 pattern types implemented.

**Replacement for Shaktra:** Single `lessons_learned.yml` file. Agents append lessons during work, read before starting new tasks. LLM's own pattern matching replaces 1,500 lines of Python. Add size cap (100 entries, archive rest).

### 7.3 Hooks & Tooling Inventory

| Name | What It Does | Active? | Platform Issues | Shaktra |
|------|-------------|---------|-----------------|---------|
| `block-main-branch.sh` | Blocks Bash ops on main/master/prod | Yes | Minor cosmetic bug | **Keep** |
| `validate-story-alignment.sh` | Warns editing files outside story scope | Yes (warn-only) | `grep -oP` breaks macOS | **Rethink** — block or remove |
| `validate-story.py` | Validates story schema by tier | Not configured | None | **Keep concept, simplify** |
| `check-p0-findings.py` | Blocks agent stop if P0 findings exist | Not configured | None | **Keep and wire up** |
| `ci/pre-commit.sh` | Lint + type check + test collection | Manual install | Test step is no-op | **Simplify** |
| `ci/pre-push.sh` | Full tests + coverage + security scan | Manual install | None | **Keep** |
| `forge-statusline.sh` | Status display: `ST-001 [GREEN] 87%` | Not configured | macOS grep issue | **Drop** |
| Learning scripts (5 files) | Event logging, pattern analysis pipeline | Never called | Import bugs | **Drop all** |
| `lock.py` | No-op context manager stub | N/A | None | **Drop** |

**Permission model worth replicating:**
```json
Deny: "Read(.env*)", "Read(**/credentials*)", "Read(**/*secret*)", "Bash(rm -rf:*)"
Allow: "Bash(pytest:*)", "Bash(git:*)", "Bash(python .claude/hooks/*.py:*)"
```
**Pitfall:** Never add `Bash(python:*)` in local settings — it's unrestricted execution.

### 7.4 MCP Servers

Both `forge-github` (Node.js) and `forge-ci` (Python) are non-functional stubs with `disabled: true`. Neither has any implementation.

**Recommendation:** Do not build custom MCP servers. Claude Code's `gh` CLI covers 90% of GitHub needs. CI integration via `gh run view`/`gh run list`. Only build MCP if a specific gap emerges later.

---

## 8. Problems: Redundancy, Bloat & Gaps

### 8.1 Redundancy Map

**Quality quadruple overlap:** 4 components (checker agent, quality agent, check skill, quality skill) with P0-P3 taxonomy duplicated across 6 files. Merge gate pseudocode verbatim in 4 files.

**Rule-skill duplication:** Every rule condenses content from its corresponding skill(s). Changes require updating 2+ files in sync.

**Agent-skill duplication:** Every agent re-explains content its loaded skill already provides (e.g., forge-developer 205 lines restates forge-tdd 139 lines).

**Cross-agent testing overlap:** forge-developer writes/runs tests, forge-test-engineer advises on testing (never invoked), forge-checker validates test quality.

**Config value duplication:** Coverage threshold `90` in 5 places with hardcoded fallbacks.

**Protocol duplication:** `CLARIFICATION_NEEDED` format copy-pasted into 5 agent files.

### 8.2 Bloat Assessment

| Category | Files | Lines | % |
|----------|-------|-------|---|
| Active framework | 174 | 52,655 | 57.5% |
| Dead code (`_to_be_deleted/`) | 97 | 37,057 | 40.5% |
| Config/docs at root | ~10 | ~1,834 | 2% |
| **Total** | **271** | **91,546** | **100%** |

82% is markdown prompts. Full pipeline per story: 11 phases, 4 quality gates, ~12 sub-agent spawns, ~150,000+ tokens. **For a SIMPLE story, this is absurd overkill.**

### 8.3 Architecture Anti-Patterns

1. **God file** — forge-workflow/SKILL.md at 1,481 lines, repeats GATES table 4x
2. **Circular knowledge deps** — forge-reference -> world-class-standard -> forge-quality -> forge-reference
3. **Leaky abstractions** — orchestrator says "never implement" but has 7 inline implementations
4. **Tight coupling via shared schema** — story YAML changes require updating 6+ files
5. **Settings fragmentation** — same threshold in 5 places, "fallback to hardcoded" pattern
6. **Naming anti-patterns** — "check" vs "quality" are near-synonyms for different functions
7. **Misplaced files** — practice files under forge-tdd but apply to all development
8. **Internal redundancy** — key tables/rules repeated multiple times within same file
9. **Cargo-cult prompting** — "Principal Engineer" persona in 7 of 12 agents adds no value

### 8.4 Missing Capabilities

**Critical:**
- No error recovery/debugging (sub-agent failure = retry once then stop)
- No incremental workflow (can't do single-file change without full ceremony)
- No rollback (advertised but unimplemented)

**Important:**
- No real Git integration (PR creation, commit formatting, changelog)
- No multi-language parity (check scripts are Python-only pattern matchers)
- No framework observability (can't measure duration, failure rates, token consumption)
- No settings validation (invalid config silently uses defaults)

**Nice-to-have:**
- No interactive debugging
- No selective practice loading
- No PR-based workflow (framework ends at code quality)

### 8.5 Maintainability Scorecard

| Component | Score | Key Issue |
|-----------|-------|-----------|
| CLAUDE.md | 8/10 | Minor: doubles as template |
| forge-reference skill | 7/10 | Well-structured shared reference |
| forge-design skill | 7/10 | Small, well-scoped |
| forge-quality skill | 6/10 | Slim (88 lines), good factoring |
| forge-analyze skill | 6/10 | Clean 13-phase structure |
| forge-plan skill | 6/10 | Clean sub-files |
| forge-checker agent | 5/10 | Duplicates skill at 329 lines |
| forge-developer agent | 5/10 | Duplicates tdd skill |
| forge-planner agent | 5/10 | Story schema changes cascade |
| forge-check skill | 5/10 | Repeats gate logic |
| forge-tdd skill | 5/10 | Good SKILL.md but 24 sub-files as baggage |
| Rules (5 files) | 4/10 | Duplicate skill content |
| Hooks | 4/10 | 2 active, 4 orphaned |
| forge-product-manager | 3/10 | 502 lines, 5 workflows, scope creep |
| Configuration files | 3/10 | 12 files, 3 formats, overlapping values |
| orchestrate.md | 3/10 | 962 lines of pseudo-code |
| forge-workflow SKILL.md | 2/10 | 1,481-line monolith, 4x repetition |
| forge-test-engineer | 2/10 | Orphaned, duplicates 2 agents |
| Learning system | 1/10 | 5 scripts, never worked |
| _to_be_deleted | 0/10 | 97 files of dead weight |
| **Weighted Average** | **~4.5/10** | |

---

## 9. Shaktra Design Guidance

### 9.1 Architecture Lessons

**Layering:**
- Define each config value exactly once. Reference from everywhere else.
- Rules = routers (<30 lines). Skills = instructional content (single source of truth). Agents = thin wrappers (~50 lines).
- Separate Claude Code infra config (settings.json) from app config (state/project.yml). Never overlap.

**Orchestration:**
- Scale ceremony to complexity. SIMPLE != 12 sub-agent invocations.
- Orchestrator under 500 lines. State machine, not god file.
- Version agent definitions alongside orchestration templates.
- Single handoff format, explicit schema, validated by hook.

**Quality:**
- One quality system with modes (fast gate vs deep review). Not four overlapping components.
- Enforce via hooks (external), not just prompts. Every critical rule needs a hook backing it.
- Wire up every hook or delete it. Dead hooks = false sense of safety.

**Agents:**
- Don't create agents for already-covered capabilities. Merge overlapping agents.
- Language specialists should be rules or reference skills, not agents.
- One agent owns each shared artifact. Others read, not write.
- Model selection explicit and justified per agent.

**Context:**
- Budget total instructions to <30K tokens (Forge loads 150K+).
- Load only what current phase needs. Precise globs, explicit skill loading.
- Cap skills at 300 lines each.

**DX:**
- Cross-platform from day one. No `grep -oP`, no undeclared deps.
- Dogfood: Shaktra's repo must run under Shaktra's rules.
- README validated or auto-generated.

**State:**
- 2-3 state files max. No dead data files.
- Template drift detection (version field comparison).

### 9.2 Workflow & Skills Lessons

**Ceremony proportional to complexity:**

| Tier | Story Fields | Pipeline | Overhead Target |
|------|-------------|----------|-----------------|
| Trivial | None. Just describe -> implement -> verify. | No YAML | <2 min |
| Small | 4-5 fields (title, description, scope, AC, files) | Skip plan gate | <5 min |
| Medium | + interfaces, test specs, error handling | Test quality gate | <15 min |
| Large | + failure modes, edge cases, feature flags | All gates | Full pipeline |

**Skill design rules:**
- Max 300 lines per instruction file
- Separate spec from instructions (schema reference != execution template)
- Centralize shared logic once (artifact loading, guard tokens, quality taxonomy)
- Skills should be stateless — state layer is separate
- Every skill declares its context budget

**Orchestrator design:**
- Thin orchestrator (classify intent, delegate, enforce gates) — everything else is separate skills
- Intent routing needs confirmation for ambiguous cases
- Quality gates configurable per project

**Quality gate strategy:**
- 2-3 gates max for standard work
- False positive handling mandatory ("accepted risk" must be a real option)
- Fix loops cap at 2, not 3
- Separate structural from behavioral checks

**State:** Single state file per work unit. Append-only event log separate from active state. Atomic transitions.

**What to keep:** YAML-as-contract, guard tokens, tiered complexity (4 tiers), create-check-fix loop (cap at 2), handoff state machine, decisions as cross-story memory, error-resolver's replay system, fresh agent per task, adversarial spec review.

**What to drop:** Self-learning system, PM as workflow interceptor, PE Review (LLM self-critique), 13-phase codebase analysis (do targeted instead), sprint planning/velocity, dashboard rendering system, version tracking in template files, 31 "world-class" principles (distill to 10).

**The 10 Shaktra Quality Principles** (replacing Forge's 31):
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

### 9.3 Quality & Tooling Lessons

**What checks matter:** P0 checks are the core (timeouts, creds, unbounded ops, hallucinated imports). Test quality gate before implementation is high-leverage. Coverage thresholds are a useful floor. The Evidence Rule ("where is the proof?") is the best single principle. Everything beyond ~40 checks is diminishing returns.

**External enforcement:** Use real hooks with real exit codes. Either block or don't check (no warn-only). Run actual test commands, not self-reported status. Use Python for YAML/JSON parsing (never bash grep). Declare all dependencies. Provide a setup command (`shaktra init`).

**State to persist:** Per-task working state (handoff equivalent), project decisions (append-only, committed to git), project settings (rarely changed), lessons learned (simple YAML, LLM reads before work). Drop: sprint/velocity, event logging, pattern analysis, pattern performance.

**Build priorities:**
1. TDD state machine as structural backbone
2. Single quality engine with quick-check and comprehensive modes
3. ~35 checks organized by severity, tier-aware
4. Hooks that actually block: branch protection, P0 on stop, schema validation
5. Python for all hooks, never `grep -oP`
6. Persist: settings, decisions, lessons-learned, per-task handoff. Nothing else.
7. Guard tokens: reduce from 40+ to ~15 core tokens
8. Skip MCP servers. Use `gh` CLI.

### 9.4 Top 20 Recommendations

1. **Single quality component** — merge 4 into 1 with modes. ~50% quality content reduction.
2. **Strict layering** — rules route (<20 lines), skills define, agents delegate (~50 lines). Zero duplication.
3. **Orchestrator under 200 lines** — intent classification + routing only. Gates/loops/handlers in separate files.
4. **Mandatory fast path** — auto-detect small changes: no story YAML, no plan gate, no PM UAT. Tests -> code -> check -> done.
5. **Zero dead code** — never ship `_to_be_deleted/`. Git history for reference. Orphan detection in CI.
6. **Single source of truth** — severity in 1 file, dimensions in 1 file, thresholds in 1 file. Everything else references.
7. **Selective context loading** — detect relevant practices from story content, load only those. ~60% token cut.
8. **3 config files max** — platform (settings.json), framework (one YAML), state (one YAML). Schema validation on startup.
9. **Error recovery with phase resume** — track completed phases, allow resume from last success.
10. **Working rollback** — if advertised, it must work. Via handoff state + git restore.
11. **Replace learning system** — append-only `lessons.yml`. 80% value at 5% complexity.
12. **Consistent naming** — `shaktra-{domain}` prefix. Names distinguish function: gates vs review.
13. **Shared protocols in one file** — CLARIFICATION_NEEDED, handoff schema, severity taxonomy. One canonical source.
14. **Reduce story schema** — SIMPLE: 5 fields. STANDARD: 10. COMPLEX: full spec. Fields only when applicable.
15. **Real Git integration** — PR creation, commit formatting, branch naming. Working features, not stubs.
16. **Multi-language checks** — language-agnostic or per-language adapters. Not Python-only matchers.
17. **`/shaktra doctor` command** — validates all files exist, configs parse, hooks executable, no circular refs.
18. **State once, reference everywhere** — critical instructions appear exactly once at the needed point. No 4x repetition.
19. **No ASCII art in prompts** — text descriptions only. LLMs process sequentially; diagrams waste tokens.
20. **Observability from day one** — track duration, failure rates, gate pass rates, token estimates.

### 9.5 Must Not Repeat Checklist

Use during Shaktra development. Each item is a concrete Forge mistake.

- [ ] No single file over 300 lines
- [ ] No content duplication across layers (if skill defines it, agent must not restate it)
- [ ] No dead code in repo (no `_to_be_deleted`, no disabled stubs, no orphaned hooks)
- [ ] No features advertised but not implemented
- [ ] No severity taxonomy in more than one file
- [ ] No hardcoded fallback values in agent files (fail loudly on missing config)
- [ ] No cargo-cult personas ("Principal Engineer" adds nothing)
- [ ] No ASCII art in LLM prompts
- [ ] No internal repetition within files (rule stated once, not 4x)
- [ ] No agents with overlapping scope
- [ ] No 12-file configuration sprawl (3 max, one format, schema-validated)
- [ ] No loading all practices for every task (detect relevant, load only those)
- [ ] No full ceremony for small changes (fast path must be default for low-complexity)
- [ ] No scripts scattered across 5+ directories
- [ ] No skill-specific directories for globally-applicable practices
- [ ] No hooks that are no-ops (hooks must enforce or be removed)
- [ ] No over-engineered subsystems (YAML file > 5 Python scripts if value is equal)
- [ ] No naming ambiguity between components ("gates" vs "review", not "check" vs "quality")
- [ ] No circular reference chains between components
- [ ] No warn-only validations (block or remove)
