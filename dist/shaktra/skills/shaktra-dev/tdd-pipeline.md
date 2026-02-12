# TDD Pipeline

Step-by-step orchestration for the TDD workflow. The SDM SKILL.md classifies intent and routes here.

---

## Quality Loop Pattern

Reusable pattern used at every gate. Referenced as "run quality loop" below.

```
quality_loop(artifact_paths, review_mode, gate, creator_agent, max_attempts=3):
  attempt = 0
  prior_findings = None

  WHILE attempt < max_attempts:
    attempt += 1
    result = spawn sw-quality(artifact_paths, review_mode, gate, prior_findings)

    IF result == CHECK_PASSED or result == QUALITY_PASS:
      RETURN PASS

    IF result == CHECK_BLOCKED or result == QUALITY_BLOCKED:
      prior_findings = result.findings
      spawn creator_agent.fix(findings=result.findings)
      CONTINUE

  # Loop exhausted
  EMIT MAX_LOOPS_REACHED
  Present to user:
    - all unresolved findings
    - number of fix attempts made
    - recommendation: manual review needed
  RETURN BLOCKED

After loop returns (PASS or BLOCKED):
  Append result.findings to handoff.quality_findings (set gate field to current gate name).
  Mark prior findings from this gate as resolved: true if they no longer appear.
```

---

## Pre-Flight Checks

Run all three before entering the pipeline. Any failure blocks the pipeline.

### 1. Language Config Check

Verify `.shaktra/settings.yml` has `language`, `test_framework`, and `coverage_tool` set.

**If missing:** "Project language config not set. Run `/shaktra:init` or update `.shaktra/settings.yml` with language, test_framework, coverage_tool." Stop.

### 2. Story Dependency Check

Read the story's `metadata.blocked_by` field (if present). Check if blocking stories are complete (their `metadata.status` is `"done"`).

**If unresolved:** "Story {id} is blocked by {blocker_id} (status: {status}). Complete blocking stories first." Stop.

### 3. Story Quality Guard

Auto-detect tier based on story complexity and scope (using `story-tiers.md` logic). Check whether the story has all required fields for the detected tier.

**If sparse:** "Story {id} is sparse ({have} of {need} required fields for {tier} tier). Missing: {field_list}. Run: `/shaktra:tpm enrich {id}`." Stop.

**If Trivial tier:** Note that `hotfix_coverage_threshold` from settings applies.

---

## Handoff Initialization

Before entering the pipeline, create `handoff.yml` at `.shaktra/stories/<story_id>/handoff.yml` with identity fields:

```yaml
story_id: <story_id>
tier: <detected_tier>
current_phase: pending
completed_phases: []
quality_findings: []
important_decisions: []
memory_captured: false
```

If `handoff.yml` already exists (resume scenario), skip this step — the existing state is preserved.

---

## Phase: PLAN

### Steps

1. Spawn **sw-engineer** with story path, settings, decisions, lessons
2. SW engineer produces `implementation_plan.md` + populates `handoff.plan_summary`
3. **If tier >= Medium:** Run quality loop:
   - `quality_loop([plan_path], "PLAN_REVIEW", "plan", sw-engineer)`
   - If BLOCKED after max loops: present to user, await resolution
4. Update handoff: append "plan" to `completed_phases`, set `current_phase: plan`

### Phase Transition Guard

- `plan_summary` must be populated
- `test_plan.test_count > 0`
- Trivial tier: skip this guard (plan is minimal)

---

## BRANCH CREATION

After PLAN passes, before RED:

1. Spawn **developer** (mode: "branch") with story path
2. Branch created: `feat/` | `fix/` | `chore/` from story scope + title
3. No commits — branch only

---

## Phase: RED (Tests)

### Steps

1. Spawn **test-agent** with story, plan, handoff
2. Test agent writes tests, runs suite, validates failure reasons:
   - Valid failures (ImportError, AttributeError, NotImplementedError): proceed
   - Invalid failures (SyntaxError, TypeError, NameError): test agent fixes and re-runs
3. Test agent updates `handoff.test_summary`
4. Run quality loop:
   - `quality_loop(test_files, "QUICK_CHECK", "test", test-agent)`
   - If BLOCKED: test agent fixes findings, sw-quality re-reviews
5. Update handoff: append "tests" to `completed_phases`, set `current_phase: tests`

### Phase Transition Guard

- `test_summary.all_tests_red == true`
- All tests fail for valid reasons
- Trivial tier: skip RED (no tests required before code)

Guard token: If test suite passes (no failures), emit `TESTS_NOT_RED` → block GREEN.

---

## Phase: GREEN (Code)

### Steps

1. Spawn **developer** (mode: "implement") with story, plan, tests, handoff, settings
2. Developer implements code following plan order, runs tests incrementally
3. Developer runs coverage check against tier threshold
4. Developer updates `handoff.code_summary`
5. Run quality loop:
   - `quality_loop(modified_files, "QUICK_CHECK", "code", developer)`
   - If BLOCKED: developer fixes findings, sw-quality re-reviews
6. Update handoff: append "code" to `completed_phases`, set `current_phase: code`

### Phase Transition Guard

- `code_summary.all_tests_green == true`
- `code_summary.coverage >= tier_threshold` (read from settings)

Guard tokens:
- If tests still failing: emit `TESTS_NOT_GREEN` → return to developer
- If coverage below threshold: emit `COVERAGE_GATE_FAILED` → return to developer

---

## Phase: QUALITY (Final)

### Steps

1. Spawn **sw-quality** (mode: "COMPREHENSIVE") with all code and test files, handoff, settings
2. SW quality runs full review:
   - Executes tests, verifies coverage
   - Applies dimensions A-M + N (Plan Adherence)
   - Identifies decisions to promote (orchestrator writes to `.shaktra/memory/decisions.yml`)
   - Checks cross-story consistency
   - For Thorough tier: expanded review (architecture, performance, dependencies)
3. Run quality loop:
   - `quality_loop(all_files, "COMPREHENSIVE", "quality", developer)`
   - If BLOCKED: developer fixes, sw-quality re-reviews
4. Update handoff: append "quality" to `completed_phases`, set `current_phase: quality`

### Tier Behavior

- **Trivial/Small:** Skip QUALITY phase entirely. Code gate is the final gate.
- **Medium:** Standard comprehensive review.
- **Thorough (Large):** Comprehensive + expanded review.

---

## MEMORY CAPTURE

Mandatory final step — the orchestrator must not skip this regardless of tier.

1. Spawn **memory-curator** with workflow_type: "tdd", artifacts_path: story directory
2. Memory curator:
   - Reads handoff (decisions, findings, patterns, risks)
   - Reads code changes
   - Evaluates capture bar: "Would this materially change future workflow execution?"
   - Writes actionable insights to `.shaktra/memory/lessons.yml` (if any)
   - Sets `memory_captured: true` in handoff
3. Update handoff: set `current_phase: complete`

Note: `decisions.yml` is already updated during QUALITY phase. Memory curator handles lessons only.

---

## SPRINT STATE UPDATE

After MEMORY CAPTURE, if `settings.sprints.enabled` is true:

1. Read `.shaktra/sprints.yml`
2. If the completed story is in `current_sprint.stories`:
   - Update the story's `metadata.status` to `"done"` in the story file
   - Track completed points: add story points to sprint velocity record
3. If all stories in `current_sprint` are done:
   - Move current sprint to `velocity.history` with `planned_points` and `completed_points`
   - Recalculate `velocity.average` and `velocity.trend` per sprint-schema.md formulas
   - Set `current_sprint` to null (next sprint workflow will create the next sprint)
4. Write updated `.shaktra/sprints.yml`

This step is skipped if sprints are not enabled or the story is not in the current sprint.

---

## Phase Resume Logic

When a user resumes a story (`/shaktra:dev "Resume ST-001"`):

1. Read `handoff.yml` at `.shaktra/stories/<story_id>/handoff.yml`
2. Check `current_phase` and `completed_phases`
3. Skip completed phases — enter the pipeline at the next incomplete phase
4. All prior state (plan_summary, test_summary, code_summary) is preserved in handoff

Resume entry points:
- `completed_phases: []` → start at PLAN
- `completed_phases: [plan]` → start at BRANCH (if no branch) or RED
- `completed_phases: [plan, tests]` → start at GREEN
- `completed_phases: [plan, tests, code]` → start at QUALITY
- `completed_phases: [plan, tests, code, quality]` → start at MEMORY CAPTURE

---

## Error Handling

### Agent Failure

If a spawned agent fails (crashes, no output, malformed output):
1. Retry the same agent spawn once
2. If retry fails: inform user with error context, do not proceed

### Mid-Workflow Resume

If the user cancels mid-phase:
1. Artifacts written to disk remain valid
2. Handoff tracks the last completed phase
3. User resumes with `/shaktra:dev "Resume {story_id}"`

### Missing Prerequisites

If the story doesn't exist, settings are missing, or dependencies are unresolved:
1. Report the specific missing prerequisite
2. Recommend the corrective action (`/shaktra:init`, `/shaktra:tpm enrich`, etc.)
3. Do not attempt to create prerequisites

---

## Tier-Aware Gate Matrix

Summary of which gates activate per tier (from `story-tiers.md`):

| Phase/Gate | Trivial | Small | Medium | Large |
|---|---|---|---|---|
| PLAN | Minimal | Minimal | Full + review | Full + review |
| BRANCH | Yes | Yes | Yes | Yes |
| RED | Skip | Required | Required | Required |
| RED quality gate | Skip | Quick-check | Quick-check | Quick-check |
| GREEN | Required | Required | Required | Required |
| GREEN quality gate | Quick-check | Quick-check | Quick-check | Quick-check |
| QUALITY | Skip | Skip | Comprehensive | Comprehensive + expanded |
| MEMORY | Required | Required | Required | Required |
