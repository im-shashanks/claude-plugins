#!/usr/bin/env python3
"""Validators for /shaktra:bugfix workflow."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_common import (
    ValidationReport, check_is_file, check_valid_yaml, print_report,
)


def validate_bugfix(project_dir: str) -> ValidationReport:
    """Validate project state after /shaktra:bugfix."""
    report = ValidationReport("/shaktra:bugfix")

    # --- Source files modified ---
    src_file = os.path.join(project_dir, "src", "calculator.py")
    if check_is_file(report, src_file, "calculator.py exists"):
        src = Path(src_file).read_text().lower()
        has_fix = any(k in src for k in ["valueerror", "zero", "if b == 0", "b == 0"])
        report.add("fix addresses zero division", has_fix,
                    "no zero-division handling found" if not has_fix else "")

    # --- Tests pass ---
    check_is_file(report, os.path.join(project_dir, "tests", "test_calculator.py"),
                  "test file exists")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True, text=True, timeout=30,
            cwd=project_dir,
        )
        tests_pass = result.returncode == 0
        report.add(
            "tests pass after fix",
            tests_pass,
            result.stdout.split("\n")[-2] if not tests_pass else "",
        )
    except Exception as e:
        report.add("tests pass after fix", False, f"pytest error: {e}")

    # --- Shaktra state ---
    shaktra = os.path.join(project_dir, ".shaktra")
    has_shaktra = os.path.isdir(shaktra)
    if has_shaktra:
        stories = list(Path(shaktra).glob("stories/ST-*.yml"))
        report.add("bugfix story or artifact created",
                    len(stories) > 0 or os.path.isfile(
                        os.path.join(shaktra, "memory", "lessons.yml")),
                    "no stories or memory updates found")

    # --- Diagnosis artifact ---
    diag_exists = (has_shaktra and (
        os.path.isdir(os.path.join(shaktra, "diagnosis"))
        or list(Path(shaktra).glob("*diagnosis*"))
        or list(Path(shaktra).glob("*bug-report*"))))
    report.add("diagnosis artifact exists", bool(diag_exists),
               "no diagnosis directory or files found" if not diag_exists else "")

    # --- Story creation with bug scope ---
    bug_story = False
    sdir = os.path.join(shaktra, "stories") if has_shaktra else ""
    if os.path.isdir(sdir):
        for sf in Path(sdir).glob("*.y*ml"):
            try:
                if "bug" in sf.read_text().lower():
                    bug_story = True
                    break
            except Exception:
                pass
    report.add("bugfix story created", bug_story,
               "no story mentioning 'bug' found" if not bug_story else "")

    # --- Root cause identification ---
    rc_found = False
    if has_shaktra:
        for rt, _, fnames in os.walk(shaktra):
            for fn in fnames:
                if fn.endswith((".yml", ".yaml", ".md")):
                    try:
                        txt = Path(os.path.join(rt, fn)).read_text().lower()
                        if "root_cause" in txt or "root cause" in txt:
                            rc_found = True
                    except Exception:
                        pass
                if rc_found:
                    break
            if rc_found:
                break
    report.add("root cause identified", rc_found,
               "no root cause reference in .shaktra/" if not rc_found else "")

    # --- Memory: bugfix lessons ---
    lp = os.path.join(shaktra, "memory", "lessons.yml") if has_shaktra else ""
    if os.path.isfile(lp):
        ld = check_valid_yaml(report, lp, "lessons.yml valid YAML")
        if isinstance(ld, dict):
            entries = ld.get("lessons", []) or []
            bl = [e for e in entries if isinstance(e, dict)
                  and any(k in str(e.get("source", "")).lower()
                          for k in ["bugfix", "bug"])]
            report.add("bugfix lessons captured", len(bl) > 0,
                       f"no bugfix source lessons (total: {len(entries)})"
                       if not bl else "")

    return report



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_bugfix.py <project_dir>"); sys.exit(2)
    sys.exit(print_report(validate_bugfix(sys.argv[1])))
