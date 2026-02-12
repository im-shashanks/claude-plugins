#!/usr/bin/env python3
"""Hook: block file writes outside the active story's declared scope.

Event: PreToolUse (Write|Edit)
Exit 0 = allow, Exit 2 = block.
"""

from __future__ import annotations

import glob
import json
import os
import sys

ALWAYS_ALLOWED = (
    ".shaktra/",
    "CLAUDE.md",
    ".gitignore",
    ".env",
    "package.json",
    "package-lock.json",
    "pyproject.toml",
    "poetry.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "Gemfile",
    "Gemfile.lock",
    "tsconfig.json",
    "requirements.txt",
)


def _import_yaml():
    """Import yaml lazily so operations that don't need it work without PyYAML."""
    try:
        import yaml
        return yaml
    except ImportError:
        print(
            "BLOCKED: PyYAML is required for Shaktra hooks.\n"
            "Install with: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(2)


def find_active_story_id(yaml) -> str | None:
    """Return the story_id for the active story, or None."""
    project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    pattern = os.path.join(project, ".shaktra", "stories", "*", "handoff.yml")
    candidates = []
    for path in glob.glob(pattern):
        try:
            with open(path) as f:
                handoff = yaml.safe_load(f)
            if not isinstance(handoff, dict):
                continue
            phase = handoff.get("current_phase", "")
            if phase not in ("complete", "failed"):
                candidates.append((os.path.getmtime(path), handoff))
        except Exception:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0], reverse=True)
    return candidates[0][1].get("story_id")


def normalize(file_path: str, project: str) -> str:
    """Strip project dir prefix, leading ./, and trailing slash to get a relative path."""
    proj = project.rstrip(os.sep)
    if file_path == proj or file_path.startswith(proj + os.sep):
        file_path = file_path[len(proj):]
    file_path = file_path.lstrip(os.sep)
    if file_path.startswith("./"):
        file_path = file_path[2:]
    return file_path.rstrip(os.sep)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print("BLOCKED: Could not parse hook input — failing closed.")
        sys.exit(2)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not isinstance(file_path, str) or not file_path.strip():
        sys.exit(0)

    project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    rel = normalize(file_path, project)

    for allowed in ALWAYS_ALLOWED:
        if allowed.endswith("/"):
            if rel.startswith(allowed) or rel == allowed.rstrip("/"):
                sys.exit(0)
        elif rel == allowed or rel.endswith("/" + allowed):
            sys.exit(0)

    yaml = _import_yaml()

    story_id = find_active_story_id(yaml)
    if story_id is None:
        sys.exit(0)

    story_path = os.path.join(project, ".shaktra", "stories", f"{story_id}.yml")
    try:
        with open(story_path) as f:
            story = yaml.safe_load(f)
    except Exception as e:
        print(
            f"BLOCKED: Could not read story file '{story_path}'.\n"
            f"  {e}\n"
            f"  Cannot verify file scope — failing closed."
        )
        sys.exit(2)

    if not isinstance(story, dict):
        sys.exit(0)

    files = story.get("files", [])
    if not isinstance(files, list) or not files:
        # No files declared — block with guidance rather than silently allowing all writes
        tier = str(story.get("tier", "")).lower()
        print(
            f"BLOCKED: Story '{story_id}' has no 'files' field declared.\n"
            f"  Even {tier or 'unknown'}-tier stories must declare their file scope.\n"
            f"  Add a 'files' list to .shaktra/stories/{story_id}.yml"
        )
        sys.exit(2)

    for declared in files:
        if not isinstance(declared, str):
            continue
        norm_declared = normalize(declared, project)
        if not norm_declared:
            continue
        # Exact match
        if rel == norm_declared:
            sys.exit(0)
        # Directory containment: rel is inside the declared directory
        if rel.startswith(norm_declared + "/"):
            sys.exit(0)
        # Suffix match: aligned on path segments (handles absolute vs relative)
        if rel.endswith("/" + norm_declared) or norm_declared.endswith("/" + rel):
            sys.exit(0)

    print(
        f"BLOCKED: '{rel}' is not in the declared scope for {story_id}.\n"
        f"Declared files:"
    )
    for f in files:
        print(f"  - {f}")
    print(f"\nAdd the file to {story_id}.yml or work within the declared scope.")
    sys.exit(2)


if __name__ == "__main__":
    main()
