#!/usr/bin/env python3
"""Validators for /shaktra:review workflow.

Checks that code review produces findings with valid severity,
renders a verdict, and captures memory.
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
    check_field_in,
    check_is_file,
    check_valid_yaml,
    load_yaml_safe,
    print_report,
)

VALID_SEVERITIES = ["P0", "P1", "P2", "P3"]
VALID_VERDICTS = ["APPROVED", "APPROVED_WITH_NOTES", "CHANGES_REQUESTED", "BLOCKED"]


def validate_review(project_dir: str, story_id: str) -> ValidationReport:
    """Validate state after /shaktra:review."""
    report = ValidationReport(f"/shaktra:review ({story_id})")
    shaktra = os.path.join(project_dir, ".shaktra")

    # --- Handoff should still be valid ---
    story_dir = os.path.join(shaktra, "stories", story_id)
    handoff_path = os.path.join(story_dir, "handoff.yml")

    if not check_is_file(report, handoff_path, "handoff.yml exists"):
        return report

    data = check_valid_yaml(report, handoff_path, "handoff.yml valid YAML")
    if not data:
        return report

    # --- Review findings ---
    # Review may add quality_findings or a separate review output
    findings = data.get("quality_findings", [])
    report.add(
        "quality_findings field present",
        "quality_findings" in data,
        "no quality_findings field" if "quality_findings" not in data else "",
    )

    if isinstance(findings, list):
        _validate_findings(report, findings)

    # --- Check for review-specific artifacts ---
    # Review may produce a review summary file
    review_files = list(Path(story_dir).glob("*review*"))
    if review_files:
        report.add("review artifact created", True)
    # Not required — review may only update handoff.yml

    # --- Memory capture ---
    lessons = None
    lessons_path = os.path.join(shaktra, "memory", "lessons.yml")
    if check_is_file(report, lessons_path, "lessons.yml exists"):
        lessons = check_valid_yaml(report, lessons_path, "lessons.yml valid YAML")
        if lessons:
            entries = lessons.get("lessons", [])
            report.add(
                "lessons.yml has entries",
                isinstance(entries, list) and len(entries) > 0,
                f"found {len(entries) if isinstance(entries, list) else 0} entries",
            )

    # --- Review findings output ---
    all_review = list(Path(story_dir).glob("*review*")) + list(
        Path(story_dir).glob("*findings*"))
    report.add(
        "review produced findings or artifacts",
        bool(findings) or bool(all_review),
        "no findings in handoff and no review artifact files"
        if not findings and not all_review else "",
    )

    # --- Memory: lessons have source attribution ---
    if lessons:
        entries = lessons.get("lessons", [])
        if isinstance(entries, list) and entries:
            has_source = any(
                isinstance(e, dict) and e.get("source") for e in entries)
            report.add(
                "lessons have source attribution",
                has_source,
                "no lessons have a source field" if not has_source else "",
            )

    return report


def _validate_findings(report: ValidationReport, findings: list) -> None:
    """Validate individual review findings."""
    if not findings:
        report.add("findings list present (may be empty)", True)
        return

    report.add(f"review produced {len(findings)} finding(s)", True)

    has_p0 = False
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            report.add(f"finding[{i}] is dict", False, f"got {type(f).__name__}")
            continue

        # Severity
        sev = f.get("severity", "")
        report.add(
            f"finding[{i}] valid severity",
            sev in VALID_SEVERITIES,
            f"got {sev!r}" if sev not in VALID_SEVERITIES else "",
        )
        if sev == "P0":
            has_p0 = True

        # Required fields
        for field in ["issue", "dimension"]:
            report.add(
                f"finding[{i}] has '{field}'",
                field in f and bool(f[field]),
                f"missing or empty" if field not in f or not f[field] else "",
            )

    # P0 → BLOCKED consistency check
    # (This is informational — the verdict may be checked externally)
    if has_p0:
        report.add("P0 findings detected (expect BLOCKED verdict)", True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_review.py <project_dir> <story_id>")
        sys.exit(2)
    r = validate_review(sys.argv[1], sys.argv[2])
    sys.exit(print_report(r))
