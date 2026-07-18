#!/usr/bin/env python3
"""Validator for /shaktra:dev refactor workflow (workflows/refactor.js).

Checks the ASSESS -> FORTIFY -> TRANSFORM -> VERIFY -> memory state machine,
and — the load-bearing behavioral check — that the pinning tests still pass
after refactoring (behavior preservation).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import (
    ValidationReport, check_no_sidecars, load_yaml_safe, print_report,
)

REFACTOR_PHASES = ["assess", "fortify", "transform", "verify"]


def validate_refactor(project_dir: str) -> ValidationReport:
    report = ValidationReport("/shaktra:dev refactor")
    shaktra = os.path.join(project_dir, ".shaktra")

    # --- Refactoring handoff exists ---
    handoffs = list(Path(shaktra).glob("refactoring/*/refactoring-handoff.yml"))
    report.add("refactoring-handoff.yml created", bool(handoffs),
               "no refactoring-handoff.yml under .shaktra/refactoring/" if not handoffs else "")
    data = {}
    if handoffs:
        data, err = load_yaml_safe(str(handoffs[0]))
        report.add("refactoring-handoff.yml valid YAML", isinstance(data, dict), err or "")
        data = data or {}

    # --- Phase progression ---
    completed = data.get("completed_phases", []) if isinstance(data, dict) else []
    for ph in REFACTOR_PHASES:
        report.add(f"phase '{ph}' completed", ph in completed,
                   f"not in completed_phases ({completed})" if ph not in completed else "")
    report.add("current_phase is complete",
               data.get("current_phase") == "complete",
               f"current_phase={data.get('current_phase')}")

    # --- Assessment recorded smells + transforms ---
    assessment = data.get("assessment", {}) if isinstance(data, dict) else {}
    smells = assessment.get("smells_detected") or []
    transforms = assessment.get("proposed_transforms") or []
    report.add("smells detected", len(smells) > 0,
               "assessment.smells_detected empty" if not smells else "")
    report.add("transforms proposed", len(transforms) > 0,
               "assessment.proposed_transforms empty" if not transforms else "")

    # --- Behavior preserved: pinning tests still pass ---
    tests_dir = os.path.join(project_dir, "tests")
    if os.path.isdir(tests_dir):
        proc = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-q"],
            cwd=project_dir, capture_output=True, text=True, timeout=120,
        )
        report.add("pinning tests still pass after refactoring",
                   proc.returncode == 0,
                   (proc.stdout or proc.stderr or "").strip().splitlines()[-1:] and
                   (proc.stdout or proc.stderr).strip().splitlines()[-1] or "pytest failed")
    else:
        report.add("tests directory present", False, "no tests/ dir to verify behavior")

    # --- Memory capture ran ---
    report.add("memory captured", bool(data.get("memory_captured")),
               "memory_captured not true" if not data.get("memory_captured") else "")

    # --- No retired sidecar mechanisms ---
    check_no_sidecars(report, project_dir)

    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_refactor.py <project_dir>")
        sys.exit(2)
    sys.exit(print_report(validate_refactor(sys.argv[1])))
