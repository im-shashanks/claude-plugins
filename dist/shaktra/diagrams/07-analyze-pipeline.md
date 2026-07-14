# 7. Analyze Pipeline (workflows/analyze.js)

The single analysis implementation: factual ground truth first, nine parallel
dimensions on top of it, then a consolidation agent that validates artifacts
and computes cross-dimension risk.

```mermaid
flowchart TD
    SKILL["/shaktra:analyze SKILL<br/>manifest + checksum staleness check"] -->|"Workflow(analyze.js, args)"| S1

    subgraph WF["analyze.js (background)"]
        S1["Stage 1: pre-analysis<br/>static.yml + overview.yml<br/>(factual extraction only)"] --> D1["D1 structure"] & D2["D2 domain"] & D3["D3 entry points"] & D4["D4 practices"] & D5["D5 dependencies"] & D6["D6 tech debt"] & D7["D7 data flows"] & D8["D8 critical paths"] & D9["D9 git intel"]
        D1 & D2 & D3 & D4 & D5 & D6 & D7 & D8 & D9 --> CONS["Consolidation agent:<br/>artifact validation (paths, schemas,<br/>evidence density) + cross-dimension<br/>risk correlation + checksums + diagrams"]
        CONS --> MEM["Memory capture"]
    end

    MEM --> DONE["SKILL: architecture back-fill<br/>(auto if high consistency, ask if mixed),<br/>optional HTML report review"]

    DBT["debt-strategy /<br/>dependency-audit modes"] -.->|"single cba-analyzer<br/>dispatch"| DONE

    style WF fill:#e8fde8,stroke:#3c763d,color:#333
    style S1 fill:#e8f4fd,stroke:#337ab7,color:#333
```

**Notes:** targeted and refresh intents pass a dimension subset; checksums map
changed files to stale dimensions (D9 is always stale). Skipped dimensions'
artifacts remain valid — the manifest tracks per-dimension state.

**Source:** `dist/shaktra/workflows/analyze.js`, `dist/shaktra/skills/shaktra-analyze/SKILL.md`
