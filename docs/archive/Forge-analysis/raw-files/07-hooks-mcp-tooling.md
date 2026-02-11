# Forge Analysis: Hooks, MCP Servers & Tooling Infrastructure

## 1. Hooks Inventory

Forge defines seven hook scripts across three categories: Claude Code lifecycle hooks, traditional git CI hooks, and utility/status hooks.

### 1.1 `block-main-branch.sh` -- Branch Protection Hook

**Location:** `.claude/hooks/block-main-branch.sh`
**Trigger:** `PreToolUse` on `Bash` operations (configured in `settings.json`)
**Language:** Bash
**Purpose:** Prevents code modifications when the working tree is on a protected branch.

**Protected branches:** `main`, `master`, `production`, `prod`

**Logic flow:**
1. Checks if inside a git repository (`git rev-parse --git-dir`)
2. Gets current branch via `git branch --show-current`
3. Allows detached HEAD or non-git scenarios
4. Checks bypass env var `FORGE_ALLOW_MAIN_BRANCH`
5. Iterates over protected branch names; exits 1 if matched

```bash
PROTECTED_BRANCHES=("main" "master" "production" "prod")

if [ "${FORGE_ALLOW_MAIN_BRANCH:-}" = "1" ] || [ "${FORGE_ALLOW_MAIN_BRANCH:-}" = "true" ]; then
    exit 0
fi

for protected in "${PROTECTED_BRANCHES[@]}"; do
    if [ "$BRANCH" = "$protected" ]; then
        # ... error message ...
        exit 1
    fi
done
```

**Exit codes:** 0 = allow, 1 = block

**Bypass:** `export FORGE_ALLOW_MAIN_BRANCH=1`

**Note:** There is a minor cosmetic bug on lines 37/39/51 -- `echo "=" *60` and `echo "="*60` do not produce the intended visual separator. The `*60` is not a repeat operator in bash; it would glob-expand or print literally. Should be `echo "$(printf '=%.0s' {1..60})"` or a heredoc.

---

### 1.2 `check-p0-findings.py` -- Critical Finding Blocker

**Location:** `.claude/hooks/check-p0-findings.py`
**Trigger:** Intended for `Stop` events (prevents Claude from stopping with unresolved P0 issues)
**Language:** Python 3
**Dependencies:** `yaml`, `re`, `glob` (all stdlib except `yaml` which requires PyYAML)

**Purpose:** Scans forge temporary files for unresolved P0 (critical) findings -- security vulnerabilities, data loss risks, race conditions, critical bugs.

**Logic flow:**
1. Checks bypass via `FORGE_SKIP_P0_CHECK` env var
2. Searches for quality report files in `forge/.tmp/*/quality_report.yml`, `forge/.tmp/*/handoff.yml`
3. Parses YAML files looking for `quality_summary.findings` where `severity == 'P0'`
4. Additionally scans all `.yml` files in `forge/.tmp` for regex patterns like `P0:`, `CRITICAL:`, `**P0**`
5. Deduplicates findings by (dimension, issue) tuple
6. If any P0 findings exist, prints detailed error and exits 1

```python
p0_patterns = [
    r'P0[:\s]+',
    r'CRITICAL[:\s]+',
    r'\*\*P0\*\*',
    r'Severity:\s*P0',
    r'severity:\s*["\']?P0',
]
```

**Bypass:** `export FORGE_SKIP_P0_CHECK=1`

**Critical note:** This hook is configured under `"Stop": []` in settings.json -- the array is EMPTY. This means the hook is defined but NOT actually wired up. It would need to be added to the Stop array to function.

---

### 1.3 `ci/pre-commit.sh` -- Git Pre-Commit Hook

**Location:** `.claude/hooks/ci/pre-commit.sh`
**Trigger:** Git pre-commit (requires manual installation: `cp .claude/hooks/ci/pre-commit.sh .git/hooks/pre-commit`)
**Language:** Bash

**Purpose:** Runs linting, type checking, and quick tests before each commit.

**Three-step pipeline:**

**Step 1 -- Lint staged files:**
- JavaScript/TypeScript: runs `eslint --fix` on staged `.js/.ts/.tsx/.jsx` files, then re-adds them
- Python: runs `ruff check --fix` + `ruff format` (fallback to `black`) on staged `.py` files, then re-adds them

**Step 2 -- Type check:**
- TypeScript: `tsc --noEmit` (if `tsconfig.json` exists)
- Python: `mypy . --ignore-missing-imports` (if `pyproject.toml` exists)
- Both are warnings only (stderr redirected, non-blocking)

**Step 3 -- Quick tests:**
- Python: `pytest --tb=line -q --co -q` (only collects tests, does not run them -- this is effectively a no-op for actual test execution)
- JavaScript: `npm test -- --passWithNoTests --watchAll=false`
- Both are warnings only

```bash
if command -v eslint &> /dev/null; then
    JS_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(js|ts|tsx|jsx)$' || true)
    if [ -n "$JS_FILES" ]; then
        echo "$JS_FILES" | xargs eslint --fix
        echo "$JS_FILES" | xargs git add
    fi
fi
```

**Issue:** The pytest step uses `--co -q` which only _collects_ tests (lists them) -- it does not execute them. The pipe to `head -20` and `|| true` further diminishes its value. This is basically a no-op.

---

### 1.4 `ci/pre-push.sh` -- Git Pre-Push Hook

**Location:** `.claude/hooks/ci/pre-push.sh`
**Trigger:** Git pre-push (requires manual installation: `cp .claude/hooks/ci/pre-push.sh .git/hooks/pre-push`)
**Language:** Bash

**Purpose:** Runs full test suite, coverage check, and security scan before pushing.

**Three-step pipeline:**

**Step 1 -- Full test suite:**
- Python: `pytest --tb=short -q` (blocking -- fails the push on test failure)
- JavaScript: `npm test` (blocking)

**Step 2 -- Coverage threshold (80%):**
- Python: `pytest --cov --cov-report=term-missing --cov-fail-under=80` with grep/awk to extract percentage
- JavaScript: `npm run coverage` (if configured)
- Warning only

**Step 3 -- Security scan:**
- Python: `bandit -r src/ -ll -q` (warning only)
- Node: `npm audit --audit-level=high` (warning only)
- Secrets: `git secrets --scan` (warning only)

```bash
if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    if command -v pytest &> /dev/null; then
        pytest --tb=short -q || { echo "Tests failed. Push aborted."; exit 1; }
    fi
fi
```

**Key distinction:** Only test failures actually block the push. Coverage and security issues are warnings only.

---

### 1.5 `forge-statusline.sh` -- Status Display Hook

**Location:** `.claude/hooks/forge-statusline.sh`
**Trigger:** Not configured in settings.json (designed for Claude Code status bar integration)
**Language:** Bash

**Purpose:** Generates a one-line status summary of current story state.

**Output format:** `ST-001 [GREEN] 87% | scope:validation | P0:0 P1:2`

**Components extracted:**
- **Story ID:** From most recent `forge/.tmp/*/handoff.yml` via `story_id:` field
- **Phase:** From `current_phase:` field, mapped to display names:
  - `plan` -> `PLAN`
  - `tests` -> `RED`
  - `code` -> `GREEN`
  - `quality` -> `REVIEW`
- **Coverage:** From `coverage:` field in handoff
- **Scope:** From `forge/stories/{story_id}.yml` via `scope:` field
- **Findings:** P0/P1 counts via `grep -c 'severity:\s*P0'` on handoff

```bash
get_phase() {
    local story_id="$1"
    local handoff="forge/.tmp/${story_id}/handoff.yml"
    if [ -f "$handoff" ]; then
        local phase=$(grep -oP 'current_phase:\s*\K\S+' "$handoff" 2>/dev/null)
        case "$phase" in
            plan)    echo "PLAN" ;;
            tests)   echo "RED" ;;
            code)    echo "GREEN" ;;
            quality) echo "REVIEW" ;;
            *)       echo "$phase" ;;
        esac
    fi
}
```

**Platform issue:** Uses `grep -oP` (Perl-compatible regex) which is not available on macOS default grep. Requires `ggrep` or GNU grep.

---

### 1.6 `validate-story-alignment.sh` -- Story Scope Guard

**Location:** `.claude/hooks/validate-story-alignment.sh`
**Trigger:** `PreToolUse` on `Write|Edit` operations (configured in settings.json)
**Language:** Bash

**Purpose:** Ensures file changes align with the active story's declared scope and file list. Warns (does not block) when editing files outside the story's declared scope.

**Logic flow:**
1. Receives tool input JSON as `$1` argument
2. Extracts `file_path` from JSON via grep
3. Skips validation for always-allowed paths (forge infrastructure, config files, README)
4. Finds active story from most recent `forge/.tmp/*/handoff.yml`
5. Loads story file from `forge/stories/{story_id}.yml`
6. Extracts declared files from `files:` section
7. Matches file path against declared files (exact, suffix, wildcard)
8. **Warns but does NOT block** (exits 0 even on mismatch)

```bash
ALLOWED_PATTERNS=(
    "forge/stories/"
    "forge/memory/"
    "forge/docs/"
    "forge/.tmp/"
    "forge/settings.yml"
    ".claude/"
    "CLAUDE.md"
    "README.md"
    "package.json"
    "requirements.txt"
    "pyproject.toml"
    "Cargo.toml"
    "go.mod"
)
```

**Critical observation:** Despite the header comment saying "Exit codes: 1: Change violates story scope (blocks the edit)", the actual implementation exits 0 on line 116 with a comment: "Exit 0 to allow (use exit 1 to block)". This is a **warn-only** hook that never blocks. The docstring is misleading.

**Platform issue:** Same `grep -oP` problem as forge-statusline.sh -- incompatible with macOS default grep.

---

### 1.7 `validate-story.py` -- Story Schema Validator

**Location:** `.claude/hooks/validate-story.py`
**Trigger:** Intended as `PreToolUse` on `Write|Edit` (documented in docstring but NOT in settings.json hook configuration)
**Language:** Python 3
**Dependencies:** `yaml` (PyYAML)

**Purpose:** Validates story files against tier-specific schema requirements before allowing implementation.

**Tier system with escalating requirements:**

| Tier | Required Fields Count | Trigger Conditions |
|------|----------------------|-------------------|
| SIMPLE | 8 fields | points <= 2, risk = low, single file |
| STANDARD | 16 fields | Default |
| COMPLEX | 21 fields | points >= 8, risk = high, critical paths |

**Field requirements by tier:**

```python
SIMPLE_FIELDS = [
    "id", "title", "description", "files",
    "acceptance_criteria", "tests", "risk_assessment", "metadata"
]

STANDARD_FIELDS = SIMPLE_FIELDS + [
    "interfaces", "io_examples", "error_handling",
    "logging_rules", "observability_rules",
    "invariants", "concurrency"
]

COMPLEX_FIELDS = STANDARD_FIELDS + [
    "failure_modes", "determinism", "resource_safety",
    "edge_case_matrix", "feature_flags"
]
```

**Auto-detection logic for tier:**
- COMPLEX if: story_points >= 8, risk = high, scope includes "security" or "integration", has feature_flags, touches critical paths (auth/, payment/, billing/, security/)
- SIMPLE if: points <= 2, risk = low, single file
- STANDARD: default

**Validation checks performed:**
1. Missing required fields for tier
2. Single-scope rule (emits `REPLAN_SCOPE_FANOUT`)
3. Feature flag requirements for high-risk stories (emits `MISSING_FEATURE_FLAGS`)
4. Minimum acceptance criteria (3+ for STANDARD/COMPLEX)
5. Test coverage mapping (`covers` field required)
6. Test fields on spec elements (`failure_modes`, `invariants`, `edge_case_matrix`)
7. Edge case matrix category validity (10 valid categories) and minimum coverage
8. Dependency validation (self-reference, circular dependency detection)

**Guard tokens emitted:** `FIX_STORY_SCHEMA`, `REPLAN_SCOPE_FANOUT`, `MISSING_FEATURE_FLAGS`, `EDGE_CASE_COVERAGE_LOW`

**Valid edge case categories:**
```python
VALID_EDGE_CASE_CATEGORIES = {
    'invalid_input', 'dependency_failure', 'duplicate', 'concurrency',
    'limits', 'time', 'config', 'lifecycle', 'capacity', 'upgrade'
}
```

**Critical note:** Despite being documented as a PreToolUse hook, it is NOT configured in `settings.json`. The `settings.json` only configures `validate-story-alignment.sh` and `block-main-branch.sh`. This script would need to be either called from the alignment hook or added to the hooks configuration separately.

---

## 2. Hook Architecture

### 2.1 Configuration in settings.json

Hooks are configured in `.claude/settings.json` under the `hooks` key:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate-story-alignment.sh \"$TOOL_INPUT\""
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-main-branch.sh"
          }
        ]
      }
    ],
    "Stop": []
  }
}
```

### 2.2 Event Types and Triggering

| Event | Matcher | Hook | Active? |
|-------|---------|------|---------|
| `PreToolUse` | `Write\|Edit` | validate-story-alignment.sh | Yes (warn-only) |
| `PreToolUse` | `Bash` | block-main-branch.sh | Yes (blocking) |
| `Stop` | (none) | check-p0-findings.py | **NO** (empty array) |
| Git pre-commit | N/A | ci/pre-commit.sh | Requires manual installation |
| Git pre-push | N/A | ci/pre-push.sh | Requires manual installation |

### 2.3 Environment Variables Used by Hooks

From `settings.json` env section:
```json
{
  "env": {
    "FORGE_MODE": "development",
    "FORGE_MIN_COVERAGE": "90",
    "FORGE_ENFORCE_TDD": "1"
  }
}
```

Additional env vars referenced by hooks:
- `FORGE_ALLOW_MAIN_BRANCH` -- bypass branch protection
- `FORGE_SKIP_P0_CHECK` -- bypass P0 finding check
- `CLAUDE_PROJECT_DIR` -- Claude Code project directory (used in hook commands)
- `TOOL_INPUT` -- JSON input passed to PreToolUse hooks
- `GITHUB_TOKEN` -- for MCP server authentication

### 2.4 Permission System

`settings.json` defines a deny/allow permission model:

**Deny rules (always applied first):**
```json
"deny": [
    "Read(.env*)",
    "Read(**/credentials*)",
    "Read(**/*secret*)",
    "Bash(rm -rf:*)"
]
```

**Allow rules:**
```json
"allow": [
    "Bash(python .claude/skills/forge-check/scripts/*.py:*)",
    "Bash(python .claude/forge/scripts/*.py:*)",
    "Bash(python .claude/hooks/*.py:*)",
    "Bash(pytest:*)",
    "Bash(git:*)",
    "Bash(npm test:*)",
    "Bash(npm run:*)"
]
```

`settings.local.json` adds broader permissions:
```json
"allow": [
    "Skill(forge-workflow)",
    "Skill(forge-workflow:*)",
    "Bash(xargs:*)",
    "Bash(python:*)",
    "Bash(grep:*)",
    "WebFetch(domain:www.aitmpl.com)",
    "WebSearch",
    "Bash(ls:*)",
    "Bash(tree:*)"
]
```

**Security concern:** `settings.local.json` grants `Bash(python:*)` which is effectively unrestricted Python execution, potentially bypassing the narrower allow rules in `settings.json`.

---

## 3. MCP Servers

### 3.1 MCP Configuration

**Location:** `.claude/mcp.json`

```json
{
  "mcpServers": {
    "forge-github": {
      "command": "node",
      "args": [".claude/mcp/servers/github-server.js"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "disabled": true,
      "_comment": "GitHub integration for PR creation, issue management. Enable when implemented."
    },
    "forge-ci": {
      "command": "python3",
      "args": [".claude/mcp/servers/ci-server.py"],
      "disabled": true,
      "_comment": "CI/CD integration for build status, test results. Enable when implemented."
    }
  }
}
```

**Both servers are disabled.** They are stubs/design documents, not functional implementations.

### 3.2 Transport Protocol

Both servers use stdio transport (command-line invocation with stdin/stdout communication), which is the standard MCP transport for local tool servers.

---

## 4. CI Server (`ci-server.py`)

**Location:** `.claude/mcp/servers/ci-server.py`
**Status:** NOT IMPLEMENTED -- stub only
**Language:** Python 3
**Planned Dependencies:** `mcp`, `httpx`

The file is entirely documentation with a stub exit:

```python
import sys
print("Forge CI MCP Server not yet implemented", file=sys.stderr)
print("See docstring in this file for implementation guide", file=sys.stderr)
sys.exit(1)
```

### 4.1 Planned Tools

| Tool | Parameters | Purpose | Consumer |
|------|-----------|---------|----------|
| `ci_get_build_status` | branch, workflow_name | Get CI build status for a branch | forge-quality agent |
| `ci_get_test_results` | run_id, test_suite | Get detailed test results | forge-quality for coverage |
| `ci_trigger_workflow` | workflow_name, ref, inputs | Trigger GitHub Actions workflow | forge-developer agent |
| `ci_get_coverage_report` | run_id | Get code coverage report | forge-quality for threshold verification |

### 4.2 Implementation Skeleton Provided

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("forge-ci")

@server.tool()
async def ci_get_build_status(branch: str, workflow_name: str = None) -> dict:
    '''Get CI build status for a branch'''
    pass

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)
```

### 4.3 Assessment

This is purely aspirational. The `gh` CLI tool (available in Claude Code natively) can already perform most of these operations. A custom MCP server adds complexity for marginal benefit unless the goal is to provide a more structured, type-safe interface for agents.

---

## 5. GitHub Server (`github-server.js`)

**Location:** `.claude/mcp/servers/github-server.js`
**Status:** NOT IMPLEMENTED -- stub only
**Language:** JavaScript (Node.js)
**Planned Dependencies:** `@modelcontextprotocol/sdk`, `@octokit/rest`

```javascript
console.error('Forge GitHub MCP Server not yet implemented');
console.error('See comments in this file for implementation guide');
process.exit(1);
```

### 5.1 Planned Tools

| Tool | Parameters | Purpose | Consumer |
|------|-----------|---------|----------|
| `github_create_pr` | title, body, base_branch, draft | Create PR from current branch | forge-quality agent |
| `github_list_issues` | labels, state, assignee | List matching open issues | forge-designer agent |
| `github_get_pr_comments` | pr_number | Get review comments | forge-quality for context |
| `github_add_pr_comment` | pr_number, body | Add comment to PR | forge-quality for automated notes |

### 5.2 Implementation Skeleton Provided

```javascript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server({
    name: 'forge-github',
    version: '1.0.0'
}, {
    capabilities: { tools: {} }
});

const transport = new StdioServerTransport();
server.connect(transport);
```

### 5.3 Assessment

Same as CI server -- Claude Code already has `gh` CLI access. The value proposition of a custom MCP server is unclear unless providing higher-level abstractions (e.g., "create PR with forge template" that auto-populates story context).

---

## 6. Python Scripts Pipeline

The scripts in `.claude/scripts/` form a self-learning system that tracks workflow events, detects patterns, and applies learned guidance. They operate as a pipeline:

### 6.1 Data Flow

```
Workflow Events
    |
    v
[log_event.py] --> events.jsonl (JSONL append-only log)
    |                    |
    v                    v
[sanitize.py]    [pattern_analysis.py]
(strips secrets)     |
                     v
              pattern_proposals.yml
                     |
                     v (auto-merge if thresholds met)
              patterns.yml (active pattern library)
                     |
                     v
              [pattern_matcher.py] --> matches patterns to current workflow
                     |
                     v
              [apply_pattern.py] --> injects guidance/validation
                     |
                     v
              [learning_state.py] --> tracks analysis timing/throttling
```

### 6.2 Script-by-Script Breakdown

#### `log_event.py` -- Event Collection

**Purpose:** Non-blocking event logging with in-memory queue and periodic flush.

**Configuration:**
- `FLUSH_THRESHOLD = 10` (flush after 10 events)
- `FLUSH_INTERVAL = 60` (flush after 60 seconds)
- `EVENTS_FILE = "forge/memory/learning/events.jsonl"`

**Event types supported (via helper functions):**
- `workflow_started`, `workflow_completed`, `workflow_failed`
- `phase_started`, `phase_completed`, `phase_failed`
- `guard_token_triggered`
- `clarification_requested`, `clarification_answered`
- `sub_agent_spawned`
- `sub_agent_retry_needed`, `sub_agent_retry_succeeded`, `sub_agent_retry_failed`
- `quality_finding`
- `deviation_detected`
- `pattern_applied`, `pattern_skipped`
- `user_override`

**Key design choice:** Uses relative imports (`from .sanitize import sanitize_context`) which means it must be invoked as a package, not as a standalone script. This is a potential footgun when called from hooks.

```python
EVENT_QUEUE: List[Dict[str, Any]] = []
LAST_FLUSH_TIME = time.time()

def log_event(event_type, context, story_id=None, workflow=None, phase=None):
    from .sanitize import sanitize_context
    event = {
        "event_id": generate_event_id(),
        "timestamp": datetime.now().isoformat() + "Z",
        "event_type": event_type,
    }
    event["context"] = sanitize_context(context)
    EVENT_QUEUE.append(event)
    if len(EVENT_QUEUE) >= FLUSH_THRESHOLD or time_since_flush >= FLUSH_INTERVAL:
        flush_events()
```

**Cleanup:** Registers `atexit.register(ensure_flush_on_exit)` to flush on process exit.

#### `sanitize.py` -- Privacy Protection

**Purpose:** Strips sensitive data from event contexts before they are written to the learning log.

**Sensitive patterns detected:**
- API keys (base64-like long strings, OpenAI `sk-*`, Anthropic `sk-ant-*`)
- GitHub tokens (`ghp_*`, `gho_*`, `ghs_*`)
- AWS access keys (`AKIA*`)
- Passwords, secrets, tokens (by field name and value pattern)
- Email addresses
- Credit card numbers
- US Social Security Numbers
- PEM private keys
- JWTs (`eyJ*.*.*`)

**Sensitive field names (redacted by name regardless of value):**
```python
SENSITIVE_FIELD_NAMES = {
    'password', 'passwd', 'pwd', 'secret', 'api_key', 'apikey', 'api_secret',
    'client_secret', 'token', 'auth_token', 'access_token', 'refresh_token',
    'private_key', 'priv_key', 'credential', 'credentials', 'auth',
    'authorization', 'cookie', 'session', 'sessionid', 'session_id'
}
```

**Implementation:** Recursive sanitization with max depth of 10 to prevent infinite loops. Deep-copies input to avoid mutation.

**False positive risk:** The base64 pattern `[A-Za-z0-9+/]{40,}` is extremely broad and will match many non-secret strings (long file paths, hashes, UUIDs, etc.). This could lead to data loss in the learning log.

#### `pattern_analysis.py` -- Pattern Detection Engine

**Purpose:** Analyzes workflow events to detect recurring patterns automatically.

**Three pattern detectors:**

1. **Clarification Predictor:** Detects when clarifications are frequently requested for certain workflow/scope/complexity combinations. If >60% of stories with attribute X require clarification, creates a pattern.

2. **Deviation Detector:** Detects when expectations (planned values) deviate from actuals consistently. Groups by workflow/scope/complexity attributes.

3. **Quality Pattern (Workflow Outcome Predictor):** Detects when P0/P1 quality findings correlate with certain story attributes.

**Auto-approval thresholds:**
```python
AUTO_APPROVE_SAMPLE_SIZE = 15
AUTO_APPROVE_OCCURRENCE_RATE = 0.80
MANUAL_REVIEW_SAMPLE_SIZE = 10
MANUAL_REVIEW_OCCURRENCE_RATE = 0.60
```

**CLI commands:**
- `load-events` -- Load and summarize events
- `detect-patterns` -- Detect patterns without writing
- `write-proposals` -- Detect and write to `pattern_proposals.yml`
- `analyze` -- Full analysis with optional `--auto-merge`

**Pattern lifecycle:** `under_review` -> `active` (auto or manual) -> `deprecated` (low accuracy or stale)

#### `pattern_matcher.py` -- Pattern Query Engine

**Purpose:** Queries the pattern library to find patterns matching current workflow attributes.

**Matching logic:**
- Filters by status (active only), expiration (90-day TTL with refresh-on-use), confidence level
- Matches trigger conditions against: workflow type, story scope, story complexity, feature category
- Returns results sorted by accuracy (highest first), then confidence

```python
def query_patterns(workflow=None, story_scope=None, story_complexity=None,
                   feature_category=None, pattern_type=None, min_confidence="low"):
    # ... filters active patterns, matches conditions, sorts by accuracy
```

**Additional operations:** `disable_pattern()`, `enable_pattern()`, `update_pattern_refresh()`, `get_pattern_summary()`

#### `apply_pattern.py` -- Pattern Application

**Purpose:** Applies matched patterns by generating guidance text, validation checks, suggestions, warnings, or checklists.

**Orchestrator actions supported:**
- `inject_guidance` -- Generates text to inject into sub-agent prompts
- `validate_output` -- Validates output against pattern expectations
- `suggest_improvement` -- Returns suggestion text
- `inject_warning` -- Returns warning text
- `inject_checklist` -- Returns checklist text

**Performance tracking:** Records each application with:
- times_applied, times_helpful, times_not_helpful, accuracy
- Workflow-specific application counts
- User feedback entries with timestamps
- Trend calculation (comparing last 5 vs previous 5 applications)

**Auto-deprecation:** Patterns with accuracy < 50% after 5+ applications, or unused for 90+ days, are automatically deprecated.

#### `learning_state.py` -- Analysis Timing/Throttling

**Purpose:** Manages when pattern analysis should trigger.

**Trigger conditions:** Either 20+ new events OR 24+ hours since last analysis.

**State file:** `forge/memory/learning/last_analysis.yml`

```python
def should_trigger_analysis() -> tuple[bool, Optional[str]]:
    # ... checks new_events >= 20 or time_elapsed_hours >= 24
```

---

## 7. Sanitize Script Deep Dive

### 7.1 What It Sanitizes

The sanitize script (`sanitize.py`) provides a privacy firewall between workflow execution and the learning event log. Without it, sensitive data from the project being worked on could leak into `events.jsonl`.

### 7.2 Why It's Needed

The self-learning system logs rich context about every workflow event. This context may include:
- File contents or snippets that contain API keys
- Configuration values with passwords
- User data like emails from test fixtures
- Authentication tokens from CI/CD contexts

Without sanitization, `forge/memory/learning/events.jsonl` would become a liability -- a single file containing potentially every secret from the project.

### 7.3 Sanitization Approach

Three layers:
1. **Field-name based:** Any key in `SENSITIVE_FIELD_NAMES` is replaced with `[REDACTED]` regardless of value
2. **Value-pattern based:** Regex patterns applied to all string values
3. **Recursive:** Handles nested dicts and lists up to depth 10

### 7.4 Limitations

- **False positives:** The `[A-Za-z0-9+/]{40,}` pattern catches too broadly (base64-encoded data, SHA hashes, etc.)
- **False negatives:** Custom secret formats not in the pattern list will pass through
- **No streaming support:** Deep-copies entire context, which could be expensive for large contexts
- **Regex ordering:** Patterns are applied sequentially, and earlier matches may obscure later ones (e.g., the generic base64 pattern fires before the specific `sk-ant-*` pattern)

---

## 8. Hook-to-Workflow Integration

### 8.1 Integration Map

```
User invokes /forge develop ST-001
    |
    v
Claude Code starts writing files
    |
    v
[PreToolUse: Write|Edit] --> validate-story-alignment.sh
    |                              |
    |                              v
    |                        Checks file against story scope
    |                        (warn only, does not block)
    |
    v
[PreToolUse: Bash] --> block-main-branch.sh
    |                       |
    |                       v
    |                  Blocks if on main/master
    |
    v
Code changes proceed
    |
    v
Developer commits (if git hooks installed)
    |
    v
[pre-commit.sh] --> lint, type-check, quick tests
    |
    v
Developer pushes
    |
    v
[pre-push.sh] --> full tests, coverage, security scan
    |
    v
Claude Code session ends
    |
    v
[Stop event] --> (check-p0-findings.py -- NOT WIRED UP)
```

### 8.2 Learning System Integration

The learning system scripts are NOT directly integrated with hooks. They are designed to be called from within the agent/skill Python code:

```python
# In a skill or agent
from .scripts.log_event import log_workflow_started
log_workflow_started("develop", {"story_scope": ["validation"]}, story_id="ST-001")
```

The pattern matching would be invoked before spawning sub-agents:

```python
from .scripts.pattern_matcher import query_patterns
from .scripts.apply_pattern import apply_pattern

patterns = query_patterns(workflow="develop", story_scope=["validation"])
for pattern in patterns:
    result = apply_pattern(pattern, context)
    if result.get("guidance_text"):
        # Inject into sub-agent prompt
        prompt += result["guidance_text"]
```

### 8.3 Disconnected Components

Several hooks and scripts exist but are not wired into the running system:
- `check-p0-findings.py` -- defined but not in Stop hooks array
- `validate-story.py` -- documented as PreToolUse hook but not configured
- `forge-statusline.sh` -- no hook event configured
- `ci/pre-commit.sh` and `ci/pre-push.sh` -- require manual git hook installation
- All learning scripts -- library code, not hooked into any event

---

## 9. Dependencies

### 9.1 npm Dependencies (package.json)

```json
{
  "name": "simpletask",
  "devDependencies": {
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0"
  }
}
```

**Note:** The package.json is for the "SimpleTask" demo application that Forge was applied to, NOT for Forge itself. Forge has no dedicated npm package.json. The MCP servers reference `@modelcontextprotocol/sdk` and `@octokit/rest` as planned dependencies but these are not installed.

### 9.2 Python Dependencies (Implicit)

Required by various scripts but never declared in a `requirements.txt` or `pyproject.toml`:

| Package | Used By | Stdlib? |
|---------|---------|---------|
| `yaml` (PyYAML) | check-p0-findings.py, validate-story.py, apply_pattern.py, learning_state.py, pattern_analysis.py, pattern_matcher.py | No |
| `json` | log_event.py, sanitize.py, pattern_analysis.py | Yes |
| `re` | check-p0-findings.py, sanitize.py | Yes |
| `glob` | check-p0-findings.py | Yes |
| `pathlib` | multiple | Yes |
| `datetime` | multiple | Yes |
| `collections` | pattern_analysis.py | Yes |
| `argparse` | pattern_analysis.py | Yes |
| `copy` | sanitize.py | Yes |
| `atexit` | log_event.py | Yes |

**Critical missing dependency:** PyYAML is required by nearly every Python script but is never declared anywhere. There is no `requirements.txt`, no `pyproject.toml` for Forge itself, and no installation instructions.

### 9.3 System Tool Dependencies

| Tool | Used By | Availability |
|------|---------|-------------|
| `git` | block-main-branch.sh, pre-commit.sh, pre-push.sh | Standard |
| `eslint` | pre-commit.sh | Optional (checked with `command -v`) |
| `ruff` | pre-commit.sh | Optional |
| `black` | pre-commit.sh (fallback) | Optional |
| `tsc` | pre-commit.sh | Optional |
| `mypy` | pre-commit.sh | Optional |
| `pytest` | pre-commit.sh, pre-push.sh | Optional |
| `bandit` | pre-push.sh | Optional |
| `git-secrets` | pre-push.sh | Optional |
| `grep -P` (PCRE) | forge-statusline.sh, validate-story-alignment.sh | **Not available on macOS** |
| `python3` | ci-server.py, all Python scripts | Standard |
| `node` | github-server.js | Standard (for JS projects) |

### 9.4 Dependency Assessment

- **PyYAML** is the sole non-stdlib Python dependency and is used pervasively. It should be declared.
- The framework has no installation mechanism for its own dependencies.
- System tool checks use `command -v` gracefully, falling back or skipping when tools are missing.
- The `grep -P` dependency is a real problem on macOS and would silently fail.

---

## 10. Security Considerations

### 10.1 Positive Security Measures

1. **Deny rules in permissions:** Blocks reading `.env*`, `credentials*`, `*secret*` files and blocks `rm -rf`
2. **Sanitize script:** Proactively strips secrets from learning logs
3. **Branch protection:** Prevents modifications on main/master
4. **Security scanning:** Pre-push hook runs `bandit`, `npm audit`, `git-secrets`
5. **Env var bypass requires explicit opt-in:** All bypass mechanisms require setting specific env vars

### 10.2 Security Concerns

1. **`settings.local.json` grants `Bash(python:*)`:** This is unrestricted Python execution, bypassing the careful allow-listing in `settings.json`. Any Claude-generated Python script can run.

2. **No hook integrity verification:** Hooks are shell scripts that run with the user's full permissions. If an attacker modifies a hook script, it executes without validation.

3. **YAML parsing (safe_load):** All Python scripts correctly use `yaml.safe_load()` rather than `yaml.load()`, which is good -- avoids arbitrary code execution via YAML deserialization.

4. **Tool input JSON parsing via grep:** `validate-story-alignment.sh` extracts JSON fields using grep patterns rather than proper JSON parsing (e.g., `jq`). This is fragile and potentially exploitable if tool input contains crafted JSON.

```bash
FILE_PATH=$(echo "$TOOL_INPUT" | grep -oP '"file_path"\s*:\s*"\K[^"]+' 2>/dev/null || echo "")
```

5. **No checksum on events.jsonl:** The learning log is append-only but not integrity-protected. A compromised script could inject false events to manipulate pattern detection.

6. **Sanitize regex false positives:** The aggressive base64 pattern could redact legitimate data, potentially hiding important debugging information in learning logs.

7. **Environment variable injection:** All hooks read environment variables for bypass. If an attacker can set `FORGE_ALLOW_MAIN_BRANCH=1` or `FORGE_SKIP_P0_CHECK=1`, protections are disabled.

8. **Pre-commit hook auto-stages modified files:** The `eslint --fix` and `ruff format` results are auto-staged via `git add`. If a linter has a bug or is compromised, it could silently modify and commit arbitrary code.

---

## 11. Status Line (`forge-statusline.sh`)

### 11.1 How It Works

The status line script reads from two YAML file sources:
- `forge/.tmp/{story_id}/handoff.yml` -- for phase, coverage, and findings
- `forge/stories/{story_id}.yml` -- for scope information

It discovers the active story by finding the most recent `handoff.yml` in `forge/.tmp/`.

### 11.2 Information Displayed

Format: `{story_id} [{phase}] {coverage}% | scope:{scope} | P0:{count} P1:{count}`

Example: `ST-001 [GREEN] 87% | scope:validation | P0:0 P1:2`

**Phase mapping reflects TDD cycle:**
- `PLAN` = planning phase
- `RED` = writing tests (tests phase)
- `GREEN` = writing implementation (code phase)
- `REVIEW` = quality review phase

### 11.3 Limitations

1. **macOS incompatibility:** Uses `grep -oP` (Perl regex) which requires GNU grep, not available on macOS by default
2. **Single story only:** Shows only the most recently modified handoff, no multi-story support
3. **Not wired up:** No hook event or configuration connects this to Claude Code's status bar
4. **File-based state:** Relies on filesystem state that may be stale or inconsistent
5. **No error handling for malformed YAML:** Uses grep rather than proper YAML parsing; silently returns empty/default values on parse failure

---

## 12. Branch Protection (`block-main-branch.sh`)

### 12.1 How It Works

Simple branch-name matching against a hardcoded list:

```bash
PROTECTED_BRANCHES=("main" "master" "production" "prod")
```

Runs on every `PreToolUse: Bash` event, checking the current git branch before allowing any bash command.

### 12.2 Effectiveness Assessment

**Effective against:**
- Accidental code modifications on protected branches
- Claude Code writing/running commands while on wrong branch

**NOT effective against:**
- Branch name variants (`develop` used as production, `release/*` branches)
- Git operations that change branches (a `git checkout main` followed by edits would not be caught until the next Bash invocation)
- Non-bash file operations (Write/Edit tool calls are NOT checked by this hook -- it only matches `Bash`)
- Detached HEAD states (explicitly allowed)
- Env var bypass is trivially accessible

**Design gap:** The hook only checks `Bash` operations. Claude Code's `Write` and `Edit` tools bypass this hook entirely since they match a different event. A developer could be on `main` and Claude Code could write files directly without triggering the branch check.

### 12.3 Minor Bugs

Lines 37, 39, 51 have a string concatenation issue:
```bash
echo "=" *60       # This does NOT print 60 '=' characters
echo "="*60        # This does NOT print 60 '=' characters
```

In bash, `*60` is a glob pattern, not a repetition operator. On most systems this would print `= *60` literally (or expand to filenames matching `*60`).

---

## 13. Pain Points

### 13.1 Over-Engineered

1. **Self-learning system (5 Python scripts, ~1400 lines):** The pattern analysis pipeline (log_event, sanitize, pattern_analysis, pattern_matcher, apply_pattern, learning_state) is a sophisticated machine learning-lite system that requires hundreds of workflow events to produce actionable patterns. For most projects, this will never reach the threshold for useful pattern detection. The 15-event auto-approve threshold and 20-event analysis trigger assume sustained, high-volume usage.

2. **Story schema validation tiers:** The three-tier validation system (SIMPLE/STANDARD/COMPLEX) with 21 required fields at the COMPLEX tier, 10 edge case categories, and auto-tier-detection heuristics is extremely prescriptive. The validation logic alone is 372 lines of Python.

3. **MCP server stubs:** Two non-functional MCP servers exist as documentation-only files. They add confusion about what's actually operational.

4. **Feature flag requirement enforcement:** The validate-story.py script mandates feature flags for any story touching auth/payment/billing/security paths, even if the project has no feature flag infrastructure.

### 13.2 Fragile Components

1. **`grep -oP` dependency:** Multiple scripts rely on Perl-compatible regex in grep, which breaks on macOS. This is the #1 portability issue.

2. **Relative path assumptions:** All scripts use relative paths (`forge/.tmp/`, `forge/stories/`, `forge/memory/learning/`). They will break if invoked from a different working directory.

3. **YAML parsing via grep:** Several bash scripts parse YAML using grep patterns instead of a proper parser. This breaks on multi-line values, quoted strings, or non-standard formatting:
   ```bash
   grep -oP 'story_id:\s*\K\S+' "$handoff" 2>/dev/null
   ```

4. **JSON parsing via grep:** `validate-story-alignment.sh` extracts JSON fields via regex, which is fragile for edge cases (escaped quotes, multiline JSON, etc.):
   ```bash
   FILE_PATH=$(echo "$TOOL_INPUT" | grep -oP '"file_path"\s*:\s*"\K[^"]+' 2>/dev/null || echo "")
   ```

5. **log_event.py relative imports:** Uses `from .sanitize import sanitize_context` which requires package-style invocation. Cannot be run standalone.

6. **learning_state.py import in pattern_analysis.py:** Uses a try/except import with fallback:
   ```python
   try:
       from learning_state import update_last_analysis
   except ImportError:
       # Fallback: manually update state file
   ```
   This suggests the import path is not reliable.

7. **Undeclared PyYAML dependency:** Every Python script that does YAML parsing will fail with `ModuleNotFoundError: No module named 'yaml'` on a fresh system.

### 13.3 Missing Components

1. **Hook installation mechanism:** Git hooks (`pre-commit.sh`, `pre-push.sh`) require manual copying. There is no `forge init` or setup script.

2. **Stop hook is empty:** `check-p0-findings.py` exists but is not wired to the Stop event.

3. **validate-story.py not configured:** The story schema validator is documented as a PreToolUse hook but not added to settings.json.

4. **No health check or diagnostic tool:** There is no way to verify that all hooks are correctly installed, that dependencies are available, or that the learning system is functioning.

5. **No log rotation for events.jsonl:** The learning event log is append-only with no rotation, truncation, or size limit. Over time it will grow unbounded.

6. **No dependency declaration:** Missing `requirements.txt` or `pyproject.toml` for Forge itself.

7. **No tests for hooks or scripts:** None of the hook scripts or Python utilities have test coverage. The `if __name__ == "__main__"` blocks provide basic smoke tests but nothing automated.

---

## 14. Technology Choices

### 14.1 Language Assessment

| Component | Language | Assessment |
|-----------|----------|-----------|
| Branch protection | Bash | **Appropriate** -- simple, fast, no dependencies |
| Story alignment | Bash | **Questionable** -- parsing JSON/YAML with grep is fragile. Python with `jq` or native JSON would be better |
| Status line | Bash | **Questionable** -- YAML parsing via grep is fragile |
| CI hooks | Bash | **Appropriate** -- standard for git hooks |
| P0 check | Python | **Appropriate** -- needs YAML parsing |
| Story validation | Python | **Appropriate** -- complex validation logic |
| Learning system | Python | **Appropriate** -- data analysis and pattern matching |
| CI MCP server | Python (planned) | **Appropriate** -- async MCP server |
| GitHub MCP server | JavaScript (planned) | **Questionable** -- mixing languages unnecessarily. Python would be consistent |
| Sanitize | Python | **Appropriate** -- regex processing |

### 14.2 Architecture Decisions

**Good choices:**
- JSONL for event logging (append-friendly, streamable, simple)
- YAML for story/pattern files (human-readable, good for configuration)
- Exit-code based hook communication (standard, simple)
- Environment variable bypasses (explicit, auditable)
- `yaml.safe_load()` everywhere (prevents deserialization attacks)
- Deep copy before sanitization (prevents mutation bugs)
- Atexit handler for event flushing (prevents data loss)

**Questionable choices:**
- Two languages for MCP servers (Python + JavaScript) when one would suffice
- Bash for YAML/JSON parsing when Python is already a dependency
- In-memory event queue in a short-lived script process (events may be lost if the process is killed)
- Relative imports in log_event.py making it non-standalone
- File-based state for the learning system rather than SQLite or similar
- No use of `jq` for JSON parsing in bash scripts despite it being widely available

### 14.3 What Should Change for a Rebuild

1. **Use Python for all hooks that parse structured data.** Bash is appropriate only for simple checks (branch protection, binary availability checks).

2. **Declare dependencies.** Create a `pyproject.toml` or `requirements.txt` for Forge itself with PyYAML as a dependency.

3. **Use `jq` for JSON parsing in bash** or move to Python entirely.

4. **Consolidate MCP servers to one language** (Python, since the learning system is already Python).

5. **Wire up all hooks.** The Stop hook and validate-story.py should be in settings.json or removed.

6. **Add log rotation** for events.jsonl (e.g., rotate at 10MB or 10000 events).

7. **Replace `grep -oP`** with `grep -E` (POSIX) or use Python for portability.

8. **Add a setup/init script** that installs git hooks, checks dependencies, and validates the environment.

9. **Simplify the learning system.** The five-script pipeline could be a single module with clear entry points, reducing the import path fragility.

10. **Implement or remove MCP stubs.** The disabled stubs add confusion. Either implement them or remove them and document the planned architecture separately.

### 14.4 Lock Utility (`lock.py`)

**Location:** `.claude/skills/forge-check/lock.py`

A minimal no-op lock implementation:

```python
from contextlib import contextmanager

@contextmanager
def acquire_lock(name: str = "", timeout: int = 30):
    """No-op lock for single-process execution."""
    yield
```

This is a stub that does nothing -- it exists so that code importing `lock.acquire_lock` does not fail, but provides no actual locking. It is used by the forge-check validation script to allow for future multi-process safety without currently implementing it. The interface (context manager with name and timeout parameters) is designed to be replaced with a real file-lock implementation if needed.

---

## Summary Assessment

The hooks and tooling infrastructure shows a thoughtful design with significant ambition but incomplete execution. The branch protection and story alignment hooks work (with caveats). The CI hooks are standard. The self-learning system is the most ambitious component -- a five-script pipeline for event collection, sanitization, pattern detection, matching, and application -- but it operates in isolation from the actual hook system and requires sustained usage volume to produce value.

**What works today:**
- Branch protection (PreToolUse: Bash)
- Story alignment warnings (PreToolUse: Write|Edit)
- Permission deny/allow rules
- Environment variable configuration

**What exists but is not connected:**
- P0 finding check (not wired to Stop event)
- Story schema validation (not in settings.json hooks)
- Status line display (no hook event)
- Git CI hooks (require manual installation)
- Learning system scripts (library code, no hook integration)

**What does not exist:**
- MCP servers (stubs only)
- Dependency management
- Setup/installation mechanism
- Tests for the tooling itself
- Log rotation
