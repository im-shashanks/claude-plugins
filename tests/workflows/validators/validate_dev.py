#!/usr/bin/env python3
"""Validators for /shaktra:dev workflow.

Checks handoff.yml phase transitions, test/code creation, coverage,
and memory capture after story development.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import (
    ValidationReport,
    check_field_equals,
    check_field_exists,
    check_field_gte,
    check_field_in,
    check_field_nonempty,
    check_glob_matches,
    check_is_dir,
    check_is_file,
    check_list_min_length,
    check_valid_yaml,
    load_yaml_safe,
    print_report,
)

VALID_PHASES = ["pending", "plan", "tests", "code", "quality", "complete", "failed"]
EXPECTED_PHASE_ORDER = ["plan", "tests", "code"]  # minimum prefix


def validate_dev(project_dir: str, story_id: str) -> ValidationReport:
    """Validate .shaktra/ and project state after /shaktra:dev."""
    report = ValidationReport(f"/shaktra:dev ({story_id})")
    shaktra = os.path.join(project_dir, ".shaktra")

    # --- Handoff file ---
    story_dir = os.path.join(shaktra, "stories", story_id)
    handoff_path = os.path.join(story_dir, "handoff.yml")

    if not check_is_file(report, handoff_path, "handoff.yml exists"):
        report.add("handoff.yml required for remaining checks", False,
                    "cannot continue without handoff.yml")
        return report

    data = check_valid_yaml(report, handoff_path, "handoff.yml valid YAML")
    if not data:
        return report

    # --- Story ID match ---
    check_field_equals(report, data, "story_id", story_id)

    # --- Phase progression ---
    check_field_in(
        report, data, "current_phase", VALID_PHASES,
        "current_phase is valid",
    )

    # Should have progressed beyond pending
    current = data.get("current_phase", "pending")
    report.add(
        "current_phase beyond pending",
        current != "pending",
        f"still pending" if current == "pending" else "",
    )

    # Completed phases
    check_field_nonempty(report, data, "completed_phases",
                         "completed_phases non-empty")
    completed = data.get("completed_phases", [])
    if isinstance(completed, list) and len(completed) >= 1:
        # Check ordering is a valid prefix of the expected sequence
        full_sequence = ["plan", "tests", "code", "quality"]
        valid_prefix = True
        for i, phase in enumerate(completed):
            if i >= len(full_sequence) or phase != full_sequence[i]:
                valid_prefix = False
                break
        report.add(
            "completed_phases in correct order",
            valid_prefix,
            f"got {completed}" if not valid_prefix else "",
        )

    # --- Plan summary ---
    check_field_nonempty(report, data, "plan_summary", "plan_summary populated")
    check_field_exists(report, data, "plan_summary.components",
                       "plan_summary has components")
    check_field_exists(report, data, "plan_summary.test_plan",
                       "plan_summary has test_plan")

    # --- Implementation plan ---
    impl_plan = os.path.join(story_dir, "implementation_plan.md")
    check_is_file(report, impl_plan, "implementation_plan.md created")

    # --- Test creation ---
    if "tests" in completed or current in ("code", "quality", "complete"):
        check_field_exists(report, data, "test_summary", "test_summary exists")
        check_field_gte(report, data, "test_summary.test_count", 1,
                        "at least 1 test created")
        check_field_exists(report, data, "test_summary.test_files",
                           "test_files listed")

    # --- Code creation ---
    if "code" in completed or current in ("quality", "complete"):
        check_field_exists(report, data, "code_summary", "code_summary exists")
        check_field_equals(report, data, "code_summary.all_tests_green", True,
                           "all tests green")
        check_field_exists(report, data, "code_summary.coverage",
                           "coverage recorded")
        # Accept either files_modified or files_created
        cs = data.get("code_summary", {}) or {}
        has_files = bool(cs.get("files_modified")) or bool(cs.get("files_created"))
        report.add("code files listed", has_files,
                    "no files_modified or files_created in code_summary"
                    if not has_files else "")

    # --- Completion checks ---
    if current == "complete":
        check_field_equals(report, data, "memory_captured", True,
                           "memory captured before completion")
        # Check lessons updated
        lessons_path = os.path.join(shaktra, "memory", "lessons.yml")
        if check_is_file(report, lessons_path, "lessons.yml exists"):
            lessons = check_valid_yaml(report, lessons_path,
                                       "lessons.yml valid YAML")
            if lessons:
                check_field_nonempty(report, lessons, "lessons",
                                     "at least 1 lesson recorded")

    # --- Feature branch (check git) ---
    _check_feature_branch(report, project_dir, story_id)

    return report


def _check_feature_branch(
    report: ValidationReport, project_dir: str, story_id: str,
) -> None:
    """Check that we're on a feature branch (not main/master)."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=project_dir,
        )
        branch = result.stdout.strip()
        on_feature = branch not in ("main", "master", "")
        report.add(
            "on feature branch",
            on_feature,
            f"on '{branch}'" if not on_feature else f"branch: {branch}",
        )
    except Exception as e:
        report.add("git branch check", False, f"git error: {e}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_dev.py <project_dir> <story_id>")
        sys.exit(2)
    r = validate_dev(sys.argv[1], sys.argv[2])
    sys.exit(print_report(r))
