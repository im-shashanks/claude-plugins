# TPM Workflow

The Technical Program Manager (`/shaktra:tpm`) is the entry point for all planning work in Shaktra. It orchestrates design doc creation, user story generation, quality review loops, RICE prioritization, and sprint planning through a coordinated sequence of specialized agents.

## When to Use

- Starting a new feature or epic
- Creating a design document for an architectural change
- Breaking a design into implementable stories
- Planning or re-planning sprints
- Applying a quick hotfix with minimal ceremony

## Prerequisites

Before running `/shaktra:tpm`, ensure your project has been initialized:

- `.shaktra/settings.yml` -- created by `/shaktra:init` (required for all workflows)
- `.shaktra/prd.md` -- your product requirements document (required for Full and Design workflows)
- `.shaktra/architecture.md` -- your architecture overview (required for Full and Design workflows)

If the PRD is missing, run `/shaktra:pm prd` to create one interactively.

## Intent Classification

When you invoke `/shaktra:tpm`, it classifies your request into one of these intents:

| Intent | Example Triggers | Workflow |
|---|---|---|
| `full` | "plan this feature", "create stories for X" | Full: Design through Sprint |
| `design` | "create design doc", "architecture for X" | Design Only |
| `stories` | "break down into stories", "generate stories" | Stories Only |
| `enrich` | "enrich stories", "add test specs" | Enrich existing stories |
| `hotfix` | "hotfix", "quick fix", "trivial fix" | Fast-path single story |
| `sprint` | "plan sprint", "re-prioritize backlog" | Sprint planning |
| `close-sprint` | "close sprint", "end sprint" | Close current sprint |

## Full Workflow: Design, Stories, Sprint

The full workflow is the default path for new features. It proceeds through four phases, each with quality gates.

### Phase 1 -- Design

**Agent:** Architect (Opus)

1. TPM reads project context from `.shaktra/settings.yml` and memory files
2. Architect receives the PRD, architecture doc, and any prior analysis
3. Architect performs gap analysis -- if gaps are found, Product Manager answers from source docs
4. If PM cannot answer a gap, the question is escalated to you
5. Architect produces the design doc at `.shaktra/designs/{name}-design.md`
6. **Quality gate:** TPM Quality reviews the design (up to 3 iterations)

**Produces:** An approved design document covering acceptance criteria, architecture, API contracts, data models, and edge cases.

### Phase 2 -- Stories

**Agent:** Scrummaster (Sonnet)

1. Scrummaster receives the approved design doc
2. Stories are created as YAML files in `.shaktra/stories/` following the story schema
3. **Quality gate:** All stories are reviewed by TPM Quality in parallel (up to 3 rounds). Findings are written to `.quality.yml` files — the TPM only receives one-line verdicts to keep context lean. Fix agents read findings from disk.

**Produces:** A set of quality-reviewed user stories with IDs, story points, acceptance criteria, and test specifications.

### Phase 3 -- PM Analysis

**Agents:** Product Manager (Sonnet), then Scrummaster (Sonnet)

1. PM runs a coverage report -- maps every PRD requirement to stories
   - If coverage is below 100%, gaps are presented for your decision
2. PM scores all stories with RICE (Reach, Impact, Confidence, Effort)
   - Stories are classified as Quick Win, Big Bet, or Standard
3. If sprints are enabled, Scrummaster allocates stories to sprints respecting velocity and dependencies
4. Sprint goal is presented for your review

**Produces:** Coverage report, RICE-scored backlog, and `.shaktra/sprints.yml` with allocated sprints.

### Phase 4 -- Memory

**Agent:** Memory Curator (Sonnet)

1. Captures lessons learned from the planning session
2. Appends to `.shaktra/memory/lessons.yml`

This step runs automatically at the end of every workflow.

## Agent Sequence Diagram

```
You ──► /shaktra:tpm
            │
            ├─► Architect ──────────► Design Doc
            │       ▲                     │
            │       │ (gaps)              │
            │   Product Manager           ▼
            │                      TPM Quality ──► PASS/BLOCKED
            │                      (findings → .quality.yml)
            │                             │
            ├─► Scrummaster ─────► Stories (all created)
            │                             │
            │                      TPM Quality ──► PARALLEL review
            │                      (findings → .quality.yml per story)
            │                      one-line verdicts back to TPM
            │                             │
            ├─► Product Manager ──► Coverage + RICE
            │                             │
            ├─► Scrummaster ──────► Sprint Allocation
            │                             │
            └─► Memory Curator ───► Lessons Captured
```

## Quality Gates

Every artifact passes through TPM Quality review before proceeding:

- **Design docs** are checked for completeness, consistency with the PRD, and technical soundness
- **Stories** are reviewed in parallel batches -- all stories in one round, then all fixes in one round
- Reviews run up to 3 rounds -- findings are written to `.quality.yml` files (not returned to TPM), and fix agents read from those files
- P0 findings block progress unconditionally
- If 3 iterations exhaust without passing, findings are escalated to you for manual resolution

## Sub-Workflows

### Design Only

Runs Phase 1 (Design) and Phase 4 (Memory). Use this when you want a design doc without proceeding to stories -- for instance, during early exploration or architecture review.

### Stories Only

Requires an existing design doc in `.shaktra/designs/`. Runs Phases 2-4 (Stories, PM Analysis, Memory). Use this when the design is already approved and you want to proceed to implementation planning.

### Enrich

Adds detail to existing sparse stories. The Scrummaster enriches stories with test specifications, implementation notes, and edge cases while preserving existing content. Each enriched story passes quality review.

### Sprint Planning

Re-runs RICE prioritization and sprint allocation for existing stories. Use this to re-prioritize after scope changes, to plan the next sprint, or to rebalance after a sprint close.

### Close Sprint

Records velocity for the current sprint, moves incomplete stories to the backlog, and advances to the next sprint. Use this at the end of a sprint cycle.

### Hotfix

Fast path for trivial fixes. Produces a single Trivial-tier story YAML file and a single quality pass -- no retry loop, no RICE scoring, no sprint allocation. After confirmation, proceed directly to `/shaktra:dev` to implement.

## Example Sessions

### Planning a new feature

```
You: /shaktra:tpm
"We need to add OAuth 2.0 support to the API"

TPM classifies intent: full

Phase 1 output:
  Design doc: .shaktra/designs/oauth-design.md
  - Token handling architecture
  - Refresh flow with sliding expiry
  - Provider abstraction layer
  Quality: PASS (2 iterations)

Phase 2 output:
  Stories created:
    ST-001 (M): Implement OAuth provider integration (8 pts)
    ST-002 (M): Add token management and refresh logic (8 pts)
    ST-003 (S): Add login endpoint and UI (5 pts)
    ST-004 (S): Add tests for OAuth flows (5 pts)
  Quality: All PASS

Phase 3 output:
  Coverage: 100% (all PRD requirements mapped)
  RICE: ST-003 Quick Win, ST-001 Big Bet
  Sprint 1: ST-001, ST-003 (13 pts / 20 capacity)
  Sprint 2: ST-002, ST-004 (13 pts / 20 capacity)

Next step: /shaktra:dev ST-001
```

### Quick hotfix

```
You: /shaktra:tpm
"hotfix: fix the null pointer in UserService.getProfile when user has no avatar"

TPM classifies intent: hotfix

Output:
  Story: ST-010 (Trivial): Fix NPE in UserService.getProfile
  Quality: PASS

Next step: /shaktra:dev ST-010
```

### Re-prioritizing after scope change

```
You: /shaktra:tpm
"re-prioritize the backlog -- the OAuth feature is now lower priority than the caching work"

TPM classifies intent: sprint

Output:
  RICE scores updated
  Sprint reallocated: caching stories moved to Sprint 1
  OAuth stories moved to Sprint 2

Next step: /shaktra:dev ST-005
```

## Options and Flags

The TPM workflow behavior is driven by your project settings in `.shaktra/settings.yml`:

- **`sprints.enabled`** -- When false, RICE scoring still runs but sprint allocation is skipped
- **`default_velocity`** -- Story points per sprint, used for capacity planning
- **`sprint_duration_weeks`** -- Sprint length, affects allocation density
- **`project_type`** -- Influences story tier detection (greenfield vs brownfield)

## Error Recovery

- **Mid-workflow cancellation:** Artifacts already written to disk are valid intermediate state. Resume by running the appropriate sub-workflow (e.g., `/shaktra:tpm stories` after a completed design phase).
- **Agent failure:** The TPM retries a failed agent once. If the retry fails, it reports the error without proceeding.
- **Missing prerequisites:** The TPM checks for required files before starting and tells you exactly what is missing and how to create it.
