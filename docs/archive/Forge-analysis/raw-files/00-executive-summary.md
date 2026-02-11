# Forge Framework Analysis — Executive Summary

> **Date:** 2026-02-05
> **Scope:** Complete analysis of the Forge framework at `~/workspace/applications/forge-claudify`
> **Purpose:** Inform the design of Shaktra, a clean rebuild of the coding framework
> **Total Analysis:** 7,875 lines across 9 detailed documents

---

## 1. What Is Forge?

Forge is a Claude Code framework that orchestrates an opinionated, agile-inspired software development workflow. It uses Claude Code's native primitives — **rules**, **skills**, **agents**, **hooks**, and **MCP** — to guide an AI coding assistant through a structured pipeline: **Plan → Design → Test (TDD) → Implement → Quality Review → Ship**.

### Framework Scale
| Metric | Count |
|--------|-------|
| Total files (non-vendor) | 271 |
| Total lines | 91,546 |
| Dead code (`_to_be_deleted/`) | 97 files / 37,057 lines (40%) |
| Active agent definitions | 12 |
| Skills | 11 (with 40+ sub-files) |
| Rules | 5 |
| Hooks | 7 (only 2 wired up) |
| MCP servers | 2 (both non-functional stubs) |
| Python scripts | 6 (~1,500 lines) |

---

## 2. Architecture Overview

### Layering Model (10 layers)
```
CLAUDE.md (root entry point — 44 lines, mostly a pointer)
  └─ .claude/settings.json (permissions, env vars, hooks config)
      └─ .claude/settings.local.json (local overrides — undermines permissions)
          └─ .claude/rules/ (5 always/glob-loaded rules)
              └─ .claude/skills/ (11 skills, invoked via /commands)
                  └─ .claude/agents/ (12 agents, spawned as sub-agents)
                      └─ .claude/hooks/ (shell/python scripts on events)
                          └─ .claude/mcp/ (MCP server configs)
                              └─ .claude/scripts/ (Python utilities)
                                  └─ forge/ (runtime state — settings, memory, learning)
```

### Core Workflow
```
User Request
  → Auto-Router (keyword matching in rules)
    → /forge-workflow (central orchestrator skill)
      → Intent Classification (22+ intents)
        → Orchestrator delegates to sub-agents:
           ├─ forge-planner → Story creation (YAML)
           ├─ forge-designer → Design doc (18 sections)
           ├─ forge-developer → TDD pipeline (RED→GREEN→REFACTOR)
           ├─ forge-checker → Quality gates (P0-P3 severity)
           ├─ forge-quality → Final CCR review (14 dimensions)
           └─ forge-docs-updater → Memory/decisions update
```

---

## 3. Top 10 Critical Findings

### Finding 1: 40% Dead Code
97 files and 37,057 lines sit in `_to_be_deleted/` — a legacy command dispatcher system (`forge_dispatch.py` at 746 lines) that was superseded by Claude Code native primitives but never cleaned up.

### Finding 2: Quadruple Quality Redundancy
Four components handle quality with massive overlap:
- `forge-checker` agent + `forge-check` skill (phase-level gates, 7 checklists, 152+ checks)
- `forge-quality` agent + `forge-quality` skill (final 14-dimension CCR review)
- P0-P3 severity taxonomy duplicated across 6 files
- The naming distinction between "check" and "quality" is unintuitive

### Finding 3: God File — forge-workflow/SKILL.md
At **1,481 lines**, this file tries to be the orchestrator, intent classifier, gate enforcer, PM coordinator, and learning system integrator all at once. It repeats its own "MANDATORY POST-COMPLETION GATES" table **4 separate times** within the file.

### Finding 4: CLAUDE.md Template/Live Gap
The live `CLAUDE.md` is a 44-line stub pointing to `/forge-workflow`. The template `CLAUDE.template.md` has 161 lines with 4 critical behavioral sections (Skill Chaining Protocol, Evidence Rule, Subagent Delegation, Brownfield Context) that are **not present** in the live file.

### Finding 5: Dead Learning System
1,500 lines of Python scripts implement pattern analysis, event logging, and learning — but:
- Zero actual data in any data file (all empty scaffolding)
- Never processed a single event
- Import paths contain invalid Python module syntax
- Not connected to any hook or automated trigger
- Solves a problem Claude's native capabilities handle better

### Finding 6: Excessive Ceremony Per Story
A single story requires: 11 phases, 4 quality gates, ~12 sub-agent invocations, consuming an estimated **150,000+ context tokens**. For a SIMPLE tier story touching one file, this is prohibitively heavy.

### Finding 7: Only 2 of 7 Hooks Actually Active
- `block-main-branch.sh` — active, blocks main branch operations
- `validate-story-alignment.sh` — active, but warns only (doesn't block despite claiming to)
- `check-p0-findings.py` — NOT wired up (empty Stop array)
- `validate-story.py` — NOT configured in settings.json
- `forge-statusline.sh` — NOT connected to any hook event
- CI hooks — require manual git installation

### Finding 8: Triple-Layer Content Duplication
Rules, skills, and agents all contain overlapping content:
- Every agent body repeats what its loaded skill already provides
- Every rule condenses content from the skills it routes to
- Changes require updating 3+ files in sync with no enforcement mechanism

### Finding 9: Undocumented and Outdated README
- README says 8-9 skills, actual count is 11
- README says 7 agents, actual count is 12
- Entire learning subsystem undocumented
- File tree diagram outdated
- `package.json` names the project "simpletask" not "Forge"

### Finding 10: macOS Incompatibility
Multiple bash hooks use `grep -oP` (Perl regex) which **does not work on macOS** (requires GNU grep). This is a framework designed to run locally that breaks on the most common developer platform.

---

## 4. What Works Well (Keep for Shaktra)

| Component | Why It Works |
|-----------|-------------|
| **TDD enforcement model** | Red-Green-Refactor with handoff state machine is sound |
| **Story-driven development** | Tying work to stories with acceptance criteria adds structure |
| **Tiered complexity** (SIMPLE/STANDARD/COMPLEX) | Right idea — scale ceremony to task size |
| **Sub-agent delegation** | Using Task tool for parallel work is architecturally correct |
| **Model selection strategy** | opus for design (high leverage), haiku for docs (low cost), sonnet for rest |
| **Branch protection hook** | Simple, effective, actually works |
| **Evidence Rule** | "Never assume, always verify" is a powerful quality principle |
| **P0 severity concept** | Blocking on critical issues (hallucinated imports, hardcoded creds) is high-value |
| **Brownfield-first design** | Always analyzing existing code before changes is correct |
| **Error-resolver skill** | Standalone, focused, practical — good template for skill design |

---

## 5. What Must Change (Shaktra Design Principles)

### Principle 1: Strict Layering
```
Rules:  Routing ONLY (<20 lines each). Never repeat skill content.
Skills: Hold ALL instructional content. Self-contained.
Agents: Thin wrappers (~50 lines). Reference skills, don't duplicate them.
Hooks:  External enforcement. All must be wired up or deleted.
```

### Principle 2: Single Source of Truth
- One place for quality criteria (not 4)
- One place for severity definitions (not 6)
- One config system (not 4 overlapping files)
- One orchestration pattern (not 2 competing ones)

### Principle 3: Ceremony Proportional to Complexity
- SIMPLE tasks: Minimal pipeline (analyze → implement → verify)
- STANDARD tasks: Full pipeline (plan → design → TDD → review)
- COMPLEX tasks: Extended pipeline with parallel execution

### Principle 4: Everything Wired or Deleted
- No stub MCP servers
- No orphaned hooks
- No empty data files
- No `_to_be_deleted` directories

### Principle 5: Context Window Budget
- Total framework instructions must fit in <30K tokens (current: 150K+)
- Load only what's needed for the current phase
- Skills should be <300 lines each

### Principle 6: External Enforcement Where Possible
- Quality checks via hooks (external) not just agent self-review
- Schema validation via scripts not prompt instructions
- CI integration that actually works

### Principle 7: Cross-Platform by Default
- No GNU-only commands
- No undeclared dependencies (PyYAML, etc.)
- Test on macOS and Linux

---

## 6. Recommended Shaktra Architecture

### Simplified Component Map
```
CLAUDE.md (concise, <100 lines, operational rules only)
├── rules/
│   ├── router.md          (intent → skill routing, <30 lines)
│   └── standards.md       (core principles, <30 lines)
├── skills/
│   ├── plan/              (story creation, tiered)
│   ├── design/            (design docs, brownfield-first)
│   ├── develop/           (TDD pipeline — the core)
│   ├── review/            (unified quality — replaces check+quality)
│   ├── workflow/           (orchestration — <500 lines)
│   └── [utility skills]/  (error-resolver, brainstorming, etc.)
├── agents/
│   ├── planner.md         (thin, references plan skill)
│   ├── designer.md        (thin, references design skill)
│   ├── developer.md       (thin, references develop skill)
│   ├── reviewer.md        (thin, unified quality agent)
│   └── [specialist].md    (language-specific if needed)
├── hooks/
│   ├── branch-guard.sh    (all wired, all functional)
│   ├── quality-gate.sh    (external enforcement)
│   └── pre-commit.sh      (integrated, not manual)
└── state/
    ├── project.yml        (simple project memory)
    └── decisions.yml      (architectural decisions log)
```

### Key Reductions
| Forge | Shaktra | Reduction |
|-------|---------|-----------|
| 12 agents | 5-6 agents | 50% |
| 11 skills (40+ files) | 6-7 skills (~15 files) | 60% |
| 5 rules | 2 rules | 60% |
| 7 hooks (2 active) | 3-4 hooks (all active) | Effective increase |
| 6 Python scripts (1,500 lines) | 0-1 scripts | 90% |
| 4 config systems | 2 (settings.json + state/project.yml) | 50% |
| 91,546 total lines | Target: <5,000 lines | 95% |

---

## 7. Detailed Analysis Documents

| Document | Lines | Focus |
|----------|-------|-------|
| [01-core-architecture.md](./01-core-architecture.md) | 625 | CLAUDE.md, rules, settings, bootstrap flow |
| [02-agent-system.md](./02-agent-system.md) | 1,253 | All 12 agents, roles, orchestration, gaps |
| [03a-skills-core-part1.md](./03a-skills-core-part1.md) | 314 | forge-analyze, forge-check, forge-design, forge-plan |
| [03b-skills-core-part2.md](./03b-skills-core-part2.md) | 714 | forge-quality, forge-reference, forge-tdd, forge-workflow, standalone skills |
| [04-workflow-process-flow.md](./04-workflow-process-flow.md) | 1,309 | End-to-end lifecycle, intent routing, agile alignment |
| [05-quality-validation.md](./05-quality-validation.md) | 941 | Quality gates, checklists, TDD, guard tokens |
| [06-memory-learning-state.md](./06-memory-learning-state.md) | 680 | Memory, learning system, state persistence |
| [07-hooks-mcp-tooling.md](./07-hooks-mcp-tooling.md) | 1,162 | Hooks, MCP servers, Python scripts, CI |
| [08-gaps-redundancy-recommendations.md](./08-gaps-redundancy-recommendations.md) | 877 | Cross-cutting bloat, redundancy, recommendations |

**Total: 7,875 lines of analysis**

---

## 8. Next Steps for Shaktra

1. **Finalize design principles** — Review this summary and lock down what Shaktra's philosophy should be
2. **Define the minimal viable framework** — What's the smallest Shaktra that delivers value?
3. **Design the skill architecture** — Clean, layered, context-budget-aware
4. **Build incrementally** — Start with the TDD pipeline (highest value), add planning/design/review
5. **Test on real projects** — Use Shaktra to build Shaktra (dogfooding)
6. **Package for distribution** — Plugin structure, installation, configuration
