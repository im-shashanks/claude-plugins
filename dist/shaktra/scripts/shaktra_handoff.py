#!/usr/bin/env python3
"""Deterministically merge workflow results into a story handoff.yml.

Usage:
    python3 shaktra_handoff.py <handoff_path> --merge-json <file|->
    python3 shaktra_handoff.py <handoff_path> --set current_phase=complete [--set k=v ...]

Orchestrator skills call this after a Workflow run returns, passing the
run's structured result (findings, observations, workflow_run, phase state)
so handoff.yml stays the cross-session source of truth without hand-edited
YAML. Merge semantics:

- dicts merge recursively; scalars overwrite
- quality_findings: append, deduplicated by (gate, file, line, issue);
  an incoming finding replaces its duplicate (so resolved flags update)
- observations: append, deduplicated by (type, text)
- completed_phases: union, preserving first-seen order
- writes are atomic (tmp + rename); file is created if missing
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

FINDING_KEY_FIELDS = ("gate", "file", "line", "issue")
OBSERVATION_KEY_FIELDS = ("type", "text")


def entry_key(entry: dict, fields: tuple) -> tuple:
    return tuple(str(entry.get(f, "")) for f in fields)


def merge_entry_list(existing: list, incoming: list, key_fields: tuple) -> list:
    merged = list(existing)
    index = {
        entry_key(e, key_fields): i
        for i, e in enumerate(merged)
        if isinstance(e, dict)
    }
    for entry in incoming:
        if not isinstance(entry, dict):
            if entry not in merged:
                merged.append(entry)
            continue
        key = entry_key(entry, key_fields)
        if key in index:
            merged[index[key]] = entry
        else:
            index[key] = len(merged)
            merged.append(entry)
    return merged


def merge(base: dict, incoming: dict) -> dict:
    out = dict(base)
    for key, value in incoming.items():
        current = out.get(key)
        if key == "quality_findings" and isinstance(value, list):
            out[key] = merge_entry_list(current or [], value, FINDING_KEY_FIELDS)
        elif key == "observations" and isinstance(value, list):
            out[key] = merge_entry_list(current or [], value, OBSERVATION_KEY_FIELDS)
        elif key == "completed_phases" and isinstance(value, list):
            seen = list(current or [])
            out[key] = seen + [p for p in value if p not in seen]
        elif isinstance(value, dict) and isinstance(current, dict):
            out[key] = merge(current, value)
        else:
            out[key] = value
    return out


def parse_set(pairs: list[str]) -> dict:
    """Turn --set a.b=c pairs into a nested dict; values parse as JSON when possible."""
    result: dict = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"error: --set expects key=value, got {pair!r}")
        key, raw = pair.split("=", 1)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        node = result
        parts = key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return result


def atomic_write_yaml(path: Path, data: dict, yaml) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("handoff", help="Path to handoff.yml")
    parser.add_argument("--merge-json", help="JSON file to merge ('-' for stdin)")
    parser.add_argument("--set", action="append", default=[], dest="sets",
                        help="key=value (dot paths ok, value parsed as JSON when possible)")
    args = parser.parse_args()

    if not args.merge_json and not args.sets:
        parser.error("nothing to do — pass --merge-json and/or --set")

    try:
        import yaml
    except ImportError:
        print("error: PyYAML required — pip install pyyaml", file=sys.stderr)
        return 1

    path = Path(args.handoff)
    base = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        if loaded is not None and not isinstance(loaded, dict):
            print(f"error: {path} is not a YAML mapping", file=sys.stderr)
            return 1
        base = loaded or {}

    incoming: dict = {}
    if args.merge_json:
        raw = sys.stdin.read() if args.merge_json == "-" else Path(args.merge_json).read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"error: invalid merge JSON — {e}", file=sys.stderr)
            return 1
        if not isinstance(payload, dict):
            print("error: merge JSON must be an object", file=sys.stderr)
            return 1
        incoming = payload
    if args.sets:
        incoming = merge(incoming, parse_set(args.sets))

    merged = merge(base, incoming)
    atomic_write_yaml(path, merged, yaml)
    print(f"handoff updated: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
