#!/usr/bin/env python3
"""Deterministic sprint-state update when a story completes.

Usage:
    python3 shaktra_sprint.py --complete-story ST-001 [--project DIR]

Implements the SPRINT STATE UPDATE step of the TDD pipeline and the velocity
formulas from skills/shaktra-stories/sprint-schema.md:

- marks the story done in its story file
- adds its points to the current sprint's completed total
- when every sprint story is done: moves the sprint into velocity.history,
  recalculates average (rolling 3) and trend, clears current_sprint

No-op (exit 0) when sprints are disabled, sprints.yml is missing, or the
story is not in the current sprint. Prints a JSON summary either way.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def atomic_write_yaml(path: Path, data: dict, yaml) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def load(path: Path, yaml):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else None


def recalc_velocity(history: list[dict]) -> tuple[float, str]:
    """average = rolling mean of last 3 completed_points; trend per sprint-schema.md."""
    if not history:
        return 0.0, "stable"
    last3 = [h.get("completed_points", 0) for h in history[-3:]]
    average = round(sum(last3) / len(last3), 2)
    if len(history) >= 3:
        recent = (history[-1].get("completed_points", 0) + history[-2].get("completed_points", 0)) / 2
        older = history[-3].get("completed_points", 0)
        if recent > older * 1.1:
            trend = "improving"
        elif recent < older * 0.9:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
    return average, trend


def story_status(shaktra: Path, story_id: str, yaml) -> tuple[Path | None, dict | None]:
    for suffix in (".yml", ".yaml"):
        path = shaktra / "stories" / f"{story_id}{suffix}"
        if path.exists():
            return path, load(path, yaml)
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--complete-story", required=True, dest="story_id")
    parser.add_argument("--project", default=os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    args = parser.parse_args()

    try:
        import yaml
    except ImportError:
        print(json.dumps({"error": "PyYAML required — pip install pyyaml"}))
        return 1

    shaktra = Path(args.project).resolve() / ".shaktra"
    settings = load(shaktra / "settings.yml", yaml) or {}
    if not (settings.get("sprints") or {}).get("enabled", False):
        print(json.dumps({"updated": False, "reason": "sprints disabled"}))
        return 0

    sprints_path = shaktra / "sprints.yml"
    sprints = load(sprints_path, yaml)
    if sprints is None:
        print(json.dumps({"updated": False, "reason": "no sprints.yml"}))
        return 0

    # Mark the story done regardless of sprint membership.
    story_path, story = story_status(shaktra, args.story_id, yaml)
    if story is not None:
        story.setdefault("metadata", {})["status"] = "done"
        atomic_write_yaml(story_path, story, yaml)

    current = sprints.get("current_sprint")
    if not isinstance(current, dict) or args.story_id not in (current.get("stories") or []):
        print(json.dumps({"updated": story is not None, "reason": "story not in current sprint",
                          "story_marked_done": story is not None}))
        return 0

    # Track completed points on the sprint.
    points = int((story or {}).get("metadata", {}).get("story_points") or 0)
    current["completed_points"] = int(current.get("completed_points") or 0) + points

    # Sprint finished when every committed story is done.
    all_done = True
    for sid in current.get("stories") or []:
        _, s = story_status(shaktra, str(sid), yaml)
        if ((s or {}).get("metadata") or {}).get("status") != "done":
            all_done = False
            break

    sprint_closed = False
    if all_done:
        velocity = sprints.setdefault("velocity", {"history": [], "average": 0, "trend": "stable"})
        history = velocity.setdefault("history", [])
        history.append({
            "sprint_id": current.get("id"),
            "planned_points": int(current.get("committed_points") or 0),
            "completed_points": int(current.get("completed_points") or 0),
        })
        velocity["average"], velocity["trend"] = recalc_velocity(history)
        sprints["current_sprint"] = None
        sprint_closed = True

    atomic_write_yaml(sprints_path, sprints, yaml)
    print(json.dumps({
        "updated": True,
        "story_marked_done": story is not None,
        "points_added": points,
        "sprint_closed": sprint_closed,
        "velocity": sprints.get("velocity"),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
