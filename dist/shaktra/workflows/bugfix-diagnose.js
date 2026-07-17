export const meta = {
  name: 'shaktra-bugfix-diagnose',
  description: 'Bug diagnosis: root-cause investigation producing a diagnosis artifact + bug_fix story',
  whenToUse: 'Invoked by the /shaktra:bugfix skill; the fix itself runs through /shaktra:dev afterwards',
  phases: [{ title: 'Diagnose' }],
}
// Replaces the diagnosis orchestration in skills/shaktra-bugfix/SKILL.md.
// Story-always-required: the diagnosis synthesizes a bug_fix story, then the
// SKILL chains to Skill(shaktra-dev) so the whole TDD pipeline runs unchanged.
//
// args = { plugin_root, project_dir,
//   bug_description, error_context,     // error_context may be null
//   stories_dir,
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = typeof args === 'string' ? JSON.parse(args) : args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))

phase('Diagnose')
const briefing = await workflow(lib('memory'), {
  mode: 'briefing',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  retrieval_tier: a.memory.retrieval_tier,
  max_briefing_entries: a.memory.max_briefing_entries,
  confidence_threshold: a.memory.confidence_threshold,
  role_hint: `Bug diagnosis. Symptom: ${a.bug_description}. Role: bug-diagnostician (anti-patterns and known failure modes are especially relevant).`,
})

const diagnosis = await agent(
  `Investigate this bug using the 5-step diagnosis methodology.
Bug description: ${a.bug_description}
Error context: ${a.error_context || 'none provided'}
Project: ${a.project_dir}
Memory briefing: ${JSON.stringify(briefing)}
Produce: (1) the diagnosis artifact at ${a.stories_dir}/diagnosis-<bug-id>.yml; (2) a story draft with scope: bug_fix at ${a.stories_dir}/ST-<NNN>.yml (next sequential id) whose test_specs include the reproduction test that must fail before the fix; set story_path in your result. Report root cause with evidence, the fix approach, affected files, confidence, and — if the same defect pattern exists elsewhere — list each blast-radius location as an observation (type "blast-radius", text describing file and needed change).
If you cannot reproduce or establish a root cause, set confidence "low" and describe what you attempted in evidence — never invent a root cause.`,
  { agentType: 'shaktra:shaktra-bug-diagnostician', schema: S.DIAGNOSIS_RESULT, label: 'diagnose', phase: 'Diagnose' },
)

if (!diagnosis) {
  return { status: 'blocked', phase: 'diagnose', reason: 'diagnostician_error', observations: [] }
}
if (diagnosis.confidence === 'low' || !diagnosis.story_path) {
  return {
    status: 'blocked', phase: 'diagnose', reason: 'diagnosis_inconclusive',
    diagnosis, observations: [],
    clarification: 'Diagnosis is inconclusive — additional context, environment details, or reproduction steps are needed before remediation.',
  }
}

const observations = [{ type: 'diagnosis', text: `Root cause: ${diagnosis.root_cause}. Fix approach: ${diagnosis.fix_approach}.`, files: diagnosis.affected_files }]

const report = await workflow(lib('report'), {
  command: 'bugfix',
  title: `Bug diagnosis — ${a.bug_description.slice(0, 80)}`,
  status: 'complete',
  phases: [{ name: 'Diagnosis', status: 'complete', summary: diagnosis.root_cause }],
  gates: [],
  findings: [],
  metrics: { confidence: diagnosis.confidence, affected_files: diagnosis.affected_files.length },
  artifacts: [diagnosis.story_path],
  memory: null,
  next_steps: [`Remediate via the TDD pipeline: /shaktra:dev "develop story <id from ${diagnosis.story_path}>"`],
})

return {
  status: 'complete',
  diagnosis,
  story_path: diagnosis.story_path,
  observations,
  report_markdown: report.markdown,
}
