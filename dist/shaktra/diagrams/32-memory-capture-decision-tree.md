# 32. Memory Capture Decision Tree

Shaktra maintains two memory files: `decisions.yml` for architectural patterns and conventions, and `lessons.yml` for workflow insights. The capture bar is deliberately high — "Would this materially change future workflow execution?" Routine operations are noise and must be filtered out. This diagram shows how the memory curator decides what to capture and where.

```mermaid
flowchart TD
    START([Workflow Complete]) --> TYPE{Memory<br/>type?}

    TYPE -->|Decision from<br/>quality phase| DEC_PATH["Decision Path"]
    TYPE -->|Lesson from<br/>any workflow| LES_PATH["Lesson Path"]

    DEC_PATH --> DEC_CAT{Decision<br/>category?}
    DEC_CAT -->|New design pattern| CAP_D["Capture to<br/>decisions.yml"]
    DEC_CAT -->|New convention| CAP_D
    DEC_CAT -->|Pattern deviation| CAP_D
    DEC_CAT -->|Canonical example| CAP_D

    LES_PATH --> BAR{"Capture bar:<br/>Would this change<br/>future workflow<br/>execution?"}
    BAR -->|No| SKIP["Do NOT capture<br/>Routine observation"]

    BAR -->|Yes| NEWDEV{"New developer<br/>test: Would this save<br/>them from a real<br/>mistake?"}
    NEWDEV -->|No| SKIP
    NEWDEV -->|Yes| DUP{"Duplicate<br/>check: Similar<br/>lesson exists?"}
    DUP -->|Yes| SKIP
    DUP -->|No| ACTION{"Has concrete<br/>action field?"}
    ACTION -->|No| SKIP
    ACTION -->|Yes| COUNT{"lessons.yml<br/>count >= 100?"}
    COUNT -->|Yes| ARCHIVE["Archive oldest to<br/>lessons-archive.yml"]
    COUNT -->|No| CAP_L["Capture to<br/>lessons.yml"]
    ARCHIVE --> CAP_L

    CAP_L --> FORMAT["Entry format:<br/>id, date, source,<br/>insight, action"]
    CAP_D --> DFMT["Entry format:<br/>category, title,<br/>summary, guidance[]"]

    FORMAT --> DONE["Set memory_captured:<br/>true in handoff"]
    DFMT --> LOADED["Loaded by architect,<br/>sw-engineer, developer<br/>for all future stories"]

    SKIP --> DONE_SKIP["Set memory_captured:<br/>true in handoff<br/>(even if nothing captured)"]

    style SKIP fill:#f5f5f5,stroke:#999,color:#999
    style DONE_SKIP fill:#f5f5f5,stroke:#999,color:#999
    style CAP_D fill:#337ab7,stroke:#2a6496,color:#fff
    style CAP_L fill:#5ba85b,stroke:#3a7a3a,color:#fff
    style BAR fill:#f0ad4e,stroke:#c09032,color:#333
    style NEWDEV fill:#f0ad4e,stroke:#c09032,color:#333
```

**Reading guide:**
- **Decision path (blue):** Decisions are promoted during the QUALITY phase of TDD. They capture design patterns, architectural conventions, and canonical examples. These persist in `decisions.yml` and are loaded by architect, sw-engineer, and developer agents for all future stories.
- **Lesson path (green):** Lessons pass through a multi-step filter (yellow nodes). The capture bar is intentionally strict — "tests passed" or "coverage met" are NOT lessons.
- **Grey nodes** represent filtered-out observations. Even when nothing is captured, `memory_captured` is set to true to satisfy the handoff completion guard.
- `lessons.yml` caps at 100 active entries. Oldest entries are archived before new ones are appended.

**Source:** `dist/shaktra/agents/shaktra-memory-curator.md`, `dist/shaktra/skills/shaktra-reference/schemas/handoff-schema.md`
