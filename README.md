# Shaktra — Maintainer & Contributor Guide

**Shaktra is an opinionated AI development framework distributed as a Claude Code plugin, orchestrating 12 specialized agents through TDD workflows to produce production-ready code.**

## What Makes Shaktra Unique

- **Enforced quality gates** — P0-P3 severity taxonomy blocks merge on critical findings
- **Two-tier QA safety net** — SW Quality checks story-level during TDD, Code Reviewer validates app-level after completion
- **TDD state machine with no shortcuts** — PLAN → RED → GREEN → QUALITY → MEMORY → COMPLETE, each transition guarded
- **Ceremony scaling** — XS stories → 70% coverage, L stories → 95%, framework adapts to complexity
- **Token-efficient architecture** — ~10K tokens per workflow step vs Forge's 150K+, on-demand skill loading

**Key Metrics:**
| Component | Count | Purpose |
|-----------|-------|---------|
| Agents | 12 | Domain experts spawned by skills |
| Skills | 16 | User-invocable orchestrators + internal references |
| Hooks | 4 | Enforcement layer (block on failure) |
| State Schemas | 5 | YAML templates for `.shaktra/` state files |

**Why contribute:** Build rigorous, scalable AI development tooling that enforces production standards through automation.

**Visual architecture:** See `Resources/workflow.drawio.png` for agent orchestration and TDD state machine diagram.

---

## For Contributors

Choose your path:

### 🌱 First-Time Contributor
- Start with [Understanding Shaktra](#understanding-shaktra)
- Read [How We Work](#how-we-work)
- Try [Your First Contribution](#your-first-contribution)

### 🔌 Plugin Developer
- Read [Plugin Architecture](#plugin-architecture)
- Understand [Discovery Mechanism](#what-is-a-claude-code-plugin)
- Review [Plugin Constraints](#plugin-constraints)

### 🏗️ Active Maintainer
- Read [CLAUDE.md](CLAUDE.md) for collaborative process
- See [Development Workflows](#development-workflows)
- Follow [Validation Checklist](#design-constraints-checklist)

### 🎯 Quality Focused
- Review [Design Philosophy](#philosophy--design-principles)
- Study [Mental Models](#mental-models)
- Check [Design Constraints](#design-constraints-checklist)

---

## Understanding Shaktra

### Philosophy & Design Principles

**1. Quality is Non-Negotiable**
- TDD state machine enforced by hooks
- P0-P3 severity taxonomy with blocking gates
- Two-tier quality safety net (SW Quality + Code Reviewer)
- Coverage thresholds (70-95%) by story tier

**2. Domain Expertise Over Generalization**
- Each workflow pillar is a Subject Matter Expert
- TPM rivals a Principal Program Manager
- Code Reviewer rivals a Principal Engineer
- Agents defer to experts, don't attempt everything

**3. Single Source of Truth**
- Every concept defined exactly once
- Severity taxonomy: ONE file only (`dist/shaktra/skills/shaktra-reference/severity-taxonomy.md`)
- Quality dimensions: ONE file only
- Everything else references, never redefines

**4. Ceremony Proportional to Complexity**
- Story tiers (XS/S/M/L) scale process rigor
- Hotfix: 70% coverage, minimal gates
- Feature: 95% coverage, full review
- Framework adapts, not the developer

**5. Reference Don't Duplicate**
- Skills define, agents reference
- Link to shaktra-reference, don't copy
- Violation example: Defining P0-P3 in both agent and skill

**6. Minimal Context, Maximum Depth**
- No file over 300 lines (complexity control)
- Skills load on-demand (10K tokens vs Forge's 150K)
- Depth from focused content, not volume

### Mental Models

**Skills Orchestrate, Agents Execute**
- Main skills (`/shaktra:tpm`) coordinate workflows
- Sub-agents (`shaktra-architect`) do the work
- Sub-agents CANNOT spawn other sub-agents
- Orchestration happens at skill level only

**Progressive Quality Gates**
- Layer 1: Hooks (always-on, blocking)
- Layer 2: SW Quality (story-level, 36 checks during TDD)
- Layer 3: Code Reviewer (app-level, 13 dimensions after completion)
- All three feed same P0-P3 taxonomy

**TDD State Machine**
```
PLAN → RED → GREEN → QUALITY → MEMORY → COMPLETE
   ↓     ↓      ↓        ↓         ↓         ↓
Gates  Gates  Gates   Gates    Lessons   Finalize
```
- Each transition has guard conditions
- No shortcuts, no skipped phases
- Handoff state machine persists in `.shaktra/.tmp/{story}/handoff.yml`

**Single Source of Truth Pattern**
- Identify: What concept needs definition?
- Define ONCE: In shaktra-reference or appropriate skill
- Reference EVERYWHERE: Link, don't duplicate
- Validate: Check no other file redefines it

### Component Hierarchy

```
┌─────────────────────────────────────────┐
│  Skills (Orchestration Layer)           │
│  /shaktra:tpm, /shaktra:dev, etc.       │
│  - User-invocable commands              │
│  - Spawn sub-agents via Task tool       │
│  - Load internal skills on-demand       │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  Agents (Execution Layer)                │
│  shaktra-architect, shaktra-sw-quality   │
│  - Spawned by skills                     │
│  - Execute specific tasks                │
│  - Return results to parent skill        │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  Hooks (Enforcement Layer)               │
│  block_main_branch, check_p0_findings    │
│  - External Python scripts               │
│  - Block on failure (no warn-only)       │
│  - Triggered by tool use or events       │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  State (Persistence Layer)               │
│  .shaktra/settings.yml, stories/*.yml    │
│  - YAML schemas validated by hooks       │
│  - Single source of truth for config     │
│  - TDD handoff state machine             │
└─────────────────────────────────────────┘
```

**Visual workflow:** See `Resources/workflow.drawio.png`

---

## Plugin Architecture

### What is a Claude Code Plugin?

Shaktra is NOT a regular project — it's a **Claude Code plugin**. This means:

1. **Discovery mechanism**: Claude Code reads `.claude-plugin/plugin.json` to discover the plugin
2. **Skill namespace**: Skills are invoked as `/shaktra:skill-name` (namespace prefix)
3. **Agent availability**: Agents defined in `agents/` are available to skills via Task tool
4. **Hook registration**: Hooks in `hooks/hooks.json` are registered on plugin load
5. **Caching**: Plugins are cached after install at `~/.claude/plugins/cache/`

### Plugin Constraints

**Critical constraints:**
- All plugin code lives in `dist/shaktra/` (no include/exclude mechanism)
- SKILL.md files MUST have YAML frontmatter with `name` and `description`
- Hook script paths use `${CLAUDE_PLUGIN_ROOT}` for portability
- Main skills MUST NOT use `context: fork` (they run inline to spawn agents)
- Sub-agents CANNOT spawn other sub-agents (no nested orchestration)

**Directory structure:**
```
dist/shaktra/                    # THE PLUGIN (everything here gets installed)
├── .claude-plugin/
│   └── plugin.json             # REQUIRED: Plugin manifest
├── agents/                     # Sub-agent definitions
├── skills/                     # Skill definitions (YAML frontmatter required)
├── hooks/hooks.json            # Hook configurations
├── scripts/                    # Hook implementation scripts (Python)
├── templates/                  # State file templates for /shaktra:init
└── README.md                   # User-facing docs (ships with plugin)
```

**Dev-only files (NOT installed):**
```
.claude-plugin/marketplace.json  # Marketplace catalog (source: "./dist/shaktra")
docs/                           # Architecture, phase plans
Resources/                      # Diagrams, reference docs
CLAUDE.md                       # Development instructions
README.md (root)                # This file (maintainer guide)
```

**Testing implication:**
- `--plugin-dir` skips install pipeline (fast iteration)
- Full install testing exercises discovery mechanism
- Always test both before finalizing a phase

---

## Repository Guide

### Directory Structure

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

### What Goes Where

**When adding a new component, use this decision tree:**

**User-invocable orchestrator?**
→ Create skill: `dist/shaktra/skills/shaktra-{name}/SKILL.md`
→ Update component count in CLAUDE.md and publish-release.sh

**Execution logic for specific task?**
→ Create agent: `dist/shaktra/agents/shaktra-{name}.md`
→ Update agent count in CLAUDE.md and publish-release.sh

**Shared knowledge/constants?**
→ Add to existing internal skill: `dist/shaktra/skills/shaktra-reference/`
→ Never create new internal skill without discussion

**Constraint enforcement?**
→ Add hook entry: `dist/shaktra/hooks/hooks.json`
→ Create Python script: `dist/shaktra/scripts/{name}.py`
→ Update hook count in publish-release.sh

**State file template?**
→ Add to: `dist/shaktra/templates/{name}.yml`
→ Reference from shaktra-init skill

**Architecture/dev documentation?**
→ Add to: `docs/` (not shipped with plugin)

**Diagram or reference?**
→ Add to: `Resources/` (not shipped with plugin)

### Component Counts

These must match validation expectations (checked in publish-release.sh):

- **Agents:** 12
- **Skills:** 16 (10 user-invocable, 6 internal)
- **Hook scripts:** 5
- **State schemas:** 5

---

## Development Workflows

### Setup

**Prerequisites:**
- Claude Code CLI installed
- Python 3.8+ (for hook scripts)
- Git (for version control)
- Bash (for release script)

**Quick iteration:**
```bash
# Load plugin directly from disk (skips install pipeline)
claude --plugin-dir dist/shaktra/
```

**Full install testing:**
```bash
# Local file path install (simulates user installing from GitHub clone)
/plugin install /absolute/path/to/shaktra-plugin/dist/shaktra

# After pushing to GitHub, test remote install
/plugin install https://github.com/im-shashanks/shaktra-plugin.git

# Test marketplace discovery
/plugin marketplace add https://github.com/im-shashanks/claude-plugins.git
/plugin install shaktra@cc-plugins
```

### Your First Contribution

**Good first issues:**
1. Add example to existing skill documentation
2. Improve error messages in hook scripts
3. Add test case to hook script tests
4. Fix typos or improve clarity in agent personas
5. Add validation to existing schemas

**End-to-end workflow:**

1. **Fork and clone**
   ```bash
   git clone https://github.com/{your-username}/shaktra-plugin.git
   cd shaktra-plugin
   ```

2. **Create feature branch FROM main**
   ```bash
   # Always branch from main, never from release
   git checkout main
   git pull origin main
   git checkout -b docs/improve-severity-examples
   ```

3. **Make your change**
   - Edit the relevant file (respect 300-line limit)
   - Check design constraints (see checklist below)

4. **Test locally**
   ```bash
   # Quick test
   claude --plugin-dir dist/shaktra/
   /shaktra:doctor

   # Full install test
   /plugin install /absolute/path/to/shaktra-plugin/dist/shaktra
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "docs: improve severity taxonomy examples"
   git push origin docs/improve-severity-examples
   ```

6. **Create PR to main**
   - Base branch: `main` (NOT release)
   - Title: Clear, descriptive, under 70 chars
   - Description: Explain WHY (not what)
   - Reference any related issues

### Working on a Feature (End-to-End Example)

**Scenario:** Adding a new quality check to SW Quality agent

**Day 1: Planning**
```bash
# Read relevant architecture docs
cat README.md  # This file
cat CLAUDE.md  # Collaborative process

# Understand the component
cat dist/shaktra/agents/shaktra-sw-quality.md
cat dist/shaktra/skills/shaktra-quality/quick-check.md
```

**Day 1: Design Proposal**
- What quality check is needed? (e.g., detect hardcoded credentials)
- Where does it fit? (P0 severity, quick-check mode)
- What's the detection logic?
- Proposed approach: Document and discuss

**Day 2: Wait for Approval**
- User reviews proposal
- Discuss tradeoffs, adjust approach if needed
- Get explicit "proceed with implementation" approval

**Day 3-4: Implementation**
```bash
# Create feature branch FROM main
git checkout main
git pull origin main
git checkout -b feat/detect-hardcoded-credentials

# Add the quality check
# Edit dist/shaktra/skills/shaktra-quality/quick-check.md
# Add detection pattern under P0 Critical Checks section

# Update agent to reference the new check
# Edit dist/shaktra/agents/shaktra-sw-quality.md if needed

# Add test case
# Edit dist/shaktra/scripts/test_quality_checks.py (if exists)
```

**Day 5: Validation**
```bash
# Check design constraints
find dist/shaktra -name "*.md" | while read f; do
  lines=$(wc -l < "$f")
  [ "$lines" -gt 300 ] && echo "$f: $lines lines"
done

# Test quick iteration
claude --plugin-dir dist/shaktra/
/shaktra:dev ST-001

# Test full install
/plugin install /path/to/shaktra-plugin/dist/shaktra
/shaktra:doctor

# Verify no duplication (e.g., severity defined in multiple places)
grep -r "hardcoded credentials" dist/shaktra/skills/
grep -r "hardcoded credentials" dist/shaktra/agents/
# Should be defined once, referenced elsewhere
```

**Day 6: Create PR**
```bash
# Commit and push
git add dist/shaktra/skills/shaktra-quality/quick-check.md
git commit -m "feat: add hardcoded credentials detection to P0 checks"
git push origin feat/detect-hardcoded-credentials

# Create PR: feat/detect-hardcoded-credentials → main
# Base: main (NOT release)
# Title: "feat: Add hardcoded credentials detection to P0 checks"
# Description: Explain why this check is needed and how it works
```

**Feature validation checklist:**
- [ ] Design constraints met (300-line limit, no duplication, etc.)
- [ ] Component counts still match (if changed)
- [ ] Tested with `--plugin-dir` and full install
- [ ] Quality check triggers correctly
- [ ] Documentation updated

### Testing Philosophy

Shaktra has three testing layers:

| Layer | What | Speed | Cost |
|-------|------|-------|------|
| **Hook unit tests** | Python scripts in `dist/shaktra/scripts/` | Fast (seconds) | Free |
| **L1-L4 Audit** | Static checks — file structure, references, schemas | Fast (seconds) | Free |
| **L5 Workflow tests** | Live end-to-end skill execution with real sub-agents | Slow (minutes) | API costs |

**19 automated tests** (14 positive + 5 negative) covering every workflow:

| Category | Tests | What They Prove |
|----------|-------|-----------------|
| Smoke (5) | help, doctor, status-dash, general, workflow | Skills load and execute without error |
| Greenfield (5) | init, pm, tpm, dev, review | Full lifecycle from project setup through code review |
| Brownfield (2) | init-brownfield, analyze | Existing codebase onboarding and assessment |
| Hotfix (1) | tpm-hotfix | Trivial-tier fast path |
| Bugfix (1) | bugfix | Diagnosis → TDD fix pipeline |
| Negative (5) | dev-no-settings, dev-blocked-story, dev-sparse-story, review-incomplete-dev, init-already-exists | Pre-flight checks catch invalid state |

Every test is standalone — own temp directory, own fixtures, no shared state. Tests can run in any order.

**How we test:**

```bash
# Unit tests (fast, during development)
python3 -m pytest dist/shaktra/scripts/

# Automated workflow tests (moderate, before PR)
python3 tests/workflows/run_workflow_tests.py --smoke        # Smoke tests (~2 min)
python3 tests/workflows/run_workflow_tests.py --negative     # Error paths (~5 min)
python3 tests/workflows/run_workflow_tests.py --test tpm     # Single workflow (~20 min)
python3 tests/workflows/run_workflow_tests.py                # Full suite (~60-90 min)

# Manual integration (ad-hoc)
claude --plugin-dir dist/shaktra/
/shaktra:init
/shaktra:tpm "add user auth"

# Release tests (slow, before publish)
./scripts/publish-release.sh
```

### Tested in Action

Real logs from automated test runs — this is what the framework produces unattended:

<details>
<summary><b>Bugfix workflow</b> — diagnosis to TDD fix in ~13 minutes</summary>

```
[14:23:52] [bugfix-orchestrator] started — investigating divide function ZeroDivisionError bug
[14:24:51] PHASE: reproduce started
[14:25:02] PHASE: reproduce complete — bug confirmed
[14:25:29] PHASE: gather-evidence complete — RC-LOGIC-1 confirmed, RC-DATA-1 eliminated
[14:26:14] WRITE: .shaktra/diagnosis/BUG-001-diagnosis.yml
[14:26:37] DIAGNOSIS_COMPLETE — root cause: RC-LOGIC, location: src/calculator.py:2
[14:26:45] PHASE: REMEDIATION started — routing to TDD pipeline for BUG-001
[14:28:55] PHASE: PLAN complete
[14:31:12] PHASE: RED complete — 2 failing tests (valid RED), 7 passing
[14:32:29] QUALITY: verdict=BLOCKED findings=2 (1 P0: missing float zero test)
[14:32:56] QUALITY-FIX: fixing 1 finding in tests/test_calculator.py
[14:35:33] PHASE: GREEN complete — all 10 tests pass, 100% coverage
[14:36:39] QUALITY: verdict=PASS findings=0
```

Validator: 9/10 checks passed. Diagnosis artifact, bug story, root cause, TDD fix all verified.
</details>

<details>
<summary><b>Dev workflow</b> — full TDD pipeline in ~19 minutes (29 tests, 98% coverage)</summary>

```
[14:45:23] [SDM] started — develop story ST-TEST-001
[14:45:55] PHASE: pre-flight complete — all 3 checks passed
[14:48:20] PHASE: plan complete
[14:49:18] QUALITY: verdict=BLOCKED findings=5
[14:50:21] QUALITY-FIX: fixing 5 findings in implementation_plan.md
[14:52:59] branch feat/ST-TEST-001-user-registration created
[14:53:14] PHASE: red started — test-agent writing failing tests
[14:56:13] WRITE: tests/test_email_validator.py, test_password_utils.py, test_user_repository.py, test_user_service.py, test_user_routes.py
[14:58:01] PHASE: red complete
[14:59:37] QUALITY: verdict=CHECK_PASSED
[15:00:18] PHASE: green started — developer implementing code
[15:03:10] WRITE: src/models/user.py, src/exceptions.py, src/utils/password_utils.py, src/utils/email_validator.py, src/repositories/user_repository.py, src/services/user_service.py, src/api/user_routes.py
[15:03:39] [developer] complete — 29 tests, 98% coverage
```

Validator: 18/19 checks passed. Full layered architecture (7 components), quality gates at every phase.
</details>

See `tests/workflows/README.md` for full documentation on the automated test framework, available tests, debugging, and cost expectations.

---

## Contributing

### How We Work

Shaktra follows a **collaborative build** process — every significant component or change is discussed before implementation.

**The Process:**

1. **Understand Current State**
   - Review existing components and architecture
   - Read CLAUDE.md for project context
   - Study relevant skills, agents, or hooks
   - Document what exists and how it works

2. **Discuss Before Implementing**
   - Present your understanding of the problem/opportunity
   - Propose your approach
   - Discuss tradeoffs (e.g., simplicity vs capability)
   - Get explicit approval to proceed

3. **Implement After Agreement**
   - Only after approval, build the component
   - Follow the agreed design
   - Respect design constraints (300-line limit, no duplication, etc.)

4. **Validate Against Constraints**
   - Check every deliverable against design constraints
   - Run `/shaktra:doctor` to validate
   - Test with both `--plugin-dir` and full install
   - Verify quality standards met

**Why this process?**
- Prevents wasted effort on rejected approaches
- Ensures alignment on tradeoffs before committing code
- Builds shared understanding of design decisions
- Documents rationale for future contributors

### Git Workflow

**Branch Structure:**

Shaktra uses a two-branch system:

- **`main`** — Active development branch
  - All development happens here
  - Create feature branches FROM main
  - Merge PRs back TO main
  - This is where contributors work

- **`release`** — Distribution branch (NEVER touch manually)
  - Auto-generated by `scripts/publish-release.sh`
  - Orphan branch with clean history
  - Contains only plugin files (dist/shaktra/ contents promoted to root)
  - Users install from this branch
  - **DO NOT create branches from release**
  - **DO NOT merge to release manually**

**Development Workflow:**

```bash
# 1. Start from main
git checkout main
git pull origin main

# 2. Create feature branch FROM main
git checkout -b feat/add-quality-check

# 3. Make your changes
# Edit files in dist/shaktra/

# 4. Test locally
claude --plugin-dir dist/shaktra/

# 5. Commit to your feature branch
git add .
git commit -m "feat: add hardcoded credentials check"

# 6. Push feature branch
git push origin feat/add-quality-check

# 7. Create PR to merge back to main
# PR: feat/add-quality-check → main
```

**Release Process:**

When ready to publish a new version:

```bash
# 1. Ensure you're on main with clean state
git checkout main
git status  # Should be clean

# 2. Run release script
./scripts/publish-release.sh

# This script:
# - Creates orphan `release` branch
# - Copies dist/shaktra/ contents to root
# - Transforms marketplace.json source path
# - Creates clean commit: "Release from main@{sha}"

# 3. Push release branch
./scripts/publish-release.sh --push
# or manually:
git push origin release --force
```

**How Release Branch Works:**

The release branch is a **build artifact**, not a development branch. Here's what happens:

1. `publish-release.sh` creates an orphan branch (no history)
2. Copies plugin files from `dist/shaktra/` to root level
3. Excludes dev-only files (docs/, Resources/, CLAUDE.md, root README.md)
4. Transforms `.claude-plugin/marketplace.json` source path from "./dist/shaktra" to "."
5. Creates single commit with reference to main branch SHA

**Result:**
- `main` branch: Full repo with dev docs, scripts, Resources
- `release` branch: Clean plugin-only structure for distribution
- Users install from `release` via `/plugin install`

**Important:**
- ⚠️ NEVER branch from `release`
- ⚠️ NEVER commit directly to `release`
- ⚠️ NEVER merge PRs to `release`
- ✅ Always branch from `main`
- ✅ Always merge PRs to `main`
- ✅ Use `publish-release.sh` to update `release`

### Design Constraints Checklist

Before any PR, verify:

- [ ] **No file over 300 lines**
  - Why: Complexity control, single clear purpose per file
  - How to check: `find dist/shaktra -name "*.md" -o -name "*.py" | while read f; do lines=$(wc -l < "$f"); [ "$lines" -gt 300 ] && echo "$f: $lines"; done`

- [ ] **No content duplication**
  - Why: Single source of truth, avoid divergence
  - Example violation: Defining P0-P3 in both shaktra-quality and sw-quality agent
  - How to check: Search for key definitions across skills/ and agents/

- [ ] **No dead code or disabled stubs**
  - Why: Forge had 40% dead code, reduced maintainability
  - How to check: Every function/section must be called, no commented-out blocks

- [ ] **Severity taxonomy in ONE file only**
  - Why: Core enforcement mechanism, must be consistent
  - File: `dist/shaktra/skills/shaktra-reference/severity-taxonomy.md`
  - How to check: `grep -r "P0.*Critical" dist/shaktra/` should find only one definition

- [ ] **All thresholds read from settings.yml**
  - Why: Configuration flexibility, no hardcoded values
  - Example: Coverage threshold read from `.shaktra/settings.yml`, not hardcoded as 90
  - How to check: Search for numeric thresholds (70, 80, 90, 95) in skills/agents — should find references to settings.yml

- [ ] **All hook scripts in Python**
  - Why: Cross-platform (Forge used bash with `grep -oP`, failed on macOS)
  - How to check: All files in `dist/shaktra/scripts/` must be `.py`

- [ ] **Hooks block or don't exist**
  - Why: Enforcement layer must enforce, warn-only is ineffective
  - How to check: Hook scripts return exit code 1 on failure, 0 on pass

- [ ] **No always-on rules consuming context**
  - Why: Token efficiency, context pollution
  - How to check: Forge had always-on auto-router, Shaktra uses `/shaktra:workflow` on-demand

- [ ] **No ASCII art in prompts**
  - Why: Token waste, readability issues
  - How to check: Visual grep for box-drawing characters in skills/ and agents/

- [ ] **No naming ambiguity**
  - Why: Clear component identity, avoid confusion
  - Example: sw-quality (agent) vs shaktra-quality (skill) — distinct purposes

- [ ] **Component counts match validation**
  - Why: Release validation depends on these counts
  - How to check: Count agents/, skills/, scripts/ — must match publish-release.sh expectations

### Common Mistakes

**1. Defining content in both skill and agent (duplication)**

❌ **Wrong:**
```markdown
# dist/shaktra/skills/shaktra-quality/SKILL.md
P0: Critical issues like timeouts, credentials in logs

# dist/shaktra/agents/sw-quality.md
P0 findings include: timeouts, credentials in logs, injection risks
```

✅ **Right:**
```markdown
# dist/shaktra/skills/shaktra-reference/severity-taxonomy.md
P0: Critical issues like timeouts, credentials in logs, injection

# dist/shaktra/agents/sw-quality.md
Use P0-P3 severity from shaktra-reference/severity-taxonomy.md
```

**2. Hardcoding thresholds instead of reading from settings.yml**

❌ **Wrong:**
```markdown
if coverage < 90:
    return BLOCKED
```

✅ **Right:**
```markdown
Read `.shaktra/settings.yml` for coverage threshold
if coverage < tier_threshold:
    return BLOCKED
```

**3. Creating warn-only hooks**

❌ **Wrong:**
```python
# Just print warning, always exit 0
print("Warning: P0 findings exist")
sys.exit(0)
```

✅ **Right:**
```python
# Block on P0 findings
if p0_count > 0:
    print("Error: P0 findings prevent completion")
    sys.exit(1)
sys.exit(0)
```

**4. Files over 300 lines**

❌ **Wrong:**
- Single 800-line skill file with multiple concerns

✅ **Right:**
- Split into sub-files (shaktra-reference uses this pattern)
- Main SKILL.md orchestrates, references sub-files

**5. Using bash shell-isms in hook scripts**

❌ **Wrong:**
```bash
grep -oP 'pattern' file  # -P flag doesn't exist on macOS
```

✅ **Right:**
```python
import re
pattern = re.compile(r'pattern')
```

**6. Main skills using `context: fork`**

❌ **Wrong:**
```yaml
---
name: shaktra-dev
context: fork  # Breaks ability to spawn sub-agents
---
```

✅ **Right:**
```yaml
---
name: shaktra-dev
# No context field = runs inline, can spawn agents
---
```

**7. Sub-agents spawning other sub-agents**

❌ **Wrong:**
```markdown
# shaktra-architect.md
Use the Task tool to spawn shaktra-researcher agent
```

✅ **Right:**
```markdown
# shaktra-tpm/SKILL.md (orchestrator)
Spawn shaktra-architect, then spawn shaktra-researcher
```

---

## Reference

### Documentation Index

**For Users (shipped with plugin):**
- `dist/shaktra/README.md` — Installation, quick start, workflows

**For Contributors (dev-only):**
- `README.md` (this file) — Development guide, architecture, contributing
- `CLAUDE.md` — Collaborative build process, design decisions
- `docs/shaktra-plan/architecture-overview.md` — Detailed architecture
- `docs/shaktra-plan/phases/` — Implementation phase plans
- `docs/Forge-analysis/analysis-report.md` — How Shaktra differs from Forge

**Visual:**
- `Resources/workflow.drawio.png` — Agent orchestration and TDD state machine

### Validation Checklist

Before declaring any phase complete:

```bash
# Quick validation
/shaktra:doctor

# Verify all skills load
/shaktra:help

# Full end-to-end
/shaktra:init
/shaktra:tpm "add feature"
/shaktra:dev ST-001
/shaktra:review ST-001
/shaktra:analyze
/shaktra:bugfix
/shaktra:workflow
```

---

## FAQ

**Q: Why is the plugin in `dist/shaktra/` instead of at the repo root?**

A: Claude Code's plugin system has no include/exclude mechanism. The marketplace.json uses `"source": "./dist/shaktra"` to scope what gets installed. This keeps dev-only files (docs/, Resources/, CLAUDE.md) at the repo root and out of user installations.

**Q: Why can't I use `context: fork` in main skills?**

A: Main skills (like shaktra-tpm) need to run inline in the main conversation so they can use the Task tool to spawn sub-agents. Forked context can't spawn agents. Only use `context: fork` for skills that don't orchestrate.

**Q: Why is severity taxonomy defined in only ONE file?**

A: Single source of truth. P0-P3 definitions are the enforcement mechanism — if they diverge across files, merge gate logic becomes inconsistent. One definition, many references.

**Q: Why Python for hooks instead of bash?**

A: Cross-platform. Forge used `grep -oP` which doesn't exist on macOS. Python runs everywhere and has better error handling.

**Q: Why are there two quality agents (sw-quality and cr-analyzer)?**

A: Different scopes. SW Quality checks story-level during TDD (does this story meet its acceptance criteria?). Code Reviewer checks app-level after completion (does this integrate well? Any broader issues?). Non-redundant, complementary.

**Q: How do I avoid duplicating content?**

A: Follow "reference don't duplicate" principle:
1. Identify the canonical location (usually shaktra-reference)
2. Define the concept ONCE in that location
3. All other files link to it (e.g., "See severity-taxonomy.md for P0-P3 definitions")
4. Validate: `grep -r "P0:" dist/shaktra/` should find only one full definition

**Q: Why is the 300-line limit so strict?**

A: Complexity control. Forge had 1,481-line skill files that were impossible to maintain. 300 lines forces single clear purpose per file. If you hit the limit, split into sub-files (like shaktra-reference does).

**Q: What's the difference between this README and CLAUDE.md?**

A: This README is comprehensive architecture and contributor guide (you are here). CLAUDE.md is process guide (how we work on this project). Read both when starting development.

**Q: Can I add a new internal skill?**

A: Rarely. Internal skills (shaktra-reference, shaktra-quality, shaktra-tdd, shaktra-stories) are shared knowledge. Before creating a new one, ask: Does this belong in an existing internal skill? Only create new internal skills after discussion.

**Q: Why does `/shaktra:workflow` exist if we have main skills?**

A: Natural language entry point. Users can describe intent in plain English, and shaktra-workflow routes to the appropriate main skill. It's an on-demand intent classifier for better UX.

**Q: How do I test hook scripts?**

A: Unit tests with pytest:
```bash
python3 -m pytest dist/shaktra/scripts/test_validate_schema.py
```

**Q: What if my skill needs to be longer than 300 lines?**

A: Split it:
- Main SKILL.md orchestrates (< 300 lines)
- Sub-files contain deep knowledge (each < 300 lines)
- See shaktra-reference for example pattern

---

## Version History

See GitHub releases for changelog and version history.

Current version: **0.1.3**

---

## License

MIT License. See [LICENSE](dist/shaktra/LICENSE).
