#!/usr/bin/env python3
"""Validators for /shaktra:incident workflow.

Checks that incident response produces post-mortem artifacts, detection gap
analysis, runbook, observations, and captures memory.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import (
    check_no_sidecars,
    ValidationReport,
    check_is_dir,
    check_is_file,
    check_valid_yaml,
    check_field_exists,
    check_list_min_length,
    load_yaml_safe,
    print_report,
)

VALID_PRIORITIES = ["P0", "P1", "P2", "P3"]


def validate_incident(project_dir: str, bug_id: str) -> ValidationReport:
    """Validate state after /shaktra:incident post-mortem."""
    report = ValidationReport(f"/shaktra:incident ({bug_id})")
    shaktra = os.path.join(project_dir, ".shaktra")
    incident_dir = os.path.join(shaktra, "incidents", bug_id)

    # --- 1. Incident directory exists ---
    if not check_is_dir(report, incident_dir, "incident directory exists"):
        return report

    # --- 2. Post-mortem artifact exists ---
    postmortem_path = os.path.join(incident_dir, "postmortem.yml")
    if not check_is_file(report, postmortem_path, "postmortem.yml exists"):
        return report

    # --- 3. Post-mortem valid YAML ---
    raw_data = check_valid_yaml(report, postmortem_path, "postmortem.yml valid YAML")
    if not raw_data:
        return report

    # Schema nests fields under a top-level "postmortem" key
    data = raw_data.get("postmortem", raw_data)

    # --- 4. Post-mortem has timeline ---
    check_list_min_length(
        report, data, "timeline", 1,
        "postmortem has timeline (non-empty list)",
    )

    # --- 5. Post-mortem has root_cause_chain.primary ---
    check_field_exists(
        report, data, "root_cause_chain.primary",
        "postmortem has root_cause_chain.primary",
    )

    # --- 6. Post-mortem has impact ---
    check_field_exists(
        report, data, "impact",
        "postmortem has impact section",
    )

    # --- 7. Post-mortem has action_items ---
    check_list_min_length(
        report, data, "action_items", 1,
        "postmortem has action_items (non-empty list)",
    )

    # --- 8. Action items have valid priorities ---
    action_items = data.get("action_items", [])
    if isinstance(action_items, list) and action_items:
        _validate_action_items(report, action_items)

    # --- 9. Detection gap artifact exists ---
    detection_path = os.path.join(incident_dir, "detection-gap.yml")
    detection_exists = os.path.isfile(detection_path)
    report.add(
        "detection-gap.yml exists",
        detection_exists,
        "no detection-gap.yml (auto_detection_gap may be off)"
        if not detection_exists else "",
    )

    # --- 10. Detection gap has gates_passed ---
    if detection_exists:
        raw_det = check_valid_yaml(
            report, detection_path, "detection-gap.yml valid YAML",
        )
        if raw_det:
            # Schema nests fields under "detection_gap" key
            det_data = raw_det.get("detection_gap", raw_det)
            check_list_min_length(
                report, det_data, "gates_passed", 1,
                "detection gap has gates_passed (non-empty list)",
            )

    # --- 11. Runbook artifact exists ---
    runbook_path = os.path.join(incident_dir, "runbook.yml")
    runbook_exists = os.path.isfile(runbook_path)
    report.add(
        "runbook.yml exists",
        runbook_exists,
        "no runbook.yml (runbook_auto_generate may be off)"
        if not runbook_exists else "",
    )

    # --- 12. No retired sidecar mechanisms ---
    check_no_sidecars(report, project_dir)

    # --- 13. Memory capture: any store grew ---
    # Incident learnings legitimately land in ANY store — a failure pattern
    # becomes an anti-pattern, a detection gap becomes a procedure, a broader
    # lesson becomes a principle. Require capture in at least one store.
    store_keys = {
        "principles.yml": "principles",
        "anti-patterns.yml": "anti_patterns",
        "procedures.yml": "procedures",
    }
    total_entries = 0
    per_store = {}
    for fname, key in store_keys.items():
        path = os.path.join(shaktra, "memory", fname)
        data, _ = load_yaml_safe(path)
        n = 0
        if isinstance(data, dict) and isinstance(data.get(key), list):
            n = len(data[key])
        per_store[fname] = n
        total_entries += n
    report.add(
        "incident learnings captured to memory (any store)",
        total_entries > 0,
        f"no memory entries in any store ({per_store})" if total_entries == 0 else "",
    )

    # --- 14. Settings has incident section ---
    settings_path = os.path.join(shaktra, "settings.yml")
    if os.path.isfile(settings_path):
        settings_data, err = load_yaml_safe(settings_path)
        if settings_data:
            has_section = "incident" in settings_data
            report.add(
                "settings has incident section",
                has_section,
                "missing incident in settings.yml"
                if not has_section else "",
            )

    return report


def _validate_action_items(report: ValidationReport, items: list) -> None:
    """Validate individual action items have valid priorities."""
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            report.add(f"action_item[{i}] is dict", False,
                       f"got {type(item).__name__}")
            continue

        priority = item.get("priority", "")
        report.add(
            f"action_item[{i}] valid priority",
            priority in VALID_PRIORITIES,
            f"got {priority!r}" if priority not in VALID_PRIORITIES else "",
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_incident.py <project_dir> <bug_id>")
        sys.exit(2)
    r = validate_incident(sys.argv[1], sys.argv[2])
    sys.exit(print_report(r))
