# TPM Workflow Templates

Step-by-step orchestration for each TPM sub-intent. The TPM SKILL.md classifies intent and routes to the appropriate workflow here.

---

## Quality Loop Patterns

### Single Artifact Quality Loop

Used for design docs (typically 1 artifact). File-based findings handoff keeps TPM context lean.

```
quality_loop(artifact_path, artifact_type, creator_agent, max_attempts=3):
  attempt = 0
  WHILE attempt < max_attempts:
    attempt += 1
    result = spawn tpm-quality(artifact_path, artifact_type, round=attempt)
    → agent writes findings to .quality.yml if BLOCKED
    → returns ONE LINE: "QUALITY_PASS: <id>" or "QUALITY_BLOCKED: <id>"

    IF result starts with "QUALITY_PASS":
      RETURN QUALITY_PASS

    IF result starts with "QUALITY_BLOCKED":
      spawn creator_agent.fix(artifact_path)
      → agent reads findings from .quality.yml, fixes, deletes file
      CONTINUE

  # Loop exhausted
  EMIT MAX_LOOPS_REACHED
  Present to user: findings are in the .quality.yml file for reference
  RETURN QUALITY_BLOCKED

  # CLEANUP — delete any remaining .quality.yml for this artifact
```

### Parallel Batch Quality Review

Used for stories (multiple artifacts). Spawns all reviews/fixes in parallel per round. File-based findings handoff keeps TPM context to one-line verdicts only.

**Findings files** (ephemeral — TPM cleans up after loop): `.shaktra/stories/ST-NNN.quality.yml` or `.shaktra/designs/{name}-design.quality.yml`

```
parallel_quality_review(story_paths, max_rounds=3):
  pending = all story_paths
  passed = []

  FOR round IN 1..max_rounds:
    IF pending is empty: BREAK

    # REVIEW BATCH — spawn ALL in parallel (one Task per story)
    FOR EACH path IN pending — PARALLEL Task() calls in single response:
      spawn tpm-quality(path, "story", round)
      → agent reviews story, writes findings to .quality.yml if BLOCKED
      → returns ONE LINE: "QUALITY_PASS: ST-NNN" or "QUALITY_BLOCKED: ST-NNN"

    # COLLECT — TPM reads one-line verdicts (minimal context)
    newly_passed = stories with QUALITY_PASS
    blocked = stories with QUALITY_BLOCKED
    passed += newly_passed

    IF blocked is empty: BREAK
    IF round == max_rounds:
      EMIT MAX_LOOPS_REACHED
      Present blocked stories to user (findings are in .quality.yml files for reference)
      BREAK

    # FIX BATCH — spawn ALL in parallel (one Task per blocked story)
    FOR EACH story IN blocked — PARALLEL Task() calls in single response:
      spawn scrummaster.fix(story_path)
      → agent reads findings from .quality.yml
      → fixes story
      → deletes .quality.yml after fixing

    pending = [paths of previously blocked stories]

  # CLEANUP — delete any remaining *.quality.yml files
  Delete all .shaktra/stories/*.quality.yml and .shaktra/designs/*.quality.yml

  RETURN passed, blocked
```

---

## Workflow: Full

Complete TPM workflow — design through sprint planning. This is the default for new features.

### Phase 1 — Design

1. Read `.shaktra/settings.yml` for project context
2. Spawn **architect** with analysis path (if brownfield) — architect reads PRD and architecture from fixed paths `.shaktra/prd.md` and `.shaktra/architecture.md`
3. Handle architect response:
   - **If `GAPS_FOUND`:** Spawn **product-manager** (mode: gaps) with the gap questions
     - For each PM answer: if `PM_ESCALATE`, present the question to the user and await their response
     - Re-spawn **architect** with gap answers
     - Repeat until no gaps remain (max 3 gap rounds)
   - **If design doc returned:** Continue to quality review
4. Run quality loop: `quality_loop(design_doc_path, "design", architect)`
5. If `QUALITY_PASS`: proceed to Phase 2
6. If `QUALITY_BLOCKED` after max loops: present to user, await resolution

### Phase 2 — Stories

1. Spawn **scrummaster** (mode: create) with the approved design doc
   - Scrummaster MUST create stories as YAML files at `.shaktra/stories/ST-<NNN>.yml`
   - Stories use the YAML structure from `story-schema.md` with tier-appropriate fields
   - Do NOT write Markdown (.md) — stories are always YAML (.yml)
2. Run parallel batch quality review: `parallel_quality_review(all_story_paths)`
3. If any story blocked after max rounds: present blocked stories to user (findings in `.quality.yml` files)
4. Collect all passing stories for Phase 3

### Phase 3 — PM Analysis

1. Spawn **product-manager** (mode: coverage) with stories directory — PM reads PRD from `.shaktra/prd.md`
   - If coverage < 100%: present gap report to user
   - User decides: create additional stories or accept gaps
   - If additional stories needed: return to Phase 2 for the new stories
2. Spawn **product-manager** (mode: rice) with stories directory
   - PM returns RICE results: scored stories, classifications, sprint goal suggestion
3. If `settings.sprints.enabled`:
   - Spawn **scrummaster** (mode: sprint-allocation) with rice_results and sprint_mode: `full`
   - Scrummaster writes `.shaktra/sprints.yml`
   - Present PM's sprint goal suggestion to user. If user provides alternative: update `current_sprint.goal` in `.shaktra/sprints.yml`

### Phase 4 — Memory

1. Spawn **memory-curator** with workflow_type: "tpm-planning", artifacts_path: stories directory
2. This step is mandatory — every full workflow ends with memory capture

### Completion

Present summary to user:
- Design doc path
- Stories created (count, total points)
- Quality review results
- Coverage report (% and any gaps)
- Quick Wins and Big Bets identified
- Sprint allocation (if enabled)
- Unresolved items (if any)

---

## Workflow: Design Only

Create a design doc without proceeding to stories.

1. Execute Full Workflow Phase 1 (Design)
2. Execute Full Workflow Phase 4 (Memory)
3. Present design doc path and quality results

---

## Workflow: Stories Only

Create stories from an existing design doc. Requires an approved design doc.

**Prerequisite:** Design doc must exist at `.shaktra/designs/`. If not found, inform user and recommend running the design workflow first.

1. Locate the design doc (user-specified path or search `.shaktra/designs/`)
2. Execute Full Workflow Phase 2 (Stories)
3. Execute Full Workflow Phase 3 (PM Analysis — includes sprint goal review if sprints enabled)
4. Execute Full Workflow Phase 4 (Memory)
5. Present stories summary, coverage, and sprint allocation

---

## Workflow: Enrich

Enrich existing sparse stories with tier-appropriate detail.

1. Locate story files to enrich (user-specified paths or search `.shaktra/stories/`)
2. Read `.shaktra/settings.yml` for project context
3. Spawn **scrummaster** (mode: enrich) with story paths
   - Single story: one spawn
   - Batch (multiple stories): scrummaster processes sequentially with batch Final Verification
4. Run parallel batch quality review: `parallel_quality_review(enriched_story_paths)`
5. Present enriched stories to user for approval before writing
6. On user approval: write final versions to `.shaktra/stories/`
7. Spawn **memory-curator** with workflow_type: "story-enrichment"

---

## Workflow: Hotfix

Fast path for trivial fixes. Produces a single Trivial-tier story YAML file with minimal overhead.

1. Read `.shaktra/settings.yml` for project context
2. Spawn **scrummaster** (mode: create) with user's hotfix description
   - Scrummaster MUST create a single Trivial-tier story as a YAML file at `.shaktra/stories/ST-<NNN>.yml`
   - The file MUST use the YAML structure from `story-schema.md` (Trivial tier: id, title, description, tier, metadata)
   - Do NOT write Markdown (.md) — stories are always YAML (.yml)
3. Single quality pass — spawn **tpm-quality** once (no loop, no retry)
   - If `QUALITY_PASS`: present to user for confirmation
   - If `QUALITY_BLOCKED`: present findings to user (hotfixes shouldn't fail quality, but if they do, user decides)
4. On user confirmation: verify `.shaktra/stories/ST-<NNN>.yml` exists and is valid YAML
5. Spawn **memory-curator** with workflow_type: "tpm-hotfix", artifacts_path: story directory
6. Recommend next step: `/shaktra:dev` to implement the hotfix

---

## Workflow: Sprint

Plan or re-plan sprint allocation for existing stories.

**Prerequisite:** Stories must exist in `.shaktra/stories/`. If none found, inform user.

### Phase 1 — RICE Prioritization

1. Spawn **product-manager** (mode: rice) with stories directory
2. PM returns RICE results: scored stories, classifications, sprint goal suggestion

### Phase 2 — Sprint Allocation

1. Determine sprint_mode:
   - If `.shaktra/sprints.yml` has no current_sprint or current_sprint is null: `full` (first-time planning)
   - If user says "re-prioritize" or "plan next sprint": `current`
   - If user says "replan all sprints": `full`
2. Spawn **scrummaster** (mode: sprint-allocation) with:
   - rice_results from Phase 1
   - sprint_mode determined above
3. Scrummaster writes updated `.shaktra/sprints.yml`

### Phase 3 — Sprint Goal Review

1. Present the PM's sprint goal suggestion to the user
2. If user provides alternative goal: TPM updates `current_sprint.goal` in `.shaktra/sprints.yml`
3. If user accepts: proceed

### Phase 4 — Memory

1. Spawn **memory-curator** with workflow_type: "sprint-planning"

### Completion

Present sprint summary:
- Sprint ID and goal
- Committed stories with points (highlight Quick Wins and Big Bets)
- Capacity: committed_points / capacity_points
- Velocity trend (if history exists)
- Backlog: remaining stories count and total points
- Recommend: `/shaktra:dev {first_story_id}` to begin implementation

---

## Workflow: Close Sprint

Close the current sprint, record velocity (including partial completion), and move incomplete stories to the backlog.

**Prerequisite:** `.shaktra/sprints.yml` must exist with a `current_sprint`. If missing, inform user.

1. Spawn **scrummaster** (mode: close-sprint)
   - Scrummaster reads `.shaktra/sprints.yml` and all story handoffs in `.shaktra/stories/`
   - Determines completed vs incomplete stories based on handoff `current_phase == "complete"`
   - Records velocity: `planned_points` (committed) and `completed_points` (sum of completed story points)
   - Appends velocity entry to `velocity.history`, recalculates `average` and `trend`
   - Moves incomplete stories to `backlog` with their existing priority
   - Clears `current_sprint` (or advances to next planned sprint if exists)
   - Writes updated `.shaktra/sprints.yml`
2. Spawn **memory-curator** with workflow_type: "sprint-close"

### Completion

Present sprint close summary:
- Sprint ID that was closed
- Completed: {N} stories, {points} points
- Incomplete: {N} stories, {points} points (moved to backlog)
- Velocity: {completed_points}/{planned_points} ({percentage}%)
- Updated velocity trend
- Recommend: "plan next sprint" or `/shaktra:tpm sprint` to plan the next sprint

---

## Error Handling

### Agent Failure

If a spawned agent fails (crashes, produces no output, or returns malformed output):
1. Retry the same agent spawn once
2. If retry fails: inform user with the error context, do not proceed with the workflow

### Missing Prerequisites

If a workflow requires artifacts that don't exist (e.g., stories workflow without a design doc):
1. Check for the artifact in the expected location
2. If not found: inform user what's missing and which workflow to run first
3. Do not attempt to create prerequisites automatically — each workflow has its scope

### Mid-Workflow Cancellation

If the user cancels mid-workflow:
1. Any artifacts already written to disk remain (they're valid intermediate state)
2. Report what was completed and what remains
3. The user can resume by running the appropriate sub-workflow (e.g., stories-only after design-only)

### Missing Settings

If `.shaktra/settings.yml` doesn't exist: inform user to run `/shaktra:init` first. Do not proceed — settings are required for tier detection and threshold evaluation.
