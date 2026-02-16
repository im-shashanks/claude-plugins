---
name: shaktra-bugfix
description: >
  Bug Fix workflow — structured diagnosis followed by TDD remediation.
  Investigates bugs through triage, root cause analysis, and blast radius assessment,
  then routes to the standard TDD pipeline for the fix.
user-invocable: true
---

# /shaktra:bugfix — Bug Fix Workflow

You orchestrate the bug fix lifecycle: **investigation** (new) followed by **remediation** (existing TDD pipeline). Investigation is detective work — bottom-up, evidence-driven. Remediation reuses the entire `/shaktra:dev` pipeline unchanged.

**INVESTIGATION** (this workflow): TRIAGE → DIAGNOSE → creates story → **REMEDIATION** (reuse `/shaktra:dev`): PLAN → RED → GREEN → QUALITY

---

## Intent Classification

| Intent | Trigger Patterns | Workflow |
|---|---|---|
| `bugfix` | "bug", "bugfix", "debug", "diagnose", bug description, error message, stack trace | Investigation → Remediation |
| `diagnose_only` | "just diagnose", "investigate only", "root cause analysis" | Investigation only (no fix) |

---

## Execution Flow

### 1. Read Project Context

Before any work:
- Read `.shaktra/settings.yml` — if missing, inform user to run `/shaktra:init` and stop
- Read `.shaktra/memory/decisions.yml` — for prior decisions (if exists)
- Read `.shaktra/memory/lessons.yml` — for past bug patterns (if exists)

### 2. Classify Intent

Parse the user's request. Extract:
- **Bug description** — the symptom being reported
- **Error context** — stack traces, error messages, log snippets (if provided)
- **Scope hints** — file paths, function names, component references

### 3. Dispatch Bug Diagnostician

Spawn the bug-diagnostician agent for investigation:

```
You are the shaktra-bug-diagnostician agent. Investigate this bug.

Bug description: {bug_description}
Error context: {error_context or "None provided"}
Settings: {settings_path}
Decisions: {decisions_path}
Lessons: {lessons_path}

Follow the 5-step diagnosis methodology. Produce a diagnosis artifact and story draft.
```

### 4. Handle Diagnosis Result

**On `DIAGNOSIS_COMPLETE`:**
- Read the diagnosis artifact and story draft
- Present the diagnosis summary to the user
- If `diagnose_only` intent: stop here, present findings
- If `bugfix` intent: proceed to remediation

**On `DIAGNOSIS_BLOCKED`:**
- Present what was attempted and why reproduction failed
- Ask user for additional context, environment details, or reproduction steps
- Do not proceed to remediation without confirmed root cause

**On `BLAST_RADIUS_FOUND`:**
- Present blast radius summary with recommended additional stories
- Ask user which (if any) blast radius stories to create
- These are separate stories — they do not block the current fix

### 5. Route to Remediation (TDD Pipeline)

The diagnosis creates a story with `scope: bug_fix`. Route to `/shaktra:dev` with that story:

```
Invoke Skill(skill: "shaktra-dev", args: "develop story {story_id}")
```

The entire TDD pipeline runs unchanged:
- **PLAN** — sw-engineer plans the fix using diagnosis artifact as additional context
- **RED** — test-agent writes tests (the reproduction test from diagnosis + regression tests)
- **GREEN** — developer implements the fix
- **QUALITY** — sw-quality reviews at every gate (quick-check + performance/data + security checks)

### 6. Memory Enhancement

After remediation completes, the memory-curator captures lessons with enhanced metadata:

```yaml
source: "bugfix-{story_id}"
tags: ["bug-pattern", "{root_cause_category}"]
```

This enables future diagnoses to reference past bug patterns from `lessons.yml`.

---

## Agent Dispatch Reference

| Agent | Phase | Purpose |
|---|---|---|
| shaktra-bug-diagnostician | Investigation | Triage + 5-step diagnosis + blast radius |
| shaktra-sw-engineer | Remediation — PLAN | Plan the fix using diagnosis as context |
| shaktra-test-agent | Remediation — RED | Write failing tests (reproduction + regression) |
| shaktra-developer | Remediation — GREEN | Implement the fix |
| shaktra-sw-quality | Remediation — All gates | Quality review at every transition |
| shaktra-memory-curator | Remediation — Memory | Capture bug patterns as lessons |

---

## Completion Report

After the full bugfix lifecycle:

```
## Bug Fix Complete

**Bug:** {bug_id} — {symptom_summary}
**Root Cause:** {category} — {one_sentence_explanation}
**Story:** {story_id} — {story_title}
**Branch:** {branch_name}

### Diagnosis
- Symptom: {symptom_type}
- Root cause category: {RC-LOGIC|RC-DATA|...}
- Location: {file:line}
- Blast radius: {N similar patterns found, M recommended as stories}

### TDD Results
- Tests written: {count} (including reproduction test)
- Tests pass: {all_green}
- Coverage: {coverage}%

### Quality Results
- All gates: {PASS/BLOCKED}
- Review iterations: {count}

### Blast Radius Stories
- {list of recommended stories, or "None"}

### Next Step
- {recommended action}
```

---

## Sub-Files

| File | Purpose |
|---|---|
| `diagnosis-methodology.md` | 5-step root cause analysis process — triage, reproduce, hypothesize, gather evidence, isolate, blast radius |

## References

- `shaktra-reference/severity-taxonomy.md` — P0-P3 severity definitions
- `shaktra-stories/story-schema.md` — story structure (scope: bug_fix)
- `shaktra-reference/schemas/handoff-schema.md` — TDD state machine (reused for remediation)

## Guard Tokens

This workflow emits and responds to:
- `DIAGNOSIS_COMPLETE` — root cause confirmed, story created → proceed to remediation
- `DIAGNOSIS_BLOCKED` — cannot reproduce → stop, ask user for input
- `BLAST_RADIUS_FOUND` — similar patterns found → present to user
- All TDD pipeline tokens (from `/shaktra:dev`) apply during remediation
