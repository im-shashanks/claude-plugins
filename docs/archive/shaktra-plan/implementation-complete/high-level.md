# Shaktra Framework — High-Level Reference

> **Load this file into any Claude Code session** to provide context about what Shaktra is, why it exists, and how it works.
> Last updated: 2026-02-06

---

## What Is Shaktra

Shaktra is a **Claude Code plugin** that provides an opinionated software development framework. It orchestrates specialized AI agents through agile-inspired workflows to produce industry-standard, reliable, production code.

**Distribution:** Installed via `/plugin install shaktra@marketplace`. Lives in a GitHub repo following the Claude Code plugin structure (`.claude-plugin/plugin.json`, `agents/`, `skills/`, `hooks/`).

**Origin:** Rebuilt from Forge (a prior framework with 91,546 lines, 40% dead code, 4.5/10 maintainability). Shaktra retains Forge's quality mechanisms while eliminating bloat — ~88% size reduction, ~93% token reduction per workflow step.

---

## Core Philosophy

1. **Quality is non-negotiable.** TDD state machine, P0-P3 severity gates, and external hook enforcement ensure production-grade output. Every quality mechanism from Forge is preserved or improved.

2. **Ceremony proportional to complexity.** Four tiers (Trivial/Small/Medium/Large) scale the workflow. A trivial fix needs no story YAML. A large feature gets full gates. The framework adapts, not the developer.

3. **Single source of truth.** Every concept defined exactly once. Severity taxonomy in one file. Quality dimensions in one file. Guard tokens in one file. Everything else references.

4. **Agents orchestrate, sub-agents execute.** Five main agent skills (TPM, Dev Manager, Code Reviewer, Codebase Analyzer, General Purpose) coordinate work but never implement. Specialized sub-agents do the work.

5. **Minimal context, maximum depth.** No file exceeds 300 lines. Skills load on-demand. A typical workflow step consumes ~10K tokens (vs Forge's 150K+). Depth comes from focused skill content, not volume.

6. **Domain expertise over generalization.** Each workflow pillar (TPM, SDM, Code Reviewer, Codebase Analyzer) is a Subject Matter Expert — they do one thing and do it exceptionally well. When building each workflow, assemble it with industry-standard best practices, tooling, and deep domain knowledge. A TPM workflow should rival a seasoned Principal PM. An SDM workflow should rival a senior Dev Lead. When a workflow encounters something outside its expertise, it escalates to the appropriate expert rather than attempting it.

---

## Architecture at a Glance

### Main Agents (User-Invocable Skills)

| Command | Agent | Purpose |
|---------|-------|---------|
| `/shaktra:tpm` | Tech Program Manager | Design docs, stories, product management, sprints |
| `/shaktra:dev` | Software Dev Manager | TDD pipeline: Plan → RED → GREEN → Quality |
| `/shaktra:review` | Code Reviewer | App-level code review, PR review |
| `/shaktra:analyze` | Codebase Analyzer | Brownfield codebase analysis |
| `/shaktra:general` | General Purpose | Domain-flexible, loads specialist skills |

### Sub-Agents (Spawned by Main Agents)

| Agent | Under | Role |
|-------|-------|------|
| shaktra-architect | TPM | Design docs from PRD + Architecture (opus model) |
| shaktra-tpm-quality | TPM | Reviews design docs and stories |
| shaktra-scrummaster | TPM | Creates stories from design docs |
| shaktra-product-manager | TPM | RICE prioritization, sprint guidance |
| shaktra-sw-engineer | Dev | Creates unified implementation + test plans |
| shaktra-test-agent | Dev | Writes tests — RED phase |
| shaktra-developer | Dev | Implements code — GREEN phase |
| shaktra-sw-quality | Dev | Reviews dev artifacts per story |
| shaktra-cba-analyzer | Analyze | Executes codebase analysis dimensions |
| shaktra-cr-analyzer | Review | Executes code review dimensions |
| shaktra-memory-curator | All | Captures actionable lessons from workflow sessions |

### Internal Skills (Agent Knowledge)

| Skill | Purpose |
|-------|---------|
| shaktra-reference | Single source of truth: severity, guard tokens, principles, tiers, dimensions |
| shaktra-quality | Quality engine: quick-check (gates) + comprehensive (final review) |
| shaktra-tdd | TDD patterns: testing practices, coding practices |
| shaktra-stories | Story schema, tier definitions, creation rules |

---

## Core Workflows

### TPM Workflow

```
/shaktra:tpm → Architect Agent → Design Doc
                → TPM Quality → Review (max 3 loops)
              → ScrumMaster → Stories
                → TPM Quality → Review (max 3 loops)
              → Product Manager → Prioritization
              → ScrumMaster → Sprint allocation
```

### Story Enrichment (for external/sparse stories)

```
/shaktra:dev ST-001 → Story quality guard detects sparse story → blocks, recommends:
/shaktra:tpm enrich ST-001 [or batch]
  → Scrummaster (enrich mode) reads sparse story + codebase context + analysis
  → Fills missing tier-required fields (test_specs, io_examples, etc.)
  → TPM Quality reviews enriched story (max 3 loops)
  → User approves → story updated → /shaktra:dev can proceed
```

### Development Workflow (TDD Pipeline)

```
/shaktra:dev ST-001 → Story quality guard passes → Read story + handoff state (resume support)
  PLAN:    SW Engineer → Implementation + Test Plan (unified)
           SW Quality → Review plan (skip for Small tier, max 3 loops)
  RED:     Test Agent → Write failing tests (behavioral, exact names from story)
           SW Quality → Review tests (max 3 loops)
  GREEN:   Developer → Implement code (make tests pass, hit coverage)
           SW Quality → Review code (max 3 loops)
  QUALITY: SW Quality → Comprehensive 13-dimension review
           → Promote decisions to decisions.yml
  MEMORY:  Memory Curator → Extract actionable lessons to lessons.yml
```

### Memory Capture (mandatory final step in every workflow)

```
Workflow completes → Spawn shaktra-memory-curator (haiku)
  → Reviews session artifacts (handoff, findings, design docs)
  → Bar: "Would this materially change future workflow execution?"
  → Writes actionable lessons to .shaktra/memory/lessons.yml
  → Zero entries is valid — no ceremony, only critical insights
```

Decisions (architectural choices) are captured separately by sw-quality during the QUALITY phase into `decisions.yml`. The memory curator captures *lessons* — gotchas, surprising behaviors, process insights.

### Quality Loop Pattern (Create-Check-Fix)

Used everywhere: TPM quality reviews, TDD gates, code review.

```
attempt = 0
while attempt < max_attempts:
    attempt++
    findings = quality_agent.review(artifact)
    if QUALITY_PASS: return SUCCESS
    if no_progress after 3 attempts: escalate to user
    creator_agent.fix(findings)
return escalate(max_attempts)
```

---

## Quality System

### Severity (defined ONCE in shaktra-reference/severity-taxonomy.md)

| Level | Merge Gate | Key Checks |
|-------|-----------|-----------|
| P0 Critical | Any = BLOCKED | Timeouts, credentials, unbounded ops, injection, hallucinated imports |
| P1 Significant | > threshold = BLOCKED | Error path coverage, over-mocking, placeholders, generic errors |
| P2 Quality | Logged only | Complexity, naming, dead code |
| P3 Cosmetic | Logged only | Style, formatting |

### Quality Engine (ONE component, TWO modes)

- **Quick-Check:** ~35 checks during TDD gates. All checks loaded regardless of tier. Max 3 fix loops.
- **Comprehensive:** Full 13-dimension review at completion. Coverage verification. Decision consolidation.

### Story Tiers

| Tier | Fields | Coverage | Gates |
|------|--------|----------|-------|
| Trivial | 3 (minimum viable story) | 70% (hotfix threshold) | Quick test + code gates |
| Small | 5 | 80% | Code gate only |
| Medium | 10 | 90% | All gates |
| Large | 15+ | 95% | All gates (thorough) |

---

## State Management

### Per-Project State (in target project's `.shaktra/` directory)

Hidden directory — the framework is a creation tool, not a storage system. Teammates who don't use Shaktra never see it. Gitignore flexibility: ignore everything, ignore only `.tmp/`, or mix and match.

| File | Purpose | Lifecycle |
|------|---------|-----------|
| `settings.yml` | Framework config (thresholds, sprint settings) | Set once, rarely changed |
| `memory/decisions.yml` | Architectural decisions | Append-only, never delete |
| `memory/lessons.yml` | Lessons learned (AI-curated) | Append-only, max 100, archived when full |
| `memory/sprints.yml` | Sprint planning state | Updated per sprint |
| `stories/ST-001.yml` | Story specifications | Created by scrummaster |
| `.tmp/{story}/handoff.yml` | TDD phase state machine | Created/updated per phase |

### Handoff State Machine (the backbone)

```
[START] → plan → tests (RED) → code (GREEN) → quality → memory → complete
```

Transition guards:
- plan → tests: requires `plan_summary` populated
- tests → code: requires `all_tests_red == true`
- code → quality: requires `all_tests_green == true`
- quality → complete: requires no P0 findings AND `memory_captured == true`

Resume: Reads `completed_phases`, continues from next phase.

---

## Enforcement Layer

### Hooks (External, Python, All Blocking)

| Hook | Prevents |
|------|----------|
| block_main_branch | Git operations on main/master/prod |
| check_p0_findings | Completing work with unresolved P0s |
| validate_story_scope | Editing files not declared in story |
| validate_schema | Writing invalid YAML schemas |

---

## Design Constraints (Must Not Repeat from Forge)

- No file over 300 lines
- No content duplication across layers
- No dead code or disabled stubs
- No severity taxonomy in more than one file
- No hardcoded threshold values (always read from .shaktra/settings.yml)
- No always-on rules consuming context every turn
- No hooks that warn instead of block
- No naming ambiguity between components
- All hook scripts in Python (cross-platform)
- Total framework: ~58 files, ~7,000 lines (vs Forge's 174 files, 52,655 lines)

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent personas | Full descriptions | User preference — detailed experience-based personas |
| Sprint planning | Full (with velocity) | User preference — complete agile capability |
| Quality scope separation | SW Quality (story) + Code Reviewer (app) | Different scopes, non-redundant |
| Fix loop cap | 3 attempts max | Consistent across all workflows — TPM, SDM, Review |
| Memory system | Memory curator sub-agent at workflow end, not hooks/infrastructure | Forge lesson — 1500-line Python system never worked. claude-mem too heavy (SQLite + ChromaDB + background HTTP). Simple sub-agent call + YAML files. |
| MCP servers | None (use `gh` CLI) | Forge lesson — both MCP stubs were non-functional |
| Intent routing | `/shaktra:workflow` (primary NL entry point) | Forge lesson — always-on routing caused false captures |
| Project state directory | `.shaktra/` (hidden) | Framework as tool, not visible structure — gitignore flexible |
| Plugin distribution | Claude Code plugin system + `.claude-plugin/marketplace.json` | User requirement — /plugin install shaktra |
| Git workflow | Developer creates branch (feat/fix/chore), staging only, no commits | SDM orchestrates, dev executes — user manages commits/PRs |
| Language handling | Language-agnostic instructions, project language in settings.yml | Adapt via config, never hardcode language-specific patterns in skills |
| Hotfix path | `/shaktra:tpm hotfix` → Trivial tier story → `/shaktra:dev` | Story always required, even for hotfix — minimum viable (3 fields) |
| Static knowledge | Internal skills contain best practices, ported from Forge | Language-agnostic, selective loading, scrutinized during each phase |
| Single version file | `plugin.json` version field only | No per-file schema versioning — one version for the package |

---

## Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Execution Plan | `docs/shaktra-plan/execution-plan.md` | Phase-by-phase build guide |
| Forge Analysis | `docs/Forge-analysis/analysis-report.md` | What to learn from Forge |
| Architecture Diagram | `Resources/workflow.drawio.png` | Visual agent architecture |
| Framework Spec | `Resources/Shaktra-Framework.docx` | Original vision document |
