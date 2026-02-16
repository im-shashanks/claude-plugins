# State Files

The `.shaktra/` directory holds all project-level development state. It is created by `/shaktra:init` and read/written by agents throughout the workflow.

```
.shaktra/
  CLAUDE.md              # State documentation (helps Claude understand the directory)
  settings.yml           # Project configuration and quality thresholds
  sprints.yml            # Sprint tracking and velocity history
  stories/               # User story files (ST-001.yml, ST-002.yml, ...)
  designs/               # Design documents from architecture phase
  memory/
    decisions.yml        # Architectural decisions (append-only)
    lessons.yml          # Team learnings (append-only, max 100 entries)
  analysis/              # Brownfield analysis results (9 dimensions)
  templates/             # Artifact templates for stories, designs, etc.
```

---

## settings.yml

Project configuration and all threshold values. Nothing in the plugin is hardcoded -- every tunable value reads from this file.

**Created by:** `/shaktra:init` (copied from plugin templates, populated interactively)
**Updated by:** User (manual edits to adjust thresholds)

**Structure:**

| Section | Key fields | Purpose |
|---------|-----------|---------|
| `project` | name, type, language, architecture, test_framework | Project identity |
| `tdd` | coverage_threshold, hotfix/small/large thresholds | Coverage gates per story tier |
| `quality` | p1_threshold | Max P1 findings before merge block |
| `review` | verification_test_persistence, min_verification_tests | Code review behavior |
| `analysis` | summary_token_budget, incremental_refresh | Brownfield analysis tuning |
| `sprints` | enabled, velocity_tracking, sprint_duration_weeks, default_velocity | Sprint planning |
| `pm` | default_framework, quick_win/big_bet thresholds | Product management |
| `refactoring` | safety_threshold, structural_safety_threshold, max_characterization_tests | Refactoring safety gates |

**Lifecycle:** Created once at init. Rarely changes after that. Agents read it at the start of every workflow to determine thresholds and behavior.

---

## sprints.yml

Sprint planning state and velocity history.

**Created by:** `/shaktra:init` (empty template)
**Updated by:** Scrummaster agent during `/shaktra:tpm` planning

**Structure:**
- `current_sprint` -- Active sprint number (null until first planning session)
- `velocity_history` -- Array of completed sprint velocities for capacity forecasting
- `sprints` -- Array of sprint objects, each containing assigned stories, points committed, points completed, and status

**Lifecycle:** Initialized empty. Populated when TPM runs sprint planning. Updated as stories move through dev and review. Velocity history grows after each sprint closes.

---

## stories/

User story files, one per story. Named by ID: `ST-001.yml`, `ST-002.yml`, etc.

**Created by:** TPM skill during `/shaktra:tpm` planning
**Updated by:** Dev Manager (status transitions), SW Quality (findings), Code Reviewer (review results)

**Each story contains:**
- Metadata: ID, title, tier (XS/S/M/L), story points, status, sprint assignment
- Description and acceptance criteria
- File scope (which files the story may touch)
- TDD state (current phase in PLAN/RED/GREEN/QUALITY/MEMORY/COMPLETE)
- Findings from quality gates and reviews

**Lifecycle:** Created during planning with status `backlog`. Moves to `planned` when assigned to a sprint. Moves to `in-progress` when `/shaktra:dev` starts. Transitions through TDD states. Reaches `complete` after quality gates pass. The `validate-story-scope` hook uses the `files:` list to enforce scope during development.

---

## designs/

Design documents produced during architecture and planning phases.

**Created by:** Architect agent during `/shaktra:tpm`
**Updated by:** Rarely updated after creation; may be revised if scope changes

**Contains:** Architecture overviews, API contracts, data models, component designs, and edge case analysis. Each design maps to one or more stories.

**Lifecycle:** Created during TPM planning. Referenced by Dev Manager when implementing stories. Serves as the source of truth for what was agreed during design.

---

## memory/

Append-only logs that preserve project knowledge across conversations.

### decisions.yml

Architectural decisions made during development.

**Created by:** `/shaktra:init` (empty template)
**Updated by:** SW Quality agent during the MEMORY phase of TDD

**Entry format:** Each decision records a date, title, reasoning, and impact. Entries are never modified or deleted -- the log is append-only.

**Lifecycle:** Grows throughout the project. Consulted by agents before making architectural choices to avoid contradicting prior decisions.

### lessons.yml

Team learnings and retrospective insights.

**Created by:** `/shaktra:init` (empty template)
**Updated by:** Memory Curator agent during the MEMORY phase of TDD

**Entry format:** Each lesson records a date, title, context, and key takeaway. Capped at 100 entries to keep the file manageable.

**Lifecycle:** Grows during development. Agents read lessons to avoid repeating past mistakes and to apply proven patterns.

---

## analysis/

Brownfield codebase analysis results. Only populated for brownfield projects.

**Created by:** `/shaktra:analyze`
**Updated by:** Analyzer agents (CBA Analyzer) during analysis runs

**Contains:**
- `manifest.yml` -- Tracks analysis completion state across 9 dimensions (resumable)
- Dimension output files: `structure.yml`, `domain-model.yml`, `entry-points.yml`, `practices.yml`, `dependencies.yml`, `tech-debt.yml`, `data-flows.yml`, `critical-paths.yml`, `git-intelligence.yml`

**Lifecycle:** Created when `/shaktra:analyze` runs. The manifest tracks which dimensions are complete, enabling interrupted analyses to resume. Supports incremental refresh via checksums when `settings.analysis.incremental_refresh` is enabled. Results inform TPM planning and dev workflows for brownfield projects.

---

## templates/

Artifact templates used when creating new stories, designs, and other structured documents.

**Created by:** `/shaktra:init` (copied from plugin templates)
**Updated by:** User (customization for project-specific needs)

**Lifecycle:** Created once at init. Templates define the structure that agents follow when producing artifacts, ensuring consistency across the project.
