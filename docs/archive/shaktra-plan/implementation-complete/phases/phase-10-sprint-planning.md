# Phase 10 — Sprint Planning Integration [COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) before starting.
> **Depends on:** Phase 4 (TPM Workflow)
> **Blocks:** None directly (Phase 11 only needs main agents)

---

## Objective

Add sprint planning capabilities to the TPM workflow, including velocity tracking and capacity planning.

## Deliverables

Updates to existing files:

| File | Changes |
|------|---------|
| `skills/shaktra-tpm/SKILL.md` | Add sprint-related sub-intents |
| `skills/shaktra-tpm/workflow-template.md` | Add sprint workflow steps |
| `agents/shaktra-product-manager.md` | Add capacity planning process |
| `agents/shaktra-scrummaster.md` | Add sprint allocation logic |
| `templates/sprints.yml` | Sprint schema (already created in Phase 1) |

## Workflow

```
User: /shaktra:tpm "Plan sprint 3"

TPM Skill:
  1. Load current sprint state (.shaktra/memory/sprints.yml)
  2. Load stories (.shaktra/stories/*.yml)
  3. Spawn product-manager → Capacity analysis based on velocity data
  4. Spawn scrummaster → Sprint allocation based on:
     - Story points and priorities (from PM)
     - Story dependencies (blocked_by fields)
     - Team capacity (from sprint history)
  5. TPM reviews sprint plan
  6. Update sprints.yml with sprint allocation
```

## Validation

- [ ] Sprint allocation respects story dependencies
- [ ] Velocity tracking updates after story completion
- [ ] Sprint state persists correctly in sprints.yml
