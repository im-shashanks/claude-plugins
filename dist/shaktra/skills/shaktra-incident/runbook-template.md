# Runbook Template

A structured operational runbook for incident response. Generated from a completed diagnosis and post-mortem to enable faster response if the same incident class recurs.

**Reference:** Severity levels follow `severity-taxonomy.md` definitions.

---

## Sections

### 1. Identification

How to recognize this incident class when it recurs.

**Symptoms:** Observable indicators — error messages, degraded behavior, user reports. Pulled from the diagnosis artifact's symptom description and triage classification.

**Log patterns:** Specific log messages, error codes, or stack trace patterns to search for. Derived from the diagnosis evidence log and reproduction steps.

**Alert triggers:** Monitoring metrics or thresholds that should fire. If none existed for this incident, document what should be created (becomes a monitoring_gap action item).

### 2. Severity Assessment

Criteria for classifying a recurrence using the P0-P3 taxonomy from `severity-taxonomy.md`.

Map conditions to severity levels:
- **P0:** When this pattern causes production downtime, data corruption, or security breach
- **P1:** When this pattern breaks major functionality or causes significant degradation
- **P2:** When this pattern affects minor features with workarounds available
- **P3:** When this pattern causes cosmetic or edge-case issues only

These map from the diagnosis severity and the conditions under which severity escalates or de-escalates.

### 3. Immediate Response

First 15 minutes after identification.

**Triage steps:** What to check first — confirm scope, assess data impact, verify the pattern matches this runbook's incident class.

**Notification:** Who to inform and when. Based on severity assessment:
- P0: Immediate escalation
- P1: Team notification within 15 minutes
- P2/P3: Standard issue tracking

**Mitigation:** Temporary measures to reduce impact while the fix is prepared. Include tradeoffs (e.g., "disable feature X — blocks 5% of users but prevents data corruption for all").

### 4. Diagnosis Shortcut

Based on the confirmed root cause, where to look first if this pattern recurs.

**Likely root cause:** The confirmed root cause from the original diagnosis (category, location, explanation).

**Where to look:** Specific files and code sections to check. Ordered by likelihood based on the original investigation.

**Confirming evidence:** How to confirm the same root cause is at play — specific test to run, value to check, log entry to find.

### 5. Resolution

**Fix approach:** Summary of the remediation (from the story and handoff). Not the full implementation — enough for someone to understand the fix strategy.

**Rollback steps:** How to revert if the fix causes issues. Based on the deployment approach and data impact assessment.

**Deployment notes:** Special considerations — feature flags, migration steps, cache invalidation, dependent service coordination.

### 6. Verification

**Tests to run:** Specific test commands and expected results. Pulled from the handoff test summary — the reproduction test plus regression tests that validate the fix.

**Smoke checks:** Manual verification steps to confirm the fix is working in the target environment. Based on the original reproduction steps, inverted (should now succeed instead of fail).

---

## Generation Process

The incident-analyst agent generates runbooks by:

1. Reading the diagnosis artifact for root cause, symptoms, reproduction steps, and evidence
2. Reading the story YAML for acceptance criteria and scope
3. Reading the handoff for test summary, fix approach, and deployment context
4. Structuring findings into the 6 runbook sections above
5. Writing the output to `.shaktra/incidents/{bug_id}/runbook.yml` following `incident-schema.md`

When `settings.incident.runbook_auto_generate` is true, runbook generation is triggered automatically as part of the post-mortem intent.
