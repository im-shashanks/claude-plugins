# Shaktra Workflow Tests

End-to-end tests that verify `/shaktra:*` skills execute correctly in a real Claude Code session. Each test launches a fresh `claude --print` session with the plugin loaded, invokes a skill, and validates the resulting `.shaktra/` state.

**Every test is standalone** — own temp directory, own fixtures, no shared state between tests.

## Testing Philosophy

Shaktra has two testing layers:

| Layer | What | Speed | Cost | Runs When |
|-------|------|-------|------|-----------|
| **L1-L4 Audit** (`audit/`) | Static checks — file structure, references, schemas, hooks, state simulations | Fast (seconds) | Free (no API calls) | Every commit |
| **L5 Workflow** (`tests/workflows/`) | Live end-to-end workflow execution — real skill invocations with real sub-agents | Slow (minutes) | API costs per test | Pre-release, manual |

**L1-L4 proves the plugin is structurally correct. L5 proves it actually works.**

L5 tests verify what static checks cannot:
- Skill routing (intent classification → correct workflow)
- Sub-agent orchestration (architect, scrummaster, quality agents spawn and produce output)
- Quality gate execution (review → findings → fix loop)
- State transitions (handoff phases, sprint allocation, memory capture)
- File creation patterns (design docs, stories, sprints — correct format and content)
- **Reference file consultation** — file-read tracking verifies agents actually read practices, standards, and quality definitions
- **Error path handling** — negative tests verify pre-flight checks catch invalid state

### Test Scoping via CLAUDE.md Overrides

Tests need to prove workflows work, not produce production-quality output. To keep tests fast and affordable, the test framework injects constraints into the test project's `CLAUDE.md` — the standard mechanism for project-level instructions that all agents read:

- **Quality loops: 1 iteration** (production default is 3) — proves the loop runs without exhausting time
- **Story creation: 2 stories max** — proves the scrummaster creates valid stories without generating 10+
- **Sprint planning: 1 sprint** — proves allocation works
- **AskUserQuestion auto-answer** — agents select the first option instead of prompting for input
- **Mandatory logging** — all agents log events to `.shaktra-test.log` for real-time observability

These overrides live in `test_definitions.py` (`_TEST_OVERRIDES`) and are appended to the test directory's `CLAUDE.md` during setup. **No plugin files are modified.**

## Real Test Runs

Here's what actual test execution looks like — these are real logs from the automated test framework.

### Bugfix Workflow (9/10 validator checks passed)

The bugfix test starts with a calculator module containing a zero-division bug and validates the full diagnosis-to-fix pipeline:

```
[14:23:44] Starting test bugfix
[14:23:52] [bugfix-orchestrator] started — investigating divide function ZeroDivisionError bug
[14:24:14] PHASE: INVESTIGATION started
[14:24:40] [bug-diagnostician] started — investigating divide ZeroDivisionError
[14:24:51] PHASE: reproduce started
[14:25:02] PHASE: reproduce complete — bug confirmed: ZeroDivisionError raised instead of ValueError
[14:25:06] PHASE: hypothesize started
[14:25:29] PHASE: gather-evidence complete — RC-LOGIC-1 confirmed, RC-DATA-1 eliminated
[14:26:14] WRITE: .shaktra/diagnosis/BUG-001-diagnosis.yml
[14:26:14] WRITE: .shaktra/stories/BUG-001.yml
[14:26:37] DIAGNOSIS_COMPLETE — root cause: RC-LOGIC, location: src/calculator.py:2
[14:26:45] PHASE: REMEDIATION started — routing to TDD pipeline for BUG-001
[14:27:14] [sdm-orchestrator] started — TDD pipeline for BUG-001 (tier: small)
[14:28:55] PHASE: PLAN complete
[14:29:07] PHASE: RED started
[14:30:37] PHASE: tests complete — 3 FAILED (valid: ZeroDivisionError instead of ValueError), 6 PASSED
[14:31:12] PHASE: RED complete — 2 failing tests (valid RED), 7 passing
[14:32:29] QUALITY: verdict=BLOCKED findings=2 (1 P0, 1 P2)
[14:32:56] QUALITY-FIX: fixing 1 finding in tests/test_calculator.py
[14:33:50] PHASE: GREEN started
[14:34:09] [developer] started — implementing fix for BUG-001
[14:35:20] PHASE: code complete
[14:35:33] PHASE: GREEN complete — all 10 tests pass, 100% coverage
[14:36:39] QUALITY: verdict=PASS findings=0
```

**Result:** Bug diagnosed (root cause identified, hypotheses tested), TDD fix implemented (10 tests, 100% coverage), quality review passed. Total: ~13 minutes.

**Validator output:**
```
[PASS] calculator.py exists
[PASS] fix addresses zero division
[PASS] test file exists
[PASS] tests pass after fix
[PASS] bugfix story or artifact created
[PASS] diagnosis artifact exists
[PASS] bugfix story created
[PASS] root cause identified
[PASS] lessons.yml valid YAML
```

### Dev Workflow (18/19 validator checks passed)

The dev test starts with a pre-built story (ST-TEST-001: user registration) and validates the full TDD pipeline:

```
[14:45:15] Starting test dev
[14:45:23] [SDM] started — develop story ST-TEST-001
[14:45:55] PHASE: pre-flight complete — all 3 checks passed
[14:46:10] PHASE: plan started
[14:48:20] PHASE: plan complete
[14:49:18] QUALITY: verdict=BLOCKED findings=5
[14:50:21] QUALITY-FIX: fixing 5 findings in implementation_plan.md
[14:52:44] PHASE: branch started
[14:52:59] [developer] complete — branch feat/ST-TEST-001-user-registration created
[14:53:14] PHASE: red started
[14:53:38] [test-agent] started — writing failing tests
[14:56:13] WRITE: tests/test_email_validator.py
[14:56:13] WRITE: tests/test_password_utils.py
[14:56:13] WRITE: tests/test_user_repository.py
[14:56:13] WRITE: tests/test_user_service.py
[14:56:13] WRITE: tests/test_user_routes.py
[14:57:32] [test-agent] complete
[14:58:01] PHASE: red complete
[14:59:37] QUALITY: verdict=CHECK_PASSED findings=1
[15:00:18] PHASE: green started
[15:00:50] [developer] started — implementing code
[15:03:10] WRITE: src/models/user.py
[15:03:10] WRITE: src/exceptions.py
[15:03:10] WRITE: src/utils/password_utils.py
[15:03:10] WRITE: src/utils/email_validator.py
[15:03:10] WRITE: src/repositories/user_repository.py
[15:03:10] WRITE: src/services/user_service.py
[15:03:10] WRITE: src/api/user_routes.py
[15:03:39] [developer] complete
```

**Result:** Full layered architecture implemented (7 components, 5 test files), 29 tests written, 98% coverage, quality gates enforced at every phase. The plan quality review found 5 issues and fixed them before proceeding. Total: ~19 minutes.

**Validator output:**
```
[PASS] handoff.yml exists
[PASS] handoff.yml valid YAML
[PASS] field 'story_id' == 'ST-TEST-001'
[PASS] current_phase is valid
[PASS] current_phase beyond pending
[PASS] completed_phases non-empty
[PASS] completed_phases in correct order
[PASS] plan_summary populated
[PASS] plan_summary has components
[PASS] plan_summary has test_plan
[PASS] implementation_plan.md created
[PASS] test_summary exists
[PASS] at least 1 test created
[PASS] test_files listed
[PASS] code_summary exists
[PASS] all tests green
[PASS] coverage recorded
[PASS] code files listed
[PASS] on feature branch
```

### File System Monitor

The external FileMonitor tracks every file creation and modification in real time, providing independent observability into the agent's work:

```
[MONITOR] +160s new: .shaktra/stories/ST-TEST-001/implementation_plan.md (10.4KB)
[MONITOR] +400s modified: implementation_plan.md (10.4KB → 14.8KB, +4.4KB)   ← quality fix
[MONITOR] +590s new: tests/__init__.py (0B)
[MONITOR] +610s new: tests/test_email_validator.py (2.6KB)
[MONITOR] +641s new: tests/test_user_service.py (4.9KB)
[MONITOR] +981s new: src/models/user.py (530B)
[MONITOR] +1031s new: src/services/user_service.py (2.7KB)
[MONITOR] +1071s modified: .pytest_cache/v/cache/lastfailed (432B → 2B, -430B)  ← all tests pass
[MONITOR] +1081s new: .coverage (52.0KB)
```

## Prerequisites

- Python 3.10+ with `pyyaml` installed (`pip install pyyaml`)
- Claude Code CLI (`claude`) on your PATH
- A valid API key configured in Claude Code

## Running Tests

From the repo root:

```bash
# List all available tests
python3 tests/workflows/run_workflow_tests.py --list

# Run just smoke tests (fast, cheap)
python3 tests/workflows/run_workflow_tests.py --smoke

# Run a single test
python3 tests/workflows/run_workflow_tests.py --test tpm

# Run a test group
python3 tests/workflows/run_workflow_tests.py --group greenfield

# Run negative tests only (error paths)
python3 tests/workflows/run_workflow_tests.py --negative

# Run all tests
python3 tests/workflows/run_workflow_tests.py

# Keep temp directories after tests (for debugging)
python3 tests/workflows/run_workflow_tests.py --test tpm --keep-dirs

# Use a specific model
python3 tests/workflows/run_workflow_tests.py --test tpm --model claude-sonnet-4-5-20250929
```

### Live Monitoring

When a test starts, the runner prints a `tail -f` command:

```
──────────────────────────────────────────────────
[1/1] tpm (timeout: 1500s)
  Live log:  tail -f /var/folders/.../shaktra-test-greenfield-abc123/.shaktra-test.log
```

**Copy-paste that command into a second terminal** to watch the test unfold in real time. The log combines two sources:

1. **Agent events** — logged by sub-agents per CLAUDE.md instructions (timestamped):
   ```
   [10:33:32] [shaktra-tpm] started — planning user authentication feature
   [10:34:04] WRITE: .shaktra/designs/TestProject-design.md
   [10:38:34] QUALITY: verdict=BLOCKED findings=4
   [10:38:35] QUALITY-FIX: fixing 4 findings in .shaktra/designs/TestProject-design.md
   [10:41:05] PHASE: Story creation started
   ```

2. **File system events** — logged by the external FileMonitor (prefixed `[MONITOR]`):
   ```
   [MONITOR] +170s new: .shaktra/designs/TestProject-design.md (18.4KB)
   [MONITOR] +440s modified: .shaktra/designs/TestProject-design.md (18.4KB → 22.5KB, +4.2KB)
   [MONITOR] +550s new: .shaktra/stories/ST-001.yml (8.3KB)
   ```

Together, these give you full visibility into what's happening — which agents are running, what quality review found, which files were created or modified, and how large they are.

### File-Read Tracking

The test runner uses `--output-format stream-json` to capture every Read tool invocation — including reads from sub-agents spawned via the Task tool. This tells you which reference files each workflow actually consulted:

```
  => PASS (138.5s)
  Reads: 8/8 expected patterns matched
  Files read: 17 unique
```

Tests can declare `expected_reads` patterns — substring matches against Read file paths. For example, the dev test expects agents to read coding practices, security practices, quality definitions, and severity taxonomy before writing code. The patterns are portable (not tied to absolute paths).

After completion, the test log gets a `[READ-MANIFEST]` section:

```
[READ-MANIFEST] Files read during test:
[READ-MANIFEST]   [plugin] skills/shaktra-tdd/coding-practices.md
[READ-MANIFEST]   [plugin] skills/shaktra-tdd/security-practices.md
[READ-MANIFEST]   [plugin] skills/shaktra-quality/comprehensive-review.md
[READ-MANIFEST]   [plugin] skills/shaktra-reference/severity-taxonomy.md
[READ-MANIFEST]   [project] .shaktra/settings.yml
[READ-MANIFEST]   [project] .shaktra/stories/ST-TEST-001.yml
[READ-MANIFEST] Total: 17 unique files
```

The markdown report includes a per-test "Reference Files Read" section with the full list and expected reads results.

File-read tracking also serves as a regression check — when adding new reference materials or changing agent workflows, the read manifest confirms agents are actually consulting the files they're supposed to. If a refactor accidentally removes a file read, the `expected_reads` check will flag it.

## Available Tests

### Positive Tests (14)

| Test | Category | What It Tests | Timeout | Turns |
|------|----------|---------------|---------|-------|
| `help` | smoke | Skill loads, outputs help text | 2m | 5 |
| `doctor` | smoke | Health check runs without error | 3m | 15 |
| `status-dash` | smoke | Dashboard renders without error | 3m | 15 |
| `general` | smoke | General question answering | 3m | 10 |
| `workflow` | smoke | Workflow routing suggestion | 3m | 10 |
| `init-greenfield` | greenfield | `.shaktra/` structure, settings, templates | 5m | 15 |
| `pm` | greenfield | PRD creation, personas, journey maps | 15m | 30 |
| `tpm` | greenfield | Design doc, quality review, stories, sprints, memory | 25m | 60 |
| `dev` | greenfield | TDD pipeline: plan, branch, tests, code, quality | 30m | 65 |
| `review` | greenfield | Code review findings, verdict, memory capture | 15m | 35 |
| `tpm-hotfix` | hotfix | Trivial-tier story creation, no sprint allocation | 10m | 30 |
| `init-brownfield` | brownfield | `.shaktra/` for existing project | 5m | 15 |
| `analyze` | brownfield | 9-dimension codebase analysis | 15m | 40 |
| `bugfix` | bugfix | Bug diagnosis, TDD fix, quality review | 15m | 55 |

### Negative Tests (5)

Negative tests verify error paths — they should detect problems at pre-flight and stop quickly.

| Test | Category | What It Tests | Timeout | Turns |
|------|----------|---------------|---------|-------|
| `dev-no-settings` | negative | Dev rejects missing settings.yml | 2m | 10 |
| `dev-blocked-story` | negative | Dev rejects story blocked by dependency | 2m | 10 |
| `dev-sparse-story` | negative | Dev rejects story missing required fields | 2m | 10 |
| `review-incomplete-dev` | negative | Review detects incomplete development | 2m | 10 |
| `init-already-exists` | negative | Init detects `.shaktra/` already exists | 2m | 5 |

### Test Independence

Every test gets its own fresh temp directory with isolated fixtures. Tests can be run in any order, individually or in groups. There are no dependencies between tests.

Each test's setup function prepares the exact `.shaktra/` state it needs:
- **Smoke tests:** greenfield `.shaktra/` with settings
- **Dev test:** pre-built story + design doc (no prior TPM run needed)
- **Review test:** completed dev handoff + actual code files (no prior dev run needed)
- **Negative tests:** deliberately broken state (missing settings, blocked stories, etc.)

### Time and Cost Expectations

| Scope | Est. Time | Est. Cost |
|-------|-----------|-----------|
| Smoke tests (`--smoke`) | 2-3 min | ~$0.10 |
| Negative tests (`--negative`) | 5-10 min | ~$0.50 |
| Single workflow (`--test tpm`) | 15-25 min | ~$2-5 |
| Full suite (all 19 tests) | 60-90 min | ~$10-20 |

Costs depend on model choice. Using `--model claude-sonnet-4-5-20250929` is recommended for testing (good balance of speed and capability). Opus is more capable but slower and more expensive.

> **Be patient with long-running workflows.** Tests like `dev` (30 min timeout), `tpm` (25 min), and `bugfix` (15 min) involve multiple sub-agents, quality review loops, and code generation — these take real time. Execution speed also varies with API latency, model load, and network conditions. **Do not kill a test just because it appears quiet for a few minutes** — quality review and code generation phases often have long gaps between log entries while the model is thinking. Use the live log (`tail -f`) to confirm the test is still progressing. If a test genuinely stalls (no new log entries for 5+ minutes), it will eventually hit its timeout and be killed automatically.

## How It Works

```
python3 run_workflow_tests.py --test dev
  │
  ├─ 1. SETUP
  │   ├─ Create fresh temp directory with git init
  │   ├─ Copy .shaktra/ from plugin templates (settings, sprints, memory)
  │   ├─ Copy test fixtures (story YAML, design doc, code files as needed)
  │   └─ Append testing overrides to CLAUDE.md (quality limits, logging, auto-answer)
  │
  ├─ 2. LAUNCH
  │   ├─ Start FileMonitor thread (watches for new/modified files every 10s)
  │   └─ Start: claude --print --dangerously-skip-permissions --verbose \
  │                   --output-format stream-json --plugin-dir dist/shaktra/ \
  │                   --max-turns 65 -- "<test prompt>"
  │
  ├─ 3. EXECUTE (inside the claude session)
  │   ├─ Agent logs "Starting test dev" to .shaktra-test.log
  │   ├─ Agent invokes: Skill("shaktra-dev", args="develop story ST-TEST-001")
  │   │   └─ Skill runs the full workflow (sub-agents, quality gates, etc.)
  │   │      All agents log events to .shaktra-test.log per CLAUDE.md instructions
  │   ├─ Agent logs "Skill workflow complete"
  │   └─ Agent runs validator: python3 validators/validate_dev.py /path/to/test ST-TEST-001
  │
  ├─ 4. VALIDATE
  │   ├─ Validator checks .shaktra/ state (files exist, YAML valid, schemas correct)
  │   └─ Agent prints [TEST:dev] VERDICT: PASS or FAIL
  │
  ├─ 5. COLLECT
  │   ├─ Test runner parses stream-json: extracts text (for verdict) and Read tool paths
  │   ├─ Records duration, output lines, and file-read manifest
  │   ├─ Checks expected_reads patterns (if defined for this test)
  │   └─ Stops FileMonitor, writes [READ-MANIFEST] to test log
  │
  └─ 6. REPORT
      ├─ Print summary table to stderr
      └─ Write detailed markdown report to tests/workflows/reports/
```

### Direct Skill Invocation

Tests invoke skills directly — the same way a real user would. The test agent calls `Skill("shaktra-dev", args="develop story ST-TEST-001")` which triggers the full skill workflow including sub-agent spawning (sw-engineer, test-agent, developer, sw-quality, memory-curator). This means tests exercise the exact same code paths as production use.

### Validators

Validators are standalone Python scripts that check `.shaktra/` file state. They report pass/fail per check with a summary count. You can also run them independently after any workflow (automated or manual):

```bash
python3 tests/workflows/validators/validate_init.py /path/to/project TestProject greenfield python
python3 tests/workflows/validators/validate_tpm.py /path/to/project
python3 tests/workflows/validators/validate_dev.py /path/to/project ST-001
python3 tests/workflows/validators/validate_review.py /path/to/project ST-001
python3 tests/workflows/validators/validate_pm.py /path/to/project
python3 tests/workflows/validators/validate_analyze.py /path/to/project
python3 tests/workflows/validators/validate_bugfix.py /path/to/project
python3 tests/workflows/validators/validate_negative.py /path/to/project no_handoff ST-001
```

## Debugging Failed Tests

### 1. Use `--keep-dirs`

Always pass `--keep-dirs` when debugging. This preserves the temp directory so you can inspect `.shaktra/` state after the test:

```bash
python3 tests/workflows/run_workflow_tests.py --test tpm --keep-dirs
```

### 2. Check the live log

The `.shaktra-test.log` file in the test directory contains the combined agent + file monitor log. Read it to see exactly where the workflow stopped or failed:

```bash
cat /var/folders/.../shaktra-test-greenfield-abc123/.shaktra-test.log
```

### 3. Inspect `.shaktra/` directly

Browse the test directory's `.shaktra/` folder to see what was created:

```bash
ls -la /var/folders/.../shaktra-test-greenfield-abc123/.shaktra/
ls -la /var/folders/.../shaktra-test-greenfield-abc123/.shaktra/stories/
cat /var/folders/.../shaktra-test-greenfield-abc123/.shaktra/designs/*.md
```

### 4. Run the validator manually

Re-run the validator against the preserved test directory to see which specific checks failed:

```bash
python3 tests/workflows/validators/validate_tpm.py /var/folders/.../shaktra-test-greenfield-abc123
```

### 5. Check the report

Reports are written to `tests/workflows/reports/` with timestamps. They include the full captured output (last 100 lines) for each test.

### Common Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| TIMEOUT | Workflow didn't complete in time | Check live log for where it stalled. May need timeout increase or tighter CLAUDE.md constraints |
| UNKNOWN verdict | `claude --print` produced no verdict line | Agent ran out of turns (`--max-turns`) before reaching the validator step |
| Validator failures in lesson schema | Memory curator used wrong field names | Check memory-curator prompt template has explicit 5-field schema |
| 0 stories created | Scrummaster didn't respect story limit | Check CLAUDE.md override was injected (look at test dir's CLAUDE.md) |
| Quality loop ran 3x | CLAUDE.md override not picked up | Verify `_append_test_overrides` ran in setup function |

## Directory Structure

```
tests/workflows/
  README.md                  ← This file
  run_workflow_tests.py      ← CLI entry point and test orchestrator
  test_runner.py             ← Core engine (subprocess, FileMonitor, timeout handling)
  test_definitions.py        ← Test configs (setup functions, prompts, CLAUDE.md overrides)
  validators/
    validate_common.py       ← Shared check utilities (YAML, field exists, schema)
    validate_init.py         ← /shaktra:init checks
    validate_tpm.py          ← /shaktra:tpm checks (design docs, stories, sprints)
    validate_dev.py          ← /shaktra:dev checks (handoff, tests, coverage)
    validate_review.py       ← /shaktra:review checks (findings, verdict)
    validate_pm.py           ← /shaktra:pm checks (PRD, personas, journeys)
    validate_analyze.py      ← /shaktra:analyze checks (analysis artifacts)
    validate_bugfix.py       ← /shaktra:bugfix checks (diagnosis, fix)
    validate_negative.py     ← Negative test checks (error detection, no handoff, no progression)
  fixtures/
    greenfield/              ← PRD, architecture doc, design doc, code files, handoff fixtures
    brownfield/              ← Sample Python project for analysis tests
    stories/                 ← Pre-built story YAML for dev/review tests
    negative/                ← Broken state fixtures (blocked stories, sparse stories, incomplete handoff)
  reports/                   ← Generated markdown reports (gitignored)
```
