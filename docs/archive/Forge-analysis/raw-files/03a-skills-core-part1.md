# Forge Core Skills Analysis (Part 1): forge-analyze, forge-check, forge-design, forge-plan

---

## 1. forge-analyze

### Purpose

Performs comprehensive 13-phase codebase analysis for brownfield (existing) projects. It generates structured YAML artifacts describing a codebase's architecture, domain model, conventions, tech debt, and more. These artifacts are consumed by downstream skills (forge-design, forge-plan, forge-develop).

**Trigger**: Not user-invocable directly (`user-invocable: false`). Invoked internally by the orchestrator or referenced in instructions as `/forge analyze`.

### Sub-components

| File | Role |
|------|------|
| `SKILL.md` | Skill manifest and overview. Lists all 13 phases (0-12), their output files, and the directory structure under `forge/.analysis/`. References phase templates in a `phases/` subdirectory (not included in the files provided). |
| `analysis-orchestrator.md` | The core execution engine. A 600-line document defining the stateful, resumable phase-execution protocol. Manages manifest (`_manifest.yml`), dependency checking between phases, context loading (summaries only for token efficiency), and error handling. |
| `analysis-finalize.md` | Phase 11 instructions. Validates all artifacts exist and have summaries, generates SHA-256 checksums for incremental refresh, updates `forge/memory/project.yml`, finalizes the manifest, and outputs a summary report to the user. |
| `analyze-codebase.md` | A **deprecation redirect**. States that the old single-template analysis (v1.1.1) has been superseded by the 13-phase system. Serves as migration documentation from v1 to v2. |

### Invocation Flow

1. Check if `forge/.analysis/_manifest.yml` exists.
2. If not, create directory and initialize manifest with all 13 phases as `pending`.
3. Run Phase 0: Python AST static analysis (`static_analysis.py`) -- zero LLM tokens.
4. For each subsequent phase (1-12):
   - Check manifest status (skip `completed`, restart `in_progress`).
   - Verify dependency phases are completed and artifact files exist.
   - Load only `summary:` sections from dependency artifacts (~200-400 tokens each).
   - Mark phase `in_progress`, execute phase template, write artifact YAML, verify output, mark `completed`.
   - Report progress to user after each phase.
5. Phase 11 (finalize): checksums, project memory update, manifest finalization.
6. Phase 12: Examples index from detected patterns.

**Resume scenarios** are explicitly handled: fresh start, partial completion, interrupted mid-phase, and already-complete.

### Dependencies

- References `forge/scripts/static_analysis.py` (Python AST analyzer)
- References phase template files at `forge/templates/analyze/` (00-static.md through 12-examples.md)
- Writes to `forge/.analysis/` and `forge/memory/project.yml`
- Downstream consumers: forge-design, forge-plan, forge-develop

### Key Instructions and Logic

The orchestrator enforces strict rules:

> "ALWAYS read `forge/.analysis/_manifest.yml` first (if it exists)"
> "NEVER re-run a completed phase (unless manifest is corrupted)"
> "CRITICAL FOR CONTEXT WINDOW MANAGEMENT: load ONLY the summary: section (~200-400 tokens each)"

Phase dependencies form a DAG:
- `overview` depends on `static`
- `structure` depends on `overview` + `static`
- `data_flows` depends on `domain_model` + `entry_points` + `static`
- `finalize` depends on ALL phases
- `examples` depends on `static` + `finalize`

Constraints: read-only (no source modification), ~200k tokens per phase max, sequential one-at-a-time execution, atomic phase completion.

### Complexity Assessment

**Over-engineered.** The 13-phase system with manifest tracking, checksums for incremental refresh, resumability, and token budgeting is ambitious. For a Claude Code framework running in a single session, the resumability logic (4 distinct scenarios) adds significant complexity. The incremental refresh via checksums (documented in finalize.md as "Future Runs") is spec'd but likely never exercised. The `analyze-codebase.md` file is pure dead weight -- a migration notice for a version transition nobody outside the framework author would encounter.

---

## 2. forge-check

### Purpose

Quality review and validation skill. Provides structured checklists and gate logic for validating plans, tests, code, stories, and design documents at different stages of the TDD workflow. Produces findings with P0-P3 severity and PASS/WARNING/BLOCKED verdicts.

**Trigger**: Not user-invocable (`user-invocable: false`). Invoked by the `forge-checker` agent at specific workflow gates.

### Sub-components

| File | Role |
|------|------|
| `SKILL.md` | Master document. Defines 5 quality review domains (plan quality, test quality, tech debt, AI slop, artifact validation), 3 quality gates in the TDD workflow, severity taxonomy (P0-P3), verdict meanings, output file schemas (findings.yml, gap_report.yml), and integration pseudocode with the orchestrator. |
| `plan-quality-checklist.md` | 13 checks across 5 categories for validating implementation plans. Uses a "principal engineer mindset" with qualitative questions rather than checkboxes. Outputs top 3-5 critical gaps. Only for STANDARD/COMPLEX tiers. Max 1 fix loop. |
| `test-quality-checklist.md` | 20 checks across 5 categories (behavioral focus, coverage, anti-patterns, structure, independence). Validates tests are behavioral and comprehensive before implementation begins. Blocks GREEN phase if P0 > 0 or P1 > 2. |
| `tech-debt-checklist.md` | 17 checks across 7 categories (reliability, error handling, complexity, duplication, coupling, dead code, SATD). Focuses on production reliability risks (timeouts, credentials, exception swallowing). |
| `ai-slop-checklist.md` | 18 checks across 7 categories detecting low-quality AI-generated code: hallucinated imports, generic naming, over-commenting, missing type hints, generic error messages, god functions. |
| `design-checklist.md` | 35 checks validating design documents across structure (5), standard sections (10), world-class sections (8), content quality (7), and completeness (5). Verifies all 18 required design sections exist and have substantive content. |
| `story-checklist.md` | 47 checks validating story YAML files across 13 categories (identity, files, interfaces, acceptance criteria, IO examples, error handling, tests, invariants, failure modes, edge cases, feature flags, risk, metadata). |
| `gap-report-format.md` | Schema specification for gap reports (gap_report.yml). Defines the full YAML structure including gap categories (schema, content, reference, structure, consistency, completeness), severity levels, fix guidance best practices, check history tracking, and escalation triggers. |
| `lock.py` | A stub no-op lock (8 lines). A context manager that yields immediately. Exists for validation scripts that might need concurrency control in the future. |

### Invocation Flow

Three quality gates in the TDD workflow:

1. **Gate 0 (Plan Quality)**: After PLAN phase, before RED. STANDARD/COMPLEX only. Checker runs plan-quality-checklist. If HIGH gaps found, 1 fix loop back to planner, then proceed regardless.
2. **Gate 1 (Test Quality)**: After RED phase, before GREEN. Runs test-quality-checklist. P0 > 0 or P1 > 2 blocks GREEN. Up to 3 fix loops.
3. **Gate 2 (Code Quality)**: After GREEN phase. Runs tech-debt + AI-slop checklists in parallel. P0 > 0 or P1 > 2 blocks. Up to 3 fix loops.

Additionally, artifact validation (stories, designs) runs pre-TDD using story-checklist and design-checklist.

### Dependencies

- Invoked by `forge-checker` agent
- Integration pseudocode references `forge-developer` agent for fix loops
- References Python scripts: `check_plan_quality.py`, `check_test_quality.py`, `check_tech_debt.py`, `check_ai_slop.py`, `validate_stories.py`, `validate_design.py`
- References `forge-reference/world-class-standard.md` for P1-P20 principles
- Reads story files from `forge/stories/` and design docs from `forge/docs/designs/`
- Writes findings to `forge/.tmp/check/{artifact_id}/`

### Key Instructions and Logic

The SKILL.md defines the gate logic concisely:

```
Gate 0: HIGH impact gaps > 0 -> NEEDS_IMPROVEMENT (1 fix loop)
Gate 1: P0 > 0 -> BLOCKED; P1 > 2 -> BLOCKED
Gate 2: P0 > 0 -> BLOCKED; P1 > 2 -> BLOCKED
```

The plan-quality-checklist has a distinct philosophy:

> "This is NOT checkbox validation - it's principal-engineer critical thinking that asks 'What would make this plan dramatically better?'"
> "Do NOT produce a laundry list. Produce 3-5 high-impact improvements."

The gap-report-format defines escalation:

> "Escalate to user when: check_attempt >= max_attempts, gap_count_unchanged for 2 attempts, requires_user_decision > 0"

### Complexity Assessment

**Appropriately comprehensive but verbose.** The 6 checklists totaling 150+ checks are thorough. The separation of concerns (plan vs. test vs. code quality) is sound. However, the sheer volume of checks (47 for stories alone) means this skill is doing the work of what should be multiple focused validation tools. The `lock.py` stub is premature abstraction. The overlap between tech-debt-checklist and ai-slop-checklist (both check timeouts on external calls, both check error handling quality) creates redundancy. The gap-report-format.md is well-designed as a contract specification.

---

## 3. forge-design

### Purpose

Creates comprehensive 18-section design documents from PRD/Architecture docs (greenfield) or codebase analysis artifacts (brownfield). Performs gap analysis first to identify missing requirements, then generates the design document.

**Trigger**: Not user-invocable (`user-invocable: false`). Invoked as `/forge design <feature>`.

### Sub-components

| File | Role |
|------|------|
| `SKILL.md` | Skill manifest. Lists the 3-step process (gap analysis, clarifying questions, design document), all 18 sections (10 standard + 8 world-class), brownfield support details, and output paths. |
| `design-template.md` | The main template (~600 lines). Defines: input detection (greenfield vs. brownfield with manifest-first validation), gap analysis with 10 gap categories (4 general + 6 brownfield-specific), all 18 design sections with schemas and examples, and a quality checklist. Heavy on brownfield artifact mapping -- a table maps each analysis artifact to design sections. |
| `gap-analysis.md` | A Handlebars-style template for design questions. Defines the structure for Critical/Important/Nice-to-Have questions with placeholders for topic, gap, impact, options, and defaults. Short file (66 lines) that is essentially a template fragment. |

### Invocation Flow

1. **Input Detection**: Check for `_manifest.yml` (brownfield) or PRD+Architecture (greenfield). Error if neither.
2. **Brownfield Validation**: Manifest-first -- verify all 11 phases show `status: completed`. Then secondary validation that artifact files exist (defense in depth). Error messages suggest running `/forge analyze` if incomplete.
3. **Gap Analysis**: Analyze inputs for 10 categories of gaps (missing requirements, undefined behaviors, technical gaps, conflicts, plus 6 brownfield-specific: pattern alignment, domain model extension, entry point integration, critical path impact, tech debt awareness, data flow integration).
4. **If gaps found**: Return `GAPS_FOUND` with structured questions to orchestrator. Orchestrator asks user via `AskUserQuestion` tool. Resume with answers.
5. **Design Generation**: Create 18-section markdown document at `forge/docs/designs/{feature-slug}.md`.

### Dependencies

- Requires either `forge/.analysis/` artifacts (all 11+ files) or `forge/docs/PRD.md` + `forge/docs/Architecture.md`
- References `world-class-standard.md` for P1-P20 principles
- The gap-analysis.md template uses Handlebars syntax (`{{#each}}`, `{{@index}}`)
- Outputs consumed by forge-plan (story derivation)
- Interactive: uses `AskUserQuestion` tool via orchestrator for gap resolution

### Key Instructions and Logic

The design-template.md enforces manifest-first validation:

> "The _manifest.yml is the **source of truth** for analysis completion. File existence alone is insufficient - a file may exist but be incomplete due to interrupted analysis."

Brownfield artifact mapping is detailed:

> "static.yml: USE FIRST: Get accurate dependency graph, call graph, type hierarchy. Never guess imports -- static.yml is 100% accurate from AST"
> "examples.yml: COPY PATTERNS: When creating new services/repos/endpoints, copy the canonical snippet."

The 18 sections are organized as 10 "standard" + 8 "world-class" (mapping to principles P2, P7, P8, P11, P12, P13, P18).

### Complexity Assessment

**Appropriately scoped but front-loaded.** The 18-section design document is thorough and well-structured. The gap analysis with 10 categories is valuable. However, the brownfield validation logic (manifest check + file existence check + error messages with recovery instructions) adds substantial conditional complexity. The design-template.md is doing double duty as both instructions and reference material. The gap-analysis.md file is underweight -- just a Handlebars template that could be inlined.

---

## 4. forge-plan

### Purpose

Derives user stories from design documents. Enforces a "single-scope rule" (each story has exactly one scope), assigns complexity tiers (SIMPLE/STANDARD/COMPLEX), generates story YAML files with 90-95% implementation detail, and organizes stories into sprints.

**Trigger**: Not user-invocable (`user-invocable: false`). Invoked as `/forge plan <feature>`.

### Sub-components

| File | Role |
|------|------|
| `SKILL.md` | Skill manifest. Defines the planning process (5 steps), single-scope rule with 10 valid scopes, 3 story tiers with field counts, and lists sub-templates. |
| `story-derivation.md` | The core planning template (~650 lines). Maps design doc sections to story fields (18 mappings). Defines the single-scope rule, size limits (max 10 points, max 3 files), completeness requirements, sprint planning algorithm, post-creation design doc status update, quality checklist (30+ items), and 9 guard conditions. For brownfield, requires loading static.yml and examples.yml first. |
| `story-schema.md` | Complete story YAML schema (~1060 lines). Defines all fields with a full worked example (email validator). Documents 3 tiers (SIMPLE: 8 fields, STANDARD: 16, COMPLEX: 20+), auto-detection logic, feature flag enforcement triggers, enforced field requirements (test references in invariants/failure_modes/edge_cases), conditional fields, and the 10-category edge case matrix. |
| `enrich.md` | Story enrichment from external inputs (~420 lines). Handles 4 input types: natural language, existing story, external document, interactive mode. Defines a 6-question clarification flow (scope, interfaces, error handling, happy path, edge cases, priority). Brownfield-aware -- uses analysis artifacts to skip obvious questions. |
| `quick-story.md` | SIMPLE-tier story creation (~165 lines). Auto-infers scope from keywords, auto-infers target file from description. Generates a minimal 8-field story. Has rejection criteria (rejects if description mentions security, payment, auth, etc.) and redirects to full `/forge enrich`. |
| `retroactive-story.md` | Creates SIMPLE-tier stories from completed hotfix commits (~220 lines). Always SIMPLE tier. Auto-infers scope from commit subject keywords. Extracts file info from git diff. Validates commit exists and no duplicate story. Updates project memory. Marked "DO NOT MODIFY - This is an audit record." |

### Invocation Flow

**Primary flow (story-derivation.md)**:
1. Load design document from `forge/docs/designs/`.
2. Load prior decisions from `forge/memory/important_decisions.yml`.
3. For brownfield: load static.yml and examples.yml first for accurate dependency/pattern info.
4. Extract story fields from design doc sections (18 mapping rules).
5. Apply single-scope rule -- split multi-scope features into multiple stories.
6. Apply size limits (max 10 points, max 3 files).
7. Self-validate: io_examples has error case, all test references resolve, scaffolds valid.
8. Assign tiers (auto-detection from points/risk/scope).
9. Sprint planning: sort by dependencies/priority/scope order, assign to sprints respecting velocity target.
10. Update `forge/memory/project.yml` with sprint assignments.
11. Update design doc status to APPROVED with story list.

**Alternative flows**:
- `enrich`: Interactive story creation from natural language or external docs.
- `quick-story`: Fast path for trivial changes.
- `retroactive-story`: Audit trail for hotfixes already committed.

### Dependencies

- Requires design document from forge-design
- Reads `forge/profiles/universal.yml` for scope definitions
- For brownfield: requires `forge/.analysis/` artifacts (static.yml, examples.yml, practices.yml, conventions.yml, structure.yml, domain-model.yml, entry-points.yml, data-flows.yml, critical-paths.yml, overview.yml, tech-debt.yml)
- Reads `forge/memory/important_decisions.yml` and `forge/memory/project.yml`
- Outputs consumed by forge-develop (implementation) and forge-check (validation)
- Writes stories to `forge/stories/ST-###.yml`

### Key Instructions and Logic

The single-scope rule is central:

> "Every story must have **exactly ONE** scope... If a feature spans multiple scopes -> create multiple single-scope stories."

Story completeness is emphasized:

> "Stories must contain everything needed for 90-95% automated code generation."

Three mandatory rules are called out in story-derivation.md:

> "Rule 1: io_examples MUST Include At Least One Error Case"
> "Rule 2: Test References MUST Point to Defined Tests"
> "Rule 3: Write Tests Section FIRST"

The tiered system reduces ceremony:

> "Match ceremony to complexity. Simple tasks need less overhead."

SIMPLE = 8 fields (bug fixes), STANDARD = 16 fields (normal features), COMPLEX = 20+ fields with mandatory feature flags (security, integrations, high-risk).

Sprint planning uses a greedy bin-packing algorithm sorted by dependencies, priority, and a fixed scope order (skeleton first, perf last).

### Complexity Assessment

**The most complex skill of the four, and somewhat over-engineered.** The story-schema.md alone is over 1000 lines -- essentially a complete specification document that LLM agents must internalize. The 3-tier system is sound in principle but the STANDARD tier already requires 16 fields with sub-structures (invariants, concurrency, determinism, resource_safety, edge_case_matrix), which is heavy for "normal feature development." The quick-story and retroactive-story templates are pragmatic additions that acknowledge the main schema's weight. The enrich.md template duplicates large portions of the story schema. Sprint planning logic (velocity targets, bin-packing) feels like scope creep for what should be a story generation tool.

---

## 5. Cross-Cutting Analysis

### 7. Common Patterns

All four skills share these architectural patterns:

1. **YAML-as-contract**: Every skill outputs structured YAML files to well-defined paths. These serve as inter-skill communication contracts (`forge/.analysis/*.yml`, `forge/stories/ST-###.yml`, `forge/docs/designs/*.md`).

2. **Brownfield-first thinking**: All skills have explicit brownfield support paths that load analysis artifacts. Each skill duplicates the "if analysis exists, load these artifacts" pattern with similar tables mapping artifacts to usage.

3. **Progressive validation**: Multi-stage validation before execution (check manifest -> check phase statuses -> check file existence -> check content).

4. **Guard conditions**: All skills define explicit "stop and report" conditions (MISSING_DESIGN_DOC, SCOPE_VIOLATION, ANALYSIS_INCOMPLETE, etc.).

5. **Template-driven execution**: Each skill contains one or more markdown templates that serve as detailed step-by-step instructions for the LLM agent. The LLM is expected to follow these instructions to produce artifacts.

6. **Severity/priority taxonomies**: forge-check uses P0-P3, forge-plan uses SIMPLE/STANDARD/COMPLEX tiers, forge-analyze uses phases. Each has its own classification system with thresholds and gates.

7. **World-Class Standard references**: forge-check, forge-design, and forge-plan all reference principles P1-P20 from `world-class-standard.md`, particularly P2 (failure), P7 (state ownership), P8 (invariants), P11 (determinism), P12 (resource safety), P13 (concurrency), P18 (tradeoffs).

8. **Version tracking**: Skills embed version numbers (v1.1.1, v1.2.0, v2.1.0, v2.2.0) in their templates and output schemas, with version history documentation.

### 8. Overlap

| Overlap Area | Skills Involved | Nature |
|---|---|---|
| **Brownfield artifact loading** | analyze, design, plan | All three define tables mapping analysis artifacts to their usage. The mapping logic is repeated in each skill rather than centralized. |
| **Error handling / failure modes** | check (tech-debt + ai-slop), design (sections 2, 11), plan (story schema failure_modes + error_handling) | Error taxonomy appears in design, is transferred to stories by plan, and is validated by check. The concepts are consistent but the check skill validates the same error patterns (timeouts, missing validation) in two separate checklists (tech-debt and ai-slop). |
| **Invariants** | check (story-checklist), design (sections 5, 12), plan (story schema invariants) | Invariants flow from design through stories to validation. Conceptually clean pipeline, but each skill re-documents what invariants are. |
| **Edge case matrix** | check (story-checklist CHK-ECM-*), design (section 17), plan (story schema edge_case_matrix) | Same 10-category matrix appears in all three. |
| **Test quality** | check (test-quality-checklist + ai-slop testing category), plan (story tests section) | The check skill validates tests, while plan generates test specifications. The ai-slop checklist has a "Testing Quality" category (2 checks) that overlaps with the dedicated test-quality-checklist (20 checks). |
| **Tech debt analysis** | analyze (phase 8 tech-debt), check (tech-debt-checklist) | forge-analyze detects existing tech debt in the codebase; forge-check validates that new code does not introduce tech debt. Different purposes but same domain terminology. |

### 9. Naming

**Consistency**: The `forge-` prefix is consistent. The verb-based naming (analyze, check, design, plan) is logical and follows a natural workflow order: analyze -> design -> plan -> (develop) -> check.

**Issues**:

1. **SKILL.md vs. sub-files**: The convention of SKILL.md as the manifest is consistent across all four skills. Good.

2. **Template naming is inconsistent**: forge-analyze uses numbered phases (`00-static.md`, `01-overview.md`). forge-plan uses descriptive names (`story-derivation.md`, `enrich.md`). forge-check uses `{domain}-checklist.md`. forge-design uses `design-template.md` and `gap-analysis.md`. No uniform convention.

3. **"analysis" overload**: `forge-analyze` produces "analysis" artifacts, but `gap-analysis.md` lives under forge-design and is a completely different concept. The word "analysis" is used for both codebase analysis and gap analysis.

4. **Checklist vs. template**: forge-check files are called "checklists" while forge-plan and forge-design files are called "templates." This distinction is meaningful and consistent within each skill.

5. **The `analyze-codebase.md` file** is named as if it were the main analysis template but is actually just a deprecation notice. It should be named `_deprecated-v1.md` or removed entirely.

6. **`lock.py`** is an outlier -- the only Python file among the skill definition files (other Python scripts are referenced but live in `scripts/` directories). Its presence in the skill directory alongside markdown files is unexpected.

7. **Scope names in forge-plan** (skeleton, validation, diff, data, response, integration, observability, coverage, perf, security) are mostly clear, but "diff" is unintuitive for "business logic, state changes, transformations."
