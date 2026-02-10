---
name: shaktra-help
description: >
  Comprehensive guide to Shaktra — lists all commands, explains workflows,
  describes the agent architecture, and provides getting-started instructions.
user-invocable: true
---

# /shaktra:help — Shaktra Guide

You are the Shaktra help system. When invoked, present the guide below **verbatim**. Do not add, omit, or rephrase sections. Use the markdown exactly as written. If the user appends a topic after the command (e.g., `/shaktra:help tpm`), present only the section most relevant to that topic.

---

## Full Guide

### Shaktra — Software Development Framework for Claude Code

Shaktra orchestrates 12 specialized AI agents through agile-inspired workflows. Every code change follows TDD, passes quality gates, and is reviewed before merge.

**Core pillars:** TDD-first | Multi-agent orchestration | Quality gates (P0-P3) | Sprint planning | Ceremony scaling

---

### Commands

#### Workflow Commands

| Command | What It Does |
|---|---|
| `/shaktra:tpm` | Design docs, user stories, sprint planning, hotfixes. The starting point for new features. |
| `/shaktra:dev ST-###` | TDD implementation of a story — PLAN → RED → GREEN → QUALITY. |
| `/shaktra:review ST-###` | Story-level or PR-level code review across 13 quality dimensions. |
| `/shaktra:analyze` | Brownfield codebase analysis across 9 dimensions with parallel deep analysis. |
| `/shaktra:bugfix <desc>` | Bug diagnosis (5-step) followed by TDD remediation. |
| `/shaktra:general` | Domain expertise, architectural guidance, technical questions. |

#### Utility Commands

| Command | What It Does |
|---|---|
| `/shaktra:init` | Initialize `.shaktra/` project structure — settings, memory, stories, designs. |
| `/shaktra:doctor` | Read-only health check — validates plugin structure, config, and constraints. |
| `/shaktra:workflow` | Natural language router — describe what you need, get dispatched to the right skill. |
| `/shaktra:help` | This guide. |

---

### Workflows

#### Greenfield Project

```
1. /shaktra:init              → create project config
2. /shaktra:tpm               → design doc → user stories → sprint plan
3. /shaktra:dev ST-001        → TDD: PLAN → RED → GREEN → QUALITY
4. /shaktra:review ST-001     → 13-dimension code review + verification tests
```

#### Brownfield Project

```
1. /shaktra:init              → create project config (select brownfield)
2. /shaktra:analyze           → 9-dimension codebase assessment
3. /shaktra:tpm               → plan improvements informed by analysis
4. /shaktra:dev / review      → implement and review as above
```

#### Hotfix (Fast Path)

```
/shaktra:tpm hotfix: users can't log in after the OAuth migration
```

Creates a trivial-tier story and routes directly to `/shaktra:dev`. Minimal ceremony, 70% coverage threshold.

#### Bug Fix

```
/shaktra:bugfix TypeError: Cannot read property 'id' of undefined in checkout flow
```

Runs 5-step diagnosis — triage → reproduce → root cause → blast radius → story creation — then TDD remediation.

---

### Agent Architecture

Shaktra uses a layered system where **skills orchestrate** and **agents execute**:

```
User
 │
 ├─ /shaktra:tpm ──────→ Architect, Scrummaster, Product Manager, TPM Quality
 │
 ├─ /shaktra:dev ──────→ SW Engineer, Test Agent, Developer, SW Quality
 │
 ├─ /shaktra:review ───→ CR Analyzer (4 parallel dimension groups)
 │
 ├─ /shaktra:analyze ──→ CBA Analyzer (9 parallel dimensions)
 │
 ├─ /shaktra:bugfix ───→ Bug Diagnostician → then reuses Dev pipeline
 │
 └─ /shaktra:general ──→ (no sub-agents — direct domain expertise)
```

**Two-tier quality system:**

- **SW Quality** — story-level checks during TDD. 36 checks per gate (PLAN/RED/GREEN).
- **Code Reviewer** — app-level review after completion. 13 dimensions + independent verification tests.

**Severity taxonomy:**

| Severity | Effect | Examples |
|---|---|---|
| P0 Critical | Merge blocker | Credentials in code, SQL injection, unbounded operations |
| P1 Significant | Threshold-based (default: max 2) | Missing error handling, over-mocking, placeholder code |
| P2 Quality | Logged, non-blocking | High complexity, poor naming, dead code |
| P3 Cosmetic | Logged, non-blocking | Style inconsistencies, formatting |

---

### TDD Pipeline

Every story implementation follows this state machine:

```
PLAN ──→ RED ──→ GREEN ──→ QUALITY ──→ MEMORY ──→ COMPLETE
  │        │        │         │
  ▼        ▼        ▼         ▼
 SW       SW       SW        SW
Quality  Quality  Quality   Quality
 gate     gate     gate    (comprehensive)
```

- **PLAN** — SW Engineer creates implementation + test plan
- **RED** — Test Agent writes failing tests (behavioral, story-scoped)
- **GREEN** — Developer implements code to make tests pass and hit coverage
- **QUALITY** — SW Quality runs comprehensive 14-dimension review
- **MEMORY** — Memory Curator captures lessons to `.shaktra/memory/lessons.yml`

---

### Story Tiers

Process ceremony scales with story complexity:

| Tier | Coverage | Design Doc | Quality Gates |
|---|---|---|---|
| Trivial (XS) | 70% | Skip | Minimal |
| Small (S) | 80% | Skip | Code gate only |
| Medium (M) | 90% | Required | All gates |
| Large (L) | 95% | Required | Thorough gates |

Tiers are assigned during story creation based on scope, file count, and cross-cutting concerns.

---

### Configuration

All settings live in `.shaktra/settings.yml` — nothing is hardcoded.

| Setting | Default | What It Controls |
|---|---|---|
| `tdd.coverage_threshold` | 90% | Minimum test coverage |
| `tdd.hotfix_threshold` | 70% | Coverage for hotfix stories |
| `quality.p1_threshold` | 2 | Max P1 findings before merge block |
| `review.min_verification_tests` | 5 | Independent verification tests per review |
| `review.verification_test_persistence` | auto | Keep verification tests (auto/always/never/ask) |
| `sprints.sprint_duration_days` | 14 | Sprint length |

Run `/shaktra:doctor` after changing settings to validate your configuration.

---

### Hooks (Automated Enforcement)

Four blocking hooks enforce constraints without manual intervention:

| Hook | What It Blocks |
|---|---|
| **block-main-branch** | Git operations directly on main/master/prod |
| **validate-story-scope** | File changes outside the current story's scope |
| **validate-schema** | YAML files that don't match Shaktra schemas |
| **check-p0-findings** | Completion when unresolved P0 findings exist |

Hooks are all-or-nothing — they block or they don't exist. No warn-only mode.

---

### Tips

- **Start with `/shaktra:workflow`** if unsure which command to use — it routes based on natural language.
- **Run `/shaktra:doctor`** after init to verify everything is configured correctly.
- **Story IDs matter** — `/shaktra:dev ST-001` knows exactly which story to implement.
- **Hotfixes are fast** — `/shaktra:tpm hotfix: ...` skips ceremony and routes straight to dev.
- **Memory persists** — lessons are captured in `.shaktra/memory/lessons.yml` and inform future work.
- **Ceremony scales** — trivial stories skip design docs; large stories get full architecture review.
- **Two quality reviewers** — SW Quality checks during TDD, Code Reviewer checks after completion. They are intentionally separate.
