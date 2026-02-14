# 20. Merge Gate Logic

The merge gate evaluates all findings from quality reviews and produces one of four verdicts. P0 findings always block. P1 findings block when they exceed the configurable threshold. The same logic is used by both SW Quality (during TDD) and Code Review (after completion).

```mermaid
flowchart TD
    START["Collect All Findings"] --> P0CHECK{"P0 count > 0?"}

    P0CHECK -->|Yes| BLOCKED["BLOCKED<br/>Critical issues --<br/>cannot merge"]
    P0CHECK -->|No| P1CHECK{"P1 count ><br/>p1_threshold?"}

    P1CHECK -->|Yes| CHANGES["CHANGES_REQUESTED<br/>Fix P1s before merge"]
    P1CHECK -->|No| P2CHECK{"P1 > 0 or P2 > 0?"}

    P2CHECK -->|Yes| NOTES["APPROVED_WITH_NOTES<br/>Merge with awareness"]
    P2CHECK -->|No| APPROVED["APPROVED<br/>Ship it"]

    style BLOCKED fill:#d9534f,stroke:#a94442,color:#fff
    style CHANGES fill:#f0ad4e,stroke:#c6920c,color:#fff
    style NOTES fill:#5bc0de,stroke:#31b0d5,color:#fff
    style APPROVED fill:#5ba85b,stroke:#3a7a3a,color:#fff
    style START fill:#337ab7,stroke:#2e6da4,color:#fff
```

**Source:** `dist/shaktra/skills/shaktra-reference/severity-taxonomy.md` (Merge Gate Logic), `dist/shaktra/skills/shaktra-review/SKILL.md` (Verdicts section)
