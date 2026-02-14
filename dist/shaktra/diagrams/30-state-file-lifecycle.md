# 30. State File Lifecycle

Shaktra maintains project state across several YAML files in `.shaktra/`. Each file has a distinct lifecycle — created at a specific point, updated by specific workflows, and consumed by downstream agents. This diagram traces how state files evolve from project initialization through planning, development, and memory capture.

```mermaid
sequenceDiagram
    participant U as User
    participant INIT as /shaktra:init
    participant TPM as /shaktra:tpm
    participant DEV as /shaktra:dev
    participant REV as /shaktra:review
    participant MEM as Memory Curator

    Note over U,MEM: Phase 1 — Project Initialization
    U->>INIT: /shaktra:init
    INIT->>INIT: Create .shaktra/settings.yml
    INIT->>INIT: Create .shaktra/memory/ (empty)
    INIT->>INIT: Create .shaktra/stories/ (empty)

    Note over U,MEM: Phase 2 — Planning (TPM)
    U->>TPM: /shaktra:tpm
    TPM->>TPM: Read settings.yml
    TPM->>TPM: Architect writes .shaktra/designs/*.md
    TPM->>TPM: Scrummaster writes .shaktra/stories/*.yml
    TPM->>TPM: PM writes RICE scores to stories
    TPM->>TPM: Scrummaster writes .shaktra/sprints.yml
    TPM->>MEM: Capture planning lessons
    MEM->>MEM: Append to .shaktra/memory/lessons.yml

    Note over U,MEM: Phase 3 — Development (TDD Pipeline)
    U->>DEV: /shaktra:dev ST-001
    DEV->>DEV: Create .shaktra/stories/ST-001/handoff.yml
    DEV->>DEV: PLAN: populate plan_summary
    DEV->>DEV: RED: populate test_summary
    DEV->>DEV: GREEN: populate code_summary
    DEV->>DEV: QUALITY: populate quality_findings
    DEV->>DEV: QUALITY: promote decisions
    DEV->>DEV: Write to .shaktra/memory/decisions.yml
    DEV->>MEM: Capture development lessons
    MEM->>MEM: Append to .shaktra/memory/lessons.yml
    MEM->>DEV: Set memory_captured: true
    DEV->>DEV: Update story status to done
    DEV->>DEV: Update .shaktra/sprints.yml velocity

    Note over U,MEM: Phase 4 — Review
    U->>REV: /shaktra:review ST-001
    REV->>REV: Read handoff.yml + code changes
    REV->>REV: Produce review findings
    REV->>MEM: Capture review lessons
    MEM->>MEM: Append to .shaktra/memory/lessons.yml

    Note over U,MEM: Ongoing — Memory Growth
    Note right of MEM: lessons.yml: max 100 active<br/>Archive oldest to lessons-archive.yml<br/>decisions.yml: pattern coherence<br/>across all future stories
```

**Reading guide:**
- **Phase 1** creates the skeleton — `settings.yml` is the project-wide configuration that every workflow reads.
- **Phase 2** populates planning artifacts — designs, stories, sprints. The TPM workflow ends with memory capture.
- **Phase 3** is the TDD pipeline where `handoff.yml` accumulates state through each phase (plan, tests, code, quality). Decisions are promoted to `decisions.yml` for cross-story consistency. Sprint velocity updates after each story completes.
- **Phase 4** adds review-level insights to lessons.
- Memory files grow across all workflows. `lessons.yml` caps at 100 entries with archival. `decisions.yml` accumulates architectural patterns that influence all future stories.

**Source:** `dist/shaktra/skills/shaktra-reference/schemas/handoff-schema.md`, `dist/shaktra/skills/shaktra-tpm/workflow-template.md`, `dist/shaktra/skills/shaktra-dev/tdd-pipeline.md`
