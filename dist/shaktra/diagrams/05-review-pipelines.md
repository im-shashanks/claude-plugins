# 5. Review Pipelines (review.js + adversarial.js)

Both review commands run deterministic fan-out pipelines. Findings travel
in-band and the verdict math lives in the script — agents only report evidence.

```mermaid
flowchart TD
    subgraph REV["review.js — /shaktra:review"]
        RB["Briefing"] --> G1["cr-analyzer:<br/>Correctness & Safety<br/>(A B C D)"]
        RB --> G2["cr-analyzer:<br/>Security & Ops<br/>(E F K)"]
        RB --> G3["cr-analyzer:<br/>Reliability & Scale<br/>(G I L)"]
        RB --> G4["cr-analyzer:<br/>Evolution<br/>(H J M)"]
        G1 & G2 & G3 & G4 --> DEDUP["dedup by file:line<br/>(higher severity wins)"]
        DEDUP --> VER["Independent verification<br/>5 categories, ≥ min tests"]
        VER --> GATE["merge gate:<br/>APPROVED · WITH_NOTES ·<br/>CHANGES_REQUESTED · BLOCKED"]
        GATE --> RMEM["Memory capture<br/>(story-linked only)"]
    end

    subgraph ADV["adversarial.js — /shaktra:adversarial-review"]
        CON["Behavior contract<br/>adversary"] --> MUT["Phase A: mutation testing<br/>(runs ALONE — mutates source)"]
        MUT --> RESTORE{"git-verified<br/>restore?"}
        RESTORE -->|clean| P1["input/boundary probes"]
        RESTORE -->|clean| P2["fault/resilience probes"]
        RESTORE -.->|dirty| STOP["blocked:<br/>source_tree_not_restored"]
        P1 & P2 --> SCORE["mutation-score verdict:<br/>pass · concern · blocked"]
        SCORE --> AMEM["Memory capture<br/>(story-linked only)"]
    end

    style REV fill:#e8f4fd,stroke:#337ab7,color:#333
    style ADV fill:#f2dede,stroke:#d9534f,color:#333
    style STOP fill:#d9534f,stroke:#b52b27,color:#fff
```

**Notes:** the four cr-analyzer groups cover all 13 review dimensions; every
failing independent-verification test becomes a P1 finding. Mutation testing
never overlaps the probe phase — the restore check between them is mandatory.

**Source:** `dist/shaktra/workflows/review.js`, `dist/shaktra/workflows/adversarial.js`
