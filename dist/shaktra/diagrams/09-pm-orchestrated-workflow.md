# 9. PM Orchestrated Workflow

The Product Manager skill offers two primary paths based on whether the user has existing research data. Both paths converge on PRD creation as the final artifact, ensuring that personas and journey insights always inform requirements. The research-first path produces evidence-backed artifacts; the hypothesis-first path produces assumption-based artifacts flagged for future validation.

```mermaid
flowchart TD
    Start(["/shaktra:pm"]) --> HasInput{Input\nprovided?}

    HasInput -->|No| Guided["Guided Entry\nQ1: Starting point\nQ2: Research check"]
    HasInput -->|Yes| ClassifyIntent{Keyword\ndetected?}

    ClassifyIntent -->|prd, brainstorm,\npersonas, etc.| Standalone["Standalone Workflow\n(prd / brainstorm /\npersonas / journey /\nresearch / prioritize)"]

    ClassifyIntent -->|No keyword| Triage

    Guided --> Triage

    subgraph Triage ["Phase 0: Triage"]
        direction TB
        CollectInput["Collect user input\n(file path or description)"] --> AskResearch{"Has existing\nuser research?"}
    end

    AskResearch -->|Yes| ResearchPath
    AskResearch -->|No| HypothesisPath

    subgraph ResearchPath ["Research-First Path"]
        direction TB
        RP1["Phase 1: Research\nAnalyze interviews,\nsurveys, feedback\n--> .shaktra/research/"]
        RP2["Phase 2: Personas\nEvidence-backed\n(high confidence)\n--> .shaktra/personas/"]
        RP3["Phase 3: Journeys\nMap experiences per persona\nPain points + opportunities\n--> .shaktra/journeys/"]
        RP4["Phase 4: PRD\nRequirements from\nresearch + journeys\n--> .shaktra/prd.md"]
        RP1 --> RP2 --> RP3 --> RP4
    end

    subgraph HypothesisPath ["Hypothesis-First Path"]
        direction TB
        HP1["Phase 1: Brainstorm\nProblem exploration,\nuser needs, market context\n--> .shaktra/pm/brainstorm.md"]
        HP2["Phase 2: Personas\nAssumption-based\n(lower confidence)\n--> .shaktra/personas/"]
        HP3["Phase 3: Journeys\nHypothesized experiences\nFlagged for validation\n--> .shaktra/journeys/"]
        HP4["Phase 4: PRD\nHypothesis-based\nrequirements\n--> .shaktra/prd.md"]
        HP1 --> HP2 --> HP3 --> HP4
    end

    RP4 --> QualityLoop["Quality Review Loop\n(max 3 attempts)"]
    HP4 --> QualityLoop

    QualityLoop --> UserApproval{"User\napproves PRD?"}
    UserApproval -->|No| Iterate["Iterate on PRD"]
    Iterate --> QualityLoop
    UserApproval -->|Yes| SharedPhases

    subgraph SharedPhases ["Shared Phases"]
        direction TB
        Prioritize{"Stories\nexist?"}
        Prioritize -->|Yes| RICE["PM: RICE scoring\n+ classification"]
        Prioritize -->|No| SkipPri["Skip: run\n/shaktra:tpm first"]
        RICE --> Memory["Memory Capture"]
        SkipPri --> Memory
    end

    SharedPhases --> Report["Completion Report\nArtifacts + next steps"]

    Standalone --> Report
    Report --> Done([Done])
```

### Path Comparison

| Aspect | Research-First | Hypothesis-First |
|--------|---------------|-----------------|
| Phase 1 | Research analysis | Brainstorm |
| Evidence quality | High (interview data) | Low (assumptions) |
| Persona confidence | High | Medium-Low |
| Journey validity | Grounded in data | Hypothesized |
| PRD traceability | Full (research --> personas --> journeys --> requirements) | Partial (assumptions flagged) |
| Recommended follow-up | Proceed to TPM | Validate with `/shaktra:pm research` |

**Source:** `dist/shaktra/skills/shaktra-pm/SKILL.md`, `full-workflow.md`, `full-workflow-research.md`, `full-workflow-hypothesis.md`
