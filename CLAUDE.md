# Shaktra — Claude Code Plugin

Shaktra is an opinionated software development framework distributed as a Claude Code plugin. It orchestrates specialized AI agents through agile-inspired workflows to produce industry-standard, reliable, production code.

## How We Work on This Project

This is a **collaborative build**. For every aspect of Shaktra:

1. **Reference Forge first** — Before building any component, review the corresponding Forge implementation at `~/workspace/applications/forge-claudify`. Understand what exists, what worked, what didn't.
2. **Discuss before implementing** — Present findings, propose the Shaktra approach, discuss tradeoffs. No implementation until we've aligned on the approach.
3. **Implement after agreement** — Only after discussion, build the component following the agreed design.
4. **Validate against constraints** — Check every deliverable against the design constraints below.

## Starting a Phase

When the user says "work on Phase X" or "let's start Phase X":

1. **Read** `docs/shaktra-plan/high-level.md` — architecture and philosophy context
2. **Read** `docs/shaktra-plan/architecture-overview.md` — plugin structure, components, constraints
3. **Read** `docs/shaktra-plan/phases/phase-XX-*.md` — the specific phase file
4. **Read each Forge file** listed in the phase's Forge Reference table (at `~/workspace/applications/forge-claudify`)
5. **Present** — what Forge does, what Shaktra should do differently, proposed approach
6. **Wait for approval** — no implementation until we've aligned
7. **Validate** — after implementation, check the phase's Validation list AND `docs/shaktra-plan/appendices.md` (Appendix A anti-patterns)

For Forge analysis reference: `docs/Forge-analysis/analysis-report.md`
For phase index and dependency graph: `docs/shaktra-plan/execution-plan.md`

## Plugin Structure

This is a **Claude Code plugin** (NOT a regular project). The directory layout follows the plugin spec:

```
.claude-plugin/marketplace.json  # Marketplace catalog (source: "./shaktra") — stays at repo root
shaktra/                         # THE PLUGIN — all plugin code lives here
  .claude-plugin/plugin.json     # Plugin manifest (required)
  agents/                        # Sub-agent definitions
  skills/                        # Skill definitions
  hooks/hooks.json               # Hook configurations
  scripts/                       # Hook implementation scripts (Python)
  templates/                     # State file templates for /shaktra:init
docs/                            # Dev-only — architecture, phase plans, Forge analysis
Resources/                       # Dev-only — diagrams, reference docs
CLAUDE.md                        # Dev-only — this file (not installed)
```

**All plugin development happens in `shaktra/`.** Dev files (docs, Resources, CLAUDE.md) stay at repo root and are never installed.

Skills are namespaced as `/shaktra:skill-name` when installed by users.

**SKILL.md files require YAML frontmatter** with at least `name` and `description` fields for Claude Code to discover them.

## Testing the Plugin

**Quick dev iteration:** `claude --plugin-dir shaktra/` — loads the plugin directly, no install step. Fast but skips the real install path.

**Full install testing (preferred before marking a phase complete):**

```bash
# Local file path — simulates a real install from a local checkout
/plugin install /absolute/path/to/claude-skills/shaktra

# Git remote — simulates how end users will install
/plugin install https://github.com/im-shashanks/claude-skills.git

# Marketplace — the intended distribution path
/plugin marketplace add https://github.com/im-shashanks/claude-skills.git
/plugin install shaktra@claude-skills-marketplace
```

Always validate at least the local file path install before finalizing a phase. The `--plugin-dir` flag is convenient for rapid iteration but does not exercise the install/discovery pipeline.

## Key Design Decisions

These were explicitly chosen and must not be overridden:

- **Full persona descriptions** for all agents (detailed experience-based identity)
- **Full sprint planning** with velocity tracking and capacity planning
- **SW Quality and Code Reviewer are separate** — SW Quality checks story-level during TDD, Code Reviewer checks app-level after completion and reviews PRs
- **Quality depth must match or exceed Forge** — we reduce bloat, not capability
- **Plugin distribution** via `/plugin install shaktra` (marketplace.json at `.claude-plugin/marketplace.json`)
- **shaktra/ is the plugin** — Claude Code has no include/exclude mechanism for plugin installs, so all plugin code lives directly in `shaktra/`. Marketplace.json uses `"source": "./shaktra"` to scope what gets installed. Dev files (docs/, Resources/, CLAUDE.md) stay at repo root and are never shipped.
- **Multi-plugin marketplace** — The repo is structured as a marketplace (`claude-skills`) where Shaktra is one plugin. Future plugins can be added as sibling directories (e.g., `another-plugin/`).

## Design Constraints

Check every file against these before considering any phase complete:

- No single file over 300 lines
- No content duplication across layers (skill defines, agent references — never both)
- No dead code, disabled stubs, or orphaned files
- Severity taxonomy (P0-P3) defined in exactly ONE file: `shaktra/skills/shaktra-reference/severity-taxonomy.md`
- All threshold values read from `.shaktra/settings.yml` — never hardcoded
- All hook scripts in Python (cross-platform, no `grep -oP`)
- Hooks block or don't exist — no warn-only
- No always-on rules consuming context every turn
- No ASCII art in agent/skill prompts
- No naming ambiguity between components

## Git Conventions

- **Never** include a `Co-Authored-By` line in commit messages

## Component Overview

**6 Main Agent Skills:** `/shaktra:tpm`, `/shaktra:dev`, `/shaktra:review`, `/shaktra:analyze`, `/shaktra:general`, `/shaktra:bugfix`
**4 Utility Skills:** `/shaktra:init`, `/shaktra:doctor`, `/shaktra:workflow`, `/shaktra:help`
**4 Internal Skills:** shaktra-quality, shaktra-tdd, shaktra-reference, shaktra-stories
**12 Sub-Agents:** architect, tpm-quality, scrummaster, product-manager, sw-engineer, test-agent, developer, sw-quality, cba-analyzer, cr-analyzer, memory-curator, bug-diagnostician
**4 Hooks:** block-main-branch, check-p0, validate-story-scope, validate-schema
