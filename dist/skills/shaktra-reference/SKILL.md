---
name: shaktra-reference
description: >
  Shared constants, quality standards, and state schemas for all Shaktra agents. Defines severity
  taxonomy, quality principles, guard tokens, story tiers, review dimensions, and YAML schemas.
user-invocable: false
---

# Shaktra Reference — Single Source of Truth

This skill contains canonical definitions for the Shaktra framework. No other file may redefine the constants, taxonomies, or standards declared here. Agents and skills reference these files — they never duplicate them.

## Loading

Agents load this skill via their `skills` frontmatter. Only load the sub-files your agent actually needs.

## Sub-Files

| File | Purpose |
|---|---|
| `severity-taxonomy.md` | P0-P3 severity levels, examples, merge gate logic |
| `quality-principles.md` | 10 core principles with verification checks |
| `guard-tokens.md` | 15 structured tokens for phase/quality/workflow signaling |
| `story-tiers.md` | 4-tier story classification with detection logic and gates |
| `quality-dimensions.md` | 13 review dimensions (A-M) with key checks and P0 triggers |
| `schemas/handoff-schema.md` | TDD state machine — phases, transitions, validation rules |
| `schemas/story-schema.md` | Tier-aware story YAML — field definitions per tier |
| `schemas/settings-schema.md` | Framework config — types, defaults, consumer reference |
| `schemas/decisions-schema.md` | Decisions log — entry schema, 14 categories, lifecycle |
| `schemas/lessons-schema.md` | Lessons learned — 5 fields, capture bar, archival rule |
| `schemas/sprint-schema.md` | Sprint state — velocity tracking, backlog |
| `schemas/design-doc-schema.md` | Design doc sections — tier-scaled structure |

## Agent Loading Guide

| Agent Role | Sub-Files Needed |
|---|---|
| SW Quality, Code Reviewer | severity-taxonomy, quality-principles, quality-dimensions, schemas/handoff-schema, schemas/decisions-schema |
| SW Engineer, Developer | severity-taxonomy, quality-principles, guard-tokens, schemas/handoff-schema, schemas/story-schema |
| Test Agent | severity-taxonomy, guard-tokens, schemas/handoff-schema |
| TPM Quality, Scrum Master | story-tiers, guard-tokens, schemas/sprint-schema, schemas/story-schema |
| Architect | quality-principles, quality-dimensions, schemas/design-doc-schema, schemas/story-schema |
| Memory Curator | schemas/lessons-schema, schemas/handoff-schema |
| Product Manager | story-tiers, schemas/story-schema |
