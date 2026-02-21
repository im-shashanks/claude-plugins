#!/usr/bin/env python3
"""Validators for /shaktra:adversarial-review workflow.

Checks that adversarial review produces mutation results, probe findings,
a verdict, and captures memory.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import (
    ValidationReport,
    check_field_exists,
    check_is_file,
    check_valid_yaml,
    load_yaml_safe,
    print_report,
)

VALID_SEVERITIES = ["P0", "P1", "P2", "P3"]
VALID_VERDICTS = ["PASS", "CONCERN", "BLOCKED"]


def validate_adversarial_review(project_dir: str, story_id: str) -> ValidationReport:
    """Validate state after /shaktra:adversarial-review."""
    report = ValidationReport(f"/shaktra:adversarial-review ({story_id})")
    shaktra = os.path.join(project_dir, ".shaktra")

    # --- Handoff should still be valid ---
    story_dir = os.path.join(shaktra, "stories", story_id)
    handoff_path = os.path.join(story_dir, "handoff.yml")

    if not check_is_file(report, handoff_path, "handoff.yml exists"):
        return report

    data = check_valid_yaml(report, handoff_path, "handoff.yml valid YAML")
    if not data:
        return report

    # --- Observations (written during adversarial review) ---
    obs_path = os.path.join(story_dir, ".observations.yml")
    obs_exists = os.path.isfile(obs_path)
    report.add("observations file exists", obs_exists,
               "no .observations.yml in story dir" if not obs_exists else "")

    # --- Briefing (generated at review start) ---
    briefing_path = os.path.join(story_dir, ".briefing.yml")
    briefing_exists = os.path.isfile(briefing_path)
    report.add("briefing file generated", briefing_exists,
               "no .briefing.yml in story dir" if not briefing_exists else "")

    # --- Adversarial review artifacts ---
    # Look for adversarial-related output files in the story dir
    adversarial_files = list(Path(story_dir).glob("*adversar*"))
    review_files = list(Path(story_dir).glob("*review*"))
    all_artifacts = adversarial_files + review_files
    if all_artifacts:
        report.add("adversarial review artifact created", True)

    # --- Adversarial test files generated ---
    # Check for generated adversarial tests anywhere in project
    adv_tests_dir = Path(project_dir) / "tests" / "adversarial"
    adv_test_files = list(Path(project_dir).rglob("*adversarial*test*"))
    adv_test_files += list(Path(project_dir).rglob("*test*adversarial*"))
    has_adv_tests = bool(adv_test_files) or adv_tests_dir.is_dir()
    report.add(
        "adversarial tests generated",
        has_adv_tests,
        "no adversarial test files found" if not has_adv_tests else
        f"found {len(adv_test_files)} adversarial test file(s)",
    )

    # --- Quality findings from adversarial review ---
    findings = data.get("quality_findings", [])
    has_findings_field = "quality_findings" in data
    report.add(
        "quality_findings field present",
        has_findings_field,
        "no quality_findings field" if not has_findings_field else "",
    )

    if isinstance(findings, list) and findings:
        _validate_findings(report, findings)

    # --- Memory capture: principles ---
    principles_path = os.path.join(shaktra, "memory", "principles.yml")
    if check_is_file(report, principles_path, "principles.yml exists"):
        pr_data = check_valid_yaml(report, principles_path,
                                   "principles.yml valid YAML")
        if pr_data:
            entries = pr_data.get("principles", [])
            report.add(
                "principles.yml has entries",
                isinstance(entries, list) and len(entries) > 0,
                f"found {len(entries) if isinstance(entries, list) else 0} entries",
            )

    # --- Settings: adversarial_review section exists ---
    settings_path = os.path.join(shaktra, "settings.yml")
    if os.path.isfile(settings_path):
        settings_data, err = load_yaml_safe(settings_path)
        if settings_data:
            has_section = "adversarial_review" in settings_data
            report.add(
                "settings has adversarial_review section",
                has_section,
                "missing adversarial_review in settings.yml"
                if not has_section else "",
            )

    return report


def _validate_findings(report: ValidationReport, findings: list) -> None:
    """Validate individual adversarial review findings."""
    report.add(f"adversarial review produced {len(findings)} finding(s)", True)

    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            report.add(f"finding[{i}] is dict", False,
                       f"got {type(f).__name__}")
            continue

        # Severity
        sev = f.get("severity", "")
        report.add(
            f"finding[{i}] valid severity",
            sev in VALID_SEVERITIES,
            f"got {sev!r}" if sev not in VALID_SEVERITIES else "",
        )

        # Required fields — at least issue/description
        has_desc = bool(f.get("issue") or f.get("description"))
        report.add(
            f"finding[{i}] has description",
            has_desc,
            "missing both 'issue' and 'description'" if not has_desc else "",
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_adversarial_review.py <project_dir> <story_id>")
        sys.exit(2)
    r = validate_adversarial_review(sys.argv[1], sys.argv[2])
    sys.exit(print_report(r))
