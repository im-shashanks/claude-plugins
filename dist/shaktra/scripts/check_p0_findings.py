#!/usr/bin/env python3
"""Hook: block agent completion when P0 findings remain.

Event: Stop (no matcher)
Exit 0 = allow, Exit 2 = block.
"""

from __future__ import annotations

import glob
import os
import sys


def find_active_story(yaml) -> dict | None:
    """Return the handoff dict for the active story, or None."""
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
                candidates.append((os.path.getmtime(path), path, handoff))
        except Exception:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0], reverse=True)
    return candidates[0][2]


def main() -> None:
    if os.environ.get("SHAKTRA_SKIP_P0_CHECK"):
        sys.exit(0)

    # Check if any handoff files exist before importing PyYAML
    project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    pattern = os.path.join(project, ".shaktra", "stories", "*", "handoff.yml")
    if not glob.glob(pattern):
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

    handoff = find_active_story(yaml)
    if handoff is None:
        sys.exit(0)

    findings = handoff.get("quality_findings", [])
    if not isinstance(findings, list):
        print(
            "BLOCKED: 'quality_findings' in handoff is not a list.\n"
            "  Cannot verify P0 status — blocking until corrected."
        )
        sys.exit(2)

    p0s = [
        f for f in findings
        if isinstance(f, dict)
        and str(f.get("severity", "")).upper() == "P0"
        and not f.get("resolved", False)
    ]
    if not p0s:
        sys.exit(0)

    print(f"BLOCKED: {len(p0s)} P0 finding(s) must be resolved before completion.\n")
    for f in p0s:
        loc = f.get("file", "unknown")
        line = f.get("line", "")
        desc = f.get("issue", "no description")
        loc_str = f"{loc}:{line}" if line else loc
        print(f"  P0  {loc_str} — {desc}")

    sys.exit(2)


if __name__ == "__main__":
    main()
