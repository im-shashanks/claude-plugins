# Shaktra — Claude Code Plugin

Shaktra is an opinionated software development framework distributed as a Claude Code plugin. It orchestrates specialized AI agents through agile-inspired workflows to produce industry-standard, reliable, production code.

## Plugin Structure

This is a **Claude Code plugin** (NOT a regular project). The directory layout follows the plugin spec:

```
.claude-plugin/marketplace.json  # Marketplace catalog (source: "./dist/shaktra") — stays at repo root
dist/shaktra/                    # THE PLUGIN — all plugin code lives here
  .claude-plugin/plugin.json     # Plugin manifest (required)
  agents/                        # Sub-agent definitions
  commands/                      # Slash commands (non-namespaced)
  skills/                        # Skill definitions
  hooks/hooks.json               # Hook configurations
  scripts/                       # Hook implementation scripts (Python)
  templates/                     # State file templates for /shaktra:init
  docs/                          # User-facing documentation (ships with plugin)
  diagrams/                      # Workflow diagrams (ships with plugin)
  README.md                      # User-facing README (ships with plugin)
tests/                           # Automated E2E test suite (dev-only)
scripts/                         # Publish/release scripts (dev-only)
.github/workflows/               # CI pipeline (dev-only)
README-marketplace.md            # Marketplace catalog description (dev-only)
CLAUDE.md                        # Dev-only — this file (not installed)
```

**All plugin development happens in `dist/shaktra/`.** Dev files (docs, tests, scripts, CLAUDE.md) stay at repo root and are never installed.

Skills are namespaced as `/shaktra:skill-name` when installed by users.

**SKILL.md files require YAML frontmatter** with at least `name` and `description` fields for Claude Code to discover them.

## Testing the Plugin

### Manual Testing

**Quick dev iteration:** `claude --plugin-dir dist/shaktra/` — loads the plugin directly, no install step. Fast but skips the real install path.

**Full install testing:**

```bash
# Local file path — simulates a real install from a local checkout
/plugin install /absolute/path/to/shaktra-plugin/dist/shaktra

# Git remote — simulates how end users will install
/plugin install https://github.com/im-shashanks/shaktra-plugin.git

# Marketplace — the intended distribution path
/plugin marketplace add https://github.com/im-shashanks/claude-plugins.git
/plugin install shaktra@cc-plugins
```

### Automated Tests

The `tests/workflows/` directory contains 21 E2E tests covering all skills (happy path and error scenarios). Run them with:

```bash
cd tests/workflows && python3 run_workflow_tests.py
```

CI runs these automatically via `.github/workflows/publish-release.yml` on pushes to the release branch.

## Key Design Decisions

These were explicitly chosen and must not be overridden:

- **Full persona descriptions** for all agents (detailed experience-based identity)
- **Full sprint planning** with velocity tracking and capacity planning
- **SW Quality and Code Reviewer are separate** — SW Quality checks story-level during TDD, Code Reviewer checks app-level after completion and reviews PRs
- **Plugin distribution** via `/plugin install shaktra` (marketplace.json at `.claude-plugin/marketplace.json`)
- **dist/shaktra/ is the plugin** — Claude Code has no include/exclude mechanism for plugin installs, so all plugin code lives directly in `dist/shaktra/`. Marketplace.json uses `"source": "./dist/shaktra"` to scope what gets installed. Dev files stay at repo root and are never shipped.
- **Multi-plugin marketplace** — The repo is structured as a marketplace where Shaktra is one plugin. Future plugins can be added as sibling directories.

## Design Constraints

Check every file against these:

- No single file over 300 lines
- No content duplication across layers (skill defines, agent references — never both)
- No dead code, disabled stubs, or orphaned files
- Severity taxonomy (P0-P3) defined in exactly ONE file: `dist/shaktra/skills/shaktra-reference/severity-taxonomy.md`
- All threshold values read from `.shaktra/settings.yml` — never hardcoded
- All hook scripts in Python (cross-platform, no `grep -oP`)
- Hooks block or don't exist — no warn-only
- No always-on rules consuming context every turn
- No ASCII art in agent/skill prompts
- No naming ambiguity between components

## Version Bumps

Source of truth: `dist/shaktra/.claude-plugin/plugin.json`

When bumping the plugin version, update these files to match:
- `dist/shaktra/README.md` — Version table at the top
- `README.md` — "Current version" near the bottom
- `README-marketplace.md` — Version reference
- `CHANGELOG.md` — Add a new version entry with release notes

Do **not** touch `dist/shaktra/skills/shaktra-status-dash/SKILL.md` — the version in its output format section is an example only. Status-dash reads the real version dynamically from `plugin.json` via `check_version.py`.

## Release Process

- **Local publish:** `scripts/publish-release.sh` — builds the release branch (orphan branch with only `dist/shaktra/` contents), tags, and pushes.
- **CI publish:** `.github/workflows/publish-release.yml` — runs E2E tests and publishes on push to the release branch.
- **Release branch strategy:** The release branch is an orphan branch containing only the plugin directory contents. It is auto-generated by the publish script — never commit to it directly.

## Git Conventions

- **Never** include a `Co-Authored-By` line in commit messages

## Component Overview

**8 Main Agent Skills:** `/shaktra:tpm`, `/shaktra:dev`, `/shaktra:review`, `/shaktra:adversarial-review`, `/shaktra:analyze`, `/shaktra:general`, `/shaktra:bugfix`, `/shaktra:pm`
**6 Utility Skills:** `/shaktra:init`, `/shaktra:doctor`, `/shaktra:workflow`, `/shaktra:help`, `/shaktra:status-dash`, `/shaktra:memory-stats`
**5 Internal Skills:** shaktra-quality, shaktra-tdd, shaktra-reference, shaktra-stories, shaktra-memory
**14 Sub-Agents:** architect, tpm-quality, scrummaster, product-manager, sw-engineer, test-agent, developer, sw-quality, cba-analyzer, cr-analyzer, memory-curator, bug-diagnostician, memory-retriever, adversary
**1 Command:** `/shaktra-update`
**4 Hooks:** block-main-branch, check-p0, validate-story-scope, validate-schema
