#!/usr/bin/env python3
"""Migrate legacy decisions.yml + lessons.yml to the new principles-based memory system."""

import sys
import shutil
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

CATEGORY_TO_ROLES = {
    "correctness": ["developer", "sw-engineer"],
    "reliability": ["developer", "sw-engineer"],
    "performance": ["developer", "sw-engineer", "architect"],
    "security": ["developer", "sw-engineer", "sw-quality"],
    "maintainability": ["developer", "sw-quality"],
    "testability": ["developer", "sw-quality", "test-agent"],
    "observability": ["developer", "architect"],
    "scalability": ["developer", "architect"],
    "compatibility": ["developer", "sw-engineer"],
    "accessibility": ["developer"],
    "usability": ["developer"],
    "cost": ["architect"],
    "compliance": ["developer", "sw-quality"],
    "consistency": ["developer", "sw-engineer", "architect"],
}


def infer_roles(categories):
    roles = set()
    for cat in categories:
        roles.update(CATEGORY_TO_ROLES.get(cat, ["developer"]))
    return sorted(roles)


def migrate(project_root):
    memory_dir = Path(project_root) / ".shaktra" / "memory"
    decisions_path = memory_dir / "decisions.yml"
    lessons_path = memory_dir / "lessons.yml"
    principles_path = memory_dir / "principles.yml"

    if principles_path.exists():
        print(f"principles.yml already exists at {principles_path}. Aborting.")
        sys.exit(1)

    principles = []
    today = date.today().isoformat()
    next_id = 1

    # Migrate decisions
    if decisions_path.exists():
        with open(decisions_path) as f:
            data = yaml.safe_load(f) or {}
        for dc in data.get("decisions", []):
            pr = {
                "id": f"PR-{next_id:03d}",
                "text": dc.get("summary", dc.get("title", "")),
                "categories": dc.get("categories", []),
                "guidance": dc.get("guidance", []),
                "confidence": 0.7,
                "source_count": 1,
                "tags": dc.get("categories", []),
                "roles": infer_roles(dc.get("categories", [])),
                "scope": "project",
                "status": dc.get("status", "active"),
                "source": f"migrated:DC-{dc.get('id', next_id):>03s}" if isinstance(dc.get("id"), str) else f"migrated:DC-{dc.get('id', next_id)}",
                "created": dc.get("created", today),
            }
            if dc.get("supersedes"):
                pr["supersedes"] = dc["supersedes"].replace("DC-", "PR-")
            principles.append(pr)
            next_id += 1

        shutil.copy2(decisions_path, str(decisions_path) + ".bak")
        print(f"Migrated {len(data.get('decisions', []))} decisions → principles")

    # Migrate strong lessons as seed principles
    lesson_count = 0
    if lessons_path.exists():
        with open(lessons_path) as f:
            data = yaml.safe_load(f) or {}
        for ls in data.get("lessons", []):
            pr = {
                "id": f"PR-{next_id:03d}",
                "text": ls.get("insight", ""),
                "categories": [],
                "guidance": [ls.get("action", "")],
                "confidence": 0.5,
                "source_count": 1,
                "tags": [],
                "roles": ["developer"],
                "scope": "project",
                "status": "active",
                "source": f"migrated:{ls.get('source', ls.get('id', ''))}",
                "created": ls.get("date", today),
            }
            principles.append(pr)
            next_id += 1
            lesson_count += 1

        shutil.copy2(lessons_path, str(lessons_path) + ".bak")
        print(f"Migrated {lesson_count} lessons → principles")

    # Write principles
    with open(principles_path, "w") as f:
        f.write("# Project principles — synthesized from observations\n")
        f.write("# Migrated from decisions.yml and lessons.yml\n")
        yaml.dump({"principles": principles}, f, default_flow_style=False, sort_keys=False)

    print(f"\nMigration complete: {len(principles)} principles written to {principles_path}")
    print(f"Backups: {decisions_path}.bak, {lessons_path}.bak")


if __name__ == "__main__":
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    migrate(project_root)
