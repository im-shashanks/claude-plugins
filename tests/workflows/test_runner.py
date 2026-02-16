#!/usr/bin/env python3
"""Core test engine — launches claude --print sessions and validates results.

Each workflow test runs as a `claude --print` session that directly invokes
the skill (like a real user session), then runs validators and reports.

Observability comes from FileMonitor (watches .shaktra/ for new files externally)
and an agent-written log file (.shaktra-test.log).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TestResult:
    """Result of a single workflow test."""

    name: str
    verdict: str = "UNKNOWN"  # PASS, FAIL, TIMEOUT, ERROR
    duration_secs: float = 0.0
    output_lines: list[str] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)  # Read tool file paths
    error: str = ""

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGIN_DIR = REPO_ROOT / "dist" / "shaktra"
VALIDATORS_DIR = Path(__file__).resolve().parent / "validators"

# Agent-written progress log — tail this for real-time observability
LOG_FILE = ".shaktra-test.log"

# Files to ignore in the monitor (git internals, etc.)
_MONITOR_IGNORE = {".git", "__pycache__", ".DS_Store", LOG_FILE}


def build_prompt(
    test_name: str,
    skill: str,
    skill_args: str = "",
    validator_cmd: str = "",
    extra: str = "",
) -> str:
    """Build a prompt for a workflow test — direct skill invocation.

    The agent invokes the skill directly (like a real user session),
    then runs the validator and reports. No team indirection.
    """
    log = LOG_FILE

    validator_block = ""
    if validator_cmd:
        validator_block = f"""
STEP 4: Run this validator command via Bash:
  {validator_cmd}
  Print the full validator output.
  Log the output to "{log}".
"""

    return f"""You are an automated test runner. Follow these steps EXACTLY.

LOGGING: Log every step to "{log}" via Bash: echo "[$(date +%H:%M:%S)] <msg>" >> {log}

STEP 1: Log "Starting test {test_name}"

STEP 2: Use the Skill tool: Skill("{skill}"{', args="' + skill_args + '"' if skill_args else ''})
  FOLLOW the skill instructions completely. Do everything the skill asks.
  This may involve spawning sub-agents, creating files, running quality checks, etc.
  Do NOT skip any part of the skill workflow.

STEP 3: After the skill workflow is FULLY complete, log "Skill workflow complete"
  Dump file state to log:
  echo "[$(date +%H:%M:%S)] files:" >> {log} && find .shaktra -type f 2>/dev/null | sort >> {log}
{extra}
{validator_block}
STEP 5: Based on the validator output, print EXACTLY one of:
  [TEST:{test_name}] VERDICT: PASS
  [TEST:{test_name}] VERDICT: FAIL
  Use PASS only if the validator shows all checks passed. Otherwise FAIL.
  Log the verdict."""


def build_smoke_prompt(test_name: str, skill: str) -> str:
    """Build a simpler prompt for smoke tests (no team, direct invocation)."""
    return f"""You are an automated test runner. Follow these steps EXACTLY.

STEP 1: Print "[TEST:{test_name}] Starting smoke test..."
STEP 2: Use the Skill tool to invoke Skill("{skill}").
STEP 3: If the skill executed without error, print:
  [TEST:{test_name}] VERDICT: PASS
  If it errored, print:
  [TEST:{test_name}] VERDICT: FAIL -- <error message>"""


# ---------------------------------------------------------------------------
# File system monitor — observability into long-running tests
# ---------------------------------------------------------------------------
class FileMonitor:
    """Watches a directory for new and modified files, logging in real-time.

    Tracks both new file creation and size changes (detects quality loop
    iterations where a design doc or story is revised).

    Writes to the shared agent log file (.shaktra-test.log) so users only
    need one `tail -f` command for full observability. Only logs actual
    events (new files, modifications) — no heartbeat noise.
    """

    def __init__(self, test_dir: str, test_name: str, interval: float = 10.0):
        self._dir = test_dir
        self._name = test_name
        self._interval = interval
        self._known: dict[str, int] = {}  # path -> size
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._log_path = os.path.join(test_dir, LOG_FILE)
        self._start_time = time.time()

    def start(self) -> None:
        self._known = self._snapshot()
        self._log(f"File monitor started ({len(self._known)} initial files)")
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
        elapsed = time.time() - self._start_time
        self._log(f"File monitor stopped after {elapsed:.0f}s")

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            current = self._snapshot()
            elapsed = time.time() - self._start_time

            # Detect new files
            new_files = sorted(set(current) - set(self._known))
            for f in new_files:
                size = current[f]
                msg = f"+{elapsed:.0f}s new: {f} ({self._fmt_size(size)})"
                self._log(msg)
                _print_progress(self._name, msg)

            # Detect modified files (size changed)
            for f in sorted(set(current) & set(self._known)):
                old_size = self._known[f]
                new_size = current[f]
                if new_size != old_size:
                    delta = new_size - old_size
                    sign = "+" if delta > 0 else ""
                    msg = (
                        f"+{elapsed:.0f}s modified: {f} "
                        f"({self._fmt_size(old_size)} → {self._fmt_size(new_size)}, "
                        f"{sign}{self._fmt_size(delta)})"
                    )
                    self._log(msg)
                    _print_progress(self._name, msg)

            self._known = current

    def _snapshot(self) -> dict[str, int]:
        files: dict[str, int] = {}
        root = Path(self._dir)
        if not root.exists():
            return files
        for p in root.rglob("*"):
            if p.is_file() and not any(part in _MONITOR_IGNORE for part in p.parts):
                try:
                    files[str(p.relative_to(root))] = p.stat().st_size
                except OSError:
                    pass
        return files

    @staticmethod
    def _fmt_size(size: int) -> str:
        if abs(size) < 1024:
            return f"{size}B"
        return f"{size / 1024:.1f}KB"

    def _log(self, msg: str) -> None:
        try:
            with open(self._log_path, "a") as f:
                f.write(f"[MONITOR] {msg}\n")
                f.flush()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------
def run_test(
    name: str,
    prompt: str,
    test_dir: str | Path,
    timeout_secs: int = 600,
    max_turns: int = 30,
    model: str = "",
) -> TestResult:
    """Launch a claude --print session and capture output with timeout."""
    result = TestResult(name=name)
    test_dir = str(test_dir)
    start = time.time()

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    cmd = [
        "claude", "--print",
        "--dangerously-skip-permissions",
        "--verbose",
        "--output-format", "stream-json",
        "--plugin-dir", str(PLUGIN_DIR),
        "--max-turns", str(max_turns),
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.extend(["--", prompt])

    # Start file system monitor for observability
    monitor = FileMonitor(test_dir, name)
    monitor.start()

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=test_dir,
            env=env,
        )
    except FileNotFoundError:
        monitor.stop()
        result.verdict = "ERROR"
        result.error = "claude CLI not found"
        return result

    try:
        # Reader thread because claude --print buffers all stdout until exit.
        reader = threading.Thread(
            target=_stream_output, args=(proc, result, name),
            daemon=True,
        )
        reader.start()
        reader.join(timeout=timeout_secs)
        if reader.is_alive():
            proc.kill()
            proc.wait(timeout=5)
            result.verdict = "TIMEOUT"
            result.error = f"killed after {timeout_secs}s"
            _print_progress(name, f"TIMEOUT after {timeout_secs}s")
            reader.join(timeout=3)
    except Exception as e:
        proc.kill()
        proc.wait(timeout=5)
        result.verdict = "ERROR"
        result.error = str(e)
    finally:
        monitor.stop()
        write_read_manifest(Path(test_dir), result)
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)

    result.duration_secs = time.time() - start

    if result.verdict == "UNKNOWN":
        result.verdict = _parse_verdict(result.output_lines, name)

    return result


def _stream_output(
    proc: subprocess.Popen,
    result: TestResult,
    test_name: str,
) -> None:
    """Parse stream-json output, extract text lines and Read file paths."""
    for line in proc.stdout:
        raw_line = line.rstrip("\n")
        if not raw_line:
            continue
        try:
            obj = json.loads(raw_line)
        except json.JSONDecodeError:
            # Not JSON — treat as plain text
            result.output_lines.append(raw_line)
            continue

        msg_type = obj.get("type")

        if msg_type == "assistant":
            for block in obj.get("message", {}).get("content", []):
                block_type = block.get("type")
                if block_type == "text":
                    text = block.get("text", "")
                    for line in text.splitlines():
                        result.output_lines.append(line)
                        if f"[TEST:{test_name}]" in line:
                            _print_progress(
                                test_name,
                                line.split(f"[TEST:{test_name}]")[-1].strip(),
                            )
                elif block_type == "tool_use" and block.get("name") == "Read":
                    file_path = block.get("input", {}).get("file_path", "")
                    if file_path:
                        result.reads.append(file_path)

        elif msg_type == "result":
            result_text = obj.get("result", "")
            if result_text:
                for line in str(result_text).splitlines():
                    result.output_lines.append(line)

    proc.wait(timeout=10)


def _parse_verdict(lines: list[str], test_name: str) -> str:
    """Extract PASS/FAIL verdict from output lines."""
    for line in reversed(lines):
        if "VERDICT:" in line:
            upper = line.upper()
            if "PASS" in upper:
                return "PASS"
            elif "FAIL" in upper:
                return "FAIL"
    return "UNKNOWN"


def _print_progress(test_name: str, message: str) -> None:
    """Print a progress line to stderr."""
    print(f"  [{test_name}] {message}", file=sys.stderr, flush=True)


def check_expected_reads(result: TestResult, expected: list[str]) -> list[str]:
    """Check that expected file patterns appear in Read tool calls.

    Returns list of missing patterns (empty = all found).
    """
    missing = []
    for pattern in expected:
        if not any(pattern in path for path in result.reads):
            missing.append(pattern)
    return missing


def _shorten_read_path(path: str) -> str:
    """Shorten a Read file path for display — strip common prefixes."""
    plugin_marker = "dist/shaktra/"
    idx = path.find(plugin_marker)
    if idx != -1:
        return "[plugin] " + path[idx + len(plugin_marker):]
    shaktra_marker = ".shaktra/"
    idx = path.find(shaktra_marker)
    if idx != -1:
        return "[project] " + path[idx:]
    return path


def write_read_manifest(test_dir: Path, result: TestResult) -> None:
    """Append a read manifest to the test log file."""
    if not result.reads:
        return
    log_path = test_dir / LOG_FILE
    seen: list[str] = []
    for r in result.reads:
        short = _shorten_read_path(r)
        if short not in seen:
            seen.append(short)
    try:
        with open(log_path, "a") as f:
            f.write("\n[READ-MANIFEST] Files read during test:\n")
            for s in seen:
                f.write(f"[READ-MANIFEST]   {s}\n")
            f.write(f"[READ-MANIFEST] Total: {len(seen)} unique files\n")
    except OSError:
        pass


def cleanup_orphan_teams(prefix: str = "test-") -> None:
    """Remove any leftover test teams from ~/.claude/teams/."""
    teams_dir = Path.home() / ".claude" / "teams"
    if teams_dir.exists():
        for entry in teams_dir.iterdir():
            if entry.is_dir() and entry.name.startswith(prefix):
                shutil.rmtree(entry, ignore_errors=True)

    tasks_dir = Path.home() / ".claude" / "tasks"
    if tasks_dir.exists():
        for entry in tasks_dir.iterdir():
            if entry.is_dir() and entry.name.startswith(prefix):
                shutil.rmtree(entry, ignore_errors=True)
