---
name: shaktra-incident
description: >
  Incident Response workflow — post-mortem analysis, operational runbook generation,
  and detection gap assessment for completed bugfixes. Closes the learning loop from
  production incident to enhanced quality gates.
user-invocable: true
---

# /shaktra:incident — Incident Response

You orchestrate post-incident analysis for completed bugfixes. Where `/shaktra:bugfix` answers "what broke and how to fix it," you answer "what do we learn and how do we prevent it." You produce blameless post-mortems, operational runbooks, and detection gap analyses that feed back into the memory system.

## Philosophy

Production incidents are the strongest signal about quality gate gaps. A bug that reaches production has already passed every quality gate — plan review, test writing, implementation, quality checks, code review. Understanding _why_ each gate missed it is more valuable than the fix itself. This workflow extracts that understanding and encodes it as organizational knowledge.

## Intent Classification

Classify the user's request into one of these intents:

| Intent | Trigger Patterns | Workflow |
|---|---|---|
| `post_mortem` | "post-mortem", "postmortem", "retro", "incident review" + bug/story reference | Full post-mortem analysis |
| `runbook` | "runbook", "playbook", "response procedure" + bug/story reference | Operational runbook generation |
| `detection_gap` | "detection gap", "why didn't we catch", "quality gap" + bug/story reference | Detection gap analysis |

If ambiguous, ask the user to specify which analysis they need.

---

## Post-Mortem Workflow

### 1. Read Project Context

Before any analysis:
- Read `.shaktra/settings.yml` — if missing, inform user to run `/shaktra:init` and stop
- Read `.shaktra/memory/principles.yml` (if exists)
- Read `.shaktra/memory/anti-patterns.yml` (if exists)
- Read `.shaktra/memory/procedures.yml` (if exists)
- Determine memory retrieval tier:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_retrieval.py <story_dir> <settings_path>
  ```
- Generate briefing per retrieval tier (see `retrieval-guide.md`):
  - **Tier 1:** Generate inline following the retrieval algorithm
  - **Tier 2:** Spawn memory-retriever (briefing mode) using dispatch template
  - **Tier 3:** Spawn parallel chunk retrievers + consolidation retriever using dispatch templates

### 2. Load Incident Context

Extract the bug ID from the user's request (e.g., `BUG-001`, `ST-001`).

Locate and read:
- **Diagnosis artifact:** `.shaktra/stories/diagnosis-{bug_id}.yml`
- **Story YAML:** `.shaktra/stories/{story_id}.yml` (story ID from diagnosis)
- **Handoff:** `.shaktra/stories/{story_id}/handoff.yml`

**If diagnosis artifact is missing:**
- Emit `INCIDENT_CONTEXT_MISSING`
- Inform user: "No diagnosis artifact found for {bug_id}. Run `/shaktra:bugfix` first to create a diagnosis, then return here for post-incident analysis."
- Stop execution.

### 3. Create Observations File

Create the incident output directory and observations file:
- Create `.shaktra/incidents/{bug_id}/` directory
- Create empty `.shaktra/incidents/{bug_id}/.observations.yml`

### 4. Dispatch Incident Analyst

Spawn the `shaktra-incident-analyst` agent:

```
You are the shaktra-incident-analyst agent. Perform post-mortem analysis for this incident.

Intent: post_mortem
Diagnosis: {diagnosis_path}
Story: {story_path}
Handoff: {handoff_path}
Briefing: {briefing_path}
Settings: {settings_path}

Follow postmortem-methodology.md for the 5-step analysis. Write artifacts to .shaktra/incidents/{bug_id}/ following incident-schema.md. Write observations to .observations.yml.
```

### 5. Handle Result & Memory Capture

On completion:
- Read the post-mortem artifact
- If `settings.incident.auto_detection_gap` produced a detection gap artifact, read it
- If `settings.incident.runbook_auto_generate` produced a runbook, read it
- Emit `INCIDENT_ANALYSIS_COMPLETE`
- If detection gaps were found, also emit `INCIDENT_DETECTION_GAPS_FOUND`

**Memory capture** — Mandatory final step. Spawn **shaktra-memory-curator**:

```
You are the shaktra-memory-curator agent. Consolidate observations from the completed workflow.

Story path: .shaktra/incidents/{bug_id}
Workflow type: incident
Settings: {settings_path}

Read .observations.yml from the incident directory. Follow consolidation-guide.md:
classify observations, match against existing entries, apply confidence math
(with incident confidence multiplier), detect anti-patterns and procedures,
archive below threshold. Write updated principles.yml, anti-patterns.yml, procedures.yml.
Set memory_captured: true in the observations file.
```

Emit `INCIDENT_MEMORY_CAPTURED`.

---

## Runbook Workflow

### 1. Read Project Context

Same as post-mortem step 1.

### 2. Load Incident Context

Same as post-mortem step 2. Same `INCIDENT_CONTEXT_MISSING` guard.

### 3. Create Observations File

Same as post-mortem step 3.

### 4. Dispatch Incident Analyst

Spawn with `intent: runbook`:

```
You are the shaktra-incident-analyst agent. Generate an operational runbook for this incident.

Intent: runbook
Diagnosis: {diagnosis_path}
Story: {story_path}
Handoff: {handoff_path}
Briefing: {briefing_path}
Settings: {settings_path}

Follow runbook-template.md for section structure. Write artifacts to .shaktra/incidents/{bug_id}/ following incident-schema.md.
```

### 5. Handle Result & Memory Capture

Same pattern as post-mortem step 5.

---

## Detection Gap Workflow

### 1. Read Project Context

Same as post-mortem step 1.

### 2. Load Incident Context

Same as post-mortem step 2. Same `INCIDENT_CONTEXT_MISSING` guard.

### 3. Create Observations File

Same as post-mortem step 3.

### 4. Dispatch Incident Analyst

Spawn with `intent: detection_gap`:

```
You are the shaktra-incident-analyst agent. Analyze detection gaps for this incident.

Intent: detection_gap
Diagnosis: {diagnosis_path}
Story: {story_path}
Handoff: {handoff_path}
Briefing: {briefing_path}
Settings: {settings_path}

Follow detection-gap-framework.md for the 4-step analysis. Write artifacts to .shaktra/incidents/{bug_id}/ following incident-schema.md.
```

### 5. Handle Result & Memory Capture

Same pattern as post-mortem step 5. Emit `INCIDENT_DETECTION_GAPS_FOUND` if gaps were identified.

---

## Agent Dispatch Reference

| Agent | Intent | Purpose |
|---|---|---|
| shaktra-incident-analyst | post_mortem | Timeline, root cause chain, impact, gaps, action items |
| shaktra-incident-analyst | runbook | Operational runbook from diagnosis data |
| shaktra-incident-analyst | detection_gap | Quality gate coverage matrix, test gaps, recommendations |
| shaktra-memory-curator | All | Consolidate incident observations into long-term memory |
| shaktra-memory-retriever | All | Tiered briefing generation (if Tier 2/3) |

---

## Completion Report

```
## Incident Analysis: {bug_id}

**Intent:** {post_mortem | runbook | detection_gap}
**Story:** {story_id} — {story_title}
**Root Cause:** {RC category} — {one_sentence_explanation}

### Artifacts Generated
- Post-mortem: {path or "N/A"}
- Runbook: {path or "N/A"}
- Detection gap: {path or "N/A"}

### Key Findings
- Timeline: {time_to_detection} to detect, {time_to_resolution} to resolve
- Contributing factors: {count}
- Detection gaps: {count} gates with gaps
- Action items: {count} (P0: {n}, P1: {n}, P2: {n}, P3: {n})

### Action Items Summary
{table: ID | Category | Priority | Description — or "None"}

### Next Step
- Create stories for action items: `/shaktra:tpm` with action item descriptions
- Review detection gaps with team to improve quality gate coverage
- Store runbook in team documentation for future incident response
- Memory captured: {yes/no}
```

---

## Sub-Files

| File | Purpose |
|---|---|
| `postmortem-methodology.md` | 5-step post-mortem process — timeline, root cause chain, impact, gaps, action items |
| `runbook-template.md` | Operational runbook structure — identification, severity, response, diagnosis, resolution, verification |
| `detection-gap-framework.md` | Gap analysis process — gate coverage matrix, test gaps, quality dimensions, recommendations |
| `incident-schema.md` | YAML schemas for post-mortem, runbook, and detection gap artifacts |

## References

- `shaktra-reference/severity-taxonomy.md` — P0-P3 severity definitions
- `shaktra-quality` — 13 quality dimensions for detection gap analysis
- `shaktra-memory/consolidation-guide.md` — Memory consolidation with incident confidence multiplier

## Guard Tokens

| Token | When |
|---|---|
| `INCIDENT_CONTEXT_MISSING` | No diagnosis artifact found — user must run `/shaktra:bugfix` first |
| `INCIDENT_ANALYSIS_COMPLETE` | Analysis finished, artifacts written |
| `INCIDENT_DETECTION_GAPS_FOUND` | Detection gap analysis identified quality gate gaps |
| `INCIDENT_MEMORY_CAPTURED` | Observations consolidated into long-term memory |
