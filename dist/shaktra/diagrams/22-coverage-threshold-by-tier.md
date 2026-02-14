# 22. Coverage Threshold by Tier

Each story tier has a minimum test coverage threshold enforced at the GREEN phase quality gate. Larger stories require higher coverage because they carry more risk. All thresholds are configurable in `.shaktra/settings.yml`.

```mermaid
graph LR
    subgraph Thresholds["Coverage Thresholds by Story Tier"]
        direction TB
        XS["<b>XS (Trivial/Hotfix)</b><br/>70% ████████████████████░░░░░░░░"]
        S["<b>S (Small)</b><br/>80% ████████████████████████░░░░"]
        M["<b>M (Medium)</b><br/>90% ████████████████████████████░"]
        L["<b>L (Large)</b><br/>95% █████████████████████████████"]
    end

    style XS fill:#f0ad4e,stroke:#c6920c,color:#333
    style S fill:#5bc0de,stroke:#31b0d5,color:#333
    style M fill:#5ba85b,stroke:#3a7a3a,color:#fff
    style L fill:#337ab7,stroke:#2e6da4,color:#fff
    style Thresholds fill:#f9f9f9,stroke:#ccc,color:#333
```

**Reading guide:**
- **XS (70%):** Hotfixes and trivial changes. Lowest bar -- speed matters more than exhaustive coverage.
- **S (80%):** Small stories with limited scope. Standard coverage for focused changes.
- **M (90%):** Medium stories -- the default tier. Most features land here.
- **L (95%):** Large stories with architectural impact. Near-complete coverage required due to higher blast radius.
- Thresholds are read from `settings.tdd` at runtime; the values above are defaults set by `/shaktra:init`.

**Source:** `dist/shaktra/README.md` (Coverage thresholds by tier), `dist/shaktra/skills/shaktra-dev/tdd-pipeline.md` (Tier-Aware Gate Matrix)
