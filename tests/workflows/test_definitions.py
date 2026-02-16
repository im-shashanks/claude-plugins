#!/usr/bin/env python3
"""Test definitions for Shaktra workflow tests.

Each test is a dict with: name, category, timeout, max_turns, setup function,
prompt builder, and optional validator.

Every test is standalone — own temp dir, own fixtures, no shared state.
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
_TEST_OVERRIDES = """

---

## Testing Mode — Automated Workflow Test

This is an automated test run. The following overrides apply:

### Workflow Constraints
- **Quality review loops: 1 iteration maximum.** After the first review+fix pass, proceed to the next workflow step regardless of remaining findings.
- **Story creation: 2 stories maximum.** Create only 2 stories (pick the 2 most representative). This is sufficient to prove the workflow works.
- **Sprint planning: 1 sprint only.**
- **Do not ask the user for clarification.** Make reasonable assumptions and proceed.

### AskUserQuestion Override
- **Do NOT call AskUserQuestion.** Instead, auto-select and proceed:
  - "How would you like to start?" → "Describe my product idea"
  - "Do you have user research?" → "No, starting fresh"
  - "What size feature is this?" / PRD template → "Standard PRD (6-8 weeks)"
  - For any other question: select the FIRST option
- Log what you would have asked: `echo "[$(date +%H:%M:%S)] AUTO-ANSWER: <question> → <selected>" >> .shaktra-test.log`

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


def _greenfield_settings() -> dict:
    return {
        "project": {
            "name": "TestProject", "type": "greenfield", "language": "python",
            "architecture": "layered", "test_framework": "pytest",
            "coverage_tool": "coverage", "package_manager": "pip",
        }
    }


def setup_greenfield(test_dir: Path) -> None:
    """Full greenfield setup: git + .shaktra/ + PRD/arch fixtures."""
    setup_git_init(test_dir)
    setup_shaktra_from_templates(test_dir, _greenfield_settings())
    # Copy PRD and architecture for TPM
    shaktra = test_dir / ".shaktra"
    for f in ["prd.md", "architecture.md"]:
        src = FIXTURES_DIR / "greenfield" / f
        if src.exists():
            shutil.copy2(src, shaktra / f)

    _append_test_overrides(test_dir / "CLAUDE.md")


def setup_brownfield(test_dir: Path) -> None:
    """Brownfield setup: git + sample project + .shaktra/."""
    setup_git_init(test_dir)
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


def setup_dev(test_dir: Path) -> None:
    """Dev setup: greenfield + story + design doc + memory templates."""
    setup_git_init(test_dir)
    setup_shaktra_from_templates(test_dir, _greenfield_settings())

    shaktra = test_dir / ".shaktra"

    # Copy story fixture
    story_src = FIXTURES_DIR / "stories" / "ST-TEST-001.yml"
    if story_src.exists():
        shutil.copy2(story_src, shaktra / "stories" / "ST-TEST-001.yml")

    # Copy design doc
    design_src = FIXTURES_DIR / "greenfield" / "TestProject-design.md"
    if design_src.exists():
        shutil.copy2(design_src, shaktra / "designs" / "TestProject-design.md")

    # Copy PRD and architecture (dev may reference these)
    for f in ["prd.md", "architecture.md"]:
        src = FIXTURES_DIR / "greenfield" / f
        if src.exists():
            shutil.copy2(src, shaktra / f)

    _append_test_overrides(test_dir / "CLAUDE.md")


def setup_review(test_dir: Path) -> None:
    """Review setup: dev fixtures + completed handoff + code files."""
    setup_dev(test_dir)

    shaktra = test_dir / ".shaktra"
    story_dir = shaktra / "stories" / "ST-TEST-001"
    story_dir.mkdir(parents=True, exist_ok=True)

    # Copy handoff showing dev complete
    handoff_src = FIXTURES_DIR / "greenfield" / "handoff-complete.yml"
    if handoff_src.exists():
        shutil.copy2(handoff_src, story_dir / "handoff.yml")

    # Copy implementation plan
    plan_src = FIXTURES_DIR / "greenfield" / "implementation_plan.md"
    if plan_src.exists():
        shutil.copy2(plan_src, story_dir / "implementation_plan.md")

    # Copy code files for review
    code_src = FIXTURES_DIR / "greenfield" / "code"
    if code_src.exists():
        for item in code_src.iterdir():
            dest = test_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)


def setup_brownfield_no_shaktra(test_dir: Path) -> None:
    """Brownfield setup for init test: git + sample project but NO .shaktra/."""
    setup_git_init(test_dir)
    src_proj = FIXTURES_DIR / "brownfield" / "sample-project"
    if src_proj.exists():
        for item in src_proj.iterdir():
            dest = test_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# ---------------------------------------------------------------------------
# Negative test setup helpers
# ---------------------------------------------------------------------------
def setup_neg_no_settings(test_dir: Path) -> None:
    """Dev test with story but NO settings.yml."""
    setup_git_init(test_dir)
    shaktra = test_dir / ".shaktra"
    shaktra.mkdir(exist_ok=True)
    (shaktra / "stories").mkdir(exist_ok=True)
    story_src = FIXTURES_DIR / "stories" / "ST-TEST-001.yml"
    if story_src.exists():
        shutil.copy2(story_src, shaktra / "stories" / "ST-TEST-001.yml")
    # Deliberately NO settings.yml


def setup_neg_blocked_story(test_dir: Path) -> None:
    """Greenfield + blocked story + blocking prerequisite."""
    setup_greenfield(test_dir)
    shaktra = test_dir / ".shaktra"
    neg_dir = FIXTURES_DIR / "negative"
    for f in ["ST-BLOCKED-001.yml", "ST-PREREQ-001.yml"]:
        src = neg_dir / f
        if src.exists():
            shutil.copy2(src, shaktra / "stories" / f)


def setup_neg_sparse_story(test_dir: Path) -> None:
    """Greenfield + a medium story missing required fields."""
    setup_greenfield(test_dir)
    shaktra = test_dir / ".shaktra"
    src = FIXTURES_DIR / "negative" / "ST-SPARSE-001.yml"
    if src.exists():
        shutil.copy2(src, shaktra / "stories" / "ST-SPARSE-001.yml")


def setup_neg_incomplete_dev(test_dir: Path) -> None:
    """Dev fixtures + incomplete handoff (only plan phase done)."""
    setup_dev(test_dir)
    shaktra = test_dir / ".shaktra"
    story_dir = shaktra / "stories" / "ST-TEST-001"
    story_dir.mkdir(parents=True, exist_ok=True)
    src = FIXTURES_DIR / "negative" / "handoff-incomplete.yml"
    if src.exists():
        shutil.copy2(src, story_dir / "handoff.yml")


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
        # =================================================================
        # Smoke tests (simple, no team needed)
        # =================================================================
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
        {
            "name": "general",
            "category": "smoke",
            "timeout": 180,
            "max_turns": 10,
            "setup": lambda td: setup_greenfield(td),
            "prompt": build_smoke_prompt("general", "shaktra-general")
            + "\n\nQuestion: What are the tradeoffs between JWT and session-based authentication?",
        },
        {
            "name": "workflow",
            "category": "smoke",
            "timeout": 180,
            "max_turns": 10,
            "setup": lambda td: setup_greenfield(td),
            "prompt": build_smoke_prompt("workflow", "shaktra-workflow")
            + "\n\nWe need to add user authentication to our app.",
        },
        # =================================================================
        # Greenfield tests (standalone, own temp dir each)
        # =================================================================
        {
            "name": "init-greenfield",
            "category": "greenfield",
            "timeout": 300,
            "max_turns": 15,
            "setup": lambda td: setup_git_init(td),
            "prompt": build_prompt(
                "init-greenfield", "shaktra-init",
                skill_args="Initialize this project with: name=TestProject, type=greenfield, language=python, architecture=layered, test_framework=pytest, coverage_tool=coverage, package_manager=pip",
                validator_cmd=_v("validate_init.py", d, "TestProject", "greenfield", "python"),
            ),
        },
        {
            "name": "pm",
            "category": "greenfield",
            "timeout": 900,
            "max_turns": 30,
            "setup": lambda td: setup_greenfield(td),
            "prompt": build_prompt(
                "pm", "shaktra-pm",
                skill_args="I want to build a user authentication system with registration, login, logout, and password reset for a Python Flask application",
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
            "timeout": 1800,
            "max_turns": 65,
            "setup": lambda td: setup_dev(td),
            "prompt": build_prompt(
                "dev", "shaktra-dev",
                skill_args="develop story ST-TEST-001",
                validator_cmd=_v("validate_dev.py", d, "ST-TEST-001"),
            ),
            "expected_reads": [
                # PLAN phase — sw-engineer loads practices
                "shaktra-tdd/testing-practices.md",
                "shaktra-tdd/coding-practices.md",
                # GREEN phase — developer loads security practices
                "shaktra-tdd/security-practices.md",
                # QUALITY — sw-quality loads check definitions
                "shaktra-quality/",
                # Reference — severity taxonomy used by quality gates
                "shaktra-reference/severity-taxonomy.md",
                # Story and settings — loaded by multiple agents
                "stories/ST-TEST-001.yml",
                "settings.yml",
                # Handoff — read/updated throughout
                "handoff.yml",
            ],
        },
        {
            "name": "review",
            "category": "greenfield",
            "timeout": 900,
            "max_turns": 35,
            "setup": lambda td: setup_review(td),
            "prompt": build_prompt(
                "review", "shaktra-review",
                skill_args="review story ST-TEST-001",
                validator_cmd=_v("validate_review.py", d, "ST-TEST-001"),
            ),
        },
        # =================================================================
        # Hotfix
        # =================================================================
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
        # =================================================================
        # Brownfield
        # =================================================================
        {
            "name": "init-brownfield",
            "category": "brownfield",
            "timeout": 300,
            "max_turns": 15,
            "setup": lambda td: setup_brownfield_no_shaktra(td),
            "prompt": _build_brownfield_init_prompt(d),
        },
        {
            "name": "analyze",
            "category": "brownfield",
            "timeout": 900,
            "max_turns": 40,
            "setup": lambda td: setup_brownfield(td),
            "prompt": build_prompt(
                "analyze", "shaktra-analyze",
                skill_args="analyze this codebase",
                validator_cmd=_v("validate_analyze.py", d),
            ),
        },
        # =================================================================
        # Bugfix
        # =================================================================
        {
            "name": "bugfix",
            "category": "bugfix",
            "timeout": 900,
            "max_turns": 55,
            "setup": lambda td: setup_bugfix(td),
            "prompt": build_prompt(
                "bugfix", "shaktra-bugfix",
                skill_args="divide function raises ZeroDivisionError instead of ValueError on zero input",
                validator_cmd=_v("validate_bugfix.py", d),
            ),
        },
        # =================================================================
        # Negative tests (error path — short timeout, should fail fast)
        # =================================================================
        {
            "name": "dev-no-settings",
            "category": "negative",
            "timeout": 120,
            "max_turns": 10,
            "setup": lambda td: setup_neg_no_settings(td),
            "prompt": build_prompt(
                "dev-no-settings", "shaktra-dev",
                skill_args="develop story ST-TEST-001",
                validator_cmd=_v("validate_negative.py", d,
                                 "no_handoff", "ST-TEST-001"),
            ),
        },
        {
            "name": "dev-blocked-story",
            "category": "negative",
            "timeout": 120,
            "max_turns": 10,
            "setup": lambda td: setup_neg_blocked_story(td),
            "prompt": build_prompt(
                "dev-blocked-story", "shaktra-dev",
                skill_args="develop story ST-BLOCKED-001",
                validator_cmd=_v("validate_negative.py", d,
                                 "no_handoff", "ST-BLOCKED-001"),
            ),
        },
        {
            "name": "dev-sparse-story",
            "category": "negative",
            "timeout": 120,
            "max_turns": 10,
            "setup": lambda td: setup_neg_sparse_story(td),
            "prompt": build_prompt(
                "dev-sparse-story", "shaktra-dev",
                skill_args="develop story ST-SPARSE-001",
                validator_cmd=_v("validate_negative.py", d,
                                 "no_handoff", "ST-SPARSE-001"),
            ),
        },
        {
            "name": "review-incomplete-dev",
            "category": "negative",
            "timeout": 120,
            "max_turns": 10,
            "setup": lambda td: setup_neg_incomplete_dev(td),
            "prompt": build_prompt(
                "review-incomplete-dev", "shaktra-review",
                skill_args="review story ST-TEST-001",
                validator_cmd=_v("validate_negative.py", d,
                                 "no_progression", "ST-TEST-001"),
            ),
        },
        {
            "name": "init-already-exists",
            "category": "negative",
            "timeout": 120,
            "max_turns": 5,
            "setup": lambda td: setup_greenfield(td),
            "prompt": build_smoke_prompt("init-already-exists", "shaktra-init")
            + '\n\nIf the skill reports the project is already initialized, that is the expected outcome. Print:\n  [TEST:init-already-exists] VERDICT: PASS\nIf it proceeds to initialize anyway, print:\n  [TEST:init-already-exists] VERDICT: FAIL',
        },
    ]


def _build_brownfield_init_prompt(d: str) -> str:
    """Build the brownfield init prompt — copies sample project first."""
    return build_prompt(
        "init-brownfield", "shaktra-init",
        skill_args="Initialize this project with: name=BrownfieldTest, type=brownfield, language=python, architecture=layered, test_framework=pytest, coverage_tool=coverage, package_manager=pip",
        validator_cmd=_v("validate_init.py", d, "BrownfieldTest", "brownfield", "python"),
        extra='\nNote: This is a brownfield project — existing code files are already present in the project directory.',
    )
