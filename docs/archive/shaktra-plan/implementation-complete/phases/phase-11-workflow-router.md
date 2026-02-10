# Phase 11 — Workflow Router [COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) before starting.
> **Depends on:** All main agent skills (Phases 4-8) should be complete.
> **Blocks:** Phase 12 (Integration)

---

## Objective

Build the primary natural language entry point. `/shaktra:workflow` classifies user intent and dispatches to the appropriate main agent, providing seamless UX. Users can also invoke agents directly via `/shaktra:tpm`, `/shaktra:dev`, etc.

## Deliverables

| File | Lines | Purpose |
|------|-------|---------|
| `skills/shaktra-workflow/SKILL.md` | ~120 | Intent classifier and router |

## Intent Classification

| Intent Patterns | Routes To |
|----------------|-----------|
| "create design", "design doc", "plan stories", "story creation", "sprint" | `/shaktra:tpm` |
| "develop", "implement", "TDD", "write tests", "write code", "fix bug" | `/shaktra:dev` |
| "review code", "code review", "review PR" | `/shaktra:review` |
| "analyze codebase", "codebase analysis", "brownfield" | `/shaktra:analyze` |
| Ambiguous or domain-specific tasks | `/shaktra:general` |

**Critical rule from Forge lessons:** For ambiguous intents, CONFIRM with user before routing. Never auto-capture common words like "plan" or "review" without context.

## Validation

- [ ] Clear intents route correctly
- [ ] Ambiguous intents prompt for confirmation
- [ ] Common words ("plan my weekend") do NOT trigger Shaktra routing

## Forge Reference

| Forge Source | What to Port | What to Change |
|-------------|-------------|----------------|
| forge-auto-router.md (85 lines) | Intent pattern matching | **Add confirmation for ambiguous cases** |
| forge-workflow SKILL.md (1481 lines) | Intent classification | **Reduce to ~120 lines — routing only** |
