#!/usr/bin/env python3
"""Hook: validate Shaktra state files on write.

Event: PostToolUse (Write|Edit)
Exit 0 = allow, Exit 2 = block.
"""

from __future__ import annotations

import json
import os
import re
import sys

STORY_RE = re.compile(r"\.shaktra/stories/[^/]+\.yml$")
HANDOFF_RE = re.compile(r"\.shaktra/stories/[^/]+/handoff\.yml$")

VALID_TIERS = {"trivial", "small", "medium", "large"}
VALID_SCOPES = {
    "bug_fix", "feature", "refactor", "config", "docs", "test",
    "performance", "security", "integration", "migration", "scaffold",
}
VALID_PHASES = {"pending", "plan", "tests", "code", "quality", "complete", "failed"}
PHASE_ORDER = ["plan", "tests", "code", "quality"]


def normalize(file_path: str, project: str) -> str:
    proj = project.rstrip(os.sep)
    if file_path == proj or file_path.startswith(proj + os.sep):
        file_path = file_path[len(proj):]
    return file_path.lstrip(os.sep)


def validate_story(data: dict) -> list[str]:
    errors = []
    for field in ("id", "title", "description"):
        if field not in data:
            errors.append(f"Missing required field: {field}")
    tier = data.get("tier")
    if tier is not None and str(tier).lower() not in VALID_TIERS:
        errors.append(f"Invalid tier '{tier}' — must be one of: {', '.join(sorted(VALID_TIERS))}")
    scope = data.get("scope")
    if scope is not None and str(scope).lower() not in VALID_SCOPES:
        errors.append(f"Invalid scope '{scope}' — must be one of: {', '.join(sorted(VALID_SCOPES))}")
    files = data.get("files")
    if files is not None and not isinstance(files, list):
        errors.append("'files' must be a list of strings")
    return errors


def validate_handoff(data: dict) -> list[str]:
    errors = []
    for field in ("story_id", "current_phase", "completed_phases"):
        if field not in data:
            errors.append(f"Missing required field: {field}")
    phase = data.get("current_phase")
    if phase is not None and str(phase).lower() not in VALID_PHASES:
        errors.append(f"Invalid current_phase '{phase}' — must be one of: {', '.join(sorted(VALID_PHASES))}")
    completed = data.get("completed_phases")
    if completed is not None:
        if not isinstance(completed, list):
            errors.append("'completed_phases' must be a list")
        else:
            for i, p in enumerate(completed):
                if i >= len(PHASE_ORDER) or str(p).lower() != PHASE_ORDER[i]:
                    errors.append(
                        f"Invalid completed_phases sequence — must be a prefix of "
                        f"{PHASE_ORDER}, got {completed}"
                    )
                    break
    return errors


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print("BLOCKED: Could not parse hook input — failing closed.")
        sys.exit(2)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not isinstance(file_path, str):
        sys.exit(0)

    project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    rel = normalize(file_path, project)

    is_story = bool(STORY_RE.search(rel))
    is_handoff = bool(HANDOFF_RE.search(rel))
    if not is_story and not is_handoff:
        sys.exit(0)

    try:
        import yaml
    except ImportError:
        print(
            "BLOCKED: PyYAML is required for Shaktra hooks.\n"
            "Install with: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        with open(file_path) as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"BLOCKED: Invalid YAML syntax in {rel}\n  {e}")
        sys.exit(2)
    except FileNotFoundError:
        sys.exit(0)

    if not isinstance(content, dict):
        print(f"BLOCKED: {rel} must be a YAML mapping, got {type(content).__name__}")
        sys.exit(2)

    errors = validate_handoff(content) if is_handoff else validate_story(content)

    if errors:
        print(f"BLOCKED: Schema validation failed for {rel}")
        print(f"  The file was already written — correct it to match the schema.\n")
        for err in errors:
            print(f"  - {err}")
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
