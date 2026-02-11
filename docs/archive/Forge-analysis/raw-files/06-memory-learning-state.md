# Forge Analysis: Memory, Learning & State Management

## Executive Summary

Forge maintains a multi-layered state management system split across two locations: `forge/` (user-facing project state) and `.claude/` (framework machinery). The state system has three distinct concerns: (1) project memory for tracking stories, sprints, and decisions; (2) a self-learning pipeline for workflow pattern discovery; and (3) settings/configuration. The learning system is the most ambitious and elaborate component -- approximately 1,500 lines of Python across 6 scripts, plus a dedicated agent and 400-line README -- but as of this analysis, **every data file is empty**. No events have been logged, no patterns discovered, no decisions recorded. The entire learning system is speculative infrastructure that has never been exercised.

---

## 1. State Architecture

### Storage Locations

State is spread across two directory trees:

```
forge/                              # Project-level state (committed to git)
  settings.yml                      # Project configuration
  memory/
    project.yml                     # Sprint/story tracking
    important_decisions.yml         # Architectural decisions log
    learning/
      README.md                     # Learning system documentation
      patterns.yml                  # Discovered patterns library
      pattern_performance.yml       # Pattern accuracy tracking
      events.jsonl                  # Raw event log (does NOT exist yet)
      last_analysis.yml             # Analysis trigger state (does NOT exist yet)
      archive/                      # Compressed old events (does NOT exist yet)

.claude/                            # Framework machinery
  scripts/
    log_event.py                    # Event logging with sanitization
    pattern_analysis.py             # Pattern discovery from events
    pattern_matcher.py              # Query patterns by attributes
    apply_pattern.py                # Apply patterns and track effectiveness
    learning_state.py               # Auto-trigger state management
    sanitize.py                     # Privacy sanitization for events
  agents/
    forge-learning-analyzer.md      # Dedicated sub-agent for pattern discovery
  templates/forge/
    settings.yml.template           # Template for settings (identical to forge/settings.yml)
```

### Format Summary

| File | Format | Purpose |
|------|--------|---------|
| `project.yml` | YAML | Sprint tracking, story registry |
| `important_decisions.yml` | YAML | Architectural decisions |
| `settings.yml` | YAML | Configuration (thresholds, toggles) |
| `patterns.yml` | YAML | Discovered patterns |
| `pattern_performance.yml` | YAML | Pattern accuracy metrics |
| `events.jsonl` | JSON Lines (append-only) | Raw event stream |
| `last_analysis.yml` | YAML | Analysis trigger state |

### Current State: Everything Is Empty

As of this analysis, all data files contain only their schema scaffolding with zero actual data:

- `project.yml`: `stories: {}`, `sprints: {}`, `history: []`, `sprint_count: 0`
- `important_decisions.yml`: `total_decisions: 0`, `decisions: []`
- `patterns.yml`: `patterns: []`
- `pattern_performance.yml`: `total_patterns: 0`, `total_applications: 0`, `patterns: {}`
- `events.jsonl`: **Does not exist** (would be created on first event)
- `last_analysis.yml`: **Does not exist** (would be created on first analysis run)

---

## 2. Project Memory (`forge/memory/project.yml`)

### Structure

```yaml
template_version: "1.2.0"
stories: {}               # ST-### -> {status, points, ...}
velocity_target: 15
current_sprint: null
sprints: {}               # sprint_number -> {stories: {...}, total_points: N}
history: []               # Append-only event log for dashboard
sprint_count: 0
```

### What It Tracks

- **Stories**: A flat map of `ST-###` story IDs to their status, story points, and metadata
- **Sprints**: Grouped sets of stories with point totals
- **Velocity**: Target points per sprint
- **History**: An append-only log of events (story completions, sprint starts) used by the dashboard skill

### How It's Used

The dashboard skill (`/Users/shashank/workspace/applications/forge-claudify/.claude/skills/forge-workflow/dashboard.md`) reads this file to render:
- Sprint progress bars (visual `...` representation)
- Story status tables (Done/In Progress/Planned/Blocked)
- Velocity metrics (capacity vs. completed vs. remaining)
- Recent activity timeline

The dashboard template shows exactly how `project.yml` fields map to UI:

```python
# From dashboard.md Step 4
completed_points = sum(s.story_points for s in sprint.stories if s.status == 'done')
in_progress_points = sum(s.story_points for s in sprint.stories if s.status == 'in_progress')
remaining_points = sprint.total_points - completed_points
```

### Initialization

The deprecated `init_project_memory.py` (`/Users/shashank/workspace/applications/forge-claudify/.claude/_to_be_deleted/forge/scripts/init_project_memory.py`) shows the original initialization logic:

```python
PROJECT_DEFAULT = {
    "template_version": get_template_version(),
    "stories": {},
    "velocity_target": 10,     # Note: default was 10, current file has 15
    "current_sprint": 1,       # Note: default was 1, current file has null
    "sprint_start": str(date.today()),
    "history": [],
}
```

The fact that the current `project.yml` has `current_sprint: null` and `sprint_count: 0` suggests it was manually edited or generated by a different initialization path than the old script.

---

## 3. Decision Tracking

### Schema (from `decisions-schema.md`)

Full path: `/Users/shashank/workspace/applications/forge-claudify/.claude/skills/forge-reference/decisions-schema.md`

Decisions use this schema:

```yaml
decisions:
  - id: ID-001                        # Unique decision ID
    story_id: ST-001                   # Story where decision was made
    title: "Email validation timeout"  # 10-100 chars
    summary: |                         # 20-500 chars
      DNS lookups for MX verification must timeout after 5 seconds...
    categories:                        # 1-3 from allowed list
      - reliability
      - performance
    guidance:                          # 1-5 actionable rules
      - "DNS lookups MUST have 5s timeout"
      - "On timeout, accept email but flag"
    impact_scope:                      # Optional: affected scopes
      - validation
      - integration
    links: [ADR-001]                   # Optional: related docs
    created: "2025-01-15T10:00:00Z"
    supersedes: null                   # Optional: replaces old decision
    status: active                     # active | superseded
```

### Allowed Categories (14 total)

`security`, `compliance`, `data_governance`, `observability`, `performance`, `reliability`, `operations`, `feature_flags`, `migration`, `architecture`, `testing`, `user_experience`, `integration`, `incident_response`

### Lifecycle

```
1. CAPTURE:      Developer adds to handoff.yml during TDD
2. CONSOLIDATE:  Quality gate promotes to important_decisions.yml
3. APPLY:        Planner/Developer reference in future stories
4. SUPERSEDE:    New decision replaces old (append-only, never delete)
```

Decisions flow from per-story temp files (`forge/.tmp/{{story_id}}/handoff.yml`) to the consolidated project-wide log (`forge/memory/important_decisions.yml`). The quality gate agent is responsible for the promotion step.

### Current State

```yaml
version: "1.1.1"
last_updated: null
total_decisions: 0
decisions: []
```

Empty. No decisions have ever been recorded.

---

## 4. Learning System

### Architecture Overview

The learning system is described in a 400-line README at `/Users/shashank/workspace/applications/forge-claudify/forge/memory/learning/README.md`. It has three conceptual layers:

```
Layer 1: EVENT CAPTURE
  Raw observation of every workflow event (append-only JSONL log)

Layer 2: PATTERN EXTRACTION
  Aggregate raw events into statistical patterns (async analysis)

Layer 3: PROACTIVE APPLICATION
  Use patterns to improve future workflows (inject guidance)
```

### Pipeline Flow

```
Orchestrator workflows
    |
    v
log_event.py (queue -> flush to events.jsonl)
    |
    v  (triggered after 20+ events or 24+ hours)
pattern_analysis.py (reads events.jsonl -> detects patterns)
    |
    v
pattern_proposals.yml (temporary proposals)
    |  (auto-merge if high-confidence)
    v
patterns.yml (active pattern library)
    |
    v  (during next workflow)
pattern_matcher.py (queries matching patterns by attributes)
    |
    v
apply_pattern.py (injects guidance, tracks effectiveness)
    |
    v
pattern_performance.yml (accuracy tracking, trend detection)
```

### Event Types (20+ defined in README)

Workflow events: `workflow_started`, `workflow_completed`, `workflow_failed`
Sub-agent events: `sub_agent_spawned`, `sub_agent_retry_needed/succeeded/failed`
Clarification events: `clarification_requested`, `clarification_answered`
Validation events: `validation_failed`, `validation_auto_fixed`
Guard events: `guard_token_triggered`
Quality events: `quality_finding`
Deviation events: `deviation_detected`
Design events: `design_gaps_found`
Planning events: `story_count_mismatch`
Analysis events: `analysis_complete`
Parallel events: `parallel_workflow_conflict`
Development events: `scope_violation`

### Pattern Categories (5 types)

1. **Clarification Predictors**: Predict when sub-agents will need clarification
2. **Workflow Outcome Predictors**: Predict likely outcomes by attributes
3. **Deviation Detectors**: Detect when expectations diverge from reality
4. **Success Indicators**: Identify what makes workflows succeed first-try
5. **Efficiency Patterns**: Optimize execution (e.g., parallelization opportunities)

### Auto-Approval Thresholds

| Level | Criteria | Action |
|-------|----------|--------|
| High Confidence | sample_size >= 15 AND occurrence_rate >= 80% | Auto-approve and auto-merge |
| Medium Confidence | sample_size >= 10 AND occurrence_rate >= 60% | Manual review |
| Low Confidence | Below thresholds | Ignore |

These thresholds are configurable in `forge/settings.yml` under `learning.confidence_levels`.

### Pattern Lifecycle

1. Detection -> 2. Proposal -> 3. Approval (auto or manual) -> 4. Merge into patterns.yml -> 5. Application during workflows -> 6. Tracking (accuracy) -> 7. Refresh on use -> 8. Expiration (90 days unused) -> 9. Deprecation (< 50% accuracy)

---

## 5. Pattern Matching (`pattern_matcher.py`)

Full path: `/Users/shashank/workspace/applications/forge-claudify/.claude/scripts/pattern_matcher.py`

### How It Works

The matcher loads `patterns.yml` and filters patterns through a multi-criteria matching system:

**Step 1: Active Check** (`is_pattern_active`)
- Status must be `active` (not `under_review` or `deprecated`)
- Pattern must not be expired (checks `last_refreshed` + `max_age_days` = 90 days)

**Step 2: Condition Matching** (`pattern_matches_conditions`)
Patterns have trigger conditions that are ANDed together:
- `workflow`: Must match exactly (e.g., `develop`)
- `story_scope`: At least one scope must overlap (OR within the list)
- `story_complexity`: Must be one of the listed tiers (`SIMPLE`, `STANDARD`, `COMPLEX`)
- `feature_category`: Must match exactly

**Step 3: Confidence Filter**
- Patterns below minimum requested confidence are excluded

**Step 4: Sorting**
- Results sorted by accuracy (highest first), then by confidence level

### Key Functions

```python
query_patterns(workflow, story_scope, story_complexity, feature_category, pattern_type, min_confidence)
  -> List[Dict]  # Matching patterns sorted by accuracy

get_pattern_by_id(pattern_id) -> Optional[Dict]

disable_pattern(pattern_id, reason) -> bool   # Sets status to "deprecated"
enable_pattern(pattern_id) -> bool             # Re-enables deprecated pattern
get_pattern_summary() -> Dict                  # Statistics for status display
```

### Usage in Practice

The orchestrator would call `query_patterns()` before spawning sub-agents, passing the current story's attributes. Any matching patterns would have their guidance injected into the sub-agent's context via `apply_pattern.py`.

---

## 6. Event Logging (`log_event.py`)

Full path: `/Users/shashank/workspace/applications/forge-claudify/.claude/scripts/log_event.py`

### Architecture

Events use an in-memory queue with periodic flush to disk:

```python
EVENT_QUEUE: List[Dict] = []           # In-memory buffer
FLUSH_THRESHOLD = 10                    # Flush after 10 events
FLUSH_INTERVAL = 60                     # Flush after 60 seconds
EVENTS_FILE = "forge/memory/learning/events.jsonl"
```

### Event Structure

```json
{
    "event_id": "evt_20260130_143000_123456",
    "timestamp": "2026-01-30T14:30:00.123456Z",
    "event_type": "workflow_started",
    "story_id": "ST-001",
    "workflow": "develop",
    "phase": "tests",
    "context": { ... }  // Sanitized via sanitize.py
}
```

### Helper Functions (18 specific helpers)

The script provides typed helper functions for common events:

```python
log_workflow_started(workflow, context, story_id)
log_workflow_completed(workflow, context, story_id)
log_workflow_failed(workflow, context, story_id)
log_phase_started(phase, context, story_id)
log_phase_completed(phase, context, story_id)
log_phase_failed(phase, context, story_id)
log_guard_token(guard_token, context, story_id, phase)
log_clarification_requested(question, context, story_id, workflow)
log_clarification_answered(question, answer, context, story_id)
log_sub_agent_spawned(agent_type, context, story_id, workflow)
log_retry(retry_type, context, story_id, phase)
log_quality_finding(severity, dimension, finding, context, story_id)
log_deviation(expected, actual, context, story_id, workflow)
log_pattern_applied(pattern_id, context, story_id, workflow)
log_pattern_skipped(pattern_id, reason, context, story_id)
log_user_override(override_type, context, story_id)
```

### Sanitization

All contexts are sanitized before logging via `sanitize.py`:

**Sensitive patterns detected and redacted:**
- API keys (OpenAI `sk-...`, Anthropic `sk-ant-...`, GitHub `ghp_/gho_/ghs_...`, AWS `AKIA...`)
- Password/secret/token fields (by name or by value pattern)
- Email addresses
- Credit card numbers
- Social Security Numbers
- Private keys (PEM format)
- JWTs

**Sensitive field names auto-redacted:**
`password`, `passwd`, `pwd`, `secret`, `api_key`, `token`, `credential`, `authorization`, `cookie`, `session` (and variants)

### Flush Guarantees

- Automatic flush when queue reaches 10 events
- Automatic flush every 60 seconds
- Guaranteed flush at process exit via `atexit.register(ensure_flush_on_exit)`

### Important Design Note

The `log_event()` function imports from `.sanitize` using relative import syntax (`from .sanitize import sanitize_context`), meaning it expects to be imported as part of a package (`.claude.scripts`), not run standalone. The `__main__` test block at the bottom of the file would fail because of this import. This is a latent bug that would manifest if someone tried to run the test directly.

---

## 7. Settings vs Memory

### `forge/settings.yml` - Configuration

```yaml
project:
  name: "Forge Framework"
  architecture: "auto"

tdd:
  coverage_threshold: 90
  hotfix_coverage_threshold: 70

quality:
  p0_blocking: true
  p1_threshold: 2
  persist_verification_tests: auto

learning:
  enabled: true
  auto_trigger:
    enabled: true
    event_threshold: 20
    time_threshold_hours: 24
  confidence_levels:
    high: 0.80
    medium: 0.60
    low: 0.40
```

### Template vs Instance

The template at `/Users/shashank/workspace/applications/forge-claudify/.claude/templates/forge/settings.yml.template` is **identical** to the current `forge/settings.yml` except `project.name` is empty and `project.architecture` is empty in the template. During init, the name and architecture are filled in.

### Relationship Between Settings and Memory

| Aspect | Settings | Memory |
|--------|----------|--------|
| **Nature** | Configuration (what should happen) | Data (what has happened) |
| **Mutability** | Rarely changed | Updated every workflow |
| **Who reads** | All agents, scripts | Dashboard, learning system, orchestrator |
| **Who writes** | User, init process | Agents, learning scripts |
| **Persistence** | Project lifetime | Grows over time |

Settings configures how the learning system behaves (thresholds, enable/disable). Memory stores what the learning system has observed and learned. Settings drives the learning system; memory is the output.

---

## 8. Cross-Session Persistence

### What Persists (committed to git)

| File | Survives Sessions | Survives Git Clone |
|------|-------------------|-------------------|
| `forge/settings.yml` | Yes | Yes |
| `forge/memory/project.yml` | Yes | Yes |
| `forge/memory/important_decisions.yml` | Yes | Yes |
| `forge/memory/learning/patterns.yml` | Yes | Yes |
| `forge/memory/learning/pattern_performance.yml` | Yes | Yes |
| `forge/memory/learning/events.jsonl` | Yes | Depends on .gitignore |
| `forge/memory/learning/last_analysis.yml` | Yes | Depends on .gitignore |

### What's Ephemeral

| File | Nature | Recreated When |
|------|--------|----------------|
| `forge/.tmp/*/handoff.yml` | Per-story working state | Each story development |
| In-memory event queue | Buffered events | Lost on process exit (flushed via atexit) |
| `pattern_proposals.yml` | Temporary analysis output | Each analysis run |

### The `forge/.tmp/` Convention

Per-story working state lives in `forge/.tmp/{story_id}/handoff.yml`. This is where:
- Phase progress is tracked (plan/tests/code/complete)
- Important decisions are captured during development
- Test plans and implementation details are stored

This data is ephemeral in that it's specific to a story in progress, but it feeds into the persistent memory files (e.g., decisions promoted to `important_decisions.yml`).

---

## 9. Legacy/Dead State (`_to_be_deleted/`)

Full path: `/Users/shashank/workspace/applications/forge-claudify/.claude/_to_be_deleted/`

### What Was Deprecated

The `_to_be_deleted` directory contains **the entire previous generation** of the Forge framework. The migration went from a `forge/`-rooted structure to a `.claude/`-rooted structure using Claude Code's native skills/agents system. Here is what was deprecated:

**Scripts (10 files)**:
- `init_project_memory.py` -- Replaced by template-based initialization
- `forge_dispatch.py` -- A massive 746-line command dispatcher with intent matching, slot extraction, prerequisite checking, environment variable generation, and load manifest creation. This was the **central routing mechanism** of the old framework. It matched natural language to intents, extracted story IDs and feature slugs, verified workflow prerequisites (design before plan, plan before develop, etc.), and generated environment files for sub-agents. **This single file reveals the old architecture was fundamentally different: it used a manifest.yml-driven dispatch system with environment variable passing, not Claude Code's native skills/commands.**
- `validate.py` -- Unified validation runner (stories, memory, capsules)
- `validate_stories.py` -- Story YAML schema validation
- `check_tools.py` -- Tool availability checker
- `doctor.py` -- 770-line diagnostic tool with 15 health checks (Python version, dependencies, directory structure, manifest, profiles, templates, context, git, permissions, profile versions, story schemas, scripts, environment, storage, best practices)
- `bootstrap.sh` -- Shell bootstrap script
- `verify_enforced_tests.py` -- Test enforcement verification
- `migrate_stories.py` -- Story migration between versions
- `static_analysis.py` -- Static code analysis

**Templates (18 files)**: The entire `forge/templates/` directory was deprecated. Templates for every workflow (design, plan, develop, quality, hotfix, orchestrate, etc.) plus snippet templates (guard tokens, schemas, etc.) were replaced by skills and agents.

**Profiles (2 files)**:
- `universal.yml` -- 698 lines defining all 10 scopes with exhaustive metadata (artifacts, patterns, observability, best practices, story point ranges, dependencies) plus archetype overrides for 20+ project types. This was a **massively detailed** scope/archetype definition system.
- `active.yml` -- Archetype selector with performance targets

**Practices (20+ files)**: The entire practices library (coding, testing, security, observability, API, patterns, data, resilience, plus 6 architecture styles and specialized practices like concurrency, determinism, accessibility, internationalization) was moved to the skills reference system.

**Commands (20+ files)**: All deprecated command definitions under `commands/forge/_deprecated/` (scaffold, design, develop, plan, quality, hotfix, orchestrate, etc.)

### Why It Was Deprecated

The old system was a custom framework built on:
1. `manifest.yml` -- Intent definitions with synonyms, required inputs, and load specifications
2. `forge_dispatch.py` -- NLP-style intent matching and slot extraction
3. Environment variable passing -- State communicated via `forge/.tmp/forge-env`
4. Template-based agent instructions -- Loaded markdown templates as agent prompts

This was replaced by Claude Code's native primitives:
1. **Skills** replaced templates and commands
2. **Agents** replaced spawned sub-processes
3. **Rules** replaced inline instructions
4. **Hooks** replaced pre/post steps

The migration preserved the concept (memory, decisions, learning) but changed the execution mechanism entirely.

### Key Insight from Legacy: `forge_dispatch.py`

The dispatch script reveals critical architectural decisions:

```python
def check_prerequisites(intent: str, slots: dict) -> tuple[bool, str]:
    """Workflow order:
    1. design -> creates forge/docs/designs/{feature}.md
    2. plan -> requires design doc, creates forge/stories/ST-###.yml
    2.5. scaffold -> requires story file (optional), creates file stubs
    3. develop_plan -> requires story file, creates handoff.yml with plan
    4. develop_tests -> requires handoff with plan phase, writes tests
    5. develop_code -> requires handoff with tests phase, implements code
    6. quality -> requires handoff with code phase
    """
```

This shows the old system had **enforced workflow ordering** via file-existence checks. The new skills-based system relies on agent instructions (guard tokens) rather than programmatic gatekeeping.

---

## 10. Complexity Assessment

### Is the Learning System Over-Built?

**Definitively yes.** Here is the evidence:

1. **Zero usage**: Every data file is empty. No events have been logged. No patterns discovered. No decisions recorded. The system has never been exercised.

2. **Speculative infrastructure**: The learning system has 6 Python scripts (~1,500 lines), a dedicated agent definition, a 400-line README with elaborate architecture diagrams, 20+ event types, 5 pattern categories, 3-tier confidence thresholds, auto-approval logic, auto-merge logic, auto-deprecation logic, auto-trigger logic with time-based and count-based thresholds, trend detection, user feedback tracking, privacy sanitization with 15+ regex patterns... all for a system that has processed exactly zero events.

3. **Premature optimization**: The system includes:
   - Event queuing with configurable flush thresholds (for performance -- but there are no events)
   - Archive management with gzip compression (for storage -- but there's nothing to archive)
   - Cross-workflow correlation patterns (for learning -- but there's no data)
   - A "Phase 6 Enhancement" with auto-trigger that "runs automatically" (but nothing triggers it because no workflows have ever completed)

4. **Self-referential documentation**: The README includes "Success Metrics" for after 20, 50, and 100 stories, and a "Philosophy" section about becoming "the first AI orchestrator with continuous learning." This is marketing copy inside a technical system that has never been used.

5. **The pattern analysis only detects 3 of 5 categories**: Despite documenting 5 pattern types, `pattern_analysis.py` only implements detectors for clarification patterns, deviation patterns, and quality patterns. Success indicators and efficiency patterns are not implemented.

### What's Actually Useful?

The core **concept** is sound and could be implemented much more simply:

1. **Decision tracking** (10 lines of YAML schema) -- Genuinely useful for cross-story consistency
2. **Project memory** (sprint/story tracking) -- Useful for progress visibility
3. **Settings** (configuration) -- Necessary

The learning system could be replaced with a simple "lessons learned" YAML file that agents append to manually, rather than an automated ML-style pipeline.

### Ceremonial vs Functional Assessment

| Component | Assessment |
|-----------|------------|
| `project.yml` | **Functional** -- Provides real value for tracking |
| `important_decisions.yml` | **Functional** -- Good concept, good schema |
| `settings.yml` | **Functional** -- Necessary configuration |
| `events.jsonl` pipeline | **Ceremonial** -- Elaborate infrastructure, zero usage |
| `patterns.yml` system | **Ceremonial** -- 5 scripts for unused pattern management |
| `pattern_performance.yml` | **Ceremonial** -- Tracks accuracy of non-existent patterns |
| `sanitize.py` | **Premature** -- Sanitizes data that doesn't exist yet |
| `learning_state.py` | **Premature** -- Throttles analysis that never runs |
| `forge-learning-analyzer` agent | **Ceremonial** -- An entire agent for a system with no data |

---

## 11. Data Flow

### Who Reads What

```
Dashboard Skill ----reads----> project.yml, important_decisions.yml, handoff.yml
Orchestrator   ----reads----> settings.yml, patterns.yml (via pattern_matcher.py)
Developer Agent ----reads----> settings.yml, important_decisions.yml
Quality Agent  ----reads----> settings.yml, important_decisions.yml
Planner Agent  ----reads----> important_decisions.yml, project.yml
Learning Agent ----reads----> events.jsonl, patterns.yml, pattern_performance.yml
```

### Who Writes What

```
Orchestrator   ----writes---> project.yml (story status, sprint progress)
                              events.jsonl (via log_event.py)
Quality Agent  ----writes---> important_decisions.yml (promotes from handoff.yml)
Developer Agent ----writes---> handoff.yml (per-story temp state)
pattern_analysis.py --writes-> pattern_proposals.yml, patterns.yml, last_analysis.yml
apply_pattern.py ----writes-> patterns.yml (performance metrics), pattern_performance.yml
Init Process   ----writes---> settings.yml (from template)
                              project.yml (empty skeleton)
                              important_decisions.yml (empty skeleton)
```

### Flow Diagram

```
User Request
    |
    v
Orchestrator
    |-- reads settings.yml for thresholds
    |-- reads patterns.yml via pattern_matcher.py for relevant patterns
    |-- logs events via log_event.py -> events.jsonl
    |-- reads/writes project.yml for story tracking
    |
    v
Sub-Agent (develop/design/plan/quality)
    |-- reads settings.yml for coverage thresholds
    |-- reads important_decisions.yml for prior guidance
    |-- writes handoff.yml (per-story temp state)
    |-- (quality agent) promotes decisions to important_decisions.yml
    |
    v
Post-Workflow
    |-- learning_state.py checks if analysis should trigger
    |-- if yes: pattern_analysis.py runs
    |       reads events.jsonl
    |       writes pattern_proposals.yml
    |       auto-merges to patterns.yml (if --auto-merge)
    |       updates last_analysis.yml
    |
    v
Next Workflow
    |-- pattern_matcher.py finds applicable patterns
    |-- apply_pattern.py injects guidance, tracks via pattern_performance.yml
```

---

## 12. Maintainability

### Strengths

1. **Clear file organization**: State in `forge/memory/`, scripts in `.claude/scripts/`, agents in `.claude/agents/`
2. **Well-documented schemas**: The decisions-schema.md and patterns.yml comments are thorough
3. **Separation of concerns**: Each script has a single responsibility
4. **Privacy-aware**: The sanitization layer shows thoughtful security design
5. **Configurable thresholds**: Learning system behavior can be tuned via settings.yml

### Weaknesses

1. **No integration tests**: None of the scripts have been tested with real data
2. **Import bug**: `log_event.py` uses `from .sanitize import sanitize_context` (relative import) but includes `if __name__ == "__main__"` test code that would fail when run directly
3. **Circular dependency risk**: `pattern_analysis.py` tries to import from `learning_state` at runtime with a try/except fallback, suggesting import issues were encountered
4. **Duplicated load logic**: Both `pattern_matcher.py` and `apply_pattern.py` have their own `load_patterns()` functions that read the same file
5. **No schema validation**: YAML files are loaded with `safe_load` but never validated against a schema -- corrupt data would silently produce wrong behavior
6. **Relative path fragility**: All scripts use relative paths (`"forge/memory/learning/events.jsonl"`) assuming they're run from the repo root. No path resolution logic.
7. **Over-documented**: The learning README is 400+ lines documenting a system that has never been used. The extensive example patterns, phase descriptions, and success metrics create a false impression of maturity.
8. **Dead code in pattern_analysis.py**: Only 3 of 5 documented pattern types are implemented (missing: success_indicator, efficiency_pattern)

### Difficulty of Modification

**Easy to modify**: The code is straightforward Python with no external dependencies beyond PyYAML. The learning scripts are loosely coupled -- you could delete the entire learning system without affecting project.yml or decisions.

**Hard to understand**: The system's complexity creates cognitive overhead. A new developer would need to read 6 Python files, 1 agent definition, 1 README, 3 YAML schemas, and 1 settings file just to understand the learning pipeline. And then discover it has never been used.

### Recommendations for Rebuild

1. **Keep**: `project.yml` (simplify), `important_decisions.yml` (simplify), `settings.yml`
2. **Simplify**: Replace the entire learning pipeline with a simple `lessons_learned.yml` file that agents can append to. Let the LLM do the "pattern matching" by reading past lessons -- it's better at this than regex-based Python analysis.
3. **Delete**: The event logging pipeline, pattern analysis scripts, pattern matching scripts, and the dedicated learning agent. They represent ~1,500 lines of code solving a problem that either doesn't exist yet or is better solved by the LLM itself.
4. **Fix**: If keeping any event logging, use absolute path resolution and fix the import issues in `log_event.py`.
5. **Consider**: Whether sprint/velocity tracking adds value. For a Claude Code workflow, tracking "what was done and what's next" is more useful than Agile-ceremony sprint metrics.
