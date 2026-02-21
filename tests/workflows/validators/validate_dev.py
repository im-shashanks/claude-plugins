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

    # --- Observations (written during workflow) ---
    obs_path = os.path.join(story_dir, ".observations.yml")
    obs_exists = os.path.isfile(obs_path)
    report.add("observations file created", obs_exists,
               "no .observations.yml in story dir" if not obs_exists else "")
    if obs_exists:
        obs_data = check_valid_yaml(report, obs_path, ".observations.yml valid YAML")
        if obs_data:
            obs_list = obs_data.get("observations", [])
            report.add(
                "observations written by agents",
                isinstance(obs_list, list) and len(obs_list) > 0,
                f"found {len(obs_list) if isinstance(obs_list, list) else 0} observations",
            )
            # Validate observation entry structure
            if isinstance(obs_list, list) and obs_list:
                entry = obs_list[0]
                for field in ["id", "agent", "phase", "type", "text"]:
                    has = isinstance(entry, dict) and field in entry
                    report.add(
                        f"observation has '{field}' field",
                        has,
                        "missing from observation entry" if not has else "",
                    )

    # --- Briefing (generated at workflow start) ---
    briefing_path = os.path.join(story_dir, ".briefing.yml")
    briefing_exists = os.path.isfile(briefing_path)
    report.add("briefing file generated", briefing_exists,
               "no .briefing.yml in story dir" if not briefing_exists else "")
    if briefing_exists:
        br_data = check_valid_yaml(report, briefing_path, ".briefing.yml valid YAML")
        if br_data:
            # Verify seeded principles surfaced in briefing
            br_principles = br_data.get("relevant_principles", [])
            if isinstance(br_principles, list):
                seeded_ids = {p.get("id") for p in br_principles
                              if isinstance(p, dict)}
                has_pr001 = "PR-001" in seeded_ids
                has_pr002 = "PR-002" in seeded_ids
                report.add(
                    "briefing includes seeded PR-001 (email validation)",
                    has_pr001,
                    f"PR-001 not in briefing (found: {seeded_ids})"
                    if not has_pr001 else "",
                )
                report.add(
                    "briefing includes seeded PR-002 (domain exceptions)",
                    has_pr002,
                    f"PR-002 not in briefing (found: {seeded_ids})"
                    if not has_pr002 else "",
                )

            # Verify seeded anti-pattern surfaced in briefing
            br_aps = br_data.get("relevant_anti_patterns", [])
            if isinstance(br_aps, list):
                ap_ids = {a.get("id") for a in br_aps if isinstance(a, dict)}
                has_ap001 = "AP-001" in ap_ids
                report.add(
                    "briefing includes seeded AP-001 (raw db errors)",
                    has_ap001,
                    f"AP-001 not in briefing (found: {ap_ids})"
                    if not has_ap001 else "",
                )

    # --- Completion checks ---
    if current == "complete":
        check_field_equals(report, data, "memory_captured", True,
                           "memory captured before completion")
        # Check principles updated (evidence memory-curator ran)
        principles_path = os.path.join(shaktra, "memory", "principles.yml")
        if check_is_file(report, principles_path, "principles.yml exists"):
            pr_data = check_valid_yaml(report, principles_path,
                                       "principles.yml valid YAML")
            if pr_data:
                pr_list = pr_data.get("principles", [])
                report.add(
                    "principles created by memory-curator",
                    isinstance(pr_list, list) and len(pr_list) > 0,
                    f"found {len(pr_list) if isinstance(pr_list, list) else 0} principles",
                )
                # Validate principle entry structure
                if isinstance(pr_list, list) and pr_list:
                    entry = pr_list[0]
                    for field in ["id", "text", "confidence", "source"]:
                        has = isinstance(entry, dict) and field in entry
                        report.add(
                            f"principle has '{field}' field",
                            has,
                            "missing from principle entry" if not has else "",
                        )
                    # Check seeded principles survived and were reinforced
                    pr_by_id = {p["id"]: p for p in pr_list
                                if isinstance(p, dict) and "id" in p}
                    report.add(
                        "seeded PR-001 still present after consolidation",
                        "PR-001" in pr_by_id,
                        "PR-001 missing from principles.yml" if "PR-001" not in pr_by_id else "",
                    )
                    report.add(
                        "seeded PR-002 still present after consolidation",
                        "PR-002" in pr_by_id,
                        "PR-002 missing from principles.yml" if "PR-002" not in pr_by_id else "",
                    )
                    # New principles beyond the 2 seeded ones = curator synthesized new knowledge
                    new_count = len(pr_list) - 2  # subtract seeded
                    report.add(
                        "memory-curator created new principles",
                        new_count > 0,
                        f"only seeded principles remain (total: {len(pr_list)})"
                        if new_count <= 0 else f"{new_count} new principle(s) created",
                    )
        # Check anti-patterns and procedures exist (may be empty)
        for mem_file in ["anti-patterns.yml", "procedures.yml"]:
            mp = os.path.join(shaktra, "memory", mem_file)
            if check_is_file(report, mp, f"{mem_file} exists"):
                check_valid_yaml(report, mp, f"{mem_file} valid YAML")

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
