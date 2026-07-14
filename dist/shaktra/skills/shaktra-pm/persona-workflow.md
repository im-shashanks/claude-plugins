# Persona Generation Workflow

Create evidence-based user personas from PRD user descriptions and research
findings. Personas ground requirements in real user needs and enable
traceability. Executed by the product-manager agent (persona target of
`workflows/pm-artifacts.js`).

## Steps

**1 — Load context:** `.shaktra/prd.md` (primary source for user segments —
if it has no user section, derive segments from the product context supplied
at dispatch), `.shaktra/research-synthesis.md` and research files (if they
exist), `.shaktra/settings.yml`.

**2 — Identify segments:** each PRD user segment becomes a candidate persona
(role, segment, key characteristic minimum).

**3 — Generate each persona** per `persona-schema.md`:

- `id` (P-NNN), `name` (archetype — "Power User Paula"), `role`, `segment`
- `goals[]` (min 2), `frustrations[]` (min 2), `behaviors[]`
- `jobs_to_be_done[]` — {situation "When I…", motivation "I want to…",
  outcome "So I can…"} (min 1)
- `evidence[]` — {type: interview|analytics|survey|observation|assumption,
  id, insight} (minimum per settings `pm.min_persona_evidence`)

**Evidence sourcing:** research exists → link specific interviews, quotes,
findings by id. No research → use PRD descriptions and mark
`type: assumption` explicitly — never dress assumptions as evidence.

**4 — Enrich from research** (when synthesis exists): match themes to
personas by segment; add specific pain points as frustrations; add JTBD
patterns; include verbatim quotes where powerful; link evidence IDs.

**5 — Validate each persona:**

| Check | Severity |
|---|---|
| Evidence entries ≥ `pm.min_persona_evidence` | P0 |
| At least 1 JTBD | P0 |
| Goals ≥ 2, frustrations ≥ 2 | P1 |
| Evidence IDs reference existing sources | P1 |

**6 — Write** each persona to `.shaktra/personas/{persona_id}.yml` (create
the directory if needed).

**7 — Summarize:** persona table (id, name, segment, evidence count),
evidence coverage (research-backed vs assumption-based), top JTBDs, files
created, next steps (journeys → PRD references → more research if evidence is
thin).

## Quality Tiers

| Tier | Evidence | Confidence |
|---|---|---|
| **Validated** | 3+ interview sources | High — supports Must Have requirements |
| **Supported** | 1-2 sources | Medium — supports Should Have requirements |
| **Hypothetical** | Assumptions only | Low — validate before major investment |

Mark each persona's tier in the summary. Personas are living documents:
update with new research, increment version, archive superseded versions.
