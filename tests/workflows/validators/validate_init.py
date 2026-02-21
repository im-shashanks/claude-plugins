#!/usr/bin/env python3
"""Validators for /shaktra:init workflow.

Checks that .shaktra/ directory is correctly initialized with all
expected files, subdirectories, and settings populated.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow imports from parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import (
    ValidationReport,
    check_exists,
    check_field_equals,
    check_field_exists,
    check_is_dir,
    check_is_file,
    check_valid_yaml,
    print_report,
)


def validate_init(
    project_dir: str,
    expected_name: str = "",
    expected_type: str = "",
    expected_language: str = "",
) -> ValidationReport:
    """Validate .shaktra/ state after /shaktra:init."""
    report = ValidationReport("/shaktra:init")
    shaktra = os.path.join(project_dir, ".shaktra")

    # --- Core directory ---
    if not check_is_dir(report, shaktra, ".shaktra/ directory exists"):
        return report

    # --- Settings ---
    settings_path = os.path.join(shaktra, "settings.yml")
    if check_is_file(report, settings_path, "settings.yml exists"):
        data = check_valid_yaml(report, settings_path, "settings.yml valid YAML")
        if data:
            if expected_name:
                check_field_equals(report, data, "project.name", expected_name)
            else:
                check_field_exists(report, data, "project.name")
            if expected_type:
                check_field_equals(report, data, "project.type", expected_type)
            else:
                check_field_exists(report, data, "project.type")
            if expected_language:
                check_field_equals(report, data, "project.language", expected_language)
            else:
                check_field_exists(report, data, "project.language")
            # Default thresholds
            check_field_exists(report, data, "tdd.coverage_threshold",
                               "tdd.coverage_threshold exists")
            check_field_exists(report, data, "quality.p1_threshold",
                               "quality.p1_threshold exists")
            check_field_exists(report, data, "sprints.enabled",
                               "sprints.enabled exists")

    # --- Subdirectories ---
    for subdir in ["memory", "stories", "designs", "analysis"]:
        check_is_dir(report, os.path.join(shaktra, subdir), f"{subdir}/ exists")

    # --- Memory templates ---
    principles = os.path.join(shaktra, "memory", "principles.yml")
    if check_is_file(report, principles, "principles.yml exists"):
        check_valid_yaml(report, principles, "principles.yml valid YAML")

    anti_patterns = os.path.join(shaktra, "memory", "anti-patterns.yml")
    if check_is_file(report, anti_patterns, "anti-patterns.yml exists"):
        check_valid_yaml(report, anti_patterns, "anti-patterns.yml valid YAML")

    procedures = os.path.join(shaktra, "memory", "procedures.yml")
    if check_is_file(report, procedures, "procedures.yml exists"):
        check_valid_yaml(report, procedures, "procedures.yml valid YAML")

    # --- Sprints ---
    sprints = os.path.join(shaktra, "sprints.yml")
    if check_is_file(report, sprints, "sprints.yml exists"):
        check_valid_yaml(report, sprints, "sprints.yml valid YAML")

    # --- Analysis manifest ---
    manifest = os.path.join(shaktra, "analysis", "manifest.yml")
    if check_is_file(report, manifest, "analysis/manifest.yml exists"):
        check_valid_yaml(report, manifest, "manifest.yml valid YAML")

    # --- CLAUDE.md files ---
    check_is_file(report, os.path.join(shaktra, "CLAUDE.md"),
                  ".shaktra/CLAUDE.md exists")
    check_is_file(report, os.path.join(project_dir, "CLAUDE.md"),
                  "project CLAUDE.md exists")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_init.py <project_dir> [name] [type] [language]")
        sys.exit(2)
    proj = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else ""
    ptype = sys.argv[3] if len(sys.argv) > 3 else ""
    lang = sys.argv[4] if len(sys.argv) > 4 else ""
    r = validate_init(proj, name, ptype, lang)
    sys.exit(print_report(r))
