#!/usr/bin/env python3
"""Validator for the dev-resume E2E test.

Confirms dev-tdd.js RESUMED from a handoff already through plan+tests — i.e.
it skipped those phases and completed GREEN — rather than re-running the whole
pipeline. The resume signal: the seeded plan/test summaries are preserved
(test_count stays 4) while the code phase completes and the implementation now
exists on disk with green tests.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import ValidationReport, load_yaml_safe, print_report


def validate_resume(project_dir: str, story_id: str) -> ValidationReport:
    report = ValidationReport(f"/shaktra:dev resume ({story_id})")
    shaktra = os.path.join(project_dir, ".shaktra")
    handoff_path = os.path.join(shaktra, "stories", story_id, "handoff.yml")

    data, err = load_yaml_safe(handoff_path)
    if not isinstance(data, dict):
        report.add("handoff.yml readable", False, err or "missing")
        return report
    report.add("handoff.yml readable", True)

    completed = data.get("completed_phases", [])
    for ph in ("plan", "tests", "code"):
        report.add(f"phase '{ph}' completed", ph in completed,
                   f"not in {completed}")
    report.add("current_phase is complete", data.get("current_phase") == "complete",
               f"current_phase={data.get('current_phase')}")

    # Resume signal: the seeded plan/test state was preserved, not regenerated.
    ts = data.get("test_summary", {}) or {}
    report.add("seeded test_summary preserved (test_count == 4)",
               ts.get("test_count") == 4,
               f"test_count={ts.get('test_count')} (expected the seeded 4 — RED may have re-run)")
    ps = data.get("plan_summary", {}) or {}
    comps = ps.get("components", []) or []
    report.add("seeded plan_summary preserved (slugify component)",
               any("slugify" in str(c).lower() for c in comps),
               "plan_summary does not carry the seeded slugify component")

    # GREEN actually ran: implementation exists and tests pass.
    impl = os.path.join(project_dir, "src", "slugify.py")
    report.add("implementation created by GREEN", os.path.isfile(impl),
               "src/slugify.py not created" if not os.path.isfile(impl) else "")
    cs = data.get("code_summary", {}) or {}
    report.add("code_summary present", bool(cs), "no code_summary")

    tests_dir = os.path.join(project_dir, "tests")
    if os.path.isdir(tests_dir):
        proc = subprocess.run(["python3", "-m", "pytest", "tests/", "-q"],
                              cwd=project_dir, capture_output=True, text=True, timeout=120)
        report.add("tests pass after resume", proc.returncode == 0,
                   (proc.stdout or proc.stderr or "").strip().splitlines()[-1]
                   if proc.returncode else "")

    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_resume.py <project_dir> <story_id>")
        sys.exit(2)
    sys.exit(print_report(validate_resume(sys.argv[1], sys.argv[2])))
