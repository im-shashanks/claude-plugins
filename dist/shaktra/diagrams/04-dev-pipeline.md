# 4. Dev Pipeline (workflows/dev-tdd.js)

`/shaktra:dev` runs pre-flight in the main loop, then hands execution to the
deterministic `dev-tdd.js` workflow. Quality gates use the single
`lib/quality-loop.js` implementation; escalations return to the skill, which
asks the user and re-invokes with cached agents replaying.

```mermaid
flowchart TD
    SKILL["/shaktra:dev SKILL<br/>pre-flight via shaktra_context.py<br/>(language, deps, story-quality guard)"] -->|"Workflow(dev-tdd.js, args)"| BRIEF

    subgraph WF["dev-tdd.js (background)"]
        BRIEF["Briefing<br/>lib/memory.js"] --> PLAN["PLAN<br/>sw-engineer"]
        PLAN -->|medium/large| PGATE{"plan gate<br/>quality-loop"}
        PGATE -->|pass| BRANCH["BRANCH<br/>developer"]
        PLAN -->|trivial/small| BRANCH
        BRANCH --> RED["RED<br/>test-agent<br/>valid-red enforced"]
        RED --> TGATE{"test gate<br/>quality-loop"}
        TGATE -->|pass| GREEN["GREEN<br/>developer<br/>coverage ≥ tier threshold"]
        GREEN --> CGATE{"code gate<br/>quality-loop"}
        CGATE -->|"pass, medium/large"| QUAL["QUALITY<br/>comprehensive + consistency gate"]
        CGATE -->|"pass, trivial/small"| MEM
        QUAL --> MEM["Memory capture<br/>lib/memory.js"]
        MEM --> REPORT["lib/report.js"]
    end

    PGATE & TGATE & CGATE & QUAL -.->|"blocked / needs_clarification<br/>(attempts exhausted)"| ESC["SKILL: AskUserQuestion →<br/>re-invoke with resumeFromRunId"]
    REPORT --> DONE["SKILL: persist via shaktra_handoff.py,<br/>sprint update via shaktra_sprint.py,<br/>present report"]

    style WF fill:#e8fde8,stroke:#3c763d,color:#333
    style ESC fill:#fcf8e3,stroke:#f0ad4e,color:#333
```

**Notes:** RED is skipped for trivial tier; the comprehensive QUALITY phase runs
for medium/large only (the tier gate matrix lives in `story-tiers.md`).
`refactor.js` follows the same shape with ASSESS → FORTIFY → TRANSFORM → VERIFY.

**Source:** `dist/shaktra/workflows/dev-tdd.js`, `dist/shaktra/skills/shaktra-dev/SKILL.md`
