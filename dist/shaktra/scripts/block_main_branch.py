#!/usr/bin/env python3
"""Hook: block git write-operations targeting protected branches.

Event: PreToolUse (Bash)
Exit 0 = allow, Exit 2 = block.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys


PROTECTED = r"(?:main|master|prod|production)"
PROTECTED_SET = {"main", "master", "prod", "production"}
# git checkout <branch> or git switch <branch> — but NOT branch-creation flags
# Handles intervening flags (e.g., --detach, --force) before the protected branch name
# Excludes: -b, -B, -c, --create (branch creation, not switching)
# Also catches remote-tracking refs: origin/main, upstream/production, refs/heads/main
CHECKOUT_RE = re.compile(
    rf"(?:^|[;&|]\s*)git\s+(?:checkout|switch)\s+(?!.*(?:-[bcB]\b|--create\b))(?:\S+\s+)*(?:\w+/)*{PROTECTED}(?![\w-])"
)
# git push ... <branch>  (captures "git push origin main", "git push main")
# [^;&|]* stops at shell operators to avoid cross-command matching
PUSH_RE = re.compile(rf"(?:^|[;&|]\s*)git\s+push\b[^;&|]*\b{PROTECTED}(?![\w-])")
# git merge|rebase|reset ... <branch>
MERGE_RE = re.compile(rf"(?:^|[;&|]\s*)git\s+(?:merge|rebase|reset)\b[^;&|]*\b{PROTECTED}(?![\w-])")

BLOCK_PATTERNS = [CHECKOUT_RE, PUSH_RE, MERGE_RE]


def get_current_branch() -> str | None:
    """Return the current git branch name, or None if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def is_git_write(command: str) -> bool:
    """Return True if the command is a git write operation (commit, push, merge, rebase, reset).

    Anchored to command start or after a shell operator (;, &&, ||, |) to avoid
    false positives from strings like: echo 'git commit'.
    """
    return bool(
        re.search(r"(?:^|[;&|]\s*)git\s+(?:commit|push|merge|rebase|reset)\b", command)
    )


def main() -> None:
    if os.environ.get("SHAKTRA_ALLOW_MAIN_BRANCH"):
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print("BLOCKED: Could not parse hook input — failing closed.")
        sys.exit(2)

    command = data.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        sys.exit(0)

    # Check 1: Block commands that explicitly target protected branches
    for pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            branch = re.search(PROTECTED, command).group()
            print(
                f"BLOCKED: Direct git operation on protected branch '{branch}'.\n"
                f"Create a feature branch instead:\n"
                f"  git checkout -b <branch-name>"
            )
            sys.exit(2)

    # Check 2: Block git write operations when currently on a protected branch
    if is_git_write(command):
        current = get_current_branch()
        if current and current in PROTECTED_SET:
            print(
                f"BLOCKED: Currently on protected branch '{current}'.\n"
                f"Create a feature branch first:\n"
                f"  git checkout -b <branch-name>"
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
