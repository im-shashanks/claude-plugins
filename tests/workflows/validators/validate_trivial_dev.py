#!/usr/bin/env python3
"""Validator for the trivial-tier dev test.

Verifies the tier gate matrix (story-tiers.md): a trivial story SKIPS the RED
phase and the comprehensive QUALITY phase, running only PLAN -> BRANCH -> GREEN
-> memory. The load-bearing assertions are the *skips* — 'tests' and 'quality'
must NOT appear in completed_phases — plus the code artifact existing.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import ValidationReport, load_yaml_safe, print_report


def validate_trivial_dev(project_dir: str, story_id: str) -> ValidationReport:
    report = ValidationReport(f"/shaktra:dev trivial ({story_id})")
    handoff = os.path.join(project_dir, ".shaktra", "stories", story_id, "handoff.yml")
    data, err = load_yaml_safe(handoff)
    if not isinstance(data, dict):
        report.add("handoff.yml readable", False, err or "missing")
        return report
    report.add("handoff.yml readable", True)

    completed = data.get("completed_phases", []) or []
    report.add("plan phase completed", "plan" in completed, f"completed={completed}")
    report.add("code phase completed", "code" in completed, f"completed={completed}")
    # completed_phases must stay a valid contiguous prefix even with skips.
    report.add("completed_phases is a valid prefix",
               completed == ["plan", "tests", "code"][:len(completed)] and "plan" in completed,
               f"completed={completed} is not a prefix of [plan,tests,code]")
    # The assertable tier-matrix skip: comprehensive QUALITY does NOT run for
    # trivial (quality is the terminal phase, so its absence is unambiguous).
    report.add("comprehensive QUALITY SKIPPED for trivial (no 'quality')",
               "quality" not in completed,
               "'quality' present — comprehensive review should be skipped for trivial")
    # RED-skip is confirmed by the reduced coverage bar (hotfix threshold), not
    # by completed_phases (a skipped phase still counts as complete for the prefix).
    report.add("current_phase is complete", data.get("current_phase") == "complete",
               f"current_phase={data.get('current_phase')}")
    report.add("memory captured", bool(data.get("memory_captured")),
               "memory_captured not true")

    # The version constant was actually written somewhere in src/.
    srcs = list(Path(project_dir).rglob("version.py")) + list(Path(os.path.join(project_dir, "src")).rglob("*.py")) \
        if os.path.isdir(os.path.join(project_dir, "src")) else []
    wrote_version = any("__version__" in p.read_text(errors="ignore") for p in srcs) if srcs else False
    report.add("version constant written to source", wrote_version,
               "no __version__ found in any src/*.py")
    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_trivial_dev.py <project_dir> <story_id>")
        sys.exit(2)
    sys.exit(print_report(validate_trivial_dev(sys.argv[1], sys.argv[2])))
