export const meta = {
  name: 'shaktra-tpm-stories',
  description: 'TPM story workflows: create/enrich/hotfix stories, per-story quality loops, RICE, sprint allocation',
  whenToUse: 'Invoked by the /shaktra:tpm skill for stories, enrich, hotfix, sprint, and close-sprint intents',
  phases: [{ title: 'Stories' }, { title: 'Quality gate' }, { title: 'Sprint' }, { title: 'Memory' }],
}
// Replaces the story/enrich/hotfix/sprint portions of workflow-template.md.
//
// args = { plugin_root, project_dir,
//   mode: 'create' | 'enrich' | 'hotfix' | 'sprint' | 'close-sprint',
//   design_path,                  // create mode
//   story_paths: [..],            // enrich mode
//   hotfix_description,           // hotfix mode
//   stories_dir, sprints_path, prd_path,
//   sprints_enabled, default_velocity, sprint_duration_weeks,
//   p1_threshold, max_attempts,
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))
let observations = []
const gates = []
let allFindings = []

async function storyGate(story) {
  const g = await workflow(lib('quality-loop'), {
    schemas: { QUALITY_VERDICT: S.QUALITY_VERDICT },
    gate: 'stories',
    review_mode: 'ARTIFACT_REVIEW',
    artifact_paths: [story.path],
    reviewer_type: 'shaktra-tpm-quality',
    creator_type: 'shaktra-scrummaster',
    context: `Story ${story.id} (${story.tier} tier). Review against the story review checklist, story-schema.md required fields for the tier, and the single-scope rule.`,
    project_dir: a.project_dir,
    handoff_path: null,
    max_attempts: a.max_attempts,
    p1_threshold: a.p1_threshold,
    phase_label: 'Quality gate',
  })
  gates.push(g)
  allFindings = allFindings.concat(g.findings || [])
  observations = observations.concat(g.observations || [])
  return g
}

let stories = []
const phaseSummaries = []

if (a.mode === 'create' || a.mode === 'enrich' || a.mode === 'hotfix') {
  phase('Stories')
  const prompt = a.mode === 'create'
    ? `Create mode: generate user stories from the design doc at ${a.design_path}. Follow story-creation.md steps 1-7 (the final verification loop is mandatory). Write stories as YAML files to ${a.stories_dir}/ST-<NNN>.yml per story-schema.md.`
    : a.mode === 'enrich'
      ? `Enrich mode: enrich these existing stories to their tier's full field set: ${a.story_paths.join(', ')}. Follow story-creation.md enrich steps 1-6; preserve existing content; run final verification.`
      : `Hotfix mode: create ONE trivial-tier story (minimum viable: id, title, description + metadata) for this hotfix: "${a.hotfix_description}". Write it to ${a.stories_dir}/ST-<NNN>.yml (next sequential id). Note in the description that hotfix_coverage_threshold applies.`
  const batch = await agent(
    `${prompt}\nProject: ${a.project_dir}`,
    { agentType: 'shaktra-scrummaster', schema: S.STORY_BATCH, label: a.mode, phase: 'Stories' },
  )
  if (!batch || !batch.stories.length) {
    return { status: 'blocked', phase: 'stories', reason: 'no_stories_produced', observations }
  }
  stories = batch.stories
  phaseSummaries.push({ name: `Stories (${a.mode})`, status: 'complete', summary: batch.summary })

  // Per-story quality loop, all stories in parallel (separate files — no write conflicts).
  // Hotfix skips the loop: a 3-field story has nothing to review.
  if (a.mode !== 'hotfix') {
    phase('Quality gate')
    const results = await parallel(stories.map((st) => () => storyGate(st)))
    const blocked = results.filter(Boolean).filter((g) => !g.passed)
    if (blocked.length) {
      return {
        status: 'blocked', phase: 'story-quality',
        blocked_gates: blocked, stories, findings: allFindings, observations, gates,
      }
    }
  }
}

// ---- RICE + coverage + sprint allocation ----
let riceSummary = null
let sprintSummary = null
if ((a.mode === 'create' || a.mode === 'sprint') && a.sprints_enabled) {
  phase('Sprint')
  const [rice, coverage] = await parallel([
    () => agent(
      `RICE prioritization mode: score every story in ${a.stories_dir} with RICE; classify Quick Win / Big Bet / Standard; suggest a sprint goal. Do NOT write sprints.yml — the scrummaster owns it. Return the ranked list in your summary.\nProject: ${a.project_dir}`,
      { agentType: 'shaktra-product-manager', schema: S.PHASE_RESULT, label: 'rice', phase: 'Sprint' },
    ),
    a.mode === 'create' && a.prd_path ? () => agent(
      `Requirement coverage mode: map every requirement in ${a.prd_path} to covering stories in ${a.stories_dir}. Report coverage % and gaps in your summary.\nProject: ${a.project_dir}`,
      { agentType: 'shaktra-product-manager', schema: S.PHASE_RESULT, label: 'coverage', phase: 'Sprint' },
    ) : () => Promise.resolve(null),
  ])
  observations = observations.concat(rice?.observations || [], coverage?.observations || [])
  riceSummary = { rice: rice?.summary, coverage: coverage?.summary }

  const allocation = await agent(
    `Sprint allocation: read all stories in ${a.stories_dir} and these RICE results: ${rice?.summary || 'unavailable — order by priority field'}. Sort by dependencies (unblocked first) -> priority -> points, allocate to sprints respecting capacity (default velocity ${a.default_velocity} points, ${a.sprint_duration_weeks}-week sprints; use velocity.average from ${a.sprints_path} when history exists). Write ${a.sprints_path} per sprint-schema.md (migrate the init template shape on first allocation).\nProject: ${a.project_dir}`,
    { agentType: 'shaktra-scrummaster', schema: S.PHASE_RESULT, label: 'allocate', phase: 'Sprint' },
  )
  observations = observations.concat(allocation?.observations || [])
  sprintSummary = allocation?.summary
  phaseSummaries.push({ name: 'Sprint planning', status: allocation?.status === 'complete' ? 'complete' : 'blocked', summary: sprintSummary })
}

if (a.mode === 'close-sprint') {
  phase('Sprint')
  const close = await agent(
    `Close the current sprint in ${a.sprints_path}: record partial velocity per sprint-schema.md formulas, move incomplete stories back to the backlog, advance to the next sprint if one is planned.\nProject: ${a.project_dir}\nStories: ${a.stories_dir}`,
    { agentType: 'shaktra-scrummaster', schema: S.PHASE_RESULT, label: 'close-sprint', phase: 'Sprint' },
  )
  if (!close || close.status !== 'complete') {
    return { status: 'blocked', phase: 'close-sprint', blockers: close?.blockers, observations }
  }
  observations = observations.concat(close.observations || [])
  sprintSummary = close.summary
  phaseSummaries.push({ name: 'Close sprint', status: 'complete', summary: close.summary })
}

// ---- Memory (mandatory) ----
phase('Memory')
const memory = await workflow(lib('memory'), {
  mode: 'capture',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  workflow_type: 'tpm',
  artifacts_path: a.stories_dir,
  handoff_path: null,
  observations,
})

const report = await workflow(lib('report'), {
  command: 'tpm',
  title: `TPM — ${a.mode}`,
  status: 'complete',
  phases: phaseSummaries,
  gates,
  findings: allFindings,
  metrics: {
    stories: stories.length || undefined,
    rice: riceSummary?.rice, coverage: riceSummary?.coverage, sprint: sprintSummary,
  },
  artifacts: stories.map((s) => s.path),
  memory,
  next_steps: a.mode === 'hotfix' && stories[0]
    ? [`Run /shaktra:dev "${stories[0].id}" to implement the hotfix`]
    : ['Start development: /shaktra:dev "<story-id>"'],
})

return {
  status: 'complete', mode: a.mode, stories, gates,
  findings: allFindings, observations, memory,
  rice: riceSummary, sprint: sprintSummary,
  report_markdown: report.markdown,
}
