# Shaktra — Appendices

> Reference material for all phases. Check Appendix A after completing every phase.

---

## Appendix A: Forge Anti-Pattern Checklist

**Use during every phase.** Check each item before marking a phase complete.

- [ ] No single file over 300 lines
- [ ] No content duplication across layers (if skill defines it, agent must not restate it)
- [ ] No dead code in repo (no `_to_be_deleted/`, no disabled stubs, no orphaned files)
- [ ] No features advertised but not implemented
- [ ] No severity taxonomy in more than one file
- [ ] No hardcoded fallback values in agent files (fail loudly on missing config)
- [ ] No ASCII art in LLM prompts
- [ ] No internal repetition within files (rule stated once, not 4x)
- [ ] No agents with overlapping scope (SW Quality = story-level, Code Reviewer = app-level)
- [ ] No loading all content for every task (only load what current phase needs)
- [ ] No full ceremony for small changes (trivial tier = minimum viable story, hotfix path)
- [ ] No hooks that are no-ops (hooks must enforce or be removed)
- [ ] No warn-only validations (block or remove)
- [ ] No naming ambiguity between components
- [ ] No circular reference chains between skills

---

## Appendix B: Forge Patterns to Port

| Pattern | Forge Source | Shaktra Target | Changes |
|---------|-------------|----------------|---------|
| TDD state machine | forge-tdd/handoff-schema.md | shaktra-reference/schemas/handoff-schema.md | Add tier-awareness, simplify |
| P0-P3 severity | 6 files (merge) | shaktra-reference/severity-taxonomy.md | **ONE file** |
| Quality gates | forge-checker + forge-quality | shaktra-quality skill (quick-check + comprehensive) | **Unified engine, 2 modes** |
| Single-scope rule | forge-planner | shaktra-scrummaster agent | Keep exactly |
| Create-check-fix loop | orchestrate.md | shaktra-tpm + shaktra-dev skills | Cap at 3 loops |
| Settings-based config | forge/settings.yml | templates/settings.yml | Keep, add sprint config |
| Important decisions | forge/memory/decisions.yml | .shaktra/memory/decisions.yml | Keep (good design) |
| Handoff phase resume | forge-developer | shaktra-dev skill | Keep (essential) |
| Guard tokens | forge-reference (40+ tokens) | shaktra-reference (15 tokens) | **Reduce by 60%** |
| Test name contract | forge-planner | shaktra-scrummaster + story schema | Keep (prevents drift) |
| Unified planning | forge-developer plan phase | shaktra-sw-engineer | Keep (test + impl together) |
| Gap analysis flow | forge-designer | shaktra-architect | Keep (high value) |
| Parallel analysis | forge-analyzer (sequential) | shaktra-cba-analyzer (parallel) | **Change from sequential to parallel** |
| Branch protection | block-main-branch.sh | scripts/block_main_branch.py | Rewrite in Python |
| Permission denials | .claude/settings.json | hooks/hooks.json | Port deny patterns |
| Per-story branching | forge-developer branch creation | shaktra-developer agent | feat/fix/chore convention, staging only |
| Parallel story dev | forge worktree support | Future phase | Port worktree isolation + conflict detection |
| Static best practices | forge skills (testing, coding, quality) | shaktra internal skills | Language-agnostic, scrutinized, selective loading |
| Hotfix workflow | forge quick/hotfix variant | shaktra-tpm hotfix sub-intent | Trivial tier story, reduced coverage threshold |
| Memory capture | forge-docs-updater (race condition) | shaktra-memory-curator (all workflows) | Single writer, haiku model, actionable lessons only |
| Decision lifecycle | forge/memory/important_decisions.yml | .shaktra/memory/decisions.yml | Keep lifecycle, fix write ownership (sw-quality only) |

---

## Appendix C: Phase Dependency Graph

```
Phase 1 (Foundation)
  └── Phase 2 (Shared Reference System)
        └── Phase 3 (State Management Schemas + Memory Curator Agent)
              ├── Phase 4 (TPM Workflow)
              │     └── Phase 10 (Sprint Planning)
              ├── Phase 5 (SDM Workflow & TDD Pipeline)
              ├── Phase 6 (Code Reviewer)
              ├── Phase 7 (Codebase Analyzer)    [depends on Phase 1 only, can start after Phase 1]
              ├── Phase 8 (General Purpose Agent) [depends on Phase 1 only, lowest priority]
              └── Phase 9 (Hooks & Enforcement)   [depends on Phase 3 for schema validation]
                    └── Phase 11 (Workflow Router) [depends on Phases 4-8 main agents]
                          └── Phase 12 (Integration & Packaging)
```

**Parallelizable groups after Phase 3:**
- Group A: Phases 4, 5, 6 (workflow agents — can be built in parallel)
- Group B: Phase 7 (can start after Phase 1; only needs Phase 3 if using schemas)
- Group C: Phase 8 (standalone, lowest priority)
- Group D: Phase 9 (hooks — can parallel with Group A after Phase 3)

**Critical path:** 1 → 2 → 3 → 5 → 11 → 12

**Future enhancement (post-v1):** Parallel story development via git worktrees (ported from Forge). Includes worktree isolation per story, conflict detection (BLOCKING vs SHARED vs DEPENDENCY), parallel sub-agent spawning, and merge order determination.

---

## Appendix D: File Count & Size Summary

| Category | Count | Avg Lines | Total Lines |
|----------|-------|-----------|-------------|
| Main agent skills (SKILL.md + sub-files) | 5 × ~2 files | ~225 | ~2,250 |
| Utility skills | 3 × 1 file | ~120 | ~360 |
| Internal skills (SKILL.md + sub-files) | 3 × ~3 files | ~170 | ~1,530 |
| Reference skill (shared constants + schemas) | 1 × ~12 files | ~58 | ~700 |
| Sub-agent definitions | 11 files | ~90 | ~990 |
| Hook scripts | 4 files | ~50 | ~200 |
| Hook config | 1 file | ~40 | ~40 |
| Templates | 4 files | ~20 | ~80 |
| Plugin config (plugin.json + marketplace.json + CLAUDE.md + README.md) | 4 files | ~50 | ~200 |
| **Total framework** | **~58 files** | — | **~7,000** |
| **Forge equivalent** | **174 active files** | — | **52,655** |

**Result:** ~88% reduction in framework size while preserving quality depth.
