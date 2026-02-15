#!/usr/bin/env python3
"""Shaktra Workflow Test Orchestrator.

Fully automated end-to-end testing of all /shaktra:* workflows.
Launches claude --print sessions with the plugin loaded, monitors
file system changes for observability, and validates results.

Usage:
    python3 run_workflow_tests.py                  # Run all tests
    python3 run_workflow_tests.py --smoke           # Smoke tests only
    python3 run_workflow_tests.py --test tpm        # Single test
    python3 run_workflow_tests.py --group greenfield # Test group
    python3 run_workflow_tests.py --list            # List available tests
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_definitions import get_test_definitions
from test_runner import LOG_FILE, TestResult, cleanup_orphan_teams, run_test

REPORTS_DIR = Path(__file__).resolve().parent / "reports"

# Test groups that share a directory (run sequentially in same temp dir)
SHARED_DIR_GROUPS = {
    "greenfield": ["init-greenfield", "pm", "tpm", "dev", "review"],
    "brownfield": ["init-brownfield", "analyze"],
}


def main() -> int:
    args = parse_args()

    if args.list:
        return list_tests()

    print(f"Shaktra Workflow Tests — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60, file=sys.stderr)

    # Cleanup any orphan test teams from prior runs
    cleanup_orphan_teams("test-")

    # Get test definitions (test_dir placeholder — resolved per group)
    all_tests = get_test_definitions("{TEST_DIR}")

    # Filter tests
    selected = _filter_tests(all_tests, args)
    if not selected:
        print("No tests matched the filter.", file=sys.stderr)
        return 2

    print(f"Running {len(selected)} test(s)...\n", file=sys.stderr)

    results: list[TestResult] = []
    temp_dirs: list[Path] = []

    try:
        results = _run_selected_tests(selected, temp_dirs, model=args.model)
    finally:
        # Cleanup
        cleanup_orphan_teams("test-")
        if not args.keep_dirs:
            for td in temp_dirs:
                if td.exists():
                    shutil.rmtree(td, ignore_errors=True)

    # Report
    _print_summary(results)
    report_path = _write_report(results)
    print(f"\nReport: {report_path}", file=sys.stderr)

    return 0 if all(r.passed for r in results) else 1


def _run_selected_tests(
    selected: list[dict], temp_dirs: list[Path], model: str = "",
) -> list[TestResult]:
    """Run tests, sharing dirs within groups."""
    results = []
    group_dirs: dict[str, Path] = {}

    for test_def in selected:
        category = test_def["category"]
        group_key = _find_group(test_def["name"])

        # Resolve test directory
        if group_key and group_key in group_dirs:
            test_dir = group_dirs[group_key]
        else:
            test_dir = Path(tempfile.mkdtemp(prefix=f"shaktra-test-{category}-"))
            temp_dirs.append(test_dir)
            # Git init for fresh dirs
            subprocess.run(["git", "init"], cwd=test_dir, capture_output=True)
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "initial"],
                cwd=test_dir, capture_output=True,
            )
            if group_key:
                group_dirs[group_key] = test_dir

        # Setup
        if test_def.get("setup"):
            test_def["setup"](test_dir)

        # Resolve {TEST_DIR} placeholder in prompt
        prompt = test_def["prompt"].replace("{TEST_DIR}", str(test_dir))

        log_path = test_dir / LOG_FILE
        print(f"\n{'─' * 50}", file=sys.stderr)
        print(
            f"[{len(results) + 1}/{len(selected)}] {test_def['name']} "
            f"(timeout: {test_def['timeout']}s)",
            file=sys.stderr,
        )
        print(f"  Live log:  tail -f {log_path}", file=sys.stderr)

        result = run_test(
            name=test_def["name"],
            prompt=prompt,
            test_dir=test_dir,
            timeout_secs=test_def["timeout"],
            max_turns=test_def["max_turns"],
            model=model,
        )
        results.append(result)

        icon = "PASS" if result.passed else result.verdict
        print(
            f"  => {icon} ({result.duration_secs:.1f}s)",
            file=sys.stderr,
        )

    return results


def _find_group(test_name: str) -> str | None:
    """Find which shared-dir group a test belongs to."""
    for group, members in SHARED_DIR_GROUPS.items():
        if test_name in members:
            return group
    return None


def _filter_tests(all_tests: list[dict], args: argparse.Namespace) -> list[dict]:
    """Filter test list based on CLI args."""
    if args.test:
        return [t for t in all_tests if t["name"] == args.test]
    if args.smoke:
        return [t for t in all_tests if t["category"] == "smoke"]
    if args.group:
        return [t for t in all_tests if t["category"] == args.group]
    return all_tests


def _print_summary(results: list[TestResult]) -> None:
    """Print final summary table."""
    print(f"\n{'=' * 60}", file=sys.stderr)
    print("RESULTS", file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)

    for r in results:
        icon = "pass" if r.passed else r.verdict.lower()
        dur = f"{r.duration_secs:.0f}s"
        err = f" ({r.error})" if r.error else ""
        print(f"  [{icon:>7}] {r.name:<20} {dur:>6}{err}", file=sys.stderr)

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    overall = "ALL PASSED" if passed == total else f"{total - passed} FAILED"
    total_time = sum(r.duration_secs for r in results)
    print(f"\n  {passed}/{total} passed — {overall} — {total_time:.0f}s total",
          file=sys.stderr)


def _write_report(results: list[TestResult]) -> Path:
    """Write markdown report to reports dir."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = REPORTS_DIR / f"workflow-test-{ts}.md"

    lines = [
        "# Shaktra Workflow Test Report",
        f"\nRun: {datetime.now().isoformat()}",
        "",
        "## Summary",
        "",
        "| # | Test | Verdict | Duration | Error |",
        "|---|------|---------|----------|-------|",
    ]
    for i, r in enumerate(results, 1):
        err = r.error or ""
        lines.append(
            f"| {i} | {r.name} | {r.verdict} | {r.duration_secs:.0f}s | {err} |"
        )

    passed = sum(1 for r in results if r.passed)
    lines.extend([
        "",
        f"**{passed}/{len(results)} passed**",
        "",
        "## Detailed Output",
        "",
    ])
    for r in results:
        lines.extend([
            f"### {r.name} ({r.verdict})",
            "",
            "<details><summary>Full output</summary>",
            "",
            "```",
            *r.output_lines[-100:],  # last 100 lines
            "```",
            "",
            "</details>",
            "",
        ])

    path.write_text("\n".join(lines))
    return path


def list_tests() -> int:
    """Print available tests and exit."""
    tests = get_test_definitions("/tmp/example")
    print("Available tests:\n")
    for t in tests:
        print(f"  {t['name']:<20} [{t['category']}] timeout={t['timeout']}s")
    print(f"\nGroups: {', '.join(SHARED_DIR_GROUPS.keys())}, smoke, hotfix, bugfix")
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Shaktra workflow test runner")
    p.add_argument("--test", help="Run a single test by name")
    p.add_argument("--group", help="Run a test group (greenfield, brownfield, etc.)")
    p.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    p.add_argument("--list", action="store_true", help="List available tests")
    p.add_argument("--keep-dirs", action="store_true",
                   help="Keep temp directories after tests")
    p.add_argument("--model", default="",
                   help="Claude model to use (e.g. claude-sonnet-4-5-20250929)")
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(main())
