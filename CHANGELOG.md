# Changelog

All notable changes to the Shaktra plugin are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Version numbers follow [Semantic Versioning](https://semver.org/).

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
