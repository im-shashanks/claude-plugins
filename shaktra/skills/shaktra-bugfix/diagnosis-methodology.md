# Bug Diagnosis Methodology

A structured 5-step root cause analysis for the bug-diagnostician agent. This methodology transforms vague bug reports into confirmed root causes with blast radius assessment.

## Step 1: Reproduce

**Goal:** Confirm the bug exists and create a minimal reproduction.

### Process

1. **Understand the report** — extract symptom, expected behavior, actual behavior, environment context
2. **Find or create a failing test** — a test that demonstrates the bug is the gold standard
3. **Minimize** — strip away unrelated code/data until the reproduction is the smallest possible case
4. **Document** — record exact steps, inputs, and observed output

### Reproduction Checklist

- [ ] Bug confirmed on current codebase (not already fixed)
- [ ] Failing test written that demonstrates the bug
- [ ] Reproduction is minimal (no unnecessary setup or data)
- [ ] Environment conditions documented (if environment-specific)

**If you cannot reproduce:** Document what was tried, note the reproduction gap, and flag for user input. Do not proceed to Step 2 without reproduction evidence.

---

## Step 2: Hypothesize

**Goal:** Generate candidate root causes across 6 categories. Breadth matters — premature narrowing misses the real cause.

### Root Cause Categories

| Category | ID | Examples | Typical Evidence |
|----------|-----|---------|-----------------|
| Logic error | RC-LOGIC | Wrong condition, off-by-one, missing case, inverted boolean, wrong operator | Test with boundary value fails |
| Data error | RC-DATA | Wrong type, missing validation, stale data, null/undefined, encoding | Inspect value at failure point |
| Integration error | RC-INTEG | API contract mismatch, schema drift, dependency behavior change | Works in isolation, fails integrated |
| Configuration error | RC-CONFIG | Wrong setting, environment-specific, missing config, wrong defaults | Works in one environment, fails in another |
| Concurrency error | RC-CONCUR | Race condition, deadlock, ordering assumption, shared state corruption | Intermittent, timing-dependent |
| Resource error | RC-RESOURCE | Leak, exhaustion, timeout, unbounded growth, connection pool depletion | Worsens over time or under load |

### Hypothesis Template

For each plausible hypothesis:

```yaml
- category: RC-LOGIC | RC-DATA | RC-INTEG | RC-CONFIG | RC-CONCUR | RC-RESOURCE
  hypothesis: "One sentence — what could cause this?"
  predictions: ["If true, we would also see...", "If true, this test would..."]
  evidence_needed: "What to check to confirm or eliminate"
  confidence: low | medium | high
```

Generate at least 2 hypotheses. Prefer breadth — the obvious guess is often wrong.

---

## Step 3: Gather Evidence

**Goal:** Systematically confirm or eliminate each hypothesis.

### Evidence Collection Techniques

| Technique | When to Use | How |
|-----------|------------|-----|
| **Trace execution** | Logic/data errors | Read code path from entry point to failure, noting state at each step |
| **Inspect state** | Data errors | Add assertions or logging at failure point, check variable values |
| **Git history** | Recent regressions | `git log --oneline -20 -- <file>`, `git blame <file>` around failure point |
| **Dependency check** | Integration errors | Check recent version changes, API docs, changelogs |
| **Config diff** | Environment-specific | Compare configs across environments where bug does/doesn't occur |
| **Timing analysis** | Concurrency errors | Check for unprotected shared state, missing locks, async ordering |
| **Resource monitoring** | Resource errors | Check for unclosed connections, growing collections, missing cleanup |

### Evidence Log

For each hypothesis, record:

```yaml
- hypothesis_ref: "RC-LOGIC-1"
  evidence_for: ["specific observation supporting this hypothesis"]
  evidence_against: ["specific observation contradicting this hypothesis"]
  status: confirmed | eliminated | insufficient_evidence
```

**Discipline:** Eliminate hypotheses explicitly. Do not just chase the first plausible one.

---

## Step 4: Isolate Root Cause

**Goal:** Confirm the root cause with three tests of understanding.

### Confirmation Criteria

All three must be true:

1. **WHY** — You can explain the causal chain from root cause to observed symptom
2. **WHEN** — You can predict exactly which inputs/conditions trigger the bug
3. **PROOF** — You can demonstrate with a test (the Step 1 failing test, refined if needed)

### Root Cause Statement

```yaml
root_cause:
  category: RC-LOGIC | RC-DATA | RC-INTEG | RC-CONFIG | RC-CONCUR | RC-RESOURCE
  location: "file:line"
  explanation: "Complete causal chain — why the bug occurs"
  trigger_conditions: "Exact conditions under which it manifests"
  proof_test: "Test name or description that demonstrates the bug"
```

**If multiple root causes:** Identify the primary (fixing it eliminates the symptom) vs contributing (fixing it reduces severity but doesn't eliminate). Contributing causes become blast radius items.

---

## Step 5: Blast Radius Assessment

**Goal:** Find every instance of the same pattern. A bug found once likely exists elsewhere.

### Search Dimensions

**Similar patterns:** Search the codebase for the same anti-pattern that caused this bug.

```yaml
similar_patterns:
  - file: "path/to/file"
    line: N
    description: "Same pattern — [what it is and why it's vulnerable]"
    risk: low | medium | high
```

Search strategies by category:
- **RC-LOGIC:** Grep for the same operator/condition pattern in related functions
- **RC-DATA:** Grep for the same type assumption or missing validation
- **RC-INTEG:** Check all consumers of the same API/interface
- **RC-CONFIG:** Check all config references for the same key
- **RC-CONCUR:** Check all shared state access points
- **RC-RESOURCE:** Check all resource acquisition points for matching cleanup

**Affected consumers:** Components that depend on the buggy behavior.

```yaml
affected_consumers:
  - component: "name"
    dependency: "how it depends on the buggy code"
    impact: "what happens when the bug is fixed — could this break?"
```

**Masking tests:** Tests that pass but don't actually verify correct behavior.

```yaml
masking_tests:
  - test: "test name or file"
    issue: "why this test passes despite the bug"
    recommendation: "how to strengthen this test"
```

### Output: Blast Radius Summary

Each similar pattern with `risk: medium+` becomes a **separate story** recommendation. The diagnostician does not create stories directly — it recommends them to the orchestrator.

---

## Triage Classification

Before beginning the 5-step process, classify the bug:

### Symptom Type

| Type | Description | Typical Categories |
|------|------------|-------------------|
| crash | Application terminates unexpectedly | RC-LOGIC, RC-DATA, RC-RESOURCE |
| wrong_result | Output is incorrect but application continues | RC-LOGIC, RC-DATA, RC-INTEG |
| performance | Degraded response time or throughput | RC-RESOURCE, RC-LOGIC, RC-DATA |
| data_corruption | Stored data is incorrect or inconsistent | RC-DATA, RC-CONCUR, RC-INTEG |
| security | Vulnerability or unauthorized access | RC-LOGIC, RC-DATA, RC-CONFIG |

### Reproducibility

| Level | Description | Investigation Impact |
|-------|------------|---------------------|
| always | Every execution with given inputs | Standard 5-step process |
| intermittent | Some executions, same inputs | Prioritize RC-CONCUR, RC-RESOURCE |
| environment | Only in specific environments | Prioritize RC-CONFIG, RC-INTEG |
| data_specific | Only with specific data patterns | Prioritize RC-DATA, RC-LOGIC |

### Severity Mapping

Bug severity maps to story tier for remediation:
- **P0** (production down, data corruption, security breach) → Large story
- **P1** (major feature broken, significant degradation) → Medium story
- **P2** (minor feature issue, workaround exists) → Small story
- **P3** (cosmetic, edge case, minor inconvenience) → Trivial story
