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
   - Identifies observations for memory consolidation (memory-curator handles promotion)
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

## Consistency Gate

**When:** After QUALITY phase passes, before MEMORY CAPTURE (Medium+ tiers only).

Verify that sw-quality wrote consistency-check observations for every briefing entry.

1. Read `.briefing.yml` — collect all `id` values from `relevant_principles` and `relevant_anti_patterns`. If briefing missing or both lists empty → skip, proceed to MEMORY CAPTURE.
2. Read `.observations.yml` — collect `principle_id` values from all `type: consistency-check` observations
3. Compare: every briefing ID must have at least one matching consistency-check
4. **All covered** → proceed to MEMORY CAPTURE
5. **Missing entries** → emit `CONSISTENCY_GATE_FAILED`, list missing IDs, return to sw-quality to write the missing checks. Max 2 attempts:

```
consistency_gate(story_dir, max_attempts=2):
  briefing_ids = load_briefing_ids(story_dir/.briefing.yml)
  IF briefing_ids is empty: RETURN PASS
  attempt = 0
  WHILE attempt < max_attempts:
    attempt += 1
    missing = briefing_ids - load_consistency_check_ids(story_dir/.observations.yml)
    IF missing is empty: RETURN PASS
    EMIT CONSISTENCY_GATE_FAILED
    spawn sw-quality(review_mode: "COMPREHENSIVE", gate: "consistency", missing_ids: missing)
  # Attempts exhausted — present missing IDs to user, proceed anyway
  RETURN PASS
```

---

## MEMORY CAPTURE

Mandatory final step — the orchestrator must not skip this regardless of tier.

1. Spawn **memory-curator** with workflow_type: "tdd", artifacts_path: story directory
2. Memory curator:
   - Reads handoff (decisions, findings, patterns, risks)
   - Reads code changes
   - Evaluates capture bar: "Would this materially change future workflow execution?"
   - Consolidates actionable insights via consolidation-guide.md (if any)
   - Sets `memory_captured: true` in handoff
3. Update handoff: set `current_phase: complete`

Note: Memory curator consolidates all observations into principles.yml, anti-patterns.yml, and procedures.yml.

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

- **Agent failure:** Retry the same agent spawn once. If retry fails: inform user with error context, do not proceed.
- **Mid-workflow cancel:** Artifacts on disk remain valid. Handoff tracks last completed phase. User resumes with `/shaktra:dev "Resume {story_id}"`.
- **Missing prerequisites:** Report the specific missing prerequisite and recommend the corrective action (`/shaktra:init`, `/shaktra:tpm enrich`, etc.). Do not attempt to create prerequisites.

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
| Consistency Gate | Skip | Skip | Required | Required |
| MEMORY | Required | Required | Required | Required |
