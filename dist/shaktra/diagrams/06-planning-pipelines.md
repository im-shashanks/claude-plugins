# 6. Planning Pipelines (tpm-design.js, tpm-stories.js, pm-artifacts.js)

Product definition (`/shaktra:pm`) feeds planning (`/shaktra:tpm`). Interactive
triage happens in the main loop; artifact generation is deterministic.

```mermaid
flowchart TD
    subgraph PM["pm-artifacts.js — /shaktra:pm"]
        RES["Research synthesis<br/>(research-first only)"] --> PER["Personas<br/>(evidence minimums)"]
        PER --> JOUR["Journeys<br/>(stage minimums)"]
        JOUR --> PRD["PRD (created LAST)<br/>+ quality loop"]
    end

    PRD -->|".shaktra/prd.md<br/>(+ optional HTML review)"| TD

    subgraph TPM["tpm-design.js → tpm-stories.js — /shaktra:tpm"]
        TD["architect:<br/>gap analysis + design doc"] -->|gaps| PMGAP["product-manager:<br/>answer from PRD/architecture"]
        PMGAP -->|unanswerable| USER["escalate to user<br/>(needs_clarification)"]
        PMGAP -->|answers| TD
        TD --> DGATE{"design gate<br/>tpm-quality loop"}
        DGATE -->|"pass (+ optional<br/>HTML design review)"| STORIES["scrummaster:<br/>story batch"]
        STORIES --> SGATES["per-story quality loops<br/>(parallel)"]
        SGATES --> RICE["product-manager:<br/>RICE + PRD coverage<br/>(parallel)"]
        RICE --> ALLOC["scrummaster:<br/>sprint allocation<br/>(velocity-aware)"]
        ALLOC --> TMEM["Memory capture"]
    end

    ALLOC -->|"stories + sprints.yml"| DEV["/shaktra:dev<br/>(diagram 4)"]

    style PM fill:#fcf8e3,stroke:#f0ad4e,color:#333
    style TPM fill:#e8f4fd,stroke:#337ab7,color:#333
    style USER fill:#f2dede,stroke:#d9534f,color:#333
```

**Notes:** hotfix mode short-circuits to a single trivial-tier story (no quality
loop — a 3-field story has nothing to review). Sprint completion math runs
deterministically in `scripts/shaktra_sprint.py` when dev finishes a story.

**Source:** `dist/shaktra/workflows/tpm-design.js`, `tpm-stories.js`, `pm-artifacts.js`
