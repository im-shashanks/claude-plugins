---
name: shaktra-stories
description: >
  Story creation and enrichment processes. Defines HOW to create, validate, and enrich user stories.
  Loaded by scrummaster agent — not called directly by users.
user-invocable: false
---

# Shaktra Stories — Creation & Enrichment Processes

This skill defines the processes for creating and enriching user stories. It is loaded by the scrummaster agent as part of the TPM workflow.

## Boundary

**This skill defines:** HOW to create stories (process steps, validation rules, enrichment logic).

**shaktra-reference defines:** WHAT fields exist per tier (`schemas/story-schema.md`), WHICH tier a story belongs to (`story-tiers.md`), and the quality framework that reviews them.

This skill never restates field definitions or tier detection logic — it references them.

## Sub-Files

| File | Purpose |
|---|---|
| `story-creation.md` | Creation process (7 steps), enrichment process (6 steps), validation rules, Final Verification Loop |

## How Agents Use This Skill

The **scrummaster** loads this skill and follows the processes in `story-creation.md`:

- **Create mode:** Design doc in → stories out. Follows the 7-step creation process.
- **Enrich mode:** Sparse stories in → enriched stories out. Follows the 6-step enrichment process.

Both modes end with validation and the mandatory Final Verification Loop for cross-story integrity.

## References

- `shaktra-reference/schemas/story-schema.md` — field definitions per tier
- `shaktra-reference/story-tiers.md` — tier detection and gate behavior
- `shaktra-reference/guard-tokens.md` — tokens emitted during creation (GAPS_FOUND, VALIDATION_FAILED)
