#!/usr/bin/env python3
"""Validators for /shaktra:bugfix workflow.

Checks that bug diagnosis was produced and a fix was implemented.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import (
    ValidationReport,
    check_exists,
    check_is_dir,
    check_is_file,
    print_report,
)


def validate_bugfix(project_dir: str) -> ValidationReport:
    """Validate project state after /shaktra:bugfix."""
    report = ValidationReport("/shaktra:bugfix")

    # --- Source files modified ---
    src_file = os.path.join(project_dir, "src", "calculator.py")
    if check_is_file(report, src_file, "calculator.py exists"):
        content = Path(src_file).read_text()
        # Check the fix addresses zero division
        has_fix = any(
            kw in content.lower()
            for kw in ["valueerror", "zero", "if b == 0", "if not b", "b == 0"]
        )
        report.add(
            "fix addresses zero division",
            has_fix,
            "no zero-division handling found in source" if not has_fix else "",
        )

    # --- Tests pass ---
    test_file = os.path.join(project_dir, "tests", "test_calculator.py")
    check_is_file(report, test_file, "test file exists")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True, text=True, timeout=30,
            cwd=project_dir,
        )
        tests_pass = result.returncode == 0
        report.add(
            "tests pass after fix",
            tests_pass,
            result.stdout.split("\n")[-2] if not tests_pass else "",
        )
    except Exception as e:
        report.add("tests pass after fix", False, f"pytest error: {e}")

    # --- Shaktra state ---
    shaktra = os.path.join(project_dir, ".shaktra")
    if os.path.isdir(shaktra):
        # Bugfix may create a story or update memory
        stories = list(Path(shaktra).glob("stories/ST-*.yml"))
        report.add(
            "bugfix story or artifact created",
            len(stories) > 0 or os.path.isfile(
                os.path.join(shaktra, "memory", "lessons.yml")),
            "no stories or memory updates found",
        )

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_bugfix.py <project_dir>")
        sys.exit(2)
    r = validate_bugfix(sys.argv[1])
    sys.exit(print_report(r))
