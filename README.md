# Shaktra

**Opinionated software development framework for Claude Code.**

Shaktra is a Claude Code plugin that orchestrates 12 specialized AI agents through agile-inspired workflows to produce industry-standard, production-quality code.

| | |
|---|---|
| **Version** | 0.1.0 |
| **License** | MIT |
| **Agents** | 12 specialized sub-agents |
| **Skills** | 14 total (10 user-invocable) |
| **Quality** | 36 checks per TDD gate, 13 review dimensions |

---

## What is Shaktra?

Shaktra turns Claude Code into a full software development team. Instead of a single assistant, you get specialized agents — a TPM, architect, developer, test engineer, quality reviewer, and more — each with deep domain expertise, working together through structured workflows.

**Five pillars:**

1. **TDD-first development** — tests are written before code, always
2. **Multi-agent orchestration** — 12 specialized agents, each with a distinct role
3. **Quality gates at every phase** — P0-P3 severity taxonomy with automated enforcement
4. **Sprint-based planning** — velocity tracking, capacity allocation, backlog management
5. **Ceremony scaling** — story tiers (XS/S/M/L) determine how much process each task gets

Quality enforcement is built into the workflow, not bolted on. Every code change passes through story-level quality checks during TDD and app-level review after completion. P0 findings block merge — no exceptions.

---

## How It Works

![Shaktra Architecture](Resources/workflow.drawio.png)

Shaktra uses a layered agent system where **skills orchestrate** and **agents execute**:

- **TPM** receives a feature request → dispatches Architect, Scrummaster, Product Manager
- **Dev Manager** receives a story → orchestrates SW Engineer, Test Agent, Developer through TDD
- **Code Reviewer** receives completed work → runs 13-dimension review with independent verification tests
- **Codebase Analyzer** receives a brownfield project → executes 9-dimension parallel analysis

Two quality tiers operate at different scopes:

- **SW Quality** checks story-level quality during TDD (36 checks per gate)
- **Code Reviewer** checks app-level quality after completion (13 dimensions)

Every implementation follows a strict TDD state machine: **PLAN → RED → GREEN → QUALITY → MEMORY → COMPLETE**. Quality gates must pass at each transition — there are no shortcuts.

---

## Installation

### Marketplace (recommended)

```
/plugin marketplace add https://github.com/im-shashanks/claude-skills.git
/plugin install shaktra@claude-skills-marketplace
```

### Direct from GitHub

```
/plugin install https://github.com/im-shashanks/claude-skills.git
```

### Local development

```
# Quick iteration (skips install pipeline)
claude --plugin-dir shaktra/

# Full install from local path
/plugin install /absolute/path/to/claude-skills/shaktra
```

---

## Quick Start

### Greenfield project

1. **Initialize** — `/shaktra:init` to create `.shaktra/` config and project structure
2. **Plan** — `/shaktra:tpm` to create a design doc, break it into user stories, and plan your sprint
3. **Build** — `/shaktra:dev ST-001` to implement stories with TDD (PLAN → RED → GREEN → QUALITY)
4. **Review** — `/shaktra:review ST-001` to run a 13-dimension code review with verification tests

### Brownfield project

1. **Initialize** — `/shaktra:init` (select "brownfield")
2. **Analyze** — `/shaktra:analyze` to assess the existing codebase across 9 dimensions
3. **Plan and build** — same as greenfield, informed by analysis results

### Hotfix

```
/shaktra:tpm hotfix: <description of the issue>
```

Creates a hotfix story and routes directly to development. Minimal ceremony, 70% coverage threshold.

### Bug fix

```
/shaktra:bugfix <bug description or error message>
```

Runs 5-step diagnosis (triage → reproduce → root cause → blast radius → story) then TDD remediation.

---

## Commands

### Workflow Commands

| Command | Agent | Purpose |
|---|---|---|
| `/shaktra:tpm` | Technical Project Manager | Design docs, user stories, sprint planning, hotfixes |
| `/shaktra:dev` | Dev Manager | TDD implementation — PLAN → RED → GREEN → QUALITY |
| `/shaktra:review` | Code Reviewer | Story reviews, PR reviews, 13-dimension quality checks |
| `/shaktra:analyze` | Codebase Analyzer | Brownfield codebase analysis (9 dimensions) |
| `/shaktra:bugfix` | Bug Fix Lead | Bug diagnosis (5-step) + TDD remediation |
| `/shaktra:general` | Domain Expert | Domain expertise, architectural guidance, technical questions |

### Utility Commands

| Command | Purpose |
|---|---|
| `/shaktra:init` | Initialize Shaktra in a project (creates `.shaktra/`) |
| `/shaktra:doctor` | Diagnose framework health — plugin structure, config, constraints |
| `/shaktra:workflow` | Natural language router — describe what you need, get routed to the right agent |
| `/shaktra:help` | Show all commands, workflows, architecture, and usage guide |

---

## Configuration

All thresholds and settings live in `.shaktra/settings.yml` — nothing is hardcoded in the plugin.

| Setting | Default | Controls |
|---|---|---|
| `tdd.coverage_threshold` | 90% | Minimum test coverage for stories |
| `tdd.hotfix_threshold` | 70% | Coverage for hotfix stories |
| `quality.p1_threshold` | 2 | Max P1 findings before merge block |
| `review.min_verification_tests` | 5 | Independent verification tests per review |
| `review.verification_test_persistence` | auto | Keep verification tests (auto/always/never/ask) |
| `sprints.sprint_duration_days` | 14 | Sprint length |
| `sprints.default_velocity` | — | Story points per sprint (estimated at init) |

Story tiers (XS/S/M/L) automatically scale process ceremony — trivial stories get 70% coverage with minimal process; large stories get 95% coverage with full architecture review.

---

## Enforcement

Four blocking hooks enforce constraints automatically:

| Hook | Blocks |
|---|---|
| **block-main-branch** | Git operations on main/master/prod |
| **validate-story-scope** | File changes outside the current story's scope |
| **validate-schema** | YAML files that don't match Shaktra schemas |
| **check-p0-findings** | Completion when unresolved P0 findings exist |

Hooks are all-or-nothing — they block or they don't exist. No warn-only mode.

---

## Design Philosophy

- **Prompt-driven, not script-driven** — agents and skills are markdown prompts, not Python scripts. The plugin leverages Claude's native tools (Glob, Read, Grep, Bash) instead of reimplementing them.
- **No file over 300 lines** — complexity stays manageable, every file has a single clear purpose.
- **Single source of truth** — severity taxonomy, quality dimensions, and schemas are defined once in the reference skill and referenced everywhere else.
- **Hooks block or don't exist** — no warn-only hooks. If a constraint matters, it's enforced.
- **Ceremony scales with complexity** — XS stories skip design docs; L stories get full architecture review. The framework adapts to the task.
- **Read-only diagnostics** — `/shaktra:doctor` reports problems but never fixes them. The user stays in control.

---

## License

MIT License. See [LICENSE](LICENSE).

## Documentation

Architecture docs, phase plans, and Forge analysis are in [`docs/`](docs/).
