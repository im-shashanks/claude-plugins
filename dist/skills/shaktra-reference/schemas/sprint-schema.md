# Sprint Schema

Defines `.shaktra/sprints.yml` — sprint state managed by the scrummaster agent. Only active when `settings.sprints.enabled` is true.

## Schema

```yaml
current_sprint:
  id: string               # "SP-001" — sequential
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

## Template Alignment Note

The init template (`templates/sprints.yml`) uses `velocity_history` and `sprints` as top-level keys for simplicity. This schema defines the target structure that the scrummaster agent migrates to on first sprint creation. Both formats are valid; the scrummaster handles the transition.
