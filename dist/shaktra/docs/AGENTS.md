# Shaktra Agent Architecture

Shaktra orchestrates 15 specialized sub-agents, each with a defined role, strict input/output contracts, and read/write boundaries. No agent operates independently -- all are spawned by skill orchestrators (`/shaktra:tpm`, `/shaktra:dev`, `/shaktra:review`, `/shaktra:adversarial-review`, `/shaktra:analyze`, `/shaktra:bugfix`, `/shaktra:incident`, `/shaktra:general`).

## Model Allocation

| Model | Agents | Rationale |
|-------|--------|-----------|
| Opus | architect, sw-engineer, test-agent, developer, cba-analyzer, cr-analyzer, bug-diagnostician, adversary, incident-analyst | Design, planning, code generation, deep analysis, adversarial probing, and incident analysis require highest capability |
| Sonnet | tpm-quality, scrummaster, product-manager, sw-quality, memory-retriever, doc-writer | Structured review, story creation, checklist-driven work, memory retrieval, and document generation |
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

**Produces:** A structured verdict (pass/blocked) with every finding in-band — severity, check ID, issue, and fix guidance per the schema supplied at dispatch.

**Key behaviors:** Applies different checklists for design review (12 checks) vs story review (10 checks). Gates on severity -- any P0 blocks, P1 count checked against the threshold supplied at dispatch. Never modifies reviewed artifacts.

## Implementation Agents (TDD Pipeline)

### SW Engineer

**Role:** Create unified implementation + test plans during the PLAN phase. Plans only -- never writes code.

**Invoked by:** `/shaktra:dev` at the PLAN phase of the TDD pipeline.

**Produces:** `implementation_plan.md` in the story directory and populated `handoff.yml` with plan summary (components, test plan, implementation order, patterns, risks).

**Key behaviors:** Maps every acceptance criterion to a planned test. Defines component structure following SRP. Orders implementation to minimize coupling. Identifies patterns from three sources: established decisions, detected codebase patterns, and quality principles.

### Test Agent

**Role:** Write failing tests during the RED phase. Tests must fail because production code does not exist yet.

**Invoked by:** `/shaktra:dev` at the RED phase of the TDD pipeline.

**Produces:** Test files in the project's test directory. Updated `handoff.yml` with test summary. Reports each failing test with its reason and whether that reason is a valid RED cause.

**Key behaviors:** Uses exact test names from the plan. Follows AAA pattern with behavioral assertions. Mocks only at boundaries. Ensures at least 30% negative tests. Validates failure reasons -- distinguishes valid failures (ImportError, ModuleNotFoundError) from invalid ones (SyntaxError, TypeError).

### Developer

**Role:** Implement production code during the GREEN phase and create feature branches. Makes failing tests pass.

**Invoked by:** `/shaktra:dev` at the GREEN phase (and for branch creation at the start of implementation).

**Produces:** Production code passing all tests, coverage report, staged files (never commits). Updated `handoff.yml` with code summary. Reports actual test status and measured coverage — the workflow blocks on red tests or a missed threshold.

**Key behaviors:** Follows implementation order from the plan exactly. Applies all patterns from `patterns_applied`. Checks coverage against tier-specific thresholds from settings. Captures observations for consolidation via memory-curator.

### SW Quality

**Role:** Review artifacts at every quality gate during the TDD pipeline. Read-only inspector across four modes: PLAN_REVIEW, QUICK_CHECK, COMPREHENSIVE, and REFACTOR_VERIFY.

**Invoked by:** `/shaktra:dev` after each TDD phase (plan, test, code) and during comprehensive review. Also invoked by the refactoring pipeline.

**Produces:** Structured findings with evidence and a pass/blocked verdict per the schema supplied at dispatch (quick-check, comprehensive, and refactor-verify modes).

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

### Doc Writer

**Role:** Generate documents from Shaktra artifacts — annotatable HTML review docs (from the review-doc template) and user-facing documentation. Compression without loss; never invents content.

**Invoked by:** The `shaktra-html-review` skill (review-doc mode) and documentation tasks (user-doc mode).

**Produces:** Self-contained HTML review documents with annotatable sections and inline question widgets, or updated user docs, per the schema supplied at dispatch.

**Key behaviors:** Keeps the review template's style/script blocks byte-identical. Section and question ids stay meaningful when read back from annotations JSON. Flags source ambiguities instead of resolving them silently. Never edits the canonical artifact it renders.

### Bug Diagnostician

**Role:** Investigate bugs using a structured 5-step methodology. Diagnoses only -- never fixes.

**Invoked by:** `/shaktra:bugfix` during the investigation phase.

**Produces:** Diagnosis artifact at `.shaktra/stories/diagnosis-{bug_id}.yml`, remediation story YAML, and blast-radius observations with recommended additional stories, returned per the schema supplied at dispatch (confidence high/medium/low gates remediation).

**Key behaviors:** Classifies bugs by symptom type and reproducibility. Generates at least 2 hypotheses before gathering evidence. Confirms root cause with three criteria (WHY, WHEN, PROOF). Searches for similar patterns across the codebase for blast radius assessment.

### Memory Curator

**Role:** Extract lessons learned from completed workflows and maintain institutional memory.

**Invoked by:** Every workflow at completion (`/shaktra:tpm`, `/shaktra:dev`, `/shaktra:review`, `/shaktra:adversarial-review`, `/shaktra:bugfix`, `/shaktra:incident`, `/shaktra:analyze`, `/shaktra:general`).

**Produces:** Updated `.shaktra/memory/principles.yml`, `anti-patterns.yml`, and `procedures.yml` by consolidating observations.

**Key behaviors:** Ruthlessly selective -- only consolidates insights that would materially change future workflow execution. No routine observations ("tests passed"). Reads from `observations.yml` and distributes consolidated knowledge into the appropriate memory store (principles, anti-patterns, or procedures). Each entry requires concrete, actionable guidance.

### Memory Retriever

**Role:** Generate context-relevant briefings from memory stores for agent consumption.

**Invoked by:** `/shaktra:dev`, `/shaktra:review`, `/shaktra:adversarial-review`, `/shaktra:bugfix` for Tier 2 and Tier 3 memory retrieval.

**Produces:** An in-band briefing of filtered, relevance-scored memory entries (persisted to `handoff.briefing` by the orchestrator).

**Key behaviors:** Operates in 3 modes — briefing (full retrieval), chunk (process a subset of entries), and consolidate (merge chunk results). Scores entries by role relevance, keyword match, and recency. Respects `settings.memory.max_briefing_entries` cap.

### Incident Analyst

**Role:** Analyze completed bug diagnoses to produce blameless post-mortems, operational runbooks, and detection gap analyses.

**Invoked by:** `/shaktra:incident` for all three intents (post-mortem, runbook, detection gap).

**Produces:** Post-mortem artifact (timeline, root cause chain, impact, action items), runbook (identification, response, diagnosis shortcut, resolution), detection gap report (gate coverage matrix, test gaps, quality dimension gaps, recommendations). All artifacts written to `.shaktra/incidents/{bug_id}/`.

**Key behaviors:** Never re-investigates the bug — works from the diagnosis artifact as ground truth. Extends single-point root cause to a contributing factors chain. Maps root cause against all quality gates to identify detection gaps. Every finding requires evidence from diagnosis, handoff, or git history. Blameless analysis — focuses on systems and processes, never individuals.

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
3. If blocked: the quality loop dispatches the producer with the findings in its prompt
4. Loop repeats until the gate passes or max iterations are reached

TPM quality reviews run **per-story quality loops in parallel** inside `workflows/tpm-stories.js` — separate story files mean no write conflicts, and findings stay in-band.

### TDD Pipeline Handoff

The `/shaktra:dev` workflow chains four agents through a shared `handoff.yml` state file:

1. **SW Engineer** (PLAN) -- writes plan summary to handoff
2. **Test Agent** (RED) -- reads plan, writes test summary to handoff
3. **Developer** (GREEN) -- reads plan + tests, writes code summary to handoff
4. **SW Quality** reviews at each gate transition

Each agent reads the prior agent's handoff section and writes its own. The handoff file is the single source of truth for pipeline state.

### Parallel Fan-Out

`/shaktra:analyze` spawns up to 9 CBA Analyzer instances in parallel (one per dimension). `/shaktra:review` spawns CR Analyzer instances in parallel groups. `/shaktra:adversarial-review` spawns 3 Adversary instances in parallel (mutation, input/boundary, fault/resilience). `/shaktra:incident` dispatches a single Incident Analyst with the appropriate intent. This pattern maximizes throughput for independent analysis work.

### Memory Capture

Every workflow ends with a Memory Curator invocation. This is the only agent that runs in every workflow, ensuring institutional knowledge accumulates across the project lifecycle.
