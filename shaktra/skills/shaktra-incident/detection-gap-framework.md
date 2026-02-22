# Detection Gap Framework

A structured analysis of why existing quality gates failed to catch a production incident. Maps the root cause against every gate the code passed through, identifies specific gaps in test coverage and quality dimensions, and produces concrete recommendations.

**Reference:** Quality dimensions from `shaktra-quality`, severity from `severity-taxonomy.md`.

---

## Step 1: Quality Gate Coverage Matrix

For each gate in the TDD pipeline that the defective code passed through, map which dimensions were checked and why the root cause survived.

### Gate Analysis Template

```yaml
gates_passed:
  - gate: "plan"
    passed_at: "PLAN phase"
    dimensions_checked:
      - dimension: "correctness"
        checked: true
        relevant: true
      - dimension: "error-handling"
        checked: false
        relevant: true
    why_missed: "Plan review checked happy-path correctness but did not require error path enumeration for this function"
```

### Gates to Analyze

| Gate | What It Checks | Common Blind Spots |
|---|---|---|
| PLAN | Implementation approach, acceptance criteria coverage | Missing failure modes, incomplete edge case enumeration |
| RED (test) | Test coverage, behavioral verification | Tests share code assumptions, missing integration scenarios |
| GREEN (code) | Implementation correctness, coverage threshold | Coverage without assertion quality, mocked dependencies |
| QUALITY | 36 checks across quality dimensions | Dimension not applicable to this code path, shallow check |
| REVIEW | 13 dimensions, verification tests | Verification tests cover new code but miss interaction effects |

---

## Step 2: Test Gap Classification

Identify which types of tests were missing that would have caught the bug.

### Test Type Analysis

| Test Type | Would Have Caught? | Priority |
|---|---|---|
| **Unit** | Isolated logic error in a single function | High if RC-LOGIC |
| **Integration** | Interaction between components or services | High if RC-INTEG |
| **Edge case** | Boundary values, empty inputs, null handling | High if RC-DATA |
| **Boundary** | Off-by-one, overflow, underflow, limits | High if RC-LOGIC with numeric types |
| **Adversarial** | Malformed input, injection, fault injection | High if RC-DATA or RC-CONFIG |
| **Regression** | Previously fixed bug recurring | High if similar pattern existed before |

### Classification Process

1. Read the root cause category from the diagnosis artifact
2. For each test type, determine: would a test of this type have caught the root cause before it reached production?
3. For each "yes": describe the specific test that was missing and why it would have caught the bug
4. Assign priority based on the root cause severity and how directly the test would have detected it

---

## Step 3: Quality Dimension Gap Analysis

Map the root cause against the 13 quality dimensions (A-M) used in code review. For each dimension that was relevant to the root cause, identify what specific check was missed.

### Analysis Template

```yaml
quality_dimension_gaps:
  - dimension: "B. Error Handling"
    check_missed: "External call timeout handling — function calls upstream API without timeout or fallback"
    why_relevant: "Root cause was an unbounded external call that timed out under load"
    recommendation: "Add explicit timeout check for all external HTTP calls in error-handling dimension"
```

### Process

1. Read the 13 quality dimensions from `shaktra-quality`
2. For each dimension, ask: "Is this dimension relevant to the root cause?"
3. For each relevant dimension: "What specific check within this dimension would have caught the issue?"
4. If the dimension was checked but the issue survived: "Why was the check insufficient?"
5. Document the gap and the specific improvement needed

---

## Step 4: Recommendations

Produce concrete, actionable recommendations to close each identified gap.

### Recommendation Categories

| Category | What It Addresses | Example |
|---|---|---|
| `test` | Missing test coverage | "Add integration test for concurrent access to shared state" |
| `quality_gate` | Quality dimension improvement | "Add explicit check for unbounded external calls in performance dimension" |
| `process` | Workflow or process change | "Require blast radius assessment for all changes touching the data layer" |
| `monitoring` | Observability gap | "Add latency percentile alerting for checkout endpoint" |
| `tooling` | Tool or automation improvement | "Add mutation testing for error handling paths in CI" |

### Effort/Impact Rating

For each recommendation:

| Rating | Effort | Impact |
|---|---|---|
| Quick win | trivial/small effort | medium/high impact |
| Investment | medium/large effort | high impact |
| Nice-to-have | trivial/small effort | low impact |
| Defer | medium/large effort | low impact |

### Priority Assignment

- Recommendations that prevent P0/P1 recurrence → match incident severity
- Recommendations that improve detection speed → one level below incident severity
- Recommendations that improve process → use `settings.incident.action_item_default_priority`

### Output

Write recommendations to the detection gap artifact following `incident-schema.md`. Each recommendation becomes a candidate action item in the post-mortem.

---

## Integration with Post-Mortem

When `settings.incident.auto_detection_gap` is true, detection gap analysis runs automatically as part of the `post_mortem` intent. The detection gap findings are:

1. Summarized in the post-mortem's `detection_gaps` section
2. Written in full to the separate detection gap artifact
3. Converted to action items in the post-mortem's `action_items` section
