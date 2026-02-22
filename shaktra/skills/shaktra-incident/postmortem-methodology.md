# Post-Mortem Methodology

A structured process for blameless post-incident analysis. Transforms a completed bugfix diagnosis into organizational learning: timeline, root cause chain, impact assessment, detection gaps, and action items.

**Input:** Completed diagnosis artifact (`.shaktra/stories/diagnosis-{bug_id}.yml`), story YAML, handoff.

---

## Step 1: Timeline Reconstruction

**Goal:** Build a complete chronological record from introduction to resolution.

### Sources

| Source | What It Provides |
|---|---|
| `git blame` on root cause location | When the defect was introduced |
| Diagnosis artifact timestamps | When detected, when diagnosed |
| Handoff phase timestamps | When each TDD phase completed |
| Story creation date | When remediation began |

### Timeline Entry Format

```yaml
timeline:
  - timestamp: "YYYY-MM-DD HH:MM"
    event: "Defect introduced in commit abc1234"
    source: "git_blame"
  - timestamp: "YYYY-MM-DD HH:MM"
    event: "Bug reported — symptom: {symptom}"
    source: "manual"
  - timestamp: "YYYY-MM-DD HH:MM"
    event: "Root cause confirmed — {RC category}"
    source: "diagnosis"
  - timestamp: "YYYY-MM-DD HH:MM"
    event: "Fix verified — all tests pass"
    source: "handoff"
```

### Process

1. Run `git log --format="%H %ai %s" -- {root_cause_file}` to find the commit that introduced the defect
2. Cross-reference with diagnosis artifact `root_cause.location` and `trigger_conditions`
3. Extract handoff timestamps for remediation phases
4. Order all events chronologically
5. Calculate **time-to-detection** (introduced → reported) and **time-to-resolution** (reported → verified)

---

## Step 2: Root Cause Chain Analysis

**Goal:** Extend the single-point root cause from diagnosis into a full contributing factors chain. Diagnosis answers "what broke" — post-mortem answers "why was it possible."

### Chain Structure

```
Primary root cause (from diagnosis)
  ├── Contributing factor 1 — what enabled the primary cause
  │     └── relationship: enabled | amplified | delayed_detection
  ├── Contributing factor 2 — what made it worse
  │     └── relationship: enabled | amplified | delayed_detection
  └── Process gap — what workflow step should have caught it
        └── phase: planning | implementation | testing | review | deployment
```

### Analysis Questions

For each contributing factor, answer:
- **Enabled:** "What condition made the primary root cause possible?" (e.g., missing input validation allowed bad data to reach the logic error)
- **Amplified:** "What made the impact worse than it needed to be?" (e.g., no circuit breaker meant one failure cascaded)
- **Delayed detection:** "What prevented earlier discovery?" (e.g., tests used mocks that masked the real behavior)

### Environmental Factors

Check for conditions outside the code that contributed:
- **Configuration:** Different settings between environments
- **Infrastructure:** Resource constraints, network conditions
- **Dependency:** Upstream service behavior change
- **Timing:** Load patterns, concurrency conditions

---

## Step 3: Impact Assessment

**Goal:** Quantify the incident's impact beyond the diagnosis severity rating.

### Assessment Dimensions

| Dimension | What to Assess |
|---|---|
| Duration estimate | How long the defect existed before detection (from timeline) |
| Affected scope | Components, modules, features impacted (from blast radius) |
| Data impact | none / read_only / write_corruption / data_loss |
| Business impact | User-facing effect: degraded experience, blocked workflow, data loss |
| Severity | From diagnosis artifact — P0/P1/P2/P3 per `severity-taxonomy.md` |

### Scope Expansion

The diagnosis blast radius identifies code-level similar patterns. Impact assessment extends this to:
- **Downstream consumers** — services or components that depend on the affected code
- **Data pipelines** — data that flowed through the buggy path during the defect window
- **User segments** — which users or use cases were affected

---

## Step 4: Detection Gap Summary

**Goal:** Identify which quality gates the code passed through and what each missed. This is a summary — the full analysis lives in the detection gap artifact (see `detection-gap-framework.md`).

### Gate Review

For each quality gate in the TDD pipeline:

| Gate | Question |
|---|---|
| PLAN | Did the implementation plan account for this failure mode? |
| RED (test) | Were tests written that would have caught this? |
| GREEN (code) | Did the implementation introduce or inherit the defect? |
| QUALITY | Did the 36-check quality review flag this pattern? |
| REVIEW | Did the 13-dimension code review catch this? |

Record which gates the defective code passed, and for each: what was checked and why the root cause survived.

---

## Step 5: Action Items

**Goal:** Produce concrete, actionable items to prevent recurrence.

### Categories

| Category | What It Covers | Examples |
|---|---|---|
| `test_gap` | Missing test type or coverage | "Add boundary test for null input on payment endpoint" |
| `quality_gate_gap` | Quality dimension that should have caught this | "Add timeout check to performance dimension in quick-check" |
| `process_gap` | Workflow step that was insufficient | "Require blast radius check before merging hotfixes" |
| `monitoring_gap` | Missing observability | "Add alert for response time > 2s on checkout endpoint" |

### Action Item Format

```yaml
action_items:
  - id: "AI-001"
    category: "test_gap"
    priority: "P1"              # default from settings.incident.action_item_default_priority
    description: "Add integration test for concurrent checkout with empty cart"
    suggested_owner: "developer"
    effort: "small"
```

### Priority Assignment

- Use `settings.incident.action_item_default_priority` as the starting point
- Escalate to P0 if the gap could cause data loss or security issues
- De-escalate to P2/P3 if the gap only affects edge cases with workarounds

### Output

Each action item with `effort: small` or `trivial` is a candidate for immediate story creation. Suggest this in the completion report.
