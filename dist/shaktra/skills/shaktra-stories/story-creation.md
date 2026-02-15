# Story Creation & Enrichment

Processes for creating stories from design docs and enriching sparse stories. Both modes produce tier-compliant, test-first stories that pass the Final Verification Loop.

## Mode: CREATE

Create stories from an approved design document. Follow steps 1-7 in order.

### Step 1 — Load Context

Read the following before creating any story:
- The approved design document
- `story-schema.md` — field definitions per tier
- `story-tiers.md` — tier detection logic
- `.shaktra/memory/decisions.yml` — prior decisions that constrain design choices
- `.shaktra/settings.yml` — project type, language, thresholds

### Step 2 — Decompose into Story Boundaries

Map design document sections to stories. Each story must have a single scope — one `scope` value from the allowed list in `story-schema.md`. If a design section maps to multiple scopes, split into multiple stories.

Ordering: infrastructure and dependency stories first, then feature stories, then integration stories.

### Step 3 — Detect Tier Per Story

Apply the auto-detection logic from `story-tiers.md` to each story. Record the detected tier. The tier determines which fields are required — see `story-schema.md` for field accumulation rules.

### Step 4 — Write test_specs FIRST

For Medium and Large tier stories, write the `test_specs` section before any other Medium+ field. Tests are the source of truth — acceptance criteria, io_examples, invariants, failure_modes, and edge_cases all reference test IDs from this section.

For each test spec entry:
- `id` must be unique within the story (T-01, T-02, ...)
- `covers` must reference a valid AC-id from `acceptance_criteria`
- `arrange/act/assert` must be concrete, not abstract

### Step 5 — Populate Tier-Required Fields

Fill all fields required by the detected tier. Every field that references tests (invariants.test, failure_modes.test, edge_cases.test) must use IDs that exist in `test_specs`.

Field completeness rules:
- Trivial: 3 fields (id, title, description)
- Small: 5 fields (add files, acceptance_criteria)
- Medium: 12 fields (add scope through observability_rules)
- Large: 18+ fields (add failure_modes through resource_safety)

Metadata fields (all tiers — populate the `metadata` section per `story-schema.md`):
- `metadata.story_points`: assign based on tier and complexity. Use `[1, 2, 3, 5, 8, 10]`. Trivial: 1-2, Small: 2-3, Medium: 3-5, Large: 5-10.
- `metadata.priority`: set to `"medium"` by default. PM adjusts via RICE scoring later.
- `metadata.blocked_by`: populate from design doc dependency analysis. Empty list if no dependencies.
- `metadata.status`: set to `"planned"` for all new stories.

### Step 6 — Per-Story Self-Validation

Before moving to the next story, verify this 6-point checklist:

1. **Single scope:** Story has exactly one `scope` value (Medium+ tiers)
2. **Error case present:** `io_examples` includes at least one error-case example (Medium+)
3. **Test reference integrity:** Every `test` field value matches an ID in `test_specs`
4. **No orphan tests:** Every `test_specs` entry is referenced by at least one other field
5. **Size limits:** `metadata.story_points` <= 10, `files` list <= 3 source files (test files are NOT listed in `files` — they're defined in `test_specs`). If exceeded, split the story.
6. **Feature flags:** Large tier stories have `feature_flags` with `default: false`

Fix any failures before proceeding.

### Step 7 — Final Verification Loop (mandatory)

After ALL stories are created, run this cross-story verification. Do not skip this step.

```
FOR EACH story in the batch:
  1. Collect all test IDs from test_specs
  2. Collect all test references from: invariants, failure_modes, edge_cases
  3. Forward check: every test reference → must exist in test_specs
  4. Reverse check: every test_specs entry → must be referenced by at least one field
  5. Cross-story check: no duplicate story IDs, no overlapping scope boundaries
  6. Size check: files list <= 3 source files, story_points <= 10. If exceeded, split the story.

IF any check fails:
  Fix the specific story
  Re-run verification for that story
  Continue until all stories pass

EMIT verification summary:
  - stories_count: N
  - total_tests: N
  - forward_refs_valid: true/false
  - reverse_refs_valid: true/false
  - duplicate_check: passed/failed
```

## Mode: ENRICH

Enrich existing sparse stories with tier-appropriate fields. Preserves original content — adds missing fields, never overwrites existing ones.

### Step 1 — Load Sparse Stories

Read the story files to enrich. Identify which fields are already populated.

### Step 2 — Load Codebase Context

For brownfield projects (`settings.project.type == "brownfield"`):
- Read `.shaktra/analysis/` artifacts for codebase patterns, existing interfaces, naming conventions
- Read existing source files listed in the story's `files` field

For greenfield projects: skip this step.

### Step 3 — Detect Tier

Apply tier detection from `story-tiers.md`. If the story already declares a tier, respect it. If not, auto-detect and record.

### Step 4 — Fill Missing Fields

For each field required by the story's tier (per `story-schema.md`):
- If field exists and has content: **preserve it** — do not overwrite
- If field is missing or empty: fill it following the same rules as CREATE mode

Write `test_specs` first if missing, then fill dependent fields.

### Step 5 — Self-Validate

Run the same 6-point checklist from CREATE Step 6.

### Step 6 — Final Verification

If enriching a batch of stories, run the Final Verification Loop from CREATE Step 7. For a single story, run only forward and reverse checks (steps 1-4 of the loop).

## Validation Quick Reference

| Check | Applies To | Severity if Violated |
|---|---|---|
| Single scope | Medium+ | P0 (multi-scope) |
| Error case in io_examples | Medium+ | P0 (missing error path) |
| Forward test ref integrity | Medium+ | P0 (orphan reference) |
| Reverse test ref coverage | Medium+ | P0 (dead test) |
| File count > 3 source files | All tiers | P0 (split needed) |
| Story points > 10 | All tiers | P1 (split needed) |
| Feature flags for Large | Large only | P1 (missing safety mechanism) |
| Edge case coverage (5/10) | Large only | P1 (insufficient coverage) |
| Field completeness per tier | All tiers | P1 (missing required field) |
