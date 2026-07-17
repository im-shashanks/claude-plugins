export const meta = {
  name: 'shaktra-refactor',
  description: 'Shaktra refactoring pipeline: ASSESS -> FORTIFY -> TRANSFORM -> VERIFY -> memory',
  whenToUse: 'Invoked by the /shaktra:dev skill for refactor intent',
  phases: [
    { title: 'ASSESS' }, { title: 'FORTIFY' }, { title: 'TRANSFORM' },
    { title: 'VERIFY' }, { title: 'Memory' },
  ],
}
// Replaces skills/shaktra-dev/refactoring-pipeline.md. No story required.
// Tier: 'targeted' (<5 files) | 'structural' (5+ files) — SKILL classifies.
//
// args = { plugin_root, project_dir, target, tier, handoff_path,
//   safety_threshold,            // per tier from settings.refactoring
//   max_characterization_tests, p1_threshold, max_attempts,
//   force_mode: bool,            // user accepted coverage risk (re-invocation)
//   approved_transforms: [id]|null,  // force mode: user-approved subset
//   completed_phases: [..],
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = typeof args === 'string' ? JSON.parse(args) : args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))
const done = new Set(a.completed_phases || [])
const phases = []
const gates = []
let observations = []
let allFindings = []
const base = `Project: ${a.project_dir}\nRefactoring target: ${a.target} (tier ${a.tier})\nHandoff: ${a.handoff_path}`

function escalate(phaseName, extra) {
  return {
    status: extra.clarification ? 'needs_clarification' : 'blocked',
    phase: phaseName, ...extra, phases, gates,
    findings: allFindings, observations,
  }
}
const absorb = (r) => { observations = observations.concat(r?.observations || []) }

// ---- ASSESS ----
let assessment = null
if (!done.has('assess')) {
  phase('ASSESS')
  assessment = await agent(
    `Refactoring-plan mode: assess the target for code smells using refactoring-smells.md. For each smell record id, location, severity; propose a transformation from refactoring-transforms.md; order transforms by risk (lowest first). Measure baseline metrics (test count, coverage, files in scope). Write the assessment (smells_detected, proposed_transforms, baseline_metrics) into ${a.handoff_path}, set current_phase: assess, append "assess" to completed_phases.\n${base}\nSummarize smells and transforms in your summary field; list transform ids in artifacts.`,
    { agentType: 'shaktra:shaktra-sw-engineer', schema: S.PHASE_RESULT, label: 'assess', phase: 'ASSESS' },
  )
  if (!assessment || assessment.status !== 'complete') {
    return escalate('assess', { clarification: assessment?.clarification, blockers: assessment?.blockers, attempts: 1 })
  }
  absorb(assessment)
  if (!assessment.artifacts || !assessment.artifacts.length) {
    return { status: 'complete', phases: [{ name: 'ASSESS', status: 'complete', summary: 'no smells detected — nothing to refactor' }], gates, findings: [], observations, report_markdown: `## Refactoring — ${a.target}\n\nNo smells detected; nothing to do.` }
  }
  phases.push({ name: 'ASSESS', status: 'complete', summary: assessment.summary })
} else {
  phases.push({ name: 'ASSESS', status: 'complete', summary: 'resumed — already complete' })
}

// ---- FORTIFY ----
if (!done.has('fortify')) {
  phase('FORTIFY')
  const fortify = await agent(
    `Characterization mode: run the existing tests and measure coverage for the target files. If coverage < ${a.safety_threshold}%, write characterization tests (capture CURRENT behavior — public API, boundaries, side effects; max ${a.max_characterization_tests}). Re-run and re-measure. Update ${a.handoff_path} with the fortify summary (coverage before/after, tests added, safety_threshold_met), set current_phase: fortify, append "fortify" to completed_phases.\n${base}\nIn your final message: status "complete" if coverage >= ${a.safety_threshold}%, else status "blocked" with the achieved coverage in blockers.`,
    { agentType: 'shaktra:shaktra-test-agent', schema: S.PHASE_RESULT, label: 'fortify', phase: 'FORTIFY' },
  )
  absorb(fortify)
  if (!fortify || (fortify.status !== 'complete' && !a.force_mode)) {
    // SKILL offers force mode to the user, then re-invokes with force_mode: true.
    return escalate('fortify', { reason: 'safety_threshold_not_met', blockers: fortify?.blockers, offer_force_mode: true, attempts: 1 })
  }
  phases.push({ name: 'FORTIFY', status: 'complete', summary: fortify.status === 'complete' ? fortify.summary : 'force mode — user accepted coverage risk' })
} else {
  phases.push({ name: 'FORTIFY', status: 'complete', summary: 'resumed — already complete' })
}

// ---- TRANSFORM ----
if (!done.has('transform')) {
  phase('TRANSFORM')
  const scope = a.approved_transforms && a.approved_transforms.length
    ? `Apply ONLY these user-approved transforms: ${a.approved_transforms.join(', ')}.`
    : 'Apply every proposed transform from the assessment in order.'
  const transform = await agent(
    `Refactor mode: ${scope} Atomic protocol per transform: (1) verify all tests pass, (2) apply ONE transformation per refactoring-transforms.md, (3) run all tests, (4) pass -> log "applied" in the handoff transforms list; fail -> REVERT the files (git checkout), verify tests pass again, log "reverted" with the reason. Never batch transforms. Update ${a.handoff_path}: set current_phase: transform, append "transform" to completed_phases.\n${base}\nSummarize applied/reverted counts; status "blocked" only if NO transform could be applied.`,
    { agentType: 'shaktra:shaktra-developer', schema: S.PHASE_RESULT, label: 'transform', phase: 'TRANSFORM' },
  )
  absorb(transform)
  if (!transform || transform.status === 'blocked') {
    return escalate('transform', { reason: 'all_transforms_reverted', blockers: transform?.blockers, attempts: 1 })
  }
  phases.push({ name: 'TRANSFORM', status: 'complete', summary: transform.summary })
} else {
  phases.push({ name: 'TRANSFORM', status: 'complete', summary: 'resumed — already complete' })
}

// ---- VERIFY ----
phase('VERIFY')
const verifyGate = await workflow(lib('quality-loop'), {
  schemas: { QUALITY_VERDICT: S.QUALITY_VERDICT },
  gate: 'refactor',
  review_mode: a.tier === 'structural' ? 'COMPREHENSIVE' : 'QUICK_CHECK',
  artifact_paths: [a.target],
  reviewer_type: 'shaktra:shaktra-sw-quality',
  creator_type: 'shaktra:shaktra-developer',
  context: `REFACTOR_VERIFY for ${a.target}: (1) full suite passes, (2) coverage >= baseline in ${a.handoff_path}, (3) no new P0/P1, (4) smell count reduced vs assessment, (5) metrics improved or neutral.${a.tier === 'structural' ? ' Structural tier: also verify architecture boundaries, no new circular dependencies, naming consistency.' : ''} A behavior regression or coverage decrease is a P0 finding.`,
  project_dir: a.project_dir,
  handoff_path: a.handoff_path,
  max_attempts: a.max_attempts,
  p1_threshold: a.p1_threshold,
  tier: a.tier,
  phase_label: 'VERIFY',
})
gates.push(verifyGate)
allFindings = allFindings.concat(verifyGate.findings || [])
observations = observations.concat(verifyGate.observations || [])
if (!verifyGate.passed) return escalate('verify', { gate: verifyGate, attempts: verifyGate.attempts })
phases.push({ name: 'VERIFY', status: 'complete' })

// ---- MEMORY ----
phase('Memory')
const memory = await workflow(lib('memory'), {
  mode: 'capture',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  workflow_type: 'refactor',
  artifacts_path: a.target,
  handoff_path: a.handoff_path,
  observations,
})
phases.push({ name: 'MEMORY', status: 'complete', summary: memory.captured ? `${memory.promoted.length} promoted` : 'nothing met the capture bar' })

const report = await workflow(lib('report'), {
  command: 'dev',
  title: `Refactoring — ${a.target}`,
  status: 'complete',
  phases, gates,
  findings: allFindings,
  metrics: { tier: a.tier, safety_threshold: a.safety_threshold },
  artifacts: [a.target],
  memory,
  next_steps: ['Review changes and commit'],
})

return { status: 'complete', phases, gates, findings: allFindings, observations, memory, report_markdown: report.markdown }
