# Shaktra Intelligence System

Shaktra genuinely learns from past development. Every workflow captures observations about what worked, what failed, and what surprised. A memory-curator agent consolidates those observations into principles, anti-patterns, and procedures — long-term knowledge that shapes how agents approach future stories.

The intelligence cycle: **observations** from completed work feed into **consolidation**, which produces curated knowledge stores. Before each new story, a **briefing** filters relevant knowledge for the agents. Agents **apply** that knowledge during implementation, then write new observations that **reinforce or challenge** existing entries. The system self-corrects — knowledge that proves wrong loses confidence and gets archived.

---

## Architecture Overview

```
  Memory Stores ──1. Filter──▶ Briefing ──2. Read──▶ Agent Execution
  (principles,                (.briefing.yml)        3. Apply principles
   anti-patterns,                                    4. Write observations
   procedures)   ◀─6. Update── Consolidation ◀─5.── .observations.yml
```

**File locations:**
- Long-term stores: `.shaktra/memory/principles.yml`, `anti-patterns.yml`, `procedures.yml`
- Per-story files: `.shaktra/stories/<id>/.briefing.yml`, `.observations.yml`

| Component | Purpose |
|---|---|
| **Principles** | Code-level patterns — what to do and why (e.g., "always validate email in the service layer") |
| **Anti-patterns** | Proven failure modes — what not to do (e.g., "never return raw database errors in API responses") |
| **Procedures** | Workflow-level patterns — how to run the process (e.g., "run coverage after each file, not at the end") |
| **Briefings** | Per-story filtered view of relevant knowledge, generated at workflow start |
| **Observations** | Raw agent findings captured during a workflow, consumed by consolidation |

---

## The Memory Lifecycle

### 1. Briefing Generation

At the start of every `/shaktra:dev` workflow, the orchestrator reads all three memory stores and generates `.briefing.yml` for the story. It filters entries by:

- `status: active` (excludes archived/superseded)
- `confidence >= 0.4` (excludes low-confidence entries)
- Keyword/tag overlap with the story's title, description, and file scope
- Workflow type match (for procedures)

Each included entry gets a one-sentence `relevance` explanation and a `roles` tag for agent-filtered reading.

### 2. Agent Reading

Agents read only the briefing entries tagged for their role:

- **Developer** reads entries where `roles` includes `developer`
- **SW Quality** reads entries where `roles` includes `sw-quality`
- **Architect** reads entries where `roles` includes `architect`

This keeps agent context focused — no agent loads the full memory stores.

### 3. Principle Application

Agents actively follow briefing guidance during their work. This is not passive — agents reference specific principle IDs in code comments, choose implementation approaches based on anti-pattern warnings, and adapt their workflow based on procedure recommendations.

### 4. Observation Capture

During execution, agents write observations to `.observations.yml` when they encounter non-obvious discoveries, quality gate findings, fix rationales, deviations from plan, or consistency checks against existing principles. Routine operations ("tests passed") are not observed.

### 5. Memory Consolidation

After the workflow completes, the memory-curator agent runs the SYNTHESIZE algorithm:

1. **Classify** each observation by type and tags into principle, anti-pattern, or procedure candidates
2. **Match** candidates against existing entries (title similarity, category overlap, guidance overlap)
3. **Apply confidence math** — reinforce matches, weaken contradictions, create new entries
4. **Detect anti-patterns** — 2+ failure observations on the same pattern within 3 stories
5. **Detect procedures** — 3+ workflow-level observations across different stories
6. **Deduplicate** — merge entries with >80% guidance overlap
7. **Archive** — set `status: archived` on entries below the confidence threshold

### 6. Knowledge Persistence

Updated stores are written back to `.shaktra/memory/`. The next story's briefing will include the new and reinforced entries, closing the loop.

---

## Confidence Math

All parameters come from `settings.memory.*`:

| Parameter | Default | Effect |
|---|---|---|
| `confidence_start` | 0.6 | Initial confidence for new entries |
| `confidence_reinforce` | +0.08 | Added when an observation confirms an existing entry |
| `confidence_weaken` | -0.08 | Subtracted when an observation partially contradicts |
| `confidence_contradict` | -0.20 | Subtracted when an observation directly contradicts |
| `confidence_archive` | 0.2 | Entries below this threshold are archived |

Confidence is clamped to `[0.0, 1.0]`.

**Example trajectory:** A principle starts at 0.6. Two stories later, two consistency-check observations reinforce it: `0.6 + 0.08 + 0.08 = 0.76`. Another reinforcement: `0.76 + 0.08 = 0.84`. One contradiction: `0.84 - 0.20 = 0.64`. The principle weakened but remains active (above 0.2).

---

## Observation Types

| Type | When Written | Typical Agent |
|---|---|---|
| `discovery` | Found a non-obvious pattern or constraint | developer, sw-engineer |
| `quality-loop-finding` | Quality gate blocked and required fixes | sw-quality |
| `fix-rationale` | Explains why a specific fix was chosen | developer |
| `deviation` | Implementation diverged from agreed plan | developer |
| `observation` | General workflow or risk observation | any agent |
| `consistency-check` | Validated or challenged an existing principle | developer, sw-quality |

Each observation includes: `id`, `agent`, `phase`, `type`, `text`, `tags`, `importance` (1-10). Type-specific optional fields include `severity`, `resolved`, `principle_id`, and `relationship`. Full schema: `dist/shaktra/skills/shaktra-reference/schemas/observations-schema.md`.

---

## Real-World Example — Test Evidence

This section uses actual data from an E2E test run of the memory system. The test implemented a user registration endpoint (`ST-TEST-001`) with seeded memory from prior stories.

### Seeded Memory

The test started with 4 entries representing knowledge from previous work:

| ID | Type | Text | Confidence |
|---|---|---|---|
| PR-001 | Principle | Always validate email format in the service layer before passing to the repository | 0.76 |
| PR-002 | Principle | Service layer must raise domain-specific exceptions, never generic Python exceptions | 0.84 |
| AP-001 | Anti-pattern | Returning raw database errors directly in API responses leaks implementation details | 0.72 |
| PC-001 | Procedure | Run test coverage check after each file rather than only at the end | 0.68 |

### Briefing Output

The orchestrator generated `.briefing.yml` at workflow start, including all 4 seeded entries:

```yaml
relevant_principles:
  - id: PR-001
    text: "Always validate email format with a regex check in the service layer"
    confidence: 0.76
    guidance:
      - "Use a standard email regex — do not rely on database constraints alone"
      - "Return a clear validation error (422) when format is invalid"
    roles: [developer, sw-engineer]

  - id: PR-002
    text: "Service layer functions must raise domain-specific exceptions"
    confidence: 0.84
    guidance:
      - "Define custom exception classes for each business error"
      - "Catch repository exceptions and re-raise as domain exceptions"
    roles: [developer, sw-engineer, sw-quality]

relevant_anti_patterns:
  - id: AP-001
    failed_approach: "Returning raw database errors directly in API responses"
    severity: P1
    recommended_approach: "Catch in service layer, map to domain errors"
    roles: [developer, sw-quality]

relevant_procedures:
  - id: PC-001
    text: "Run test coverage check after each file rather than only at the end"
    confidence: 0.68
    roles: [developer]
```

### Agent Application

The developer read the briefing and applied each entry, logging each application:

```
MEMORY: [developer] applying PR-001 — email validation implemented in service layer
MEMORY: [developer] applying PR-002 — domain-specific exception hierarchy
MEMORY: [developer] applying AP-001 — route handler catches domain exceptions
MEMORY: [developer] applying PC-001 — ran tests after each component group
```

The generated code references principle IDs directly:

```python
# src/services/user_service.py
# Applies: PR-001 (email validation in service layer), PR-002 (domain-specific
# exceptions only), AP-001 (never return raw database errors)

# src/exceptions.py
# Generic exceptions and raw database errors must never leak to the API layer (PR-002, AP-001).
```

### Consistency Checks

During execution, agents wrote consistency-check observations that explicitly validate seeded principles:

| Observation | Agent | Phase | Principle | Relationship |
|---|---|---|---|---|
| OB-003 | developer | code | PR-001 | reinforce |
| OB-004 | developer | code | PR-002 | reinforce |
| OB-013 | sw-quality | quality | PR-001 | reinforce |
| OB-014 | sw-quality | quality | PR-002 | reinforce |

Example observation:

```yaml
- id: OB-003
  agent: developer
  phase: code
  type: consistency-check
  importance: 8
  principle_id: PR-001
  relationship: reinforce
  text: "Email validation implemented in service layer via validate_email()
         before any repository interaction, exactly as PR-001 prescribes."
```

### Consolidation Results

The memory-curator consolidated all observations, updating confidence scores:

**Principles:**

| ID | Before | After | Change |
|---|---|---|---|
| PR-001 | 0.76 | **0.92** | +0.16 (2 reinforcements) |
| PR-002 | 0.84 | **1.0** (capped) | +0.16 (2 reinforcements) |
| PR-003 | — | **0.6** (new) | "Security invariants must be verified with caplog-based tests" |
| PR-004 | — | **0.6** (new) | "Dependency wiring must live outside all layers" |

**Anti-patterns:**

| ID | Before | After | Change |
|---|---|---|---|
| AP-001 | 0.72 | **0.80** | Reinforced |
| AP-002 | — | **0.6** (new) | "API route modules importing concrete repository classes directly" |

**Procedures:**

| ID | Before | After | Change |
|---|---|---|---|
| PC-001 | 0.68 | **0.76** | Reinforced, source_count 3 → 4 |

**Confidence math verified:** PR-001: `0.76 + 0.08 + 0.08 = 0.92`. PR-002: `0.84 + 0.08 + 0.08 = 1.0` (capped). New entries start at `0.6`. All match `settings.memory.*` defaults.

### Timeline

| Time | Event |
|---|---|
| 19:47:24 | Briefing generated — all 4 seeded entries included |
| 19:54:23 | RED phase — test-agent reads briefing (2 principles, 1 AP, 1 procedure) |
| 20:02:09 | GREEN phase — developer applies all 4 entries |
| 20:04:50 | Code complete — developer writes 2 discoveries + 2 consistency-checks |
| 20:12:55 | QUALITY complete — sw-quality writes 6 observations + 2 consistency-checks |
| 20:17:57 | MEMORY phase — memory-curator consolidates |
| 20:21:23 | `memory_captured=true` — consolidation complete |

---

## Memory Stores Reference

| Store | ID Format | Key Fields | Full Schema |
|---|---|---|---|
| `principles.yml` | PR-NNN | text, categories, guidance, confidence, roles, scope, status | `dist/shaktra/skills/shaktra-reference/schemas/principles-schema.md` |
| `anti-patterns.yml` | AP-NNN | failed_approach, failure_mode, severity, recommended_approach, trigger_patterns | `dist/shaktra/skills/shaktra-reference/schemas/anti-patterns-schema.md` |
| `procedures.yml` | PC-NNN | text, confidence, applies_to, roles | `dist/shaktra/skills/shaktra-reference/schemas/procedures-schema.md` |

All stores share: `confidence`, `tags`, `roles`, `scope`, `status`, `source`, `created`. Active entries are included in briefings; archived entries remain in the file for audit but are excluded from agent loading.

---

## Configuration

All intelligence parameters live in `settings.memory.*`:

| Parameter | Default | Purpose |
|---|---|---|
| `confidence_start` | 0.6 | Initial confidence for newly created entries |
| `confidence_reinforce` | 0.08 | Confidence boost per reinforcing observation |
| `confidence_weaken` | 0.08 | Confidence penalty per weakening observation |
| `confidence_contradict` | 0.20 | Confidence penalty per direct contradiction |
| `confidence_archive` | 0.2 | Entries below this are archived |
| `max_principles` | 200 | Active principle cap (lowest-confidence archived first) |
| `max_anti_patterns` | 100 | Active anti-pattern cap |
| `max_procedures` | 50 | Active procedure cap |
| `max_observations_per_story` | 30 | Max observations per story workflow |

---

## Migration from Legacy System

Earlier versions of Shaktra used `decisions.yml` and `lessons.yml` for project memory. The new system replaces both with the principles/anti-patterns/procedures model, adding confidence tracking, role-based filtering, and automated consolidation.

To migrate an existing project:

```bash
python3 dist/shaktra/scripts/migrate_memory.py /path/to/project
```

The script converts decisions to principles (confidence 0.7) and lessons to seed principles (confidence 0.5). Original files are backed up as `.bak`. Anti-patterns and procedures start empty — they are created organically through the consolidation process as new observations accumulate.
