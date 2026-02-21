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

Code that passes review and tests may still harbor blind spots. Tests can share the same assumptions as the code they test. Mutation testing reveals what the test suite actually verifies vs. what it merely executes. Adversarial probes reveal how code behaves under conditions nobody thought to test. The goal is not to find style issues — it is to find behaviors that would surprise the team in production.

## Intent Classification

Classify the user's request into one of these intents:

| Intent | Trigger Patterns | Workflow |
|---|---|---|
| `story-adversarial` | "adversarial review story", "adversarial ST-", story ID reference | Story Adversarial Review |
| `pr-adversarial` | "adversarial review PR", "adversarial pull request", "#" followed by number, PR URL | PR Adversarial Review |

If ambiguous, ask the user to specify which mode.

---

## Story Adversarial Review Workflow

### 1. Read Project Context

Before any review:
- Read `.shaktra/settings.yml` — if missing, inform user to run `/shaktra:init` and stop
- Read `.shaktra/memory/principles.yml` (if exists)
- Read `.shaktra/memory/anti-patterns.yml` (if exists)
- Read `.shaktra/memory/procedures.yml` (if exists)
- Determine memory retrieval tier:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_retrieval.py <story_dir> <settings_path>
  ```
- Generate `.shaktra/stories/<story_id>/.briefing.yml` per retrieval tier (see `retrieval-guide.md`):
  - **Tier 1:** Generate inline following the retrieval algorithm
  - **Tier 2:** Spawn memory-retriever (briefing mode) using dispatch template
  - **Tier 3:** Spawn parallel chunk retrievers + consolidation retriever using dispatch templates
- Create empty `.shaktra/stories/<story_id>/.observations.yml`

### 2. Load Change Context & Build Behavior Contract

- Read story YAML at `.shaktra/stories/<story_id>.yml`
- Read handoff at `.shaktra/stories/<story_id>/handoff.yml`
- Read all files in `handoff.code_summary.files_modified`
- Read all files in `handoff.test_summary.test_files`

From the loaded context, build a behavior contract identifying:
- **Changed functions/methods** — the mutation targets (file, function name, line range)
- **Acceptance criteria** — the behavior hypotheses to test (from story YAML)
- **Invariants** — behavior that must NOT change (existing tests that should still pass)
- **Dependencies** — external systems/modules called by changed code (mock targets for fault injection)
- **Test files** — existing test suite to run against mutations
- **Test command** — from `settings.project.test_framework` or detected from project structure

### 3. Dispatch Adversary Agents in Parallel

Spawn 3 `shaktra-adversary` agent instances, one per probe group:

**Group 1 — Mutation Probes:**
```
You are the shaktra-adversary agent. Execute adversarial probes against the code changes.

Probe group: mutation — arithmetic, relational, logical, conditional, return_value, exception, boundary, deletion
Changed functions: {function_list_with_files_and_lines}
Test files: {test_file_paths}
Test command: {test_command}
Behavior contract: {behavior_contract}
Briefing: {briefing_path}
Settings path: {settings_path}

Follow mutation-strategy.md for mutation operators and safety protocol.
Return structured findings with evidence from execution.
```

**Group 2 — Input & Boundary Probes:**
```
You are the shaktra-adversary agent. Execute adversarial probes against the code changes.

Probe group: input_boundary — null_empty, type_mismatch, boundary_values, injection, format
Changed functions: {function_list_with_files_and_lines}
Test files: {test_file_paths}
Test command: {test_command}
Behavior contract: {behavior_contract}
Briefing: {briefing_path}
Settings path: {settings_path}

Follow probe-strategies.md Group 2 section for input and boundary probes.
Return structured findings with evidence from execution.
```

**Group 3 — Fault & Resilience Probes:**
```
You are the shaktra-adversary agent. Execute adversarial probes against the code changes.

Probe group: fault_resilience — timeout, error_response, partial_response, connection_refused, slow_response, race_condition, idempotency
Changed functions: {function_list_with_files_and_lines}
Test files: {test_file_paths}
Test command: {test_command}
Behavior contract: {behavior_contract}
Briefing: {briefing_path}
Settings path: {settings_path}

Follow probe-strategies.md Group 3 section for fault and resilience probes.
Return structured findings with evidence from execution.
```

### 4. Aggregate Results

Collect findings from all 3 adversary agents. Deduplicate:
- If two agents flag the same function for the same issue, keep the higher severity
- Order findings: P0 first, then P1, P2, P3

Assign final severity per `severity-taxonomy.md`.

### 5. Compute Mutation Score

From Group 1 results:
```
mutation_score = killed / total * 100
mutation_threshold = settings.adversarial_review.mutation_kill_threshold
```

If Group 1 produced no mutations (e.g., no changed functions amenable to mutation), record mutation score as N/A.

### 6. Apply Verdict

Read thresholds from settings. Apply gate logic:

```
p0_count = count findings where severity == P0
p1_count = count findings where severity == P1
p1_max   = settings.quality.p1_threshold
mutation_score = killed / total * 100
mutation_threshold = settings.adversarial_review.mutation_kill_threshold

if p0_count > 0:
    verdict = BLOCKED
elif p1_count > p1_max:
    verdict = CONCERN
elif mutation_score < mutation_threshold:
    verdict = CONCERN
else:
    verdict = PASS
```

Emit the corresponding guard token: `ADVERSARIAL_PASS`, `ADVERSARIAL_CONCERN`, or `ADVERSARIAL_BLOCKED`.

### 7. Report & Memory Capture

Output the structured report using the output template below.

**Test persistence** — Read `settings.adversarial_review.test_persistence`:
- `auto`: persist adversarial tests that found bugs, discard passing probes
- `always`: persist all generated adversarial tests to the project's test suite
- `never`: discard all adversarial tests after review (findings still reported)
- `ask`: present test results and ask user whether to persist each set

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

Same as story adversarial review step 1.

### 2. Load Change Context & Build Behavior Contract

- Run `gh pr view {pr_number} --json title,body,files,baseRefName,headRefName` to get PR metadata
- Run `gh pr diff {pr_number}` to get the full diff
- If the PR references a story ID (in title or body), load the story YAML
- Read all changed files in full (not just diff)
- Identify test files related to changed code

Build the same behavior contract as story mode, using PR metadata and diff as the source instead of handoff.

### 3. Dispatch Adversary Agents in Parallel

Same parallel dispatch as story adversarial review step 3.

### 4. Aggregate Results

Same as story adversarial review step 4.

### 5. Compute Mutation Score

Same as story adversarial review step 5.

### 6. Apply Verdict

Same gate logic as story adversarial review step 6.

### 7. Report & Memory Capture

Same as story adversarial review step 7 (artifacts path = `.shaktra/stories/<story_id>` if a story is linked, otherwise skip memory capture for non-story PRs).

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

## Verdicts

| Verdict | Condition | Meaning |
|---|---|---|
| `PASS` | 0 P0, P1 within threshold, mutation score above threshold | Ship with confidence |
| `CONCERN` | 0 P0, but P1 exceeds threshold or mutation score below threshold | Review blind spots — merge with awareness |
| `BLOCKED` | P0 > 0 | Critical issues from adversarial testing — fix before merge |

---

## Guard Tokens

| Token | When |
|---|---|
| `ADVERSARIAL_PASS` | Verdict is PASS |
| `ADVERSARIAL_CONCERN` | Verdict is CONCERN |
| `ADVERSARIAL_BLOCKED` | Verdict is BLOCKED |
