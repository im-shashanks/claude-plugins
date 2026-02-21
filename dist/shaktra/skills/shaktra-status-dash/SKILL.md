---
name: shaktra-status-dash
description: >
  Full-view project dashboard. Shows plugin version and update status, sprint health,
  story pipeline, quality summary, memory health, and analysis progress. Read-only.
user-invocable: true
---

# /shaktra:status-dash — Project Dashboard

When this skill is invoked, immediately execute all sections below in order and present the results as a formatted dashboard. Do not ask clarifying questions — just run the checks and display the output.

Read-only — never create, modify, or delete any file. Use `${CLAUDE_PLUGIN_ROOT}` to locate the installed plugin directory.

---

## Section 1 — Plugin Info + Version Check

Run the version check script via Bash:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_version.py ${CLAUDE_PLUGIN_ROOT}
```

The script outputs a JSON object. Parse the `status` field and display accordingly:

| `status` value | Display |
|---|---|
| `up_to_date` | `Version: {local_version}` + `Up to date (v{local_version})` |
| `update_available` | `Version: {local_version}` + `Update available: {local_version} → {remote_version}` + `Run: /plugin install {repository}` |
| `ahead` | `Version: {local_version}` + `Local version ({local_version}) is ahead of remote ({remote_version})` |
| `offline` | `Version: {local_version}` + `Could not check for updates (offline or rate-limited)` |
| `no_repository` | `Version: {local_version}` + `No repository configured — version check unavailable` |

If the JSON contains `"error"`, display: "Plugin not configured — plugin.json not found."

---

## Section 2 — Sprint Health

1. Read `.shaktra/sprints.yml`.
2. Find the sprint where `status` is `active` (or the most recent sprint).
3. Display:
   - Sprint ID and goal
   - Start date → end date
   - Days remaining (compute from end date vs today)
   - Capacity: committed points vs capacity points
4. If `velocity_history` exists, show the last 3 entries as a trend line (e.g., `Velocity trend: 18 → 21 → 24`).
5. If no sprints file or no active sprint: display "No active sprint — run `/shaktra:tpm` to plan one."

---

## Section 3 — Story Pipeline

1. Glob `.shaktra/stories/*/handoff.yml` — read each file.
2. Extract `story_id` and `current_phase` from each handoff.
3. Group stories by phase in pipeline order: `pending` → `plan` → `tests` → `code` → `quality` → `complete` → `failed`.
4. Display as a table:

```
| Phase    | Count | Stories          |
|----------|-------|------------------|
| pending  | 2     | ST-004, ST-005   |
| plan     | 1     | ST-003           |
| code     | 1     | ST-002           |
| complete | 1     | ST-001           |
```

5. Only show phases that have at least one story.
6. If a story has `blocked: true` or `blocker` field set, append "(blocked)" after its ID.
7. If no stories exist: display "No stories found — run `/shaktra:tpm` to create stories."

---

## Section 4 — Quality Summary

1. Read all `.shaktra/stories/*/handoff.yml` files.
2. For each, check for `quality_findings` (a list of findings with `severity` and `resolved` fields).
3. Count **unresolved** findings (where `resolved` is false or absent) grouped by severity: P0, P1, P2, P3.
4. Read `.shaktra/settings.yml` → `quality.p1_threshold` for the P1 limit.
5. Determine merge-blocking status:
   - **Blocked** if any unresolved P0 exists
   - **Blocked** if unresolved P1 count exceeds `p1_threshold`
   - **Clear** otherwise
6. Display:

```
| Severity | Unresolved |
|----------|------------|
| P0       | 0          |
| P1       | 1          |
| P2       | 3          |
| P3       | 2          |

Merge status: Clear (P1: 1/2 threshold)
```

7. If no quality findings exist across any story: display "No quality findings recorded."

---

## Section 5 — Memory Health

1. Read `.shaktra/memory/principles.yml` → count entries by confidence band. If file is missing or empty, count is 0.
   - High: `confidence >= 0.7`
   - Moderate: `confidence >= 0.4` and `< 0.7`
   - Low: `confidence >= 0.2` and `< 0.4`
2. Read `.shaktra/memory/anti-patterns.yml` → count active entries. If missing or empty, count is 0.
3. Read `.shaktra/memory/procedures.yml` → count active entries. If missing or empty, count is 0.
4. Read `.shaktra/settings.yml` → `memory.max_principles`, `memory.max_anti_patterns`, `memory.max_procedures` for limits.
5. Display:
   - `Principles: {total_count} ({high}↑ {moderate}~ {low}↓)`
   - `Anti-patterns: {count}`
   - `Procedures: {count}`
6. If any file is at 80% or more of its max limit, add warning: "Approaching limit — lowest confidence entries will be archived."

---

## Section 6 — Analysis Progress

1. Check if `.shaktra/analysis/manifest.yml` exists. If not, skip this section entirely.
2. Read the manifest — extract each dimension entry (D1 through D9) with its `status`.
3. Display:

```
| Dimension | Name            | Status    |
|-----------|-----------------|-----------|
| D1        | Architecture    | complete  |
| D2        | Practices       | complete  |
| D3        | Dependencies    | pending   |
| ...       | ...             | ...       |
```

4. Show summary: `Completed: {n}/9 dimensions`

---

## Graceful Degradation

Each section degrades independently:
- If a file is missing or unreadable, show a short message for that section and continue to the next.
- **If `.shaktra/` directory does not exist**, show Section 1 (Plugin Info + Version Check) only, then display: "Project not initialized — run `/shaktra:init` to set up."
- Never fail the entire dashboard because one section has missing data.

---

## Output Format

Present the dashboard as a structured report:

```
## Shaktra Dashboard

### Plugin Info
Version: 0.1.0
Status: Up to date (v0.1.0)

### Sprint Health
Sprint: S-003 — "Auth module"
Dates: 2025-01-06 → 2025-01-20 (5 days remaining)
Capacity: 21/30 points committed
Velocity trend: 18 → 21 → 24

### Story Pipeline
| Phase    | Count | Stories        |
|----------|-------|----------------|
| code     | 1     | ST-002         |
| complete | 2     | ST-001, ST-003 |

### Quality Summary
| Severity | Unresolved |
|----------|------------|
| P0       | 0          |
| P1       | 1          |
| P2       | 3          |
| P3       | 2          |
Merge status: Clear (P1: 1/2 threshold)

### Memory Health
Principles: 12 (8↑ 3~ 1↓)
Anti-patterns: 2
Procedures: 1

### Analysis Progress
Not applicable — no analysis manifest found.
```
