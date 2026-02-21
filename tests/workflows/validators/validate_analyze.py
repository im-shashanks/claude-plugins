#!/usr/bin/env python3
"""Validators for /shaktra:analyze workflow.

Checks that brownfield analysis produces manifest updates and
dimension artifacts.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import (
    ValidationReport,
    check_field_exists,
    check_field_in,
    check_glob_matches,
    check_is_dir,
    check_is_file,
    check_valid_yaml,
    load_yaml_safe,
    print_report,
)

DIMENSION_FILES = [
    "structure.yml", "domain-model.yml", "entry-points.yml",
    "practices.yml", "dependencies.yml", "tech-debt.yml",
    "data-flows.yml", "critical-paths.yml", "git-intelligence.yml",
]


def validate_analyze(project_dir: str) -> ValidationReport:
    """Validate .shaktra/ state after /shaktra:analyze."""
    report = ValidationReport("/shaktra:analyze")
    shaktra = os.path.join(project_dir, ".shaktra")
    analysis = os.path.join(shaktra, "analysis")

    if not check_is_dir(report, analysis, "analysis/ exists"):
        return report

    # --- Manifest ---
    manifest_path = os.path.join(analysis, "manifest.yml")
    if check_is_file(report, manifest_path, "manifest.yml exists"):
        data = check_valid_yaml(report, manifest_path, "manifest.yml valid YAML")
        if data:
            check_field_in(
                report, data, "status",
                ["in_progress", "complete", "partial"],
                "manifest status progressed",
            )
            # Check at least some dimensions completed
            dims = data.get("stages", {}).get("dimensions", {})
            completed = 0
            for key, dim in dims.items():
                if isinstance(dim, dict) and dim.get("status") == "complete":
                    completed += 1
            report.add(
                "at least 3 dimensions completed",
                completed >= 3,
                f"found {completed} completed dimensions",
            )

    # --- Dimension artifacts ---
    found_artifacts = 0
    for dim_file in DIMENSION_FILES:
        path = os.path.join(analysis, dim_file)
        if os.path.isfile(path):
            found_artifacts += 1
            check_valid_yaml(report, path, f"{dim_file} valid YAML")

    report.add(
        "at least 3 dimension artifacts created",
        found_artifacts >= 3,
        f"found {found_artifacts} of {len(DIMENSION_FILES)}",
    )

    # --- Memory ---
    principles_path = os.path.join(shaktra, "memory", "principles.yml")
    if os.path.isfile(principles_path):
        check_valid_yaml(report, principles_path, "principles.yml valid YAML")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_analyze.py <project_dir>")
        sys.exit(2)
    r = validate_analyze(sys.argv[1])
    sys.exit(print_report(r))
