export const meta = {
  name: 'shaktra-analyze',
  description: 'Codebase analysis: pre-analysis ground truth, 9 parallel dimensions, consolidation',
  whenToUse: 'Invoked by the /shaktra:analyze skill — the single analysis implementation',
  phases: [{ title: 'Pre-analysis' }, { title: 'Dimensions' }, { title: 'Consolidate' }, { title: 'Memory' }],
}
// THE analysis implementation — replaces deep-analysis-workflow.md (teams) and
// standard-analysis-workflow.md (subagent fallback). The consolidator agent
// preserves the cross-dimension correlation the teams path provided.
//
// args = { plugin_root, project_dir, analysis_dir, skill_dir,
//   mode: 'full' | 'targeted' | 'debt-strategy' | 'dependency-audit',
//   dimensions: ['D1'..'D9'],      // targeted/refresh subset; all 9 for full
//   stage1_complete: bool,          // static.yml + overview.yml already fresh
//   summary_token_budget,           // settings.analysis.summary_token_budget
//   memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold } }

const a = args
const lib = (name) => ({ scriptPath: `${a.plugin_root}/workflows/lib/${name}.js` })
const S = await workflow(lib('schemas'))

const DIMENSIONS = {
  D1: { name: 'Architecture & Structure', file: 'structure.yml', spec: 'analysis-dimensions-core.md' },
  D2: { name: 'Domain Model & Business Rules', file: 'domain-model.yml', spec: 'analysis-dimensions-core.md' },
  D3: { name: 'Entry Points & Interfaces', file: 'entry-points.yml', spec: 'analysis-dimensions-core.md' },
  D4: { name: 'Coding Practices & Conventions', file: 'practices.yml', spec: 'analysis-dimensions-core.md' },
  D5: { name: 'Dependencies & Tech Stack', file: 'dependencies.yml', spec: 'analysis-dimensions-health.md' },
  D6: { name: 'Technical Debt & Security', file: 'tech-debt.yml', spec: 'analysis-dimensions-health.md' },
  D7: { name: 'Data Flows & Integration', file: 'data-flows.yml', spec: 'analysis-dimensions-health.md' },
  D8: { name: 'Critical Paths & Risk', file: 'critical-paths.yml', spec: 'analysis-dimensions-health.md' },
  D9: { name: 'Git Intelligence', file: 'git-intelligence.yml', spec: 'analysis-dimensions-git.md' },
}

// ---- Special modes: debt strategy / dependency audit (single dispatch) ----
if (a.mode === 'debt-strategy' || a.mode === 'dependency-audit') {
  const cfg = a.mode === 'debt-strategy'
    ? { input: 'tech-debt.yml', guide: 'debt-strategy.md', out: 'debt-strategy.yml' }
    : { input: 'dependencies.yml', guide: 'dependency-audit.md', out: 'dependency-audit.yml' }
  const r = await agent(
    `${a.mode} mode. Read ${a.analysis_dir}/${cfg.input} and follow ${a.skill_dir}/${cfg.guide} for categorization, scoring, and story generation rules. Write ${a.analysis_dir}/${cfg.out} per its schema.\nProject: ${a.project_dir}`,
    { agentType: 'shaktra-cba-analyzer', schema: S.ANALYSIS_DIMENSION_RESULT, label: a.mode, phase: 'Dimensions' },
  )
  return {
    status: r && r.status === 'complete' ? 'complete' : 'blocked',
    mode: a.mode, artifact: `${a.analysis_dir}/${cfg.out}`, summary: r?.summary,
    findings: r?.findings || [], observations: [],
    report_markdown: `## Analysis — ${a.mode}\n\n${r?.summary || 'failed'}\n\nFeed generated stories into /shaktra:tpm for sprint planning.`,
  }
}

// ---- Stage 1: pre-analysis ground truth (factual extraction only) ----
phase('Pre-analysis')
if (!a.stage1_complete) {
  const stage1 = await agent(
    `Pre-analysis extraction (Stage 1) — FACTUAL extraction only, no interpretation. Using Glob/Grep/Bash on ${a.project_dir}:
(1) write ${a.analysis_dir}/static.yml: file inventory by language, dependency graph from import statements, call-graph skeleton, type hierarchy, detected structural patterns, config inventory;
(2) write ${a.analysis_dir}/overview.yml: project identity, repository structure, build system, tech stack, entry points — starting with a self-contained summary: section (~300 tokens);
(3) update ${a.analysis_dir}/manifest.yml stage_1 status per analysis-manifest-schema.md.
Every entry must come from actual tool output — never guess.`,
    { agentType: 'shaktra-cba-analyzer', schema: S.PHASE_RESULT, label: 'stage1', phase: 'Pre-analysis' },
  )
  if (!stage1 || stage1.status !== 'complete') {
    return { status: 'blocked', phase: 'stage1', blockers: stage1?.blockers, observations: [] }
  }
}

// ---- Stage 2: parallel dimension analysis ----
phase('Dimensions')
const requested = (a.dimensions && a.dimensions.length ? a.dimensions : Object.keys(DIMENSIONS))
  .filter((d) => DIMENSIONS[d])
const results = await parallel(requested.map((id) => () => {
  const d = DIMENSIONS[id]
  return agent(
    `Execute analysis dimension ${id}: ${d.name}.
INPUTS (read first): ${a.analysis_dir}/static.yml (ground truth), ${a.analysis_dir}/overview.yml, ${a.memory.dir}/principles.yml (if present).
SPECIFICATION: read ${a.skill_dir}/${d.spec}, find the ${id} section, follow its steps, evidence requirements, and output structure exactly.
OUTPUT: write ${a.analysis_dir}/${d.file} matching its schema in ${a.skill_dir}/analysis-output-schemas.md — the file MUST begin with a self-contained summary: section (budget ~${a.summary_token_budget} tokens). Then update ${a.analysis_dir}/manifest.yml for ${id} only.
RULES: analyze ALL files in static.yml's inventory across multiple directories; every finding cites file/line/pattern evidence you verified exists; code snippets are copied, never generated; report absence rather than guessing; actively hunt cross-file duplication and inconsistent handling of the same concern; canonical examples are 10-40 lines of real code; note dimension ${id} in your result.`,
    { agentType: 'shaktra-cba-analyzer', schema: S.ANALYSIS_DIMENSION_RESULT, label: id, phase: 'Dimensions' },
  )
}))
const dims = results.map((r, i) => ({ id: requested[i], ...(r || { status: 'error', summary: 'agent failed' }) }))
const failed = dims.filter((d) => d.status !== 'complete')
if (failed.length) log(`${failed.length} dimension(s) failed: ${failed.map((d) => d.id).join(', ')} — consolidation will validate and flag`)

// ---- Stage 3: consolidate (validation + cross-dimension correlation) ----
phase('Consolidate')
const consolidation = await agent(
  `Analysis consolidation (Stage 3) for ${a.project_dir}. Dimension results: ${JSON.stringify(dims.map((d) => ({ id: d.id, status: d.status, summary: (d.summary || '').slice(0, 300) })))}
(1) VALIDATE each completed artifact in ${a.analysis_dir}: parses as YAML; summary: is first key and substantive; required schema keys present (analysis-output-schemas.md); spot-check 5 file paths per artifact with Glob (>1 of 5 missing = hallucinated, mark failed); evidence density (no major section with zero citations). Mark failures in manifest.yml with error details.
(2) CROSS-DIMENSION CORRELATION: read tech-debt.yml, critical-paths.yml, git-intelligence.yml; compute composite risk per critical-path file (debt presence x coverage x change frequency x coupling) and append cross_cutting_risk under details: in critical-paths.yml. Note any cross-dimension insights (e.g. high-churn files with debt, unowned critical paths) as observations.
(3) CHECKSUMS: SHA256 of all analyzed source files -> ${a.analysis_dir}/checksum.yml with file->dimensions mapping.
(4) DIAGRAMS: generate a Mermaid module-dependency diagram from structure.yml into its diagrams: key.
(5) MANIFEST: set completed dimensions to complete, record timestamp and execution_mode: workflow.
(6) ARCHITECTURE: report structure.yml's detected patterns and consistency in your summary (detected style + consistency level) — the orchestrator decides settings updates.`,
  { agentType: 'shaktra-cba-analyzer', schema: S.PHASE_RESULT, label: 'consolidate', phase: 'Consolidate' },
)
let observations = consolidation?.observations || []

// ---- Memory ----
phase('Memory')
const memory = await workflow(lib('memory'), {
  mode: 'capture',
  project_dir: a.project_dir,
  memory_dir: a.memory.dir,
  workflow_type: 'analysis',
  artifacts_path: a.analysis_dir,
  handoff_path: null,
  observations,
})

const report = await workflow(lib('report'), {
  command: 'analyze',
  title: `Codebase analysis — ${a.mode}`,
  status: failed.length === requested.length ? 'blocked' : 'complete',
  phases: [
    { name: 'Pre-analysis', status: 'complete', summary: a.stage1_complete ? 'reused fresh ground truth' : 'static.yml + overview.yml extracted' },
    ...dims.map((d) => ({ name: `${d.id}: ${DIMENSIONS[d.id].name}`, status: d.status === 'complete' ? 'complete' : 'error', summary: (d.summary || '').slice(0, 160) })),
    { name: 'Consolidation', status: consolidation?.status === 'complete' ? 'complete' : 'error', summary: consolidation?.summary?.slice(0, 200) },
  ],
  gates: [],
  findings: dims.flatMap((d) => d.findings || []),
  metrics: { dimensions_run: requested.length, dimensions_failed: failed.length },
  artifacts: requested.map((id) => `${a.analysis_dir}/${DIMENSIONS[id].file}`),
  memory,
  next_steps: [
    'Review dimension summaries in .shaktra/analysis/',
    'Debt prioritization: /shaktra:analyze "debt strategy"',
    'Plan work from findings: /shaktra:tpm',
  ],
})

return {
  status: failed.length === requested.length ? 'blocked' : 'complete',
  mode: a.mode,
  dimensions: dims.map((d) => ({ id: d.id, status: d.status, artifact: `${a.analysis_dir}/${DIMENSIONS[d.id].file}`, summary: d.summary })),
  failed_dimensions: failed.map((d) => d.id),
  architecture_note: consolidation?.summary,
  observations, memory,
  report_markdown: report.markdown,
}
