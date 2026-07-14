# 3. Layering Architecture

Shaktra 1.x is layered: thin user-invocable skills prepare context and handle
escalations; deterministic workflow scripts own orchestration; agents carry
personas and do the work; knowledge skills and the shared reference layer hold
the quality content. The key design rule is **no content duplication** — every
definition lives in exactly one layer.

```mermaid
graph TD
    subgraph SkillLayer["Thin orchestrator skills (main loop)"]
        direction LR
        SK["/shaktra:tpm · dev · review · adversarial-review<br/>analyze · bugfix · pm · incident<br/>+ general, html-review, 6 utilities"]
    end

    subgraph WorkflowLayer["Deterministic workflow scripts (Workflow tool)"]
        direction LR
        WF["dev-tdd · refactor · review · adversarial<br/>tpm-design · tpm-stories · analyze<br/>bugfix-diagnose · incident · pm-artifacts"]
        LIB["lib/: schemas · quality-loop · memory · report"]
        WF --> LIB
    end

    subgraph AgentLayer["Agents (personas, agentType)"]
        direction LR
        AG["15 agents: architect, sw-engineer, developer,<br/>test-agent, sw-quality, cr-analyzer, adversary,<br/>cba-analyzer, scrummaster, product-manager,<br/>tpm-quality, bug-diagnostician, incident-analyst,<br/>memory-curator, memory-retriever"]
    end

    subgraph KnowledgeLayer["Knowledge skills + shared reference"]
        direction LR
        KNOW["shaktra-tdd · shaktra-quality<br/>shaktra-stories · shaktra-memory"]
        REF["shaktra-reference: severity-taxonomy,<br/>quality-dimensions, quality-principles, schemas/"]
    end

    SK -->|"Workflow({scriptPath, args})<br/>args from shaktra_context.py"| WF
    WF -->|"agent(prompt, {agentType, schema})"| AG
    AG -->|"skills: frontmatter"| KNOW
    KNOW --> REF
    WF -.->|"blocked / needs_clarification"| SK
    SK -.->|"persists results via shaktra_handoff.py"| STATE[(".shaktra/ state:<br/>handoff, settings,<br/>stories, memory")]

    style SkillLayer fill:#e8f4fd,stroke:#337ab7,color:#333
    style WorkflowLayer fill:#e8fde8,stroke:#3c763d,color:#333
    style AgentLayer fill:#fcf8e3,stroke:#f0ad4e,color:#333
    style KnowledgeLayer fill:#f2dede,stroke:#d9534f,color:#333
```

**Reading guide:**
- **Skills (blue):** classify intent, run pre-flight via `scripts/shaktra_context.py`, invoke a workflow, present results, and handle escalations with AskUserQuestion. They never orchestrate agents by hand.
- **Workflows (green):** deterministic JS pipelines — real loops, `parallel()` fan-out, schema-validated agent returns. Shared logic lives in `lib/` children (see `workflows/README.md` for the runtime constraints).
- **Agents (yellow):** full personas dispatched via `agentType`; their structured output must satisfy the schema supplied at dispatch.
- **Knowledge + reference (red):** the quality moat — TDD practices, quality checklists, severity taxonomy, YAML schemas. Defined exactly once, loaded through agent `skills:` frontmatter.
- Dashed arrows: escalation back to the user, and deterministic state persistence (`shaktra_handoff.py`, `shaktra_sprint.py`).

**Source:** `dist/shaktra/workflows/README.md`, `dist/shaktra/skills/*/SKILL.md`, `CLAUDE.md` (Component Overview)
