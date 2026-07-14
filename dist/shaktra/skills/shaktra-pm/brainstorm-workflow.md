# Brainstorm Workflow

Guided ideation for exploring the problem space before committing to
requirements. Conversational — runs in the main loop. The goal is exploration,
not commitment: surface options, identify constraints, align on the
opportunity before formal requirements.

## Steps

**1 — Load context:** `.shaktra/settings.yml` (project type),
`.shaktra/memory/principles.yml` and `anti-patterns.yml` (constraints from
prior work, if they exist).

**2 — Problem exploration.** What problem? Who has it (be specific — not
"users" but "developers who deploy multiple times per day")? Impact of not
solving it (cost, time, frustration, risk)? Why now (market, business, user
demand)?
→ Capture: `problem` {statement (1-2 sentences), affected_users[], impact[]
{type: cost|time|frustration|risk|revenue, description}, urgency {driver,
reasoning}}.

**3 — User needs.** Primary and secondary users; how they solve it today
(workarounds, competitors); what success looks like for them; their
constraints.
→ Capture: `users` {primary {description, current_solution,
success_looks_like}, secondary[] {description, relationship}}.

**4 — Market context.** How competitors solve it and what they miss; trends
that help or hinder; regulatory/technical/business constraints; adjacent
opportunities.
→ Capture: `market` {competitors[] {name, approach, gaps[]}, trends[] {trend,
implication}, constraints[] {type, description}}.

**5 — Opportunity definition.** The opportunity; our unique angle; target
scope; explicit out-of-scope.
→ Capture: `opportunity` {statement, unique_angle, target_scope,
out_of_scope[]}.

**6 — Write notes** to `.shaktra/pm/brainstorm.md`: the four captured
sections plus **Open Questions** (unresolved items surfaced) and **Next
Steps** (create PRD via `/shaktra:pm prd`, validate assumptions with research,
review with stakeholders).

**7 — Present summary:** 1-line problem, primary users, 1-line opportunity,
top 3 insights, open questions, output path, next step.

## Quality Checklist (iterate with the user until all pass)

- Problem statement is specific (not "improve X")
- At least one primary user identified
- Impact quantified or described concretely
- Current solutions/workarounds documented
- Opportunity statement is actionable
- Out-of-scope explicitly stated

## Standalone vs Full Workflow

**Standalone** (`/shaktra:pm brainstorm`): produces the notes only; the user
decides the next step. **Full workflow:** after user confirmation, the notes
become the `context_summary` for the artifact workflow (hypothesis-first path).
