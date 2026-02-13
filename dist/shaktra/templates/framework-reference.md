# Shaktra Framework Reference

This project uses the **Shaktra** development framework — an opinionated workflow with TDD, quality gates, and multi-agent orchestration.

For complete user guide, installation, and usage: see the plugin README.md that comes with Shaktra.

## Available Commands

| Command | Purpose |
|---|---|
| `/shaktra:tpm` | Technical Project Manager — design docs, user stories, sprint planning |
| `/shaktra:dev` | Developer — TDD implementation (PLAN → RED → GREEN → QUALITY → MEMORY) |
| `/shaktra:review` | Code Reviewer — PR reviews, 13-dimension quality checks, verification tests |
| `/shaktra:analyze` | Analyzer — brownfield codebase analysis (9 dimensions) |
| `/shaktra:bugfix` | Bug Diagnostician — 5-step diagnosis, root cause analysis, TDD remediation |
| `/shaktra:general` | Domain Expert — architectural guidance, technical questions |
| `/shaktra:init` | Initialize Shaktra (already done) |
| `/shaktra:doctor` | Health check — diagnose framework and configuration issues |
| `/shaktra:workflow` | Smart router — auto-route to right agent based on intent |
| `/shaktra:help` | Help — commands, workflows, usage guide |

## State Structure

Framework state is stored in the `.shaktra/` directory:

```
.shaktra/
├── settings.yml                    # Project configuration and thresholds
├── sprints.yml                     # Sprint tracking and velocity
├── framework-reference.md          # This file — Shaktra framework docs
├── memory/
│   ├── decisions.yml              # Architectural decisions (append-only)
│   └── lessons.yml                # Lessons learned (append-only)
├── stories/                       # User story files (ST-XXX.md)
├── designs/                       # Design documents
├── analysis/                      # Codebase analysis outputs (brownfield)
└── pm/                           # PM artifacts (brainstorm, personas, etc.)
```

## TDD State Machine

Every story follows this state machine:

```
PLAN (test plan + skeleton)
  ↓ [quality gate]
RED (write failing tests)
  ↓ [quality gate]
GREEN (pass all tests)
  ↓ [quality gate]
QUALITY (fix findings, improve coverage)
  ↓ [quality gate]
MEMORY (document decisions, lessons)
  ↓ [quality gate]
COMPLETE (ready for review)
```

Each transition requires passing quality checks (36 checks per gate). P0 findings block progress.

## Quality Tiers

### SW Quality (Story-Level)
- **When:** During `/shaktra:dev` at each state transition
- **What:** 36 checks across 8 dimensions
- **Blocks:** P0 findings block transition to next state
- **Thresholds:** Vary by story tier (XS: 70%, S: 80%, M: 90%, L: 95%)

### Code Review (App-Level)
- **When:** After story completion via `/shaktra:review`
- **What:** 13 review dimensions (Contract, Failure Modes, Data Integrity, Security, etc.)
- **Blocks:** P0 blocks merge; P1 count subject to threshold
- **Verification:** Independent tests validate behavior

## Severity Taxonomy (P0-P3)

**P0 — Critical:** Causes data loss, security breach, or unbounded resource consumption
- Must be fixed before any merge
- Examples: SQL injection, hardcoded credentials, unbounded loops

**P1 — Major:** Incorrect behavior, missing error handling, inadequate coverage
- Allowed up to threshold (see settings.yml)
- Examples: Coverage below threshold, missing error path, off-by-one error

**P2 — Moderate:** Code quality, maintainability, observability gaps
- Does not block merge
- Examples: Missing docstring, code duplication, inconsistent formatting

**P3 — Minor:** Style, naming, documentation
- Does not block merge
- Examples: Variable naming, import ordering, trailing whitespace

## Story Tiers & Ceremony

Process scales with complexity:

| Tier | Points | Coverage | Ceremony | Use For |
|---|---|---|---|---|
| **XS** | 1-2 | 70% | Minimal | Hotfixes, trivial changes |
| **S** | 3-5 | 80% | Light | Small features, bug fixes |
| **M** | 8-13 | 90% | Standard | Medium features, refactoring |
| **L** | 20+ | 95% | Full | Large features, architecture changes |

## Configuration (settings.yml)

Key configurable values:

```yaml
tdd:
  coverage_threshold: 90           # Default coverage for normal stories
  hotfix_coverage_threshold: 70    # For hotfixes (XS tier)
  small_coverage_threshold: 80     # For S tier
  large_coverage_threshold: 95     # For L tier

quality:
  p1_threshold: 2                  # Max P1 findings before merge block

review:
  min_verification_tests: 5        # Independent tests per review
  verification_test_persistence: ask  # Keep tests? (ask/auto/always/never)

sprints:
  enabled: true
  velocity_tracking: true
  sprint_duration_weeks: 2
  default_velocity: 15             # Story points per sprint
```

## Hooks: Automated Enforcement

Four blocking hooks enforce constraints automatically:

| Hook | Triggers | Blocks |
|---|---|---|
| **block-main-branch** | Bash (git ops) | Operations on main/master/prod |
| **validate-story-scope** | Write/Edit | File changes outside story scope |
| **validate-schema** | Write/Edit (YAML) | Files not matching Shaktra schemas |
| **check-p0-findings** | Stop (on finish) | Completion with unresolved P0s |

## Workflows

### TPM Workflow (Design → Stories → Sprint)
1. Describe feature request
2. TPM creates design doc with architecture, API, data models
3. TPM breaks into stories with acceptance criteria
4. TPM schedules sprint based on velocity
5. Implement stories via `/shaktra:dev`

### Dev Workflow (TDD Implementation)
1. Read story from `.shaktra/stories/ST-XXX.md`
2. PLAN: Test plan + skeleton code
3. RED: Write failing tests
4. GREEN: Write code to pass tests
5. QUALITY: Fix findings, improve coverage
6. MEMORY: Document decisions, lessons
7. COMPLETE: Ready for `/shaktra:review`

### Review Workflow (13-Dimension Quality)
1. Code Reviewer analyzes all 13 dimensions
2. Verification tests (≥5) independently validate behavior
3. Findings categorized as P0/P1/P2/P3
4. P0 blocks merge, P1 subject to threshold
5. Approved → Ready to merge

### Analysis Workflow (Brownfield Assessment)
1. Run `/shaktra:analyze` on existing codebase
2. Outputs findings across 9 dimensions (Architecture, Testing, Code Quality, Security, etc.)
3. Results stored in `.shaktra/analysis/`
4. Use findings to plan refactoring and feature work

### Bug Fix Workflow (5-Step Diagnosis)
1. **Triage** — Is this real? Reproducible? Severity?
2. **Reproduce** — Create minimal test case
3. **Root Cause** — Identify the bug location and cause
4. **Blast Radius** — What else could this affect?
5. **Create Story** — Write story with test, route to `/shaktra:dev`

## Design Philosophy

- **Prompt-driven, not script-driven** — Agents are markdown prompts, leveraging Claude's native tools
- **No file over 300 lines** — Complexity stays manageable
- **Single source of truth** — Severity taxonomy, quality dimensions, schemas defined once
- **Hooks block or don't exist** — No warn-only. If it matters, it's enforced.
- **Ceremony scales with complexity** — XS → minimal, L → full architecture review
- **Read-only diagnostics** — `/shaktra:doctor` reports, never auto-modifies

## Key Resources

- **User guide:** Plugin README.md (from Shaktra installation)
- **Decisions:** `.shaktra/memory/decisions.yml` — Append architectural decisions here
- **Lessons:** `.shaktra/memory/lessons.yml` — Append team learnings here
- **Settings:** `.shaktra/settings.yml` — Adjust thresholds and configuration
- **Project guide:** `CLAUDE.md` — Project-specific context, conventions, architecture
