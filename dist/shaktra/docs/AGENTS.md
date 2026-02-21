# Shaktra Agent Architecture

Shaktra orchestrates 14 specialized sub-agents, each with a defined role, strict input/output contracts, and read/write boundaries. No agent operates independently -- all are spawned by skill orchestrators (`/shaktra:tpm`, `/shaktra:dev`, `/shaktra:review`, `/shaktra:adversarial-review`, `/shaktra:analyze`, `/shaktra:bugfix`, `/shaktra:general`).

## Model Allocation

| Model | Agents | Rationale |
|-------|--------|-----------|
| Opus | architect, sw-engineer, test-agent, developer, cba-analyzer, cr-analyzer, bug-diagnostician, adversary | Design, planning, code generation, deep analysis, and adversarial probing require highest capability |
| Sonnet | tpm-quality, scrummaster, product-manager, sw-quality, memory-retriever | Structured review, story creation, checklist-driven work, and memory retrieval |
| Haiku | memory-curator | Lightweight extraction and append-only writes |

## Planning Agents

### Architect

**Role:** Create design documents from PRD and architecture inputs. Identify gaps before they propagate to stories.

**Invoked by:** `/shaktra:tpm` during the design workflow.

**Produces:** Design document at `.shaktra/designs/` or a `GAPS_FOUND` structured gap list for PM resolution.

**Key behaviors:** Reads PRD, architecture doc, settings, decisions, and lessons. Performs gap analysis across four sources before escalating. Scales document depth by story tier (Medium vs Large). Validates pattern alignment with the project's declared architecture style.

### Product Manager

**Role:** Bridge business requirements and engineering reality across multiple modes: gap answering, RICE prioritization, requirement coverage, brainstorming, PRD creation/review, research analysis, persona and journey creation.

**Invoked by:** `/shaktra:tpm` for gap resolution, RICE scoring, coverage checks, and product discovery workflows.

**Produces:** Gap answers with decision logging, RICE-scored story rankings, coverage reports, brainstorm docs, PRDs, research synthesis, personas, and journey maps.

**Key behaviors:** Exhausts all sources (PRD, architecture, principles, memory stores) before escalating to the user. Logs observations for consolidation by the Memory Curator. Uses concrete numbers -- never "roughly medium."

### Scrum Master

**Role:** Create implementation-ready stories from design docs, enrich sparse stories, and manage sprint allocation and closure.

**Invoked by:** `/shaktra:tpm` for story creation, enrichment, sprint planning, and sprint closure.

**Produces:** Story YAML files at `.shaktra/stories/`, updated `sprints.yml` with velocity tracking and capacity planning.

**Key behaviors:** Follows test-first ordering (writes `test_specs` before dependent fields). Enforces single-scope-per-story and size limits (max 10 points, max 3 files). Manages sprint velocity with rolling 3-sprint averages and trend adjustments.

### TPM Quality

**Role:** Review TPM artifacts (design docs and stories) for quality and completeness. Read-only inspector.

**Invoked by:** `/shaktra:tpm` after architect produces a design or scrum master produces stories.

**Produces:** One-line verdict (`QUALITY_PASS: <id>` or `QUALITY_BLOCKED: <id>`). When blocked, writes structured findings (severity, check ID, issue, guidance) to a `.quality.yml` file alongside the reviewed artifact — findings are never returned to the TPM orchestrator.

**Key behaviors:** Applies different checklists for design review (12 checks) vs story review (10 checks). Gates on severity -- any P0 blocks, P1 count checked against threshold. Never modifies reviewed artifacts. Writes findings to `.shaktra/stories/ST-NNN.quality.yml` or `.shaktra/designs/{name}-design.quality.yml` for fix agents to consume.

## Implementation Agents (TDD Pipeline)

### SW Engineer

**Role:** Create unified implementation + test plans during the PLAN phase. Plans only -- never writes code.

**Invoked by:** `/shaktra:dev` at the PLAN phase of the TDD pipeline.

**Produces:** `implementation_plan.md` in the story directory and populated `handoff.yml` with plan summary (components, test plan, implementation order, patterns, risks).

**Key behaviors:** Maps every acceptance criterion to a planned test. Defines component structure following SRP. Orders implementation to minimize coupling. Identifies patterns from three sources: established decisions, detected codebase patterns, and quality principles.

### Test Agent

**Role:** Write failing tests during the RED phase. Tests must fail because production code does not exist yet.

**Invoked by:** `/shaktra:dev` at the RED phase of the TDD pipeline.

**Produces:** Test files in the project's test directory. Updated `handoff.yml` with test summary. Emits `TESTS_NOT_RED` if tests are broken rather than properly red.

**Key behaviors:** Uses exact test names from the plan. Follows AAA pattern with behavioral assertions. Mocks only at boundaries. Ensures at least 30% negative tests. Validates failure reasons -- distinguishes valid failures (ImportError, ModuleNotFoundError) from invalid ones (SyntaxError, TypeError).

### Developer

**Role:** Implement production code during the GREEN phase and create feature branches. Makes failing tests pass.

**Invoked by:** `/shaktra:dev` at the GREEN phase (and for branch creation at the start of implementation).

**Produces:** Production code passing all tests, coverage report, staged files (never commits). Updated `handoff.yml` with code summary. Emits `TESTS_NOT_GREEN` or `COVERAGE_GATE_FAILED` on failure.

**Key behaviors:** Follows implementation order from the plan exactly. Applies all patterns from `patterns_applied`. Checks coverage against tier-specific thresholds from settings. Captures observations for consolidation via memory-curator.

### SW Quality

**Role:** Review artifacts at every quality gate during the TDD pipeline. Read-only inspector across four modes: PLAN_REVIEW, QUICK_CHECK, COMPREHENSIVE, and REFACTOR_VERIFY.

**Invoked by:** `/shaktra:dev` after each TDD phase (plan, test, code) and during comprehensive review. Also invoked by the refactoring pipeline.

**Produces:** Structured findings with evidence, gate results (`CHECK_PASSED`, `CHECK_BLOCKED`, `QUALITY_PASS`, `QUALITY_BLOCKED`, `REFACTOR_PASS`, `REFACTOR_BLOCKED`).

**Key behaviors:** Applies 36+ checks from quick-check plus specialized checks (performance, security, architecture). Enforces check depth by tier -- Trivial/Small get lighter enforcement than Medium/Large. Every finding requires evidence; opinions without evidence are dropped.

## Analysis Agents

### CBA Analyzer

**Role:** Execute a single codebase analysis dimension (D1-D9) assigned by the `/shaktra:analyze` orchestrator.

**Invoked by:** `/shaktra:analyze` -- one instance per dimension, run in parallel.

**Produces:** Structured YAML artifact at `.shaktra/analysis/` with self-contained summary and evidence-dense findings.

**Key behaviors:** Reads ground truth from `static.yml` before analyzing. Uses tools aggressively (Glob, Grep, Read, Bash) to explore the codebase. Every finding cites specific file, line, or code pattern. No hallucinated paths -- all referenced files must exist.

### CR Analyzer

**Role:** Execute quality dimension review at the application level during code review.

**Invoked by:** `/shaktra:review` -- receives a subset of dimensions (A-M) to review in parallel groups.

**Produces:** Findings with severity, evidence, and guidance. Structured reviewer deliverable tables per dimension (e.g., Contract Analysis, Failure Mode Analysis).

**Key behaviors:** Reviews changed code in context of surrounding application code -- never in isolation. Every dimension produces a deliverable table. Cross-references analysis artifacts (structure, practices, critical paths) when available. Findings without concrete fix actions are dropped.

## Specialized Agents

### Bug Diagnostician

**Role:** Investigate bugs using a structured 5-step methodology. Diagnoses only -- never fixes.

**Invoked by:** `/shaktra:bugfix` during the investigation phase.

**Produces:** Diagnosis artifact at `.shaktra/stories/diagnosis-{bug_id}.yml`, remediation story YAML, and blast radius summary with recommended additional stories. Emits `DIAGNOSIS_COMPLETE` or `DIAGNOSIS_BLOCKED`.

**Key behaviors:** Classifies bugs by symptom type and reproducibility. Generates at least 2 hypotheses before gathering evidence. Confirms root cause with three criteria (WHY, WHEN, PROOF). Searches for similar patterns across the codebase for blast radius assessment.

### Memory Curator

**Role:** Extract lessons learned from completed workflows and maintain institutional memory.

**Invoked by:** Every workflow at completion (`/shaktra:tpm`, `/shaktra:dev`, `/shaktra:review`, `/shaktra:adversarial-review`, `/shaktra:bugfix`, `/shaktra:analyze`, `/shaktra:general`).

**Produces:** Updated `.shaktra/memory/principles.yml`, `anti-patterns.yml`, and `procedures.yml` by consolidating observations.

**Key behaviors:** Ruthlessly selective -- only consolidates insights that would materially change future workflow execution. No routine observations ("tests passed"). Reads from `observations.yml` and distributes consolidated knowledge into the appropriate memory store (principles, anti-patterns, or procedures). Each entry requires concrete, actionable guidance.

### Memory Retriever

**Role:** Generate context-relevant briefings from memory stores for agent consumption.

**Invoked by:** `/shaktra:dev`, `/shaktra:review`, `/shaktra:adversarial-review`, `/shaktra:bugfix` for Tier 2 and Tier 3 memory retrieval.

**Produces:** `.briefing.yml` in the story directory with filtered, relevance-scored memory entries.

**Key behaviors:** Operates in 3 modes — briefing (full retrieval), chunk (process a subset of entries), and consolidate (merge chunk results). Scores entries by role relevance, keyword match, and recency. Respects `settings.memory.max_briefing_entries` cap.

### Adversary

**Role:** Execute adversarial probes against code changes through mutation testing, adversarial input generation, and fault injection.

**Invoked by:** `/shaktra:adversarial-review` -- 3 instances spawned in parallel (mutation probes, input/boundary probes, fault/resilience probes).

**Produces:** Structured findings with execution evidence (test output, stack traces). Mutation results (killed/survived). Adversarial test files.

**Key behaviors:** Follows strict mutation safety protocol (apply one mutation → run tests → restore → verify restoration). Never leaves mutated code in place. Never modifies existing test files — only creates new adversarial tests. Every finding requires execution evidence. Respects `max_mutations_per_function` and `max_adversarial_tests` caps from settings.

## Orchestration Patterns

### Quality Gate Loop

Most workflows follow a produce-review-fix loop:

1. A **producing agent** creates an artifact (design doc, stories, code)
2. A **reviewing agent** inspects it (tpm-quality, sw-quality)
3. If blocked: the reviewer writes findings to a `.quality.yml` file; the producer reads and fixes from that file
4. Loop repeats until the gate passes or max iterations are reached

TPM quality reviews use **parallel batch processing** for stories — all reviews spawn in parallel per round, then all fixes spawn in parallel. File-based findings handoff (`.quality.yml`) keeps the TPM orchestrator's context lean (one-line verdicts only).

### TDD Pipeline Handoff

The `/shaktra:dev` workflow chains four agents through a shared `handoff.yml` state file:

1. **SW Engineer** (PLAN) -- writes plan summary to handoff
2. **Test Agent** (RED) -- reads plan, writes test summary to handoff
3. **Developer** (GREEN) -- reads plan + tests, writes code summary to handoff
4. **SW Quality** reviews at each gate transition

Each agent reads the prior agent's handoff section and writes its own. The handoff file is the single source of truth for pipeline state.

### Parallel Fan-Out

`/shaktra:analyze` spawns up to 9 CBA Analyzer instances in parallel (one per dimension). `/shaktra:review` spawns CR Analyzer instances in parallel groups. `/shaktra:adversarial-review` spawns 3 Adversary instances in parallel (mutation, input/boundary, fault/resilience). This pattern maximizes throughput for independent analysis work.

### Memory Capture

Every workflow ends with a Memory Curator invocation. This is the only agent that runs in every workflow, ensuring institutional knowledge accumulates across the project lifecycle.
