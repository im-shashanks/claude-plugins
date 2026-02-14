# 19. Severity Taxonomy Decision Tree

Every quality finding in Shaktra is classified into one of four severity levels (P0-P3). This decision tree shows how to classify a finding based on its impact. The severity taxonomy is defined in exactly one file and referenced everywhere else.

```mermaid
flowchart TD
    START["New Finding"] --> Q1{"Does it cause<br/>data loss, security breach,<br/>or unbounded resource<br/>consumption?"}

    Q1 -->|Yes| P0["<b>P0 Critical</b><br/>Blocks merge -- always"]
    Q1 -->|No| Q2{"Does it cause<br/>incorrect behavior,<br/>missing error handling,<br/>or inadequate coverage?"}

    Q2 -->|Yes| P1["<b>P1 Major</b><br/>Blocks merge if count<br/>> p1_threshold"]
    Q2 -->|No| Q3{"Does it affect<br/>code quality,<br/>maintainability, or<br/>observability?"}

    Q3 -->|Yes| P2["<b>P2 Moderate</b><br/>Does not block merge"]
    Q3 -->|No| P3["<b>P3 Minor</b><br/>Does not block merge"]

    P0 --- EX0["Examples:<br/>SQL injection, hardcoded credentials,<br/>unbounded loops on external input,<br/>missing auth on endpoints,<br/>file write without fsync"]
    P1 --- EX1["Examples:<br/>Coverage below tier threshold,<br/>generic exception messages,<br/>off-by-one errors,<br/>missing retry classification"]
    P2 --- EX2["Examples:<br/>Missing docstrings on public APIs,<br/>magic numbers without constants,<br/>code duplication > 10%"]
    P3 --- EX3["Examples:<br/>Variable naming style,<br/>import ordering,<br/>trailing whitespace"]

    style P0 fill:#d9534f,stroke:#a94442,color:#fff
    style P1 fill:#f0ad4e,stroke:#c6920c,color:#fff
    style P2 fill:#5bc0de,stroke:#31b0d5,color:#fff
    style P3 fill:#bbb,stroke:#999,color:#333
    style EX0 fill:#f9f9f9,stroke:#d9534f,color:#333
    style EX1 fill:#f9f9f9,stroke:#f0ad4e,color:#333
    style EX2 fill:#f9f9f9,stroke:#5bc0de,color:#333
    style EX3 fill:#f9f9f9,stroke:#bbb,color:#333
    style START fill:#337ab7,stroke:#2e6da4,color:#fff
```

**Reading guide:**
- Start at the top with any new finding.
- Each decision node asks about the **impact** of the finding, moving from most severe to least.
- P0 findings always block merge. P1 findings block merge only when they exceed `settings.quality.p1_threshold`. P2 and P3 never block merge.
- Example boxes show representative findings for each severity level drawn from the canonical taxonomy.

**Source:** `dist/shaktra/skills/shaktra-reference/severity-taxonomy.md` (canonical source for P0-P3 definitions)
