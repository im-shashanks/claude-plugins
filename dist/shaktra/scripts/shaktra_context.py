#!/usr/bin/env python3
"""Emit the Shaktra context blob as JSON — the single threshold-read point.

Usage:
    python3 shaktra_context.py [--story ST-XXX] [--project DIR]

Orchestrator skills run this once during pre-flight and pass the relevant
parts into workflow scripts via Workflow args. Nothing else reads settings
thresholds directly. Story tier detection and the story-quality guard follow
skills/shaktra-stories/story-tiers.md; field lists follow story-schema.md.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

TIER_FIELDS = {
    "trivial": ["id", "title", "description"],
    "small": ["files", "acceptance_criteria"],
    "medium": [
        "scope", "interfaces", "io_examples", "error_handling",
        "test_specs", "invariants", "logging_rules", "observability_rules",
    ],
    "large": [
        "failure_modes", "edge_cases", "determinism",
        "feature_flags", "concurrency", "resource_safety",
    ],
}
TIER_ORDER = ["trivial", "small", "medium", "large"]
COVERAGE_KEYS = {
    "trivial": "hotfix_coverage_threshold",
    "small": "small_coverage_threshold",
    "medium": "coverage_threshold",
    "large": "large_coverage_threshold",
}
LANGUAGE_FIELDS = ["language", "test_framework", "coverage_tool"]
MEMORY_STORES = ["principles.yml", "anti-patterns.yml", "procedures.yml"]


def load_yaml(path: Path):
    import yaml
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else None
    except (OSError, yaml.YAMLError):
        return None


def detect_tier(story: dict) -> str:
    """Auto-detect tier per story-tiers.md. Explicit story tier wins."""
    explicit = str(story.get("tier", "")).lower()
    if explicit in TIER_ORDER:
        return explicit
    files = story.get("files") or []
    implements = (story.get("interfaces") or {}).get("implements") or []
    if not story.get("acceptance_criteria"):
        return "trivial"
    if len(files) <= 3 and not implements:
        return "small"
    if len(files) <= 10 or implements:
        return "medium"
    return "large"


def required_fields(tier: str) -> list[str]:
    fields: list[str] = []
    for t in TIER_ORDER:
        fields.extend(TIER_FIELDS[t])
        if t == tier:
            break
    return fields


def story_quality(story: dict, tier: str) -> dict:
    need = required_fields(tier)
    missing = [f for f in need if not story.get(f)]
    return {
        "tier": tier,
        "required_fields": len(need),
        "present": len(need) - len(missing),
        "missing": missing,
        "sparse": bool(missing),
    }


def find_story(shaktra: Path, story_id: str) -> tuple[dict | None, str | None]:
    for pattern in (f"{story_id}.yml", f"{story_id}.yaml"):
        path = shaktra / "stories" / pattern
        if path.exists():
            return load_yaml(path), str(path)
    return None, None


def dependency_state(story: dict, shaktra: Path) -> dict:
    blocked_by = (story.get("metadata") or {}).get("blocked_by") or []
    unresolved = []
    for dep_id in blocked_by:
        dep, _ = find_story(shaktra, str(dep_id))
        status = ((dep or {}).get("metadata") or {}).get("status", "missing")
        if status != "done":
            unresolved.append({"id": str(dep_id), "status": status})
    return {"blocked_by": blocked_by, "unresolved": unresolved}


def memory_state(shaktra: Path, settings: dict) -> dict:
    counts = {}
    total = 0
    for store in MEMORY_STORES:
        data = load_yaml(shaktra / "memory" / store) or {}
        n = 0
        for value in data.values():
            if isinstance(value, list):
                n += sum(
                    1 for e in value
                    if isinstance(e, dict) and e.get("status", "active") == "active"
                )
        counts[store.replace(".yml", "").replace("-", "_")] = n
        total += n
    mem = settings.get("memory") or {}
    tier1_max = mem.get("retrieval_tier1_max", 100)
    tier2_max = mem.get("retrieval_tier2_max", 500)
    tier = 1 if total <= tier1_max else 2 if total <= tier2_max else 3
    return {"total_entries": total, "retrieval_tier": tier, "counts": counts}


def active_handoffs(shaktra: Path) -> list[str]:
    """Paths of handoffs not complete/failed — most recently modified first."""
    found = []
    for path in glob.glob(str(shaktra / "stories" / "*" / "handoff.yml")):
        data = load_yaml(Path(path))
        if data and data.get("current_phase") not in ("complete", "failed"):
            found.append((os.path.getmtime(path), path))
    return [p for _, p in sorted(found, reverse=True)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--story", help="Story id (e.g. ST-001)")
    parser.add_argument("--project", default=os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    args = parser.parse_args()

    try:
        import yaml  # noqa: F401
    except ImportError:
        print(json.dumps({"error": "PyYAML required — pip install pyyaml"}))
        return 1

    project = Path(args.project).resolve()
    shaktra = project / ".shaktra"
    ctx: dict = {
        "schema_version": "1.0.0",
        "project_dir": str(project),
        "plugin_root": os.environ.get("CLAUDE_PLUGIN_ROOT"),
        "shaktra_initialized": shaktra.is_dir(),
    }

    settings = load_yaml(shaktra / "settings.yml") or {}
    ctx["settings"] = settings or None
    ctx["test_mode"] = settings.get("test_mode")

    proj = settings.get("project") or {}
    missing_lang = [f for f in LANGUAGE_FIELDS if not proj.get(f)]
    ctx["pre_flight"] = {
        "language_configured": not missing_lang,
        "missing_language_fields": missing_lang,
    }

    ctx["memory"] = memory_state(shaktra, settings) if shaktra.is_dir() else None
    ctx["active_handoffs"] = active_handoffs(shaktra) if shaktra.is_dir() else []

    if args.story:
        story, story_path = find_story(shaktra, args.story)
        ctx["story"] = story
        ctx["story_path"] = story_path
        if story:
            tier = detect_tier(story)
            tdd = settings.get("tdd") or {}
            ctx["tier"] = tier
            ctx["coverage_threshold"] = tdd.get(COVERAGE_KEYS[tier])
            ctx["p1_threshold"] = (settings.get("quality") or {}).get("p1_threshold")
            ctx["story_quality"] = story_quality(story, tier)
            ctx["dependencies"] = dependency_state(story, shaktra)
            handoff_path = shaktra / "stories" / args.story / "handoff.yml"
            ctx["handoff"] = load_yaml(handoff_path)
            ctx["handoff_path"] = str(handoff_path)

    print(json.dumps(ctx, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
