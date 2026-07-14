# Research Analysis Workflow

Transform raw qualitative research (interview transcripts, surveys, feedback,
observation notes — text/markdown files or pasted text) into structured
insights that inform personas, validate requirements, and guide decisions.
Executed by the product-manager agent (research target of
`workflows/pm-artifacts.js`).

## Steps

**1 — Load:** the research inputs named at dispatch, plus `.shaktra/prd.md`
(if it exists, for validation) and `.shaktra/memory/principles.yml`.

**2 — Extract per-source findings** to `.shaktra/research/{source_id}.yml`:

- `pain_points[]` {id PP-NN, description, severity: high|medium|low,
  frequency: daily|weekly|monthly|rarely, quote (verbatim when available)}
- `feature_requests[]` {id FR-NN, description, priority (their words), context}
- `jobs_to_be_done[]` {situation, motivation, outcome, current_solution}
- `competitor_mentions[]` {name, context, sentiment}
- `key_quotes[]` {quote (verbatim), context, theme}

**3 — Synthesize** to `.shaktra/research-synthesis.md`:

- **Themes:** cluster pain points across sources by similarity; name each
  ("Slow Onboarding"); count evidence; confidence = high (3+ sources),
  medium (2), low (1 or conflicting). Each theme lists its supporting
  source/pain-point ids.
- **Patterns:** {name, description, frequency: common|occasional|rare,
  evidence[] {source_id, observation}}.
- **Recommendations:** {id REC-NN, recommendation, rationale, priority,
  supporting_themes[], confidence}.

**4 — Validate against the PRD** (when one exists): map themes to
requirements; report requirements validated by research, requirements resting
on assumptions, and user needs missing from the PRD (potential gaps).

**5 — Identify research gaps:** {area, reason, suggested_method:
interview|survey|analytics|observation}.

**6 — Summarize:** sources analyzed, top pain points by frequency, theme
table with confidence, top recommendations, gaps, files created, next steps
(personas → gap research → PRD update).

## Quality Checklist

- Each source yields at least 1 pain point and 1 JTBD (or its absence is noted)
- Synthesis has at least 2 themes
- Confidence levels match the evidence criteria exactly
- At least 1 actionable recommendation

## Integration Notes

- **Personas:** persona `evidence` entries reference these source ids.
- **PRD:** high-confidence themes should map to Must Have requirements.
- **Journeys:** pain points and JTBD inform journey stage details.
