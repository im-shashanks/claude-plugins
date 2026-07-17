# Shaktra Workflow Scripts

Deterministic orchestration for every Shaktra pipeline, executed by Claude Code's
**Workflow tool**. Thin SKILLs prepare args (via `scripts/shaktra_context.py`) and
invoke a top-level script here; agents referenced by `agentType` supply personas
from `agents/*.md`; structured returns replace the old guard-token protocol.

## Layout

| File | Role |
|---|---|
| `lib/schemas.js` | Data-only child — returns every structured-output schema + `SCHEMA_VERSION` |
| `lib/quality-loop.js` | Agent-running child — the ONE review→fix→re-review gate loop (merge-gate semantics live here) |
| `lib/memory.js` | Agent-running child — briefing retrieval + end-of-workflow capture (owns `BRIEFING`, `MEMORY_CAPTURE_RESULT`) |
| `lib/report.js` | Data-only child — the ONE completion-report builder |
| `dev-tdd.js`, `refactor.js`, `review.js`, `adversarial.js`, `tpm-design.js`, `tpm-stories.js`, `analyze.js`, `bugfix-diagnose.js`, `incident.js`, `pm-artifacts.js` | Top-level pipeline scripts, one per command mode |

## Hard constraints (verified against the Workflow runtime)

1. **No imports.** Workflow scripts cannot `import` — statically or dynamically.
   Sharing happens ONLY via `workflow({scriptPath}, args)` child calls.
2. **One nesting level.** A child workflow cannot call `workflow()`. Therefore:
   top-level scripts fetch schemas from `lib/schemas.js` and pass the needed
   schema objects DOWN to agent-running children through `args`.
3. **JSON boundary.** Only JSON-serializable values cross `workflow()`/`agent()`
   boundaries — never functions. Small pure checks (e.g. a coverage comparison)
   are inlined in each script; anything bigger becomes a child workflow.
4. **No filesystem access.** Scripts route data via args and returns. Files are
   written only by agents, or after the run by the SKILL via
   `scripts/shaktra_handoff.py` (deterministic, atomic handoff merges).
5. **No `Date.now()` / `Math.random()`.** Timestamps come in via args; the SKILL
   stamps results after the run.
6. **Absolute `scriptPath`.** SKILLs write `${CLAUDE_PLUGIN_ROOT}/workflows/…`;
   Claude Code expands the variable when the skill loads, so the Workflow call
   receives an absolute path. Child calls use `args.plugin_root` +
   `'/workflows/lib/….js'`.
7. **Namespaced `agentType`.** Plugin agents register as
   `shaktra:<frontmatter-name>` (e.g. `shaktra:shaktra-developer`) — the bare
   frontmatter name does NOT resolve. Every `agentType` literal in these
   scripts carries the `shaktra:` prefix.
8. **Args coercion.** Every script binds
   `const a = typeof args === 'string' ? JSON.parse(args) : args` — defensive
   against callers passing a JSON-encoded string instead of an object.

## Conventions

- **Escalation, not interaction.** Scripts never ask the user anything. They
  return early with `{status: 'blocked' | 'needs_clarification', …}`; the SKILL
  presents it via AskUserQuestion and re-invokes (Workflow resume caches
  completed agents; `handoff.completed_phases` makes cross-session re-entry correct).
- **Handoff writes.** Only sequential phase agents (and the fix agents inside
  `lib/quality-loop.js`) write `handoff.yml` during a run. Parallel fan-out
  agents are read-only — findings return in-band. The SKILL persists the final
  result (`quality_findings`, `observations`, `workflow_run`) with
  `shaktra_handoff.py` when the run returns.
- **Severity semantics** are defined once in
  `skills/shaktra-reference/severity-taxonomy.md` and loaded through reviewer
  personas. JS only counts severities; the pass rule (0 P0, P1 ≤
  `settings.quality.p1_threshold`) is implemented once, in `lib/quality-loop.js`.
- **Thresholds** always arrive through args, sourced from `.shaktra/settings.yml`
  by `scripts/shaktra_context.py`. No threshold literals in scripts.
- **Schema changes** bump `SCHEMA_VERSION` in `lib/schemas.js` and require the
  matching field-list update in `scripts/validate_schema.py`.
