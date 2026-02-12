# Shaktra Framework

This project uses the **Shaktra** development framework — an opinionated workflow with TDD, quality gates, and multi-agent orchestration.

## Available Commands

| Command | Purpose |
|---|---|
| `/shaktra:pm` | Product Manager — PRD creation, personas, journeys, prioritization |
| `/shaktra:tpm` | Technical Project Manager — planning, stories, sprint management |
| `/shaktra:dev` | Developer — implementation with TDD workflow + refactoring |
| `/shaktra:bugfix` | Bug Fix — diagnosis, root cause analysis, fix via TDD |
| `/shaktra:review` | Code Reviewer — PR reviews and app-level quality checks |
| `/shaktra:analyze` | Analyzer — brownfield codebase analysis for development readiness |
| `/shaktra:general` | General assistant — questions, explanations, guidance |
| `/shaktra:init` | Initialize Shaktra in a project |
| `/shaktra:doctor` | Diagnose framework health and configuration issues |
| `/shaktra:workflow` | Auto-route to the right agent based on intent |

## Routing

Use `/shaktra:workflow` for automatic intent routing, or invoke agents directly with the commands above.

## State

Framework state is stored in the `.shaktra/` directory:
- `settings.yml` — project configuration and thresholds
- `prd.md` — product requirements document
- `sprints.yml` — sprint state and velocity tracking
- `memory/decisions.yml` — architectural decisions (append-only)
- `memory/lessons.yml` — lessons learned (append-only)
- `stories/` — user story files
- `designs/` — design documents
- `personas/` — user personas
- `journeys/` — customer journey maps
- `research/` — customer research analysis
- `pm/` — PM working artifacts (brainstorm notes)
- `analysis/` — codebase analysis outputs (brownfield)

## Quality Standards

Shared quality standards (severity taxonomy, review checklists) are defined in the `shaktra-reference` skill. Agents reference these standards — they are not duplicated.
