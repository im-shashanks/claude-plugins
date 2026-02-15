#!/usr/bin/env python3
"""Validators for /shaktra:pm workflow.

Checks that PM workflow produces PRD artifacts, personas, journey maps,
and/or prioritization output.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import (
    ValidationReport,
    check_exists,
    check_glob_matches,
    check_is_dir,
    check_is_file,
    check_valid_yaml,
    print_report,
)


def validate_pm(project_dir: str) -> ValidationReport:
    """Validate .shaktra/ state after /shaktra:pm."""
    report = ValidationReport("/shaktra:pm")
    shaktra = os.path.join(project_dir, ".shaktra")

    if not check_is_dir(report, shaktra, ".shaktra/ exists"):
        return report

    # --- PRD artifacts ---
    # PM may create PRD in .shaktra/ or .shaktra/designs/
    prd_locations = [
        os.path.join(shaktra, "prd.md"),
        os.path.join(shaktra, "designs"),
    ]
    prd_found = False
    for loc in prd_locations:
        if os.path.isfile(loc):
            prd_found = True
            break
        if os.path.isdir(loc):
            prds = list(Path(loc).glob("*prd*"))
            prds += list(Path(loc).glob("*PRD*"))
            prds += list(Path(loc).glob("*requirement*"))
            if prds:
                prd_found = True
                break
    report.add("PRD artifact found", prd_found,
               "no PRD file in .shaktra/ or designs/" if not prd_found else "")

    # --- PM output artifacts (any of: personas, journeys, prioritization) ---
    pm_dir = os.path.join(shaktra, "pm")
    if os.path.isdir(pm_dir):
        report.add("pm/ directory exists", True)
        # Check for various PM artifacts
        artifacts = list(Path(pm_dir).iterdir())
        report.add(
            "PM artifacts created",
            len(artifacts) > 0,
            f"found {len(artifacts)} artifacts" if artifacts else "pm/ is empty",
        )
    else:
        # PM artifacts might be in designs/ or root .shaktra/
        any_pm = False
        for pattern in ["*persona*", "*journey*", "*prioriti*", "*research*"]:
            matches = list(Path(shaktra).glob(f"**/{pattern}"))
            if matches:
                any_pm = True
                report.add(f"PM artifact ({pattern}) found", True)
        if not any_pm:
            report.add("PM artifacts found", False,
                       "no persona/journey/prioritization artifacts found")

    # --- Memory (optional for PM) ---
    decisions_path = os.path.join(shaktra, "memory", "decisions.yml")
    if os.path.isfile(decisions_path):
        check_valid_yaml(report, decisions_path, "decisions.yml valid YAML")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_pm.py <project_dir>")
        sys.exit(2)
    r = validate_pm(sys.argv[1])
    sys.exit(print_report(r))
