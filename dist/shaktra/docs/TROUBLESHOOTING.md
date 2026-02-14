# Troubleshooting

> Common issues, their symptoms, root causes, and step-by-step solutions.
>
> Run `/shaktra:doctor` first — it diagnoses most problems automatically.

---

## Plugin Not Loading

**Symptom:** `/shaktra:help` not found, no commands available.

**Cause:** Plugin not installed correctly or Claude Code version too old.

**Solution:**
1. Verify installation — `/plugin list` should show `shaktra`
2. Confirm Claude Code version is February 2025 or later
3. If missing, do a full reinstall:
   ```bash
   /plugin uninstall shaktra
   /plugin install https://github.com/im-shashanks/claude-plugins.git
   ```

---

## Plugin Not Updating / Stale Version

**Symptom:** You updated Shaktra but still see old behavior, missing commands, or `/shaktra:status-dash` shows an outdated version.

**Cause:** Claude Code's plugin cache (`~/.claude/plugins/cache/`) does not always invalidate when a plugin is updated on the marketplace. This is a [known issue](https://github.com/anthropics/claude-code/issues/17361) — `/plugin update` and `autoUpdate` may report success without actually refreshing cached files.

**Solution:**
```bash
# Clear the stale cache
rm -rf ~/.claude/plugins/cache/

# Restart Claude Code, then reinstall
/plugin install shaktra@cc-plugins
```

---

## Hooks Blocking Unexpectedly

**Symptom:** "Hook validation failed" when trying to edit files or commit.

**Cause:** One of Shaktra's enforcement hooks is rejecting the operation. The three most common hooks that block are listed below.

### block-main-branch

**Symptom:** Hook blocks your commit.

**Cause:** You are committing directly to `main`, `master`, or `prod`.

**Solution:** Create a feature branch first:
```bash
git checkout -b feature/your-feature
# Make changes and commit on the feature branch
git commit -m "your message"
```

### validate-story-scope

**Symptom:** Hook blocks a file edit.

**Cause:** The file you are editing is not listed in the current story's scope.

**Solution:** Add the file to the story's `files:` list:
```yaml
# .shaktra/stories/ST-XXX.md
files:
  - src/new-file.ts
```

### validate-schema

**Symptom:** Hook reports YAML validation failure.

**Cause:** A `.shaktra/` state file has invalid or missing fields.

**Solution:** Read the error message — it names the invalid field. Ensure all required fields are present in the affected file.

---

## Schema Validation Errors

**Symptom:** "File does not match schema" when editing YAML files.

**Cause:** State files under `.shaktra/` do not conform to the expected schema.

**Solution — check these common issues in order:**

1. **Missing required fields** — Stories need `id`, `title`, `description`, and `acceptance_criteria`. Check `.shaktra/settings.yml` against the template from `/shaktra:init`.

2. **Invalid YAML syntax** — Verify indentation uses spaces (not tabs) and all quotes are matched. Lint with `yaml lint .shaktra/settings.yml` if a linter is available.

3. **Invalid enum values** — Story status must be one of: `backlog`, `planned`, `in-progress`, `complete`. Project type must be `greenfield` or `brownfield`.

---

## State File Corruption

**Symptom:** `/shaktra:doctor` reports schema errors or missing files.

**Cause:** State files under `.shaktra/` were manually edited incorrectly, partially written, or deleted.

**Solution — try these in order:**

1. **Diagnose** — run `/shaktra:doctor` and note which files are affected.

2. **Restore from git** (if the files were previously committed):
   ```bash
   git checkout .shaktra/
   ```

3. **Reinitialize** (last resort — loses sprint and story state):
   ```bash
   rm -rf .shaktra/
   /shaktra:init
   ```

---

## Dev Workflow Stuck in a State

**Symptom:** `/shaktra:dev ST-001` keeps asking to retry the same phase.

**Cause:** A quality gate is failing repeatedly. Common reasons:
- P0 or P1 findings not resolved
- Test coverage below the configured threshold
- Schema validation errors in the story file

**Solution:**
1. Read the error message — it tells you which gate is blocking
2. Fix the underlying issue (failing tests, unresolved findings, invalid YAML)
3. Re-run `/shaktra:dev ST-001` to continue from where it left off

---

## Coverage Below Threshold

**Symptom:** Tests pass (green phase) but coverage is below the required threshold (e.g., 85% actual vs 90% required).

**Cause:** New code paths lack test coverage, or dead code inflates the uncovered line count.

**Solution:**
1. Run the coverage report to identify exactly which lines are uncovered
2. Write tests for the uncovered paths
3. Remove dead code that will never execute — this raises the coverage ratio
4. If a lower threshold is genuinely appropriate, request a story tier adjustment

---

## Using /shaktra:doctor

`/shaktra:doctor` is the built-in diagnostic tool. Run it whenever something seems wrong.

**When to use:**
- After `/shaktra:init` to validate setup
- When troubleshooting any issue above
- Before calling developer support
- As a pre-commit sanity check

**What it checks:**
- Plugin installation (all files present)
- `.shaktra/` configuration (valid YAML, required keys)
- `settings.yml` compatibility (required fields, valid values)
- Hook scripts (executable, valid Python)
- Component counts (agents and skills match expected totals)
- Design constraints (no files over 300 lines, no dead code)
- P0 findings (all resolved before story completion)

**Interpreting results:**
- **Green** — all checks passed, framework is healthy
- **Yellow** — warnings, optional but recommended to fix
- **Red** — errors, must fix before continuing
