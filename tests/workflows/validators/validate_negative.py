#!/usr/bin/env python3
"""Validators for negative (error-path) tests.

Generic validators that check error conditions were detected properly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import ValidationReport, check_is_file, print_report


def validate_error_detected(
    project_dir: str, expected_patterns: list[str],
) -> ValidationReport:
    """Check that expected error patterns appear in test log or output."""
    report = ValidationReport("negative test (error detection)")

    log_path = os.path.join(project_dir, ".shaktra-test.log")
    content = ""
    if os.path.isfile(log_path):
        content = Path(log_path).read_text().lower()

    # Also check any handoff files for error info
    shaktra = os.path.join(project_dir, ".shaktra")
    for root, dirs, files in os.walk(shaktra):
        for f in files:
            if f.endswith((".yml", ".yaml", ".md", ".log")):
                try:
                    content += "\n" + Path(os.path.join(root, f)).read_text().lower()
                except Exception:
                    pass

    for pattern in expected_patterns:
        found = pattern.lower() in content
        report.add(
            f"error pattern detected: '{pattern}'",
            found,
            f"pattern not found in logs/artifacts" if not found else "",
        )

    return report


def validate_no_handoff(
    project_dir: str, story_id: str,
) -> ValidationReport:
    """Confirm no handoff.yml was created (pre-flight blocked correctly)."""
    report = ValidationReport(f"negative test (no handoff for {story_id})")

    handoff_path = os.path.join(
        project_dir, ".shaktra", "stories", story_id, "handoff.yml"
    )
    exists = os.path.isfile(handoff_path)
    report.add(
        "no handoff created (pre-flight blocked)",
        not exists,
        "handoff.yml exists — pre-flight did not block" if exists else "",
    )

    return report


def validate_no_progression(
    project_dir: str, story_id: str,
) -> ValidationReport:
    """Confirm handoff stayed at initial state (no progression past pre-flight)."""
    report = ValidationReport(f"negative test (no progression for {story_id})")

    handoff_path = os.path.join(
        project_dir, ".shaktra", "stories", story_id, "handoff.yml"
    )

    if not os.path.isfile(handoff_path):
        report.add("no handoff (blocked at pre-flight)", True)
        return report

    # If handoff exists, check it hasn't progressed
    import yaml
    try:
        with open(handoff_path) as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        report.add("handoff readable", False, "failed to parse")
        return report

    phase = data.get("current_phase", "")
    completed = data.get("completed_phases", [])

    report.add(
        "handoff did not progress past plan",
        phase in ("", "pending", "plan") and len(completed) <= 1,
        f"current_phase={phase}, completed={completed}",
    )

    return report


# CLI
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_negative.py <project_dir> <check_type> [args...]")
        print("  check_type: error_detected|no_handoff|no_progression")
        sys.exit(2)

    project_dir = sys.argv[1]
    check_type = sys.argv[2]

    if check_type == "no_handoff":
        story_id = sys.argv[3] if len(sys.argv) > 3 else "UNKNOWN"
        r = validate_no_handoff(project_dir, story_id)
    elif check_type == "no_progression":
        story_id = sys.argv[3] if len(sys.argv) > 3 else "UNKNOWN"
        r = validate_no_progression(project_dir, story_id)
    elif check_type == "error_detected":
        patterns = sys.argv[3:]
        r = validate_error_detected(project_dir, patterns)
    else:
        print(f"Unknown check type: {check_type}")
        sys.exit(2)

    sys.exit(print_report(r))
