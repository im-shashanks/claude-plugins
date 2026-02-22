# Incident Response Schemas

YAML schemas for the three incident response artifacts. All output files are written to `.shaktra/incidents/{bug_id}/`.

---

## Post-Mortem Schema

File: `.shaktra/incidents/{bug_id}/postmortem.yml`

```yaml
postmortem:
  bug_id: "BUG-###"
  story_id: "ST-###"                    # remediation story (from diagnosis)
  incident_date: "YYYY-MM-DD"
  analyst: "incident-analyst"

  timeline:
    - timestamp: "YYYY-MM-DD HH:MM"
      event: "description of what happened"
      source: "git_blame | diagnosis | handoff | manual"
    # Ordered chronologically: introduced → detected → diagnosed → fixed → verified

  root_cause_chain:
    primary:
      category: "RC-LOGIC | RC-DATA | RC-INTEG | RC-CONFIG | RC-CONCUR | RC-RESOURCE"
      location: "file:line"
      explanation: "why this was the direct cause"
    contributing_factors:
      - category: "RC-*"
        description: "what made the primary cause possible or worse"
        relationship: "enabled | amplified | delayed_detection"
    process_gaps:
      - description: "process or workflow gap that allowed the issue"
        phase: "planning | implementation | testing | review | deployment"
    environmental_factors:
      - description: "environmental condition that contributed"
        type: "configuration | infrastructure | dependency | timing"

  impact:
    duration_estimate: "how long the issue existed before detection"
    affected_scope: "components, modules, or features affected"
    data_impact: "none | read_only | write_corruption | data_loss"
    business_impact: "user-facing effect summary"
    severity: "P0 | P1 | P2 | P3"     # from diagnosis artifact

  detection_gaps:
    - gate: "plan | test | code | quality | review"
      dimension: "dimension name (from 13 quality dimensions)"
      gap: "what this gate missed and why"
    # Summary only — full analysis in detection-gap artifact

  action_items:
    - id: "AI-001"
      category: "test_gap | quality_gate_gap | process_gap | monitoring_gap"
      priority: "P0 | P1 | P2 | P3"   # from settings.incident.action_item_default_priority
      description: "specific action to prevent recurrence"
      suggested_owner: "role or team"
      effort: "trivial | small | medium | large"
```

---

## Runbook Schema

File: `.shaktra/incidents/{bug_id}/runbook.yml`

```yaml
runbook:
  bug_id: "BUG-###"
  incident_class: "short label for this type of incident"
  created_date: "YYYY-MM-DD"
  analyst: "incident-analyst"

  identification:
    symptoms:
      - "observable symptom that indicates this incident class"
    log_patterns:
      - "log message pattern or regex to search for"
    alert_triggers:
      - "monitoring alert or metric threshold"

  severity_assessment:
    criteria:
      - severity: "P0 | P1 | P2 | P3"
        condition: "when this severity applies"
    # Maps to severity-taxonomy.md definitions

  immediate_response:
    first_15_minutes:
      - step: "action to take"
        purpose: "why this step matters"
    notification:
      - role: "who to notify"
        condition: "when to notify them"
    mitigation:
      - action: "temporary mitigation step"
        tradeoff: "what this mitigation costs or limits"

  diagnosis_shortcut:
    likely_root_cause: "confirmed root cause from this incident"
    where_to_look:
      - file: "file path"
        what: "what to check"
    confirming_evidence: "how to confirm the same root cause is recurring"

  resolution:
    fix_approach: "summary of the fix (from remediation story)"
    rollback_steps:
      - "step to rollback if fix causes issues"
    deployment_notes: "special deployment considerations"

  verification:
    tests_to_run:
      - test: "test name or command"
        expected: "expected result"
    smoke_checks:
      - "manual verification step"
```

---

## Detection Gap Schema

File: `.shaktra/incidents/{bug_id}/detection-gap.yml`

```yaml
detection_gap:
  bug_id: "BUG-###"
  story_id: "ST-###"
  analyst: "incident-analyst"

  gates_passed:
    - gate: "plan | test | code | quality | review"
      passed_at: "phase when code passed this gate"
      dimensions_checked:
        - dimension: "dimension name"
          checked: true | false
          relevant: true | false        # was this dimension relevant to the root cause?
      why_missed: "explanation of why the gate did not catch the issue"

  test_gaps:
    - type: "unit | integration | edge_case | boundary | adversarial | regression"
      description: "what test was missing"
      would_have_caught: "how this test would have detected the bug"
      priority: "P0 | P1 | P2 | P3"

  quality_dimension_gaps:
    - dimension: "dimension letter and name (from 13 quality dimensions)"
      check_missed: "specific check within the dimension that was absent or insufficient"
      why_relevant: "how this dimension relates to the root cause"
      recommendation: "specific improvement to the dimension check"

  recommendations:
    - id: "REC-001"
      category: "test | quality_gate | process | monitoring | tooling"
      description: "concrete action to close this gap"
      effort: "trivial | small | medium | large"
      impact: "low | medium | high"
      priority: "P0 | P1 | P2 | P3"
```
