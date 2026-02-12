# Refactoring Pipeline

Step-by-step orchestration for the refactoring workflow. The SDM SKILL.md classifies intent and routes here when a refactoring request is detected.

---

## State Machine

```
ASSESS → FORTIFY → TRANSFORM → VERIFY → MEMORY
```

---

## Entry and Tiering

### Entry Modes

| Mode | Trigger | Target |
|---|---|---|
| Direct path | `/shaktra:dev refactor src/path/` | File or directory |
| Intent detection | "clean up", "restructure", "extract", "simplify" | Inferred from context |

### Tier Classification

| Tier | Scope | Safety Threshold | Quality Gate |
|---|---|---|---|
| **Targeted** | Single file/module, <5 files in scope | `settings.refactoring.safety_threshold` | Quick-check |
| **Structural** | Cross-cutting, 5+ files in scope | `settings.refactoring.structural_safety_threshold` | Quick-check + Comprehensive |

No story required — refactoring can be invoked directly on a file/module path.

---

## Handoff Initialization

Create `refactoring-handoff.yml` at `.shaktra/refactoring/<target-name>/`:

```yaml
target: <file_or_module_path>
tier: <targeted | structural>
current_phase: pending
completed_phases: []
memory_captured: false
```

---

## Phase: ASSESS

### Agent: SW Engineer (mode: refactoring-plan)

Spawn sw-engineer with refactoring-plan mode:

```
You are the shaktra-sw-engineer agent operating in refactoring-plan mode.

Target: {target_path}
Settings: {settings_path}
Decisions: {decisions_path}
Lessons: {lessons_path}

Assess the target for code smells using refactoring-smells.md. For each detected smell:
1. Record the smell ID, location, and severity
2. Propose a transformation from refactoring-transforms.md
3. Order transformations by risk (lowest first)

Measure baseline metrics: test count, coverage, files in scope.
Write assessment to refactoring-handoff.yml.
```

### Output

SW Engineer populates `assessment` in handoff:
- `smells_detected` — list of smells with IDs, locations, severity
- `proposed_transforms` — ordered list of transformations
- `baseline_metrics` — test count, coverage, files in scope

### Phase Transition Guard

- `assessment.smells_detected` is non-empty
- At least one transform proposed
- If no smells detected: report to user, skip remaining phases

Update handoff: append "assess" to `completed_phases`, set `current_phase: assess`.

---

## Phase: FORTIFY

### Agent: Test Agent (mode: characterization)

Check coverage against the tier's safety threshold. If insufficient, write characterization tests.

```
You are the shaktra-test-agent agent operating in characterization mode.

Target: {target_path}
Refactoring handoff: {handoff_path}
Settings: {settings_path}
Safety threshold: {tier_safety_threshold}%
Max characterization tests: {settings.refactoring.max_characterization_tests}

1. Run existing tests and measure coverage for the target files.
2. If coverage >= safety threshold: record metrics, proceed.
3. If coverage < safety threshold: write characterization tests that capture current behavior.
   - Characterization tests verify WHAT the code does now (not what it should do).
   - Focus on public API behavior, boundary conditions, and side effects.
   - Limit to max_characterization_tests.
4. Re-run tests and verify coverage meets threshold.
5. Update refactoring-handoff.yml with fortify summary.
```

### Force Mode

If coverage cannot meet the safety threshold even after characterization tests:

1. Inform user: "Coverage for {target} is {actual}% (threshold: {required}%). Characterization tests added {N} but gap remains."
2. Offer force mode: "Proceed with acknowledged risk? Each transformation will require manual approval."
3. If user accepts: set `fortify.force_mode: true` in handoff
4. If user declines: stop refactoring

### Phase Transition Guard

- `fortify.safety_threshold_met == true` OR `fortify.force_mode == true`

Update handoff: append "fortify" to `completed_phases`, set `current_phase: fortify`.

---

## Phase: TRANSFORM

### Agent: Developer (mode: refactor)

Apply transformations one at a time following the atomic protocol from `refactoring-transforms.md`.

```
You are the shaktra-developer agent operating in refactor mode.

Target: {target_path}
Refactoring handoff: {handoff_path}
Settings: {settings_path}

Apply each transformation from assessment.proposed_transforms in order:
1. Pre-check: verify all tests pass
2. Apply ONE transformation (follow steps in refactoring-transforms.md)
3. Post-check: run all tests
4. If tests pass: log as "applied" in handoff transforms
5. If tests fail: REVERT the transformation, log as "reverted", report reason
6. Proceed to next transformation

If force_mode is true: present each transformation to user for approval before applying.
Never batch multiple transformations. One at a time, tests between each.
```

### Revert Protocol

On test failure after a transformation:
1. Revert all changes from that transformation (git checkout the affected files)
2. Verify tests pass again after revert
3. Log the transformation as `reverted` with reason
4. Ask user: "Transformation {id} ({description}) caused test failures. Skip and continue, or abort refactoring?"
5. If skip: proceed to next transformation
6. If abort: set `current_phase: failed`, stop

### Phase Transition Guard

- All transforms either `applied`, `reverted`, or `skipped`

Update handoff: append "transform" to `completed_phases`, set `current_phase: transform`.

---

## Phase: VERIFY

### Agent: SW Quality (mode: REFACTOR_VERIFY)

Confirm the refactoring preserved behavior and improved quality.

```
You are the shaktra-sw-quality agent operating in REFACTOR_VERIFY mode.

Target: {target_path}
Refactoring handoff: {handoff_path}
Settings: {settings_path}

Verify:
1. All tests pass (run full suite, not just target tests)
2. Coverage has not decreased (compare against baseline_metrics.coverage)
3. No new P0/P1 findings introduced
4. Smell count reduced (compare against assessment.smells_detected count)
5. Code metrics improved or neutral (not degraded)

Emit REFACTOR_PASS or REFACTOR_BLOCKED with findings.
```

### Structural Tier Additional Checks

For structural refactoring (5+ files), run comprehensive review in addition to REFACTOR_VERIFY:
- Architecture dimension: boundaries preserved
- Dependency dimension: no new circular dependencies introduced
- Naming dimension: consistent with existing conventions

### Phase Transition Guard

- `verify.all_tests_green == true`
- `verify.coverage_change >= 0`

Update handoff: append "verify" to `completed_phases`, set `current_phase: verify`.

---

## MEMORY CAPTURE

Mandatory final step.

```
You are the shaktra-memory-curator agent.

Workflow type: refactor
Artifacts path: {refactoring_dir}

Extract lessons: which smells were found and how they were resolved.
Capture patterns that should be avoided in future code.
Append to .shaktra/memory/lessons.yml (if actionable).
Set memory_captured: true in refactoring-handoff.yml.
```

Update handoff: set `current_phase: complete`.

---

## Completion Report

```
## Refactoring Complete

**Target:** {target_path}
**Tier:** {targeted | structural}

### Assessment
- Smells detected: {count}
- Transformations proposed: {count}

### Results
- Applied: {count}
- Reverted: {count} (test failures)
- Skipped: {count} (user decision or force-mode rejection)

### Quality
- Tests: all green
- Coverage: {before}% → {after}% (delta: {change})
- Smells resolved: {resolved} of {total}

### Transformations Applied
| # | Transform | Target Smell | Status |
|---|-----------|-------------|--------|
{for each transform: id, description, smell, status}

### Next Step
- {recommendation — e.g., "Review changes and commit" or "Consider structural refactoring for remaining smells"}
```

---

## Guard Tokens

| Token | When |
|---|---|
| `REFACTOR_PASS` | Verification passed — behavior preserved, metrics improved |
| `REFACTOR_BLOCKED` | Verification failed — tests broken, coverage decreased, or P0/P1 found |
| `TRANSFORM_REVERTED` | A transformation caused test failures and was rolled back |
| `FORCE_MODE_ACTIVE` | User acknowledged risk — transformations require manual approval |
