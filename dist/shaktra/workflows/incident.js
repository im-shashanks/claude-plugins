export const meta = {
  name: 'shaktra-incident',
  description: 'Incident response: post-mortem analysis, detection gaps, runbook generation, memory capture',
  whenToUse: 'Invoked by the /shaktra:incident skill for post-mortem and runbook intents',
  phases: [{ title: 'Analysis' }, { title: 'Memory' }],
}
// Replaces the prose orchestration in skills/shaktra-incident/SKILL.md.
//
// args = { plugin_root, project_dir,
//   intent: 'post_mortem' | 'runbook' | 'detection_gap',
//   bug_id, diagnosis_path, story_path, handoff_path, incident_dir,
//   auto_detection_gap, runbook_auto_generate,   // settings.incident flags
//   incident_confidence_multiplier, action_item_default_priority,
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))

phase('Analysis')
const briefing = await workflow(lib('memory'), {
  mode: 'briefing',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  retrieval_tier: a.memory.retrieval_tier,
  max_briefing_entries: a.memory.max_briefing_entries,
  confidence_threshold: a.memory.confidence_threshold,
  role_hint: `Incident ${a.intent} for ${a.bug_id}. Diagnosis: ${a.diagnosis_path}. Role: incident-analyst.`,
})

const task = a.intent === 'runbook'
  ? `Generate the operational runbook for this incident. Follow runbook-template.md for section structure.`
  : a.intent === 'detection_gap'
    ? `Analyze detection gaps for this incident. Follow detection-gap-framework.md for the 4-step analysis (gate coverage matrix, test gaps, quality dimensions, recommendations).`
    : `Perform the post-mortem analysis. Follow postmortem-methodology.md for the 5-step analysis.${a.auto_detection_gap ? ' Then run detection-gap analysis per detection-gap-framework.md and write its artifact too.' : ''}${a.runbook_auto_generate ? ' Also generate the runbook per runbook-template.md.' : ''}`

const analysis = await agent(
  `${task}
Incident: ${a.bug_id}
Diagnosis: ${a.diagnosis_path}
Story: ${a.story_path}
Handoff: ${a.handoff_path}
Project: ${a.project_dir}
Memory briefing: ${JSON.stringify(briefing)}
Write all artifacts to ${a.incident_dir}/ following incident-schema.md. Default action-item priority: ${a.action_item_default_priority}. Return the timeline, root cause, contributing factors, detection gaps, action items, and artifact paths. Return non-routine insights as in-band observations — incident insights are high-value for anti-pattern detection.`,
  { agentType: 'shaktra-incident-analyst', schema: S.INCIDENT_ANALYSIS, label: a.intent, phase: 'Analysis' },
)
if (!analysis) {
  return { status: 'blocked', phase: 'analysis', reason: 'analyst_error', observations: [] }
}
const observations = [
  { type: 'incident', text: `Incident ${a.bug_id} root cause: ${analysis.root_cause}` },
  ...(analysis.detection_gaps || []).map((g) => ({ type: 'detection-gap', text: g })),
]

phase('Memory')
const memory = await workflow(lib('memory'), {
  mode: 'capture',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  workflow_type: 'incident',
  artifacts_path: a.incident_dir,
  handoff_path: null,
  observations: observations.map((o) => ({
    ...o,
    text: `${o.text} [incident-sourced: apply confidence multiplier ${a.incident_confidence_multiplier}]`,
  })),
})

const report = await workflow(lib('report'), {
  command: 'incident',
  title: `Incident ${a.intent.replace('_', '-')} — ${a.bug_id}`,
  status: 'complete',
  phases: [{ name: a.intent === 'runbook' ? 'Runbook' : 'Post-mortem', status: 'complete', summary: analysis.summary }],
  gates: [],
  findings: [],
  metrics: {
    root_cause: analysis.root_cause,
    detection_gaps: (analysis.detection_gaps || []).length,
    action_items: (analysis.action_items || []).length,
  },
  artifacts: analysis.artifacts || [],
  memory,
  next_steps: (analysis.action_items || []).slice(0, 5).map((i) => `[${i.priority}] ${i.description}`),
})

return {
  status: 'complete',
  analysis,
  detection_gaps_found: (analysis.detection_gaps || []).length > 0,
  observations, memory,
  report_markdown: report.markdown,
}
