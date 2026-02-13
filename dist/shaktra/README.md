# Shaktra
**Opinionated software development framework for Claude Code**

Shaktra turns Claude Code into a full software development team. Instead of a single assistant, you get 12 specialized agents — a Technical Project Manager, architect, developers, quality reviewers, and more — each with deep domain expertise, working together through structured TDD workflows with quality gates at every phase.

| | |
|---|---|
| **Version** | 0.1.2 |
| **License** | MIT |
| **Agents** | 12 specialized sub-agents |
| **Skills** | 16 total (10 user-invocable) |
| **Quality** | 36 checks per TDD gate, 13 review dimensions |

---

## What is Shaktra?

Shaktra is built on five pillars:

1. **TDD-first development** — Tests are written before code, always. Quality is part of the workflow, not an afterthought.
2. **Multi-agent orchestration** — 12 specialized agents, each with a distinct role and deep expertise in their domain.
3. **Quality gates at every phase** — P0-P3 severity taxonomy with automated enforcement. P0 findings block merge — no exceptions.
4. **Sprint-based planning** — Velocity tracking, capacity allocation, and backlog management for sustainable delivery.
5. **Ceremony scaling** — Story tiers (XS/S/M/L) determine how much process each task gets — trivial stories get minimal ceremony, complex stories get full architecture review.

---

## How It Works

Shaktra uses a layered agent system where **skills orchestrate** and **agents execute**:

- **TPM** receives a feature request → dispatches Architect, Scrummaster, Product Manager to design and plan
- **Dev Manager** receives a story → orchestrates SW Engineer, Test Agent, Developer through TDD
- **Code Reviewer** receives completed work → runs 13-dimension review with verification tests
- **Codebase Analyzer** receives a brownfield project → executes 9-dimension parallel analysis
- **Bug Diagnostician** receives a bug report → executes 5-step diagnosis then TDD remediation

Two quality tiers operate at different scopes:

- **SW Quality** checks story-level quality during TDD (36 checks per gate)
- **Code Reviewer** checks app-level quality after completion (13 dimensions)

Every implementation follows a strict TDD state machine: **PLAN → RED → GREEN → QUALITY → MEMORY → COMPLETE**. Quality gates must pass at each transition — there are no shortcuts.

---

## Installation

### Marketplace (recommended)

```
/plugin marketplace add https://github.com/im-shashanks/claude-plugins.git
/plugin install shaktra@cc-plugins
```

### Direct from GitHub

```
/plugin install https://github.com/im-shashanks/claude-plugins.git
```

### Updating

Claude Code's plugin cache does not always refresh automatically when a new version is published. If you're running an older version or seeing stale behavior after an update:

```bash
# 1. Clear the plugin cache
rm -rf ~/.claude/plugins/cache/

# 2. Restart Claude Code

# 3. Reinstall
/plugin install shaktra@cc-plugins
```

You can check your installed version with `/shaktra:status-dash` — it compares your local version against the latest release.

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

## Commands Reference

### Main Workflow Commands

#### `/shaktra:tpm` — Technical Project Manager
**Purpose:** Design documents, user story creation, sprint planning, hotfix routing

**When to use:**
- Starting a new feature or epic
- Breaking down a large request into stories
- Planning a sprint
- Creating a hotfix with minimal process

**Typical workflow:**
1. You describe what you want to build
2. TPM creates a design doc with architecture, API contracts, data models
3. TPM breaks the design into stories (XS/S/M/L) with acceptance criteria
4. TPM schedules stories into a sprint based on velocity
5. You then invoke `/shaktra:dev` on each story to implement

**Options:**
- `hotfix: <description>` — Fast-track minimal-ceremony hotfix (70% coverage)
- `epic: <description>` — Large multi-sprint feature

#### `/shaktra:dev <story-id>` — Developer
**Purpose:** Implement a story with TDD, following the state machine

**State machine:** PLAN → RED → GREEN → QUALITY → MEMORY → COMPLETE

**When to use:**
- Implementing any user story from the backlog
- Refactoring existing code with test coverage
- Fixing a bug after diagnosis

**Typical workflow:**
1. Dev Manager reads the story from `.shaktra/stories/<story-id>.md`
2. PLAN phase: Develop a test plan and skeleton code structure
3. RED phase: Write failing tests
4. GREEN phase: Write minimal code to pass tests
5. QUALITY phase: Run quality checks (36 checks), fix any findings
6. MEMORY phase: Document decisions and lessons learned
7. COMPLETE: Story ready for review

**Quality gates:** Each transition must pass quality checks. P0 findings block progress.

**Coverage thresholds by tier:**
- XS: 70% (hotfix coverage)
- S: 80%
- M: 90%
- L: 95%

#### `/shaktra:review <story-id|pr>` — Code Reviewer
**Purpose:** Story review and PR review with 13-dimension quality analysis

**When to use:**
- After `/shaktra:dev` completes (story review)
- Before merging a PR (PR review)
- Validating architectural decisions

**13 review dimensions:**
1. **Contract & API** — Do public signatures match behavior? Is input validated?
2. **Failure Modes** — Does every operation that can fail have an error path?
3. **Data Integrity** — Are writes atomic? Is data validated before persistence?
4. **Concurrency** — Is shared state protected? Are operations atomic?
5. **Security** — Are inputs sanitized? Are secrets excluded? Is auth enforced?
6. **Observability** — Are operations logged? Do calls carry trace IDs?
7. **Performance** — Do network calls have timeouts? Are collections bounded?
8. **Maintainability** — Does each unit have single responsibility? Is code readable?
9. **Testing** — Do tests cover edge cases? Are tests independent?
10. **Deployment** — Is change backward-compatible? Can it be rolled back?
11. **Configuration** — Are values externalized? Are secrets handled securely?
12. **Dependencies** — Are imports real packages? Are versions pinned?
13. **Compatibility** — Is backward compatibility maintained? Are breaking changes documented?

**Verification tests:** Code Reviewer runs at least 5 independent verification tests to validate behavior beyond what the story's tests check.

**P0 rules:** Any P0 finding blocks merge. Must be fixed or escalated.

#### `/shaktra:analyze` — Codebase Analyzer
**Purpose:** Brownfield codebase assessment across 9 dimensions

**When to use:**
- On-boarding to an unfamiliar codebase
- Assessing development readiness before feature work
- Planning refactoring efforts

**9 analysis dimensions:**
1. **Architecture** — Layering, modularity, dependency cycles
2. **Testing** — Coverage, test pyramid, test quality
3. **Code Quality** — Duplication, complexity, maintainability
4. **Error Handling** — Exception handling patterns, error propagation
5. **Performance** — Hot paths, resource leaks, N+1 queries
6. **Security** — Injection vulnerabilities, authentication, data protection
7. **Observability** — Logging, tracing, monitoring instrumentation
8. **Dependencies** — Outdated packages, security vulnerabilities, license compliance
9. **Documentation** — API docs, architecture docs, runbook completeness

**Output:** Detailed findings organized by dimension with evidence, severity, and remediation guidance.

#### `/shaktra:bugfix <bug-description>` — Bug Diagnostician
**Purpose:** 5-step bug diagnosis followed by TDD remediation

**When to use:**
- Investigating a reported bug
- Triaging a production issue
- Understanding root cause before fixing

**5-step diagnosis:**
1. **Triage** — Is this a real bug? Reproducible? Security-related?
2. **Reproduce** — Create minimal test case demonstrating the bug
3. **Root Cause** — Trace the code path, identify what's wrong
4. **Blast Radius** — What else could this bug affect?
5. **Create Story** — Write a user story with test case for TDD remediation

**Remediation:** After diagnosis, creates a story for `/shaktra:dev` to fix via TDD.

#### `/shaktra:general` — Domain Expert
**Purpose:** Domain expertise, architectural guidance, technical questions

**When to use:**
- Architectural questions (patterns, tradeoffs)
- Domain expertise on unfamiliar technology
- Technical design review
- "How do we..." questions

**Capabilities:**
- Design pattern suggestions
- Technology tradeoff analysis
- Best practices for your language/framework
- Architectural alternatives evaluation

### Utility Commands

#### `/shaktra:init` — Initialize Project
Creates the `.shaktra/` directory with default configuration, templates, and project structure.

**Interactive setup:**
- Project type: greenfield or brownfield
- Language and framework
- Test framework and coverage tool
- Architecture style (layered, hexagonal, clean, mvc, etc.)
- Package manager

**Creates:**
- `.shaktra/settings.yml` — Project configuration
- `.shaktra/sprints.yml` — Sprint tracking
- `.shaktra/memory/` — Decision and lesson log
- `.shaktra/stories/` — User story storage
- `.shaktra/designs/` — Design document storage
- `.shaktra/templates/` — Artifact templates

#### `/shaktra:doctor` — Health Check
Diagnoses framework health and configuration issues.

**Checks:**
- Plugin structure (all required files present)
- `.shaktra/` configuration valid YAML
- `settings.yml` has all required keys
- Hook scripts executable and valid Python
- Agent and skill count matches expectations
- No design constraint violations (no >300-line files, etc.)
- All P0 findings resolved

**Output:** Pass/fail for each check with remediation guidance for failures.

**Read-only:** Doctor reports problems but never fixes them. You stay in control.

#### `/shaktra:workflow` — Smart Router
Natural language router that automatically dispatches you to the right agent.

**When to use:**
- When you're not sure which command to use
- Complex requests that might span multiple agents
- You prefer natural language over command names

**Example:** "We need to refactor the authentication module but we're worried about breaking things" → Routes to `/shaktra:analyze` (assessment) + `/shaktra:dev` (refactoring with TDD)

#### `/shaktra:help` — Help & Documentation
Shows all commands, workflows, and detailed usage guide.

**Available anytime for reference within Claude Code.**

---

## Workflows & Use Cases

### TPM Workflow: Design → Stories → Sprint

**When to use:** Starting a feature, epic, or hotfix

**Step-by-step:**

1. Describe your feature request in natural language
2. TPM creates a design doc with:
   - Acceptance criteria
   - Architecture overview
   - API contracts (if applicable)
   - Data models
   - Edge cases
3. TPM breaks design into stories with story points
4. TPM assigns stories to sprint based on velocity
5. You execute stories via `/shaktra:dev`

**Example session:**
```
You: /shaktra:tpm
"We need to add OAuth 2.0 support to the API"

TPM output:
- Design doc: Authentication architecture, token handling, refresh flow
- Stories:
  ST-001 (M): Implement OAuth provider integration (8 points)
  ST-002 (M): Add token management and refresh logic (8 points)
  ST-003 (S): Add login endpoint and UI (5 points)
  ST-004 (S): Add tests for OAuth flows (5 points)
- Sprint: All stories in Sprint 1
```

### Dev Workflow: TDD State Machine

**When to use:** Implementing any story

**State machine steps:**

```
PLAN
 ↓ (quality gate)
RED (write tests)
 ↓ (quality gate)
GREEN (pass tests)
 ↓ (quality gate)
QUALITY (fix findings)
 ↓ (quality gate)
MEMORY (document decisions)
 ↓ (quality gate)
COMPLETE (ready for review)
```

**Quality gates:** 36 checks per transition. P0 findings block progress.

**Example: Implementing ST-001**

```
You: /shaktra:dev ST-001

Dev Manager reads the story, then:

1. PLAN phase:
   - Outline test cases needed
   - Sketch code structure
   - Question edge cases

2. RED phase:
   - Write failing tests for all acceptance criteria
   - Coverage at this point: ~5%

3. GREEN phase:
   - Write minimal code to pass tests
   - Coverage at this point: ~85%

4. QUALITY phase:
   - Run 36 quality checks
   - Fix any P1/P2 findings
   - Add coverage-improving tests if needed

5. MEMORY phase:
   - Document architectural decisions
   - Note any learnings or gotchas

6. COMPLETE:
   - Story ready for /shaktra:review
```

**Coverage by story tier:**
- XS: 70% (hotfixes only)
- S: 80%
- M: 90%
- L: 95%

### Code Review Workflow: 13-Dimension Review

**When to use:** After `/shaktra:dev` completes a story, or before merging a PR

**Process:**

1. You invoke `/shaktra:review ST-001` or `/shaktra:review #123`
2. Code Reviewer runs all 13 dimensions of analysis
3. Each dimension has 3 checks + P0 trigger assessment
4. Verification tests (≥5) independently validate behavior
5. Findings categorized as P0/P1/P2/P3
6. P0 blocks merge, P1 subject to threshold, P2-P3 for future work

**13 dimensions explained:**
- **A: Contract & API** — Do APIs do what they promise?
- **B: Failure Modes** — Do we handle failures correctly?
- **C: Data Integrity** — Is data safe?
- **D: Concurrency** — Are concurrent operations safe?
- **E: Security** — Are we secure?
- **F: Observability** — Can we see what's happening?
- **G: Performance** — Is it fast enough?
- **H: Maintainability** — Is it understandable?
- **I: Testing** — Is it well-tested?
- **J: Deployment** — Can we deploy safely?
- **K: Configuration** — Is configuration handled safely?
- **L: Dependencies** — Are dependencies real and managed?
- **M: Compatibility** — Does it maintain compatibility?

**Merge gate logic:**
```
if P0 findings > 0:
    BLOCKED — fix all P0s first
else if P1 findings > threshold:
    BLOCKED — too many major issues
else:
    PASS — ready to merge
```

### Codebase Analysis Workflow: Brownfield Assessment

**When to use:** On-boarding to a new codebase, planning refactoring

**Process:**

1. You invoke `/shaktra:analyze` in a brownfield project
2. Analyzer assesses code across 9 dimensions in parallel
3. Each dimension produces:
   - Health score
   - Key findings (organized by severity)
   - Improvement roadmap
4. Output stored in `.shaktra/analysis/` for reference

**Use findings to:**
- Understand code quality baseline
- Identify refactoring priorities
- Plan technical debt paydown
- Estimate feature development risk

**Example output:**
```
Architecture: 7/10 — Good layering, minor dependency cycles in data layer
Testing: 6/10 — 72% coverage, gaps in integration tests
Security: 8/10 — Injection vulnerabilities in 2 API endpoints
Performance: 9/10 — No hot spots, good async handling
Observability: 5/10 — Minimal logging, no correlation IDs
```

### Bug Fix Workflow: 5-Step Diagnosis + TDD

**When to use:** Investigating any reported bug

**5-step process:**

1. **Triage**
   - Is this a real bug or expected behavior?
   - Reproducible? Always or intermittent?
   - Security-related?
   - Affects single user or multiple?

2. **Reproduce**
   - Create minimal test case
   - Confirm the bug with the test
   - Understand under what conditions it happens

3. **Root Cause**
   - Trace code paths
   - Identify the exact location of the bug
   - Explain why the current code is wrong

4. **Blast Radius**
   - What else could this bug affect?
   - Could this bug exist in similar code?
   - Are there related issues?

5. **Create Story**
   - Write a user story with the test case
   - Acceptance criteria: bug is fixed and test passes
   - Ready for `/shaktra:dev` to implement via TDD

**Remediation:** Dev Manager implements the fix via TDD, using the test case from diagnosis as the starting point.

---

## Configuration

### settings.yml Reference

All settings live in `.shaktra/settings.yml`. Nothing is hardcoded in the plugin.

#### TDD Thresholds

```yaml
tdd:
  coverage_threshold: 90          # Default coverage for normal stories
  hotfix_coverage_threshold: 70   # Coverage for hotfixes
  small_coverage_threshold: 80    # Coverage for S-tier stories
  large_coverage_threshold: 95    # Coverage for L-tier stories
```

**How it works:**
- Each story tier has its own threshold
- Quality gates enforce coverage during TDD
- Hotfixes use the lowest threshold (70%)
- Large stories require highest coverage (95%)

#### Quality Thresholds

```yaml
quality:
  p1_threshold: 2  # Max P1 findings before merge block
```

**Merge gate logic:**
- Any P0 finding → blocks merge
- P1 count > threshold → blocks merge
- P1 count ≤ threshold → allowed to merge
- P2/P3 → never blocks merge

#### Review Settings

```yaml
review:
  verification_test_persistence: ask   # auto | always | never | ask
  min_verification_tests: 5            # Minimum independent tests per review
```

**Verification tests:** Code Reviewer runs these to independently validate behavior beyond the story's own tests.

**Persistence options:**
- `ask` — Ask if you want to keep them after review
- `auto` — Keep them if coverage improves
- `always` — Always keep them
- `never` — Always discard them

#### Analysis Settings

```yaml
analysis:
  summary_token_budget: 600   # Max tokens per artifact summary
  incremental_refresh: true   # Use checksums for incremental refresh
```

#### Sprint Settings

```yaml
sprints:
  enabled: true
  velocity_tracking: true
  sprint_duration_weeks: 2
  default_velocity: 15  # Story points per sprint (used at init)
```

#### Product Management

```yaml
pm:
  default_framework: rice    # rice | weighted | moscow
  quick_win_effort_threshold: 3    # Max points for Quick Win
  big_bet_impact_threshold: 7      # Min impact score for Big Bet
```

### Hooks: Enforcement Rules

Four blocking hooks enforce constraints automatically. Hooks are all-or-nothing — they block or don't exist. No warn-only mode.

#### block-main-branch
**Triggers:** Bash (git operations)

**Blocks:** Any git operation that targets `main`, `master`, or `prod` branches

**Why:** Prevents accidental direct commits to protected branches. All changes must go through stories and reviews.

**Resolution:** Create a feature branch, commit there, then open a PR when ready.

#### validate-story-scope
**Triggers:** Write/Edit operations

**Blocks:** File changes outside the current story's scope

**How it works:**
1. During `/shaktra:dev`, the current story is tracked
2. Edits are validated against story's `files:` list
3. Out-of-scope changes are rejected

**Why:** Keeps stories focused. Prevents scope creep.

**Resolution:** If you need to edit a file outside scope, either:
- Create a separate story for that change
- Update the current story's scope and re-run validation

#### validate-schema
**Triggers:** Write/Edit operations (YAML files)

**Blocks:** YAML files that don't match Shaktra schemas

**What it checks:**
- `.shaktra/stories/*.md` — Story schema
- `.shaktra/settings.yml` — Config schema
- `.shaktra/sprints.yml` — Sprint schema
- All other `.shaktra/` YAML files

**Why:** Ensures consistent structure across state files.

**Resolution:** Check error message for missing/invalid fields. Fix the YAML and retry.

#### check-p0-findings
**Triggers:** Stop (when you finish)

**Blocks:** Completion if unresolved P0 findings exist

**How it works:**
- When you finish work, checks all story findings
- Any P0 findings → blocks stop
- You must fix or escalate P0s before continuing

**Why:** P0 findings are critical (security, data loss). They must be resolved before merging.

**Resolution:** Return to `/shaktra:dev` to fix the P0, or document why it cannot be fixed.

---

## Quality & Enforcement

### Quality Tiers

Shaktra operates at two quality levels:

#### SW Quality (Story-Level)
**When:** During `/shaktra:dev` at each state transition

**What it checks:** 36 checks across 8 dimensions
- Code correctness (logic, edge cases)
- Test quality (coverage, assertions)
- Error handling patterns
- Documentation completeness
- Security (input validation, secrets)
- Observability (logging, tracing)
- Performance (no obvious bottlenecks)
- Maintainability (naming, complexity)

**Blocks progress:** P0 findings block transition to next state

#### Code Review (App-Level)
**When:** After story completion via `/shaktra:review`

**What it checks:** 13 dimensions (see Commands Reference)
- Does it work in production context?
- Is it compatible with rest of system?
- Can it be safely deployed?
- Verified by independent tests

**Blocks merge:** P0 findings block merge; P1 count can block merge if exceeds threshold

### Severity Taxonomy (P0-P3)

Every finding is categorized by severity. This taxonomy is the single source of truth.

#### P0: Critical
**Definition:** Causes data loss, security breach, or unbounded resource consumption. Must be fixed before any merge.

**Examples:**
- SQL injection in query building
- File write without fsync (data loss on crash)
- Unbounded loop over external input
- Hardcoded credentials in code
- Missing authentication on protected endpoint
- Catch-all exception swallowing without re-raise

**Merge gate:** Blocks merge — always

#### P1: Major
**Definition:** Incorrect behavior, missing error handling, or inadequate test coverage. Allowed up to threshold.

**Examples:**
- Coverage below story tier threshold
- Missing error path for operation that can fail
- Off-by-one error in business logic
- Generic exception message that loses context
- Missing null guard on external data

**Merge gate:** Blocks merge if count > `settings.quality.p1_threshold`

#### P2: Moderate
**Definition:** Code quality, maintainability, or observability gaps. Does not affect correctness.

**Examples:**
- Missing docstring on public API
- Inconsistent error message formatting
- Code duplication that should be extracted
- Magic number without named constant

**Merge gate:** Does not block merge

#### P3: Minor
**Definition:** Style, naming, documentation. Cosmetic or subjective.

**Examples:**
- Variable naming style
- Import ordering
- Trailing whitespace
- Comment wording

**Merge gate:** Does not block merge

### Design Philosophy

These principles guide Shaktra's design:

**Prompt-driven, not script-driven**
- Agents and skills are markdown prompts, not Python scripts
- Leverages Claude's native tools (Glob, Read, Grep, Bash)
- More maintainable, more interpretable

**No file over 300 lines**
- Complexity stays manageable
- Every file has single clear purpose
- Easier to understand and modify

**Single source of truth**
- Severity taxonomy defined once: `shaktra-reference/severity-taxonomy.md`
- Quality dimensions defined once: `shaktra-reference/quality-dimensions.md`
- Other files reference, never duplicate

**Hooks block or don't exist**
- No warn-only hooks
- If a constraint matters, it's enforced
- Builds trust in the framework

**Ceremony scales with complexity**
- XS stories (hotfix): Minimal ceremony, 70% coverage
- S stories: Light ceremony, 80% coverage
- M stories: Standard ceremony, 90% coverage
- L stories: Full ceremony, 95% coverage + architecture review

**Read-only diagnostics**
- `/shaktra:doctor` reports problems but never fixes them
- You stay in control of your codebase
- Framework never auto-modifies code

---

## Troubleshooting

### Plugin not loading

**Symptoms:** `/shaktra:help` not found, no commands available

**Check:**
1. Plugin installed correctly: `/plugin list` should show shaktra
2. Claude Code recent version (February 2025+)
3. Try full reinstall: `/plugin uninstall shaktra` then `/plugin install https://github.com/im-shashanks/claude-plugins.git`

### Plugin not updating / stale version

**Symptoms:** You updated Shaktra but still see old behavior, missing commands, or `/shaktra:status-dash` shows an outdated version

**Cause:** Claude Code's plugin cache (`~/.claude/plugins/cache/`) does not always invalidate when a plugin is updated on the marketplace. This is a [known issue](https://github.com/anthropics/claude-code/issues/17361) — `/plugin update` and `autoUpdate` may report success without actually refreshing cached files.

**Fix:**
```bash
# Clear the stale cache
rm -rf ~/.claude/plugins/cache/

# Restart Claude Code, then reinstall
/plugin install shaktra@cc-plugins
```

This forces a fresh download from the marketplace.

### Hooks blocking unexpectedly

**Symptom:** "Hook validation failed" when trying to edit files

**Common issues:**

1. **block-main-branch** — Trying to commit to main/master/prod
   - Solution: Create a feature branch first
   - ```bash
     git checkout -b feature/your-feature
     # Make changes
     # Commit to feature branch (allowed)
     git commit -m "message"
     ```

2. **validate-story-scope** — Editing file not in current story
   - Solution: Add file to story scope or create separate story
   - Update `.shaktra/stories/ST-XXX.md` and add file to `files:` list

3. **validate-schema** — YAML validation failure
   - Solution: Check error message for invalid fields
   - Ensure all required fields present in `.shaktra/stories/*.md`

### Schema validation errors

**Symptom:** "File does not match schema" when editing YAML

**Common fixes:**

1. **Missing required fields**
   - Stories need: `id`, `title`, `description`, `acceptance_criteria`
   - Check `.shaktra/settings.yml` against template

2. **Invalid YAML syntax**
   - Check indentation (spaces, not tabs)
   - Check quote matching
   - Run `yaml lint .shaktra/settings.yml` (if tool available)

3. **Invalid enum values**
   - Story status must be: `backlog`, `planned`, `in-progress`, `complete`
   - Project type must be: `greenfield` or `brownfield`

### State file corruption

**Symptom:** `/shaktra:doctor` reports schema errors or missing files

**Recovery:**

1. **Check what's missing:**
   ```bash
   /shaktra:doctor
   ```

2. **Restore from backup** (if available):
   ```bash
   git checkout .shaktra/
   ```

3. **Reinitialize** (last resort, loses some state):
   ```bash
   rm -rf .shaktra/
   /shaktra:init
   ```

### Dev workflow stuck in a state

**Symptom:** `/shaktra:dev ST-001` keeps asking to retry the same state

**Causes:**
1. Quality gate failing repeatedly (P0/P1 findings)
2. Test coverage not meeting threshold
3. Schema validation errors in story file

**Resolution:**
1. Check error message carefully
2. Fix the underlying issue (tests, code, findings)
3. Continue dev workflow

### Coverage below threshold

**Symptom:** Green phase passes tests but coverage is 85% and threshold is 90%

**Resolution:**
1. Write additional tests for uncovered lines
2. Check if code has dead paths that should be removed
3. Run coverage report to see exactly what's uncovered
4. If legitimate lower coverage is needed, request story tier adjustment

### Using /shaktra:doctor

**When to use:**
- After `/shaktra:init` to validate setup
- Troubleshooting issues
- Before calling developer support
- As a pre-commit check

**What it checks:**
- ✅ Plugin installation (all files present)
- ✅ `.shaktra/` configuration (valid YAML, required keys)
- ✅ `settings.yml` compatibility (required fields, valid values)
- ✅ Hook scripts (executable, valid Python)
- ✅ Component counts (agents, skills match expected)
- ✅ Design constraints (no >300-line files, no dead code)
- ✅ P0 findings (all resolved before completion)

**Interpreting results:**
- 🟢 Green = all checks passed, framework healthy
- 🟡 Yellow = warnings (optional but recommended)
- 🔴 Red = errors (must fix before continuing)

**Output includes:**
- Which checks passed/failed
- Specific files/values causing failures
- Remediation steps for each failure

---

## Contributing to Shaktra

Shaktra is developed openly on GitHub. If you'd like to contribute bug fixes, features, or improvements:

1. **Switch to the `main` branch** of the repository
2. **Read the documentation** in the main branch for development guidelines, architecture, and phase plans
3. **All development happens from `main`** — create feature branches for your work

The development guide and contribution guidelines are in the main branch, not in this plugin directory. See the repository's README.md and CLAUDE.md files on the main branch for full details.

---

## License

MIT License. See LICENSE file in repository.

---

## Learn More

- **Getting help:** `/shaktra:help` for commands and examples
- **Contributing:** See the main branch for development guidelines and contribution process
- **Architecture:** Full architecture docs are on the main branch
