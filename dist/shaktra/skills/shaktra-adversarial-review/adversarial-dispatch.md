# Adversarial Agent Dispatch

Reference file for `/shaktra:adversarial-review` step 3. Dispatches adversary agents in two phases to prevent source file conflicts during mutation testing.

**Used by:** shaktra-adversarial-review SKILL.md (step 3).
**Prerequisites:** Behavior contract built (step 2), settings loaded (step 1).

---

## Variable Resolution

Before constructing prompts, replace ALL `{variables}` with actual values:
- `{skill_directory}` → absolute path to this skill's directory (the directory containing SKILL.md)
- `{settings_path}` → absolute path to `.shaktra/settings.yml`
- `{briefing_path}` → absolute path to `.briefing.yml` (or "none" if no briefing generated)
- `{behavior_contract}` → the YAML behavior contract from step 2 (inline, not a file path)
- `{function_list}` → extracted from `behavior_contract.changed_functions`
- `{test_file_paths}` → extracted from `behavior_contract.test_files`
- `{test_command}` → extracted from `behavior_contract.test_command`

Agents cannot resolve variables or relative paths — every path must be concrete and absolute.

---

## Two-Phase Dispatch

Mutation testing temporarily modifies source files on disk (edit → run tests → restore). If probe agents read those files during a mutation window, they see mutated code and generate tests against wrong behavior. To prevent this:

- **Phase A** — Spawn Agent 1 (mutation) alone. Wait for it to complete.
- **Verify restoration** — Check source files are clean before Phase B.
- **Phase B** — Spawn Agents 2 and 3 in the same message for parallel execution.

### Phase A: Agent 1 — Mutation Probes (sequential)

Spawn this agent alone and wait for completion before proceeding.

```
You are the shaktra-adversary agent. Execute adversarial probes against the code changes.

Probe group: mutation
Mutation operators: arithmetic, relational, logical, conditional, return_value, exception, boundary, deletion

Changed functions:
{function_list}

Test files: {test_file_paths}
Test command: {test_command}

Behavior contract:
{behavior_contract}

Briefing: {briefing_path}
Settings: {settings_path}

Strategy file (READ THIS FIRST): {skill_directory}/mutation-strategy.md
Severity reference: {skill_directory}/../shaktra-reference/severity-taxonomy.md

Follow mutation-strategy.md exactly — especially the safety protocol for restoration verification.
Return observations (non-routine insights) in your structured output under the observations field.
Do NOT write to the observations file directly — the orchestrator handles that.
Return structured findings per the adversary_analysis output format in your agent definition.
Every finding must include execution evidence (test output, stack trace, or command result).
```

### Source File Verification (between Phase A and Phase B)

After Agent 1 completes, verify all source files are restored before spawning Phase B agents. **Prerequisite:** This verification assumes the story/PR changes are committed. If uncommitted changes exist, `git checkout --` would revert them along with stuck mutations — never run adversarial review on uncommitted work. Run:

```bash
git diff --name-only
```

If any files from `behavior_contract.changed_functions` show uncommitted changes:
1. These are likely stuck mutations from a crashed agent
2. Restore them: `git checkout -- <file_path>` for each affected file
3. Log a warning: "Restored {n} files with stuck mutations after Phase A"

Only proceed to Phase B after verification passes.

### Phase B: Agents 2 and 3 — Probe Tests (parallel, after verification)

Spawn both agents in the same message for parallel execution.

**Agent-specific test file naming** to prevent write collisions:
- Agent 2 writes: `test_<module>_adversarial_input.py` (or language equivalent)
- Agent 3 writes: `test_<module>_adversarial_fault.py` (or language equivalent)

#### Agent 2 — Input & Boundary Probes

```
You are the shaktra-adversary agent. Execute adversarial probes against the code changes.

Probe group: input_boundary
Probe types: null_empty, type_mismatch, boundary_values, injection, format

Changed functions:
{function_list}

Test files: {test_file_paths}
Test command: {test_command}

Behavior contract:
{behavior_contract}

Briefing: {briefing_path}
Settings: {settings_path}

Strategy file (READ THIS FIRST): {skill_directory}/probe-strategies.md → Group 2 section
Severity reference: {skill_directory}/../shaktra-reference/severity-taxonomy.md

IMPORTANT: Name generated test files with suffix `_adversarial_input` (e.g., test_auth_adversarial_input.py).
Follow probe-strategies.md Group 2 for test generation patterns and finding classification.
Return observations (non-routine insights) in your structured output under the observations field.
Do NOT write to the observations file directly — the orchestrator handles that.
Return structured findings per the adversary_analysis output format in your agent definition.
Every finding must include execution evidence (test output, stack trace, or command result).
```

#### Agent 3 — Fault & Resilience Probes

```
You are the shaktra-adversary agent. Execute adversarial probes against the code changes.

Probe group: fault_resilience
Probe types: timeout, error_response, partial_response, connection_refused, slow_response, race_condition, idempotency

Changed functions:
{function_list}

Test files: {test_file_paths}
Test command: {test_command}

Behavior contract:
{behavior_contract}

Briefing: {briefing_path}
Settings: {settings_path}

Strategy file (READ THIS FIRST): {skill_directory}/probe-strategies.md → Group 3 section
Severity reference: {skill_directory}/../shaktra-reference/severity-taxonomy.md

IMPORTANT: Name generated test files with suffix `_adversarial_fault` (e.g., test_auth_adversarial_fault.py).
Follow probe-strategies.md Group 3 for test generation patterns and finding classification.
Return observations (non-routine insights) in your structured output under the observations field.
Do NOT write to the observations file directly — the orchestrator handles that.
Return structured findings per the adversary_analysis output format in your agent definition.
Every finding must include execution evidence (test output, stack trace, or command result).
```

---

## Output Validation

After each phase completes, validate agent output before proceeding.

**Required structure:**
```yaml
adversary_analysis:
  group: "{probe_group_name}"
  probes_executed: integer          # must be > 0
  mutation_results:                 # mutation group only
    total: integer
    killed: integer
    survived: integer
    surviving_mutations: [...]
  test_results:                     # input_boundary and fault_resilience groups
    generated: integer
    passed: integer
    failed: integer
    errors: integer
  findings:
    - severity: P0|P1|P2|P3
      probe_type: "..."
      function: "file:function_name"
      description: "..."
      evidence: "..."               # non-empty — execution output, not speculation
      guidance: "..."
  observations:                     # non-routine insights (may be empty)
    - type: "discovery|quality-loop-finding|observation"
      text: "..."
      tags: [...]
      importance: integer
  summary:
    p0_count: integer
    p1_count: integer
    p2_count: integer
    p3_count: integer
```

**Validation checklist:**
1. `adversary_analysis` top-level key exists
2. `probes_executed` > 0 (agent actually ran probes, not just planned them)
3. Every finding has non-empty `evidence` field containing execution output — reject findings with speculative evidence like "this could fail" or "potential issue"
4. Severity values are valid: P0, P1, P2, or P3
5. For mutation group: `mutation_results.total` > 0 if changed functions were provided
6. `summary` counts match actual findings array length

**On validation failure:**
- Log which agent failed and which checks failed
- Re-dispatch the failed agent once with the same prompt plus: "Your previous output failed validation: {specific_failures}. Ensure you execute probes and include real execution evidence."
- If second attempt also fails: note the gap in the final report under a "### Agent Failures" section and exclude unvalidated findings from aggregate counts and verdict logic
