# 15. PM Agent Dispatch

The Product Manager workflow supports two orchestrated flows (research-first and hypothesis-first) plus standalone modes. Both orchestrated flows produce artifacts in a fixed order, with PRD created last so persona and journey insights inform requirements. The PM agent (Sonnet) is spawned repeatedly in different modes rather than using separate agents.

```mermaid
sequenceDiagram
    participant U as User
    participant O as /shaktra:pm<br/>Orchestrator
    participant PM as Product Manager<br/>(Sonnet)
    participant MC as Memory Curator<br/>(Haiku)

    U->>O: /shaktra:pm {context}
    O->>O: Read settings, decisions, lessons
    O->>O: Classify intent

    alt Orchestrated (default)
        O->>O: Check for research data

        alt Research-First Path
            O->>PM: mode: research-analyze
            Note right of PM: Extract pain points,<br/>JTBD patterns, themes
            PM-->>O: RESEARCH_SYNTHESIZED

            O->>PM: mode: persona-create
            Note right of PM: Create personas from<br/>research evidence
            PM-->>O: PERSONAS_COMPLETE

            O->>PM: mode: journey-create
            Note right of PM: Map journeys per persona,<br/>classify opportunities
            PM-->>O: Journeys written

        else Hypothesis-First Path
            O->>PM: mode: brainstorm
            Note right of PM: Problem exploration,<br/>user needs, market context
            PM-->>O: Brainstorm written

            O->>PM: mode: persona-create
            Note right of PM: Create personas from<br/>brainstorm insights
            PM-->>O: PERSONAS_COMPLETE

            O->>PM: mode: journey-create
            Note right of PM: Map journeys per persona
            PM-->>O: Journeys written
        end

        O->>PM: mode: prd-create
        Note right of PM: Personas -> metrics<br/>Pain points -> requirements<br/>Opportunities -> should-haves
        PM-->>O: PRD_COMPLETE

        O->>PM: mode: prd-review
        PM-->>O: QUALITY_PASS / QUALITY_BLOCKED

        alt QUALITY_BLOCKED
            O->>PM: Fix findings (max 3 attempts)
            PM-->>O: QUALITY_PASS
        end

        O->>U: PRD_APPROVED? (user review)

    else Standalone (keyword detected)
        Note over O,PM: Single mode execution:<br/>brainstorm, prd, personas,<br/>journey, research, prioritize
        O->>PM: mode: {detected keyword}
        PM-->>O: Artifacts written
    end

    O->>MC: workflow_type: pm
    MC-->>O: Lessons captured
    O->>U: Present completion report
```

### Reading Guide

- The PM agent is a single agent (Sonnet) invoked in different modes. Each mode produces a distinct artifact type.
- **Orchestrated flow** runs 4-5 sequential PM spawns. The order ensures downstream artifacts build on upstream context (research informs personas, personas inform journeys, all inform the PRD).
- **PRD review** uses the PM agent itself in prd-review mode -- there is no separate quality agent for PM artifacts.
- **Standalone mode** bypasses orchestration for users who need a single artifact (e.g., `/shaktra:pm brainstorm`).
- Memory Curator runs at the end of every PM workflow, regardless of path taken.

**Source:** `dist/shaktra/skills/shaktra-pm/SKILL.md`, `dist/shaktra/skills/shaktra-pm/agent-prompts.md`, `dist/shaktra/agents/shaktra-product-manager.md`
