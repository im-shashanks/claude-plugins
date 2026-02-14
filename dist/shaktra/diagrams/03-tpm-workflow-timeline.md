# 3. TPM Workflow Timeline

The Technical Project Manager orchestrates 7 distinct intents, each dispatching a different sequence of specialized agents. The Full workflow is the default path for new features -- it progresses through design, story creation, PM analysis, and memory capture, with quality loops at each stage.

```mermaid
flowchart TD
    Start(["/shaktra:tpm"]) --> Classify{Classify\nintent}

    Classify -->|New feature| Full
    Classify -->|"design only"| DesignOnly
    Classify -->|"stories only"| StoriesOnly
    Classify -->|"enrich"| Enrich
    Classify -->|"hotfix: ..."| HotfixFlow
    Classify -->|"sprint"| SprintFlow
    Classify -->|"close sprint"| CloseFlow

    subgraph Full ["Full Workflow"]
        direction TB
        F1["Phase 1: Design\nArchitect + PM (gaps)\n+ Quality Loop"] --> F2["Phase 2: Stories\nScrummaster (create)\n+ Quality Loop per story"]
        F2 --> F3["Phase 3: PM Analysis\nPM (coverage + RICE)\n+ Sprint Allocation"]
        F3 --> F4["Phase 4: Memory\nMemory Curator"]
    end

    subgraph DesignOnly ["Design Only"]
        DO1["Design Phase"] --> DO2["Memory"]
    end

    subgraph StoriesOnly ["Stories Only"]
        SO1["Stories Phase"] --> SO2["PM Analysis"] --> SO3["Memory"]
    end

    subgraph Enrich ["Enrich"]
        EN1["Scrummaster (enrich)"] --> EN2["Quality Loop"] --> EN3["User Approval"] --> EN4["Memory"]
    end

    subgraph HotfixFlow ["Hotfix"]
        HF1["Scrummaster creates\nTrivial story"] --> HF2["Single quality pass\n(no loop)"] --> HF3["Memory"]
    end

    subgraph SprintFlow ["Sprint Planning"]
        SP1["PM (RICE)"] --> SP2["Scrummaster\n(sprint-allocation)"] --> SP3["Sprint Goal\nReview"] --> SP4["Memory"]
    end

    subgraph CloseFlow ["Close Sprint"]
        CS1["Scrummaster\n(close-sprint)"] --> CS2["Memory"]
    end

    Full --> Summary([Present Summary])
    DesignOnly --> Summary
    StoriesOnly --> Summary
    Enrich --> Summary
    HotfixFlow --> Summary
    SprintFlow --> Summary
    CloseFlow --> Summary
```

### Agent Sequence by Intent

| Intent | Agents (in order) |
|--------|-------------------|
| Full | Architect, PM (gaps), TPM-Quality, Scrummaster, PM (coverage), PM (RICE), Scrummaster (sprint), Memory Curator |
| Design Only | Architect, PM (gaps), TPM-Quality, Memory Curator |
| Stories Only | Scrummaster, TPM-Quality, PM (coverage), PM (RICE), Scrummaster (sprint), Memory Curator |
| Enrich | Scrummaster (enrich), TPM-Quality, Memory Curator |
| Hotfix | Scrummaster, TPM-Quality, Memory Curator |
| Sprint | PM (RICE), Scrummaster (sprint), Memory Curator |
| Close Sprint | Scrummaster (close), Memory Curator |

**Source:** `dist/shaktra/skills/shaktra-tpm/workflow-template.md`
