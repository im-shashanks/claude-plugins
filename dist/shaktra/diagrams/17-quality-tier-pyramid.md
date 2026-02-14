# 17. Quality Tier Pyramid

SW Quality and Code Review operate at different scopes. SW Quality checks story-level correctness during TDD (36 checks per gate), while Code Review checks app-level production readiness after completion (13 dimensions). Both feed findings into the same P0-P3 severity taxonomy and merge gate.

```mermaid
graph TD
    CR["Code Review<br/><b>App-Level</b><br/>13 dimensions<br/>After story completion"]
    SWQ["SW Quality<br/><b>Story-Level</b><br/>36 checks per gate<br/>During TDD phases"]
    HOOKS["Hooks<br/><b>Constraint Enforcement</b><br/>4 blocking hooks<br/>Always active"]

    CR -->|"feeds findings"| MG["Merge Gate<br/>P0-P3 Severity"]
    SWQ -->|"feeds findings"| MG

    HOOKS -->|"blocks violations"| MG

    style CR fill:#4a90d9,stroke:#2c5f8a,color:#fff
    style SWQ fill:#5ba85b,stroke:#3a7a3a,color:#fff
    style HOOKS fill:#d9534f,stroke:#a94442,color:#fff
    style MG fill:#f0ad4e,stroke:#c6920c,color:#fff
```

**Reading guide:**
- **Top tier (Code Review):** Broadest scope — reviews how code fits the overall application. Runs once after story completion or on PR.
- **Middle tier (SW Quality):** Story-scoped checks at each TDD phase transition. Runs multiple times per story (plan, test, code, quality gates).
- **Bottom tier (Hooks):** Always-on constraint enforcement. Blocks violations in real time, independent of review workflows.
- All three tiers feed into the shared **Merge Gate** which applies the P0-P3 severity taxonomy.

**Source:** `dist/shaktra/README.md` (Quality & Enforcement section), `dist/shaktra/skills/shaktra-quality/quick-check.md`, `dist/shaktra/skills/shaktra-review/SKILL.md`
