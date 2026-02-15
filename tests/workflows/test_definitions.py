#!/usr/bin/env python3
"""Test definitions for Shaktra workflow tests.

Each test is a dict with: name, category, timeout, max_turns, setup function,
prompt builder, and optional validator.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from test_runner import VALIDATORS_DIR, build_prompt, build_smoke_prompt

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "dist" / "shaktra" / "templates"

# Testing overrides injected into CLAUDE.md — read by all agents in the session.
# This avoids modifying actual plugin files while constraining test behavior.
_TEST_OVERRIDES = """

---

## Testing Mode — Automated Workflow Test

This is an automated test run. The following overrides apply:

### Workflow Constraints
- **Quality review loops: 1 iteration maximum.** After the first review+fix pass, proceed to the next workflow step regardless of remaining findings.
- **Story creation: 2 stories maximum.** Create only 2 stories (pick the 2 most representative). This is sufficient to prove the workflow works.
- **Sprint planning: 1 sprint only.**
- **Do not ask the user for clarification.** Make reasonable assumptions and proceed.

### Observability — Mandatory Logging
Every agent (including sub-agents) MUST log major events to `.shaktra-test.log` in the project root:
```
echo "[$(date +%H:%M:%S)] <event>" >> .shaktra-test.log
```

Events to log:
- Agent start: `"[agent-name] started — <purpose>"`
- Phase transition: `"PHASE: <phase-name> started"` / `"PHASE: <phase-name> complete"`
- Quality review: `"QUALITY: reviewing <artifact>" / "QUALITY: verdict=<PASS|BLOCKED> findings=<count>"`
- Quality fix: `"QUALITY-FIX: fixing <count> findings in <artifact>"`
- File write: `"WRITE: <file-path>"`
- Sprint allocation: `"SPRINT: allocated <count> stories to <sprint-id>"`
- Memory capture: `"MEMORY: captured <count> lessons"`
- Agent complete: `"[agent-name] complete"`
"""


# ---------------------------------------------------------------------------
# Setup functions — prepare test_dir before each test
# ---------------------------------------------------------------------------
def _append_test_overrides(claude_md_path: Path) -> None:
    """Append testing overrides to CLAUDE.md in the test directory."""
    if claude_md_path.exists():
        with open(claude_md_path, "a") as f:
            f.write(_TEST_OVERRIDES)


def setup_git_init(test_dir: Path) -> None:
    """Initialize a git repo if not already initialized."""
    import subprocess
    if not (test_dir / ".git").exists():
        subprocess.run(["git", "init"], cwd=test_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "initial"],
            cwd=test_dir, capture_output=True,
        )


def setup_shaktra_from_templates(test_dir: Path, settings: dict) -> None:
    """Initialize .shaktra/ from templates with settings overrides."""
    import yaml

    shaktra = test_dir / ".shaktra"
    shaktra.mkdir(exist_ok=True)

    copies = {
        "settings.yml": shaktra / "settings.yml",
        "sprints.yml": shaktra / "sprints.yml",
        "decisions.yml": shaktra / "memory" / "decisions.yml",
        "lessons.yml": shaktra / "memory" / "lessons.yml",
        "analysis-manifest.yml": shaktra / "analysis" / "manifest.yml",
        "shaktra-CLAUDE.md": shaktra / "CLAUDE.md",
        "CLAUDE.md": test_dir / "CLAUDE.md",
    }
    for template_name, dest in copies.items():
        src = TEMPLATES_DIR / template_name
        if src.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    for subdir in ["stories", "designs"]:
        (shaktra / subdir).mkdir(exist_ok=True)

    # Apply settings
    settings_path = shaktra / "settings.yml"
    if settings_path.exists() and settings:
        with open(settings_path) as f:
            data = yaml.safe_load(f) or {}
        _deep_merge(data, settings)
        with open(settings_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def setup_greenfield(test_dir: Path) -> None:
    """Full greenfield setup: git + .shaktra/ + fixtures."""
    setup_git_init(test_dir)
    setup_shaktra_from_templates(test_dir, {
        "project": {
            "name": "TestProject", "type": "greenfield", "language": "python",
            "architecture": "layered", "test_framework": "pytest",
            "coverage_tool": "coverage", "package_manager": "pip",
        }
    })
    # Copy PRD and architecture for TPM
    shaktra = test_dir / ".shaktra"
    for f in ["prd.md", "architecture.md"]:
        src = FIXTURES_DIR / "greenfield" / f
        if src.exists():
            shutil.copy2(src, shaktra / f)

    # Inject testing overrides into CLAUDE.md
    _append_test_overrides(test_dir / "CLAUDE.md")


def setup_brownfield(test_dir: Path) -> None:
    """Brownfield setup: git + sample project + .shaktra/."""
    setup_git_init(test_dir)
    # Copy sample project
    src_proj = FIXTURES_DIR / "brownfield" / "sample-project"
    if src_proj.exists():
        for item in src_proj.iterdir():
            dest = test_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
    setup_shaktra_from_templates(test_dir, {
        "project": {
            "name": "BrownfieldTest", "type": "brownfield", "language": "python",
            "architecture": "layered", "test_framework": "pytest",
            "coverage_tool": "coverage", "package_manager": "pip",
        }
    })
    _append_test_overrides(test_dir / "CLAUDE.md")


def setup_bugfix(test_dir: Path) -> None:
    """Setup a project with a known bug for bugfix testing."""
    setup_greenfield(test_dir)
    src_dir = test_dir / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "calculator.py").write_text(
        'def divide(a, b):\n    return a / b  # BUG: no zero division check\n'
    )
    tests_dir = test_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_calculator.py").write_text(
        'from src.calculator import divide\n\n'
        'def test_divide():\n    assert divide(10, 2) == 5\n\n'
        'def test_divide_zero():\n'
        '    # This test fails — the bug\n'
        '    try:\n        divide(1, 0)\n        assert False, "should raise"\n'
        '    except ValueError:\n        pass  # expects ValueError, gets ZeroDivisionError\n'
    )


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# ---------------------------------------------------------------------------
# Validator command builders
# ---------------------------------------------------------------------------
def _v(script: str, *args: str) -> str:
    """Build a validator command string."""
    parts = [f"python3 {VALIDATORS_DIR / script}"] + list(args)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------
def get_test_definitions(test_dir: str) -> list[dict]:
    """Return all test definitions. test_dir is substituted into validators."""
    d = test_dir
    return [
        # --- Smoke tests (simple, no team needed) ---
        {
            "name": "help",
            "category": "smoke",
            "timeout": 120,
            "max_turns": 5,
            "setup": None,
            "prompt": build_smoke_prompt("help", "shaktra-help"),
        },
        {
            "name": "doctor",
            "category": "smoke",
            "timeout": 180,
            "max_turns": 15,
            "setup": lambda td: setup_greenfield(td),
            "prompt": build_smoke_prompt("doctor", "shaktra-doctor"),
        },
        {
            "name": "status-dash",
            "category": "smoke",
            "timeout": 180,
            "max_turns": 15,
            "setup": lambda td: setup_greenfield(td),
            "prompt": build_smoke_prompt("status-dash", "shaktra-status-dash"),
        },
        # --- Greenfield chain (shared dir) ---
        {
            "name": "init-greenfield",
            "category": "greenfield",
            "timeout": 300,
            "max_turns": 5,
            "setup": lambda td: setup_greenfield(td),
            "prompt": build_smoke_prompt("init-greenfield", "shaktra-doctor")
            + f'\n\nAlso run: python3 {_v("validate_init.py", d, "TestProject", "greenfield", "python")}\nPrint the validator output. If all checks pass, VERDICT: PASS. Otherwise VERDICT: FAIL.',
        },
        {
            "name": "pm",
            "category": "greenfield",
            "timeout": 900,
            "max_turns": 30,
            "setup": None,  # reuses greenfield dir
            "prompt": build_prompt(
                "pm", "shaktra-pm",
                skill_args="Create a PRD for the user authentication feature described in .shaktra/prd.md",
                validator_cmd=_v("validate_pm.py", d),
            ),
        },
        {
            "name": "tpm",
            "category": "greenfield",
            "timeout": 1500,
            "max_turns": 60,
            "setup": lambda td: setup_greenfield(td),
            "prompt": build_prompt(
                "tpm", "shaktra-tpm",
                skill_args="plan the user authentication feature from the PRD",
                validator_cmd=_v("validate_tpm.py", d),
            ),
        },
        {
            "name": "dev",
            "category": "greenfield",
            "timeout": 1200,
            "max_turns": 50,
            "setup": None,
            "prompt": build_prompt(
                "dev", "shaktra-dev",
                skill_args="develop the first story",
                validator_cmd=_v("validate_dev.py", d, "AUTO"),
                extra='Note: "AUTO" means find the first ST-*.yml story ID automatically. '
                'Before running the validator, find the story ID: ls .shaktra/stories/ST-*.yml, '
                'extract the ID, and substitute it in place of AUTO.',
            ),
        },
        {
            "name": "review",
            "category": "greenfield",
            "timeout": 900,
            "max_turns": 35,
            "setup": None,
            "prompt": build_prompt(
                "review", "shaktra-review",
                skill_args="review the completed story",
                validator_cmd=_v("validate_review.py", d, "AUTO"),
                extra='Note: "AUTO" means find the story ID from the previous dev step. '
                'Check .shaktra/stories/ for the story, substitute its ID for AUTO.',
            ),
        },
        # --- Hotfix (independent) ---
        {
            "name": "tpm-hotfix",
            "category": "hotfix",
            "timeout": 600,
            "max_turns": 30,
            "setup": lambda td: setup_greenfield(td),
            "prompt": build_prompt(
                "tpm-hotfix", "shaktra-tpm",
                skill_args="hotfix: fix the login timeout bug causing 500 errors",
                validator_cmd=_v("validate_tpm.py", d, "--hotfix"),
            ),
        },
        # --- Brownfield chain ---
        {
            "name": "init-brownfield",
            "category": "brownfield",
            "timeout": 300,
            "max_turns": 5,
            "setup": lambda td: setup_brownfield(td),
            "prompt": build_smoke_prompt("init-brownfield", "shaktra-doctor")
            + f'\n\nAlso run: python3 {_v("validate_init.py", d, "BrownfieldTest", "brownfield", "python")}\nPrint the validator output. If all checks pass, VERDICT: PASS. Otherwise VERDICT: FAIL.',
        },
        {
            "name": "analyze",
            "category": "brownfield",
            "timeout": 900,
            "max_turns": 40,
            "setup": None,
            "prompt": build_prompt(
                "analyze", "shaktra-analyze",
                skill_args="analyze this codebase",
                validator_cmd=_v("validate_analyze.py", d),
            ),
        },
        # --- Bugfix (independent) ---
        {
            "name": "bugfix",
            "category": "bugfix",
            "timeout": 900,
            "max_turns": 40,
            "setup": lambda td: setup_bugfix(td),
            "prompt": build_prompt(
                "bugfix", "shaktra-bugfix",
                skill_args="divide function raises ZeroDivisionError instead of ValueError on zero input",
                validator_cmd=_v("validate_bugfix.py", d),
            ),
        },
    ]
