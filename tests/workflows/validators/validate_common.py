#!/usr/bin/env python3
"""Shared validation utilities for Shaktra workflow tests.

Provides reusable check functions for YAML parsing, field existence,
file existence, schema conformance, and structured result tracking.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------
class CheckResult:
    """Single validation check result."""

    def __init__(self, name: str, passed: bool, detail: str = ""):
        self.name = name
        self.passed = passed
        self.detail = detail

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        suffix = f" -- {self.detail}" if self.detail and not self.passed else ""
        return f"[{status}] {self.name}{suffix}"


class ValidationReport:
    """Collects check results for a single workflow test."""

    def __init__(self, workflow: str):
        self.workflow = workflow
        self.results: list[CheckResult] = []

    def add(self, name: str, passed: bool, detail: str = "") -> CheckResult:
        r = CheckResult(name, passed, detail)
        self.results.append(r)
        return r

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def all_passed(self) -> bool:
        return self.failed == 0

    def summary(self) -> str:
        status = "PASS" if self.all_passed else "FAIL"
        return f"[{status}] {self.workflow}: {self.passed}/{self.total} checks passed"

    def detail_lines(self) -> list[str]:
        lines = [self.summary()]
        for r in self.results:
            lines.append(f"  {r}")
        return lines


# ---------------------------------------------------------------------------
# File & directory checks
# ---------------------------------------------------------------------------
def check_exists(report: ValidationReport, path: str, label: str | None = None) -> bool:
    """Check that a file or directory exists."""
    name = label or f"{Path(path).name} exists"
    exists = os.path.exists(path)
    report.add(name, exists, f"not found: {path}" if not exists else "")
    return exists


def check_is_dir(report: ValidationReport, path: str, label: str | None = None) -> bool:
    """Check that a path is a directory."""
    name = label or f"{Path(path).name} is directory"
    is_dir = os.path.isdir(path)
    report.add(name, is_dir, f"not a directory: {path}" if not is_dir else "")
    return is_dir


def check_is_file(report: ValidationReport, path: str, label: str | None = None) -> bool:
    """Check that a path is a file."""
    name = label or f"{Path(path).name} is file"
    is_file = os.path.isfile(path)
    report.add(name, is_file, f"not a file: {path}" if not is_file else "")
    return is_file


# ---------------------------------------------------------------------------
# YAML checks
# ---------------------------------------------------------------------------
def load_yaml_safe(path: str) -> tuple[Any, str | None]:
    """Load a YAML file, returning (data, error_message)."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data, None
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    except FileNotFoundError:
        return None, f"file not found: {path}"
    except Exception as e:
        return None, f"unexpected error: {e}"


def check_valid_yaml(report: ValidationReport, path: str, label: str | None = None) -> Any:
    """Check that a file contains valid YAML. Returns parsed data or None."""
    name = label or f"{Path(path).name} valid YAML"
    data, err = load_yaml_safe(path)
    if err:
        report.add(name, False, err)
        return None
    report.add(name, True)
    return data


# ---------------------------------------------------------------------------
# Field checks (dot-path navigation)
# ---------------------------------------------------------------------------
def _resolve_dotpath(data: Any, dotpath: str) -> tuple[bool, Any]:
    """Navigate a dot-separated path into nested dicts.

    Returns (found, value). If any segment is missing, returns (False, None).
    """
    parts = dotpath.split(".")
    current = data
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def check_field_exists(
    report: ValidationReport, data: Any, dotpath: str, label: str | None = None,
) -> bool:
    """Check that a dot-path field exists in a parsed YAML structure."""
    name = label or f"field '{dotpath}' exists"
    found, _ = _resolve_dotpath(data, dotpath)
    report.add(name, found, f"missing field: {dotpath}" if not found else "")
    return found


def check_field_equals(
    report: ValidationReport, data: Any, dotpath: str, expected: Any,
    label: str | None = None,
) -> bool:
    """Check that a dot-path field equals an expected value."""
    name = label or f"field '{dotpath}' == {expected!r}"
    found, value = _resolve_dotpath(data, dotpath)
    if not found:
        report.add(name, False, f"missing field: {dotpath}")
        return False
    ok = value == expected
    report.add(name, ok, f"got {value!r}, expected {expected!r}" if not ok else "")
    return ok


def check_field_in(
    report: ValidationReport, data: Any, dotpath: str, allowed: list[Any],
    label: str | None = None,
) -> bool:
    """Check that a field's value is in an allowed set."""
    name = label or f"field '{dotpath}' in {allowed!r}"
    found, value = _resolve_dotpath(data, dotpath)
    if not found:
        report.add(name, False, f"missing field: {dotpath}")
        return False
    ok = value in allowed
    report.add(name, ok, f"got {value!r}" if not ok else "")
    return ok


def check_field_nonempty(
    report: ValidationReport, data: Any, dotpath: str, label: str | None = None,
) -> bool:
    """Check that a field exists and is non-empty (truthy)."""
    name = label or f"field '{dotpath}' is non-empty"
    found, value = _resolve_dotpath(data, dotpath)
    if not found:
        report.add(name, False, f"missing field: {dotpath}")
        return False
    ok = bool(value)
    report.add(name, ok, f"field is empty/falsy: {value!r}" if not ok else "")
    return ok


def check_field_gte(
    report: ValidationReport, data: Any, dotpath: str, minimum: int | float,
    label: str | None = None,
) -> bool:
    """Check that a numeric field is >= minimum."""
    name = label or f"field '{dotpath}' >= {minimum}"
    found, value = _resolve_dotpath(data, dotpath)
    if not found:
        report.add(name, False, f"missing field: {dotpath}")
        return False
    try:
        ok = float(value) >= float(minimum)
    except (TypeError, ValueError):
        report.add(name, False, f"not numeric: {value!r}")
        return False
    report.add(name, ok, f"got {value}" if not ok else "")
    return ok


def check_list_min_length(
    report: ValidationReport, data: Any, dotpath: str, min_len: int,
    label: str | None = None,
) -> bool:
    """Check that a list field has at least min_len entries."""
    name = label or f"field '{dotpath}' has >= {min_len} entries"
    found, value = _resolve_dotpath(data, dotpath)
    if not found:
        report.add(name, False, f"missing field: {dotpath}")
        return False
    if not isinstance(value, list):
        report.add(name, False, f"not a list: {type(value).__name__}")
        return False
    ok = len(value) >= min_len
    report.add(name, ok, f"has {len(value)} entries" if not ok else "")
    return ok


# ---------------------------------------------------------------------------
# Glob-based file checks
# ---------------------------------------------------------------------------
def check_glob_matches(
    report: ValidationReport, directory: str, pattern: str, min_count: int = 1,
    label: str | None = None,
) -> list[str]:
    """Check that glob pattern matches at least min_count files."""
    from pathlib import Path as P

    name = label or f"glob '{pattern}' matches >= {min_count} files"
    matches = sorted(P(directory).glob(pattern))
    ok = len(matches) >= min_count
    detail = f"found {len(matches)}" if not ok else ""
    report.add(name, ok, detail)
    return [str(m) for m in matches]


# ---------------------------------------------------------------------------
# Composite validators
# ---------------------------------------------------------------------------
def validate_yaml_file_fields(
    report: ValidationReport, path: str, required_fields: list[str],
    file_label: str | None = None,
) -> Any:
    """Load a YAML file and check that all required dot-path fields exist."""
    label_prefix = file_label or Path(path).name
    if not check_is_file(report, path, f"{label_prefix} exists"):
        return None
    data = check_valid_yaml(report, path, f"{label_prefix} valid YAML")
    if data is None:
        return None
    for field in required_fields:
        check_field_exists(report, data, field, f"{label_prefix}: '{field}' exists")
    return data


def validate_all_yaml_in_dir(report: ValidationReport, directory: str) -> None:
    """Check that all .yml files in a directory are valid YAML."""
    if not os.path.isdir(directory):
        report.add(f"directory {directory} exists", False, "not found")
        return
    for fname in sorted(os.listdir(directory)):
        if fname.endswith((".yml", ".yaml")):
            fpath = os.path.join(directory, fname)
            check_valid_yaml(report, fpath, f"{fname} valid YAML")


# ---------------------------------------------------------------------------
# CLI entry point for standalone testing
# ---------------------------------------------------------------------------
def print_report(report: ValidationReport) -> int:
    """Print a report and return exit code (0=pass, 1=fail)."""
    for line in report.detail_lines():
        print(line)
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    # Self-test: validate that the module loads and basic checks work
    r = ValidationReport("self-test")
    check_exists(r, __file__, "this file exists")
    check_valid_yaml(r, __file__ + ".nonexistent", "missing file fails")
    # The second check should fail — that's expected
    print("validate_common.py self-test:")
    for line in r.detail_lines():
        print(f"  {line}")
    passed = r.results[0].passed and not r.results[1].passed
    print(f"  Self-test: {'OK' if passed else 'BROKEN'}")
    sys.exit(0 if passed else 1)
