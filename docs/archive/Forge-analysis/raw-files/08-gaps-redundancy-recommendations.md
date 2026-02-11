# Forge Framework: Cross-Cutting Analysis -- Gaps, Redundancy, Bloat, Pain Points & Recommendations

**Date:** 2026-02-05
**Scope:** Complete framework analysis of `/Users/shashank/workspace/applications/forge-claudify`
**Files Analyzed:** 271 files, ~91,546 total lines

---

## Table of Contents

1. [Redundancy Map](#1-redundancy-map)
2. [Bloat Assessment](#2-bloat-assessment)
3. [Dead Code & Abandoned Features](#3-dead-code--abandoned-features)
4. [Naming & Organization Issues](#4-naming--organization-issues)
5. [Architecture Anti-Patterns](#5-architecture-anti-patterns)
6. [Missing Capabilities (Gaps)](#6-missing-capabilities-gaps)
7. [Prompt Engineering Issues](#7-prompt-engineering-issues)
8. [Configuration Mess](#8-configuration-mess)
9. [Maintainability Score](#9-maintainability-score)
10. [Top 15 Recommendations](#10-top-15-recommendations)

---

## 1. Redundancy Map

### 1.1 The Quality Review Quadruple: forge-checker vs forge-quality vs forge-check vs forge-quality (skill)

This is the single worst redundancy in the framework. Four separate components all deal with "quality" and their boundaries are maddeningly unclear:

| Component | Type | Location | Lines | Purpose |
|-----------|------|----------|-------|---------|
| `forge-checker` | Agent | `.claude/agents/forge-checker.md` | 329 | "Quality reviewer agent" -- plan quality, test quality, tech debt, AI slop |
| `forge-quality` | Agent | `.claude/agents/forge-quality.md` | 163 | "Quality review expert" -- 14-dimension code review, verification testing |
| `forge-check` | Skill | `.claude/skills/forge-check/SKILL.md` | 417 | "Quality review skill" -- test quality, tech debt, AI slop, artifacts |
| `forge-quality` | Skill | `.claude/skills/forge-quality/SKILL.md` | 88 | "Quality review skill" -- 14-dimension review, severity taxonomy |

**The overlap is severe:**

- **Severity taxonomy (P0-P3)**: Defined in `quality-standards.md` (rule), `forge-quality/SKILL.md` (skill), `forge-check/SKILL.md` (skill), `forge-quality` (agent), `forge-checker` (agent), and `forge-reference/world-class-standard.md`. That is **six separate locations** repeating the same `P0 > 0 = BLOCKED, P1 > 2 = BLOCKED` logic.

- **14-dimension review (A-M)**: Defined in `quality-standards.md` (rule), `forge-quality` agent, `forge-quality/SKILL.md`, and `forge-reference/world-class-standard.md`. The rule file says "14 Quality Dimensions" but the agent says "13-Dimension Code Review" (the agent's own table only lists A through M, which is 13, not 14). The skill says "14 Quality Dimensions" but the quality-review.md inside it contains yet another version. Dimension N ("Plan Adherence") appears in the rule but not consistently elsewhere.

- **Merge gate logic**: The exact same pseudocode block (`if P0 > 0: BLOCKED`) appears verbatim in at least four files.

**Who does what?** The intended split appears to be:
- `forge-checker` agent: Pre-TDD and during-TDD quality gates (schema validation, plan quality, test quality, tech debt, AI slop)
- `forge-quality` agent: Post-TDD full code review (14-dimension review, verification testing)

But this distinction is never clearly stated. The orchestrator SKILL.md blurs these boundaries by describing check flows that sometimes use `forge-checker` and sometimes `forge-quality`.

### 1.2 Rules That Repeat Skills

Every rule file is a condensed version of content already present in skills and agents:

| Rule | Duplicates |
|------|-----------|
| `forge-framework.md` (88 lines) | Condenses `forge-workflow/SKILL.md` (1481 lines). Lists the same intents, same scopes, same file locations. |
| `quality-standards.md` (122 lines) | Duplicates content in `forge-quality/SKILL.md`, `forge-check/SKILL.md`, `forge-reference/world-class-standard.md` |
| `story-validation.md` (128 lines) | Duplicates `forge-plan/story-schema.md` and `forge-check/scripts/validate_stories.py` |
| `tdd-workflow.md` (122 lines) | Duplicates `forge-tdd/SKILL.md` and `forge-tdd/tdd-workflow.md` |
| `forge-auto-router.md` (85 lines) | Duplicates intent tables from `forge-workflow/SKILL.md` and `forge-workflow/intent-patterns.md` |

The rules serve as "always-loaded context" but they create a maintenance problem: change the quality gate logic in the skill and forget to update the rule, and you have contradictory instructions.

### 1.3 Agent-Skill Duplication

Every agent file repeats content from its associated skill:

- `forge-developer.md` (205 lines) restates the entire TDD workflow that `forge-tdd/SKILL.md` (139 lines) already describes. The agent includes its own version of test execution commands, phase detection logic, and coverage thresholds.
- `forge-checker.md` (329 lines) restates all 5 check modes, gate logic, and checklist references from `forge-check/SKILL.md` (417 lines). The agent is basically a verbose copy of the skill with a persona prefix.
- `forge-planner.md` (235 lines) restates story creation rules, tier detection, and validation logic from `forge-plan/SKILL.md` (67 lines) and its sub-files.

**The pattern:** Agent files load skills via the `skills:` frontmatter field, meaning the skill content is ALREADY available. Yet the agent body re-explains the same content, often inconsistently. The agents should be thin wrappers -- persona + delegation instructions -- not full duplicates.

### 1.4 Duplicate Practice Files

The practices (coding.md, testing.md, contracts.md, security.md, etc.) exist in THREE locations:

1. **Active:** `/Users/shashank/workspace/applications/forge-claudify/.claude/skills/forge-tdd/practices/` (18 files)
2. **Deleted copy:** `/Users/shashank/workspace/applications/forge-claudify/.claude/_to_be_deleted/forge/practices/` (21 files)
3. **Referenced from:** `forge-reference/world-class-standard.md` (lists all of them as "Related Practice Files")

The active and deleted versions appear to be identical or near-identical copies.

### 1.5 Duplicate Analysis Phase Templates

Analysis phase templates exist in TWO locations:

1. **Active:** `.claude/skills/forge-analyze/phases/` (14 files)
2. **Deleted copy:** `.claude/_to_be_deleted/forge/templates/analyze/` (14 files)

Both sets contain the same phase definitions (00-static through 12-examples plus _orchestrator and _finalize).

### 1.6 Duplicate Scripts

- `static_analysis.py` exists in both `.claude/skills/forge-analyze/scripts/` and `.claude/_to_be_deleted/forge/scripts/`
- `validate_stories.py` exists in both `.claude/skills/forge-check/scripts/` and `.claude/_to_be_deleted/forge/scripts/`
- `check_tools.py` / `doctor.py` exist in both `.claude/skills/forge-workflow/scripts/` and `.claude/_to_be_deleted/forge/scripts/`

### 1.7 Profile Configuration Duplication

Profile files exist in TWO active locations:

1. `.claude/skills/forge-reference/profiles/` (active.yml, universal.yml)
2. `.claude/_to_be_deleted/forge/profiles/` (active.yml, universal.yml)

And a template exists at `.claude/templates/forge/settings.yml.template`.

### 1.8 Redundant Quality Mechanisms: forge-test-engineer vs forge-developer vs forge-checker

Three agents all perform overlapping testing responsibilities:

| Agent | Testing Role |
|-------|-------------|
| `forge-developer` | Writes tests (RED phase), runs tests with coverage (GREEN phase) |
| `forge-test-engineer` | "Test automation and quality assurance specialist" -- enforces test pyramid, checks coverage, verifies TDD compliance |
| `forge-checker` | Validates test quality (TEST_QUALITY mode), checks behavioral assertions, coverage |

The `forge-test-engineer` (402 lines) is the most confusing. It duplicates content from both `forge-developer` (test execution, coverage thresholds) and `forge-checker` (test quality principles, guard tokens). Yet it is never referenced in the orchestration workflow. There is no intent that routes to `forge-test-engineer`. It appears to be an abandoned experiment that was never connected.

### 1.9 Overlapping "World-Class Standard" and "Quality Review"

The world-class standard is documented in:
- `forge-reference/world-class-standard.md` (223 lines) -- P1-P31 principles, severity taxonomy, CCR dimensions, edge-case matrix, developer checklist, testing principles
- `forge-quality/quality-review.md` -- the 14-dimension review
- `quality-standards.md` (rule) -- the severity taxonomy and dimensions

There is enormous content overlap between the world-class standard reference doc and the quality review skill. The world-class standard includes the CCR review dimensions (A-M), which are the SAME as the "14 Quality Dimensions" in the quality skill. Having the same information in a "reference" skill and a "quality" skill creates confusion about which is authoritative.

---

## 2. Bloat Assessment

### 2.1 Framework Size

| Category | Files | Lines | % of Total |
|----------|-------|-------|------------|
| Active framework (`.claude/`) | 174 | 52,655 | 57.5% |
| Dead code (`_to_be_deleted/`) | 97 | 37,057 | 40.5% |
| Config/docs at root | ~10 | ~1,834 | 2% |
| **Total** | **271** | **91,546** | **100%** |

**40% of the framework is explicitly dead code that has never been cleaned up.** This alone is damning.

### 2.2 Token Budget Abuse

Claude Code loads rule files and skill content into the model's context window. The active framework consumes roughly:

| Component | Files Loaded | Estimated Tokens |
|-----------|-------------|-----------------|
| Rules (always loaded) | 5 files, 545 lines | ~4,000 tokens |
| forge-workflow SKILL.md (on invoke) | 1 file, 1481 lines | ~11,000 tokens |
| orchestrate.md (on invoke) | 1 file, 962 lines | ~7,000 tokens |
| intent-handlers.md (referenced) | 1 file, 462 lines | ~3,500 tokens |
| forge-tdd practices (all 18 files) | 18 files | ~15,000 tokens |
| Agent files | ~200-500 lines each | ~2,000-4,000 tokens per agent |

The forge-workflow SKILL.md alone is 1,481 lines. This is loaded every time `/forge-workflow` is invoked. It contains:
- Intent classification tables (duplicated from the rule file)
- Orchestrator boundaries (repeated three separate times within the file)
- Create-Check-Fix Loop (described with pseudo-code AND ASCII diagrams)
- PM integration points (described twice: once in delegation section, once in PM section)
- Self-learning system integration (described at length)
- The "MANDATORY POST-COMPLETION GATES" table is stated FOUR times: once at the top, once mid-file, once in a checkpoint, and once in the verification section.

**The orchestrator SKILL.md says "Keep orchestrator light" and then consumes ~11,000 tokens.** This is deeply ironic.

### 2.3 Over-Engineered Components

**The Self-Learning System (forge-learning-analyzer, learning_state.py, pattern_analysis.py, pattern_matcher.py, apply_pattern.py, log_event.py):**

This is the most over-engineered component. It includes:
- 5 Python scripts (`.claude/scripts/`)
- 1 dedicated agent (`forge-learning-analyzer.md`, 287 lines)
- ~200 lines of learning integration in the orchestrator SKILL.md
- Settings in `forge/settings.yml` with confidence thresholds
- Template files for learning patterns and performance
- An auto-trigger system with event counting and time thresholds

For a framework that generates coding workflows, this machine-learning-style pattern discovery system is absurdly complex. The `events.jsonl` file it depends on is never populated by any hook or automated process visible in the codebase. The pattern_matcher.py and pattern_analysis.py scripts exist but there is no evidence they have ever been meaningfully used. The entire subsystem solves a problem that does not exist at the scale this framework operates at.

**Estimated value relative to complexity: ~5%**. A simple "lessons learned" YAML file that agents append to would provide 80% of the value at 5% of the complexity.

**The Product Manager Agent (forge-product-manager.md, 502 lines):**

This is the largest agent file. It defines 5 workflows:
1. Create PRD (interactive and from-document modes)
2. Create Architecture
3. Story Review (post-plan)
4. Answer Clarifications
5. UAT Checklist (post-quality)

The PM agent relies on `product-manager-toolkit` skill (352 lines) which includes RICE prioritization scripts and customer interview analyzers. This is product management tooling embedded inside a code development framework. The `customer_interview_analyzer.py` script is particularly out of place -- it performs NLP sentiment analysis on interview transcripts. This has nothing to do with the core loop of "write spec, write tests, write code."

**The Architecture Pattern Library (18 practice files + 6 architecture files):**

The `forge-tdd/practices/` directory contains 18 markdown files covering coding practices, plus 6 architecture pattern files (hexagonal, layered, feature-based, MVC, clean, event-driven). These are all loaded as context for the `forge-developer` agent.

Each practice file is a comprehensive reference guide (e.g., `concurrency.md` covers idempotency patterns, lock strategies, async patterns). These are essentially textbook chapters on software engineering loaded into the context window. While valuable as reference, loading all 18 files for every development task is wasteful. Most stories will only need 2-3 of these.

### 2.4 Ceremony vs Value Ratio

| Ceremony | Value | Ratio |
|----------|-------|-------|
| Story YAML schema (20+ required fields for COMPLEX tier) | Provides spec for agents | High ceremony. A COMPLEX story requires `id`, `title`, `description`, `scope`, `files`, `acceptance_criteria`, `tests`, `risk_assessment`, `interfaces`, `io_examples`, `error_handling`, `logging_rules`, `observability_rules`, `concurrency`, `invariants`, `metadata`, `failure_modes`, `determinism`, `resource_safety`, `edge_case_matrix`, `feature_flags`. That is 21 top-level fields, many with sub-fields. |
| Pre-TDD Validation Gate | Catches schema errors | Moderate value but adds a full validation loop before work begins |
| Plan Quality Gate | Catches bad plans | Only runs for STANDARD/COMPLEX. Good ROI. |
| Test Quality Gate | Catches bad tests | High value -- prevents wasted implementation effort |
| Code Quality Gate (TECH_DEBT + AI_SLOP) | Catches code issues | Runs two separate checker instances. Moderate value. |
| Full 14-dimension Quality Review | Comprehensive review | Very high ceremony. After already passing 3 quality gates, running a FOURTH review with 14 dimensions often just re-finds what the gates already caught. |
| Final Principal Engineer Review | Fresh-eyes review | Even MORE ceremony on top of quality review. |
| PM UAT Generation | Creates UAT checklist | Adds a PM agent invocation for every story completion. |

**The full orchestration pipeline for a single story is: validate -> scaffold -> plan -> [Plan Quality Gate] -> tests -> [Test Quality Gate] -> code -> [Code Quality Gate] -> quality review -> PM UAT -> final review.**

That is 11 phases, 4 quality gates, and requires spawning at minimum 7 sub-agent invocations (developer 4x, checker 3x, quality 1x, PM 1x). For a SIMPLE tier story that changes one file, this is absurd overkill.

---

## 3. Dead Code & Abandoned Features

### 3.1 The _to_be_deleted Directory

**97 files, 37,057 lines -- 40% of the entire framework.**

Contents fall into three categories:

**A. Old Command System (23 files)**
Path: `.claude/_to_be_deleted/commands/forge/_deprecated/`
Files: `analyze.md`, `design.md`, `design-continue.md`, `develop.md`, `develop-code.md`, `develop-plan.md`, `develop-tests.md`, `enrich.md`, `help.md`, `hotfix.md`, `init.md`, `merge.md`, `orchestrate.md`, `orchestrate-parallel.md`, `plan.md`, `quality.md`, `quick.md`, `rollback.md`, `scaffold.md`, `scope.md`, `status.md`, `validate.md`

These are the original slash-command implementations before the framework was refactored to use the unified `/forge-workflow` entry point with skills. Each was a standalone command template. The content was migrated to skills but the originals were never deleted.

**B. Old Template System (20+ files)**
Path: `.claude/_to_be_deleted/forge/templates/`
Files include: `orchestrate.md`, `develop.md`, `quality.md`, `scaffold.md`, `hotfix.md`, etc.

These are the original template files that were used by the old command system. Their content was migrated to skill files. Again, never deleted.

**C. Old Practices Library (21 files)**
Path: `.claude/_to_be_deleted/forge/practices/`
Files include all the practice files (coding.md, testing.md, security.md, etc.) plus architecture patterns and an `index.yml`. These are duplicates of what now lives in `.claude/skills/forge-tdd/practices/`.

**D. Old Scripts (10 files)**
Path: `.claude/_to_be_deleted/forge/scripts/`
Files: `bootstrap.sh`, `check_tools.py`, `doctor.py`, `forge_dispatch.py`, `init_project_memory.py`, `migrate_stories.py`, `static_analysis.py`, `validate.py`, `validate_stories.py`, `verify_enforced_tests.py`

The `forge_dispatch.py` is particularly interesting -- it was an intent-classification Python script that has been replaced by the natural language classification in the orchestrator SKILL.md. Several scripts (`migrate_stories.py`, `verify_enforced_tests.py`) represent features that were planned but apparently abandoned.

**E. Old Profile/Config Files**
Path: `.claude/_to_be_deleted/forge/profiles/`
Files: `active.yml`, `universal.yml`

Duplicates of what now lives in `.claude/skills/forge-reference/profiles/`.

### 3.2 Features That Don't Actually Work

**MCP Servers (Disabled):**
File: `.claude/mcp.json`
Both MCP servers (`forge-github` and `forge-ci`) are explicitly `"disabled": true` with comments saying "Enable when implemented." The server files (`.claude/mcp/servers/github-server.js` and `ci-server.py`) exist but their implementation status is unknown. These are vaporware entries.

**Self-Learning Auto-Trigger:**
The orchestrator SKILL.md describes an elaborate auto-trigger system for pattern analysis that runs after every workflow completion. However:
- The `events.jsonl` file that it reads from is never mentioned in any hook configuration
- No `PostToolUse` or `Stop` hook calls `log_event.py`
- The learning scripts reference `from .claude.scripts.pattern_matcher import ...` which is invalid Python (dotted imports with leading dot inside a non-package directory)
- The subprocess.Popen call in the orchestrator uses Python path syntax that would fail

The entire learning system appears to be designed but never integrated.

**Merge Intent:**
The `merge` intent is listed in the orchestrator's intent table but the handler just says "Handle merging of completed stories" with no real implementation. The `_to_be_deleted/commands/forge/_deprecated/merge.md` was apparently never migrated.

**Rollback:**
Referenced in `forge-auto-router.md` as a route target and in `forge-developer.md` as a mode, but there is no actual rollback implementation in any active skill file. The `_to_be_deleted/commands/forge/_deprecated/rollback.md` was never migrated.

**forge-statusline.sh Hook:**
File: `.claude/hooks/forge-statusline.sh`
This hook exists but is not referenced in `settings.json` hooks configuration. It appears to be an orphaned file.

**validate-story.py Hook:**
File: `.claude/hooks/validate-story.py`
Listed in the hooks directory but not referenced in `settings.json`. Only `validate-story-alignment.sh` (different file) is actually configured.

**CI Hooks (Pre-commit, Pre-push):**
Files: `.claude/hooks/ci/pre-commit.sh`, `.claude/hooks/ci/pre-push.sh`
These exist in a `ci/` subdirectory but are not referenced in `settings.json`. Their purpose is unclear -- they may have been intended for git hook integration but are not active.

### 3.3 Orphaned Files

- `.claude/CLAUDE.template.md` -- Template for CLAUDE.md but the actual CLAUDE.md already exists. It is unclear when this template would be used.
- `.claude/skills/forge-check/__pycache__/lock.cpython-311.pyc` and multiple other `.pyc` files -- Compiled Python cache files committed to the repository.
- `.claude/skills/forge-check/lock.py` -- A file locking utility that appears to support concurrent checker runs, but the framework does not actually invoke concurrent checkers on the same story (they are sequential or on different stories).
- `forge-claudify.code-workspace` -- VS Code workspace file, not relevant to the framework functionality.

---

## 4. Naming & Organization Issues

### 4.1 Inconsistent Naming Patterns

**Agent naming:**
Most agents follow `forge-{role}` but two break the pattern:
- `python-pro.md` -- Not prefixed with `forge-`
- `typescript-pro.md` -- Not prefixed with `forge-`

These are also the only agents without the `skills:` field in frontmatter, suggesting they were added separately and not integrated into the Forge workflow.

**Skill naming:**
Some skills follow `forge-{domain}` but others do not:
- `brainstorming` -- No `forge-` prefix
- `error-resolver` -- No `forge-` prefix
- `product-manager-toolkit` -- No `forge-` prefix, uses different naming style
- `subagent-driven-development` -- No `forge-` prefix, verbose name

**The forge-check vs forge-quality distinction:**
The names do not convey the actual difference. "check" and "quality" are near-synonyms. A developer encountering this framework cannot intuit that "check" means "automated validation gates during TDD" while "quality" means "comprehensive post-implementation review." Better names would be something like "forge-gates" and "forge-review."

**File naming within skills:**
- `forge-check/` has `ai-slop-checklist.md`, `design-checklist.md` (kebab-case)
- `forge-reference/` has `world-class-standard.md`, `guard-tokens.md` (kebab-case)
- `forge-tdd/` has `tdd-workflow.md`, `handoff-schema.md` (kebab-case)
- Scripts use `snake_case`: `check_ai_slop.py`, `validate_stories.py`

This is actually consistent (kebab for markdown, snake for Python), which is fine.

### 4.2 Confusing Folder Structure

```
.claude/
  agents/           # 12 agent definitions
  hooks/            # 6 hook scripts (2 orphaned)
    ci/             # 2 CI hook scripts (orphaned)
  mcp/
    servers/        # 2 disabled MCP servers
  rules/            # 5 rule files
  scripts/          # 6 Python scripts (learning system)
  settings.json     # Claude Code settings
  settings.local.json # Local overrides
  skills/           # 11 skill directories
    brainstorming/
    error-resolver/
    forge-analyze/
    forge-check/
      scripts/      # 8 Python check scripts
        lib/        # Shared library
    forge-design/
    forge-plan/
    forge-quality/
      practices/    # 2 practice files
      references/   # 1 evidence checklist
    forge-reference/
      profiles/     # 2 profile configs
    forge-tdd/
      practices/    # 18 practice files
        architectures/ # 6 architecture patterns
    forge-workflow/
      scripts/      # 2 utility scripts
    product-manager-toolkit/
      scripts/      # 2 PM scripts
      references/   # 1 PRD template
    subagent-driven-development/
  templates/        # Project init templates
    forge/
      docs/
      memory/
        learning/
  _to_be_deleted/   # 97 files of dead code
```

**Problems:**

1. **Practice files are in the wrong place.** Coding practices (testing.md, security.md, etc.) are under `forge-tdd/practices/` but they apply to ALL development, not just TDD. They should be in `forge-reference/` or a shared `practices/` directory. The `forge-quality/practices/` directory has its own security.md and observability.md, duplicating what is in `forge-tdd/practices/`.

2. **Scripts are scattered across 5 locations:**
   - `.claude/scripts/` (learning scripts)
   - `.claude/skills/forge-check/scripts/` (check scripts)
   - `.claude/skills/forge-analyze/scripts/` (static analysis)
   - `.claude/skills/forge-workflow/scripts/` (doctor, check_tools)
   - `.claude/skills/product-manager-toolkit/scripts/` (PM scripts)

   There is no central scripts directory and no shared import path.

3. **Templates directory purpose is unclear.** `.claude/templates/forge/` contains templates for project initialization (Architecture.md.template, PRD.md.template, settings.yml.template). But the `init.md` skill references creating these files directly. The template directory's relationship to the init workflow is implicit.

4. **The `_to_be_deleted` directory.** If it should be deleted, delete it. Its continued existence in the repository means it shows up in searches, confuses navigation, and makes the framework look larger than it is.

### 4.3 Things in the Wrong Location

| File | Current Location | Should Be |
|------|-----------------|-----------|
| Practice files (18) | `forge-tdd/practices/` | `forge-reference/practices/` (shared across agents) |
| `security.md`, `observability.md` | `forge-quality/practices/` | Same shared location |
| `evidence-checklist.md` | `forge-quality/references/` | `forge-reference/` (used by multiple agents) |
| `profiles/` | `forge-reference/profiles/` | `forge/config/` or top-level config |
| `practices-index.yml` | `forge-reference/` | `forge-reference/practices/` (with the practices) |
| Learning scripts (5) | `.claude/scripts/` | Should be in a single `forge-learning/` skill if kept |

---

## 5. Architecture Anti-Patterns

### 5.1 The God File: forge-workflow/SKILL.md

At 1,481 lines, this is by far the largest and most complex file in the framework. It is the orchestrator skill definition and it tries to do everything:

- Intent classification (table + decision tree)
- Orchestrator boundary enforcement (repeated 3 times)
- Inline handlers for 7 intents (help, init, status, scope, learn, merge, validate)
- Delegation instructions for 13 intents
- Pre-TDD validation gate (complete with error categories and auto-fix logic)
- Create-Check-Fix loop (with pseudo-code and ASCII diagrams)
- PM integration points (with example Task invocations)
- Self-learning system integration (with Python code examples)
- Quality gate descriptions (duplicating forge-check/SKILL.md)

This file violates the Single Responsibility Principle at the file level. It should be broken into at least 5 smaller files.

### 5.2 Circular Knowledge Dependencies

```
forge-framework.md (rule) → references forge-workflow skill
forge-auto-router.md (rule) → routes to forge-workflow skill
forge-workflow/SKILL.md → references intent-handlers.md
intent-handlers.md → references forge-checker agent
forge-checker agent → loads forge-check skill
forge-check/SKILL.md → references forge-reference skill
forge-reference/SKILL.md → references world-class-standard.md
world-class-standard.md → references quality-review.md (in forge-quality skill)
forge-quality/SKILL.md → references forge-reference skill
```

The reference chain is long and sometimes circular. `forge-reference` is loaded by both `forge-check` and `forge-quality`, but `world-class-standard.md` within `forge-reference` references content that lives in `forge-quality`. If content is shared, it should live in exactly one place.

### 5.3 Leaky Abstractions

**The orchestrator "never implements" but does:** The orchestrator SKILL.md repeatedly states "NEVER implement directly" and defines strict boundaries. Yet the file itself contains:
- Complete inline implementation for 7 intents (help, init, status, scope, learn, merge, validate)
- Pseudo-code that is essentially implementation (the `orchestrate_with_check` function, the `detect_check_mode` function)
- Detailed Python code for learning system integration

**Agents duplicate skill content:** The `skills:` frontmatter in agent files tells Claude Code to load those skills. But then the agent body repeats the skill's instructions, creating a leaky abstraction where the agent both delegates to and duplicates the skill.

**Rules duplicate workflow content:** The `forge-framework.md` rule lists all intents, scopes, and file locations. This is the same information that the orchestrator SKILL.md provides when invoked. The rule is always loaded; the skill is loaded on invoke. The overlap means changes must be synchronized.

### 5.4 Tight Coupling Between Components

**Story YAML schema couples everything:** The story schema is the central data format that couples:
- The planner (creates stories)
- The validator (validates stories)
- The developer (reads stories for implementation)
- The checker (validates story artifacts)
- The quality reviewer (reads stories for review)

Any change to the story schema requires updating: the story-schema.md, the story-validation.md rule, the validate_stories.py script, the planner agent, the developer agent, and potentially the checker agent. There is no schema versioning.

**Handoff YAML couples orchestrator to developer:** The handoff file format is the integration point between the orchestrator, developer, checker, and quality agents. Changes to the handoff schema (e.g., adding a new phase gate) require coordinating changes across multiple files.

### 5.5 The Settings Fragmentation Problem

Coverage thresholds are defined in multiple places with a "read from settings, fallback to default" pattern:
- `forge/settings.yml`: `tdd.coverage_threshold: 90`
- `forge-developer.md`: "default 90 if not set"
- `forge-test-engineer.md`: "default: 90%"
- `forge-tdd/SKILL.md`: "STANDARD: 90%"
- `settings.json`: `FORGE_MIN_COVERAGE: "90"`

Every agent is told to "read settings first" but they all have their own hardcoded fallbacks. If you want to change the coverage threshold, you need to update settings.yml AND verify that all the fallback values match.

---

## 6. Missing Capabilities (Gaps)

### 6.1 No Error Recovery or Debugging Support

When something goes wrong during orchestration (e.g., a sub-agent fails, a test framework is not installed, a coverage tool is not available), the framework's response is:
- "Attempt ONE retry with enhanced context"
- "If retry fails, report both failures and stop"

There is no:
- Diagnostic mode to identify what went wrong
- Ability to resume from a failed phase (the handoff tracks phases but resume logic is fragile)
- Interactive debugging where the user can step through phases
- Log of what happened during sub-agent execution

### 6.2 No Rollback Implementation

The `rollback` intent is referenced in the auto-router, the developer agent (as "Rollback Mode"), and the orchestrator intent table. But there is NO actual rollback implementation in any active file. The deprecated command file was never migrated. If a developer completes the code phase but the quality review reveals fundamental problems, there is no supported way to roll back to the plan phase.

### 6.3 No Incremental / Partial Workflow Support

The framework assumes you will run the full pipeline (analyze -> design -> plan -> develop -> quality). There is no support for:
- Using Forge on just ONE file change without creating a story
- Quick iteration cycles (edit -> test -> review) without the full ceremony
- Applying quality checks to code that was written outside of Forge
- "Lite" mode for small changes (the SIMPLE tier helps but still requires a story YAML)

### 6.4 No Multi-Language Parity

The test execution section in `forge-tdd/SKILL.md` covers pytest, jest, vitest, go test, cargo test, and rspec. But the check scripts (`check_ai_slop.py`, `check_tech_debt.py`, `check_test_quality.py`) are all Python scripts that analyze code by pattern-matching. They would likely fail or produce garbage results for non-Python codebases.

The `python-pro.md` and `typescript-pro.md` agents exist but are never referenced by the Forge workflow. They appear to be standalone agents not integrated into the pipeline.

### 6.5 No Version Migration Support

There is no mechanism for migrating from one version of the Forge framework to another. The `_to_be_deleted` directory represents an old version but there is no migration script or guide. If a user has stories and handoff files from an older version, there is no path to upgrade.

### 6.6 No Real Git Integration

Despite blocking main branch edits and creating feature branches, the framework has:
- No PR creation support (the MCP github server is disabled)
- No commit message formatting
- No changelog generation
- No branch naming enforcement (the scaffold mentions `feat/{story_id}-*` but it is not enforced)
- The merge intent is effectively unimplemented

### 6.7 No Observability of the Framework Itself

There is no way to answer:
- How long does a typical orchestration take?
- Which phases fail most often?
- What percentage of quality gates pass on first try?
- How much token budget does the framework consume?

The learning system was supposed to address this but it is not connected.

---

## 7. Prompt Engineering Issues

### 7.1 Excessive Repetition Within Files

The orchestrator SKILL.md is the worst offender. The "MANDATORY POST-COMPLETION GATES" concept is stated:

1. At the very top under "MANDATORY POST-COMPLETION GATES (READ FIRST)" -- a table
2. In "CHECKPOINT: Orchestrator Boundaries" -- prose explanation
3. In "CHECKPOINT: After Sub-Agent Returns" -- another table and decision tree
4. In "Step 4: Verify and Report" -- yet another table with gate references

Each repetition adds tokens without adding information. A well-structured prompt states critical information ONCE, clearly, at the right point in the instruction flow.

### 7.2 Mixed Abstraction Levels

The orchestrator SKILL.md mixes:
- High-level intent tables (good for quick lookup)
- Detailed pseudo-code implementations (appropriate for a separate reference file)
- ASCII art diagrams (visually helpful but token-expensive)
- Python code examples (implementation detail that should be in the skill, not the orchestrator prompt)

A prompt should maintain a consistent abstraction level. If the orchestrator is a coordinator, its prompt should describe coordination, not implementation.

### 7.3 Vague Instructions Alongside Specific Ones

From `forge-checker.md`:
> "Think like a senior engineer who has been burned by production incidents"

This is followed by very specific checklist items and scripts to run. The motivational preamble adds nothing actionable. LLMs do not need to be motivated; they need clear instructions.

From `forge-quality.md`:
> "You are a Principal Engineer performing quality review."

This persona instruction is repeated in nearly every agent. The word "Principal" or "Senior" appears in: forge-analyzer ("Principal Engineer"), forge-checker ("Principal Engineer"), forge-designer ("Principal Engineer"), forge-developer ("Senior Software Engineer (FAANG-calibre)"), forge-planner ("Principal Engineer"), forge-product-manager ("Principal Product Manager"), forge-quality ("Principal Engineer"). This is cargo-cult prompt engineering.

### 7.4 Over-Specification of Agent Behavior

The `forge-planner.md` agent (235 lines) includes a detailed "CRITICAL RULES" section with examples of correct and incorrect YAML. This is helpful. But then the agent also includes a "Final Verification (MANDATORY)" section that describes a verification loop, AND references the `forge-check` scripts for validation. The agent is being told to self-validate AND the orchestrator will also validate after the agent returns. This creates confusion about who is responsible for validation.

### 7.5 Prompt Duplication Across Files

The "CLARIFICATION_NEEDED" pattern is described identically in 5 agent files:
- forge-analyzer.md
- forge-designer.md
- forge-developer.md
- forge-planner.md
- forge-quality.md

Each includes the same format specification:
```
CLARIFICATION_NEEDED

Questions requiring answers before proceeding:

1. [CATEGORY: ...]
   Question: <text>
   Context: <why>
   Options: <options>
```

This could be a single shared reference in `forge-reference/` loaded by all agents, rather than duplicated 5 times.

### 7.6 Token-Expensive ASCII Art

The orchestrate.md file includes multiple large ASCII diagrams:
- The quality gates architecture diagram (~15 lines)
- The quality gate fix loop diagram (~30 lines)
- Multiple box-drawing diagrams for flows

These diagrams consume significant tokens and provide minimal value to an LLM that processes text sequentially. A concise textual description would be more token-efficient.

---

## 8. Configuration Mess

### 8.1 Configuration File Inventory

| File | Purpose | Format |
|------|---------|--------|
| `.claude/settings.json` | Claude Code permissions, hooks, env vars | JSON |
| `.claude/settings.local.json` | Local permission overrides | JSON |
| `forge/settings.yml` | Project settings (coverage, quality, learning) | YAML |
| `.claude/templates/forge/settings.yml.template` | Template for init | YAML |
| `.claude/skills/forge-reference/profiles/active.yml` | Active profile (archetype, performance targets) | YAML |
| `.claude/skills/forge-reference/profiles/universal.yml` | Universal scope definitions | YAML |
| `.claude/skills/forge-reference/practices-index.yml` | Practice file index | YAML |
| `forge/memory/project.yml` | Project state (sprints, stories) | YAML |
| `forge/memory/important_decisions.yml` | Architectural decisions | YAML |
| `forge/memory/learning/patterns.yml` | Learned patterns | YAML |
| `forge/memory/learning/pattern_performance.yml` | Pattern effectiveness | YAML |
| `.claude/mcp.json` | MCP server configuration | JSON |

**That is 12 configuration files across 3 different formats (JSON, YAML, YAML templates).**

### 8.2 Overlapping Configuration

**Coverage thresholds are defined in 3 places:**
1. `forge/settings.yml`: `tdd.coverage_threshold: 90`
2. `.claude/settings.json`: `"FORGE_MIN_COVERAGE": "90"` (env var)
3. Each agent file has hardcoded fallback values

**Quality gate parameters are defined in 2 places:**
1. `forge/settings.yml`: `quality.p0_blocking: true`, `quality.p1_threshold: 2`
2. Hard-coded in rule files, skill files, and agent files

**Profile/archetype configuration:**
- `active.yml` defines the project archetype (auto-detect or explicit)
- `forge/settings.yml` defines `project.architecture: "auto"`
- Both represent the same concept (what kind of project is this?) in different files

### 8.3 Settings That Are Never Read

- `quality.persist_verification_tests: auto` in `forge/settings.yml` -- this setting is never referenced in any agent, skill, or script
- `learning.auto_trigger.time_threshold_hours: 24` -- referenced only in the learning system which is not connected
- The `performance_defaults` in `active.yml` (p95_latency_ms, max_memory_mb) -- never referenced by any agent or script

### 8.4 No Settings Validation

There is no schema or validation for `forge/settings.yml`. If a user sets `tdd.coverage_threshold: "ninety"` instead of `90`, the framework will silently use the fallback value. The `check_tools.py` and `doctor.py` scripts in `forge-workflow/scripts/` appear to perform some validation, but they are not invoked by any hook or startup process.

---

## 9. Maintainability Score

Rating each component on a 1-10 scale (1 = unmaintainable, 10 = trivially maintainable):

| Component | Score | Justification |
|-----------|-------|---------------|
| **CLAUDE.md** | 8/10 | Small, clear, points to the right places. Slightly undermined by being a template for a framework repo. |
| **Rules (5 files)** | 4/10 | They duplicate content from skills. Any change requires updating both. The auto-router is fragile (keyword matching duplicated from the orchestrator). |
| **forge-workflow SKILL.md** | 2/10 | At 1,481 lines, this is unmaintainable. Changes require understanding the entire file. Information is repeated internally. Dependencies on other files are implicit (references intent-handlers.md, orchestrate.md, pm-touchpoints.md, etc.). |
| **orchestrate.md** | 3/10 | At 962 lines, also too large. Contains detailed pseudo-code that would need updating for any workflow change. The quality gate fix loop alone is ~100 lines of pseudo-code. |
| **forge-checker agent** | 5/10 | Well-structured with clear modes, but at 329 lines it duplicates the forge-check skill significantly. |
| **forge-quality agent** | 6/10 | Reasonably sized at 163 lines. The main issue is overlap with forge-checker. |
| **forge-developer agent** | 5/10 | At 205 lines, reasonable size but duplicates forge-tdd skill content. The "Settings Consumption (REQUIRED)" section at the top is a maintenance smell -- it means agents are not automatically reading settings. |
| **forge-planner agent** | 5/10 | Detailed validation rules are helpful but create maintenance burden when the story schema changes. |
| **forge-product-manager agent** | 3/10 | At 502 lines, far too large. Defines 5 separate workflows inline. Should be decomposed. |
| **forge-test-engineer agent** | 2/10 | Orphaned -- not connected to any workflow. 402 lines of content that duplicates forge-developer and forge-checker. Should be deleted or merged. |
| **python-pro / typescript-pro agents** | 6/10 | Standalone, no dependencies, but not integrated with Forge. |
| **forge-check skill** | 5/10 | Good structure with clear domains and scripts, but the SKILL.md duplicates content from the agent and repeats quality gate logic. |
| **forge-quality skill** | 6/10 | Slim SKILL.md (88 lines) that points to sub-files. Better factored than forge-check. |
| **forge-tdd skill** | 5/10 | Good SKILL.md (139 lines) but carries 24 sub-files of practices. The practices are stable but any change to TDD workflow requires updating both the skill and the agent. |
| **forge-reference skill** | 7/10 | Well-structured as a shared reference. But the world-class-standard.md (223 lines) tries to be both a reference document and a checklist, creating ambiguity. |
| **forge-analyze skill** | 6/10 | Clean 13-phase structure with individual phase files. Main risk is the static_analysis.py script which could break with language updates. |
| **forge-design skill** | 7/10 | Small, well-scoped. The 18-section template is comprehensive. |
| **forge-plan skill** | 6/10 | Small SKILL.md, clean sub-files. The story-schema.md is critical and well-defined. |
| **Learning system** | 1/10 | Five Python scripts with no integration, no tests, no evidence of ever working. A pure liability. |
| **Hooks** | 4/10 | Two active hooks that work, four orphaned hooks. The validate-story-alignment.sh does not actually block operations (exits 0 always), making it a no-op that just prints warnings. |
| **_to_be_deleted** | 0/10 | Should not exist. 97 files of dead weight. |
| **brainstorming skill** | 7/10 | Self-contained, clear process. Not integrated with Forge but useful standalone. |
| **error-resolver skill** | 6/10 | Comprehensive error resolution framework. Not integrated with Forge. |
| **product-manager-toolkit skill** | 5/10 | Overbuilt for its use case. The RICE prioritizer and interview analyzer are niche tools bundled into a coding framework. |
| **subagent-driven-development skill** | 6/10 | Clean, well-documented process. Overlaps significantly with how the Forge orchestrator already works. |
| **Configuration files** | 3/10 | Scattered across 12 files, 3 formats, with overlapping settings and no validation. |

**Weighted Average: ~4.5/10**

---

## 10. Top 15 Recommendations

Ordered by impact (highest first):

### 1. DELETE _to_be_deleted -- Immediately

**Impact: High | Effort: Trivial**
Remove the 97 files / 37,057 lines of dead code. This is a 40% reduction in framework size with zero functionality impact. There is no reason to keep deprecated files in the active tree. If historical reference is needed, git history provides it.

### 2. Merge forge-checker + forge-quality into ONE Quality Component

**Impact: High | Effort: Medium**
The current split between "checker" (TDD gates) and "quality" (post-implementation review) is confusing and creates massive duplication. Merge them into a single quality agent with modes:
- `gate:plan-quality` (during TDD)
- `gate:test-quality` (during TDD)
- `gate:code-quality` (during TDD)
- `review:full` (post-implementation)

A single skill definition with a single agent eliminates the duplication of severity taxonomy, gate logic, and quality dimensions across 6+ files.

### 3. Eliminate Rule-Skill-Agent Triple Redundancy

**Impact: High | Effort: Medium**
Adopt a strict layering:
- **Rules**: Only contain routing/behavioral directives (e.g., "use /forge-workflow for all Forge operations"). No content duplication. Rules should be under 20 lines.
- **Skills**: Contain the reference content (schemas, checklists, practices).
- **Agents**: Are thin wrappers (~50 lines) -- persona, tool access, skill references. No content that the skill already provides.

This means rewriting agents to be concise delegates rather than full documentation repeaters.

### 4. Break Up the Orchestrator SKILL.md

**Impact: High | Effort: Medium**
Split the 1,481-line monolith into focused files:
- `SKILL.md`: Intent classification + sub-agent routing (under 200 lines)
- `intent-handlers.md`: Already exists, make it the single source of truth for intent workflows
- `gates.md`: Quality gate definitions and create-check-fix loop logic
- `pm-integration.md`: PM touchpoints (already partially exists as pm-touchpoints.md)
- Remove inline handlers for simple intents (help, init, status) -- these do not need orchestrator complexity

### 5. Introduce a SIMPLE-Mode Fast Path

**Impact: High | Effort: Medium**
For small changes (one file, low risk), provide a path that bypasses the full ceremony:
- No story YAML required (auto-generate a minimal one)
- Skip plan quality gate
- Skip PM UAT
- Skip final review
- Just: write tests -> write code -> run quality check -> done

This addresses the biggest UX complaint: the framework is too heavy for small changes.

### 6. Delete the Self-Learning System

**Impact: Medium | Effort: Low**
Remove: `learning_state.py`, `pattern_analysis.py`, `pattern_matcher.py`, `apply_pattern.py`, `log_event.py`, `forge-learning-analyzer.md`, and all learning references in the orchestrator SKILL.md.

Replace with a simple `forge/memory/lessons.yml` file that agents can append to, with entries like:
```yaml
- date: 2025-01-15
  story: ST-001
  lesson: "Integration stories need timeout specs"
  category: development
```

This provides 80% of the value at 5% of the complexity.

### 7. Delete or Merge forge-test-engineer

**Impact: Medium | Effort: Low**
This agent is never used in any workflow. Its content overlaps with forge-developer (test execution) and forge-checker (test quality). Either:
- Delete it entirely (recommended)
- Merge its unique content (test pyramid enforcement, edge case matrix) into the forge-tdd skill

### 8. Centralize Practice Files

**Impact: Medium | Effort: Low**
Move all practice files to a single `forge-reference/practices/` directory. Remove the duplicate copies in `forge-tdd/practices/` and `forge-quality/practices/`. Update skill frontmatter to reference the shared location. This eliminates the drift risk of maintaining practices in multiple locations.

### 9. Consolidate Configuration

**Impact: Medium | Effort: Medium**
Reduce from 12 config files to 3:
1. `.claude/settings.json` -- Claude Code platform config (permissions, hooks, env)
2. `forge/config.yml` -- All Forge framework settings (merge settings.yml, active.yml, universal.yml)
3. `forge/memory/project.yml` -- Project runtime state (stories, decisions, sprints)

Add a validation step to the `init` workflow that checks config schema.

### 10. Fix the "CLARIFICATION_NEEDED" Duplication

**Impact: Medium | Effort: Low**
Create a single `forge-reference/clarification-protocol.md` that defines the format. Each agent references it instead of copy-pasting the format definition. This also makes it easy to evolve the protocol in one place.

### 11. Implement Actual Rollback

**Impact: Medium | Effort: Medium**
The rollback feature is advertised but not implemented. Either implement it (using the handoff file to reset phases) or remove all references to it. Having dead references erodes trust in the framework.

### 12. Remove ASCII Art from Prompts

**Impact: Low-Medium | Effort: Low**
Replace all ASCII art diagrams in skill files with concise text descriptions. The quality gate architecture diagram, the fix loop diagram, and the TDD flow diagrams each consume 15-30 lines of tokens. A 3-line textual description would be equally clear to the LLM.

### 13. Reduce Story Schema Complexity for STANDARD Tier

**Impact: Medium | Effort: Medium**
The STANDARD tier requires 16 fields. Several are rarely useful for typical features:
- `determinism` (only needed for stateful/concurrent code)
- `concurrency` (only needed for multi-threaded code)
- `resource_safety` (only needed for external integrations)

Make these optional for STANDARD, only required for COMPLEX. This reduces the planning burden for the majority of stories.

### 14. Connect or Remove MCP Servers

**Impact: Low | Effort: Low**
Either implement the GitHub and CI MCP servers or remove the `mcp.json` file and server stubs. Disabled vaporware clutters the framework.

### 15. Add Framework Self-Test

**Impact: Medium | Effort: Medium**
Create a simple validation command (`/forge doctor`) that checks:
- All referenced files exist
- Config files parse correctly
- Hook scripts are executable
- Required tools (pytest, ruff, mypy) are installed
- No circular skill references
- No orphaned agent files (agents that are never spawned)

The `doctor.py` script exists in `forge-workflow/scripts/` but is never called. Wire it up or replace it with something that actually runs.

---

## Appendix A: Redundancy Heat Map

Files sorted by how many OTHER files contain duplicated content:

| File | Duplicate Count | What Is Duplicated |
|------|----------------|-------------------|
| Severity taxonomy (P0-P3) | 6 files | Gate logic, severity definitions, merge rules |
| Quality dimensions (A-M/N) | 4 files | Dimension names, focus areas, P0 triggers |
| Valid scopes (10) | 4 files | Scope names and descriptions |
| TDD workflow phases | 4 files | plan -> tests (RED) -> code (GREEN) sequence |
| Coverage thresholds | 5 files | 90% standard, 70% hotfix, tier-specific values |
| Guard tokens | 3 files | Token names, triggers, resolutions |
| Intent classification table | 3 files | Intent names, example phrases, sub-agents |
| CLARIFICATION_NEEDED format | 5 files | Question format specification |
| Story tier detection | 4 files | SIMPLE/STANDARD/COMPLEX criteria |

## Appendix B: File Count by Type

| Type | Count | Lines |
|------|-------|-------|
| Markdown (.md) | ~195 | ~75,000 |
| Python (.py) | ~35 | ~12,000 |
| YAML (.yml/.yaml) | ~20 | ~2,500 |
| Shell (.sh) | ~6 | ~300 |
| JSON (.json) | ~4 | ~100 |
| JavaScript (.js) | ~1 | ~50 |
| Other | ~10 | ~1,596 |

**The framework is ~82% markdown prompts**, which means most of the "code" is actually prompt text for LLMs. This has implications for testing -- you cannot unit test prompts the way you test code. Quality assurance for this framework requires running actual LLM interactions and observing outputs.

## Appendix C: The Full Execution Pipeline Token Cost

For a single STANDARD-tier story going through full orchestration:

| Phase | Agent Spawned | Estimated Context Tokens |
|-------|---------------|-------------------------|
| Always-loaded rules | N/A | ~4,000 |
| Orchestrator invocation | forge-workflow | ~18,000 (SKILL.md + orchestrate.md + intent-handlers.md) |
| Pre-TDD validation | Inline script | ~500 |
| Scaffold | forge-developer | ~15,000 (agent + forge-tdd skill + practices) |
| Plan | forge-developer | ~15,000 |
| Plan Quality Gate | forge-checker | ~10,000 (agent + forge-check skill + checklists) |
| Tests (RED) | forge-developer | ~15,000 |
| Test Quality Gate | forge-checker | ~10,000 |
| Code (GREEN) | forge-developer | ~15,000 |
| Code Quality Gate (2x) | forge-checker x2 | ~20,000 |
| Quality Review | forge-quality | ~10,000 (agent + forge-quality skill + review guide) |
| PM UAT | forge-product-manager | ~8,000 (agent + PM toolkit) |
| Final Review | forge-quality | ~10,000 |
| **Total** | **~12 sub-agent spawns** | **~150,000+ tokens** |

This is a rough estimate but illustrates the cost. Each sub-agent gets its own context window loaded with agent definition + skill files + practice files. The total token consumption for a single story is substantial and much of it is redundant information loaded repeatedly across agents.

---

*This analysis is intentionally critical. The Forge framework contains genuinely good ideas -- the single-scope rule, the TDD phase gates, the structured story schema, the separation of concerns between agents. But the execution has become bloated through organic growth without refactoring. The Shaktra redesign has an opportunity to keep the good ideas while cutting the framework to a fraction of its current size.*
