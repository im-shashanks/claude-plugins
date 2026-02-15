---
name: shaktra-stories
description: >
  Story creation, enrichment, and related schemas. Defines HOW to create and validate user stories,
  WHAT fields exist per tier (story-schema), WHICH tier a story belongs to (story-tiers),
  and sprint state format (sprint-schema). Loaded by scrummaster and other story-consuming agents.
user-invocable: false
---

# Shaktra Stories — Creation, Enrichment & Story Schemas

This skill defines story creation processes and contains the canonical schemas for stories, tiers, and sprints.

## Sub-Files

| File | Purpose |
|---|---|
| `story-creation.md` | Creation process (7 steps), enrichment process (6 steps), validation rules, Final Verification Loop |
| `story-schema.md` | Tier-aware story YAML — field definitions per tier (source of truth for story structure) |
| `story-tiers.md` | 4-tier story classification with detection logic and gates |
| `sprint-schema.md` | Sprint state — velocity tracking, backlog, capacity |

## How Agents Use This Skill

The **scrummaster** loads this skill and follows the processes in `story-creation.md`:

- **Create mode:** Design doc in → stories out. Follows the 7-step creation process.
- **Enrich mode:** Sparse stories in → enriched stories out. Follows the 6-step enrichment process.
- **Sprint allocation:** Uses `sprint-schema.md` for sprint state format.

Other agents (**tpm-quality**, **product-manager**, **developer**, **sw-engineer**, **bug-diagnostician**) load this skill to access `story-schema.md` and `story-tiers.md` for reading and reviewing stories.
