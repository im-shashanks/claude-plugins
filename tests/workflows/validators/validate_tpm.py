#!/usr/bin/env python3
"""Validators for /shaktra:tpm workflow.

Checks that TPM planning produces design docs, stories, sprint allocation,
and memory entries — with deep content validation per story-schema.md.
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
    check_field_nonempty,
    check_glob_matches,
    check_is_dir,
    check_is_file,
    check_list_min_length,
    check_valid_yaml,
    load_yaml_safe,
    print_report,
    validate_all_yaml_in_dir,
)

VALID_TIERS = ["trivial", "small", "medium", "large"]
VALID_SCOPES = [
    "bug_fix", "feature", "refactor", "config", "docs", "test",
    "performance", "security", "integration", "migration", "scaffold",
]
VALID_PRIORITIES = ["critical", "high", "medium", "low"]
VALID_STATUSES = ["planned", "in_progress", "done"]
STORY_POINTS = [1, 2, 3, 5, 8, 10]


def validate_tpm(project_dir: str, expect_hotfix: bool = False) -> ValidationReport:
    """Validate .shaktra/ state after /shaktra:tpm."""
    report = ValidationReport("/shaktra:tpm" + (" (hotfix)" if expect_hotfix else ""))
    shaktra = os.path.join(project_dir, ".shaktra")

    # --- Design docs ---
    designs_dir = os.path.join(shaktra, "designs")
    if check_is_dir(report, designs_dir, "designs/ exists"):
        if not expect_hotfix:
            design_files = check_glob_matches(
                report, designs_dir, "*-design.md", min_count=1,
                label="at least 1 design doc created",
            )
            for df in design_files:
                try:
                    content = Path(df).read_text()
                    has_content = len(content.strip()) > 50
                    report.add(
                        f"{Path(df).name} has content",
                        has_content,
                        f"only {len(content)} chars" if not has_content else "",
                    )
                except Exception as e:
                    report.add(f"{Path(df).name} readable", False, str(e))

    # --- Stories ---
    stories_dir = os.path.join(shaktra, "stories")
    if check_is_dir(report, stories_dir, "stories/ exists"):
        story_files = check_glob_matches(
            report, stories_dir, "ST-*.yml",
            min_count=1 if expect_hotfix else 2,
            label=f"at least {'1 story (hotfix)' if expect_hotfix else '2 stories'} created",
        )
        _validate_stories(report, story_files, expect_hotfix)

        # Check no .md story files (stories must be YAML)
        md_stories = list(Path(stories_dir).glob("ST-*.md"))
        report.add(
            "no .md story files (stories must be .yml)",
            len(md_stories) == 0,
            f"found {len(md_stories)} .md files: {[f.name for f in md_stories]}" if md_stories else "",
        )

    # --- Sprints ---
    sprints_path = os.path.join(shaktra, "sprints.yml")
    if check_is_file(report, sprints_path, "sprints.yml exists"):
        sprints_data = check_valid_yaml(report, sprints_path, "sprints.yml valid YAML")
        if sprints_data and not expect_hotfix:
            check_field_nonempty(
                report, sprints_data, "current_sprint",
                "current_sprint populated",
            )
        if sprints_data and expect_hotfix:
            # Hotfix should NOT create a sprint
            cs = sprints_data.get("current_sprint")
            report.add(
                "hotfix did not create a sprint",
                cs is None or cs == {},
                f"current_sprint is set: {cs}" if cs and cs != {} else "",
            )

    # --- Memory: principles (evidence memory-curator ran) ---
    principles_path = os.path.join(shaktra, "memory", "principles.yml")
    if check_is_file(report, principles_path, "principles.yml exists"):
        pr_data = check_valid_yaml(report, principles_path, "principles.yml valid YAML")
        if pr_data and not expect_hotfix:
            check_list_min_length(
                report, pr_data, "principles", 1,
                "principles.yml has at least 1 entry (memory-curator ran)",
            )
            # Validate principle entry structure
            principles = pr_data.get("principles", [])
            if principles and isinstance(principles, list):
                entry = principles[-1]
                for field in ["id", "text", "confidence", "source", "status"]:
                    has = isinstance(entry, dict) and field in entry
                    report.add(
                        f"latest principle has '{field}' field",
                        has,
                        f"missing from principle entry" if not has else "",
                    )

    # --- Memory: anti-patterns + procedures exist ---
    for mem_file in ["anti-patterns.yml", "procedures.yml"]:
        mp = os.path.join(shaktra, "memory", mem_file)
        if check_is_file(report, mp, f"{mem_file} exists"):
            check_valid_yaml(report, mp, f"{mem_file} valid YAML")

    # --- No YAML parse errors in stories ---
    validate_all_yaml_in_dir(report, stories_dir)

    return report


def _validate_stories(
    report: ValidationReport, story_files: list[str], expect_hotfix: bool,
) -> None:
    """Validate individual story files against story-schema.md."""
    for sf in story_files:
        fname = Path(sf).name
        data, err = load_yaml_safe(sf)
        if err:
            report.add(f"{fname} valid YAML", False, err)
            continue
        report.add(f"{fname} valid YAML", True)

        # --- Required fields for ALL tiers ---
        check_field_exists(report, data, "id", f"{fname}: 'id' exists")
        check_field_exists(report, data, "title", f"{fname}: 'title' exists")
        check_field_exists(report, data, "description", f"{fname}: 'description' exists")
        check_field_exists(report, data, "tier", f"{fname}: 'tier' exists")

        check_field_in(report, data, "tier", VALID_TIERS, f"{fname}: valid tier")

        # Title length check (≤100 chars per schema)
        title = data.get("title", "")
        if isinstance(title, str):
            report.add(
                f"{fname}: title ≤100 chars",
                len(title) <= 100,
                f"title is {len(title)} chars" if len(title) > 100 else "",
            )

        # Description non-empty
        desc = data.get("description", "")
        report.add(
            f"{fname}: description non-empty",
            bool(desc and str(desc).strip()),
            "description is empty" if not (desc and str(desc).strip()) else "",
        )

        # --- Hotfix-specific checks ---
        if expect_hotfix:
            check_field_equals(
                report, data, "tier", "trivial",
                f"{fname}: hotfix tier is trivial",
            )

        # --- Metadata (all tiers) ---
        if check_field_exists(report, data, "metadata", f"{fname}: metadata exists"):
            check_field_in(
                report, data, "metadata.priority", VALID_PRIORITIES,
                f"{fname}: valid priority",
            )
            check_field_in(
                report, data, "metadata.story_points", STORY_POINTS,
                f"{fname}: valid story_points",
            )
            check_field_in(
                report, data, "metadata.status", VALID_STATUSES,
                f"{fname}: valid status",
            )
            check_field_exists(
                report, data, "metadata.blocked_by",
                f"{fname}: blocked_by exists",
            )

        # --- Tier-dependent fields ---
        tier = data.get("tier", "")

        if tier in ("small", "medium", "large"):
            check_field_exists(report, data, "files", f"{fname}: files (≥ small)")
            check_field_exists(
                report, data, "acceptance_criteria",
                f"{fname}: acceptance_criteria (≥ small)",
            )

        if tier in ("medium", "large"):
            check_field_exists(report, data, "scope", f"{fname}: scope (≥ medium)")
            if "scope" in (data or {}):
                check_field_in(
                    report, data, "scope", VALID_SCOPES,
                    f"{fname}: valid scope",
                )
            check_field_exists(
                report, data, "test_specs", f"{fname}: test_specs (≥ medium)",
            )
            check_field_exists(
                report, data, "interfaces", f"{fname}: interfaces (≥ medium)",
            )
            check_field_exists(
                report, data, "io_examples", f"{fname}: io_examples (≥ medium)",
            )
            check_field_exists(
                report, data, "error_handling", f"{fname}: error_handling (≥ medium)",
            )

        if tier == "large":
            check_field_exists(
                report, data, "edge_cases", f"{fname}: edge_cases (large)",
            )
            check_field_exists(
                report, data, "feature_flags", f"{fname}: feature_flags (large)",
            )

        # --- Size limits (all tiers) ---
        meta = data.get("metadata", {}) if isinstance(data, dict) else {}
        points = meta.get("story_points", 0) if isinstance(meta, dict) else 0
        if isinstance(points, (int, float)):
            report.add(
                f"{fname}: story_points ≤ 10",
                points <= 10,
                f"got {points}" if points > 10 else "",
            )

        files_list = data.get("files", []) if isinstance(data, dict) else []
        if isinstance(files_list, list) and tier in ("small", "medium", "large"):
            report.add(
                f"{fname}: files ≤ 3",
                len(files_list) <= 3,
                f"got {len(files_list)}" if len(files_list) > 3 else "",
            )


def validate_tpm_hotfix(project_dir: str) -> ValidationReport:
    """Validate .shaktra/ state after /shaktra:tpm hotfix route."""
    return validate_tpm(project_dir, expect_hotfix=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("project_dir")
    p.add_argument("--hotfix", action="store_true")
    args = p.parse_args()
    r = validate_tpm(args.project_dir, expect_hotfix=args.hotfix)
    sys.exit(print_report(r))
