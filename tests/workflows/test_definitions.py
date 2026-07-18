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

import yaml

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
- **Two distinct stop types — do not confuse them:**
  - **Pre-flight prerequisite stops** (a skill's pre-flight reports missing settings / PRD / design doc / diagnosis, or a blocked/sparse story) are terminal and CORRECT: log it, print the verdict the validator expects, and END. Never fabricate the missing artifact, patch plugin files, or copy/modify workflow scripts to force progress.
  - **Mid-workflow clarifications** are different: when a WORKFLOW returns `needs_clarification` (e.g. a design gap the architect flagged, an ambiguous requirement) it is asking you to resolve an in-flight decision, not reporting a missing prerequisite. Resolve it the way the skill instructs — make a reasonable assumption (the auto-answer) and RE-INVOKE the workflow with that answer (`resumeFromRunId` + `gap_answers`/`clarifications`). Completing this escalation round-trip is the correct, expected behavior; do NOT halt on it.
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
- Briefing generation: `"MEMORY: briefing generated for <story_id> — <count> principles, <count> anti-patterns, <count> procedures included"`
- Briefing entry detail (for each entry included): `"MEMORY: briefing includes <PR-NNN|AP-NNN|PC-NNN> — <first 60 chars of text> (roles: <roles>)"`
- Agent briefing read: `"MEMORY: [agent-name] read briefing — <count> principles, <count> anti-patterns, <count> procedures applicable to role"`
- Agent applied principle: `"MEMORY: [agent-name] applying <PR-NNN> — <short description of how it was applied>"`
- Observation written: `"MEMORY: observation <OB-NNN> written — type=<type> importance=<N>"`
- Consistency check: `"MEMORY: consistency-check <OB-NNN> — <principle_id> relationship=<reinforce|weaken|contradict>"`
- Memory consolidation: `"MEMORY: consolidated — <N> principles (M reinforced, K new), <N> anti-patterns, <N> procedures"`
- Memory capture: `"MEMORY: memory_captured=true"`
- Agent complete: `"[agent-name] complete"`
"""


# ---------------------------------------------------------------------------
# Setup functions — prepare test_dir before each test
# ---------------------------------------------------------------------------
_TEST_MODE_SETTINGS = {
    "test_mode": {
        "max_quality_loops": 1,
        "max_stories": 2,
        "auto_answer": True,
    }
}


def _append_test_overrides(claude_md_path: Path) -> None:
    """Apply testing overrides: CLAUDE.md prose for the main loop, plus the
    test_mode settings block consumed by shaktra_context.py (v1.0.0)."""
    if claude_md_path.exists():
        with open(claude_md_path, "a") as f:
            f.write(_TEST_OVERRIDES)
    settings_path = claude_md_path.parent / ".shaktra" / "settings.yml"
    if settings_path.exists():
        with open(settings_path) as f:
            data = yaml.safe_load(f) or {}
        _deep_merge(data, dict(_TEST_MODE_SETTINGS))
        with open(settings_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


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
        "principles.yml": shaktra / "memory" / "principles.yml",
        "anti-patterns.yml": shaktra / "memory" / "anti-patterns.yml",
        "procedures.yml": shaktra / "memory" / "procedures.yml",
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
    """Dev setup: greenfield + story + design doc + seeded memory."""
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

    # Seed memory with prior learnings (overwrite empty templates)
    # These simulate knowledge from prior stories (PR-001, PR-002, AP-001, PC-001)
    # that are relevant to ST-TEST-001 (user registration endpoint).
    memory_dir = shaktra / "memory"
    for mem_file in ["principles.yml", "anti-patterns.yml", "procedures.yml"]:
        src = FIXTURES_DIR / "memory" / mem_file
        if src.exists():
            shutil.copy2(src, memory_dir / mem_file)

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


def setup_refactor(test_dir: Path) -> None:
    """Refactor setup: greenfield .shaktra + a smelly-but-tested module."""
    setup_git_init(test_dir)
    setup_shaktra_from_templates(test_dir, _greenfield_settings())
    src = FIXTURES_DIR / "refactor"
    for sub in ("src", "tests"):
        s = src / sub
        if s.exists():
            shutil.copytree(s, test_dir / sub, dirs_exist_ok=True)
    _append_test_overrides(test_dir / "CLAUDE.md")


def setup_dev_resume(test_dir: Path) -> None:
    """Dev resume setup: a small story with a handoff already through plan+tests.

    Verifies dev-tdd.js resumes at GREEN (skips the completed plan/tests phases)
    rather than re-running them. Self-contained (a small slugify story) so GREEN
    is fast and deterministic.
    """
    setup_git_init(test_dir)
    setup_shaktra_from_templates(test_dir, _greenfield_settings())
    shaktra = test_dir / ".shaktra"
    res = FIXTURES_DIR / "resume"
    story_dir = shaktra / "stories" / "ST-RESUME-001"
    story_dir.mkdir(parents=True, exist_ok=True)
    if (res / "ST-RESUME-001.yml").exists():
        shutil.copy2(res / "ST-RESUME-001.yml", shaktra / "stories" / "ST-RESUME-001.yml")
    if (res / "handoff-plan-tests.yml").exists():
        shutil.copy2(res / "handoff-plan-tests.yml", story_dir / "handoff.yml")
    if (res / "implementation_plan.md").exists():
        shutil.copy2(res / "implementation_plan.md", story_dir / "implementation_plan.md")
    if (res / "tests").exists():
        shutil.copytree(res / "tests", test_dir / "tests", dirs_exist_ok=True)
    _append_test_overrides(test_dir / "CLAUDE.md")


def setup_javascript_dev(test_dir: Path) -> None:
    """Non-Python dev setup: JavaScript project using Node's built-in test
    runner (node --test) — zero install, so the pipeline runs in the sandbox."""
    setup_git_init(test_dir)
    setup_shaktra_from_templates(test_dir, {
        "project": {
            "name": "JsProject", "type": "greenfield", "language": "javascript",
            "architecture": "layered", "test_framework": "node:test",
            "coverage_tool": "node --test --experimental-test-coverage",
            "package_manager": "npm",
        }
    })
    shaktra = test_dir / ".shaktra"
    js = FIXTURES_DIR / "javascript"
    if (js / "ST-JS-001.yml").exists():
        shutil.copy2(js / "ST-JS-001.yml", shaktra / "stories" / "ST-JS-001.yml")
    if (js / "package.json").exists():
        shutil.copy2(js / "package.json", test_dir / "package.json")
    _append_test_overrides(test_dir / "CLAUDE.md")


def setup_tpm_enrich(test_dir: Path) -> None:
    """TPM enrich setup: greenfield + a sparse medium story to enrich."""
    setup_greenfield(test_dir)
    shaktra = test_dir / ".shaktra"
    src = FIXTURES_DIR / "stories" / "enrich" / "ST-SPARSE-ENRICH.yml"
    if src.exists():
        shutil.copy2(src, shaktra / "stories" / "ST-SPARSE-ENRICH.yml")


def setup_tpm_sprint(test_dir: Path) -> None:
    """TPM sprint setup: greenfield + several complete stories to allocate."""
    setup_greenfield(test_dir)
    shaktra = test_dir / ".shaktra"
    src = FIXTURES_DIR / "sprint"
    if src.exists():
        for f in src.glob("ST-*.yml"):
            shutil.copy2(f, shaktra / "stories" / f.name)


def setup_analyze_targeted(test_dir: Path) -> None:
    """Analyze targeted setup: brownfield sample + a story-quality dimension request."""
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


def setup_pm_prioritize(test_dir: Path) -> None:
    """PM prioritize setup: greenfield + stories to RICE-rank."""
    setup_greenfield(test_dir)
    shaktra = test_dir / ".shaktra"
    src = FIXTURES_DIR / "sprint"
    if src.exists():
        for f in src.glob("ST-*.yml"):
            shutil.copy2(f, shaktra / "stories" / f.name)


def setup_incident_runbook(test_dir: Path) -> None:
    """Incident runbook setup: same fixtures as the post-mortem incident test."""
    setup_incident(test_dir)


def setup_trivial_dev(test_dir: Path) -> None:
    """Trivial-tier dev setup: greenfield + a 3-field trivial story.

    Verifies the tier gate matrix skips RED and comprehensive QUALITY.
    """
    setup_git_init(test_dir)
    setup_shaktra_from_templates(test_dir, _greenfield_settings())
    shaktra = test_dir / ".shaktra"
    src = FIXTURES_DIR / "stories" / "ST-TRIVIAL-001.yml"
    if src.exists():
        shutil.copy2(src, shaktra / "stories" / "ST-TRIVIAL-001.yml")
    _append_test_overrides(test_dir / "CLAUDE.md")


def _setup_analyze_seeded(test_dir: Path) -> None:
    """Brownfield sample + a pre-completed analysis (manifest + seed artifacts)."""
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
    analysis = test_dir / ".shaktra" / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    for f in ("tech-debt.yml", "dependencies.yml", "manifest.yml"):
        src = FIXTURES_DIR / "analyze-seed" / f
        if src.exists():
            shutil.copy2(src, analysis / f)
    _append_test_overrides(test_dir / "CLAUDE.md")


def setup_analyze_debt(test_dir: Path) -> None:
    _setup_analyze_seeded(test_dir)


def setup_analyze_dependency(test_dir: Path) -> None:
    _setup_analyze_seeded(test_dir)


def setup_incident_detection_gap(test_dir: Path) -> None:
    """Detection-gap setup: same fixtures as the post-mortem incident test."""
    setup_incident(test_dir)


def _write_gh_shim(test_dir: Path) -> None:
    """Write a fake `gh` onto a bin dir so PR-mode workflows run offline.

    Handles `gh auth status`, `gh pr view <n> --json ...` (canned metadata), and
    `gh pr diff <n>` (the real branch diff computed via git).
    """
    bin_dir = test_dir / ".bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    shim = bin_dir / "gh"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        "set -e\n"
        'if [ "$1" = "auth" ]; then echo "Logged in to github.com as tester"; exit 0; fi\n'
        'if [ "$1" = "pr" ] && [ "$2" = "view" ]; then\n'
        '  cat <<JSON\n'
        '{"title":"Add safe divide helper","body":"Adds divide() to math_utils. Closes #12.",'
        '"baseRefName":"main","headRefName":"feature/add-divide",'
        '"files":[{"path":"src/math_utils.py","additions":6,"deletions":0}]}\n'
        'JSON\n'
        '  exit 0\n'
        'fi\n'
        'if [ "$1" = "pr" ] && [ "$2" = "diff" ]; then\n'
        '  git -C "$(dirname "$0")/.." diff main...feature/add-divide 2>/dev/null || '
        'git diff main...feature/add-divide\n'
        '  exit 0\n'
        'fi\n'
        'echo "gh shim: unhandled args: $*" >&2; exit 0\n'
    )
    shim.chmod(0o755)


def setup_pr_review(test_dir: Path) -> None:
    """PR-review setup: a git repo with a feature branch diff + a gh shim.

    Exercises the pr-review code path (fetch change set via `gh pr diff`) rather
    than the story handoff. The diff intentionally contains a divide-by-zero
    gap so the reviewer has something real to find.
    """
    import subprocess as _sp
    setup_shaktra_from_templates(test_dir, _greenfield_settings())
    _run = lambda *c: _sp.run(list(c), cwd=test_dir, capture_output=True)
    _run("git", "init", "-b", "main")
    _run("git", "config", "user.email", "t@example.com")
    _run("git", "config", "user.name", "tester")
    src = test_dir / "src"
    src.mkdir(exist_ok=True)
    (src / "math_utils.py").write_text('def add(a, b):\n    return a + b\n')
    _run("git", "add", "-A")
    _run("git", "commit", "-m", "base: math_utils.add")
    _run("git", "checkout", "-b", "feature/add-divide")
    (src / "math_utils.py").write_text(
        'def add(a, b):\n    return a + b\n\n\n'
        'def divide(a, b):\n'
        '    # BUG: no zero-division guard, no type validation\n'
        '    return a / b\n'
    )
    _run("git", "add", "-A")
    _run("git", "commit", "-m", "feat: add divide helper")
    _run("git", "checkout", "main")
    _write_gh_shim(test_dir)
    _append_test_overrides(test_dir / "CLAUDE.md")


def setup_pr_adversarial(test_dir: Path) -> None:
    """PR adversarial-review setup: same repo + gh shim as pr-review."""
    setup_pr_review(test_dir)


def setup_escalation(test_dir: Path) -> None:
    """TPM design escalation setup: a PRD with a critical, unanswerable gap.

    The PRD mandates a horizontally-scaled multi-instance backend and <200ms
    peer fan-out but never specifies the realtime transport, and the arch doc
    explicitly lacks one. The architect must escalate; the PM cannot answer
    from sources; test-mode auto-answers and the SKILL re-invokes to completion.
    """
    setup_git_init(test_dir)
    setup_shaktra_from_templates(test_dir, {
        "project": {
            "name": "CollabCursors", "type": "greenfield", "language": "python",
            "architecture": "layered", "test_framework": "pytest",
            "coverage_tool": "coverage", "package_manager": "pip",
        }
    })
    shaktra = test_dir / ".shaktra"
    esc = FIXTURES_DIR / "escalation"
    for f in ("prd.md", "architecture.md"):
        if (esc / f).exists():
            shutil.copy2(esc / f, shaktra / f)
    _append_test_overrides(test_dir / "CLAUDE.md")


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
def setup_incident(test_dir: Path) -> None:
    """Incident setup: greenfield + completed bugfix artifacts."""
    setup_greenfield(test_dir)

    shaktra = test_dir / ".shaktra"

    # Copy diagnosis artifact
    diag_src = FIXTURES_DIR / "incident" / "diagnosis-BUG-TEST-001.yml"
    if diag_src.exists():
        shutil.copy2(diag_src, shaktra / "stories" / "diagnosis-BUG-TEST-001.yml")

    # Copy remediation story
    story_src = FIXTURES_DIR / "incident" / "ST-FIX-001.yml"
    if story_src.exists():
        shutil.copy2(story_src, shaktra / "stories" / "ST-FIX-001.yml")

    # Copy completed bugfix handoff
    story_dir = shaktra / "stories" / "ST-FIX-001"
    story_dir.mkdir(parents=True, exist_ok=True)
    handoff_src = FIXTURES_DIR / "incident" / "handoff-bugfix-complete.yml"
    if handoff_src.exists():
        shutil.copy2(handoff_src, story_dir / "handoff.yml")

    # Copy code files (the fixed implementation)
    code_src = FIXTURES_DIR / "greenfield" / "code"
    if code_src.exists():
        for item in code_src.iterdir():
            dest = test_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)


def setup_neg_no_diagnosis(test_dir: Path) -> None:
    """Greenfield setup with NO diagnosis artifact for incident negative test."""
    setup_greenfield(test_dir)
    # Deliberately no diagnosis artifact — incident skill should detect and block


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
            "prompt": (
                'You are an automated test runner for the Shaktra workflow ROUTER.\n'
                'STEP 1: Print "[TEST:workflow] Starting smoke test..."\n'
                'STEP 2: Invoke Skill("shaktra-workflow") with the request: '
                '"We need to add user authentication to our app."\n'
                'STEP 3: This smoke test verifies ROUTING ONLY. The moment the router '
                'announces its route decision (it should route to /shaktra:tpm for '
                'feature-planning intent), print the verdict — do NOT execute the '
                'routed planning pipeline.\n'
                '  [TEST:workflow] VERDICT: PASS   (router chose /shaktra:tpm)\n'
                '  [TEST:workflow] VERDICT: FAIL -- <reason>   (router errored or chose another route)'
            ),
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
            "max_turns": 100,
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
            "max_turns": 150,
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
            "timeout": 3000,
            "max_turns": 250,
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
            "timeout": 1500,
            "max_turns": 120,
            "setup": lambda td: setup_review(td),
            "prompt": build_prompt(
                "review", "shaktra-review",
                skill_args="review story ST-TEST-001",
                validator_cmd=_v("validate_review.py", d, "ST-TEST-001"),
            ),
        },
        # =================================================================
        # Adversarial review
        # =================================================================
        {
            "name": "adversarial-review",
            "category": "greenfield",
            "timeout": 1800,
            "max_turns": 150,
            "setup": lambda td: setup_review(td),
            "prompt": build_prompt(
                "adversarial-review", "shaktra-adversarial-review",
                skill_args="adversarial review story ST-TEST-001",
                validator_cmd=_v("validate_adversarial_review.py", d, "ST-TEST-001"),
            ),
        },
        # =================================================================
        # Hotfix
        # =================================================================
        {
            "name": "tpm-hotfix",
            "category": "hotfix",
            "timeout": 600,
            "max_turns": 80,
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
            "timeout": 1800,
            "max_turns": 150,
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
            "timeout": 1800,
            "max_turns": 150,
            "setup": lambda td: setup_bugfix(td),
            "prompt": build_prompt(
                "bugfix", "shaktra-bugfix",
                skill_args="divide function raises ZeroDivisionError instead of ValueError on zero input",
                validator_cmd=_v("validate_bugfix.py", d),
            ),
        },
        # =================================================================
        # Incident
        # =================================================================
        {
            "name": "incident",
            "category": "incident",
            "timeout": 1200,
            "max_turns": 120,
            "setup": lambda td: setup_incident(td),
            "prompt": build_prompt(
                "incident", "shaktra-incident",
                skill_args="post-mortem BUG-TEST-001",
                validator_cmd=_v("validate_incident.py", d, "BUG-TEST-001"),
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
            "name": "adversarial-review-incomplete-dev",
            "category": "negative",
            "timeout": 120,
            "max_turns": 10,
            "setup": lambda td: setup_neg_incomplete_dev(td),
            "prompt": build_prompt(
                "adversarial-review-incomplete-dev", "shaktra-adversarial-review",
                skill_args="adversarial review story ST-TEST-001",
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
        {
            "name": "incident-no-diagnosis",
            "category": "negative",
            "timeout": 120,
            "max_turns": 10,
            "setup": lambda td: setup_neg_no_diagnosis(td),
            "prompt": build_prompt(
                "incident-no-diagnosis", "shaktra-incident",
                skill_args="post-mortem BUG-MISSING-001",
                validator_cmd=_v("validate_negative.py", d, "no_incidents"),
            ),
        },
        # =================================================================
        # Extended coverage — previously-untested modes & mechanisms
        # =================================================================
        {
            "name": "refactor",
            "category": "extended",
            "timeout": 2400,
            "max_turns": 200,
            "setup": lambda td: setup_refactor(td),
            "prompt": build_prompt(
                "refactor", "shaktra-dev",
                skill_args="refactor src/order_pricing.py",
                validator_cmd=_v("validate_refactor.py", d),
            ),
        },
        {
            "name": "dev-resume",
            "category": "extended",
            "timeout": 1800,
            "max_turns": 160,
            "setup": lambda td: setup_dev_resume(td),
            "prompt": build_prompt(
                "dev-resume", "shaktra-dev",
                skill_args="resume story ST-RESUME-001",
                validator_cmd=_v("validate_resume.py", d, "ST-RESUME-001"),
            ),
        },
        {
            "name": "dev-javascript",
            "category": "extended",
            "timeout": 2400,
            "max_turns": 200,
            "setup": lambda td: setup_javascript_dev(td),
            "prompt": build_prompt(
                "dev-javascript", "shaktra-dev",
                skill_args="develop story ST-JS-001",
                validator_cmd=_v("validate_js_dev.py", d, "ST-JS-001"),
            ),
        },
        {
            "name": "tpm-enrich",
            "category": "extended",
            "timeout": 900,
            "max_turns": 120,
            "setup": lambda td: setup_tpm_enrich(td),
            "prompt": build_prompt(
                "tpm-enrich", "shaktra-tpm",
                skill_args="enrich story ST-SPARSE-ENRICH",
                validator_cmd=_v("validate_modes.py", d, "enrich", "ST-SPARSE-ENRICH"),
            ),
        },
        {
            "name": "tpm-sprint",
            "category": "extended",
            "timeout": 900,
            "max_turns": 120,
            "setup": lambda td: setup_tpm_sprint(td),
            "prompt": build_prompt(
                "tpm-sprint", "shaktra-tpm",
                skill_args="plan a sprint from the backlog stories in .shaktra/stories",
                validator_cmd=_v("validate_modes.py", d, "sprint"),
            ),
        },
        {
            "name": "analyze-targeted",
            "category": "extended",
            "timeout": 1200,
            "max_turns": 120,
            "setup": lambda td: setup_analyze_targeted(td),
            "prompt": build_prompt(
                "analyze-targeted", "shaktra-analyze",
                skill_args="analyze the coding practices and conventions",
                validator_cmd=_v("validate_modes.py", d, "analyze_targeted"),
            ),
        },
        {
            "name": "pm-prioritize",
            "category": "extended",
            "timeout": 900,
            "max_turns": 100,
            "setup": lambda td: setup_pm_prioritize(td),
            "prompt": build_prompt(
                "pm-prioritize", "shaktra-pm",
                skill_args="prioritize the backlog stories in .shaktra/stories using RICE",
                validator_cmd=_v("validate_modes.py", d, "pm_prioritize"),
            ),
        },
        {
            "name": "incident-runbook",
            "category": "extended",
            "timeout": 1200,
            "max_turns": 100,
            "setup": lambda td: setup_incident_runbook(td),
            "prompt": build_prompt(
                "incident-runbook", "shaktra-incident",
                skill_args="generate a runbook for BUG-TEST-001",
                validator_cmd=_v("validate_modes.py", d, "incident_runbook", "BUG-TEST-001"),
            ),
        },
        {
            "name": "tpm-design-escalation",
            "category": "extended",
            "timeout": 1500,
            "max_turns": 140,
            "setup": lambda td: setup_escalation(td),
            "prompt": build_prompt(
                "tpm-design-escalation", "shaktra-tpm",
                skill_args="create a design doc for the realtime collaboration cursors feature",
                validator_cmd=_v("validate_modes.py", d, "escalation", "CollabCursors"),
            ),
        },
        {
            "name": "dev-trivial",
            "category": "extended",
            "timeout": 1200,
            "max_turns": 120,
            "setup": lambda td: setup_trivial_dev(td),
            "prompt": build_prompt(
                "dev-trivial", "shaktra-dev",
                skill_args="develop story ST-TRIVIAL-001",
                validator_cmd=_v("validate_trivial_dev.py", d, "ST-TRIVIAL-001"),
            ),
        },
        {
            "name": "incident-detection-gap",
            "category": "extended",
            "timeout": 1200,
            "max_turns": 100,
            "setup": lambda td: setup_incident_detection_gap(td),
            "prompt": build_prompt(
                "incident-detection-gap", "shaktra-incident",
                skill_args="analyze the detection gap for BUG-TEST-001",
                validator_cmd=_v("validate_modes.py", d, "detection_gap", "BUG-TEST-001"),
            ),
        },
        {
            "name": "analyze-debt-strategy",
            "category": "extended",
            "timeout": 1200,
            "max_turns": 100,
            "setup": lambda td: setup_analyze_debt(td),
            "prompt": build_prompt(
                "analyze-debt-strategy", "shaktra-analyze",
                skill_args="produce a debt strategy from the existing analysis",
                validator_cmd=_v("validate_modes.py", d, "debt_strategy"),
            ),
        },
        {
            "name": "analyze-dependency-audit",
            "category": "extended",
            "timeout": 1200,
            "max_turns": 100,
            "setup": lambda td: setup_analyze_dependency(td),
            "prompt": build_prompt(
                "analyze-dependency-audit", "shaktra-analyze",
                skill_args="run a dependency audit from the existing analysis",
                validator_cmd=_v("validate_modes.py", d, "dependency_audit"),
            ),
        },
        {
            "name": "pr-review",
            "category": "extended",
            "timeout": 1500,
            "max_turns": 130,
            "setup": lambda td: setup_pr_review(td),
            "env": {"PATH": "{TEST_DIR}/.bin:" + os.environ.get("PATH", "")},
            "prompt": build_prompt(
                "pr-review", "shaktra-review",
                skill_args="review PR 1",
                validator_cmd=_v("validate_pr_review.py", d, "review"),
                extra=(
                    "\nPR-MODE LOGGING (mandatory): the moment you fetch the PR diff, "
                    "log `echo \"PR-GH-DIFF-FETCHED\" >> .shaktra-test.log`. When the "
                    "review finishes, log the final verdict: "
                    "`echo \"PR-VERDICT: <APPROVED|APPROVED_WITH_NOTES|CHANGES_REQUESTED|BLOCKED>\" >> .shaktra-test.log`."
                ),
            ),
        },
        {
            "name": "pr-adversarial",
            "category": "extended",
            "timeout": 1800,
            "max_turns": 150,
            "setup": lambda td: setup_pr_adversarial(td),
            "env": {"PATH": "{TEST_DIR}/.bin:" + os.environ.get("PATH", "")},
            "prompt": build_prompt(
                "pr-adversarial", "shaktra-adversarial-review",
                skill_args="adversarial review PR 1",
                validator_cmd=_v("validate_pr_review.py", d, "adversarial-review"),
                extra=(
                    "\nPR-MODE LOGGING (mandatory): the moment you fetch the PR diff, "
                    "log `echo \"PR-GH-DIFF-FETCHED\" >> .shaktra-test.log`. When the "
                    "review finishes, log the final verdict: "
                    "`echo \"PR-VERDICT: <pass|concern|blocked>\" >> .shaktra-test.log`."
                ),
            ),
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
