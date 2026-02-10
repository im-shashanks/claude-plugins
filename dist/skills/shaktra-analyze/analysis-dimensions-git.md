# Analysis Dimensions — Git Intelligence (D9)

Historical signals from git that are invisible to static analysis. Answers "How has this codebase EVOLVED?" — change patterns, bug density, knowledge distribution, and code age.

**Used by:** shaktra-cba-analyzer agent during `/shaktra:analyze` workflow.
**Input dependency:** Requires a git repository. Consumes `static.yml` (file inventory for scoping).
**Companion:** `analysis-dimensions-core.md` defines D1-D4, `analysis-dimensions-health.md` defines D5-D8.

---

## Extraction Philosophy

All data in this dimension comes from **tool-based extraction** — the same philosophy as `static.yml`. Run git commands via Bash and parse the output. No LLM interpretation of git data. The CBA analyzer's role is structuring the output, not inferring meaning.

**Shallow clone guard:** Before extraction, check commit count with `git rev-list --count HEAD`. If fewer than 10 commits, note the limitation in `summary:` and produce minimal output (hotspots and code_age only, with a caveat).

---

## D9: Git Intelligence → `git-intelligence.yml`

**Scope:** Historical change patterns, bug-fix density, co-change coupling, knowledge distribution, and code age across all tracked source files.

**What to extract:**

1. **Hotspots** — files with the most commits. Use `git log --format=format: --name-only | sort | uniq -c | sort -rn` scoped to source files from `static.yml`. Classify: top 10% = hot, middle 40% = warm, bottom 50% = cold. Also extract distinct author count per file via `git shortlog -sn -- {file}`.

2. **Bug-fix density** — commits matching fix/bug/patch/hotfix patterns in their message. Use `git log --oneline --all -- {file}` and grep for `fix|bug|patch|hotfix` (case-insensitive). Compute fix_ratio = fix_commits / total_commits. Also count recent fixes (last 90 days) via `git log --since="90 days ago"`.

3. **Co-change patterns** — files that frequently change together in the same commit. Use `git log --format=format: --name-only` to get file lists per commit, then compute pairwise co-occurrence. Report clusters with minimum 3 co-occurrences. Flag `hidden_coupling: true` when co-changing files don't import each other (cross-reference `static.yml` dependency graph).

4. **Knowledge distribution** — author concentration per file. Use `git shortlog -sn -- {file}` for commit counts per author. Compute bus_factor (authors with >20% of commits). Flag `knowledge_risk: high` when bus_factor = 1 and file is on a critical path.

5. **Code age** — last modification date per file. Use `git log -1 --format=%aI -- {file}`. Classify: fresh (<30 days), recent (30-180 days), aging (180-365 days), stale (>365 days). Age categories are analysis constants, not quality gates.

**Git commands reference:**
- Hotspot ranking: `git log --format=format: --name-only --diff-filter=ACDMR | sort | uniq -c | sort -rn`
- Per-file authors: `git shortlog -sn -- {file}`
- Fix-commit detection: `git log --oneline --all --grep='fix\|bug\|patch\|hotfix' -i -- {file}`
- Recent fix commits: `git log --oneline --since="90 days ago" --grep='fix\|bug\|patch\|hotfix' -i -- {file}`
- Co-change extraction: `git log --format=format: --name-only` (group by blank-line-delimited commits)
- Code age: `git log -1 --format=%aI -- {file}`
- Commit count check: `git rev-list --count HEAD`

**Evidence requirements:**
- All data from actual git command output — no LLM inference
- Hotspot thresholds based on actual commit count distribution (percentile-based)
- Co-change patterns require minimum 3 co-occurrences to report
- Bug-fix matching uses commit message pattern matching, not code analysis
- Knowledge distribution uses commit count attribution (approximation, not perfect)

**Output structure:**
```yaml
summary: |
  {Self-contained 400-token overview: hotspot count, highest-churn files,
   co-change clusters, bug-fix density distribution, knowledge risks}
details:
  hotspots:
    - file: string
      commits_last_90_days: integer
      commits_last_365_days: integer
      distinct_authors: integer
      churn_category: hot | warm | cold
  bug_fix_density:
    - file: string
      total_commits: integer
      fix_commits: integer
      fix_ratio: float
      recent_fixes: integer
  co_change_patterns:
    - cluster_name: string
      files: [string]
      co_change_frequency: integer
      linked_in_code: boolean
      hidden_coupling: boolean
  knowledge_distribution:
    - file: string
      primary_author: string
      author_count: integer
      bus_factor: integer
      knowledge_risk: high | medium | low
  code_age:
    - file: string
      last_modified: ISO-8601
      age_category: fresh | recent | aging | stale
```
