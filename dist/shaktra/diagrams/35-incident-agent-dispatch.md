# 35. Incident Agent Dispatch

Shows the dispatch relationship between the `/shaktra:incident` skill and its agents. The skill classifies intent and dispatches the incident-analyst agent with the appropriate parameters. Memory-curator and memory-retriever are shared agents used for knowledge capture and briefing generation.

```mermaid
flowchart TD
    subgraph Skill ["Skill Layer"]
        INC["/shaktra:incident\nOrchestrator"]
    end

    subgraph Classification ["Intent Classification"]
        PM_INT["post_mortem intent"]
        RB_INT["runbook intent"]
        DG_INT["detection_gap intent"]
    end

    subgraph Agents ["Agent Layer"]
        INA["Incident Analyst\n(Opus)\nPost-mortem, runbook, gaps"]
        MC["Memory Curator\n(Haiku)\nObservation consolidation"]
        MR["Memory Retriever\n(Sonnet)\nTiered briefing generation"]
    end

    subgraph Artifacts ["Output Artifacts"]
        A_PM["postmortem.yml\nTimeline, root cause chain,\nimpact, action items"]
        A_RB["runbook.yml\nIdentification, response,\ndiagnosis, resolution"]
        A_DG["detection-gap.yml\nGate matrix, test gaps,\nrecommendations"]
        A_OBS[".observations.yml\nincident-learning +\ndetection-gap types"]
    end

    subgraph Memory ["Memory Store"]
        PRIN["principles.yml"]
        ANTI["anti-patterns.yml\n(fast-track from incidents)"]
        PROC["procedures.yml"]
    end

    INC --> PM_INT
    INC --> RB_INT
    INC --> DG_INT

    PM_INT -->|"dispatch with\nintent: post_mortem"| INA
    RB_INT -->|"dispatch with\nintent: runbook"| INA
    DG_INT -->|"dispatch with\nintent: detection_gap"| INA

    INA --> A_PM
    INA --> A_RB
    INA --> A_DG
    INA --> A_OBS

    INC -->|"Tier 2/3\nbriefing"| MR
    INC -->|"after analysis"| MC

    MC -->|consolidate| PRIN
    MC -->|fast-track anti-pattern| ANTI
    MC -->|procedure detection| PROC
```

### Reading Guide

- **Skill layer:** `/shaktra:incident` is the orchestrator that classifies intent and manages dispatch.
- **Intent classification:** Three intents map to the same agent with different parameters. The post-mortem intent may auto-generate runbook and detection gap artifacts based on settings.
- **Agent layer:** Incident Analyst (Opus) handles all analysis work. Memory Curator (Haiku) consolidates observations. Memory Retriever (Sonnet) generates briefings for Tier 2/3 memory stores.
- **Artifacts:** Each intent produces its primary artifact plus observations. All artifacts are written to `.shaktra/incidents/{bug_id}/`.
- **Memory store:** Incident observations receive a confidence multiplier and can fast-track anti-pattern creation.

**Source:** `dist/shaktra/skills/shaktra-incident/SKILL.md`, `dist/shaktra/agents/shaktra-incident-analyst.md`
