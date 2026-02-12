---
name: shaktra-doctor
description: >
  Diagnose Shaktra framework health. Validates plugin structure, project configuration,
  and design constraints. Read-only — never modifies files.
user-invocable: true
---

# /shaktra:doctor — Framework Health Check

Read-only diagnostic. Runs 10 checks across 3 categories. Never creates, modifies, or deletes any file.

Use `${CLAUDE_PLUGIN_ROOT}` to locate the installed plugin directory for all plugin structure checks.

---

## Category 1: Plugin Structure

Checks the installed plugin at `${CLAUDE_PLUGIN_ROOT}`.

### Check 1 — Agent Files

Glob `${CLAUDE_PLUGIN_ROOT}/agents/*.md`. Verify all 12 agent files exist and each has valid YAML frontmatter (opening and closing `---` with at least `name` field).

**Expected agents:**
shaktra-architect, shaktra-bug-diagnostician, shaktra-cba-analyzer, shaktra-cr-analyzer, shaktra-developer, shaktra-memory-curator, shaktra-product-manager, shaktra-scrummaster, shaktra-sw-engineer, shaktra-sw-quality, shaktra-test-agent, shaktra-tpm-quality

PASS: All 12 files exist with valid frontmatter.
FAIL: List missing files or files with invalid frontmatter.

### Check 2 — Skill Directories

Glob `${CLAUDE_PLUGIN_ROOT}/skills/*/SKILL.md`. Verify all 14 skill directories exist and each SKILL.md has valid YAML frontmatter (opening and closing `---` with at least `name` and `description` fields).

**Expected skills:**
shaktra-analyze, shaktra-bugfix, shaktra-dev, shaktra-doctor, shaktra-general, shaktra-help, shaktra-init, shaktra-quality, shaktra-reference, shaktra-review, shaktra-stories, shaktra-tdd, shaktra-tpm, shaktra-workflow

PASS: All 14 skill SKILL.md files exist with valid frontmatter.
FAIL: List missing skills or invalid frontmatter.

### Check 3 — Hook Scripts

Glob `${CLAUDE_PLUGIN_ROOT}/scripts/*.py`. Verify all 4 hook scripts exist, then use Bash `test -x` on each to confirm they are executable.

**Expected scripts:**
block_main_branch.py, check_p0_findings.py, validate_schema.py, validate_story_scope.py

PASS: All 4 scripts exist and are executable.
FAIL: List missing or non-executable scripts.

### Check 4 — Sub-File References

For each SKILL.md that references sub-files (files within the same skill directory), verify those files actually exist. Read each SKILL.md that has a "Sub-Files" section or references relative `.md` files. For each referenced file, confirm it exists at the expected path under `${CLAUDE_PLUGIN_ROOT}/skills/<skill-name>/`.

PASS: All referenced sub-files exist.
FAIL: List each dangling reference with the SKILL.md that references it and the missing file path.

### Check 10 — Python Dependencies

Run `python3 -c "import yaml"` via Bash. Check the return code.

PASS: PyYAML is installed and importable.
FAIL: PyYAML is not installed → run: pip install pyyaml

---

## Category 2: Project Health

Checks the `.shaktra/` directory in the current working directory.

**If `.shaktra/` does not exist**, skip all Category 2 checks and report: "`.shaktra/` not found — run `/shaktra:init` first. Skipping project health checks."

### Check 5 — Settings File

Read `.shaktra/settings.yml`. Verify it exists and contains the required top-level sections: `project`, `tdd`, `quality`, `review`, `analysis`, `refactoring`, `sprints`.

Within `project`, verify these fields are present and non-empty: `name`, `type`, `language`.

PASS: settings.yml exists with all required sections and populated project fields.
FAIL: List missing sections or empty required fields.

### Check 6 — Directory Structure

Verify these subdirectories exist within `.shaktra/`:

- `memory/`
- `stories/`
- `designs/`
- `analysis/`

PASS: All expected subdirectories exist.
FAIL: List missing directories.

---

## Category 3: Design Constraints

Plugin-wide validation against Shaktra design rules. Run these checks against `${CLAUDE_PLUGIN_ROOT}`.

### Check 7 — File Line Limits

Use Bash `wc -l` on all `.md` and `.py` files under `${CLAUDE_PLUGIN_ROOT}`. Flag any file exceeding 300 lines.

PASS: No file exceeds 300 lines.
FAIL: List each file over 300 lines with its line count.

### Check 8 — Severity Taxonomy Uniqueness

The severity taxonomy (P0-P3 definitions) must be defined in exactly one file: `skills/shaktra-reference/severity-taxonomy.md`.

Grep `${CLAUDE_PLUGIN_ROOT}` for the pattern `## P0` (heading-level severity definitions). The pattern should match only in `severity-taxonomy.md`. Other files may *mention* severity levels (e.g., "P0 findings block merge") — that is fine. Only flag files that *redefine* the taxonomy with their own heading-level P0-P3 sections.

PASS: Severity taxonomy defined in exactly one file.
FAIL: List additional files that redefine severity levels.

### Check 9 — No Orphaned Files

Every `.md` file inside a skill directory (other than SKILL.md itself) must be referenced by that skill's SKILL.md. Glob all non-SKILL.md `.md` files under `${CLAUDE_PLUGIN_ROOT}/skills/`. For each, check that the parent skill's SKILL.md contains a reference to its filename.

PASS: All sub-files are referenced by their parent SKILL.md.
FAIL: List orphaned files not referenced by any SKILL.md.

---

## Output Format

Present results as a structured report:

```
## Shaktra Doctor Report

### Category 1: Plugin Structure
- [PASS] Check 1 — Agent Files: 12/12 agents found with valid frontmatter
- [PASS] Check 2 — Skill Directories: 15/15 skills found with valid frontmatter
- [PASS] Check 3 — Hook Scripts: 4/4 scripts found and executable
- [PASS] Check 4 — Sub-File References: All references resolve
- [PASS] Check 10 — Python Dependencies: PyYAML installed

### Category 2: Project Health
- [PASS] Check 5 — Settings File: All required sections and fields present
- [PASS] Check 6 — Directory Structure: All subdirectories present

### Category 3: Design Constraints
- [PASS] Check 7 — File Line Limits: All files under 300 lines
- [PASS] Check 8 — Severity Taxonomy: Defined in exactly 1 file
- [PASS] Check 9 — No Orphaned Files: All sub-files referenced

Summary: 10/10 checks passed
```

For any FAIL result, include actionable detail immediately after the check line:

```
- [FAIL] Check 3 — Hook Scripts: 1 issue
  - validate_schema.py is not executable → run: chmod +x scripts/validate_schema.py
```
