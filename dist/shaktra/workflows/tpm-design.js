export const meta = {
  name: 'shaktra-tpm-design',
  description: 'TPM design workflow: architect gap analysis -> PM answers -> design doc -> quality loop',
  whenToUse: 'Invoked by the /shaktra:tpm skill for design (and the first half of full) intent',
  phases: [{ title: 'Design' }, { title: 'Quality gate' }, { title: 'Memory' }],
}
// Replaces the design portion of skills/shaktra-tpm/workflow-template.md.
// Gap flow: the architect reports gaps as blockers; the PM answers them from
// source docs; unanswerable gaps escalate to the user via needs_clarification.
//
// args = { plugin_root, project_dir, project_name,
//   prd_path, architecture_path, analysis_path,   // analysis_path may be null
//   design_path,                                  // .shaktra/designs/<name>-design.md
//   p1_threshold, max_attempts,
//   gap_answers: {question: answer}|null,         // user answers on re-invocation
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))
let observations = []
const base = `Project: ${a.project_dir}
PRD: ${a.prd_path}
Architecture: ${a.architecture_path}
Analysis: ${a.analysis_path || 'N/A — no codebase analysis available'}`

phase('Design')
let gapAnswers = a.gap_answers ? { ...a.gap_answers } : {}
let design = null
for (let round = 1; round <= 3; round++) {
  design = await agent(
    `Create (or revise) the design document for this project.
${base}
Gap answers so far: ${Object.keys(gapAnswers).length ? JSON.stringify(gapAnswers) : 'none — first pass'}
Follow your process: gather context, run gap analysis, then either write the design doc to ${a.design_path} (status "complete", per design-doc-schema.md) or — if requirement gaps block the design — return status "blocked" with each open question as one entry in blockers.`,
    { agentType: 'shaktra-architect', schema: S.PHASE_RESULT, label: `design#${round}`, phase: 'Design' },
  )
  if (!design) return { status: 'blocked', phase: 'design', reason: 'architect_error', observations }
  observations = observations.concat(design.observations || [])
  if (design.status === 'complete') break
  if (design.status === 'needs_clarification') {
    return { status: 'needs_clarification', phase: 'design', clarification: design.clarification, gap_answers: gapAnswers, observations }
  }
  const gaps = design.blockers || []
  if (!gaps.length || round === 3) {
    return { status: 'blocked', phase: 'design', blockers: gaps, gap_answers: gapAnswers, observations }
  }
  log(`Architect found ${gaps.length} gap(s) — dispatching product-manager`)
  const pm = await agent(
    `Gap answering mode. The architect needs these questions answered before the design can proceed:
${JSON.stringify(gaps)}
${base}
Search priority: PRD -> architecture doc -> .shaktra/memory/principles.yml -> anti-patterns.yml. Return status "complete" with a JSON object {question: answer} in your summary for everything you can ground in the sources. Any question that CANNOT be answered from the sources goes into blockers verbatim — never invent an answer.`,
    { agentType: 'shaktra-product-manager', schema: S.PHASE_RESULT, label: `gaps#${round}`, phase: 'Design' },
  )
  observations = observations.concat(pm?.observations || [])
  if (pm?.blockers?.length) {
    // PM escalation: the user must answer these.
    return {
      status: 'needs_clarification', phase: 'design',
      clarification: `The PM could not answer these design gaps from the PRD or architecture doc:\n- ${pm.blockers.join('\n- ')}`,
      unanswered_gaps: pm.blockers, gap_answers: gapAnswers, observations,
    }
  }
  try { Object.assign(gapAnswers, JSON.parse(pm.summary)) } catch { gapAnswers[`round-${round}`] = pm?.summary || '' }
}

phase('Quality gate')
const g = await workflow(lib('quality-loop'), {
  schemas: { QUALITY_VERDICT: S.QUALITY_VERDICT },
  gate: 'design',
  review_mode: 'DESIGN_REVIEW',
  artifact_paths: [a.design_path],
  reviewer_type: 'shaktra-tpm-quality',
  creator_type: 'shaktra-architect',
  context: `Design doc for ${a.project_name}. Review against the design review checklist and design-doc-schema.md. Source PRD: ${a.prd_path}.`,
  project_dir: a.project_dir,
  handoff_path: null,
  max_attempts: a.max_attempts,
  p1_threshold: a.p1_threshold,
  phase_label: 'Quality gate',
})
observations = observations.concat(g.observations || [])
if (!g.passed) {
  return { status: 'blocked', phase: 'design-quality', gate: g, gap_answers: gapAnswers, observations, findings: g.findings }
}

phase('Memory')
const memory = await workflow(lib('memory'), {
  mode: 'capture',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  workflow_type: 'tpm-design',
  artifacts_path: a.design_path,
  handoff_path: null,
  observations,
})

const report = await workflow(lib('report'), {
  command: 'tpm',
  title: `Design — ${a.project_name}`,
  status: 'complete',
  phases: [
    { name: 'Design doc', status: 'complete', summary: design.summary },
    { name: 'Quality gate', status: 'complete', attempts: g.attempts },
  ],
  gates: [g],
  findings: g.findings,
  artifacts: [a.design_path],
  memory,
  next_steps: [`Generate stories: /shaktra:tpm "create stories from design"`, 'Or request an annotatable HTML design review'],
})

return {
  status: 'complete', design_path: a.design_path, gap_answers: gapAnswers,
  findings: g.findings, observations, memory, report_markdown: report.markdown,
}
