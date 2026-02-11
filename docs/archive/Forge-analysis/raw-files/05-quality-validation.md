# Forge Quality & Validation Infrastructure -- Deep Analysis

## Executive Summary

Forge's quality infrastructure is its most elaborately engineered subsystem. It comprises **7 checklists** totaling **137+ individual checks**, **3 quality gates** in the TDD pipeline, **2 independent review systems** (forge-check and forge-quality), **3 validation hooks**, a severity taxonomy (P0-P3), a guard token system with **40+ tokens**, and a "world-class standard" of **31 engineering principles**. The system is deeply intertwined with the TDD workflow, making quality enforcement structural rather than advisory.

The central tension in this system is between comprehensive coverage (catching every possible issue) and practical usability (not drowning in ceremony). The analysis below examines every component, how they interact, where they overlap, and whether this level of infrastructure actually translates to better code.

---

## 1. Quality Gates: What Exists, When Triggered, Mandatory vs Optional

### Gate Architecture

Forge implements **3 formal quality gates** plus **2 informal phase exit checks**, all embedded in the TDD workflow:

```
PLAN --> [Gate 0: Plan Quality] --> RED (tests) --> [Gate 1: Test Quality] --> GREEN (code) --> [Gate 2: Code Quality] --> QUALITY REVIEW
```

### Gate 0: Plan Quality (Conditional)

- **Location:** After PLAN phase, before RED phase
- **Trigger:** `handoff.yml` has `plan_summary` populated
- **Condition:** Only for STANDARD and COMPLEX tier stories (skipped for SIMPLE)
- **Checker:** `forge-checker` agent in PLAN_QUALITY mode
- **Gate logic:**
  ```
  HIGH impact gaps > 0 --> NEEDS_IMPROVEMENT (1 fix loop)
  MEDIUM impact gaps > 2 --> NEEDS_IMPROVEMENT (1 fix loop)
  else --> PASS
  ```
- **Max fix loops:** 1 (lighter than other gates)
- **Mandatory:** Yes, for qualifying tiers. But only allows 1 fix iteration before proceeding regardless.

**Key insight:** This gate is qualitative, not quantitative. It asks "principal engineer critical thinking" questions rather than running checklists. The output is "Top 3-5 critical gaps" rather than a full findings list. This is the most pragmatic gate in the system.

### Gate 1: Test Quality (Mandatory)

- **Location:** After RED phase (tests written), before GREEN phase (implementation)
- **Trigger:** `handoff.yml` has `test_summary.all_tests_red: true`
- **Checker:** `forge-checker` agent in TEST_QUALITY mode
- **Gate logic:**
  ```
  P0 > 0 --> BLOCKED (cannot proceed to GREEN)
  P1 > 2 --> BLOCKED
  else --> PASS
  ```
- **Max fix loops:** 3
- **Mandatory:** Yes. Cannot proceed to implementation without passing.

**What it checks:** Behavioral assertions (not mock.called), error coverage for all error_handling codes, anti-patterns (over-mocking, flickering tests, giant tests), test independence.

### Gate 2: Code Quality (Mandatory)

- **Location:** After GREEN phase (all tests green), before quality review
- **Trigger:** `handoff.yml` has `code_summary.all_tests_green: true`
- **Checkers:** TECH_DEBT + AI_SLOP (run in parallel)
- **Gate logic:**
  ```
  P0 > 0 --> BLOCKED
  P1 > 2 --> BLOCKED
  else --> PASS
  ```
- **Max fix loops:** 3
- **Mandatory:** Yes.

**What it checks:** Two parallel checkers -- tech debt (timeouts, credentials, complexity, coupling) and AI slop (hallucinated imports, generic names, over-commenting, error quality).

### Phase Exit Gates (Informal)

In addition to the 3 formal gates, the TDD workflow has built-in phase exit checks:

**After RED phase (before Gate 1):**
```bash
ruff check tests/        # Lint
mypy tests/              # Type check
python -c "import pytest; ..."  # Import verification
```

**After GREEN phase (before Gate 2):**
```bash
pytest tests/ -v --tb=short          # All tests pass
pytest tests/ --cov=src --cov-fail-under=90  # Coverage threshold
ruff check src/ tests/               # Lint
mypy src/ --strict                   # Type check
bandit -r src/ -ll                   # Security scan
```

### The Final Quality Review

After all gates pass, `forge-quality` agent performs a comprehensive 14-dimension review (described in Section 4 below). This is the most extensive check and includes independent verification testing.

---

## 2. Checklist System: Complete Catalog

### Checklist Inventory

| Checklist | File | Check Count | Domain | When Used |
|-----------|------|-------------|--------|-----------|
| Plan Quality | `plan-quality-checklist.md` | ~15 qualitative | Plan comprehensiveness | After PLAN phase (STANDARD/COMPLEX) |
| Test Quality | `test-quality-checklist.md` | 20 | Behavioral testing, coverage, anti-patterns | After RED phase |
| Tech Debt | `tech-debt-checklist.md` | 17 | Reliability, complexity, coupling | After GREEN phase |
| AI Slop | `ai-slop-checklist.md` | 18 | AI-generated code quality | After GREEN phase |
| Story Validation | `story-checklist.md` | 47 | Story YAML schema validation | Pre-TDD |
| Design Validation | `design-checklist.md` | 35 | Design document validation | Pre-TDD |
| Gap Report Format | `gap-report-format.md` | N/A (format spec) | Gap report structure | N/A |
| **Total** | | **~152** | | |

### Plan Quality Checklist (Qualitative, ~15 checks)

Organized into 5 categories:
1. **Coverage Completeness** (CHK-PQ-001 to CHK-PQ-004): AC mapping, error handling coverage, invariant coverage, edge case strategy
2. **Failure Mode Analysis** (CHK-PQ-010 to CHK-PQ-012): External call resilience, partial failure handling, concurrent access strategy
3. **Test Strategy Quality** (CHK-PQ-020 to CHK-PQ-022): Behavioral vs implementation testing, mock strategy, test independence
4. **Implementation Soundness** (CHK-PQ-030 to CHK-PQ-033): Component responsibility, pattern appropriateness, complexity vs tier, implementation order
5. **Scope-Specific Deep Dive**: Integration (timeouts, retry, circuit breaker), Security (validation, encoding, auth), Data (transactions, validation, migration)

**Distinctive feature:** Unlike other checklists, this one explicitly says "Do NOT produce a laundry list" and limits output to 3-5 critical gaps. This shows learning from over-engineering -- the plan review was made deliberately lighter.

### Test Quality Checklist (20 checks)

Organized into 5 categories:
1. **Behavioral Focus** (CHK-TQ-001 to CHK-TQ-003): No mock assertions (P1), outcome-based assertions (P1), refactoring safety (P1)
2. **Coverage** (CHK-TQ-010 to CHK-TQ-013): Error path coverage (P0), edge case coverage (P1), invariant coverage (P1), happy path coverage (P1)
3. **Anti-Patterns** (CHK-TQ-020 to CHK-TQ-025): No over-mocking (P1), no flickering tests (P1), no giant tests (P2), no empty assertions (P1), mock at boundaries only (P1), specific exception assertions (P2)
4. **Structure & Maintainability** (CHK-TQ-030 to CHK-TQ-033): Descriptive test names (P2), AAA structure (P3), minimal setup (P2), visible assertions (P2)
5. **Test Independence** (CHK-TQ-040 to CHK-TQ-042): Test isolation (P1), no order dependency (P1), no external dependencies (P1)

**Most impactful checks:** CHK-TQ-010 (error path coverage, P0) and CHK-TQ-001 (no mock assertions, P1) target the two most common test quality issues in AI-generated code.

### Tech Debt Checklist (17 checks)

Organized into 7 categories:
1. **Reliability** (CHK-TD-001 to CHK-TD-003): External calls have timeouts (P0), no hardcoded credentials (P0), bounded user input operations (P0)
2. **Error Handling** (CHK-TD-010 to CHK-TD-012): No exception swallowing (P1), error classification (P1), specific exception types (P2)
3. **Complexity** (CHK-TD-020 to CHK-TD-022): Cyclomatic complexity (P1/P2), nesting depth (P1/P2), function length (P2)
4. **Duplication** (CHK-TD-030 to CHK-TD-031): Code duplication (P1/P2), copy-paste errors (P1)
5. **Coupling** (CHK-TD-040 to CHK-TD-041): Dependency injection (P2), interface segregation (P2)
6. **Dead Code** (CHK-TD-050 to CHK-TD-052): Unused functions (P3), unreachable code (P3), commented code (P3)
7. **Self-Admitted Technical Debt** (CHK-TD-060): SATD detection (P2)

**P0 triggers worth noting:** Missing timeouts on external calls, hardcoded credentials, and unbounded operations on user input. These are genuinely critical production issues.

### AI Slop Checklist (18 checks)

Organized into 7 categories:
1. **Critical Issues** (CHK-AI-001 to CHK-AI-003): Hallucinated imports (P0), missing input validation (P0), missing timeout on external calls (P0)
2. **Generic Patterns** (CHK-AI-010 to CHK-AI-012): Generic function names (P2), generic variable names (P2), placeholder logic (P1)
3. **Over-Documentation** (CHK-AI-020 to CHK-AI-021): Over-commenting obvious code (P2), redundant docstrings (P2)
4. **Missing Contracts** (CHK-AI-030 to CHK-AI-032): Missing type hints (P2), missing error documentation (P2), missing return documentation (P2)
5. **Error Handling Quality** (CHK-AI-040 to CHK-AI-041): Generic error messages (P1), no error classification (P1)
6. **Code Structure** (CHK-AI-050 to CHK-AI-052): God functions (P2), inconsistent patterns (P2), magic numbers/strings (P2)
7. **Testing Quality** (CHK-AI-060 to CHK-AI-061): Tests mirror implementation (P2), no negative tests (P2)

**Overlap with tech debt:** CHK-AI-003 (missing timeouts) explicitly references tech-debt-checklist.md CHK-TD-001. CHK-AI-041 (no error classification) references CHK-TD-011. These are intentional cross-references, not accidental duplication, but the same issue could be flagged twice when both checkers run in parallel.

### Story Checklist (47 checks)

The most granular checklist, organized into 13 categories:
- **Identity** (5): Valid story ID, title length, description quality, single scope, valid scope value
- **Files** (4): File count (1-3), file structure, valid action, SIMPLE tier constraint
- **Interfaces** (4): Interfaces present, implements structure, uses structure, method signatures
- **Acceptance Criteria** (4): Minimum count, criteria structure, unique IDs, testable criteria
- **IO Examples** (4): Present, structure, error case present, notes for complex cases
- **Error Handling** (4): Present, structure, unique codes, valid HTTP status
- **Tests** (6): Present, unit tests exist, structure, function name pattern, coverage traceability, assertion details
- **Invariants** (4): Present, structure, enforcement location, test reference valid
- **Failure Modes** (4): Present, structure, test reference valid, fallback defined
- **Edge Cases** (4): Present, category coverage (5/10 for COMPLEX), structure, test reference valid
- **Feature Flags** (2): Required for COMPLEX, flag structure
- **Risk Assessment** (3): Present, valid level, notes present
- **Metadata** (3): Present, valid story points, design doc reference

**Most common failures (noted in bold):** Error case in io_examples, test reference valid in invariants/failure_modes.

### Design Checklist (35 checks)

Organized into 4 categories:
- **Structure** (5): All 18 sections present, section order, no empty sections, proper markdown, feature name in title
- **Standard Sections** (10): Contract specs, error taxonomy, state machines, threat model, invariants, observability, test strategy, ADRs, data model, dependencies
- **World-Class Sections** (8): Failure modes (P2), invariant enforcement (P8), state ownership (P7), concurrency (P13), determinism (P11), resource safety (P12), edge case matrix, tradeoffs (P18)
- **Content Quality** (7): No placeholder text, consistent terminology, specific values, testable assertions, error code uniqueness, complete examples, valid cross-references
- **Completeness** (5): PRD coverage, architecture alignment, security addressed, scalability considered, rollout plan

**Notable:** The design document requires **18 mandatory sections**, which is an extraordinarily detailed specification format. Most software teams would find this overwhelming for anything short of a large feature.

---

## 3. TDD Implementation: How It Is Actually Enforced

### The Red-Green-Refactor Flow (Forge's Version)

Forge's TDD is a modified version of classical red-green-refactor, expanded with a planning phase and quality gates:

```
PLAN --> [Plan Quality Gate] --> RED (tests) --> [Test Quality Gate] --> GREEN (code) --> [Code Quality Gate] --> QUALITY REVIEW
```

### Phase 1: PLAN (Unified Planning)

The plan phase combines test planning and implementation planning into a single step:

**Test Planning:**
- Derive tests from acceptance_criteria
- Cover all io_examples (happy path + errors)
- Map error_handling codes to test cases
- Include invariants as test assertions
- Identify mocks, fixtures, edge cases

**Implementation Planning:**
- Define components with SRP
- Map requirements to P6-P20 patterns (with actionable guidance)
- Identify scope-specific risks
- Define implementation order (types -> interfaces -> logic -> adapters)

**Output:** `forge/.tmp/{story_id}/implementation_plan.md` and initial `handoff.yml`

### Phase 2: RED (Tests Written, All Failing)

Key enforcement mechanisms:
- Tests MUST fail (guard: `TESTS_NOT_RED`)
- Tests must fail for the RIGHT reason (missing implementation, not syntax errors)
- One behavior per test
- Naming convention: `test_<unit>__given_<precondition>__when_<action>__then_<outcome>`
- Every `failure_modes[]`, `edge_case_matrix[]`, `invariants[]`, and `concurrency.tests[]` entry from the story MUST produce a corresponding test

**Enforcement points:**
1. `test_summary.all_tests_red` must be true in handoff.yml
2. Phase exit gate runs lint + type check + import verification
3. Test Quality Gate (Gate 1) validates behavioral assertions, coverage, anti-patterns

### Phase 3: GREEN (Implementation Makes Tests Pass)

Key enforcement mechanisms:
- MUST follow `plan_summary.implementation_order`
- MUST apply `plan_summary.patterns_applied`
- MUST avoid `plan_summary.scope_risks`
- Coverage must meet threshold (default 90%, configurable in settings.yml)
- All error codes from story must be implemented
- All logging_rules must emit structured logs

**Enforcement points:**
1. `code_summary.all_tests_green` must be true
2. Coverage must meet `tdd.coverage_threshold` from settings
3. Phase exit gate runs all tests, coverage, lint, type check, security scan
4. Code Quality Gate (Gate 2) runs tech debt + AI slop checkers

### Plan Adherence (Dimension N)

A unique aspect of Forge's TDD: the quality review explicitly checks whether the implementation followed the plan. Deviations without justification are findings:

| Deviation Type | Severity |
|----------------|----------|
| Missing risk prevention | P0 |
| Pattern not applied | P1 |
| Component structure differs | P2 |
| Order differs (no impact) | P3 |

### Hotfix Mode

Forge provides a reduced-ceremony path for emergencies:
- 70% coverage threshold (vs 90%)
- Skips quality gates
- Runs existing test suite as regression guard
- Critical paths (auth/, payment/, security/) require `--force` flag
- Generates retroactive story for audit trail
- Can bypass tests entirely with `--skip-tests --force` (dangerous, documented as such)

### How Effective Is This TDD Enforcement?

**Strengths:**
- Writing tests before code is structurally enforced through the handoff state machine
- The `all_tests_red` / `all_tests_green` guards prevent phase-skipping
- Test quality gate before implementation catches bad tests early
- Coverage thresholds are configurable and tier-aware

**Weaknesses:**
- The enforcement is entirely within the LLM agent context. There is no actual CI pipeline enforcing gates -- they are instructions the agent is supposed to follow
- The agent could potentially skip phases if the prompt instructions are overridden
- The handoff.yml state machine relies on the agent truthfully updating it
- No actual execution verification -- the agent self-reports `all_tests_red: true`

---

## 4. Quality vs Check: forge-quality and forge-check Compared

### forge-check (The Checklist Machine)

**Skill file:** `.claude/skills/forge-check/SKILL.md`
**Agent:** `forge-checker` (model: sonnet, tools: Read/Glob/Grep/Bash)
**Skills loaded:** forge-check, forge-reference

**Purpose:** Owns all validation -- test quality, tech debt, AI slop, and artifact schema validation. Reports gaps for creators to fix.

**Key property:** Read-only. Never modifies artifacts.

**Modes of operation:**
| Mode | When | What It Checks |
|------|------|----------------|
| PLAN_QUALITY | After PLAN | Plan comprehensiveness, scope patterns |
| TEST_QUALITY | After RED | Behavioral testing, coverage, anti-patterns |
| TECH_DEBT | After GREEN | Timeouts, credentials, complexity, coupling |
| AI_SLOP | After GREEN | AI-generated code patterns |
| ARTIFACT | Pre-TDD | Story/design schema validation |

**Output:** `findings.yml` or `gap_report.yml` in `forge/.tmp/check/{artifact_id}/`

### forge-quality (The Principal Engineer)

**Skill file:** `.claude/skills/forge-quality/SKILL.md`
**Agent:** `forge-quality` (model: sonnet, tools: Read/Write/Bash/Glob/Grep)
**Skills loaded:** forge-quality, forge-reference
**Hooks:** Stop hook runs `check-p0-findings.py`

**Purpose:** Comprehensive quality review as a final gate before merge.

**Key property:** Can write (unlike forge-checker). Runs verification tests, updates story status, consolidates decisions.

**Steps:**
1. **Tool Verification** (pytest, coverage, ruff, mypy, bandit)
2. **Coverage Gate** (pre-CCR, blocks if below threshold)
3. **14-Dimension Code Review** (CCR -- Comprehensive Code Review)
4. **Independent Verification Testing** (5+ tests different from developer tests)
5. **Automated QA** (tests, coverage, lint, type check, security)
6. **Decision Consolidation** (promote important_decisions to project memory)
7. **Design Doc Completion Check** (mark design as IMPLEMENTED if all stories done)

### The Overlap

| Concern | forge-check | forge-quality | Overlap? |
|---------|-------------|---------------|----------|
| Behavioral test assertions | TEST_QUALITY mode | Dimension I (Testing) | YES |
| Missing timeouts | TECH_DEBT mode | Dimension B (Failure Modes) | YES |
| Hardcoded credentials | TECH_DEBT mode | Dimension E (Security) | YES |
| Error handling quality | AI_SLOP + TECH_DEBT | Dimension A (Contract) | YES |
| Code complexity | TECH_DEBT mode | Dimension H (Maintainability) | YES |
| Coverage threshold | Not directly | Step 0b (Coverage Gate) | NO |
| Verification testing | Not present | Step 1b (Independent Tests) | NO |
| Story schema | ARTIFACT mode | Not present | NO |
| Design validation | ARTIFACT mode | Not present | NO |
| Decision consolidation | Not present | Step 7 | NO |
| Plan quality | PLAN_QUALITY mode | Dimension N (Plan Adherence) | PARTIAL |

**Assessment:** There is significant overlap in the code quality checking domain. The same timeout issue could be flagged by forge-check's TECH_DEBT mode (CHK-TD-001) AND forge-quality's Dimension B review. The same credential exposure could be flagged by TECH_DEBT (CHK-TD-002) AND Dimension E.

However, they serve different purposes in the pipeline:
- **forge-check** runs at quality gates DURING development (between phases)
- **forge-quality** runs as a final comprehensive review AFTER development

The redundancy is arguably intentional -- catch issues early (forge-check) and verify nothing was missed (forge-quality). But the duplication of effort is real.

---

## 5. Validation Hooks: What They Validate, When They Run

### Hook 1: validate-story-alignment.sh

**File:** `.claude/hooks/validate-story-alignment.sh`
**Type:** PreToolUse hook (Write/Edit operations)
**Exit codes:** 0 = allowed, 1 = blocked

**What it does:**
1. Extracts the file path from the tool input JSON
2. Skips validation for always-allowed paths (forge/, .claude/, README.md, package.json, etc.)
3. Finds the active story by reading the most recent handoff.yml
4. Loads the story's declared `files` section
5. Checks if the file being edited is in the declared files list
6. If NOT in scope: emits a WARNING but **does not block** (exit 0)

**Critical detail from the code:**
```bash
# File not in declared scope - warn but don't block
# (Blocking would be too disruptive in practice)
echo "WARNING: File '$FILE_PATH' is not in story $ACTIVE_STORY declared files."
exit 0
```

**Assessment:** This hook is deliberately toothless. It warns but allows all edits. The comment explicitly acknowledges that blocking would be "too disruptive in practice." This is a pragmatic concession that undermines the scope enforcement story -- the guard token `SCOPE_VIOLATION` exists, but the actual hook never triggers it.

### Hook 2: validate-story.py

**File:** `.claude/hooks/validate-story.py`
**Type:** PreToolUse hook (Write/Edit operations)
**Exit codes:** 0 = valid, 1 = validation failed
**Guard tokens emitted:** `FIX_STORY_SCHEMA`, `REPLAN_SCOPE_FANOUT`, `MISSING_FEATURE_FLAGS`, `EDGE_CASE_COVERAGE_LOW`

**What it does:**
1. Finds the most recently modified story file
2. Auto-detects tier (SIMPLE/STANDARD/COMPLEX) based on points, risk, scope, files
3. Validates required fields for tier
4. Checks single-scope rule
5. Validates feature flags (mandatory for high-risk, security, integration, COMPLEX, or critical path)
6. Validates test fields exist on `failure_modes[]`, `invariants[]`, `edge_case_matrix[]`
7. Validates edge case matrix coverage (3 categories for STANDARD, 5 for COMPLEX)
8. Validates dependencies (no self-reference, no direct circular deps)

**Tier detection logic:**
```python
COMPLEX: points >= 8 OR risk == 'high' OR scope in [security, integration] OR touches critical paths
SIMPLE:  points <= 2 AND risk == 'low' AND len(files) == 1
STANDARD: everything else
```

**Assessment:** This is a well-implemented validator. The auto-tier detection is particularly useful -- it prevents developers from gaming the system by manually setting a lower tier. However, it runs on every Write/Edit operation, which could slow down development if there are many file operations.

### Hook 3: check-p0-findings.py

**File:** `.claude/hooks/check-p0-findings.py`
**Type:** Stop hook (on the forge-quality agent)
**Exit codes:** 0 = safe to stop, 1 = P0 findings exist, block stop

**What it does:**
1. Scans `forge/.tmp/*/quality_report.yml` and `forge/.tmp/*/handoff.yml` for P0 findings
2. Looks for P0 patterns in YAML content using regex (`P0:`, `CRITICAL:`, `**P0**`, etc.)
3. Deduplicates findings
4. If P0 findings exist: prints warning and exits 1 (blocks agent from stopping)
5. Can be bypassed with `FORGE_SKIP_P0_CHECK=1` environment variable

**Assessment:** This is a clever mechanism -- it prevents the quality agent from stopping its work if there are unresolved critical issues. The regex-based scanning is a bit fragile (could match P0 in unrelated contexts), but the deduplication helps. The bypass mechanism is appropriate for emergencies.

---

## 6. Guard Tokens: What They Are and How They Work

### Concept

Guard tokens are **fail-fast signals** -- structured error codes that stop execution immediately when critical conditions are not met. They are not code constructs but rather **convention-based strings** that the LLM agents are instructed to output and respond to.

### Complete Guard Token Inventory

The system defines **40+ guard tokens** across 8 categories:

**Universal Guards (3):**
- `MISSING_STORY` -- Story file not found
- `MISSING_DESIGN_DOC` -- Design document required but not found
- `INVALID_YAML` -- YAML parse error

**Story Guards (4):**
- `FIX_STORY_SCHEMA` -- Missing required fields
- `REPLAN_SCOPE_FANOUT` -- Multiple scopes detected
- `MISSING_FEATURE_FLAGS` -- COMPLEX tier without feature_flags
- `SCOPE_VIOLATION` -- Code changes outside declared scope

**TDD Phase Guards (5):**
- `PHASE_GATE_FAILED` -- Quality checks failed
- `COVERAGE_GATE_FAILED` -- Coverage below threshold
- `VALIDATION_FAILED` -- Implementation doesn't match spec
- `TESTS_NOT_RED` -- Tests pass before implementation
- `TESTS_NOT_GREEN` -- Tests still fail after implementation

**Analysis Guards (2):**
- `ANALYSIS_INCOMPLETE` -- Analysis phases not completed
- `ANALYSIS_FILE_MISSING` -- File missing from manifest

**Design Guards (3):**
- `MISSING_FEATURE_NAME` -- No feature name provided
- `DESIGN_INPUT_MISSING` -- No PRD/analysis inputs
- `CORE_PILLAR_GAP` -- Design doesn't address P1-P5

**Quality Guards (3):**
- `P0_FINDING` -- Critical quality issue
- `P1_FINDING` -- Significant quality issue
- `TOOLS_MISSING` -- Required tools not installed

**Orchestration Guards (4):**
- `BLOCKED` -- Story blocked by another
- `RETRY_EXHAUSTED` -- Max retries reached
- `CIRCULAR_DEPENDENCY` -- Dependency cycle detected
- `WORKFLOW_STEP_SKIPPED` -- Mandatory step not executed

**Scaffold Guards (3):**
- `MISSING_SCAFFOLDS` -- skeleton scope without scaffolds.entrypoint
- `FILE_EXISTS` -- File exists and no --force
- `WRONG_BRANCH` -- On main/master branch

**Merge Guards (4):**
- `NO_STORIES_FOUND` -- No story branches to merge
- `INCOMPLETE_STORIES` -- Stories not done
- `UNRESOLVABLE_CONFLICT` -- Auto-resolution failed
- `POST_MERGE_FAILED` -- Tests fail after merge

**Checker Loop Guards (5):**
- `CHECK_PASSED` -- All checks pass
- `CHECK_PASSED_WITH_WARNINGS` -- Pass with warnings
- `CHECK_GAPS_FOUND` -- Validation gaps found
- `CHECK_ESCALATE` -- Max attempts or unfixable
- `CHECK_NO_PROGRESS` -- Gap count unchanged

### Output Format

```
{TOKEN_NAME}

{Brief explanation of what triggered it}

{Resolution steps}
-> command to run
```

### How They Work In Practice

Guard tokens are a **prompt engineering pattern**, not a runtime mechanism. The LLM agents are instructed to:
1. Check for certain conditions
2. If conditions are not met, output the guard token string
3. STOP processing immediately

The hooks (validate-story.py, check-p0-findings.py) provide actual enforcement through exit codes, but most guard tokens are purely convention-based -- they rely on the LLM following instructions.

**Assessment:** Guard tokens are an intelligent adaptation to the constraint that LLM agents cannot truly enforce rules. They provide a structured vocabulary for failure modes. However, their effectiveness depends entirely on the LLM reliably following the instruction to check for and emit them. There is no runtime validation that a guard token was properly evaluated.

---

## 7. AI Slop Detection: What It Checks and Effectiveness

### What "AI Slop" Means in This Context

The AI slop checklist specifically targets patterns commonly produced by LLMs writing code. The term reflects the observation that LLMs tend to produce code that "works" but lacks the quality markers of code written by experienced engineers.

### The 18 Checks

**P0 (Critical -- 3 checks):**
1. **Hallucinated imports** (CHK-AI-001): Modules that do not exist imported. LLMs sometimes invent library names. Verification: check each import against stdlib, requirements.txt, and local modules.
2. **Missing input validation** (CHK-AI-002): User input used without sanitization. Detection: functions accepting external input that flow directly to eval(), SQL, or system calls.
3. **Missing timeout on external calls** (CHK-AI-003): HTTP/API calls without timeout parameters. Cross-referenced with tech-debt CHK-TD-001.

**P1 (Significant -- 2 checks):**
4. **Placeholder logic** (CHK-AI-012): TODO markers in critical paths, `raise NotImplementedError("Fix later")`, `pass` in implementation functions.
5. **Generic error messages** (CHK-AI-040): `raise Exception("Failed")`, `logger.error("Error occurred")`, `return {"error": "Invalid input"}` without context.

**P2 (Quality -- 11 checks):**
6-7. **Generic function/variable names** (CHK-AI-010/011): `process_data()`, `handle_request()`, `data`, `result`, `item`.
8-9. **Over-commenting/Redundant docstrings** (CHK-AI-020/021): Comments that restate code, docstrings that just repeat the signature.
10-12. **Missing contracts** (CHK-AI-030/031/032): No type hints, no error documentation, no return documentation.
13-15. **Code structure** (CHK-AI-050/051/052): God functions, inconsistent error handling patterns, magic numbers.
16. **No error classification** (CHK-AI-041): Only generic Exception types.
17-18. **Testing quality** (CHK-AI-060/061): Tests mirror implementation, no negative tests.

### Effectiveness Assessment

**Likely effective checks:**
- **Hallucinated imports (P0):** This is a real and common LLM failure mode. Checking imports against actual available packages is straightforward and high-value.
- **Placeholder logic (P1):** LLMs frequently leave TODO stubs, especially in complex functions. Catching these prevents incomplete features.
- **Generic error messages (P1):** LLMs default to generic messages. Requiring context (error codes, correlation IDs) genuinely improves debuggability.
- **Over-commenting (P2):** LLMs are notorious for adding comments like "# Import the requests library" above `import requests`. This check has real value.

**Questionable checks:**
- **Generic variable names (P2):** The detection of names like `data`, `result`, `item` will produce many false positives. Sometimes `result` is the most appropriate name for a variable holding a result. The exceptions list (loop variables, lambda params) is insufficient.
- **Missing type hints (P2):** While useful, this overlaps with mypy --strict which is already run in the phase exit gate.
- **Tests mirror implementation (P2):** Difficult to distinguish automatically between "test mirrors implementation" and "test verifies important implementation detail."

**Missing checks that would be valuable:**
- Hardcoded URLs or endpoints (common in LLM output)
- Inconsistent encoding/string handling
- Missing `async` on functions that should be async
- Excessive use of `Any` type

---

## 8. Standards Definition: The "World-Class Standard"

### Structure

The world-class standard is defined in `world-class-standard.md` and comprises **31 principles** organized into 4 parts:

**Part 1: Core Pillars (P1-P5) -- Non-Negotiables:**

| # | Principle | Summary |
|---|-----------|---------|
| P1 | Correctness Under Real Conditions | Works for happy paths, bad inputs, failures, concurrency, and scale |
| P2 | Predictable Failure Behavior | Fail fast, fail safely, degrade gracefully |
| P3 | Operational Excellence Built-In | Observable, debuggable, deployable by design |
| P4 | Change Is Cheap | Strong boundaries, low coupling, good tests |
| P5 | Security & Data Integrity by Default | Least privilege, validated inputs, protected secrets |

**Part 2: Developer Disciplines (P6-P20):**
Covers explicit contracts, minimal state, invariants, error handling, pure core/imperative shell, determinism, resource safety, concurrency, simplicity, testability, clarity, consistency, tradeoffs, performance, and evolution readiness.

**Part 3: Excellence Multipliers (P21-P28):**
Covers dependency hygiene, configuration validation, startup/shutdown, auditability, domain integrity, build quality, backward compatibility, and cost efficiency.

**Part 4: Context-Dependent (P29-P31):**
Multi-tenancy, internationalization, accessibility.

### How Principles Map to Quality Checks

The checker validates against specific principles:

| Principle | Test Quality | Tech Debt | AI Slop |
|-----------|--------------|-----------|---------|
| P2 (Predictable Failure) | Error coverage | Timeout checks | Error handling |
| P8 (Invariants) | Invariant tests | -- | -- |
| P11 (Determinism) | Flickering tests | -- | -- |
| P12 (Resource Safety) | -- | Timeout checks | -- |
| P13 (Concurrency) | Idempotency tests | -- | -- |

### The CCR Review Dimensions (A-N)

The quality review uses 14 dimensions that map to multiple principles:

| Dimension | Focus | P0 Triggers |
|-----------|-------|-------------|
| A: Contract & API | Inputs validated, outputs documented | Unvalidated external input |
| B: Failure Modes | What can fail, timeouts | External call without timeout |
| C: Data Integrity | Corruption prevention, invariants | Possible data corruption |
| D: Concurrency | Race conditions, deadlocks | Race condition, deadlock |
| E: Security | Injection, secrets, auth | Injection, exposed secrets |
| F: Observability | Debug in prod, error logging | No error logging at all |
| G: Performance | Big-O, N+1 queries | Unbounded operation on user input |
| H: Maintainability | Understandable code | (rarely P0) |
| I: Testing | Critical paths tested | No tests for security-critical code |
| J: Deploy & Rollback | Safe deployment | Breaking migration without rollback |
| K: Configuration | Secrets in config | Hardcoded production secrets |
| L: Dependencies | CVEs, licenses | Critical CVE in dependency |
| M: Compatibility | Backward compatible | Breaking change without versioning |
| N: Plan Adherence | Implementation follows plan | Missing risk prevention from plan |

### The Evidence Rule

A distinctive feature: every behavioral claim must be backed by evidence.

```
"This is thread-safe" without tests or synchronization evidence --> P0
"This handles retries correctly" without tests --> P1
"This is performant" without benchmarks --> P2
```

If there is no evidence for a risky behavior, the severity is escalated.

### Assessment

The world-class standard is comprehensive and well-structured. The principles themselves are genuinely good engineering advice drawn from FAANG practices. However:

1. **31 principles is a lot to apply consistently.** In practice, an LLM agent will struggle to meaningfully evaluate all 31 principles for every code review.
2. **The "FAANG-level" framing is aspirational.** Real FAANG code reviews are done by humans who understand the business context. An LLM applying a checklist will produce different results.
3. **The evidence rule is the best part.** Requiring proof for behavioral claims is a concrete, actionable standard that actually improves quality.

---

## 9. Gap Report System

### What Gap Reports Are

Gap reports are structured YAML files that communicate validation failures from the checker to creator agents. They provide enough detail for automated or semi-automated fixing.

### Format

Written to `forge/.tmp/check/{artifact_id}/gap_report.yml`:

```yaml
artifact: "forge/stories/ST-001.yml"
artifact_type: story
check_timestamp: "2024-01-15T10:30:00Z"
check_attempt: 1
max_attempts: 3

gaps:
  - id: GAP-001
    severity: error        # error | warning
    category: content      # schema | content | reference | structure | consistency | completeness
    location: "io_examples"
    issue: "No error case in io_examples"
    requirement: "At least one io_example must show error handling"
    spec_reference: "story-schema.md#io_examples"
    fix_guidance: |
      Add an io_example entry showing an error case.
      [Detailed instructions with code example]
    auto_fixable: false
    suggested_fix: null

summary:
  total_gaps: 1
  by_severity: { error: 1, warning: 0 }
  by_category: { content: 1 }
  fixable_by_creator: 1
  requires_user_decision: 0

escalation:
  needed: false
  reason: null
  gaps_requiring_decision: []
```

### The Check Loop

The orchestrator uses gap reports in a retry loop:

```python
def check_loop(creator_agent, artifact_path, max_attempts=3):
    attempt = 0
    previous_gap_count = None

    while attempt < max_attempts:
        attempt += 1
        result = spawn(forge-checker, f"Check {artifact_path}")

        if result.verdict == "PASSED":
            return SUCCESS

        gap_report = read_yaml(gap_report_path)

        if gap_report.escalation.needed:
            return escalate_to_user(gap_report)

        if attempt > 1 and gap_report.total_gaps >= previous_gap_count:
            return escalate_to_user(gap_report, reason="no_progress")

        previous_gap_count = gap_report.total_gaps
        spawn(creator_agent, f"Fix these gaps: {gap_report.gaps}")

    return escalate_to_user(gap_report, reason="max_attempts")
```

### Escalation Triggers

| Condition | Escalation Reason |
|-----------|-------------------|
| `check_attempt >= max_attempts` | Max attempts reached |
| Gap count unchanged for 2 attempts | Creator cannot fix |
| `requires_user_decision > 0` | Human judgment needed |
| Multiple scopes detected | Requires story split |
| Conflicting requirements | Needs clarification |

### Assessment

The gap report system is well-designed for machine-to-machine communication between agents. The `fix_guidance` field with detailed examples is particularly good -- it gives the fixing agent concrete instructions rather than vague directions.

The check history tracking (`attempt_1.yml`, `attempt_2.yml`, etc.) and no-progress detection are intelligent features that prevent infinite fix loops.

**Potential issue:** The system assumes a maximum of 3 attempts for most gates. If the creator agent cannot fix a gap in 3 attempts, it escalates to the user. This is reasonable, but the gap report format does not include what the creator attempted, making it harder for the user to understand why fixes failed.

---

## 10. Lock Mechanism: lock.py

### What It Is

```python
"""Stub lock module for validation script."""
from contextlib import contextmanager

@contextmanager
def acquire_lock(name: str = "", timeout: int = 30):
    """No-op lock for single-process execution."""
    yield
```

### Analysis

This is a **stub/no-op implementation** of a locking mechanism. The context manager yields immediately without doing anything.

### Why It Exists

The lock module exists as a placeholder for what would be a concurrent-access protection mechanism if multiple checker instances ran simultaneously on the same files. Since the current execution model is single-process (one checker at a time per story), the lock is a no-op.

The SKILL.md mentions that "TECH_DEBT and AI_SLOP (can run in parallel)" after the GREEN phase. If these parallel checkers needed to write to the same findings file, a real lock would be needed. The stub suggests:

1. The original design anticipated concurrent checker execution
2. The implementation found it unnecessary (or the concurrency was handled at a higher level, e.g., separate output directories per checker)
3. The stub was left in place rather than removing the import from consuming scripts

This is itself a minor instance of dead code that the tech debt checklist (CHK-TD-050) would flag.

---

## 11. Over-Engineering Assessment

### Where the Quality System Is Over-Engineered

**1. Dual Review Systems with Substantial Overlap**

Having both forge-check (per-phase gates) and forge-quality (final review) creates redundant checking. The same timeout issue gets checked by:
- CHK-TD-001 in tech debt checklist
- CHK-AI-003 in AI slop checklist
- Dimension B (Failure Modes) in quality review
- Dimension A (Contract & API) in quality review

That is potentially 4 checks for one class of issue.

**2. 152+ Individual Checks Across 7 Checklists**

The sheer volume of checks means:
- Most will never trigger for any given story
- The LLM must "load" all checks into context, consuming tokens
- Diminishing returns after the first ~30 most impactful checks

**3. 18 Required Design Document Sections**

Requiring 18 sections in a design document is enterprise-grade overhead. For small features or SIMPLE stories, this is wildly disproportionate. (Though SIMPLE stories may not require design docs at all.)

**4. 47 Story Validation Checks**

Many of these checks are structural (does field X exist, does it have the right type) rather than quality-oriented. A YAML schema validator (jsonschema or similar) could handle most of these automatically without a custom checklist.

**5. 14-Dimension Review with 10-Category Edge Case Matrix**

The quality review template prescribes reviewing across 14 dimensions and testing 10 edge case categories. For a simple validation function, this is ceremonial. The framework does not appear to scale down the review scope based on story complexity, though the tier system suggests it should.

**6. Guard Token Proliferation (40+ Tokens)**

Having 40+ distinct failure tokens creates a vocabulary that no human (or LLM) can realistically remember. Many tokens serve similar purposes and could be consolidated.

### Where It Is Appropriately Engineered

**1. The Plan Quality Gate**

The plan quality gate is notable for its restraint: 1 fix loop max, top 3-5 gaps only, qualitative not quantitative. This shows awareness of over-engineering.

**2. The Severity Taxonomy (P0-P3)**

The P0-P3 system with concrete merge gate logic is clean and practical:
```
P0 > 0: BLOCKED
P1 > 2: BLOCKED
P1 > 0: WARNING
else: PASS
```

**3. The Evidence Rule**

"Where is the proof?" is a simple, powerful principle that genuinely improves review quality.

**4. Hotfix Mode**

Providing a reduced-ceremony path for emergencies shows pragmatism.

**5. Configurable Thresholds**

Coverage thresholds in settings.yml rather than hardcoded shows flexibility.

### Simplification Opportunities

1. **Merge forge-check and forge-quality** into a single system with configurable depth (quick check vs. comprehensive review)
2. **Replace story/design checklists with JSON Schema** validators for structural checks, keeping only content-quality checks as manual items
3. **Reduce guard tokens** to ~15 core tokens, grouping related failures
4. **Make review dimensions tier-aware**: SIMPLE stories get 5 key dimensions, STANDARD gets 10, COMPLEX gets all 14
5. **Eliminate the AI slop checklist** as a separate entity -- merge its unique checks (hallucinated imports, generic names) into the tech debt checklist and the quality review
6. **Remove the lock.py stub** -- it serves no purpose
7. **Consolidate the world-class standard** from 31 principles to a smaller set of actionable rules that an LLM can consistently apply

---

## 12. Effectiveness Assessment

### What Would Actually Improve Code Quality

**High-Value Components:**

1. **TDD enforcement through handoff state machine**: Structurally requiring tests before code is the single most impactful quality mechanism. The `all_tests_red` / `all_tests_green` gates prevent the most common AI coding pattern (write code first, add tests later).

2. **Test Quality Gate (Gate 1)**: Catching bad tests before implementation is genuinely high-leverage. The behavioral assertion checks (no mock.called) target a real and common AI failure mode.

3. **P0 checks for timeouts, credentials, and unbounded operations**: These are the checks most likely to catch real production issues. A missing timeout can cause cascading failures; exposed credentials are security incidents.

4. **The Evidence Rule**: Requiring evidence for behavioral claims is simple, memorable, and genuinely useful.

5. **Hallucinated import detection**: LLMs do invent library names. This is a concrete, automatable check.

6. **Coverage thresholds**: While coverage percentage is an imperfect metric, it prevents the worst case (no tests at all).

**Medium-Value Components:**

7. **Plan quality review**: Catching issues before coding starts is theoretically highest-leverage, but depends on the quality of the LLM's planning ability.

8. **Gap report system**: Well-structured for machine-to-machine communication, enables automated fix loops.

9. **Story validation hooks**: Prevent malformed stories from entering the pipeline.

10. **Decision consolidation**: Building institutional memory across stories is genuinely useful for long projects.

**Low-Value Components (Mostly Ceremony):**

11. **14-dimension review for every story**: Most stories will not have concurrency issues, deployment concerns, or dependency problems. The framework does not adapt review scope to actual risk.

12. **152+ checklist items**: Diminishing returns. The most common issues are covered by the first 20-30 checks.

13. **Independent verification testing** (5+ tests): In theory excellent, in practice the LLM is generating both the code and the verification tests, reducing the independence. True verification would require a different model or human review.

14. **Design document 18-section requirement**: Appropriate for large features, crushing overhead for small ones.

15. **World-class standard (31 principles)**: Aspirational content that serves as good reference material but is too broad to consistently apply in automated review.

### The Fundamental Limitation

The entire quality system runs within LLM agent context. There is no external CI/CD enforcement. The agent is both the developer and the quality checker. This creates a structural weakness:

- The agent writes the tests, then checks if they are behavioral
- The agent writes the code, then checks its own code for issues
- The agent reports `all_tests_green: true` based on its own test execution

Using separate agent instances (forge-checker runs with fresh context from forge-developer) partially mitigates this, but both instances are the same model with the same biases. The subagent-driven-development skill addresses this with two-stage independent review (spec compliance then code quality), which is a step in the right direction.

### Overall Verdict

The quality infrastructure is **well-intentioned, grounded in real engineering principles, and contains several genuinely high-value components** (TDD enforcement, test quality gates, P0 checks, evidence rule). However, it is **over-engineered by approximately 2-3x** -- the volume of checklists, dimensions, principles, and guard tokens exceeds what an LLM can consistently apply. A streamlined version focusing on the top 30 most impactful checks, with tier-aware depth scaling, would likely produce equal or better results with significantly less overhead.

The quality system would benefit most from:
1. **Consolidation** of overlapping systems (forge-check + forge-quality)
2. **Tier-aware scaling** of review depth
3. **External validation** (actual CI running tests, not agent self-reporting)
4. **Focus on the 20% of checks that catch 80% of issues**

---

## Appendix: Key File Locations

| File | Path | Purpose |
|------|------|---------|
| Quality Skill | `.claude/skills/forge-quality/SKILL.md` | 14-dimension review skill definition |
| Quality Review Guide | `.claude/skills/forge-quality/quality-review.md` | CCR dimensions A-N, severity taxonomy, evidence rule |
| Quality Workflow | `.claude/skills/forge-quality/quality-workflow.md` | Full quality workflow template with all steps |
| Check Skill | `.claude/skills/forge-check/SKILL.md` | Checklist-based validation skill definition |
| AI Slop Checklist | `.claude/skills/forge-check/ai-slop-checklist.md` | 18 AI code quality checks |
| Design Checklist | `.claude/skills/forge-check/design-checklist.md` | 35 design document checks |
| Gap Report Format | `.claude/skills/forge-check/gap-report-format.md` | Gap report YAML schema |
| Lock Module | `.claude/skills/forge-check/lock.py` | No-op stub lock |
| Plan Quality Checklist | `.claude/skills/forge-check/plan-quality-checklist.md` | ~15 qualitative plan checks |
| Story Checklist | `.claude/skills/forge-check/story-checklist.md` | 47 story YAML checks |
| Tech Debt Checklist | `.claude/skills/forge-check/tech-debt-checklist.md` | 17 code quality checks |
| Test Quality Checklist | `.claude/skills/forge-check/test-quality-checklist.md` | 20 test quality checks |
| TDD Skill | `.claude/skills/forge-tdd/SKILL.md` | TDD workflow skill definition |
| TDD Workflow | `.claude/skills/forge-tdd/tdd-workflow.md` | Detailed TDD phases with handoff |
| Handoff Schema | `.claude/skills/forge-tdd/handoff-schema.md` | Handoff YAML v1.3.0 schema |
| Hotfix Template | `.claude/skills/forge-tdd/hotfix.md` | Reduced-ceremony hotfix workflow |
| Scaffold Template | `.claude/skills/forge-tdd/scaffold.md` | File stub generation |
| Quality Standards Rule | `.claude/rules/quality-standards.md` | P0-P3 severity taxonomy rule |
| TDD Workflow Rule | `.claude/rules/tdd-workflow.md` | Phase sequence enforcement rule |
| Story Validation Rule | `.claude/rules/story-validation.md` | Story schema validation rule |
| Checker Agent | `.claude/agents/forge-checker.md` | Read-only checker agent definition |
| Quality Agent | `.claude/agents/forge-quality.md` | Quality review agent definition |
| Test Engineer Agent | `.claude/agents/forge-test-engineer.md` | Test automation specialist agent |
| World-Class Standard | `.claude/skills/forge-reference/world-class-standard.md` | 31 engineering principles |
| Guard Tokens | `.claude/skills/forge-reference/guard-tokens.md` | 40+ guard token definitions |
| Practices Index | `.claude/skills/forge-reference/practices-index.yml` | Scope-to-practice mapping |
| Story Alignment Hook | `.claude/hooks/validate-story-alignment.sh` | PreToolUse file scope check |
| Story Validation Hook | `.claude/hooks/validate-story.py` | PreToolUse story schema validation |
| P0 Check Hook | `.claude/hooks/check-p0-findings.py` | Stop hook blocking on P0 findings |
| SDD Skill | `.claude/skills/subagent-driven-development/SKILL.md` | Subagent dispatch workflow |
| Code Quality Reviewer | `.claude/skills/subagent-driven-development/code-quality-reviewer-prompt.md` | Code review prompt template |
| Spec Reviewer | `.claude/skills/subagent-driven-development/spec-reviewer-prompt.md` | Spec compliance prompt template |
