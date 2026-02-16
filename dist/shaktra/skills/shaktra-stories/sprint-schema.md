# Sprint Schema

Defines `.shaktra/sprints.yml` — sprint state managed by the scrummaster agent. Only active when `settings.sprints.enabled` is true.

## Schema

```yaml
current_sprint:
  id: string               # "SP-001" — sequential
  goal: string             # business objective for this sprint (PM assigns)
  start_date: string       # ISO 8601 date
  end_date: string         # start_date + settings.sprints.sprint_duration_weeks
  stories: [string]        # story IDs committed to this sprint
  capacity_points: integer # team capacity in story points
  committed_points: integer # sum of committed story points

velocity:
  history:
    - sprint_id: string
      planned_points: integer
      completed_points: integer
  average: number          # rolling average of completed_points
  trend: string            # "improving" | "stable" | "declining"

backlog:
  - story_id: string
    points: integer
    priority: string       # "critical" | "high" | "medium" | "low"
    blocked_by: [string]   # story IDs that must complete first
```

## Velocity Calculation

```
average = sum(history[-3:].completed_points) / min(len(history), 3)

if len(history) >= 3:
    recent = average of last 2 sprints
    older  = history[-3].completed_points
    if recent > older * 1.1: trend = "improving"
    elif recent < older * 0.9: trend = "declining"
    else: trend = "stable"
else:
    trend = "stable"
```

## Backlog Ordering

Scrummaster sorts backlog by: blocked_by (unblocked first) → priority → points (smallest first).

## Template Migration Contract

The init template (`templates/sprints.yml`) uses a simplified structure:

```yaml
current_sprint: null
velocity_history: []
sprints: []
```

On first sprint creation, the scrummaster agent migrates to the target schema:

1. `velocity_history: []` → `velocity.history: []` + `velocity.average: 0` + `velocity.trend: "stable"`
2. `sprints: []` → removed (sprint history lives in `velocity.history`)
3. `current_sprint: null` → populated with first sprint data
4. `backlog: []` → added (empty initially, populated during sprint allocation)

After migration, the file follows this schema exclusively. The scrummaster performs this migration automatically on first sprint creation; no manual intervention required.
