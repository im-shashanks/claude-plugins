# 14. Analyze Agent Dispatch

The Codebase Analyzer has two execution modes: standard (9 parallel CBA Analyzers in a single session) and deep (4 team members, each spawning 2-3 CBA Analyzer subagents). Both produce the same 9 dimension artifacts. Stage 1 (tool-based pre-analysis) always runs first to establish ground truth before any LLM analysis begins.

```mermaid
sequenceDiagram
    participant U as User
    participant O as /shaktra:analyze<br/>Orchestrator
    participant TM1 as TM-1: Structure<br/>(D1, D5, D9)
    participant TM2 as TM-2: Domain<br/>(D2, D3)
    participant TM3 as TM-3: Health<br/>(D6, D8)
    participant TM4 as TM-4: Practices<br/>(D4, D7)
    participant MC as Memory Curator<br/>(Haiku)

    U->>O: /shaktra:analyze
    O->>O: Read settings, check manifest
    O->>O: Classify intent (full/targeted/refresh)

    rect rgb(255, 245, 235)
        Note over O,O: STAGE 1: PRE-ANALYSIS (tool-based, no LLM)
        O->>O: Extract file inventory, deps,<br/>call graph, patterns -> static.yml
        O->>O: Scan project structure,<br/>tech stack -> overview.yml
    end

    O->>O: Check execution mode

    alt Deep Mode (teams available)
        rect rgb(235, 245, 255)
            Note over O,TM4: STAGE 2: PARALLEL TEAM ANALYSIS
            par TM-1: Structure
                O->>TM1: D1, D5, D9
                Note right of TM1: Spawns 3 CBA Analyzers<br/>-> structure.yml<br/>-> dependencies.yml<br/>-> git-intelligence.yml
                TM1-->>O: tm1-summary.md
            and TM-2: Domain
                O->>TM2: D2, D3
                Note right of TM2: Spawns 2 CBA Analyzers<br/>+ error propagation correlation<br/>-> domain-model.yml<br/>-> entry-points.yml
                TM2-->>O: tm2-summary.md
            and TM-3: Health
                O->>TM3: D6, D8
                Note right of TM3: Spawns 2 CBA Analyzers<br/>+ cross-cutting risk (sequential)<br/>-> tech-debt.yml<br/>-> critical-paths.yml
                TM3-->>O: tm3-summary.md
            and TM-4: Practices
                O->>TM4: D4, D7
                Note right of TM4: Spawns 2 CBA Analyzers<br/>+ test intelligence correlation<br/>-> practices.yml<br/>-> data-flows.yml
                TM4-->>O: tm4-summary.md
            end
        end

    else Standard Mode (single session)
        rect rgb(235, 245, 255)
            Note over O,O: STAGE 2: 9 PARALLEL CBA ANALYZERS
            O->>O: Spawn D1-D9 CBA Analyzers<br/>simultaneously
            Note right of O: Each writes one artifact:<br/>structure, domain-model,<br/>entry-points, practices,<br/>dependencies, tech-debt,<br/>data-flows, critical-paths,<br/>git-intelligence
        end
    end

    rect rgb(245, 255, 235)
        Note over O,O: STAGE 3: FINALIZE
        O->>O: Validate all 9 artifacts
        O->>O: Cross-cutting risk correlation
        Note right of O: Combine: debt (D6)<br/>+ coverage (D6) + change freq (D9)<br/>+ coupling -> composite_risk
        O->>O: Generate checksums
        O->>O: Update manifest
    end

    rect rgb(245, 235, 255)
        Note over O,MC: STAGE 4: MEMORY
        O->>MC: workflow_type: analysis
        MC-->>O: Lessons captured
    end

    O->>O: Back-fill settings.project.architecture<br/>(if empty + high consistency detected)
    O->>U: Present analysis summary +<br/>architecture diagram
```

### Reading Guide

- **Stage 1** is pure tool execution (Glob, Grep, Bash) with no LLM analysis. It produces static.yml and overview.yml as ground truth that all CBA Analyzers consume.
- **Deep mode** uses 4 team members that each manage 2-3 dimensions. TM-3 has a sequential constraint: its cross-cutting risk agent runs after D6 and D8 complete, optionally reading TM-1's git-intelligence.yml.
- **Standard mode** spawns all 9 CBA Analyzers directly. Simpler but loses the cross-dimension correlation that team members perform.
- **CBA Analyzer** (Opus) is a single agent definition spawned multiple times with different dimension assignments. Each instance writes exactly one YAML artifact.
- **Stage 3** runs in the orchestrator thread: validates artifacts, computes cross-cutting risk if TM-3 did not, generates checksums, and updates the manifest.

**Source:** `dist/shaktra/skills/shaktra-analyze/SKILL.md`, `dist/shaktra/skills/shaktra-analyze/deep-analysis-workflow.md`, `dist/shaktra/skills/shaktra-analyze/standard-analysis-workflow.md`, `dist/shaktra/agents/shaktra-cba-analyzer.md`
