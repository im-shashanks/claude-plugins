---
name: shaktra-reference
description: >
  Shared constants, quality standards, and state schemas for all Shaktra agents. Defines severity
  taxonomy, quality principles, guard tokens, review dimensions, and YAML schemas.
user-invocable: false
---

# Shaktra Reference — Single Source of Truth

This skill contains canonical definitions for the Shaktra framework. No other file may redefine the constants, taxonomies, or standards declared here. Agents and skills reference these files — they never duplicate them.

## Loading

Agents load this skill via their `skills` frontmatter. Story-related schemas (story-schema, story-tiers, sprint-schema) live in `shaktra-stories`. All other schemas and quality references live here.

## Sub-Files

| File | Purpose |
|---|---|
| `severity-taxonomy.md` | P0-P3 severity levels, examples, merge gate logic |
| `quality-principles.md` | 10 core principles with verification checks |
| `guard-tokens.md` | 14 core tokens for phase/quality/workflow signaling (domain skills define additional tokens) |
| `quality-dimensions.md` | 13 review dimensions (A-M) with key checks and P0 triggers |
| `schemas/handoff-schema.md` | TDD state machine — phases, transitions, validation rules |
| `schemas/settings-schema.md` | Framework config — types, defaults, consumer reference |
| `schemas/decisions-schema.md` | Decisions log — entry schema, 14 categories, lifecycle |
| `schemas/lessons-schema.md` | Lessons learned — 5 fields, capture bar, archival rule |
| `schemas/design-doc-schema.md` | Design doc sections — tier-scaled structure |
| `schemas/refactoring-handoff-schema.md` | Refactoring state machine — phases, transitions, baseline metrics |
| `schemas/prd-schema.md` | PRD validation — required sections, quality checks |
| `schemas/persona-schema.md` | Persona YAML — fields, evidence requirements |
| `schemas/journey-schema.md` | Journey map YAML — stages, touchpoints, opportunities |
| `schemas/research-schema.md` | Research synthesis YAML — themes, patterns, recommendations |
| `schemas/analysis-manifest-schema.md` | Analysis checkpoint — dimension progress, resumability, status transitions |

**Moved to `shaktra-stories`:** story-schema.md, story-tiers.md, sprint-schema.md — loaded by agents that work with stories and sprints.

## Agent Loading Guide

| Agent Role | From shaktra-reference | From shaktra-stories |
|---|---|---|
| SW Quality | severity-taxonomy, quality-principles, quality-dimensions, schemas/handoff-schema, schemas/decisions-schema | — |
| CR Analyzer | severity-taxonomy, quality-principles, quality-dimensions | — |
| SW Engineer, Developer | severity-taxonomy, quality-principles, guard-tokens, schemas/handoff-schema | story-schema, story-tiers |
| Test Agent | severity-taxonomy, guard-tokens, schemas/handoff-schema | — |
| TPM Quality | severity-taxonomy, quality-dimensions, guard-tokens, schemas/design-doc-schema | story-schema, story-tiers |
| Scrum Master | — | story-schema, story-tiers, sprint-schema |
| Architect | quality-principles, quality-dimensions, schemas/design-doc-schema | — |
| Memory Curator | schemas/lessons-schema, schemas/handoff-schema | — |
| Bug Diagnostician | severity-taxonomy, guard-tokens | story-schema |
| CBA Analyzer | quality-principles, schemas/decisions-schema, schemas/analysis-manifest-schema | — |
| Product Manager | schemas/decisions-schema, schemas/prd-schema, schemas/persona-schema, schemas/journey-schema, schemas/research-schema | story-schema, story-tiers, sprint-schema |
