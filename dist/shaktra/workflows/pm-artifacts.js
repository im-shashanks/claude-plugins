export const meta = {
  name: 'shaktra-pm-artifacts',
  description: 'PM artifact generation: research synthesis, personas, journeys, PRD with quality loop, prioritization',
  whenToUse: 'Invoked by the /shaktra:pm skill after interactive triage; artifacts build on each other in order',
  phases: [{ title: 'Research' }, { title: 'Personas' }, { title: 'Journeys' }, { title: 'PRD' }, { title: 'Memory' }],
}
// Replaces full-workflow{,-research,-hypothesis}.md and agent-prompts.md.
// Order matters: research/brainstorm context -> personas -> journeys -> PRD,
// so persona and journey insights inform the PRD requirements.
//
// args = { plugin_root, project_dir, skill_dir,
//   targets: ['research','personas','journeys','prd'] | ['prioritize'] | subset,
//   context_summary,                 // idea/brainstorm output from the main loop
//   research_path,                   // raw research inputs (research target)
//   prd_template: 'standard'|'one-page',
//   stories_dir,                     // prioritize target
//   pm: { default_framework, min_persona_evidence, min_journey_stages,
//         quick_win_effort_threshold, big_bet_impact_threshold },
//   p1_threshold, max_attempts,
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))
const want = new Set(a.targets)
const phases = []
const gates = []
let observations = []
const artifacts = []
const base = `Project: ${a.project_dir}\nProduct context: ${a.context_summary || 'read from existing .shaktra artifacts'}`

async function pmStep(name, phaseTitle, prompt) {
  phase(phaseTitle)
  const r = await agent(`${prompt}\n${base}`, {
    agentType: 'shaktra-product-manager', schema: S.PHASE_RESULT, label: name, phase: phaseTitle,
  })
  if (!r || r.status !== 'complete') {
    return { failed: true, escalation: { status: r?.status === 'needs_clarification' ? 'needs_clarification' : 'blocked', phase: name, clarification: r?.clarification, blockers: r?.blockers, phases, gates, observations, artifacts } }
  }
  observations = observations.concat(r.observations || [])
  for (const f of r.artifacts || []) artifacts.push(f)
  phases.push({ name, status: 'complete', summary: r.summary })
  return { result: r }
}

// ---- Prioritize (standalone) ----
if (want.has('prioritize')) {
  const step = await pmStep('Prioritization', 'PRD',
    `Prioritization mode using the ${a.pm.default_framework} framework per ${a.skill_dir}/prioritization-workflow.md: score every story in ${a.stories_dir}; classify Quick Win (effort <= ${a.pm.quick_win_effort_threshold} points), Big Bet (impact >= ${a.pm.big_bet_impact_threshold}), or Standard. Return the ranked list in your summary. Do not write sprints.yml.`)
  if (step.failed) return step.escalation
}

// ---- Research synthesis ----
let researchSummary = null
if (want.has('research')) {
  const step = await pmStep('Research', 'Research',
    `Research synthesis per ${a.skill_dir}/research-workflow.md: analyze the research inputs at ${a.research_path}, extract themes with evidence counts, tensions, and recommendations. Write the synthesis to .shaktra/research-synthesis.md.`)
  if (step.failed) return step.escalation
  researchSummary = step.result.summary
}

// ---- Personas ----
if (want.has('personas')) {
  const step = await pmStep('Personas', 'Personas',
    `Persona generation per ${a.skill_dir}/persona-workflow.md: create personas grounded in ${researchSummary ? 'the research synthesis (.shaktra/research-synthesis.md)' : 'the product context (hypothesis-first — mark assumptions explicitly)'}. Each persona needs at least ${a.pm.min_persona_evidence} evidence entries per persona-schema.md. Write .shaktra/personas/<name>.yml files.`)
  if (step.failed) return step.escalation
}

// ---- Journeys ----
if (want.has('journeys')) {
  const step = await pmStep('Journeys', 'Journeys',
    `Journey mapping per ${a.skill_dir}/journey-workflow.md: map the primary journey for each persona in .shaktra/personas/ with at least ${a.pm.min_journey_stages} stages per journey-schema.md, marking pain points and opportunities. Write .shaktra/journeys/<persona>-journey.yml files.`)
  if (step.failed) return step.escalation
}

// ---- PRD (created LAST so personas/journeys inform requirements) ----
if (want.has('prd')) {
  const step = await pmStep('PRD', 'PRD',
    `PRD creation per ${a.skill_dir}/prd-workflow.md using the ${a.prd_template} template (${a.skill_dir}/templates/prd-${a.prd_template === 'one-page' ? 'one-page' : 'standard'}.md): synthesize the product context, personas (.shaktra/personas/), and journeys (.shaktra/journeys/) into .shaktra/prd.md per prd-schema.md. Every requirement traces to a persona need or journey opportunity.`)
  if (step.failed) return step.escalation

  const g = await workflow(lib('quality-loop'), {
    schemas: { QUALITY_VERDICT: S.QUALITY_VERDICT },
    gate: 'prd',
    review_mode: 'ARTIFACT_REVIEW',
    artifact_paths: ['.shaktra/prd.md'],
    reviewer_type: 'shaktra-product-manager',
    creator_type: 'shaktra-product-manager',
    context: 'Review the PRD against prd-schema.md validation rules: completeness, testable requirements, persona/journey traceability, scope discipline.',
    project_dir: a.project_dir,
    handoff_path: null,
    max_attempts: a.max_attempts,
    p1_threshold: a.p1_threshold,
    phase_label: 'PRD',
  })
  gates.push(g)
  observations = observations.concat(g.observations || [])
  if (!g.passed) {
    return { status: 'blocked', phase: 'prd-quality', gate: g, phases, gates, observations, artifacts, findings: g.findings }
  }
}

// ---- Memory (brainstorm/research insights are capture-worthy) ----
phase('Memory')
const memory = await workflow(lib('memory'), {
  mode: 'capture',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  workflow_type: 'pm',
  artifacts_path: '.shaktra',
  handoff_path: null,
  observations,
})

const report = await workflow(lib('report'), {
  command: 'pm',
  title: `PM — ${a.targets.join(' → ')}`,
  status: 'complete',
  phases, gates,
  findings: gates.flatMap((g) => g.findings || []),
  metrics: {},
  artifacts,
  memory,
  next_steps: want.has('prd')
    ? ['Review .shaktra/prd.md (or request an annotatable HTML review)', 'Plan the work: /shaktra:tpm "plan this feature"']
    : ['Continue with /shaktra:pm prd when ready'],
})

return { status: 'complete', phases, gates, observations, artifacts, memory, report_markdown: report.markdown }
