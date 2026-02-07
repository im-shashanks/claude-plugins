# Shaktra Framework — Execution Plan

> **Purpose:** Master index for the Shaktra build plan. Each phase is a separate, self-contained file with all context required for execution.
> **Created:** 2026-02-06
> **Source material:** Forge analysis report, Shaktra Framework doc, Architecture diagram
> **Constraint:** Quality and reliability of Forge must be preserved or improved.

---

## How to Use This Plan

1. Read [high-level.md](high-level.md) for architecture and philosophy context
2. Read [architecture-overview.md](architecture-overview.md) for plugin structure, components, and constraints
3. Read the specific phase file you're working on
4. Each phase file includes its own Forge Reference table — read those Forge files before implementing
5. After implementation, validate against the phase's checklist AND [Appendix A](appendices.md#appendix-a-forge-anti-pattern-checklist)

---

## Phases

| Phase | File | Description | Status |
|-------|------|-------------|--------|
| Overview | [architecture-overview.md](architecture-overview.md) | Plugin structure, components, token budget, design constraints | — |
| 1 | [phase-01-foundation.md](phases/phase-01-foundation.md) | Plugin scaffold, init skill, templates | Complete |
| 2 | [phase-02-reference-system.md](phases/phase-02-reference-system.md) | Shared constants — severity, principles, guard tokens, dimensions | Complete |
| 3 | [phase-03-state-schemas.md](phases/phase-03-state-schemas.md) | State file schemas + memory curator agent | Complete |
| 4 | [phase-04-tpm-workflow.md](phases/phase-04-tpm-workflow.md) | TPM workflow — design docs, stories, PM, sprints | — |
| 5 | [phase-05-sdm-workflow.md](phases/phase-05-sdm-workflow.md) | SDM workflow — TDD pipeline (PLAN/RED/GREEN/QUALITY) | — |
| 6 | [phase-06-code-reviewer.md](phases/phase-06-code-reviewer.md) | Code reviewer — app-level review, PR review | — |
| 7 | [phase-07-codebase-analyzer.md](phases/phase-07-codebase-analyzer.md) | Codebase analyzer — brownfield analysis | — |
| 8 | [phase-08-general-purpose.md](phases/phase-08-general-purpose.md) | General purpose agent — domain-flexible | — |
| 9 | [phase-09-hooks.md](phases/phase-09-hooks.md) | Hooks — external enforcement (block, not warn) | — |
| 10 | [phase-10-sprint-planning.md](phases/phase-10-sprint-planning.md) | Sprint planning integration | — |
| 11 | [phase-11-workflow-router.md](phases/phase-11-workflow-router.md) | Workflow router — NL intent classification | — |
| 12 | [phase-12-integration.md](phases/phase-12-integration.md) | Integration testing, doctor skill, packaging | — |
| — | [appendices.md](appendices.md) | Anti-patterns, Forge patterns to port, dependency graph, file counts | — |

---

## Phase Dependency Graph

```
Phase 1 (Foundation)
  └── Phase 2 (Shared Reference System)
        └── Phase 3 (State Management Schemas + Memory Curator Agent)
              ├── Phase 4 (TPM Workflow)
              │     └── Phase 10 (Sprint Planning)
              ├── Phase 5 (SDM Workflow & TDD Pipeline)
              ├── Phase 6 (Code Reviewer)
              ├── Phase 7 (Codebase Analyzer)    [depends on Phase 1 only]
              ├── Phase 8 (General Purpose Agent) [depends on Phase 1 only, lowest priority]
              └── Phase 9 (Hooks & Enforcement)   [depends on Phase 3]
                    └── Phase 11 (Workflow Router) [depends on Phases 4-8]
                          └── Phase 12 (Integration & Packaging)
```

**Parallelizable after Phase 3:**
- Group A: Phases 4, 5, 6 (workflow agents)
- Group B: Phase 7 (can start after Phase 1)
- Group C: Phase 8 (standalone, lowest priority)
- Group D: Phase 9 (hooks — parallel with Group A after Phase 3)

**Critical path:** 1 → 2 → 3 → 5 → 11 → 12
