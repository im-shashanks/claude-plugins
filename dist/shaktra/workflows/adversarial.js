export const meta = {
  name: 'shaktra-adversarial',
  description: 'Adversarial review: behavior contract, mutation testing, fault/input probes, score gate',
  whenToUse: 'Invoked by the /shaktra:adversarial-review skill for story and PR modes',
  phases: [{ title: 'Contract' }, { title: 'Mutation' }, { title: 'Probes' }, { title: 'Memory' }],
}
// Replaces skills/shaktra-adversarial-review/adversarial-dispatch.md and the
// SKILL's prose orchestration. Phase A (mutation) runs ALONE because it
// mutates source files; a git-status check gates Phase B (parallel probes).
//
// args = { plugin_root, project_dir, mode: 'story-adversarial'|'pr-adversarial',
//   story_id, story_dir, handoff_path, pr_number,
//   mutation_kill_threshold, mutation_timeout, max_mutations_per_function,
//   max_adversarial_tests, test_persistence, p1_threshold,
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = typeof args === 'string' ? JSON.parse(args) : args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))
const subject = a.mode === 'pr-adversarial' ? `PR #${a.pr_number}` : `story ${a.story_id}`
const source = a.mode === 'pr-adversarial'
  ? `PR #${a.pr_number} (use \`gh pr view\`/\`gh pr diff\` for the change set)`
  : `story ${a.story_id} (story dir ${a.story_dir}, handoff ${a.handoff_path})`

// ---- Behavior contract ----
phase('Contract')
const contract = await agent(
  `Build the behavior contract for adversarial review of ${subject}.
Project: ${a.project_dir}
Change source: ${source}
Extract: changed_functions (file, function, line range, modified|added), acceptance criteria, invariants with verifying tests, external dependencies (database/api/file_io/queue/cache), test_files, and a runnable test_command scoped to those files (framework from .shaktra/settings.yml project.test_framework). Return it as JSON in your summary field; list test_files in artifacts. Status "blocked" only if the change set cannot be determined.`,
  { agentType: 'shaktra:shaktra-adversary', schema: S.PHASE_RESULT, label: 'contract', phase: 'Contract' },
)
if (!contract || contract.status !== 'complete') {
  return { status: 'blocked', phase: 'contract', blockers: contract?.blockers, findings: [], observations: [] }
}
const testFiles = contract.artifacts || []
let observations = contract.observations || []
let findings = []

// Config/docs-only changes: nothing to attack.
if (contract.summary.includes('"changed_functions": []') || /no code changes/i.test(contract.summary)) {
  return {
    status: 'complete', verdict: 'pass', mutation_score: null, findings: [], observations,
    report_markdown: `## Adversarial review — ${subject}\n\nNo code changes detected (config/docs only). Verdict: PASS.`,
  }
}

// ---- Phase A: mutation testing (alone — it mutates source files) ----
phase('Mutation')
let mutation = null
if (testFiles.length) {
  mutation = await agent(
    `Mutation testing for ${subject}. Behavior contract: ${contract.summary}
Project: ${a.project_dir}
Follow mutation-strategy.md: for each changed function generate up to ${a.max_mutations_per_function} mutations, apply ONE at a time, run the contract's test_command (timeout ${a.mutation_timeout}s per run), record killed/survived, and RESTORE the original source after each mutation. When finished, verify with git status/diff that every source file is byte-identical to its pre-mutation state — restoring the working tree is mandatory. Score = killed / total * 100. Each surviving mutant means the tests missed a behavior — record it with why_survived.`,
    { agentType: 'shaktra:shaktra-adversary', schema: S.ADVERSARIAL_VERDICT, label: 'mutation', phase: 'Mutation' },
  )
  if (mutation) {
    findings = findings.concat((mutation.findings || []).map((f) => ({ ...f, gate: 'adversarial' })))
  }
  // Safety gate between phases: source tree must be clean of mutation leftovers.
  const clean = await agent(
    `Verify the working tree has no leftover mutations: run git status and git diff in ${a.project_dir}. If any source file still carries a mutation from mutation testing, restore it (git checkout -- <file>) and report what you restored. Status "complete" when the tree is verified clean of mutation artifacts, "blocked" if you cannot restore it.`,
    { agentType: 'shaktra:shaktra-adversary', schema: S.PHASE_RESULT, label: 'restore-check', phase: 'Mutation' },
  )
  if (!clean || clean.status !== 'complete') {
    return { status: 'blocked', phase: 'mutation', reason: 'source_tree_not_restored', blockers: clean?.blockers, findings, observations }
  }
} else {
  log('No test files in the contract — mutation analysis skipped (score N/A)')
}

// ---- Phase B: adversarial probes (parallel, read-only on source) ----
phase('Probes')
const probeShared = `Behavior contract: ${contract.summary}
Project: ${a.project_dir}
Cap generated tests at ${a.max_adversarial_tests}. Test persistence policy "${a.test_persistence}": "always" keep them in the suite, "never" delete after running, "auto" keep only tests exposing real gaps, "ask" keep in place and report paths. Do not modify production source files.`
const probes = await parallel([
  () => agent(
    `Input & boundary probing for ${subject}. Follow probe-strategies.md input/boundary sections: malformed inputs, boundary values, type confusion, injection payloads against the changed functions. RUN the probes as tests. ${probeShared}`,
    { agentType: 'shaktra:shaktra-adversary', schema: S.ADVERSARIAL_VERDICT, label: 'probes:input', phase: 'Probes' },
  ),
  () => agent(
    `Fault & resilience probing for ${subject}. Follow probe-strategies.md fault-injection sections: dependency failures, timeouts, partial writes, resource exhaustion, concurrent access against the contract's dependencies. RUN the probes as tests. ${probeShared}`,
    { agentType: 'shaktra:shaktra-adversary', schema: S.ADVERSARIAL_VERDICT, label: 'probes:fault', phase: 'Probes' },
  ),
])
let blindSpots = mutation?.blind_spots || []
for (const p of probes.filter(Boolean)) {
  findings = findings.concat((p.findings || []).map((f) => ({ ...f, gate: 'adversarial' })))
  blindSpots = blindSpots.concat(p.blind_spots || [])
}

// Dedup: same function + same behavioral gap keeps higher severity.
const rank = { P0: 0, P1: 1, P2: 2, P3: 3 }
const byKey = new Map()
for (const f of findings) {
  const key = `${f.file || ''}:${f.dimension}:${(f.issue || '').slice(0, 60)}`
  const prev = byKey.get(key)
  if (!prev || rank[f.severity] < rank[prev.severity]) byKey.set(key, f)
}
findings = [...byKey.values()]

// ---- Verdict ----
const count = (sev) => findings.filter((f) => f.severity === sev && !f.resolved).length
const p0 = count('P0'); const p1 = count('P1')
const score = mutation ? mutation.mutation_score : null
const verdict = p0 > 0 ? 'blocked'
  : (score != null && score < a.mutation_kill_threshold) || p1 > a.p1_threshold || blindSpots.length ? 'concern'
    : 'pass'

// ---- Memory (story-linked only) ----
let memory = null
if (a.story_dir) {
  phase('Memory')
  memory = await workflow(lib('memory'), {
    mode: 'capture',
    project_dir: a.project_dir,
    memory_dir: a.memory.dir,
    workflow_type: 'adversarial-review',
    artifacts_path: a.story_dir,
    handoff_path: a.handoff_path,
    observations,
  })
}

const report = await workflow(lib('report'), {
  command: 'adversarial-review',
  title: `Adversarial review — ${subject}`,
  status: verdict === 'blocked' ? 'blocked' : 'complete',
  phases: [
    { name: 'Behavior contract', status: 'complete', summary: contract.summary.slice(0, 200) },
    { name: 'Mutation testing', status: mutation ? 'complete' : 'skipped', summary: mutation ? `score ${score}% (threshold ${a.mutation_kill_threshold}%), ${(mutation.surviving_mutants || []).length} survivors` : 'no existing tests' },
    { name: 'Adversarial probes', status: 'complete', summary: `${probes.filter(Boolean).length}/2 probe agents completed` },
  ],
  gates: [{ gate: 'adversarial', passed: verdict === 'pass', reason: verdict, attempts: 1 }],
  findings,
  metrics: { verdict, mutation_score: score ?? 'N/A', blind_spots: blindSpots.length },
  artifacts: testFiles,
  memory,
  next_steps: verdict === 'pass' ? ['Proceed with confidence']
    : verdict === 'blocked' ? ['Fix P0 findings before merge']
      : ['Review surviving mutants and blind spots — merge with awareness'],
})

return {
  status: 'complete', verdict, mutation_score: score,
  surviving_mutants: mutation?.surviving_mutants || [],
  blind_spots: blindSpots, findings, observations, memory,
  test_persistence: a.test_persistence,
  report_markdown: report.markdown,
}
