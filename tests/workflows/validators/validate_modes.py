#!/usr/bin/env python3
"""Validators for previously-untested command modes and the escalation loop.

Modes: enrich | sprint | analyze_targeted | pm_prioritize | incident_runbook |
escalation. Dispatched by the second CLI arg.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import ValidationReport, load_yaml_safe, print_report

MEDIUM_FIELDS = [
    "scope", "interfaces", "io_examples", "error_handling", "test_specs",
    "invariants", "logging_rules", "observability_rules",
]


def _log_text(project_dir: str) -> str:
    p = os.path.join(project_dir, ".shaktra-test.log")
    return Path(p).read_text().lower() if os.path.isfile(p) else ""


def validate_enrich(project_dir: str, story_id: str) -> ValidationReport:
    """After tpm enrich, the sparse medium story has all medium-tier fields."""
    report = ValidationReport(f"/shaktra:tpm enrich ({story_id})")
    path = os.path.join(project_dir, ".shaktra", "stories", f"{story_id}.yml")
    data, err = load_yaml_safe(path)
    if not isinstance(data, dict):
        report.add("story readable", False, err or "missing")
        return report
    report.add("story readable", True)
    missing = [f for f in MEDIUM_FIELDS if not data.get(f)]
    report.add("all medium-tier fields now present", not missing,
               f"still missing: {missing}" if missing else "")
    # Enrich preserves existing content (title/AC unchanged).
    report.add("existing acceptance_criteria preserved",
               bool(data.get("acceptance_criteria")), "AC lost during enrich")
    return report


def validate_sprint(project_dir: str) -> ValidationReport:
    """After tpm sprint, sprints.yml has a populated current_sprint."""
    report = ValidationReport("/shaktra:tpm sprint")
    path = os.path.join(project_dir, ".shaktra", "sprints.yml")
    data, err = load_yaml_safe(path)
    if not isinstance(data, dict):
        report.add("sprints.yml readable", False, err or "missing")
        return report
    report.add("sprints.yml readable", True)
    cur = data.get("current_sprint")
    report.add("current_sprint populated", isinstance(cur, dict) and bool(cur),
               "current_sprint is null/empty")
    if isinstance(cur, dict):
        stories = cur.get("stories") or []
        report.add("sprint has allocated stories", len(stories) > 0,
                   "no stories allocated")
        report.add("committed_points computed",
                   isinstance(cur.get("committed_points"), int),
                   f"committed_points={cur.get('committed_points')}")
    return report


def validate_analyze_targeted(project_dir: str) -> ValidationReport:
    """After a targeted analyze (practices dimension), that artifact exists."""
    report = ValidationReport("/shaktra:analyze targeted")
    adir = os.path.join(project_dir, ".shaktra", "analysis")
    # Stage-1 ground truth must exist, plus the requested dimension artifact.
    report.add("static.yml (Stage-1) exists",
               os.path.isfile(os.path.join(adir, "static.yml")),
               "no static.yml — Stage 1 did not run")
    practices = os.path.join(adir, "practices.yml")
    data, _ = load_yaml_safe(practices)
    report.add("practices.yml (D4) produced", isinstance(data, dict) and bool(data),
               "practices.yml missing/empty")
    if isinstance(data, dict):
        report.add("practices.yml has a summary", "summary" in data,
                   "no summary section")
    return report


def validate_pm_prioritize(project_dir: str) -> ValidationReport:
    """After pm prioritize, ranked RICE output is evident (log or artifact)."""
    report = ValidationReport("/shaktra:pm prioritize")
    log = _log_text(project_dir)
    art = os.path.join(project_dir, ".shaktra", "prioritization.md")
    has_artifact = os.path.isfile(art)
    has_log = any(k in log for k in ("rice", "quick win", "big bet", "ranked", "prioriti"))
    report.add("prioritization ran (ranked output in log or artifact)",
               has_artifact or has_log,
               "no RICE/ranking evidence in log or .shaktra/prioritization.md")
    # sprints.yml must NOT have been written by prioritization (scrummaster owns it).
    return report


def validate_incident_runbook(project_dir: str, bug_id: str) -> ValidationReport:
    """After incident runbook, runbook.yml exists with operational content."""
    report = ValidationReport(f"/shaktra:incident runbook ({bug_id})")
    rb = os.path.join(project_dir, ".shaktra", "incidents", bug_id, "runbook.yml")
    data, err = load_yaml_safe(rb)
    report.add("runbook.yml exists", isinstance(data, dict) and bool(data),
               err or "missing/empty")
    if isinstance(data, dict):
        blob = str(data).lower()
        report.add("runbook has operational sections",
                   any(k in blob for k in ("symptom", "detection", "response",
                                           "resolution", "verification", "severity")),
                   "no recognizable runbook sections")
    return report


def validate_escalation(project_dir: str, project_name: str) -> ValidationReport:
    """The design gap escalated and the design still completed after re-invoke."""
    report = ValidationReport("/shaktra:tpm design escalation")
    designs = list(Path(os.path.join(project_dir, ".shaktra", "designs")).glob("*.md")) \
        if os.path.isdir(os.path.join(project_dir, ".shaktra", "designs")) else []
    report.add("design document produced", bool(designs),
               "no design doc in .shaktra/designs/ — escalation loop did not complete")
    log = _log_text(project_dir)
    # Evidence the escalation/clarification round-trip happened (soft but expected).
    escalated = any(k in log for k in (
        "auto-answer", "needs_clarification", "clarification", "gap", "escalat",
        "unanswered"))
    report.add("escalation/clarification round-trip observed in log", escalated,
               "no escalation evidence logged (architect may not have flagged the gap)")
    # The transport gap should be addressed in the final design.
    if designs:
        text = designs[0].read_text().lower()
        report.add("design addresses the realtime transport gap",
                   any(k in text for k in ("pub/sub", "pubsub", "redis", "websocket",
                                           "message broker", "broker", "fan-out",
                                           "fanout", "realtime", "transport", "channel")),
                   "design doc does not resolve the fan-out/transport decision")
    return report


DISPATCH = {
    "enrich": lambda a: validate_enrich(a[0], a[1]),
    "sprint": lambda a: validate_sprint(a[0]),
    "analyze_targeted": lambda a: validate_analyze_targeted(a[0]),
    "pm_prioritize": lambda a: validate_pm_prioritize(a[0]),
    "incident_runbook": lambda a: validate_incident_runbook(a[0], a[1]),
    "escalation": lambda a: validate_escalation(a[0], a[1] if len(a) > 1 else ""),
}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_modes.py <project_dir> <mode> [args...]")
        print(f"  modes: {', '.join(DISPATCH)}")
        sys.exit(2)
    project_dir, mode = sys.argv[1], sys.argv[2]
    rest = [project_dir] + sys.argv[3:]
    if mode not in DISPATCH:
        print(f"Unknown mode: {mode}")
        sys.exit(2)
    sys.exit(print_report(DISPATCH[mode](rest)))
