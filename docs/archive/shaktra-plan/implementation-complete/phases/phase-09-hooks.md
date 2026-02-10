# Phase 9 — Hooks & External Enforcement [COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) before starting.
> **Depends on:** Phase 1 (Foundation), Phase 3 (State Schemas) for validation.
> **Blocks:** Phase 11 (Workflow Router)

---

## Objective

Wire up all hooks to provide real, external enforcement of quality gates. Every hook either blocks or doesn't exist — no warn-only.

## Deliverables

| File | Lines | Purpose |
|------|-------|---------|
| `hooks/hooks.json` | ~40 | Hook event configurations |
| `scripts/block_main_branch.py` | ~40 | Block git ops on protected branches |
| `scripts/check_p0_findings.py` | ~50 | Block completion with P0 findings |
| `scripts/validate_story_scope.py` | ~60 | Block file changes outside story scope |
| `scripts/validate_schema.py` | ~60 | Validate YAML schema on write |

## Hook Details

**hooks.json:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/block_main_branch.py" }]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_story_scope.py" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [{ "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_schema.py" }]
      }
    ],
    "Stop": [
      {
        "hooks": [{ "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_p0_findings.py" }]
      }
    ]
  }
}
```

**block_main_branch.py:**
- Reads tool_input from stdin (JSON)
- Checks if bash command contains git operations targeting main/master/prod/production
- Exit 2 to block, exit 0 to allow
- Cross-platform (Python, not bash grep)

**Active story detection (used by check_p0_findings and validate_story_scope):**
- Scan `.shaktra/.tmp/*/handoff.yml` for handoffs where `current_phase` is NOT `complete` or `failed`
- If exactly one found → that's the active story
- If multiple found → use most recently modified (pre-v1 limitation; worktrees solve this post-v1)
- If none found → no active story, hooks allow all operations

**check_p0_findings.py:**
- Detects active story via mechanism above
- Checks latest quality_findings for P0 count
- If P0 > 0, exit 2 with "Cannot complete: X P0 findings remain"
- If no active story, exit 0 (allow)

**validate_story_scope.py:**
- Detects active story via mechanism above
- Reads story's declared `files` list from `.shaktra/stories/{story-id}.yml`
- Compares file being written/edited against declared files
- If file not in scope, exit 2 with "File X not in story scope for ST-001"
- If no active story, exit 0 (allow)

**validate_schema.py:**
- Triggers on writes to `.shaktra/stories/*.yml` and `.shaktra/.tmp/*/handoff.yml`
- Validates YAML structure against schemas from shaktra-reference
- If invalid, exit 2 with specific validation errors
- If not a Shaktra YAML file, exit 0

## Validation

- [ ] `git checkout main` blocked when hook is active
- [ ] Agent cannot complete with P0 findings
- [ ] Writing to files outside story scope is blocked
- [ ] Invalid YAML schema is caught on write
- [ ] All hooks use Python (no `grep -oP` or bash-only constructs)
- [ ] All hooks have clear error messages
- [ ] No hook is warn-only

## Forge Reference

| Forge Source | What to Port | What to Change |
|-------------|-------------|----------------|
| block-main-branch.sh | Branch protection | Rewrite in Python |
| validate-story-alignment.sh (warn-only) | Scope checking | **Make blocking, not warn-only** |
| check-p0-findings.py (not wired) | P0 blocking | **Actually wire it up** |
| validate-story.py (not configured) | Schema validation | **Actually configure it** |
