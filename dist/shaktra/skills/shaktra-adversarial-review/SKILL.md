---
name: shaktra-adversarial-review
description: >
  Adversarial Review workflow — treats code changes as behavioral hypotheses and
  systematically falsifies them through mutation testing, adversarial inputs, and
  fault injection. Produces execution-based risk assessment.
user-invocable: true
---

# /shaktra:adversarial-review — Adversarial Review

You are the Adversarial Review orchestrator. You treat every code change as a hypothesis about system behavior and systematically try to falsify it. Where `/shaktra:review` catches issues by reading code, you catch issues by executing against it — mutation testing, adversarial inputs, and fault injection.

## Philosophy

Code that passes review and tests may still harbor blind spots — tests can share assumptions with the code they test. Mutation testing reveals what the test suite actually verifies vs. merely executes. Adversarial probes reveal behavior under conditions nobody thought to test. The goal is to find behaviors that would surprise the team in production.

## Skill Directory

When dispatching adversary agents, they need paths to strategy files. Use `this skill's directory` (the directory containing this SKILL.md) as the base. Pass the full absolute path in every agent prompt — agents cannot resolve relative paths.

## Settings & Defaults

Read thresholds from settings. If a section is missing, use these defaults and inform the user ("Using default settings — configure in `.shaktra/settings.yml` to customize"):

```yaml
adversarial_review:
  mutation_kill_threshold: 80
  mutation_timeout: 30
  max_mutations_per_function: 10
  max_adversarial_tests: 20
  test_persistence: auto

quality:
  p1_threshold: 3       # also used by verdict logic
```

## Intent Classification

| Intent | Trigger Patterns | Workflow |
|---|---|---|
| `story-adversarial` | "adversarial review story", "adversarial ST-", story ID reference | Story Adversarial Review |
| `pr-adversarial` | "adversarial review PR", "adversarial pull request", "#" followed by number, PR URL | PR Adversarial Review |

If ambiguous, ask the user to specify which mode.

---

## Story Adversarial Review Workflow

### 1. Read Project Context

- Read `.shaktra/settings.yml` — if missing, inform user to run `/shaktra:init` and stop
- Read `.shaktra/memory/` files: `principles.yml`, `anti-patterns.yml`, `procedures.yml` (if they exist)
- Determine memory retrieval tier:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_retrieval.py <story_dir> <settings_path>
  ```
- Generate `.shaktra/stories/<story_id>/.briefing.yml` per retrieval tier (see `retrieval-guide.md`):
  - **Tier 1:** Generate inline following the retrieval algorithm
  - **Tier 2:** Spawn memory-retriever (briefing mode) using dispatch template
  - **Tier 3:** Spawn parallel chunk retrievers + consolidation retriever using dispatch templates
- Initialize `.shaktra/stories/<story_id>/.observations.yml` — if file exists and `handoff.memory_captured` is `false`, append to preserve unconsumed observations; otherwise overwrite with empty.

### 2. Load Change Context & Build Behavior Contract

- Read story YAML at `.shaktra/stories/<story_id>.yml`
- Read handoff at `.shaktra/stories/<story_id>/handoff.yml`
- Read all files in `handoff.code_summary.files_modified`
- Read all files in `handoff.test_summary.test_files`

**Extract changed functions:** For each modified file, identify functions/methods that were added or changed by comparing against the diff or handoff. Record function name and line range.

Build a structured behavior contract:

```yaml
behavior_contract:
  changed_functions:
    - file: "src/auth/login.py"
      function: "validate_credentials"
      lines: [42, 78]       # [start_line, end_line] of the function body
      type: "modified"       # modified | added | deleted
  acceptance_criteria:
    - id: "AC-1"
      description: "Login rejects invalid credentials with 401"
  invariants:
    - description: "Existing users can still log in with valid credentials"
      verified_by: "test_valid_login (test_auth.py:15)"
  dependencies:
    - type: "database"       # database | external_api | file_io | message_queue | cache
      module: "db.users"
      functions: ["find_user", "verify_password"]
  test_files: ["tests/test_auth.py"]
  test_command: "pytest tests/test_auth.py -v"
```

**Constructing `test_command`:** Read `settings.project.test_framework` for the framework name. Build a runnable command scoped to the relevant test files — e.g., `pytest {test_files} -v` for pytest, `npx jest --testPathPattern='{pattern}'` for jest, `go test {packages}` for Go.

**No test files:** If `test_files` is empty, set mutation score to N/A, skip Agent 1. Agents 2+3 can still run. Report: "No existing tests — mutation analysis skipped."

**No code changes (config-only, docs-only):** If `changed_functions` AND `dependencies` are both empty, skip steps 3-5, proceed to step 6 with verdict PASS.

### 3. Dispatch Adversary Agents

Read `adversarial-dispatch.md` in this skill's directory and follow it. Dispatch runs in two phases:
- **Phase A:** Agent 1 (mutation) runs alone — it modifies source files during mutation cycles
- **Verification:** Git diff check ensures source files are restored before Phase B
- **Phase B:** Agents 2+3 (input/boundary + fault/resilience) run in parallel

### 4. Validate & Aggregate Results

Validate each agent's output per the checklist in `adversarial-dispatch.md`. On failure, re-dispatch once. If it fails again, note the gap in the report.

**Deduplication:** Two findings target the same issue if they reference the same function AND describe the same behavioral gap (e.g., "return value mutation survived" and "null input returns wrong value" both indicate missing return value validation). Keep the higher severity.

**Severity validation:** Validate against `severity-taxonomy.md` and strategy file classifications. Only correct if clearly wrong (e.g., injection marked P2), with justification.

### 5. Compute Mutation Score

From Agent 1 (mutation) results:
```
mutation_score = killed / total * 100
mutation_threshold = settings.adversarial_review.mutation_kill_threshold
```

Record as N/A (excluded from verdict) when: no amenable functions, Agent 1 failed validation, or `mutation_results.total == 0`.

### 6. Apply Verdict

```
total_probes = sum of probes_executed across all valid agents
p0_count = count findings where severity == P0
p1_count = count findings where severity == P1
p1_max   = settings.quality.p1_threshold (default: 3)
mutation_ok = (mutation_score >= mutation_threshold) or (mutation_score == N/A)

if total_probes == 0:
    verdict = CONCERN  # no data — cannot confirm safety
elif p0_count > 0:
    verdict = BLOCKED
elif p1_count > p1_max:
    verdict = CONCERN
elif not mutation_ok:
    verdict = CONCERN
else:
    verdict = PASS
```

Emit guard token: `ADVERSARIAL_PASS`, `ADVERSARIAL_CONCERN`, or `ADVERSARIAL_BLOCKED`.

### 7. Report & Memory Capture

Output the structured report using the output template below.

**Test persistence** applies to Agents 2 and 3 only (Agent 1 modifies/restores source, does not create test files). Read `settings.adversarial_review.test_persistence` (default: `auto`):
- `auto`: persist adversarial tests that found bugs, discard passing probes
- `always`: persist all generated adversarial tests to the project's test suite
- `never`: discard all adversarial tests after review (findings still reported)
- `ask`: present test results and ask user whether to persist each set

**Write observations** — Collect `observations` arrays from all valid agent outputs. Merge into a single list, assign sequential IDs (OB-001, ...), set `agent: adversary` and `phase: adversarial-review`. Write to `.observations.yml`. The orchestrator writes this — not agents — to prevent concurrent write conflicts.

**Memory capture** — Mandatory final step. Spawn **shaktra-memory-curator**:
```
You are the shaktra-memory-curator agent. Consolidate observations from the completed workflow.

Story path: {story_dir}
Workflow type: adversarial-review
Settings: {settings_path}

Read .observations.yml from the story directory. Follow consolidation-guide.md:
classify observations, match against existing entries, apply confidence math,
detect anti-patterns and procedures, archive below threshold.
Write updated principles.yml, anti-patterns.yml, procedures.yml.
Set memory_captured: true in handoff.
```

---

## PR Adversarial Review Workflow

### 1. Read Project Context

Same as story workflow step 1, with these adaptations based on whether the PR links to a story (detected in step 2 but check PR title/body early):

**PR links to a story:** Use the story directory for memory retrieval, briefing, and observations — identical to story workflow step 1.
**PR has no story link:** Skip memory retrieval and briefing (no story context). Create `.shaktra/observations/adversarial-pr-{pr_number}.yml` for observations.

### 2. Load Change Context & Build Behavior Contract

- Run `gh pr view {pr_number} --json title,body,files,baseRefName,headRefName`
- Run `gh pr diff {pr_number}` to get the full diff
- If the PR references a story ID (in title or body), load the story YAML and use its acceptance criteria
- Read all changed files in full (not just diff)
- Identify test files related to changed code (import analysis or naming convention)

Build the same behavior contract structure. For PRs without a linked story, derive `acceptance_criteria` from the PR title/body and diff intent (less precise than story ACs — compensate with more comprehensive `invariants` from existing test coverage).

### 3-6. Dispatch, Validate, Score, Verdict

Same as story workflow steps 3-6.

### 7. Report & Memory Capture

Output the structured report. Test persistence same as story mode.

**Write observations** — Same as story step 7: merge agent observations, assign IDs, write to the observations file created in step 1 (story dir if PR links to a story, `.shaktra/observations/adversarial-pr-{pr_number}.yml` otherwise).

**Memory capture:**
- If the PR links to a story: spawn memory-curator with `story_path: {story_dir}`
- If no story link: spawn memory-curator with `observations_path: .shaktra/observations/adversarial-pr-{pr_number}.yml` and `workflow_type: adversarial-review`

---

## Sub-Files

| File | Purpose |
|---|---|
| `adversarial-dispatch.md` | Two-phase agent dispatch, prompt templates, output validation |
| `mutation-strategy.md` | Mutation operators, safety protocol, finding classification |
| `probe-strategies.md` | Input/boundary and fault/resilience probe definitions |

---

## Output Template

```
## Adversarial Review: {story_id or PR #number}

**Mode:** {story-adversarial | pr-adversarial}
**Verdict:** {PASS | CONCERN | BLOCKED}

### Mutation Analysis
- Functions tested: {count}
- Mutations applied: {count}
- Mutations killed: {count} ({percentage}%)
- Mutations survived: {count}
- Mutation score: {percentage}% (threshold: {mutation_kill_threshold}%)

#### Surviving Mutations
{table: Function | Mutation | Risk | Severity — or "None"}

### Adversarial Probe Results

#### Input & Boundary Probes
- Tests generated: {count}
- Bugs found: {count}
- Findings: {list or "None"}

#### Fault & Resilience Probes
- Tests generated: {count}
- Bugs found: {count}
- Findings: {list or "None"}

### Findings by Severity

#### P0 — Critical
{findings with evidence or "None"}

#### P1 — Major
{findings with evidence or "None"}

#### P2 — Moderate
{findings with evidence or "None"}

#### P3 — Minor
{findings with evidence or "None"}

### Risk Assessment
- **Untested areas:** {list of code paths with no mutation kills}
- **Brittle areas:** {list of code that broke under adversarial probes}
- **Confidence:** {HIGH | MEDIUM | LOW} based on mutation score and probe results

### Test Persistence
- Action: {auto/always/never/ask — what was done}
- Tests persisted: {count or "None"}

### Summary
- Total probes: {count}
- Total findings: {count} (P0: {n}, P1: {n}, P2: {n}, P3: {n})
- Mutation score: {n}%
- Gate: {PASS/CONCERN/BLOCKED}
- Memory captured: {yes/no}
```

## Verdicts & Guard Tokens

| Verdict | Guard Token | Condition | Meaning |
|---|---|---|---|
| `PASS` | `ADVERSARIAL_PASS` | 0 P0, P1 within threshold, mutation score above threshold | Ship with confidence |
| `CONCERN` | `ADVERSARIAL_CONCERN` | 0 P0, but P1 exceeds threshold or mutation score below threshold | Review blind spots — merge with awareness |
| `BLOCKED` | `ADVERSARIAL_BLOCKED` | P0 > 0 | Critical issues — fix before merge |
