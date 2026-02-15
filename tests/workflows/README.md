# Shaktra Workflow Tests

End-to-end tests that verify `/shaktra:*` skills execute correctly in a real Claude Code session. Each test launches a fresh `claude --print` session with the plugin loaded, invokes a skill, and validates the resulting `.shaktra/` state.

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

### Test Scoping via CLAUDE.md Overrides

Tests need to prove workflows work, not produce production-quality output. To keep tests fast and affordable, the test framework injects constraints into the test project's `CLAUDE.md` — the standard mechanism for project-level instructions that all agents read:

- **Quality loops: 1 iteration** (production default is 3) — proves the loop runs without exhausting time
- **Story creation: 2 stories max** — proves the scrummaster creates valid stories without generating 10+
- **Sprint planning: 1 sprint** — proves allocation works
- **No clarification prompts** — agents make reasonable assumptions instead of blocking on user input

These overrides live in `test_definitions.py` (`_TEST_OVERRIDES`) and are appended to the test directory's `CLAUDE.md` during setup. **No plugin files are modified.**

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

## Available Tests

| Test | Group | What It Tests | Timeout | Est. Time |
|------|-------|---------------|---------|-----------|
| `help` | smoke | Skill loads, outputs help text | 2 min | ~30s |
| `doctor` | smoke | Health check runs without error | 3 min | ~1 min |
| `status-dash` | smoke | Dashboard renders without error | 3 min | ~1 min |
| `init-greenfield` | greenfield | `.shaktra/` structure, settings, templates | 5 min | ~2 min |
| `pm` | greenfield | PRD creation, personas, journey maps | 15 min | ~10 min |
| `tpm` | greenfield | Design doc → quality review → stories → sprints → memory | 25 min | ~20 min |
| `dev` | greenfield | TDD pipeline: plan → tests → code → quality gates | 20 min | ~15 min |
| `review` | greenfield | Code review findings, verdict, memory capture | 15 min | ~10 min |
| `tpm-hotfix` | hotfix | Trivial-tier story creation, no sprint allocation | 10 min | ~5 min |
| `init-brownfield` | brownfield | `.shaktra/` for existing project | 5 min | ~2 min |
| `analyze` | brownfield | 9-dimension codebase analysis | 15 min | ~10 min |
| `bugfix` | bugfix | Bug diagnosis and TDD fix | 15 min | ~10 min |

### Test Groups

Tests within `greenfield` and `brownfield` groups share a temp directory and run sequentially — each step builds on the previous one's state:

```
greenfield:  init-greenfield → pm → tpm → dev → review
brownfield:  init-brownfield → analyze
```

The `hotfix` and `bugfix` groups run in isolated directories.

### Time and Cost Expectations

| Scope | Est. Time | Est. Cost |
|-------|-----------|-----------|
| Smoke tests (`--smoke`) | 2-3 min | ~$0.10 |
| Single workflow (`--test tpm`) | 15-25 min | ~$2-5 |
| Full suite (all tests) | 60-90 min | ~$10-20 |

Costs depend on model choice. Using `--model claude-sonnet-4-5-20250929` is recommended for testing (good balance of speed and capability). Opus is more capable but slower and more expensive.

## How It Works

```
python3 run_workflow_tests.py --test tpm
  │
  ├─ 1. SETUP
  │   ├─ Create temp directory with git init
  │   ├─ Copy .shaktra/ from plugin templates (settings, sprints, memory)
  │   ├─ Copy test fixtures (PRD, architecture docs)
  │   └─ Append testing overrides to CLAUDE.md (story limits, quality loop limits, logging)
  │
  ├─ 2. LAUNCH
  │   ├─ Start FileMonitor thread (watches for new/modified files every 10s)
  │   └─ Start: claude --print --dangerously-skip-permissions \
  │                   --plugin-dir dist/shaktra/ --max-turns 60 \
  │                   -- "<test prompt>"
  │
  ├─ 3. EXECUTE (inside the claude session)
  │   ├─ Agent logs "Starting test tpm" to .shaktra-test.log
  │   ├─ Agent invokes: Skill("shaktra-tpm", args="...")
  │   │   └─ Skill runs the full workflow (sub-agents, quality gates, etc.)
  │   │      All agents log events to .shaktra-test.log per CLAUDE.md instructions
  │   ├─ Agent logs "Skill workflow complete"
  │   └─ Agent runs validator: python3 validators/validate_tpm.py /path/to/test
  │
  ├─ 4. VALIDATE
  │   ├─ Validator checks .shaktra/ state (files exist, YAML valid, schemas correct)
  │   └─ Agent prints [TEST:tpm] VERDICT: PASS or FAIL
  │
  ├─ 5. COLLECT
  │   ├─ Test runner parses verdict from stdout
  │   ├─ Records duration and output
  │   └─ Stops FileMonitor
  │
  └─ 6. REPORT
      ├─ Print summary table to stderr
      └─ Write detailed markdown report to tests/workflows/reports/
```

### Direct Skill Invocation

Tests invoke skills directly — the same way a real user would. The test agent calls `Skill("shaktra-tpm", args="...")` which triggers the full skill workflow including sub-agent spawning (architect, scrummaster, quality agents, memory curator). This means tests exercise the exact same code paths as production use.

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
  test_definitions.py        ← Test configs (prompts, setup functions, CLAUDE.md overrides)
  validators/
    validate_common.py       ← Shared check utilities (YAML, field exists, schema)
    validate_init.py         ← /shaktra:init checks
    validate_tpm.py          ← /shaktra:tpm checks (design docs, stories, sprints)
    validate_dev.py          ← /shaktra:dev checks (handoff, tests, coverage)
    validate_review.py       ← /shaktra:review checks (findings, verdict)
    validate_pm.py           ← /shaktra:pm checks (PRD, personas, journeys)
    validate_analyze.py      ← /shaktra:analyze checks (analysis artifacts)
    validate_bugfix.py       ← /shaktra:bugfix checks (diagnosis, fix)
  fixtures/
    greenfield/              ← PRD + architecture doc for planning tests
    brownfield/              ← Sample Python project for analysis tests
    stories/                 ← Pre-built story YAML for dev tests (if running dev standalone)
  reports/                   ← Generated markdown reports (gitignored)
```
