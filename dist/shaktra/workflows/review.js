export const meta = {
  name: 'shaktra-review',
  description: 'App-level code review: parallel dimension analysis, independent verification, merge gate',
  whenToUse: 'Invoked by the /shaktra:review skill for story-review and pr-review',
  phases: [{ title: 'Analyze' }, { title: 'Verify' }, { title: 'Memory' }],
}
// Replaces the prose orchestration in skills/shaktra-review/SKILL.md.
// Findings are in-band; nothing writes .quality.yml. Analyzer agents are
// read-only fan-out — only the SKILL persists results afterwards.
//
// args = { plugin_root, project_dir, mode: 'story-review'|'pr-review',
//   story_id, story_dir, handoff_path,     // story mode (null for storyless PRs)
//   pr_number,                             // pr mode
//   files_modified: [..], test_files: [..],
//   p1_threshold, min_verification_tests, verification_persistence,
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = typeof args === 'string' ? JSON.parse(args) : args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))
const subject = a.mode === 'pr-review' ? `PR #${a.pr_number}` : `story ${a.story_id}`

// Dimension groups from review-dimensions.md — 13 dimensions across 4 analyzers.
const GROUPS = [
  { name: 'Correctness & Safety', dims: 'A (Contract & API), B (Failure Modes), C (Data Integrity), D (Concurrency)' },
  { name: 'Security & Ops', dims: 'E (Security), F (Observability), K (Configuration)' },
  { name: 'Reliability & Scale', dims: 'G (Performance), I (Testing), L (Dependencies)' },
  { name: 'Evolution', dims: 'H (Maintainability), J (Deployment), M (Compatibility)' },
]

phase('Analyze')
const briefing = await workflow(lib('memory'), {
  mode: 'briefing',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  retrieval_tier: a.memory.retrieval_tier,
  max_briefing_entries: a.memory.max_briefing_entries,
  confidence_threshold: a.memory.confidence_threshold,
  role_hint: `App-level code review of ${subject}. Changed files: ${(a.files_modified || []).join(', ')}. Role: cr-analyzer.`,
})

const context = a.mode === 'pr-review'
  ? `PR #${a.pr_number} — use \`gh pr view ${a.pr_number}\` and \`gh pr diff ${a.pr_number}\` for metadata and the diff; review the diff in the context of the FULL surrounding files.`
  : `Story ${a.story_id} — story dir ${a.story_dir}, handoff ${a.handoff_path}.`

const groupResults = await parallel(GROUPS.map((g) => () =>
  agent(
    `App-level review of ${subject} — dimension group "${g.name}": dimensions ${g.dims}.
Project: ${a.project_dir}
${context}
Modified files: ${(a.files_modified || []).join(', ') || 'derive from the diff/handoff'}
Test files: ${(a.test_files || []).join(', ') || 'derive from the project'}
Memory briefing: ${JSON.stringify(briefing)}
Apply the app-level focus questions and checklists from review-dimensions.md for exactly your assigned dimensions. Review changed code in the context of surrounding application code (imports, callers, shared modules). Evidence for every claim. You are read-only. List each assigned dimension in checked_dimensions with your findings carrying that dimension letter.`,
    { agentType: 'shaktra:shaktra-cr-analyzer', schema: S.QUALITY_VERDICT, label: `dims:${g.name}`, phase: 'Analyze' },
  )))

// Dedup across analyzers: same (file, line) keeps the higher severity.
const rank = { P0: 0, P1: 1, P2: 2, P3: 3 }
const byKey = new Map()
let observations = []
for (const r of groupResults.filter(Boolean)) {
  observations = observations.concat(r.observations || [])
  for (const f of r.findings || []) {
    const key = f.file && f.line != null ? `${f.file}:${f.line}` : `${f.dimension}:${f.issue}`
    const prev = byKey.get(key)
    if (!prev || rank[f.severity] < rank[prev.severity]) byKey.set(key, { ...f, gate: 'review' })
  }
}
let findings = [...byKey.values()]

// Independent verification testing — scenarios DIFFERENT from the dev's suite.
phase('Verify')
const verification = await agent(
  `Independent verification testing for ${subject}.
Project: ${a.project_dir}
${context}
Write and RUN at least ${a.min_verification_tests} tests that are fundamentally different from the existing suite — one or more per category: (1) core behavior from an external perspective (from the spec, not the implementation), (2) error handling at system boundaries (timeouts, malformed responses, connection drops, auth failures), (3) edge cases from the review-dimensions.md matrix (>=3 categories), (4) security boundary probing (injection, privilege escalation, data leakage via errors), (5) integration point stress (slow/unavailable/unexpected upstream and downstream).
Every failing verification test is a P1 finding (behavior claim without evidence). Test persistence policy: "${a.verification_persistence}" — for "always" keep the test files in the project suite; for "never" delete them after running; for "auto" keep only tests covering previously-untested risk areas; for "ask" keep them in place and report their paths so the orchestrator can ask the user.
Report each test in verification_tests (name, result, detail) and failures as findings.`,
  { agentType: 'shaktra:shaktra-cr-analyzer', schema: S.REVIEW_VERDICT, label: 'verification', phase: 'Verify' },
)
const verificationTests = verification?.verification_tests || []
findings = findings.concat((verification?.findings || []).map((f) => ({ ...f, gate: 'review' })))

// Independent verification is the distinguishing gate of app-level review — it
// must actually have run. If fewer than the required tests were produced, the
// review cannot cleanly APPROVE regardless of finding counts (the reviewer may
// have under-delivered, timed out, or silently failed).
const verificationShortfall = verificationTests.length < a.min_verification_tests
if (verificationShortfall) {
  findings.push({
    id: 'REV-VERIFY-GAP', severity: 'P1', dimension: 'I', gate: 'review',
    issue: `Independent verification incomplete: ${verificationTests.length} of the required ${a.min_verification_tests} verification tests were produced.`,
    recommendation: 'Re-run review so the independent verification suite is generated and executed.',
    resolved: false,
  })
}

// Merge gate (verdict ladder from severity-taxonomy.md).
const count = (sev) => findings.filter((f) => f.severity === sev && !f.resolved).length
const p0 = count('P0'); const p1 = count('P1'); const p2 = count('P2')
const verdict = p0 > 0 ? 'BLOCKED'
  : p1 > a.p1_threshold ? 'CHANGES_REQUESTED'
    : (p1 > 0 || p2 > 0) ? 'APPROVED_WITH_NOTES' : 'APPROVED'

// Memory capture — story-linked reviews only.
let memory = null
if (a.story_dir) {
  phase('Memory')
  memory = await workflow(lib('memory'), {
    mode: 'capture',
    project_dir: a.project_dir,
    memory_dir: a.memory.dir,
    workflow_type: 'review',
    artifacts_path: a.story_dir,
    handoff_path: a.handoff_path,
    observations,
  })
}

const report = await workflow(lib('report'), {
  command: 'review',
  title: `Code review — ${subject}`,
  status: verdict === 'BLOCKED' ? 'blocked' : 'complete',
  phases: [
    { name: 'Dimension analysis', status: 'complete', summary: `${GROUPS.length} analyzer groups, 13 dimensions` },
    { name: 'Independent verification', status: 'complete', summary: `${verificationTests.length} tests, ${verificationTests.filter((t) => t.result === 'fail').length} failed` },
  ],
  gates: [{ gate: 'merge', passed: p0 === 0 && p1 <= a.p1_threshold, reason: verdict, attempts: 1 }],
  findings,
  metrics: {
    verdict,
    verification_tests: verificationTests.length,
    verification_failures: verificationTests.filter((t) => t.result === 'fail').length,
    plan_adherence: verification?.plan_adherence,
  },
  artifacts: [],
  memory,
  next_steps: verdict === 'APPROVED' ? ['Merge when ready']
    : verdict === 'BLOCKED' ? ['Resolve every P0, then re-run /shaktra:review']
      : ['Address P1 findings, then re-run /shaktra:review'],
})

return {
  status: 'complete',
  verdict,
  findings,
  observations,
  verification_tests: verificationTests,
  verification_persistence: a.verification_persistence,
  memory,
  report_markdown: report.markdown,
}
