# Full Workflow — Hypothesis-First Path

Use when starting fresh without research data. Produces assumption-based artifacts that can be validated later.

```
Brainstorm → Personas → Journeys → PRD → [USER APPROVAL]
```

---

## Phase 1 — Brainstorm

**Purpose:** Explore the problem space and articulate hypotheses.

### Steps

1. Spawn **product-manager** (mode: brainstorm) with user's context
   - If context from document: extract and structure existing thinking
   - If brief context: ask deeper questions

2. **Guide through ideation:**
   - Problem exploration: What problem? Who has it? Impact?
   - User needs: Who are the users? What do they need? Current solutions?
   - Market context: Competitors? Trends? Constraints?
   - Opportunity definition: What's the opportunity? Why now? Out of scope?

3. Write to `.shaktra/pm/brainstorm.md`
4. Present summary

5. **User checkpoint:**
   > "Ready to define user personas?"
   - If yes: proceed
   - If no: iterate on brainstorm

### Output

- `.shaktra/pm/brainstorm.md` — structured ideation notes (hypotheses)

---

## Phase 2 — Personas (Assumption-Based)

**Purpose:** Create personas from brainstorm insights (lower evidence, but enables journey mapping).

### Steps

1. Spawn **product-manager** (mode: persona-create) with:
   - Brainstorm notes (user segments, needs identified)
   - User's original context

2. For each user segment from brainstorm:
   - Generate persona with JTBD
   - Evidence type = "assumption" (from brainstorm)
   - Note: Lower confidence than research-backed personas

3. Write to `.shaktra/personas/`
4. EMIT `PERSONAS_COMPLETE`
5. Present summary with caveat about assumption-based evidence

### Output

- `.shaktra/personas/*.yml` — assumption-based personas (medium-low evidence quality)

---

## Phase 3 — Journey Mapping

**Purpose:** Map hypothesized experiences to surface potential pain points for PRD.

### Steps

1. Spawn **product-manager** (mode: journey-create) for ALL personas in parallel — one Task() call per persona, all in a single response:
   - Each agent maps its persona through: Awareness → Consideration → Acquisition → Service → Loyalty
   - Captures per stage: touchpoints, actions, emotions, pain points, opportunities
   - Identifies moments of truth
   - Note: These are hypotheses to validate
   - Writes to `.shaktra/journeys/{persona_id}-journey.yml`

3. **Aggregate for PRD input:**
   - Collect hypothesized pain points
   - Collect opportunity ideas (classified by impact/effort)
   - Collect moments of truth (to become acceptance criteria)

4. Present summary:
   > "Journey mapping identified {N} potential pain points and {N} opportunities.
   > These are hypotheses — consider validating with user research later."

### Output

- `.shaktra/journeys/*.yml` — hypothesized journey maps
- Aggregated insights ready for PRD phase

---

## Phase 4 — PRD Creation

**Purpose:** Write requirements informed by brainstorm, personas, AND journeys.

### Steps

1. **Select PRD template (REQUIRED — use AskUserQuestion tool):**

   Ask the user: "What size feature is this?"
   - **Standard PRD (6-8 weeks)** — Full PRD for complex features requiring design docs
   - **One-Page PRD (2-4 weeks)** — Abbreviated PRD for smaller, well-understood features

   Wait for user response before proceeding.

2. Spawn **product-manager** (mode: prd-create) with:
   - Brainstorm notes
   - Personas (goals, frustrations — assumption-based)
   - Journey insights (pain points, opportunities, moments of truth)
   - Selected template

3. **PRD incorporates journey insights:**
   - Journey pain points → functional requirements (marked as hypotheses)
   - Journey opportunities → "should have" / "could have" requirements
   - Moments of truth → acceptance criteria for key requirements
   - Persona goals → success metrics

4. **Quality review loop** (max 3 attempts)

5. Write to `.shaktra/prd.md`
6. EMIT `PRD_COMPLETE`

7. **User approval gate:**
   > "PRD ready for review. It includes:
   > - {N} requirements from journey pain points (hypotheses)
   > - {N} opportunities identified
   >
   > Note: Requirements are hypothesis-based. Consider user research to validate.
   >
   > Approve to finalize, or request changes."

   - On approval: EMIT `PRD_APPROVED`
   - On rejection: iterate

### Output

- `.shaktra/prd.md` — hypothesis-based PRD with journey insights

---

## Continue to Shared Phases

After PRD approval, continue with shared phases in `full-workflow.md`:
- Prioritization (if stories exist)
- Memory Capture

---

## Evidence Quality Note

Hypothesis-first path produces **assumption-based artifacts**:

| Artifact | Evidence Quality | Recommendation |
|---|---|---|
| Personas | Low (assumptions) | Validate with research before major investment |
| Journeys | Low (hypothesized) | Test with real users |
| PRD Requirements | Medium (structured but unvalidated) | Run `/shaktra:pm research` to validate |

The artifacts are useful for getting started, but should be validated. Run `/shaktra:pm research` later when you have user data.
