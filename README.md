# Shaktra Development

**Plugin repository for the Shaktra software development framework**

This repository contains the source code for Shaktra, a Claude Code plugin that orchestrates 12 specialized AI agents through TDD workflows to produce industry-standard, production-quality code.

## Repository Structure

```
shaktra-plugin/
├── .claude-plugin/marketplace.json  # Marketplace catalog
├── dist/shaktra/                    # THE PLUGIN (installed by users)
│   ├── .claude-plugin/plugin.json   # Plugin manifest
│   ├── agents/                      # 12 sub-agent definitions
│   ├── skills/                      # 16 skills (10 user-invocable)
│   ├── hooks/hooks.json             # Hook configurations
│   ├── scripts/                     # Hook implementations (Python)
│   ├── templates/                   # State file templates
│   ├── README.md                    # User-facing documentation
│   └── LICENSE                      # MIT License
├── docs/                            # Dev-only — not shipped
│   ├── archive/                     # Phase plans, Forge analysis
│   └── Forge-analysis/              # Comparative analysis with Forge
├── Resources/                       # Dev-only — diagrams, reference
├── scripts/                         # Build and release scripts
│   └── publish-release.sh           # Release builder
├── CLAUDE.md                        # Development instructions
└── README.md                        # This file
```

**Plugin distribution:** The plugin is defined in `dist/shaktra/`. The marketplace.json file at `.claude-plugin/marketplace.json` (repo root) registers it with source path `"./dist/shaktra"`.

**User documentation:** Lives in `dist/shaktra/README.md` — this is what users read when they install the plugin.

**Dev documentation:** Lives in `/docs` and `CLAUDE.md` — not shipped with plugin installs.

---

## Architecture Overview

### Core Concepts

- **Multi-agent orchestration** — 12 specialized agents with deep domain expertise
- **TDD state machine** — PLAN → RED → GREEN → QUALITY → MEMORY → COMPLETE
- **Quality tiers** — SW Quality (story-level), Code Reviewer (app-level)
- **Sprint-based planning** — Velocity tracking, capacity allocation
- **Ceremony scaling** — Story tiers (XS/S/M/L) adjust process rigor

### Component Layers

**1. Skills** (skills/) — Orchestration layer, user-facing commands
- **Main agents:** tpm, dev, review, analyze, general, bugfix
- **Utilities:** init, doctor, workflow, help
- **Internal:** quality, tdd, reference, stories

**2. Sub-agents** (agents/) — Execution layer, spawned by skills
- **TPM workflow:** architect, tpm-quality, scrummaster, product-manager
- **Dev workflow:** sw-engineer, test-agent, developer, sw-quality
- **Other:** cba-analyzer, cr-analyzer, memory-curator, bug-diagnostician

**3. Enforcement** (hooks/ + scripts/) — Constraint validation
- **Python scripts** (cross-platform, no shell-isms)
- **Block on failure** — no warn-only mode
- **Triggered by:** tool use (Bash, Write/Edit), task completion

**4. State Management** (templates/) — YAML schemas
- `.shaktra/settings.yml` — Project configuration
- `.shaktra/stories/` — User story files
- `.shaktra/sprints.yml` — Sprint tracking
- `.shaktra/memory/` — Decision and lesson logs
- Other artifacts (designs, personas, analysis, etc.)

### Design Constraints

Every component must adhere to these constraints:

- **No file over 300 lines** — Complexity stays manageable
- **No content duplication** — Skill defines, agent references — never both
- **No dead code** — All code active, no disabled stubs
- **Single source of truth** — Severity taxonomy, quality dimensions, schemas defined once
- **All thresholds in settings.yml** — Never hardcoded
- **Hook scripts in Python** — Cross-platform, no platform-specific shell commands
- **Hooks block or don't exist** — No warn-only mode
- **No always-on rules** — Rules must be triggered, not always-running
- **No ASCII art** — In agent/skill prompts
- **No naming ambiguity** — Components have distinct, unambiguous names

---

## Development Setup

### Prerequisites

- Claude Code CLI installed
- Python 3.8+ (for hook scripts)
- Git (for version control)
- Bash (for release script)

### Quick Iteration

For fast development cycle without full plugin install:

```bash
# Load plugin directly from disk (skips install pipeline)
claude --plugin-dir dist/shaktra/
```

### Full Install Testing

For validating the install/discovery pipeline before release:

```bash
# Local file path install (simulates user installing from GitHub clone)
/plugin install /absolute/path/to/shaktra-plugin/dist/shaktra

# After pushing to GitHub, test remote install
/plugin install https://github.com/im-shashanks/shaktra-plugin.git

# Test marketplace discovery
/plugin marketplace add https://github.com/im-shashanks/claude-plugins.git
/plugin install shaktra@cc-plugins
```

### Validation Checklist

Before declaring a phase complete:

```bash
# Quick validation
/shaktra:doctor

# Verify all agents load
/shaktra:help

# Full end-to-end
/shaktra:init
/shaktra:tpm
/shaktra:dev
/shaktra:review
/shaktra:analyze
/shaktra:bugfix
/shaktra:workflow
```

---

## Contributing

### Before You Start

**Read CLAUDE.md** for:
- Collaborative build process (Reference Forge → Discuss → Implement)
- Design decisions (not to be overridden)
- Starting a phase workflow
- Component overview

**Read docs/architecture-overview.md** for:
- Detailed component layer explanations
- Constraint validation guidelines
- Phase dependencies

### Adding Components

#### New Skill

1. Create `dist/shaktra/skills/shaktra-{name}/SKILL.md` with YAML frontmatter
   ```markdown
   ---
   name: skill-display-name
   description: One-line description of what this skill does
   ---
   # Skill content (max 300 lines)
   ```

2. Skills are namespace-scoped: users invoke as `/shaktra:name`

3. Follow design constraints:
   - No file over 300 lines
   - Reference don't duplicate (link to shaktra-reference)
   - Single clear purpose

4. Register in component overview in CLAUDE.md

#### New Agent

1. Create `dist/shaktra/agents/shaktra-{name}.md` with persona
   - Full experience-based identity (not just role)
   - Expertise areas, communication style
   - Constraints and scope

2. Update agent count in:
   - CLAUDE.md (Component Overview section)
   - scripts/publish-release.sh (validation)

#### New Hook

1. Add entry to `dist/shaktra/hooks/hooks.json`
   - Matcher (tool name or regex)
   - Hook type and command
   - Python script path

2. Create Python script in `dist/shaktra/scripts/{name}.py`
   - Read `.shaktra/settings.yml` if needed
   - Print error message to stdout
   - Exit code: 0 = pass, 1 = fail (blocks operation)

3. Update hook count in scripts/publish-release.sh

### Design Constraints Checklist

Before any PR, verify:

- [ ] No file over 300 lines
- [ ] No content duplication (check skill references vs agent definitions)
- [ ] No dead code or disabled stubs
- [ ] Severity taxonomy in ONE file only: `dist/shaktra/skills/shaktra-reference/severity-taxonomy.md`
- [ ] All thresholds read from `settings.yml` (never hardcoded)
- [ ] All hook scripts in Python (cross-platform)
- [ ] Hooks block or don't exist (no warn-only)
- [ ] No always-on rules consuming context
- [ ] No ASCII art in prompts
- [ ] No naming ambiguity between components
- [ ] Component counts match validation expectations

### Git Workflow

- Feature branches for all work (never commit to main)
- No "Co-Authored-By" lines in commit messages
- Hooks enforce branch protection automatically
- PR title: clear, descriptive, under 70 chars
- PR description: explains why (not what)

### Release Process

Handled by `scripts/publish-release.sh`:

1. **Validates state:**
   - On main branch
   - Working tree clean
   - All files present
   - Component counts correct

2. **Builds release:**
   - Copies `dist/shaktra/` contents to root level
   - Promotes `.claude-plugin/plugin.json`
   - Transforms `marketplace.json` source path
   - **Copies `dist/shaktra/README.md`** as-is (no transformation)

3. **Validates release:**
   - 12 agents present
   - 16 skills present
   - 5 hook scripts present
   - No dev-only files leaked

4. **Creates release branch:**
   - Orphan branch (clean history)
   - Commit message: "Release from main@{sha}"
   - Can push with `--push` flag

**Usage:**

```bash
# Build release locally
./scripts/publish-release.sh

# Build and push to origin
./scripts/publish-release.sh --push
```

**Result:**
- `release` branch — clean, ready for distribution
- Contains only plugin files, user README, resources
- No dev docs, CLAUDE.md, or phase plans

---

## File Limits & Constraints

### No file over 300 lines

**Why:** Complexity stays manageable, every file has single clear purpose.

**Checking:**
```bash
find dist/shaktra -name "*.md" -o -name "*.py" | while read f; do
  lines=$(wc -l < "$f")
  if [ "$lines" -gt 300 ]; then
    echo "$f: $lines lines"
  fi
done
```

### No content duplication

**Pattern to avoid:** Defining something in both places
```
❌ Don't do this:
   dist/shaktra/skills/shaktra-quality/SKILL.md defines severity taxonomy
   dist/shaktra/agents/sw-quality.md redefines severity taxonomy

✅ Do this:
   dist/shaktra/skills/shaktra-reference/severity-taxonomy.md defines it (once)
   All other files reference it (link or cite)
```

### Severity taxonomy: single source of truth

**File:** `dist/shaktra/skills/shaktra-reference/severity-taxonomy.md`

**Rule:** P0-P3 definitions, merge gate logic, examples — all in ONE file. No other file may redefine or reexplain severity levels.

**Other files do:** Reference it — "See severity-taxonomy.md for P0-P3 definitions"

---

## Component Counts

These must match validation expectations (checked in publish-release.sh):

- **Agents:** 12
- **Skills:** 16 (10 user-invocable: tpm, dev, review, analyze, general, bugfix, init, doctor, workflow, help; 6 internal: quality, tdd, reference, stories, pm, status-dash)
- **Hook scripts:** 5 (block_main_branch.py, validate_story_scope.py, validate_schema.py, check_p0_findings.py, and one more)
- **Hooks.json entries:** Corresponding to scripts

---

## Development Workflow

### Phase-Based Development

Phases are defined in `docs/shaktra-plan/phases/`. Each phase:

1. **Exploration** — Understand Forge implementation, current state
2. **Design** — Propose Shaktra approach, align on tradeoffs
3. **Implementation** — Build following agreed design
4. **Validation** — Check constraints, run tests

**Starting a phase:**

```bash
# Read the phase plan
cat docs/shaktra-plan/phases/phase-XX-{name}.md

# Read architecture docs
cat docs/shaktra-plan/architecture-overview.md

# Check Forge reference
ls ~/workspace/applications/forge-claudify/...
```

Then discuss findings and approach before implementing.

### Phase Dependency Graph

See `docs/shaktra-plan/execution-plan.md` for:
- All phases and their status
- Dependencies between phases
- Critical path to completion

### Validating Against Constraints

After implementation:

1. Check design constraints (see checklist above)
2. Verify component counts
3. Run `/shaktra:doctor` in a test project
4. Check `docs/shaktra-plan/appendices.md` (Appendix A) for anti-patterns

---

## Architecture Diagrams

Visual diagrams are in `Resources/`:
- `workflow.drawio.png` — Agent orchestration and TDD state machine
- Other architecture diagrams (as developed)

---

## Testing the Plugin

### Unit Testing

Hook scripts have unit tests. Run:

```bash
# Test hook scripts
python3 -m pytest dist/shaktra/scripts/

# Test with coverage
python3 -m pytest --cov=dist/shaktra/scripts dist/shaktra/scripts/
```

### Integration Testing

Test in real Claude Code environment:

```bash
# Initialize test project
mkdir test-project && cd test-project
claude --plugin-dir /path/to/shaktra-plugin/dist/shaktra/
/shaktra:init

# Run through workflows
/shaktra:tpm
/shaktra:dev ST-001
/shaktra:review ST-001
/shaktra:doctor
```

### Release Testing

Before publishing:

```bash
./scripts/publish-release.sh
git checkout release
# Verify README is user-facing (not dev-focused)
cat README.md
# Verify no CLAUDE.md
ls -la | grep CLAUDE
# Verify plugin.json present
cat .claude-plugin/plugin.json
```

---

## Troubleshooting Development

### Plugin not loading with `--plugin-dir`

```bash
# Check plugin structure
ls -la dist/shaktra/.claude-plugin/
# Should have plugin.json

# Check for syntax errors in SKILL.md files
claude --plugin-dir dist/shaktra/
/shaktra:help
```

### Hook script failing

```bash
# Run script directly to see error
python3 dist/shaktra/scripts/validate_schema.py

# Check Python syntax
python3 -m py_compile dist/shaktra/scripts/validate_schema.py
```

### Schema validation errors during development

```bash
# Run validator on test file
python3 dist/shaktra/scripts/validate_schema.py /path/to/.shaktra/settings.yml

# Check schema definition
cat dist/shaktra/skills/shaktra-reference/schemas/settings-schema.md
```

---

## Version History

See GitHub releases for changelog and version history.

Current version: **0.1.0**

---

## License

MIT License. See [LICENSE](dist/shaktra/LICENSE).

---

## Documentation Index

- **User Guide:** `dist/shaktra/README.md` — How to use the plugin
- **Development:** `CLAUDE.md` — How to contribute
- **Architecture:** `docs/shaktra-plan/architecture-overview.md`
- **Phase Plans:** `docs/shaktra-plan/phases/` — Implementation phases
- **Forge Analysis:** `docs/Forge-analysis/analysis-report.md` — How Shaktra differs from Forge
- **Diagrams:** `Resources/` — Architecture and workflow diagrams
