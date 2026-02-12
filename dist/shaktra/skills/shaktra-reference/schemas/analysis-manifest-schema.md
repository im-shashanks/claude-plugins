# Analysis Manifest Schema

Defines `.shaktra/analysis/manifest.yml` — the checkpoint file that tracks analysis progress for resumability. Managed by `/shaktra:analyze`; initialized by `/shaktra:init`.

## Schema

```yaml
version: string             # analysis version identifier
started_at: datetime | null  # ISO 8601 timestamp when analysis began
completed_at: datetime | null # ISO 8601 when all stages finished
status: string              # "pending" | "in_progress" | "complete" | "partial"
execution_mode: string      # "standard" | "deep"

stages:
  pre_analysis:
    static:
      status: string        # "pending" | "complete"
      completed_at: datetime | null
    overview:
      status: string        # "pending" | "complete"
      completed_at: datetime | null

  dimensions:
    D1..D9:                  # one entry per analysis dimension
      name: string           # human-readable dimension name
      status: string         # "pending" | "in_progress" | "complete" | "failed"
      output_file: string    # filename for dimension output (e.g., "structure.yml")
      started_at: datetime | null
      completed_at: datetime | null
      error: string | null   # error message if status is "failed"

  finalize:
    validation:
      status: string        # "pending" | "complete"
    checksums:
      status: string        # "pending" | "complete"
    diagrams:
      status: string        # "pending" | "complete"
    memory:
      status: string        # "pending" | "complete"
```

## Dimensions

| Key | Name | Output File |
|---|---|---|
| D1 | Architecture & Structure | `structure.yml` |
| D2 | Domain Model & Business Rules | `domain-model.yml` |
| D3 | Entry Points & Interfaces | `entry-points.yml` |
| D4 | Coding Practices & Conventions | `practices.yml` |
| D5 | Dependencies & Tech Stack | `dependencies.yml` |
| D6 | Technical Debt & Security | `tech-debt.yml` |
| D7 | Data Flows & Integration | `data-flows.yml` |
| D8 | Critical Paths & Risk | `critical-paths.yml` |
| D9 | Git Intelligence | `git-intelligence.yml` |

## Status Transitions

**Top-level status:**
- `pending` -> `in_progress` (first dimension starts)
- `in_progress` -> `complete` (all dimensions + finalize stages complete)
- `in_progress` -> `partial` (some dimensions complete, others failed or pending at session end)

**Dimension status:**
- `pending` -> `in_progress` (analyzer agent starts dimension)
- `in_progress` -> `complete` (output file written and valid)
- `in_progress` -> `failed` (error captured in `error` field)

## Consumer Reference

| Consumer | Usage |
|---|---|
| `/shaktra:analyze` | Reads to resume interrupted analysis; writes to update progress |
| `/shaktra:init` | Creates from template with all stages set to `pending` |
| `/shaktra:doctor` | Reads to report analysis health status |
| `cba-analyzer` agent | Reads assigned dimension; writes status on completion |
