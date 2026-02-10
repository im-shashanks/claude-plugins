# Phase 4 — TPM Workflow [COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) before starting.
> **Depends on:** Phase 2 (Reference System), Phase 3 (State Schemas)
> **Blocks:** Phase 10 (Sprint Planning), Phase 11 (Workflow Router)

---

## Objective

Build the first complete workflow: Tech Program Manager. Covers design doc creation, user story generation, quality review loops, product management, and sprint planning basics.

## Deliverables — Skill

| File | Lines | Purpose |
|------|-------|---------|
| `skills/shaktra-tpm/SKILL.md` | ~250 | TPM orchestrator — intent classification, sub-agent dispatch |
| `skills/shaktra-tpm/workflow-template.md` | ~200 | Step-by-step orchestration for design → stories → PM |

## Deliverables — Internal Skill

| File | Lines | Purpose |
|------|-------|---------|
| `skills/shaktra-stories/SKILL.md` | ~80 | Story schema manifest |
| `skills/shaktra-stories/story-creation.md` | ~150 | Story creation rules, enrichment rules, tier detection |

## Deliverables — Agents

| File | Lines | Purpose |
|------|-------|---------|
| `agents/shaktra-architect.md` | ~120 | Design doc creation from PRD + Architecture |
| `agents/shaktra-tpm-quality.md` | ~80 | Quality review of TPM artifacts |
| `agents/shaktra-scrummaster.md` | ~150 | Story creation from design docs + enrichment of sparse stories |
| `agents/shaktra-product-manager.md` | ~100 | RICE prioritization, requirement alignment |

## Workflow

```
User: /shaktra:tpm "Create design and stories for user authentication"

TPM Skill (main thread):
  1. Read project context (.shaktra/settings.yml, .shaktra/memory/decisions.yml, .shaktra/memory/lessons.yml)
  2. Classify sub-intent: design | stories | full-workflow | sprint | enrich | hotfix
  3. If hotfix:
     a. Spawn shaktra-scrummaster (hotfix mode) → Trivial tier story
        - Scrummaster reads user's hotfix description
        - Reads codebase context to identify affected files
        - Creates minimum viable story (3 fields: title, description, files)
        - Auto-sets tier to Trivial
     b. Spawn shaktra-tpm-quality → Quick review (single pass, no loop)
     c. Present story to user for confirmation
     d. Write story to .shaktra/stories/
     e. Recommend: "Run /shaktra:dev ST-XXX to fix"
  4. If enrich:
     a. Load target stories (.shaktra/stories/ST-XXX.yml — single or batch)
     b. For each story (parallel if batch):
        - Spawn shaktra-scrummaster (enrich mode) → Enriched Story
          - Scrummaster reads sparse story
          - Reads codebase context (existing code, patterns, architecture)
          - Reads .shaktra/analysis/ if available (from prior /shaktra:analyze)
          - Auto-detects appropriate tier based on complexity
          - Fills missing tier-required fields (test_specs, io_examples, error_handling, etc.)
        - Spawn shaktra-tpm-quality → Review Enriched Story (loop max 3)
          - Same create-review-fix loop pattern as story creation
     c. Present enriched stories to user for approval (AskUserQuestion)
     d. Write approved stories to .shaktra/stories/
  5. If full-workflow or design:
     a. Spawn shaktra-architect → Design Doc
        - Architect reads PRD + Architecture files
        - If gaps found → returns GAPS_FOUND with questions
        - TPM spawns shaktra-product-manager to answer questions
        - If PM can't answer → TPM uses AskUserQuestion to surface to user
        - TPM re-spawns architect with answers → Design Doc completed
     b. Spawn shaktra-tpm-quality → Review Design Doc (loop max 3)
        - If QUALITY_BLOCKED → spawn architect with gaps → re-review
        - If QUALITY_PASS → proceed
        - If MAX_LOOPS_REACHED → surface to user
  6. If full-workflow or stories:
     a. Spawn shaktra-scrummaster → User Stories (from Design Doc)
     b. Spawn shaktra-tpm-quality → Review Stories (loop max 3)
        - Same create-review-fix loop pattern
  7. If full-workflow or sprint:
     a. Spawn shaktra-product-manager → RICE, prioritization, alignment
     b. Spawn shaktra-scrummaster → Sprint allocation
  8. MEMORY CAPTURE (mandatory final step):
     a. Spawn shaktra-memory-curator
        - Reviews workflow artifacts (design docs, stories, quality findings)
        - Evaluates: "Would this materially change future workflow execution?"
        - Writes actionable insights to .shaktra/memory/lessons.yml (if any)
  9. Report completion summary to user
```

## Agent Content Outlines

**shaktra-architect.md:**
- **Persona:** Principal Software Architect with over 25 years experience designing large-scale, distributed systems at FAANG companies. Expert in system design, API contracts, failure mode analysis, and creating comprehensive technical specifications.
- **Skills loaded:** `shaktra-reference` (via `skills` frontmatter — preloaded at agent startup)
- **Tools:** Read, Write, Glob, Grep, WebSearch, WebFetch (via `tools` frontmatter)
- **Model:** opus (justified: design docs are high-leverage artifacts)
- **Input contract:** PRD path, Architecture path, optional analysis artifacts path, optional gap answers
- **Process:**
  1. Load and synthesize all input documents
  2. Gap analysis: identify missing requirements, unclear edge cases, architecture conflicts
  3. If gaps found → return GAPS_FOUND with structured questions (do NOT create doc yet)
  4. If no gaps → create comprehensive design document
- **Output:** Design document in `.shaktra/designs/` or GAPS_FOUND response
- **Design doc sections:** Scale by project complexity (not always all sections)
  - Core (always): Contract specs, Error taxonomy, State machines, Test strategy, Data model, Dependencies
  - Extended (medium+ projects): Threat model, Invariants, Observability, ADRs
  - Advanced (large projects): Failure modes, Concurrency, Resource safety, Edge case matrix

**shaktra-tpm-quality.md:**
- **Persona:** Principal Quality Assurance Architect with over 25 years experience ensuring FAANG-level quality standards across design documents, user stories, and technical specifications.
- **Skills loaded:** `shaktra-quality`, `shaktra-reference`
- **Tools:** Read, Glob, Grep
- **Model:** sonnet
- **Input contract:** Artifact path, artifact type (design | story), review context
- **Output format:**
  ```yaml
  verdict: QUALITY_PASS | QUALITY_BLOCKED
  findings:
    - severity: P0
      dimension: A  # References quality-dimensions.md
      issue: "Missing timeout on external API call"
      guidance: "Add 5s timeout with circuit breaker"
  ```

**shaktra-scrummaster.md:**
- **Persona:** Senior Scrum Master with over 15 years experience in agile delivery at FAANG companies. Expert in user story crafting, sprint planning, and translating design specifications into actionable development tasks.
- **Skills loaded:** `shaktra-stories`, `shaktra-reference`
- **Tools:** Read, Write, Glob, Grep
- **Model:** sonnet
- **Input contract:** Design doc path OR sparse story path, project context, mode (create | enrich)
- **Mode: CREATE** (from design docs — default):
  1. Load design doc and story schema from skills
  2. Decompose design into stories following single-scope rule
  3. Auto-detect tier for each story
  4. Populate tier-appropriate fields
  5. **Self-validate before writing:** io_examples has error case, test names match across fields
  6. Write story files to `.shaktra/stories/`
- **Mode: ENRICH** (from sparse external stories):
  1. Load existing sparse story and story schema from skills
  2. Read codebase context: existing code, patterns, architecture relevant to story scope
  3. Read `.shaktra/analysis/` artifacts if available (brownfield context)
  4. Auto-detect appropriate tier based on story complexity and codebase scope
  5. Fill missing tier-required fields by inferring from codebase context
  6. Preserve all original story content — enrich, never overwrite user-provided fields
  7. **Self-validate before returning** (same as create mode)
- **Critical rules (both modes):**
  - Single-scope rule: one scope per story, multi-scope features split
  - Test name contract: all test references must match exact function_name in test_specs
  - io_examples must include at least one error case
  - Max 10 points, max 3 files per story

**shaktra-product-manager.md:**
- **Persona:** Senior Product Manager with over 15 years experience in FAANG product strategy, RICE prioritization, and cross-functional alignment.
- **Skills loaded:** `shaktra-reference`
- **Tools:** Read, Write, Glob, Grep
- **Model:** sonnet
- **Input contract:** Stories path, project context, optional gap questions from architect
- **Process (varies by invocation):**
  - **Gap answering:** Attempt to answer architect's questions from product perspective
  - **RICE prioritization:** Score stories on Reach, Impact, Confidence, Effort
  - **Requirement alignment:** Verify stories cover all PRD requirements
  - **Sprint guidance:** Recommend sprint allocation based on priorities and dependencies

## Validation

- [ ] `/shaktra:tpm "Create design doc"` produces a design document
- [ ] Gap analysis flow works (architect finds gaps → PM answers → architect continues)
- [ ] User escalation works (PM can't answer → user prompted)
- [ ] Quality loop catches issues and architect/scrummaster fixes them
- [ ] Stories match tier requirements
- [ ] Enrichment flow: sparse story → `/shaktra:tpm enrich` → enriched story with tier fields
- [ ] Enrichment preserves original fields (never overwrites user-provided content)
- [ ] Batch enrichment works (multiple stories in parallel)
- [ ] Hotfix flow: `/shaktra:tpm hotfix` → Trivial tier story → ready for `/shaktra:dev`
- [ ] Sprint allocation produces valid sprint plan
- [ ] shaktra-stories skill created with creation rules and enrichment rules
- [ ] All agent files under 150 lines
- [ ] Skill files under 250 lines each
- [ ] No content duplication between agents and loaded skills
- [ ] All static knowledge files are language-agnostic (no language-specific examples)

## Forge Reference

| Forge Source | What to Port | What to Change |
|-------------|-------------|----------------|
| forge-designer agent (389 lines) | Gap analysis flow | Simplify, scale sections by complexity |
| forge-planner agent (252 lines) | Story derivation, single-scope rule | Use tier-aware schema, not 1060-line spec |
| forge-product-manager agent (502 lines) | RICE prioritization | **Reduce scope from 5 workflows to 3** |
| forge-checker PLAN_QUALITY mode | Qualitative review | Move to tpm-quality agent |
| forge-quality skill | Quality dimensions | Reference from shaktra-quality, don't redefine |
