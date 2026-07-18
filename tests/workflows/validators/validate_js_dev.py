#!/usr/bin/env python3
"""Validator for the JavaScript dev E2E test (language-agnostic pipeline).

Confirms the TDD pipeline works for a non-Python project: the handoff
transitions through the phases and the produced JavaScript actually passes
under Node's built-in test runner.
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


def validate_js_dev(project_dir: str, story_id: str) -> ValidationReport:
    report = ValidationReport(f"/shaktra:dev JS ({story_id})")
    shaktra = os.path.join(project_dir, ".shaktra")
    handoff_path = os.path.join(shaktra, "stories", story_id, "handoff.yml")

    data, err = load_yaml_safe(handoff_path)
    if not isinstance(data, dict):
        report.add("handoff.yml readable", False, err or "missing")
        return report
    report.add("handoff.yml readable", True)

    completed = data.get("completed_phases", [])
    for ph in ("plan", "tests", "code"):
        report.add(f"phase '{ph}' completed", ph in completed, f"not in {completed}")
    report.add("current_phase is complete", data.get("current_phase") == "complete",
               f"current_phase={data.get('current_phase')}")

    # Production JS exists.
    impl = os.path.join(project_dir, "src", "email.js")
    report.add("JavaScript implementation created", os.path.isfile(impl),
               "src/email.js not created" if not os.path.isfile(impl) else "")

    # Tests exist and pass under node --test (the real behavioral check).
    js_tests = list(Path(project_dir).rglob("*.test.js"))
    report.add("JavaScript test file created", bool(js_tests),
               "no *.test.js found" if not js_tests else "")
    if js_tests:
        proc = subprocess.run(
            ["node", "--test"],
            cwd=project_dir, capture_output=True, text=True, timeout=120,
        )
        ok = proc.returncode == 0 and "fail 0" in (proc.stdout + proc.stderr).replace("# ", "")
        report.add("JavaScript tests pass (node --test)", proc.returncode == 0,
                   (proc.stdout or proc.stderr or "").strip().splitlines()[-1]
                   if proc.returncode else "")

    check_no_sidecars(report, project_dir)
    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_js_dev.py <project_dir> <story_id>")
        sys.exit(2)
    sys.exit(print_report(validate_js_dev(sys.argv[1], sys.argv[2])))
