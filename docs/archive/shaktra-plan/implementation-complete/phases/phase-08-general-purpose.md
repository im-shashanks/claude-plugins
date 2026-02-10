# Phase 8 — General Purpose Agent [COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) before starting.
> **Depends on:** Phase 1 (Foundation). Standalone workflow — lowest priority.
> **Blocks:** Phase 11 (Workflow Router)

---

## Objective

Build the flexible agent that adapts to different domains by loading specialist skills.

## Deliverables

| File | Lines | Purpose |
|------|-------|---------|
| `skills/shaktra-general/SKILL.md` | ~150 | General purpose orchestrator with domain detection |
| `skills/shaktra-general/specialist-{domain}.md` | ~varies | Specialist skill sub-files (added incrementally) |

## Notes

- Lowest priority phase — build only after core workflows are solid
- Specialist skills are sub-files within `shaktra-general/` (e.g., `specialist-aws.md`, `specialist-statistics.md`) — not a separate top-level directory
- Each specialist skill is <200 lines
- General skill detects domain from user input and loads appropriate specialist sub-file
- Not counted in Appendix D file totals (added post-v1 as needed)

## Validation

- [ ] Domain detection correctly identifies specialist area from user input
- [ ] Specialist skills load on-demand (not all at once)
- [ ] Each specialist sub-file under 200 lines
