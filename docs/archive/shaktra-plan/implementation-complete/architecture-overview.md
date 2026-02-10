# Shaktra — Architecture Overview

> **Purpose:** Shared architecture context for all phases. Read this before starting any phase.
> **Companion:** [high-level.md](high-level.md) for philosophy and workflow summaries.

---

## Plugin Structure

Shaktra is a Claude Code **plugin** distributed via GitHub. Users install with `/plugin install shaktra@marketplace`. The repo follows the official plugin layout:

```
shaktra-plugin/
├── .claude-plugin/
│   ├── plugin.json             # Plugin manifest (required)
│   └── marketplace.json        # Marketplace catalog for distribution
├── agents/                     # Sub-agent definitions (~11 files)
│   ├── shaktra-architect.md
│   ├── shaktra-tpm-quality.md
│   ├── shaktra-scrummaster.md
│   ├── shaktra-product-manager.md
│   ├── shaktra-sw-engineer.md
│   ├── shaktra-test-agent.md
│   ├── shaktra-developer.md
│   ├── shaktra-sw-quality.md
│   ├── shaktra-cba-analyzer.md
│   ├── shaktra-cr-analyzer.md
│   └── shaktra-memory-curator.md
├── skills/                     # All skills (~12 directories)
│   ├── shaktra-tpm/            # Main agent: TPM orchestrator
│   ├── shaktra-dev/            # Main agent: SDM orchestrator
│   ├── shaktra-review/         # Main agent: Code review orchestrator
│   ├── shaktra-analyze/        # Main agent: Codebase analysis orchestrator
│   ├── shaktra-general/        # Main agent: General purpose
│   ├── shaktra-init/           # Utility: Project initialization
│   ├── shaktra-doctor/         # Utility: Framework validation
│   ├── shaktra-workflow/       # Utility: Auto-intent router
│   ├── shaktra-quality/        # Internal: Quality standards engine
│   ├── shaktra-tdd/            # Internal: TDD patterns & practices
│   ├── shaktra-reference/      # Internal: Shared constants (single source of truth)
│   └── shaktra-stories/        # Internal: Story schema & creation
├── hooks/
│   └── hooks.json              # Hook event configurations
├── scripts/                    # Hook implementation scripts (Python)
│   ├── block_main_branch.py
│   ├── check_p0_findings.py
│   ├── validate_story_scope.py
│   └── validate_schema.py
├── templates/                  # State file templates for /shaktra:init
│   ├── settings.yml
│   ├── decisions.yml
│   ├── lessons.yml
│   └── sprints.yml
├── docs/                       # Analysis and planning docs
├── Resources/                  # Architecture diagrams, framework doc
├── CLAUDE.md                   # Plugin-level instructions
└── README.md                   # Usage guide
```

**Key structural rules:**
- `.claude-plugin/` contains `plugin.json` and `marketplace.json`
- Everything else (agents, skills, hooks) lives at the **plugin root**, not inside `.claude/`
- Skills are namespaced as `/shaktra:skill-name` when installed
- Agents are available to the plugin's skills via the Task tool
- **Main agent skills must NOT use `context: fork`** — they run inline in the main conversation to spawn sub-agents via Task tool
- **Sub-agents cannot spawn other sub-agents** — orchestrator skills handle all coordination, sub-agents execute and return
- **Plugins are cached after install** — all internal paths must use `${CLAUDE_PLUGIN_ROOT}` (e.g., hook scripts)
- **Agent `skills` frontmatter** — agents declare which internal skills to preload via the `skills` field in YAML frontmatter

---

## Target Project Structure (after init)

When a user runs `/shaktra:init` in their project, this hidden directory is created:

```
user-project/
└── .shaktra/                   # Hidden — framework-managed workspace
    ├── settings.yml            # Framework configuration (from template)
    ├── memory/
    │   ├── decisions.yml       # Architectural decisions (append-only)
    │   ├── lessons.yml         # Lessons learned (append-only, max 100)
    │   └── sprints.yml         # Sprint planning state
    ├── stories/                # Story YAML files (ST-001.yml, etc.)
    ├── designs/                # Design documents
    ├── analysis/               # Codebase analysis output (brownfield)
    └── .tmp/                   # Per-story working state (always gitignored)
        └── {story-id}/
            ├── handoff.yml     # TDD phase state machine
            └── implementation_plan.md
```

**Why hidden (`.shaktra/` not `shaktra/`):** The framework is a creation tool, not a storage system. Teammates who don't use Shaktra never need to know about it. Gitignore flexibility:
- `.shaktra/` — ignore everything (solo use)
- `.shaktra/.tmp/` — ignore only ephemeral state (commit artifacts)
- Selective — mix and match

`/shaktra:init` adds `.shaktra/.tmp/` to `.gitignore` by default.

---

## Component Inventory

### Main Agent Skills (5 — user-invocable orchestrators)

| # | Skill | Command | Purpose | Spawns |
|---|-------|---------|---------|--------|
| 1 | shaktra-tpm | `/shaktra:tpm` | Design docs, stories, PM, sprints | architect, tpm-quality, scrummaster, product-manager, memory-curator |
| 2 | shaktra-dev | `/shaktra:dev` | TDD pipeline orchestration | sw-engineer, test-agent, developer, sw-quality, memory-curator |
| 3 | shaktra-review | `/shaktra:review` | App-level code review, PR review | cr-analyzer, memory-curator |
| 4 | shaktra-analyze | `/shaktra:analyze` | Codebase analysis (brownfield) | cba-analyzer, memory-curator |
| 5 | shaktra-general | `/shaktra:general` | Flexible, domain-specialized tasks | (uses specialist skills) |

### Utility Skills (3 — user-invocable commands)

| # | Skill | Command | Purpose |
|---|-------|---------|---------|
| 6 | shaktra-init | `/shaktra:init` | Initialize project directory structure |
| 7 | shaktra-doctor | `/shaktra:doctor` | Validate framework setup and configs |
| 8 | shaktra-workflow | `/shaktra:workflow` | Auto-classify intent and route to main agent |

### Internal Skills (4 — loaded by agents, not user-invocable)

| # | Skill | Loaded By | Purpose |
|---|-------|-----------|---------|
| 9 | shaktra-quality | sw-quality, tpm-quality | Quality standards, P0-P3, dimensions, checks |
| 10 | shaktra-tdd | sw-engineer, test-agent, developer | TDD patterns, testing practices, coding practices |
| 11 | shaktra-reference | All agents | Shared constants: severity, guard tokens, principles |
| 12 | shaktra-stories | scrummaster | Story schema, tier definitions, creation rules |

### Sub-Agents (11)

| # | Agent | Spawned By | Purpose | Model |
|---|-------|-----------|---------|-------|
| 1 | shaktra-architect | TPM skill | Create design docs from PRD + Architecture | opus |
| 2 | shaktra-tpm-quality | TPM skill | Review TPM artifacts (design docs, stories) | sonnet |
| 3 | shaktra-scrummaster | TPM skill | Create user stories from design docs | sonnet |
| 4 | shaktra-product-manager | TPM skill | RICE prioritization, requirement alignment | sonnet |
| 5 | shaktra-sw-engineer | Dev skill | Create implementation + test plans | opus |
| 6 | shaktra-test-agent | Dev skill | Write tests — RED phase | opus |
| 7 | shaktra-developer | Dev skill | Implement code — GREEN phase | opus |
| 8 | shaktra-sw-quality | Dev skill | Review dev artifacts per story | sonnet |
| 9 | shaktra-cba-analyzer | Analyze skill | Execute codebase analysis dimensions | opus |
| 10 | shaktra-cr-analyzer | Review skill | Execute code review dimensions | opus |
| 11 | shaktra-memory-curator | All main skills | Capture actionable memory from workflow sessions | haiku |

### Hooks (4)

| # | Hook | Event | Matcher | Action |
|---|------|-------|---------|--------|
| 1 | block_main_branch | PreToolUse | Bash | Block git ops on main/master/prod |
| 2 | check_p0_findings | Stop | — | Block completion if P0 findings exist |
| 3 | validate_story_scope | PreToolUse | Write\|Edit | Block file changes outside story scope |
| 4 | validate_schema | PostToolUse | Write | Validate YAML files against schemas |

---

## Token Budget

| Context | Lines | Est. Tokens | Notes |
|---------|-------|-------------|-------|
| Always loaded (CLAUDE.md) | ~30 | ~500 | Plugin identity, available commands |
| Main agent skill | ~250 | ~3,500 | Orchestration logic |
| Sub-agent definition | ~80 | ~1,200 | Persona + role + constraints |
| Internal skill (loaded by agent) | ~200 | ~3,000 | Deep knowledge, loaded on-demand |
| Reference skill (shared constants) | ~150 | ~2,000 | Severity, tokens, principles |
| **Typical workflow step** | **~710** | **~10,000** | Main skill + 1 sub-agent + skills |
| **Maximum single step** | **~960** | **~14,000** | All skills loaded simultaneously |
| **Forge equivalent** | **22,000+** | **150,000+** | For comparison |

**Result:** ~93% reduction in per-step token consumption vs Forge.

### Token Optimization Strategy

Optimization is **architectural, not format-based**. YAML and Markdown remain the standard formats — human readability, reliable parsing, and schema validation outweigh marginal token savings from compact formats.

**Architectural optimization principles:**

1. **Selective loading** — Load only the files relevant to the current operation
2. **Progressive depth** — Sub-agents receive only the context they need
3. **On-demand skill loading** — Internal skills load when their consumer agent is spawned, not upfront
4. **Reference sub-file splitting** — shaktra-reference split into sub-files so agents load only relevant sections
5. **No tier-aware content reduction** — All quality checks (~35) always loaded regardless of story tier
6. **Batch summaries** — When loading multiple stories, use summary views rather than full story content

**What these principles do NOT mean:**
- Do NOT compress or abbreviate skill instructions to save tokens
- Do NOT skip loading reference material
- Do NOT reduce agent persona depth

### Static Knowledge Files (Best Practices & Patterns)

| Skill | File | Loaded By | Content |
|-------|------|-----------|---------|
| shaktra-tdd | testing-practices.md | test-agent, sw-engineer | Behavioral testing, test isolation, mocking discipline |
| shaktra-tdd | coding-practices.md | developer, sw-engineer | Implementation patterns, error handling, anti-patterns |
| shaktra-quality | quick-check.md | sw-quality, tpm-quality | ~35 quality checks organized by severity and gate |
| shaktra-quality | comprehensive-review.md | sw-quality | Full 13-dimension review template |
| shaktra-review | review-dimensions.md | cr-analyzer | App-level review dimensions, evidence enforcement, edge-case matrix |
| shaktra-reference | quality-principles.md | All agents | 10 core quality principles |
| shaktra-reference | quality-dimensions.md | Quality agents | 13 review dimensions (A-M) |
| shaktra-stories | story-creation.md | scrummaster | Story crafting rules, enrichment rules, tier detection |

**Key rules:** Language-agnostic. Selective loading. Ported from Forge with scrutiny.

**Gap:** Architect agent has no architecture patterns knowledge file. Evaluate during Phase 4.

---

## Design Constraints

Non-negotiable rules for every phase:

| # | Constraint | Source |
|---|-----------|--------|
| 1 | No single file over 300 lines | Forge analysis 9.5 |
| 2 | No content duplication across layers | Forge analysis 9.5 |
| 3 | No dead code, disabled stubs, or orphaned files | Forge analysis 9.5 |
| 4 | No features advertised but not implemented | Forge analysis 9.5 |
| 5 | P0-P3 severity defined in exactly ONE file | Forge analysis 9.4 #6 |
| 6 | Guard tokens reduced to ~15 (from Forge's 40+) | Forge analysis 9.4 #7 |
| 7 | Hooks enforce or don't exist — no warn-only | Forge analysis 9.5 |
| 8 | All hook scripts in Python — cross-platform | Forge analysis 9.3 |
| 9 | Full persona descriptions for all agents | User decision |
| 10 | Full sprint planning with velocity tracking | User decision |
| 11 | SW Quality (story-level) separate from Code Reviewer (app-level) | User decision |
| 12 | Quality depth and breadth must match or exceed Forge | User requirement |

---

## Agent Design Philosophy — Domain Expertise

Each main workflow pillar is a **Subject Matter Expert**. They do one thing and do it exceptionally well.

**What this means in practice:**
- When building each workflow, assemble it with **industry-standard best practices**, tooling, and deep domain knowledge
- A TPM workflow should rival a seasoned Principal Program Manager
- An SDM workflow should rival a senior Dev Lead
- A Code Reviewer should rival a Principal Engineer
- A Codebase Analyzer should rival a Staff Engineer during due diligence

**How this guides implementation:**
- Each agent's skill content is written as if training a world-class practitioner
- Sub-agents inherit their parent workflow's domain depth
- Internal skills encode hard-won domain knowledge
- No agent tries to be good at everything — they defer to the appropriate expert

**Cross-workflow collaboration:** When a workflow encounters something outside its expertise, it escalates rather than attempting it. SDM escalates story quality to TPM. Code Reviewer escalates architecture concerns to TPM.
