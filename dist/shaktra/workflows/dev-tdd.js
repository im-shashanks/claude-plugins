export const meta = {
  name: 'shaktra-dev-tdd',
  description: 'Shaktra TDD pipeline: PLAN -> BRANCH -> RED -> GREEN -> QUALITY -> consistency -> memory',
  whenToUse: 'Invoked by the /shaktra:dev skill for develop/resume intents',
  phases: [
    { title: 'Briefing' }, { title: 'PLAN' }, { title: 'RED' },
    { title: 'GREEN' }, { title: 'QUALITY' }, { title: 'Memory' },
  ],
}
// Replaces skills/shaktra-dev/tdd-pipeline.md. Tier gate matrix (story-tiers.md):
//   RED skipped for trivial; plan review + comprehensive QUALITY for medium/large;
//   coverage threshold comes pre-resolved per tier via args.
//
// args (built by the SKILL from shaktra_context.py output):
// { plugin_root, project_dir, story_id, story_path, story_dir, handoff_path,
//   tier, coverage_threshold, p1_threshold, max_attempts,
//   completed_phases: [..], branch_exists: bool, briefing: object|null,
//   clarifications: {phase: answer}|null,
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = typeof args === 'string' ? JSON.parse(args) : args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))
const done = new Set(a.completed_phases || [])
const heavyTier = a.tier === 'medium' || a.tier === 'large'
const phases = []
const gates = []
let observations = []
let allFindings = []

const clarNote = a.clarifications && Object.keys(a.clarifications).length
  ? `\nUser clarifications from earlier escalations: ${JSON.stringify(a.clarifications)}`
  : ''
const base = `Project: ${a.project_dir}\nStory: ${a.story_path} (id ${a.story_id}, tier ${a.tier})\nHandoff: ${a.handoff_path}${clarNote}`

function escalate(phase, extra) {
  return {
    status: extra.clarification ? 'needs_clarification' : 'blocked',
    phase, ...extra, phases, gates,
    findings: allFindings, observations,
    briefing: typeof briefing === 'undefined' ? null : briefing,
  }
}

function absorb(result) {
  observations = observations.concat(result?.observations || [])
}

async function gate(name, opts) {
  const g = await workflow(lib('quality-loop'), {
    schemas: { QUALITY_VERDICT: S.QUALITY_VERDICT },
    gate: name,
    project_dir: a.project_dir,
    handoff_path: a.handoff_path,
    max_attempts: a.max_attempts,
    p1_threshold: a.p1_threshold,
    tier: a.tier,
    reviewer_type: 'shaktra:shaktra-sw-quality',
    context: `Story ${a.story_id} (${a.story_path})`,
    ...opts,
  })
  gates.push(g)
  allFindings = allFindings.concat(g.findings || [])
  observations = observations.concat(g.observations || [])
  return g
}

// ---- Briefing (memory retrieval) ----
phase('Briefing')
let briefing = a.briefing
if (!briefing) {
  briefing = await workflow(lib('memory'), {
    mode: 'briefing',
    project_dir: a.project_dir,
    memory_dir: a.memory.dir,
    retrieval_tier: a.memory.retrieval_tier,
    max_briefing_entries: a.memory.max_briefing_entries,
    confidence_threshold: a.memory.confidence_threshold,
    role_hint: `TDD pipeline for story ${a.story_id} (tier ${a.tier}). Story file: ${a.story_path}. Roles involved: sw-engineer (plan), test-agent (tests), developer (code), sw-quality (review).`,
  })
}
const briefingNote = `\nMemory briefing (apply these; sw-quality verifies consistency): ${JSON.stringify(briefing)}`

// ---- PLAN ----
if (!done.has('plan')) {
  phase('PLAN')
  const plan = await agent(
    `Create the unified implementation + test plan for this story.\n${base}${briefingNote}\nWrite implementation_plan.md to ${a.story_dir}/implementation_plan.md. Update the handoff with plan_summary, set current_phase: plan, and append "plan" to completed_phases. Trivial-tier stories get a minimal plan.`,
    { agentType: 'shaktra:shaktra-sw-engineer', schema: S.PHASE_RESULT, label: 'plan', phase: 'PLAN' },
  )
  if (!plan || plan.status !== 'complete') {
    return escalate('plan', { clarification: plan?.clarification, blockers: plan?.blockers, attempts: 1 })
  }
  absorb(plan)
  phases.push({ name: 'PLAN', status: 'complete', summary: plan.summary })

  if (heavyTier) {
    const g = await gate('plan', {
      review_mode: 'PLAN_REVIEW',
      artifact_paths: [`${a.story_dir}/implementation_plan.md`],
      creator_type: 'shaktra:shaktra-sw-engineer',
      phase_label: 'PLAN',
    })
    if (!g.passed) return escalate('plan', { gate: g, attempts: g.attempts })
  }
} else {
  phases.push({ name: 'PLAN', status: 'complete', summary: 'resumed — already complete' })
}

// ---- BRANCH ----
if (!a.branch_exists) {
  phase('PLAN')
  const branch = await agent(
    `Branch mode: create the feature branch for this story following the feat/fix/chore naming convention. Do not commit anything.\n${base}`,
    { agentType: 'shaktra:shaktra-developer', schema: S.PHASE_RESULT, label: 'branch', phase: 'PLAN' },
  )
  if (!branch || branch.status !== 'complete') {
    return escalate('branch', { clarification: branch?.clarification, blockers: branch?.blockers, attempts: 1 })
  }
  phases.push({ name: 'BRANCH', status: 'complete', summary: branch.summary })
}

// ---- RED ----
let testRun = null
if (a.tier !== 'trivial' && !done.has('tests')) {
  phase('RED')
  let attempt = 0
  while (attempt < Math.max(1, a.max_attempts)) {
    attempt++
    testRun = await agent(
      `RED phase: write failing tests per the implementation plan (${a.story_dir}/implementation_plan.md).\n${base}\nRun the suite and verify every test fails for a VALID red reason (missing implementation: ImportError/AttributeError/NotImplementedError or equivalents). Invalid reasons (SyntaxError/TypeError/NameError or equivalents) mean the test itself is broken — fix and re-run before returning. Update the handoff with test_summary, set current_phase: tests, append "tests" to completed_phases.${attempt > 1 ? ' Previous attempt did not reach a valid RED state — fix that now: ' + JSON.stringify(testRun?.failing_tests || testRun) : ''}`,
      { agentType: 'shaktra:shaktra-test-agent', schema: S.TEST_RUN_RESULT, label: `red#${attempt}`, phase: 'RED' },
    )
    absorb(testRun)
    const validRed = testRun && testRun.status === 'red'
      && testRun.failing_tests.length > 0
      && testRun.failing_tests.every((t) => t.valid_red)
    if (validRed) break
    if (attempt >= Math.max(1, a.max_attempts)) {
      return escalate('tests', { reason: 'tests_not_red', test_run: testRun, attempts: attempt })
    }
  }
  phases.push({ name: 'RED', status: 'complete', summary: `${testRun.test_count} failing tests, all valid-red` })

  const g = await gate('test', {
    review_mode: 'QUICK_CHECK',
    artifact_paths: testRun.test_files || [a.story_dir],
    creator_type: 'shaktra:shaktra-test-agent',
    phase_label: 'RED',
  })
  if (!g.passed) return escalate('tests', { gate: g, attempts: g.attempts })
} else {
  phases.push({ name: 'RED', status: a.tier === 'trivial' ? 'skipped' : 'complete', summary: a.tier === 'trivial' ? 'trivial tier' : 'resumed — already complete' })
}

// ---- GREEN ----
let codeRun = null
if (!done.has('code')) {
  phase('GREEN')
  let attempt = 0
  while (attempt < Math.max(1, a.max_attempts)) {
    attempt++
    codeRun = await agent(
      `GREEN phase (implement mode): make all tests pass following implementation_order from the plan (${a.story_dir}/implementation_plan.md).\n${base}${briefingNote}\nRun the full suite and the coverage tool. Coverage must reach ${a.coverage_threshold}% for this tier. Stage all changes — do not commit. Update the handoff with code_summary (all_tests_green, coverage, files_modified, deviations), set current_phase: code, append "code" to completed_phases.${attempt > 1 ? ' Previous attempt failed the green/coverage gate: ' + JSON.stringify({ status: codeRun?.status, coverage: codeRun?.coverage_pct }) : ''}`,
      { agentType: 'shaktra:shaktra-developer', schema: S.TEST_RUN_RESULT, label: `green#${attempt}`, phase: 'GREEN' },
    )
    absorb(codeRun)
    const green = codeRun && codeRun.status === 'green'
    const covered = codeRun && (codeRun.coverage_pct ?? 0) >= a.coverage_threshold
    if (green && covered) break
    if (attempt >= Math.max(1, a.max_attempts)) {
      return escalate('code', {
        reason: !green ? 'tests_not_green' : 'coverage_gate_failed',
        test_run: codeRun, attempts: attempt,
      })
    }
  }
  phases.push({ name: 'GREEN', status: 'complete', summary: `tests green, coverage ${codeRun.coverage_pct}% (threshold ${a.coverage_threshold}%)` })

  const g = await gate('code', {
    review_mode: 'QUICK_CHECK',
    artifact_paths: codeRun.test_files && codeRun.test_files.length ? codeRun.test_files : [a.project_dir],
    context: `Story ${a.story_id}. Review the files listed in code_summary.files_modified in ${a.handoff_path}.`,
    creator_type: 'shaktra:shaktra-developer',
    phase_label: 'GREEN',
  })
  if (!g.passed) return escalate('code', { gate: g, attempts: g.attempts })
} else {
  phases.push({ name: 'GREEN', status: 'complete', summary: 'resumed — already complete' })
}

// ---- QUALITY (comprehensive, medium/large only) ----
if (heavyTier && !done.has('quality')) {
  phase('QUALITY')
  const g = await gate('quality', {
    review_mode: 'COMPREHENSIVE',
    artifact_paths: [a.project_dir],
    context: `Story ${a.story_id}. Review all code and test files from this story (see handoff summaries in ${a.handoff_path}). ${a.tier === 'large' ? 'Large tier: expanded review — architecture impact, performance, dependency audit, cross-cutting concerns.' : ''}`,
    creator_type: 'shaktra:shaktra-developer',
    briefing,
    phase_label: 'QUALITY',
  })
  if (!g.passed) return escalate('quality', { gate: g, attempts: g.attempts })

  // Consistency gate: every briefing entry needs a consistency-check observation.
  const briefingIds = []
    .concat(briefing.relevant_principles || [], briefing.relevant_anti_patterns || [])
    .map((e) => e.id).filter(Boolean)
  let missing = briefingIds.filter((id) =>
    !observations.some((o) => o.type === 'consistency-check' && o.principle_id === id))
  for (let i = 0; i < 2 && missing.length; i++) {
    log(`Consistency gate: ${missing.length} briefing entr${missing.length > 1 ? 'ies' : 'y'} unverified — dispatching sw-quality`)
    const extra = await agent(
      `Consistency check pass. These memory briefing entries were never verified against the story's code: ${JSON.stringify(missing)}. Full briefing: ${JSON.stringify(briefing)}.\n${base}\nVerify each listed entry id against the implemented code and return one consistency-check observation per id (type: "consistency-check", principle_id: the entry id). You are read-only.`,
      { agentType: 'shaktra:shaktra-sw-quality', schema: S.QUALITY_VERDICT, label: `consistency#${i + 1}`, phase: 'QUALITY' },
    )
    observations = observations.concat(extra?.observations || [])
    missing = briefingIds.filter((id) =>
      !observations.some((o) => o.type === 'consistency-check' && o.principle_id === id))
  }
  gates.push({ gate: 'consistency', passed: missing.length === 0, reason: missing.length ? `unverified: ${missing.join(', ')}` : 'pass', attempts: 1 })
  phases.push({ name: 'QUALITY', status: 'complete' })
} else {
  phases.push({ name: 'QUALITY', status: heavyTier ? 'complete' : 'skipped', summary: heavyTier ? 'resumed — already complete' : `${a.tier} tier — code gate is final` })
}

// ---- MEMORY (mandatory, all tiers) ----
phase('Memory')
const memory = await workflow(lib('memory'), {
  mode: 'capture',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  workflow_type: 'tdd',
  artifacts_path: a.story_dir,
  handoff_path: a.handoff_path,
  observations,
})
phases.push({ name: 'MEMORY', status: 'complete', summary: memory.captured ? `${memory.promoted.length} promoted` : 'nothing met the capture bar' })

const report = await workflow(lib('report'), {
  command: 'dev',
  title: `TDD pipeline — ${a.story_id}`,
  status: 'complete',
  phases, gates,
  findings: allFindings,
  metrics: {
    tier: a.tier,
    test_count: codeRun?.test_count ?? testRun?.test_count,
    coverage_pct: codeRun?.coverage_pct,
    coverage_threshold: a.coverage_threshold,
  },
  artifacts: codeRun?.test_files || [],
  memory,
  next_steps: ['Review staged changes and commit', 'Run /shaktra:review before opening a PR'],
})

return {
  status: 'complete',
  phases, gates,
  findings: allFindings,
  observations,
  briefing,
  completed_phases: ['plan'].concat(a.tier !== 'trivial' ? ['tests'] : [], ['code'], heavyTier ? ['quality'] : []),
  memory,
  metrics: { coverage_pct: codeRun?.coverage_pct, test_count: codeRun?.test_count ?? testRun?.test_count },
  report_markdown: report.markdown,
}
