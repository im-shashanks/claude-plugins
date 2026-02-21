# 32. Memory Capture Decision Tree

Shaktra maintains three long-term memory files: `principles.yml` for project patterns and constraints, `anti-patterns.yml` for failure patterns, and `procedures.yml` for workflow adaptations. During workflows, agents write observations to per-story `.observations.yml` files. After each workflow, the memory-curator consolidates observations into the long-term stores using confidence-based math.

```mermaid
flowchart TD
    START([Workflow Complete]) --> READ["Read<br/>.observations.yml"]

    READ --> EMPTY{Observations<br/>exist?}
    EMPTY -->|No| DONE_SKIP["Set memory_captured:<br/>true in handoff"]

    EMPTY -->|Yes| CLASSIFY["CLASSIFY each<br/>observation by type"]

    CLASSIFY --> TYPE{Observation<br/>type?}

    TYPE -->|discovery / fix-rationale /<br/>deviation| PR_CAND["Principle<br/>candidate"]
    TYPE -->|quality-loop-finding<br/>resolved: false| AP_CHECK{"2+ failures<br/>same pattern<br/>within 3 stories?"}
    TYPE -->|quality-loop-finding<br/>resolved: true| PR_CAND
    TYPE -->|observation /<br/>workflow-level| PC_CHECK{"3+ observations<br/>across different<br/>stories?"}
    TYPE -->|consistency-check| MATCH_EXIST["Reinforce / weaken /<br/>contradict existing"]

    PR_CAND --> MATCH{"Match existing<br/>principle?<br/>(title + category +<br/>guidance overlap)"}
    MATCH -->|Yes| REINFORCE["Reinforce:<br/>confidence += 0.08"]
    MATCH -->|No| CREATE_PR["Create new principle<br/>confidence = 0.6"]

    AP_CHECK -->|Yes| CREATE_AP["Create anti-pattern<br/>with trigger patterns"]
    AP_CHECK -->|No| PR_CAND

    PC_CHECK -->|Yes| CREATE_PC["Create procedure<br/>with applies_to"]
    PC_CHECK -->|No| SKIP_OBS["Skip — insufficient<br/>evidence"]

    MATCH_EXIST --> CONF_UPDATE["Update confidence:<br/>reinforce +0.08<br/>weaken -0.08<br/>contradict -0.20"]

    REINFORCE --> ARCHIVE_CHECK
    CREATE_PR --> ARCHIVE_CHECK
    CREATE_AP --> ARCHIVE_CHECK
    CREATE_PC --> ARCHIVE_CHECK
    CONF_UPDATE --> ARCHIVE_CHECK

    ARCHIVE_CHECK{"Confidence<br/>< 0.2?"}
    ARCHIVE_CHECK -->|Yes| ARCHIVE["Set status:<br/>archived"]
    ARCHIVE_CHECK -->|No| ROTATE{"Exceeds<br/>max limit?"}
    ROTATE -->|Yes| ROTATE_ACT["Archive lowest<br/>confidence entries"]
    ROTATE -->|No| WRITE["Write updated<br/>memory files"]
    ROTATE_ACT --> WRITE
    ARCHIVE --> WRITE

    WRITE --> DONE["Set memory_captured:<br/>true in handoff"]

    SKIP_OBS --> DONE

    style SKIP_OBS fill:#f5f5f5,stroke:#999,color:#999
    style DONE_SKIP fill:#f5f5f5,stroke:#999,color:#999
    style CREATE_PR fill:#337ab7,stroke:#2a6496,color:#fff
    style REINFORCE fill:#337ab7,stroke:#2a6496,color:#fff
    style CREATE_AP fill:#d9534f,stroke:#b52b27,color:#fff
    style CREATE_PC fill:#5ba85b,stroke:#3a7a3a,color:#fff
    style CONF_UPDATE fill:#f0ad4e,stroke:#c09032,color:#333
    style ARCHIVE fill:#f5f5f5,stroke:#999,color:#999
```

**Reading guide:**
- **Blue nodes** — principle creation and reinforcement. Principles are the primary knowledge store.
- **Red node** — anti-pattern creation. Triggered only by repeated failures (2+ on same pattern).
- **Green node** — procedure creation. Triggered by workflow-level observations across 3+ stories.
- **Yellow node** — confidence updates for existing entries (reinforce/weaken/contradict).
- **Grey nodes** — filtered-out observations or archived entries. Even when nothing is captured, `memory_captured` is set to true.
- All confidence thresholds are read from `settings.memory.*` — never hardcoded.

**Source:** `dist/shaktra/agents/shaktra-memory-curator.md`, `dist/shaktra/skills/shaktra-memory/consolidation-guide.md`
