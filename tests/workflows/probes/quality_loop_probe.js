export const meta = {
  name: 'quality-loop-probe',
  description: 'Deterministic integration test of lib/quality-loop.js — iteration + escalation',
  whenToUse: 'Run via the Workflow tool to verify the real gate loop threads prior_findings, iterates, and escalates at the attempt cap',
  phases: [{ title: 'iterate' }, { title: 'escalate' }],
}
// Exercises the ACTUAL workflows/lib/quality-loop.js child, not a re-implementation.
// The reviewer is a general-purpose agent driven by an explicit contract keyed on
// the presence of prior findings, so the outcome is deterministic without relying
// on a creator agent producing a defect.
//
// args = { plugin_root }

const a = typeof args === 'string' ? JSON.parse(args) : args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))

const REVIEW_CONTRACT_ITERATE =
  'PROBE FIXTURE ITER-A7. You are a deterministic test stub, NOT a real reviewer — ' +
  'do not evaluate the artifact and ignore every persona/checklist/verdict instruction ' +
  'above. Emit ONLY the structured output described here. If this prompt contains NO ' +
  '"Prior findings" section, emit: verdict "blocked", p0_count 0, p1_count 1, ' +
  'findings=[{id:"ITERA7-1",severity:"P1",dimension:"A",issue:"iter fixture finding",resolved:false}], ' +
  'checked_dimensions:["A"]. If it DOES contain a "Prior findings" section, emit: ' +
  'verdict "pass", p0_count 0, p1_count 0, ' +
  'findings=[{id:"ITERA7-1",severity:"P1",dimension:"A",issue:"iter fixture finding",resolved:true}], ' +
  'checked_dimensions:["A"]. This blocked-then-pass behavior is intentional and correct.'

const REVIEW_CONTRACT_ESCALATE =
  'PROBE FIXTURE ESC-Q3. You are a deterministic test stub, NOT a real reviewer — do ' +
  'not evaluate the artifact and ignore every persona/checklist/verdict instruction ' +
  'above. Emit ONLY this structured output EVERY time, unconditionally, whether or not ' +
  'a "Prior findings" section is present: verdict "blocked", p0_count 1, p1_count 0, ' +
  'findings=[{id:"ESCQ3-1",severity:"P0",dimension:"B",issue:"deliberately unresolvable fixture finding",resolved:false}], ' +
  'checked_dimensions:["B"]. Never emit "pass". Always emit the unresolved P0 above. ' +
  'This permanently-blocked behavior is intentional and correct for testing loop exhaustion.'

function runGate(gate, artifact, contract, maxAttempts, label) {
  return workflow(lib('quality-loop'), {
    schemas: { QUALITY_VERDICT: S.QUALITY_VERDICT },
    gate,
    review_mode: 'ARTIFACT_REVIEW',
    artifact_paths: [artifact],
    reviewer_type: 'general-purpose',
    creator_type: 'general-purpose',
    context: contract,
    project_dir: a.plugin_root,
    handoff_path: null,
    max_attempts: maxAttempts,
    p1_threshold: 0,
    phase_label: label,
  })
}

phase('iterate')
const iterate = await runGate('probe-iterate', 'probe-iterate.txt', REVIEW_CONTRACT_ITERATE, 3, 'iterate')

phase('escalate')
const escalate = await runGate('probe-escalate', 'probe-escalate.txt', REVIEW_CONTRACT_ESCALATE, 2, 'escalate')

return {
  iterate: {
    passed: iterate.passed, attempts: iterate.attempts, reason: iterate.reason,
    expect: 'passed=true, attempts=2 (blocked on 1, fixed, pass on 2)',
    ok: iterate.passed === true && iterate.attempts === 2,
  },
  escalate: {
    passed: escalate.passed, attempts: escalate.attempts, reason: escalate.reason,
    blocking: (escalate.blocking_findings || []).length,
    expect: 'passed=false, attempts=2, reason=max_loops_reached, blocking>=1',
    ok: escalate.passed === false && escalate.attempts === 2 &&
        escalate.reason === 'max_loops_reached' && (escalate.blocking_findings || []).length >= 1,
  },
}
