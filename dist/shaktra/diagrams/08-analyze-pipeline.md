# 8. Analyze Pipeline

The Codebase Analyzer uses a 2-stage pipeline: Stage 1 extracts ground truth via tool-based scanning (no LLM), then Stage 2 dispatches 9 parallel CBA Analyzer agents for deep dimension analysis grounded in that factual data. The pipeline supports 6 intents including incremental refresh and targeted single-dimension analysis.

```mermaid
flowchart TD
    Start(["/shaktra:analyze"]) --> Classify{Classify\nintent}

    Classify -->|Full analysis| CheckManifest{Manifest\nexists?}
    Classify -->|Specific dimension| Targeted
    Classify -->|"refresh"| Refresh
    Classify -->|"debt strategy"| DebtStrategy
    Classify -->|"dependency audit"| DepAudit
    Classify -->|"status"| Status["Report manifest\nstate"]

    CheckManifest -->|Incomplete| AskResume{"Resume or\nstart fresh?"}
    CheckManifest -->|No| Stage1
    AskResume -->|Resume| SkipComplete["Skip completed\nstages"]
    AskResume -->|Fresh| Stage1

    SkipComplete --> Stage2

    subgraph Stage1 ["Stage 1: Pre-Analysis (Sequential)"]
        direction TB
        S1a["Static Extraction\nFile inventory, dependency graph,\ncall graph, type hierarchy,\npattern detection, config inventory\n--> static.yml"]
        S1b["System Overview\nProject identity, repo structure,\nbuild system, tech stack, entry points\n--> overview.yml"]
        S1a --> S1b
    end

    Stage1 --> TeamCheck{Agent teams\navailable?}

    TeamCheck -->|Yes| DeepMode["Deep mode:\n4 parallel team members\nwith subagents"]
    TeamCheck -->|No| StandardMode

    subgraph StandardMode ["Stage 2: Standard Mode (Parallel)"]
        direction LR
        D1["D1: Architecture\n& Structure"]
        D2["D2: Domain Model\n& Business Rules"]
        D3["D3: Entry Points\n& Interfaces"]
        D4["D4: Coding\nPractices"]
        D5["D5: Dependencies\n& Tech Stack"]
        D6["D6: Tech Debt\n& Security"]
        D7["D7: Data Flows\n& Integration"]
        D8["D8: Critical Paths\n& Risk"]
        D9["D9: Git\nIntelligence"]
    end

    DeepMode --> Finalize
    StandardMode --> Finalize

    subgraph Finalize ["Stage 3: Finalize"]
        direction TB
        F1["Validate artifacts\n(summary key required)"]
        F2["Cross-cutting risk\ncorrelation"]
        F3["Generate checksums"]
        F4["Generate Mermaid\ndiagrams"]
        F5["Update manifest"]
        F1 --> F2 --> F3 --> F4 --> F5
    end

    Finalize --> SettingsUpdate["Update settings\narchitecture field\nfrom analysis"]
    SettingsUpdate --> MemoryCapture["Stage 4: Memory\nCapture"]
    MemoryCapture --> Report["Report Summary\nKey findings + dimension scores"]

    subgraph Targeted ["Targeted Analysis"]
        T1["Map intent to\ndimension D1-D9"] --> T2{"static.yml\nexists?"}
        T2 -->|No| T3["Run Stage 1 first"]
        T2 -->|Yes| T4["Spawn single\nCBA Analyzer"]
        T3 --> T4
        T4 --> T5["Update manifest"]
    end

    subgraph Refresh ["Incremental Refresh"]
        R1["Read checksums"] --> R2["Recompute hashes"]
        R2 --> R3["Identify stale\ndimensions"]
        R3 --> R4["User confirms\nwhich to re-run"]
        R4 --> R5["Re-run selected\ndimensions"]
    end

    subgraph DebtStrategy ["Debt Strategy"]
        DS1{"tech-debt.yml\nexists?"} -->|No| DS2["Run D6 first"]
        DS1 -->|Yes| DS3["CBA Analyzer\n(debt-strategy mode)"]
        DS2 --> DS3
        DS3 --> DS4["debt-strategy.yml"]
    end

    subgraph DepAudit ["Dependency Audit"]
        DA1{"dependencies.yml\nexists?"} -->|No| DA2["Run D5 first"]
        DA1 -->|Yes| DA3["CBA Analyzer\n(dependency-audit mode)"]
        DA2 --> DA3
        DA3 --> DA4["dependency-audit.yml"]
    end

    Report --> Done([Done])
    Targeted --> Done
    Refresh --> Done
    DebtStrategy --> Done
    DepAudit --> Done
    Status --> Done
```

### Reading Guide

- **Top:** Intent classification routes to one of 6 workflows
- **Left column:** Full analysis flows through Stage 1 (sequential extraction), Stage 2 (parallel deep analysis), Stage 3 (finalization), and Stage 4 (memory)
- **Right column:** Targeted, refresh, debt, and dependency workflows are self-contained sub-flows
- **Stage 2 fork:** Teams availability determines whether analysis uses parallel team members or parallel agents within a single session

### Output Artifacts

| Stage | Artifacts |
|-------|-----------|
| Stage 1 | `static.yml`, `overview.yml` |
| Stage 2 | `structure.yml`, `domain-model.yml`, `entry-points.yml`, `practices.yml`, `dependencies.yml`, `tech-debt.yml`, `data-flows.yml`, `critical-paths.yml`, `git-intelligence.yml` |
| Stage 3 | `checksum.yml`, updated `manifest.yml` |

**Source:** `dist/shaktra/skills/shaktra-analyze/SKILL.md`, `standard-analysis-workflow.md`
