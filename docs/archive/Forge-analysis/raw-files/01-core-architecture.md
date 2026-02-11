# Forge Framework: Core Architecture Analysis

**Analysis Date:** 2026-02-05
**Framework Version:** 2.1.0 (per README)
**Repository:** `forge-claudify`

---

## 1. Bootstrap Flow

### How Claude Code Loads This Framework

Claude Code's loading order for project configuration is:

1. **`CLAUDE.md`** (project root) -- loaded first, always, unconditionally
2. **`.claude/settings.json`** -- loaded for hooks, permissions, and environment variables
3. **`.claude/settings.local.json`** -- merged on top of settings.json (local overrides)
4. **`.claude/rules/*.md`** -- auto-loaded rule files, filtered by glob patterns in frontmatter
5. **Skills** (`.claude/skills/*/SKILL.md`) -- loaded on demand when invoked
6. **Agents** (`.claude/agents/*.md`) -- loaded on demand when spawned via Task tool
7. **MCP servers** (`.claude/mcp.json`) -- loaded at session start (both are disabled)

### The Actual Initialization Chain

When a user opens Claude Code in this project, the effective bootstrap is:

```
Step 1: CLAUDE.md loads
  - Establishes project identity ("Forge Framework repository")
  - Points to /forge-workflow as the entry point
  - (In the template version: includes Skill Chaining Protocol, Evidence Rule,
    Subagent Delegation rules, and Brownfield Context Consumption rules)

Step 2: settings.json loads
  - Registers hooks (PreToolUse: validate-story-alignment.sh, block-main-branch.sh)
  - Sets permissions (deny .env/credentials/secrets, allow forge scripts + test runners)
  - Sets environment: FORGE_MODE=development, FORGE_MIN_COVERAGE=90, FORGE_ENFORCE_TDD=1

Step 3: settings.local.json merges
  - Adds: Skill(forge-workflow) permissions, python/grep/ls/tree bash permissions
  - Adds: WebFetch for www.aitmpl.com, WebSearch
  - Disables spinner tips

Step 4: Rules auto-load (5 files)
  - forge-auto-router.md -- always loaded (no glob filter)
  - forge-framework.md -- always loaded (no glob filter)
  - quality-standards.md -- loaded when files match forge/.tmp/**/quality_report.yml or handoff.yml
  - story-validation.md -- loaded when files match forge/stories/**/*.yml or .yaml
  - tdd-workflow.md -- loaded when files match forge/.tmp/**

Step 5: User types a message
  - forge-auto-router.md intercepts natural language and routes to /forge-workflow
  - /forge-workflow skill loads, classifies intent, spawns appropriate sub-agent
```

### Critical Observation: Two Different CLAUDE.md Files

There are two versions of CLAUDE.md:

1. **`/CLAUDE.md`** (root, 44 lines) -- The actual live file. Minimal. Points to `/forge-workflow`.
2. **`.claude/CLAUDE.template.md`** (161 lines) -- A much richer template with Skill Chaining Protocol, Evidence Rule, Subagent Delegation, and Brownfield Context Consumption rules.

**The template is 4x larger and contains critical operational rules that the live CLAUDE.md does not include.** This means that when the framework is used as-is in this repository, those rules (Skill Chaining, Evidence Rule, Subagent Delegation, Brownfield Context) are NOT active. They only become active if someone copies the template to their project root and fills it in.

This is a significant architectural gap -- the framework's own repository does not dogfood its own template.

---

## 2. CLAUDE.md Analysis

### Root CLAUDE.md (`/CLAUDE.md`, 44 lines)

**Structure:**
- Lines 1-6: Header with a template replacement comment
- Lines 7-9: Notes about `.venv` activation
- Lines 11-14: Project overview (self-referential: "This is the Forge Framework repository")
- Lines 16-19: Tech stack (Markdown, YAML, Python)
- Lines 22-26: Project-specific rules (2 items)
- Lines 28-33: Quick reference (skill/agent/rule locations)
- Lines 37-43: Forge Framework section pointing to `/forge-workflow`

**What it instructs Claude to do:**
- Activate `.venv` before running scripts
- Recognize this repo as the framework itself, not a consumer project
- Use `forge/` as the test workspace
- Use `/forge-workflow` or `forge-workflow help` for framework operations

**What it does NOT do:**
- Does not include the Skill Chaining Protocol from the template
- Does not include the Evidence Rule from the template
- Does not include Subagent Delegation rules from the template
- Does not include Brownfield Context Consumption rules from the template
- Does not define any behavioral constraints beyond "use /forge-workflow"

### Template CLAUDE.md (`.claude/CLAUDE.template.md`, 161 lines)

**Structure:**
- Lines 1-7: Setup instructions (copy to root)
- Lines 8-55: Standard project metadata sections (Overview, Tech Stack, Structure, Rules, Workflow, Patterns, Dependencies)
- Lines 57-69: Forge Framework section with natural language command examples
- Lines 71-78: Getting Started guide (greenfield vs brownfield)
- Lines 81-99: **Skill Chaining Protocol** -- a routing table for multi-skill tasks
- Lines 103-109: **Evidence Rule** -- "Where is the proof?" mandate
- Lines 120-137: **Subagent Delegation** -- coordinator-only pattern for main agent
- Lines 140-161: **Brownfield Context Consumption** -- rules for loading analysis artifacts

**What the template instructs Claude to do that the live file does not:**

1. **Skill Chaining Protocol** (lines 81-99): Defines a table mapping tasks to ordered skill chains. E.g., "Create PRD" must use `brainstorming -> forge-design`. This is a critical routing instruction.

2. **Evidence Rule** (lines 103-109): States `"Where is the proof?"` -- every claim about code behavior must be backed by evidence. Risky claims without evidence are P0/P1 findings.

3. **Subagent Delegation** (lines 120-137): Main agent must be a coordinator only. If a sub-agent exists for a task, delegate. Never implement directly.

4. **Brownfield Context Consumption** (lines 140-161): Before designing or developing, check for `.claude/.analysis/_manifest.yml`. Different roles load different artifacts.

**Assessment:** The template is the actual operational specification. The live CLAUDE.md is a stripped-down stub that would be insufficient for a consumer project. The framework relies on the template being manually copied and filled in, but provides no automation for this step (the `/forge-workflow init` command presumably handles this, but the template itself says "Copy this file to your project root").

---

## 3. Rules System

### Rule File Inventory

| File | Lines | Has Glob Filter | Always Loaded? |
|------|-------|-----------------|----------------|
| `forge-auto-router.md` | 85 | No | Yes |
| `forge-framework.md` | 88 | No | Yes |
| `quality-standards.md` | 122 | Yes (`forge/.tmp/**/quality_report.yml`, `forge/.tmp/**/handoff.yml`) | No |
| `story-validation.md` | 128 | Yes (`forge/stories/**/*.yml`, `forge/stories/**/*.yaml`) | No |
| `tdd-workflow.md` | 122 | Yes (`forge/.tmp/**`) | No |

### Individual Rule File Analysis

#### forge-auto-router.md (85 lines)

**Purpose:** Intercept natural language messages and route them to `/forge-workflow` without the user needing to type the skill prefix.

**Key mechanism:** A keyword lookup table with ~20 high-confidence triggers (`init`, `analyze`, `design`, `plan`, `develop`, `scaffold`, `quality`, `review`, `orchestrate`, `complete`, `hotfix`, `rollback`, `validate`, `check`, `enrich`, `quick`, `create story`, `create stories`, `create PRD`, `create architecture`, `forge status`, `forge help`).

**Also routes:** Story ID patterns (`ST-###`) embedded in any message.

**Does NOT route:** General questions, explanations, debugging, file exploration, greetings.

**Decision tree (line 56-68):**
```
1. ST-### pattern? -> Route
2. Starts with trigger keyword? -> Route
3. Contains "forge" + action? -> Route
4. Otherwise -> Normal response
```

**Concern:** This is essentially a prompt-based "middleware" that tries to intercept free-text input. There is no enforcement mechanism -- it relies entirely on Claude following the rule. The keyword list is broad enough that it could accidentally capture messages not intended for Forge (e.g., "review this PR" where the user means a general code review, not a Forge quality check). The "Do NOT Route" section attempts to mitigate this but relies on LLM judgment.

#### forge-framework.md (88 lines)

**Purpose:** Serves as the canonical reference for the Forge architecture, available to Claude at all times.

**Contents:**
- Entry point documentation (`/forge-workflow` with examples)
- Architecture overview (single entry point, orchestrator pattern, 5 sub-agents listed)
- Core rules (single-scope, TDD mandatory, 90% coverage, timeouts, honor decisions)
- Valid scopes list (10 scopes)
- Natural language intents table (12 intents)
- File locations table (8 path mappings)
- On-demand reference table (4 reference file pointers)
- Ground rules (no co-authored commits, read before modify, use existing patterns, run tests)

**Overlap with CLAUDE.md template:** Significant. The template's "Forge Framework" section (lines 57-78) repeats the same information. The intent table here duplicates the auto-router's trigger table. The file locations here duplicate what's in the README.

**Conflict:** Line 84 says `"DO NOT add co-authored in commits"`. This directly contradicts the standard Claude Code behavior of appending "Co-Authored-By: Claude" to commits. This is an intentional override specific to the Forge workflow.

#### quality-standards.md (122 lines, glob-filtered)

**Purpose:** Defines the 14-dimension quality review framework and P0-P3 severity taxonomy.

**Loaded when:** Claude is working with files matching `forge/.tmp/**/quality_report.yml` or `forge/.tmp/**/handoff.yml`.

**Contents:**
- 14 quality dimensions (A through N) with key questions per dimension
- P0 through P3 severity definitions with examples
- Merge gate logic (P0 blocks, P1 > 2 blocks, P1 > 0 warns, else pass)
- P0 triggers by dimension table
- Guard tokens: `P0_FINDING`, `P1_FINDING`, `PHASE_GATE_FAILED`

**Discrepancy:** The README says "13-dimension quality review" in multiple places (lines 457, 869). This rule file defines **14 dimensions** (A through N). Dimension N ("Plan Adherence") appears to have been added later. The README's architecture section also says "13-Dimension Code Review" at line 456. This inconsistency propagates through the framework -- the forge-framework.md rule also says "14-dimension quality review" on line 15, which contradicts the README's "13-dimension" claims.

#### story-validation.md (128 lines, glob-filtered)

**Purpose:** Schema validation rules for story YAML files.

**Loaded when:** Claude is working with files matching `forge/stories/**/*.yml` or `forge/stories/**/*.yaml`.

**Contents:**
- Single scope rule (exactly one scope per story)
- Tier detection logic (COMPLEX, SIMPLE, STANDARD)
- Required fields per tier: SIMPLE (8 fields), STANDARD (16 fields), COMPLEX (20+ fields)
- Enforced requirements (test fields, error cases in io_examples, valid metadata, feature flags)
- Guard tokens: `FIX_STORY_SCHEMA`, `REPLAN_SCOPE_FANOUT`, `MISSING_FEATURE_FLAGS`, `MISSING_ERROR_CASE_IN_IO_EXAMPLES`, `ORPHAN_INVARIANT_TEST_REFERENCE`, `ORPHAN_FAILURE_MODE_TEST_REFERENCE`, `ORPHAN_EDGE_CASE_TEST_REFERENCE`, `INVALID_SCAFFOLD_KIND`

**Overlap:** The valid scopes list (`skeleton | validation | diff | data | response | integration | observability | coverage | perf | security`) is repeated here, in forge-framework.md, and in the README. Three copies of the same data.

#### tdd-workflow.md (122 lines, glob-filtered)

**Purpose:** Defines the TDD phase sequence and handoff state management.

**Loaded when:** Claude is working with files matching `forge/.tmp/**`.

**Contents:**
- Phase sequence: `plan -> tests (RED) -> code (GREEN) -> quality`
- Phase 1 (Plan): Unified planning covering implementation + test planning
- Phase 2 (Tests): Write failing tests; one behavior per test; naming convention
- Phase 3 (Code): Implement to make tests pass; 90% coverage
- Handoff state schema (YAML format showing all fields)
- Guard tokens: `PHASE_GATE_FAILED`, `TESTS_NOT_RED`, `TESTS_NOT_GREEN`, `COVERAGE_GATE_FAILED`

**Overlap:** Phase sequence and guard tokens are repeated in the README (lines 356-414), in forge-framework.md (lines 32-37), and in the tdd-workflow rule itself. The handoff schema here is also described in the forge-tdd skill's `handoff-schema.md`.

### Rule Interaction Analysis

The rules form a layered system:

```
Always Active:
  forge-auto-router.md  -- "how to get to Forge"
  forge-framework.md    -- "what Forge is"

Contextually Active:
  story-validation.md   -- "how stories must be structured"
  tdd-workflow.md       -- "how development must proceed"
  quality-standards.md  -- "how quality is measured"
```

**Interaction pattern:** The auto-router triggers `/forge-workflow`, which spawns sub-agents. Those sub-agents create/modify files in `forge/.tmp/` and `forge/stories/`, which activates the contextual rules. The contextual rules then constrain Claude's behavior when working with those specific file types.

**Potential conflicts:**
1. The auto-router's broad keyword matching could conflict with the user's desire for a normal Claude response. For example, "plan my weekend" would trigger Forge routing because "plan" is a trigger keyword.
2. The quality-standards rule references 14 dimensions; the forge-framework rule references the same system. If they drift apart, Claude receives contradictory instructions.
3. The tdd-workflow rule's glob (`forge/.tmp/**`) is very broad and would activate whenever ANY file under `forge/.tmp/` is being worked with, including non-TDD temporary files.

---

## 4. Settings Architecture

### Three Settings Layers

#### Layer 1: `.claude/settings.json` (Project Settings, 47 lines)

**Purpose:** Defines project-level permissions, hooks, and environment variables. This is committed to version control and shared across all developers.

**Contents:**

**Permissions (deny):**
- `Read(.env*)` -- blocks reading environment files
- `Read(**/credentials*)` -- blocks reading credential files
- `Read(**/*secret*)` -- blocks reading secret files
- `Bash(rm -rf:*)` -- blocks destructive removal

**Permissions (allow):**
- `Bash(python .claude/skills/forge-check/scripts/*.py:*)` -- validation scripts
- `Bash(python .claude/forge/scripts/*.py:*)` -- forge scripts
- `Bash(python .claude/hooks/*.py:*)` -- hook scripts
- `Bash(pytest:*)` -- test runner
- `Bash(git:*)` -- git operations
- `Bash(npm test:*)` -- npm test
- `Bash(npm run:*)` -- npm run scripts

**Hooks:**
- **PreToolUse (Write|Edit):** Runs `validate-story-alignment.sh` with `$TOOL_INPUT` -- checks that file modifications align with the active story
- **PreToolUse (Bash):** Runs `block-main-branch.sh` -- prevents direct commits to main/master
- **Stop:** Empty array (placeholder)

**Environment Variables:**
- `FORGE_MODE=development`
- `FORGE_MIN_COVERAGE=90`
- `FORGE_ENFORCE_TDD=1`

**Concern:** The allow path `Bash(python .claude/forge/scripts/*.py:*)` references `.claude/forge/scripts/` but the actual scripts directory is `.claude/scripts/` (containing learning-related Python scripts). This is either a stale reference from v1.x or a path mismatch.

#### Layer 2: `.claude/settings.local.json` (Local Settings, 16 lines)

**Purpose:** Local developer overrides, not committed to version control.

**Contents:**

**Permissions (allow):**
- `Skill(forge-workflow)` and `Skill(forge-workflow:*)` -- allows the forge-workflow skill
- `Bash(xargs:*)`, `Bash(python:*)`, `Bash(grep:*)` -- general-purpose bash commands
- `WebFetch(domain:www.aitmpl.com)` -- allows fetching from aitmpl.com (likely an AI template site)
- `WebSearch` -- allows web searching
- `Bash(ls:*)`, `Bash(tree:*)` -- directory listing

**Other:** `spinnerTipsEnabled: false`

**Concern:** The `Bash(python:*)` permission here is extremely broad -- it allows running ANY Python command. This effectively bypasses the more restrictive `python .claude/skills/forge-check/scripts/*.py` pattern in settings.json. The local settings override undermines the security posture of the project settings.

#### Layer 3: `forge/settings.yml` (Runtime Settings, 30 lines)

**Purpose:** Project-specific configuration read by sub-agents at runtime. This is NOT a Claude Code configuration file -- it is a YAML file that agents are instructed to read before applying thresholds.

**Contents:**
```yaml
project:
  name: "Forge Framework"
  architecture: "auto"

tdd:
  coverage_threshold: 90
  hotfix_coverage_threshold: 70

quality:
  p0_blocking: true
  p1_threshold: 2
  persist_verification_tests: auto

learning:
  enabled: true
  auto_trigger:
    enabled: true
    event_threshold: 20
    time_threshold_hours: 24
  confidence_levels:
    high: 0.80
    medium: 0.60
    low: 0.40
```

**How it relates to the other settings:**
- `settings.json` is Claude Code infrastructure (hooks, permissions, env vars)
- `settings.local.json` is local Claude Code infrastructure overrides
- `forge/settings.yml` is application-level configuration that the Forge sub-agents read

The environment variable `FORGE_MIN_COVERAGE=90` in settings.json duplicates the `tdd.coverage_threshold: 90` in forge/settings.yml. If they drift apart, agents could get conflicting thresholds depending on which source they consult.

### The Settings Template

The template at `.claude/templates/forge/settings.yml.template` is identical to the runtime `forge/settings.yml` except the template has empty `project.name` and `project.architecture` fields. This template is used during `/forge-workflow init` to generate the runtime settings file.

---

## 5. Configuration Layering

### The Full Configuration Stack

```
Layer 0 (Always):   CLAUDE.md                    -- Project identity, minimal rules
Layer 1 (Always):   .claude/settings.json         -- Permissions, hooks, env vars
Layer 2 (Local):    .claude/settings.local.json   -- Local permission overrides
Layer 3 (Always):   .claude/rules/forge-auto-router.md    -- Intent routing
Layer 4 (Always):   .claude/rules/forge-framework.md      -- Framework reference
Layer 5 (Context):  .claude/rules/quality-standards.md    -- Quality review rules
Layer 6 (Context):  .claude/rules/story-validation.md     -- Story schema rules
Layer 7 (Context):  .claude/rules/tdd-workflow.md         -- TDD phase rules
Layer 8 (Demand):   .claude/skills/forge-workflow/SKILL.md -- Orchestrator logic
Layer 9 (Demand):   .claude/agents/forge-*.md              -- Sub-agent configs
Layer 10 (Runtime): forge/settings.yml                     -- Project thresholds
```

### Is the Layering Clean?

**No. There are several problems:**

#### Problem 1: Redundant Information Across Layers

The same information is repeated in multiple places:

| Information | Locations |
|-------------|-----------|
| Valid scopes (10) | forge-framework.md, story-validation.md, README, forge-reference skill |
| TDD phase sequence | tdd-workflow.md rule, forge-framework.md rule, README, forge-tdd skill |
| Coverage thresholds | settings.json env var, forge/settings.yml, README, tdd-workflow.md |
| P0-P3 severity | quality-standards.md rule, README, forge-quality skill |
| Quality dimensions | quality-standards.md (14 dims), README (says "13"), forge-framework.md |
| File locations | forge-framework.md, README, CLAUDE.md template |
| Sub-agent list | forge-framework.md, README, CLAUDE.md template |

This creates a maintenance burden where any change must be propagated to 3-5 locations.

#### Problem 2: Inconsistent Authority

There is no clear "single source of truth" for most configuration:

- **Coverage threshold:** Is it `FORGE_MIN_COVERAGE` env var (settings.json), or `tdd.coverage_threshold` (forge/settings.yml), or the value hardcoded in rules? The comment in forge/settings.yml says `"Agents MUST read this file before applying thresholds"`, suggesting it should be authoritative, but the env var exists independently.

- **Quality dimensions:** The rule file says 14. The README says 13. Which is canonical?

- **Entry point:** The root CLAUDE.md says to use `/forge-workflow`. The auto-router says you can just type naturally. The forge-framework rule lists `/forge-workflow` as the entry point. Three layers saying slightly different things about how to invoke the framework.

#### Problem 3: Template vs Live CLAUDE.md Gap

The template (`.claude/CLAUDE.template.md`) contains four critical behavioral sections:
1. Skill Chaining Protocol
2. Evidence Rule
3. Subagent Delegation
4. Brownfield Context Consumption

None of these exist in the live `CLAUDE.md`. This means:
- In the framework's own repository, these rules are NOT enforced
- Users who don't copy the template to their project root will miss these rules
- The framework cannot be validated against its own rules because it doesn't apply them to itself

#### Problem 4: Local Settings Undermine Security

`settings.local.json` grants `Bash(python:*)` which allows arbitrary Python execution, bypassing the narrow script-specific permissions in `settings.json`. While local settings are intended for developer convenience, including such a broad permission in a template file that could be copied by users is a security concern.

---

## 6. Template System

### What CLAUDE.template.md Enables

The template serves as a **project onboarding document** for teams adopting Forge. It provides:

1. **Structured project metadata** -- Sections for project description, tech stack, project structure, conventions, workflow, patterns, and external dependencies. These are all fill-in-the-blank sections that help Claude understand the project context.

2. **Forge integration** -- The bottom half of the template contains the Forge-specific rules that make the framework operational:
   - Natural language command examples (line 62-67)
   - Getting started guide (lines 71-78)
   - Skill chaining protocol (lines 81-99)
   - Evidence rule (lines 103-109)
   - Subagent delegation (lines 120-137)
   - Brownfield context consumption (lines 140-161)

### How It Is Meant to Be Used

Per the comment at line 4: `"SETUP: Copy this file to your project root as CLAUDE.md and fill in the sections below."`

The intended flow is:
1. User runs `/forge-workflow init` (or manually copies)
2. Template is copied to project root as `CLAUDE.md`
3. User fills in project-specific sections
4. The Forge rules at the bottom are automatically included

### What Other Templates Exist

The `.claude/templates/forge/` directory contains:
- `settings.yml.template` -- generates `forge/settings.yml`
- `memory/important_decisions.yml.template` -- generates `forge/memory/important_decisions.yml`
- `memory/project.yml.template` -- generates `forge/memory/project.yml`
- `memory/learning/patterns.yml.template` -- learning pattern tracking
- `memory/learning/pattern_performance.yml.template` -- pattern performance tracking
- `memory/learning/README.md` -- learning system documentation
- `docs/Architecture.md.template` -- architecture document template
- `docs/PRD.md.template` -- product requirements document template

These templates form the scaffold for the `forge/` workspace directory, generated during init.

### Template System Assessment

The template system is straightforward but has a gap: there is no automated mechanism to ensure the template stays in sync with the rules and skills. If someone adds a new rule to a skill but forgets to update the template's Skill Chaining Protocol table, users who copy the template will get stale routing instructions.

---

## 7. README vs Reality

### README Claims vs Actual Implementation

The README is comprehensive at 1139 lines. Let me verify its key claims against the actual file system.

#### Claim: "8 skills with supporting files" (line 1123)

**Reality:** The `.claude/skills/` directory contains **12 directories**, not 8:
1. `brainstorming`
2. `error-resolver`
3. `forge-analyze`
4. `forge-check`
5. `forge-design`
6. `forge-plan`
7. `forge-quality`
8. `forge-reference`
9. `forge-tdd`
10. `forge-workflow`
11. `product-manager-toolkit`
12. `subagent-driven-development`

The README documents 9 skills (forge-workflow, forge-analyze, forge-design, forge-plan, forge-check, forge-tdd, forge-quality, forge-reference, product-manager-toolkit). It does not mention `brainstorming`, `error-resolver`, or `subagent-driven-development`. **The README undercounts skills by 3.**

#### Claim: "7 specialized sub-agents" (line 1124)

**Reality:** The `.claude/agents/` directory contains **12 agent files**:
1. `forge-analyzer.md`
2. `forge-checker.md`
3. `forge-designer.md`
4. `forge-developer.md`
5. `forge-docs-updater.md`
6. `forge-learning-analyzer.md`
7. `forge-planner.md`
8. `forge-product-manager.md`
9. `forge-quality.md`
10. `forge-test-engineer.md`
11. `python-pro.md`
12. `typescript-pro.md`

The README documents 7 agents (forge-analyzer, forge-designer, forge-planner, forge-developer, forge-quality, forge-docs-updater, forge-product-manager). It does not mention `forge-checker`, `forge-learning-analyzer`, `forge-test-engineer`, `python-pro`, or `typescript-pro`. **The README undercounts agents by 5.**

#### Claim: "13-dimension quality review" (multiple locations)

**Reality:** The `quality-standards.md` rule file defines **14 dimensions** (A through N). Dimension N is "Plan Adherence." The README itself contradicts itself -- at line 456 it says "13-Dimension Code Review" but then lists dimensions A through M (which is 13). However the rule file adds N. **The README is behind the rule file by one dimension.**

#### Claim: "13-phase brownfield analysis" (line 222)

**Reality:** The README lists phases 0-12, which is indeed 13 phases. The output files listed (13 files including `_manifest.yml`) also confirms this. **This claim is accurate.**

#### Claim: Package.json describes "SimpleTask - Minimalist task tracker"

**Reality:** The `package.json` has `"name": "simpletask"` and `"description": "SimpleTask - Minimalist task tracker"`. This is clearly a test/demo project, NOT the framework itself. The package.json sets up Jest with jsdom for testing an `index.html` file. **The package.json does not represent the Forge framework -- it represents a demo project that Forge was used on.** This is confusing for anyone examining the repository.

#### Claim: File structure shows `.claude/rules/` with 4 files (line 982-986)

**Reality:** There are **5** rule files:
1. `forge-auto-router.md`
2. `forge-framework.md`
3. `quality-standards.md`
4. `story-validation.md`
5. `tdd-workflow.md`

The README's file tree (line 982-986) lists only 4, omitting `forge-auto-router.md`. **The README's file tree is out of date.**

#### Claim: Hooks directory has 3 files (line 977-979)

**Reality:** The hooks directory has **6 entries**: `block-main-branch.sh`, `check-p0-findings.py`, `ci/` (directory), `forge-statusline.sh`, `validate-story-alignment.sh`, and `validate-story.py`. The README lists only 3 hooks. **The README omits 3 hook files/directories.**

#### Claim: Scripts are inside skills (v2.0 migration)

**Reality:** There is a separate `.claude/scripts/` directory with 6 Python files related to a "learning" system (`apply_pattern.py`, `learning_state.py`, `log_event.py`, `pattern_analysis.py`, `pattern_matcher.py`, `sanitize.py`). These are NOT mentioned anywhere in the README. **An entire subsystem (learning/pattern analysis) exists undocumented.**

### README Accuracy Verdict

The README is **substantially accurate** for the core workflow (init -> analyze -> design -> plan -> develop -> review) but is **out of date** regarding:
- Actual skill count (12 vs documented 9)
- Actual agent count (12 vs documented 7)
- Quality dimension count (14 vs documented 13)
- File tree (missing forge-auto-router.md rule, extra hooks, undocumented scripts)
- Learning subsystem (entirely undocumented)
- Package.json identity (says "simpletask", not "forge")

---

## 8. Architectural Concerns

### Concern 1: Massive Duplication of Rules

The same rules and reference data are repeated across multiple files. For example, the valid scopes list appears in at least 4 locations. The TDD phase sequence appears in at least 4 locations. The quality dimensions appear in at least 3 locations (with an inconsistency between them). Coverage thresholds appear in at least 3 locations.

**Impact:** High maintenance burden. When a rule changes, it must be updated in multiple files. The existing 13-vs-14 dimension inconsistency demonstrates that this duplication has already caused drift.

**Root cause:** The framework tries to make every layer self-contained. The auto-router duplicates intents from the framework rule. The framework rule duplicates information from the skills. The README duplicates everything.

### Concern 2: Over-Reliance on LLM Compliance

The entire auto-routing system, the skill chaining protocol, the evidence rule, and the subagent delegation rules are all enforced purely through prompt instructions. There are no programmatic checks that Claude actually followed these rules (except for the two hooks: story alignment and main branch protection).

**Impact:** If Claude ignores or misinterprets a rule (which happens with prompt-based enforcement), there is no fallback. The hooks provide some enforcement, but they only cover two specific scenarios.

### Concern 3: Unclear Boundary Between "Framework" and "Demo Project"

The repository contains:
- `package.json` for "simpletask" (a demo/test project)
- `forge/settings.yml` with `project.name: "Forge Framework"` (the framework itself)
- `CLAUDE.md` saying "This is the Forge Framework repository"
- A `coverage/` directory (likely from running Jest on the demo project)
- `node_modules/` (260 entries, for Jest)

This creates confusion about what this repository IS. Is it the framework? The framework plus a demo? A demo project that happens to contain the framework? The `package.json` name mismatch ("simpletask" vs "Forge Framework") is particularly jarring.

### Concern 4: Undocumented Learning Subsystem

The `.claude/scripts/` directory contains a substantial learning/pattern analysis system (6 Python files, ~75KB total). The `forge/settings.yml` references this system with a `learning:` configuration section. There is a `forge-learning-analyzer.md` agent. The templates include learning pattern files.

Yet the README does not mention this subsystem AT ALL. The CLAUDE.md does not reference it. No rule file governs it. This is a significant undocumented feature.

### Concern 5: MCP Servers Are Placeholder

The `mcp.json` defines two MCP servers (`forge-github` and `forge-ci`), both marked `disabled: true` with comments saying "Enable when implemented." These are aspirational, not functional. Yet having them in the configuration suggests to users that GitHub and CI integration exist.

### Concern 6: The Framework Does Not Dogfood Itself

As noted in Section 2, the live `CLAUDE.md` does not include the Skill Chaining Protocol, Evidence Rule, Subagent Delegation, or Brownfield Context Consumption rules from the template. This means:
- Development on the framework itself does not follow the rules the framework prescribes
- Testing the framework cannot validate that these rules work in practice
- There is no way to know if these rules cause conflicts when combined with the rules and skills

### Concern 7: Hook Scripts Reference Patterns That May Not Exist

`settings.json` registers `validate-story-alignment.sh` as a PreToolUse hook on Write/Edit operations. This hook receives `$TOOL_INPUT` and presumably checks that the file being modified is related to the active story. However, if there is no active story (the user is just editing a file outside of Forge workflow), this hook would either fail silently or raise a false alarm. The behavior in the non-Forge case is unclear.

Similarly, `block-main-branch.sh` runs on every Bash command. If the user is not on a git branch (e.g., a fresh repo or detached HEAD), the behavior is unclear.

### Concern 8: Settings Priority Ambiguity

When `FORGE_MIN_COVERAGE=90` (env var) conflicts with `forge/settings.yml` `tdd.coverage_threshold`, which wins? The env var is injected by Claude Code infrastructure. The YAML file is read by sub-agents who are instructed to read it. If a sub-agent reads `forge/settings.yml` and sees 85%, but the env var says 90%, the behavior depends on which the sub-agent's code checks first.

The comment in `forge/settings.yml` says `"Agents MUST read this file before applying thresholds"` but does not say it is authoritative over the env var.

### Concern 9: Template vs Live Configuration Drift

The `forge/settings.yml` (runtime) has `project.name: "Forge Framework"` while the template has `project.name: ""`. This shows the init process works. However, there is no mechanism to detect when the template evolves (e.g., a new setting is added) and the runtime settings need to be regenerated. Once initialized, the settings file is never updated from the template again.

### Concern 10: Bloat in Rule Context

When all always-loaded rules are combined, Claude receives forge-auto-router.md (85 lines) + forge-framework.md (88 lines) = 173 lines of framework instructions on EVERY conversation turn, even when the user is doing something completely unrelated to Forge (like asking "what does this function do?"). The auto-router explicitly says to NOT route such questions, but the rules still consume context window space.

Additionally, when working with files in `forge/.tmp/`, both `tdd-workflow.md` (122 lines) and `quality-standards.md` (122 lines) may load simultaneously (since both have globs matching `forge/.tmp/**` patterns), adding another 244 lines. Combined with the always-on rules, this is ~417 lines of rules before any skill or agent instructions load.

---

## Summary

The Forge framework's core architecture is an ambitious attempt to impose a structured, spec-driven development workflow on Claude Code through a layered configuration system. The architecture has clear strengths:

1. **Well-defined workflow** -- The progression from analyze -> design -> plan -> develop -> review is logically sound and well-documented.
2. **Separation of concerns via sub-agents** -- Each phase has a dedicated agent with specific tools and skills.
3. **Quality gates** -- Guard tokens, severity taxonomy, and coverage thresholds provide measurable standards.
4. **Template system** -- The init process scaffolds a consistent workspace.

However, the architecture suffers from:

1. **Significant duplication** -- Rules, scopes, thresholds, and phase sequences are repeated across 3-5 locations, leading to drift (13 vs 14 dimensions).
2. **Documentation lag** -- The README undercounts skills by 3, agents by 5, and misses an entire subsystem (learning).
3. **Template/live gap** -- The live CLAUDE.md omits critical rules present in the template, meaning the framework does not dogfood itself.
4. **Ambiguous authority** -- Multiple sources define the same thresholds (env vars, YAML settings, hardcoded in rules) with no clear precedence.
5. **Prompt-only enforcement** -- Most rules rely on Claude following instructions rather than programmatic enforcement.
6. **Context window bloat** -- Always-on rules consume ~173+ lines on every turn, even for non-Forge interactions.

For a rebuild, the key lesson is: **define each piece of configuration exactly once, reference it from everywhere else, and ensure programmatic enforcement where possible.**
