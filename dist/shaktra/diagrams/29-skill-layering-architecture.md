# 29. Skill Layering Architecture

Shaktra organizes its 16 skills into three distinct layers: user-invocable skills (the entry points users interact with), internal skills (loaded by agents, never called directly), and the shared reference layer (schemas, taxonomies, and practices used by all components). The key design rule is **no content duplication** — skills define behavior, agents reference it, and the reference layer provides shared definitions.

```mermaid
graph TD
    subgraph UserLayer["User-Invocable Skills (10)"]
        direction LR
        TPM["/shaktra:tpm<br/>TPM Orchestrator"]
        DEV["/shaktra:dev<br/>TDD Pipeline"]
        REV["/shaktra:review<br/>Code Reviewer"]
        ANA["/shaktra:analyze<br/>Codebase Analyzer"]
        GEN["/shaktra:general<br/>Domain Expert"]
        BUG["/shaktra:bugfix<br/>Bug Fix"]
        INIT["/shaktra:init<br/>Project Setup"]
        DOC["/shaktra:doctor<br/>Health Check"]
        WF["/shaktra:workflow<br/>Workflow Router"]
        HELP["/shaktra:help<br/>Help System"]
    end

    subgraph InternalLayer["Internal Skills (4)"]
        direction LR
        QUAL["shaktra-quality<br/>Quality Engine"]
        TDD["shaktra-tdd<br/>TDD Practices"]
        STORIES["shaktra-stories<br/>Story Creation"]
        PM["shaktra-pm<br/>PM Practices"]
    end

    subgraph RefLayer["Shared Reference (1)"]
        direction LR
        REF["shaktra-reference"]
        REF --> SCH["schemas/<br/>story, handoff,<br/>sprint, design-doc,<br/>decisions, lessons"]
        REF --> SEV["severity-taxonomy.md"]
        REF --> QD["quality-dimensions.md"]
        REF --> GT["guard-tokens.md"]
        REF --> ST["story-tiers.md"]
        REF --> QP["quality-principles.md"]
    end

    TPM -->|orchestrates| STORIES
    TPM -->|orchestrates| PM
    DEV -->|orchestrates| TDD
    DEV -->|orchestrates| QUAL
    REV -->|references| QUAL
    BUG -->|routes to| DEV

    QUAL -->|references| REF
    TDD -->|references| REF
    STORIES -->|references| REF
    PM -->|references| REF

    style UserLayer fill:#e8f4fd,stroke:#337ab7,color:#333
    style InternalLayer fill:#fcf8e3,stroke:#f0ad4e,color:#333
    style RefLayer fill:#f2dede,stroke:#d9534f,color:#333
```

**Reading guide:**
- **Top layer (blue):** User-invocable skills — these appear as `/shaktra:name` commands. They orchestrate workflows by spawning agents.
- **Middle layer (yellow):** Internal skills — loaded by agents via their `skills:` frontmatter field. Never called by users directly. They define HOW work is done (quality checks, TDD practices, story creation rules).
- **Bottom layer (red):** Shared reference — the single source of truth for schemas, severity definitions, guard tokens, and quality dimensions. Every internal skill and most agents reference this layer. Content is defined here exactly once.
- Arrows show the dependency direction: user skills orchestrate internal skills, internal skills reference the shared layer.

**Source:** `dist/shaktra/skills/*/SKILL.md` (frontmatter), `CLAUDE.md` (Component Overview)
