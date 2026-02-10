# Phase 12 — Integration Testing & Packaging [COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) and [appendices.md](../appendices.md) before starting.
> **Depends on:** All previous phases complete.
> **Blocks:** None — this is the final phase.

---

## Objective

End-to-end testing of all workflows, dogfooding, documentation, and plugin packaging.

## Deliverables

| File | Lines | Purpose |
|------|-------|---------|
| `skills/shaktra-doctor/SKILL.md` | ~100 | Framework validation command |
| `README.md` | ~150 | Usage guide with examples |

## Testing Scenarios

1. **Greenfield full workflow:**
   - `/shaktra:init` → `/shaktra:tpm "Full workflow for user auth"` → `/shaktra:dev "Develop ST-001"` → `/shaktra:review "Review ST-001"`

2. **Brownfield workflow:**
   - `/shaktra:init` → `/shaktra:analyze` → `/shaktra:tpm "Design from analysis"` → development

3. **Hotfix workflow (trivial tier):**
   - `/shaktra:tpm hotfix "Fix null pointer in auth module"` → creates Trivial tier story (3 fields) → `/shaktra:dev ST-XXX` → reduced ceremony, hotfix coverage threshold

4. **Sprint planning:**
   - `/shaktra:tpm "Plan sprint 2"` → allocation with velocity data

5. **PR review:**
   - `/shaktra:review "Review PR #42"` → structured review

6. **Hook enforcement:**
   - Verify branch protection blocks main branch operations
   - Verify P0 findings prevent completion
   - Verify story scope enforcement blocks out-of-scope changes

7. **Phase resume:**
   - Start `/shaktra:dev "Develop ST-001"`, stop after RED phase
   - Resume `/shaktra:dev "Resume ST-001"` → continues from GREEN phase

## `/shaktra:doctor` Checks

- All agent files exist and are valid
- All skill files exist and SKILL.md present
- `.shaktra/settings.yml` exists and validates against schema
- Hook scripts are executable
- No circular references between skills
- All referenced sub-files exist
- No file exceeds 300 lines
- No duplicated severity taxonomy
- No orphaned files (every file referenced somewhere)

## Plugin Packaging

1. Ensure `.claude-plugin/plugin.json` has correct version
2. Push to GitHub repository
3. Test installation: `/plugin install shaktra@marketplace`
4. Verify all commands available after installation
5. Test in a fresh project (not shaktra-plugin itself)
