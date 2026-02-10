# Phase 1 — Foundation & Plugin Scaffold [COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) before starting.
> **Depends on:** None — this is the first phase.
> **Blocks:** Phase 2, Phase 7, Phase 8

---

## Objective

Set up the plugin skeleton with manifest, directory structure, initialization command, and default templates.

## Deliverables

| File | Lines | Purpose |
|------|-------|---------|
| `.claude-plugin/plugin.json` | ~15 | Plugin manifest |
| `CLAUDE.md` | ~30 | Plugin identity and command listing |
| `skills/shaktra-init/SKILL.md` | ~100 | Initialize target project for Shaktra |
| `templates/settings.yml` | ~35 | Default framework settings |
| `templates/decisions.yml` | ~10 | Empty decisions template |
| `templates/lessons.yml` | ~10 | Empty lessons template |
| `templates/sprints.yml` | ~15 | Empty sprints template |
| `hooks/hooks.json` | ~5 | Empty hooks config (populated in Phase 9) |
| `.claude-plugin/marketplace.json` | ~15 | Marketplace catalog for plugin distribution |

## File Content Outlines

**marketplace.json (at `.claude-plugin/marketplace.json`):**
```json
{
  "name": "shaktra-marketplace",
  "owner": { "name": "Shashank" },
  "plugins": [
    {
      "name": "shaktra",
      "source": ".",
      "description": "Opinionated software development framework with TDD, quality gates, and multi-agent orchestration"
    }
  ]
}
```
Enables installation via `/plugin marketplace add ./path-to-shaktra` (local) or `/plugin marketplace add owner/shaktra-plugin` (GitHub). Users then run `/plugin install shaktra@shaktra-marketplace`.

**plugin.json:**
```json
{
  "name": "shaktra",
  "version": "0.1.0",
  "description": "Opinionated software development framework with TDD, quality gates, and multi-agent orchestration",
  "author": { "name": "Shashank" },
  "keywords": ["tdd", "quality", "agile", "framework"]
}
```

**CLAUDE.md:**
- Project identity: "This project uses the Shaktra framework"
- List of available commands: `/shaktra:tpm`, `/shaktra:dev`, `/shaktra:review`, `/shaktra:analyze`, `/shaktra:general`, `/shaktra:init`, `/shaktra:doctor`, `/shaktra:workflow`
- Pointer: "Use `/shaktra:workflow` for auto-intent routing or invoke agents directly"
- State location: `.shaktra/` directory (hidden — see architecture overview)
- Reference: "Shared quality standards in shaktra-reference skill"

**shaktra-init SKILL.md:**
- Creates `.shaktra/` directory tree in target project
- Copies templates into correct locations
- Prompts user for project name, type (greenfield/brownfield), language, test framework, coverage tool, package manager
- Validates that directory doesn't already exist
- Reports created structure and next steps

**templates/settings.yml:**
```yaml
project:
  name: ""
  type: ""  # greenfield | brownfield
  language: ""  # python | typescript | go | java | rust | etc.
  test_framework: ""  # pytest | jest | go test | junit | cargo test | etc.
  coverage_tool: ""  # coverage.py | nyc | go cover | jacoco | etc.
  package_manager: ""  # pip | npm | go mod | maven | cargo | etc.

tdd:
  coverage_threshold: 90
  hotfix_coverage_threshold: 70

quality:
  p1_threshold: 2      # Referenced by severity-taxonomy merge gate logic

sprints:
  enabled: true
  velocity_tracking: true
  sprint_duration_weeks: 2
```

## Validation

- [ ] `claude --plugin-dir .` loads the plugin without errors
- [ ] `/shaktra:init` is listed in available commands
- [ ] Running `/shaktra:init` in a test project creates correct `.shaktra/` directory structure
- [ ] `templates/settings.yml` has all required fields
- [ ] `marketplace.json` exists and points to plugin source
- [ ] No file exceeds 300 lines

## Forge Reference

| Forge Source | What to Port | What to Change |
|-------------|-------------|----------------|
| `CLAUDE.md` (44 lines) | Minimal project identity pattern | Remove template-as-config pattern |
| `forge/settings.yml` (30 lines) | Threshold definitions | Add sprint config, remove learning config |
| `.claude/settings.json` | Permission deny patterns | Move to hooks.json format |
