#!/usr/bin/env python3
"""Validator for PR-mode review / adversarial-review (storyless).

A PR review has no story handoff, so the verdict is validated from the session
log: the test prompt instructs the agent to log 'PR-VERDICT: <verdict>' and
'PR-GH-DIFF-FETCHED' once it has pulled the diff via the gh shim. This confirms
the pr-review code path (gh fetch -> analyze -> verdict) actually ran.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import ValidationReport, print_report

REVIEW_VERDICTS = {"approved", "approved_with_notes", "changes_requested", "blocked"}
ADV_VERDICTS = {"pass", "concern", "blocked"}


def validate_pr_review(project_dir: str, kind: str) -> ValidationReport:
    report = ValidationReport(f"/shaktra:{kind} PR mode")
    log_path = os.path.join(project_dir, ".shaktra-test.log")
    log = Path(log_path).read_text().lower() if os.path.isfile(log_path) else ""

    report.add("session log present", bool(log), "no .shaktra-test.log")

    # The gh-fetch path ran (the PR-specific delta vs story review).
    fetched = ("pr-gh-diff-fetched" in log) or ("gh pr diff" in log) or ("pr diff" in log)
    report.add("PR diff fetched via gh", fetched,
               "no evidence the gh PR diff was fetched")

    # A verdict was produced and is valid for this review kind.
    m = re.search(r"pr-verdict:\s*([a-z_]+)", log)
    verdict = m.group(1) if m else None
    valid = ADV_VERDICTS if "adversarial" in kind else REVIEW_VERDICTS
    report.add("PR review produced a valid verdict",
               verdict in valid,
               f"PR-VERDICT={verdict!r} not in {sorted(valid)}")

    # The analysis actually ran (dimensions / mutation, per kind).
    if "adversarial" in kind:
        ran = any(k in log for k in ("mutation", "probe", "adversar"))
        report.add("adversarial analysis ran", ran, "no mutation/probe evidence")
    else:
        ran = any(k in log for k in ("dimension", "cr-analyzer", "verification", "analyz"))
        report.add("review analysis ran", ran, "no dimension/verification evidence")

    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate_pr_review.py <project_dir> <review|adversarial-review>")
        sys.exit(2)
    sys.exit(print_report(validate_pr_review(sys.argv[1], sys.argv[2])))
