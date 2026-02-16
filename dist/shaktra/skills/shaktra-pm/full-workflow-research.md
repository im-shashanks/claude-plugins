# Full Workflow — Research-First Path

Use when you have existing user research (interviews, surveys, feedback). Produces evidence-backed artifacts.

```
Research → Personas → Journeys → PRD → [USER APPROVAL]
```

---

## Phase 1 — Research Analysis

**Purpose:** Extract insights from existing research data.

### Steps

1. **Collect research inputs:**
   - If research is embedded in user's document → extract research sections
   - If separate files → ask for paths
   - Supported: interview transcripts, survey data, support tickets, feedback logs

2. Spawn **product-manager** (mode: research-analyze) with inputs

3. **Extract per source:**
   - Pain points (severity, frequency)
   - Feature requests (context, priority)
   - JTBD patterns (situation, motivation, outcome)
   - Competitor mentions (sentiment, context)
   - Key quotes (theme-tagged)

4. **Synthesize:**
   - Cluster pain points into themes
   - Calculate confidence (3+ sources = high, 2 = medium, 1 = low)
   - Generate recommendations

5. Write to `.shaktra/research/`
6. EMIT `RESEARCH_SYNTHESIZED`
7. Present summary to user

### Output

- `.shaktra/research/{id}.yml` — per-source analyses
- `.shaktra/research/synthesis.yml` — themes, patterns, recommendations

---

## Phase 2 — Personas

**Purpose:** Create personas grounded in research evidence.

### Steps

1. Spawn **product-manager** (mode: persona-create) with:
   - Research synthesis
   - User's original context/document

2. For each user segment identified in research:
   - Generate persona with JTBD
   - Link evidence (interview IDs, quotes)
   - Minimum 2 evidence entries (should be easy with research)

3. Validate against persona schema
4. Write to `.shaktra/personas/`
5. EMIT `PERSONAS_COMPLETE`
6. Present summary

### Output

- `.shaktra/personas/*.yml` — research-backed personas (high evidence quality)

---

## Phase 3 — Journey Mapping

**Purpose:** Map experiences to surface pain points and opportunities for PRD.

### Steps

1. Spawn **product-manager** (mode: journey-create) for ALL personas in parallel — one Task() call per persona, all in a single response:
   - Each agent maps its persona through: Awareness → Consideration → Acquisition → Service → Loyalty
   - Captures per stage: touchpoints, actions, emotions, pain points, opportunities
   - Identifies moments of truth
   - Writes to `.shaktra/journeys/{persona_id}-journey.yml`

3. **Aggregate for PRD input:**
   - Collect all pain points across journeys
   - Collect all opportunities (classified by impact/effort)
   - Collect all moments of truth

4. Present summary with key findings that will inform PRD

### Output

- `.shaktra/journeys/*.yml` — journey maps
- Aggregated insights ready for PRD phase

---

## Phase 4 — PRD Creation

**Purpose:** Write requirements informed by research, personas, AND journeys.

### Steps

1. **Select PRD template (REQUIRED — use AskUserQuestion tool):**

   Ask the user: "What size feature is this?"
   - **Standard PRD (6-8 weeks)** — Full PRD for complex features requiring design docs
   - **One-Page PRD (2-4 weeks)** — Abbreviated PRD for smaller, well-understood features

   Wait for user response before proceeding.

2. Spawn **product-manager** (mode: prd-create) with:
   - Research synthesis (themes, recommendations)
   - Personas (goals, frustrations)
   - Journey insights (pain points, opportunities, moments of truth)
   - User's original context/document
   - Selected template

3. **PRD incorporates journey insights:**
   - Journey pain points → functional requirements
   - Journey opportunities (Quick Wins) → "should have" requirements
   - Moments of truth → acceptance criteria for key requirements
   - Persona goals → success metrics

4. **Quality review loop** (max 3 attempts):
   ```
   WHILE attempts < 3:
     spawn PM (mode: prd-review)
     IF QUALITY_PASS: break
     ELSE: spawn PM (mode: prd-create, fix=findings)
   ```

5. Write to `.shaktra/prd.md`
6. EMIT `PRD_COMPLETE`

7. **User approval gate:**
   > "PRD ready for review. It includes:
   > - {N} requirements from journey pain points
   > - {N} requirements from research recommendations
   > - {N} acceptance criteria from moments of truth
   >
   > Approve to finalize, or request changes."

   - On approval: EMIT `PRD_APPROVED`, continue to Memory
   - On rejection: iterate

### Output

- `.shaktra/prd.md` — evidence-backed PRD with journey insights

---

## Continue to Shared Phases

After PRD approval, continue with shared phases in `full-workflow.md`:
- Prioritization (if stories exist)
- Memory Capture

---

## Traceability

Research-first path produces full traceability:

```
Research findings
    ↓
Personas (evidence: interview IDs)
    ↓
Journeys (pain points link to research)
    ↓
PRD (requirements trace to personas + journeys)
    ↓
TPM → Stories (requirements trace to REQ-IDs)
```
