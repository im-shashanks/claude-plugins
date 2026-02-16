# Changelog

All notable changes to the Shaktra plugin are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Version numbers follow [Semantic Versioning](https://semver.org/).

---

## [0.1.3] - 2026-02-15

### Added
- **File-read tracking in test framework** — captures every Read tool invocation (including sub-agent reads) via stream-json parsing, reports which plugin reference files each workflow actually consulted
- **Expected reads validation** — test definitions can declare `expected_reads` patterns (substring matches against file paths); dev test validates 8 patterns covering practices, quality checks, severity taxonomy, story, settings, and handoff files
- **Read manifest in test logs** — `.shaktra-test.log` gets a `[READ-MANIFEST]` section listing all unique files read during the test, with `[plugin]` and `[project]` path prefixes for readability
- **Reads in markdown reports** — per-test "Reference Files Read" section showing unique files read, plus "Expected Reads: N/N matched" with missing pattern details
- **Comprehensive automated test framework** — 19 end-to-end tests (14 positive + 5 negative) covering every `/shaktra:*` workflow
- **Standalone test architecture** — every test gets its own temp directory with isolated fixtures, no shared state
- **Negative test suite** — validates pre-flight checks catch invalid state (missing settings, blocked stories, sparse stories, incomplete dev, already-initialized projects)
- **Test fixtures for dev/review** — pre-built code files (Flask user registration app), handoff artifacts, design docs, and story YAML so dev and review tests run independently
- **Enhanced validators** — PM validator checks PRD content, personas, journeys, brainstorm notes; review validator checks findings and memory; bugfix validator checks diagnosis artifacts, root cause, bug stories
- **Negative test validator** — `validate_negative.py` for error detection, no-handoff, and no-progression checks
- **AskUserQuestion auto-answer override** — test agents auto-select first option instead of blocking on user input
- **Real test run documentation** — README includes actual bugfix (13min, 100% coverage) and dev (19min, 98% coverage, 29 tests) workflow logs

### Changed
- **Test runner uses stream-json** — switched from plain text capture to `--output-format stream-json --verbose`, enabling structured parsing of tool calls while preserving text output and verdict parsing
- **Test isolation** — removed shared directory chaining (`SHARED_DIR_GROUPS`); every test creates its own fresh temp dir
- **Dev test** uses explicit story ID (`ST-TEST-001`) with pre-built fixtures instead of depending on prior TPM run
- **Review test** includes completed handoff + actual Python code files instead of depending on prior dev run
- **Bugfix max_turns** increased (40→55) to allow memory capture and validator execution
- **Dev max_turns** increased (50→65) to allow quality phase, memory capture, and validator execution

---

## [0.1.2] - 2026-02-12

### Changed
- **Documentation restructured** for clear audience separation:
  - `dist/shaktra/README.md` — Comprehensive user guide (installation, commands, workflows, configuration, troubleshooting)
  - `README.md` — Developer-focused (architecture, contribution, development setup)
- **CLAUDE.md templates reworked** during `/shaktra:init`:
  - Project root `CLAUDE.md` — Project-specific skeleton (architecture, conventions, deployment)
  - `.shaktra/CLAUDE.md` — Documents what `.shaktra/` directory contains and how agents use it
- **CI workflow updated** — Release branch receives `dist/shaktra/README.md` directly (no transformation)
- **Path references fixed** — All references updated from `shaktra/` to `dist/shaktra/`

### Added
- Contributing guidelines section in user-facing README
- Version bump guidance in dev CLAUDE.md
- CHANGELOG.md (this file)

---

## [0.1.1] - 2026-02-12

### Added
- `/shaktra:status-dash` skill — Project dashboard with version check, sprint health, story pipeline, and quality overview
- Version check script (`check_version.py`) — Compares local plugin version against remote release

### Fixed
- `/shaktra:doctor` check failures resolved

---

## [0.1.0] - 2026-02-11

### Added
- Initial release of Shaktra plugin
- 12 specialized sub-agents (architect, tpm-quality, scrummaster, product-manager, sw-engineer, test-agent, developer, sw-quality, cba-analyzer, cr-analyzer, memory-curator, bug-diagnostician)
- 16 skills — 10 user-invocable (tpm, dev, review, analyze, general, bugfix, init, doctor, workflow, help) + 6 internal
- TDD state machine (PLAN → RED → GREEN → QUALITY → MEMORY → COMPLETE)
- Quality gates: 36 checks per TDD gate, 13 review dimensions
- P0-P3 severity taxonomy with automated enforcement
- Sprint-based planning with velocity tracking
- Ceremony scaling by story tier (XS/S/M/L)
- 4 blocking hooks (block-main-branch, validate-story-scope, validate-schema, check-p0-findings)
- Configurable thresholds via `.shaktra/settings.yml`
- Marketplace distribution support
