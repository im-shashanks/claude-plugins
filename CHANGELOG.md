# Changelog

All notable changes to the Shaktra plugin are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Version numbers follow [Semantic Versioning](https://semver.org/).

---

## [0.4.0] - 2026-02-21

### Added
- **`/shaktra:incident` skill** — Incident response workflow for post-incident analysis. Three intents: `post_mortem` (timeline reconstruction, root cause chain, impact assessment, detection gaps, action items), `runbook` (operational runbook generation from diagnosis data), `detection_gap` (quality gate coverage matrix, test gap classification, dimension gap analysis, recommendations). Requires a completed `/shaktra:bugfix` diagnosis as input.
- **`shaktra-incident-analyst` agent** — Senior incident response engineer agent (Opus) for blameless post-mortem analysis. Produces structured YAML artifacts for post-mortems, runbooks, and detection gap reports. References diagnosis artifacts without re-investigating.
- **Incident response schemas** — YAML schemas for post-mortem, runbook, and detection gap artifacts in `incident-schema.md`.
- **Post-mortem methodology** — 5-step process: timeline reconstruction, root cause chain analysis, impact assessment, detection gap summary, action items.
- **Runbook template** — 6-section operational runbook: identification, severity assessment, immediate response, diagnosis shortcut, resolution, verification.
- **Detection gap framework** — 4-step gap analysis: quality gate coverage matrix, test gap classification, quality dimension gap analysis, recommendations with effort/impact ratings.
- **4 incident guard tokens** — `INCIDENT_CONTEXT_MISSING`, `INCIDENT_ANALYSIS_COMPLETE`, `INCIDENT_DETECTION_GAPS_FOUND`, `INCIDENT_MEMORY_CAPTURED`.
- **`incident` settings section** — `incident_confidence_multiplier`, `auto_detection_gap`, `runbook_auto_generate`, `action_item_default_priority` in settings.yml template.
- **2 new observation types** — `incident-learning` (importance 8-10) and `detection-gap` (importance 7-9) in observation guide.
- **Incident memory enhancements** — Confidence multiplier for incident-sourced observations, fast-track anti-pattern creation for high-importance incident learnings, role inference for incident/detection-gap tags.
- **2 new diagrams** — Incident response workflow (34) and incident agent dispatch (35).
- **2 E2E tests for incident response** — Happy-path test (post-mortem with auto detection gap + runbook) and negative test (missing diagnosis blocked).

### Changed
- **Component counts updated** — 15 agents (added incident-analyst), 20 skills (added incident), 35 diagrams, across all docs, CI, diagrams, doctor checks, and publish scripts.
- **`/shaktra:doctor`** — Updated expected counts (15 agents, 20 skills).
- **`/shaktra:bugfix` completion report** — Added next-step suggestion for `/shaktra:incident post-mortem` on production incidents.
- **`/shaktra:workflow` router** — Added Incident Response route with noun signals (post-mortem, runbook, incident review, detection gap).
- **`/shaktra:help` guide** — Added `/shaktra:incident` to workflow commands table and agent architecture diagram.
- **Documentation** — Updated AGENTS.md (incident-analyst entry), COMMANDS.md (incident entry), README (counts, examples), diagrams.

---

## [0.3.0] - 2026-02-20

### Added
- **`/shaktra:adversarial-review` skill** — Adversarial review workflow that treats code changes as behavioral hypotheses and systematically falsifies them through mutation testing, adversarial inputs, and fault injection. Dispatches 3 parallel adversary agents (mutation probes, input/boundary probes, fault/resilience probes). Produces execution-based risk assessment with mutation score and structured findings.
- **`shaktra-adversary` agent** — Chaos engineer agent for executing adversarial probes. Supports mutation testing with strict safety protocol (apply-run-restore-verify), adversarial input generation, and fault injection testing.
- **Mutation testing strategy** — 8 mutation operator categories (arithmetic, relational, logical, conditional, return value, exception, boundary, deletion) with safety protocol and surviving-mutation-to-severity mapping.
- **Adversarial probe strategies** — Input/boundary probes (null/empty, type mismatch, boundary values, injection, format) and fault/resilience probes (timeout, error response, partial response, connection refused, race condition, idempotency).
- **3 adversarial guard tokens** — `ADVERSARIAL_PASS`, `ADVERSARIAL_CONCERN`, `ADVERSARIAL_BLOCKED` in guard-tokens.md.
- **`adversarial_review` settings section** — `mutation_kill_threshold`, `max_mutations_per_function`, `mutation_timeout`, `max_adversarial_tests`, `test_persistence` in settings.yml template.
- **Memory system enhancements** — Trigger matching for memory entries, briefing dispatch across all workflows, workflow observation capture, and `shaktra-memory` internal skill with consolidation, observation, and retrieval guides.
- **`/shaktra:memory-stats` skill** — Memory inspector for auditing learned knowledge, checking entries near archive threshold, inspecting story briefings, and seeding new entries.
- **2 E2E tests for adversarial review** — Happy-path test (full pipeline with mutations and probes) and negative test (incomplete dev blocked).

---

## [0.2.0] - 2026-02-17

### Added
- **Tiered memory retrieval** — 3-tier architecture for briefing generation that scales with memory store size. Tier 1 (≤100 entries): inline generation. Tier 2 (≤500): dedicated memory-retriever agent. Tier 3 (500+): parallel chunk retrieval with consolidation.
- **`shaktra-memory-retriever` agent** — New sonnet-model agent with 3 modes (briefing, chunk, consolidate) for offloading context-heavy memory filtering from orchestrators.
- **`memory_retrieval.py` script** — Counts active memory entries, determines retrieval tier, and splits entries into chunks for Tier 3 processing.
- **`retrieval-guide.md`** — Shared retrieval algorithm (relevance scoring, dispatch templates) referenced by all orchestrators and the memory-retriever agent. Eliminates duplication across workflows.
- **5 new memory settings** — `briefing_confidence_threshold`, `retrieval_tier1_max`, `retrieval_tier2_max`, `max_briefing_entries`, `retrieval_chunk_size` in `settings.yml`.

### Changed
- **`/shaktra:dev` and `/shaktra:review`** — Replaced inline briefing generation with tier-aware retrieval (calls `memory_retrieval.py`, dispatches memory-retriever for Tier 2/3).
- **`/shaktra:bugfix`** — Added missing `procedures.yml` reading and `.observations.yml` creation.
- **`briefing-schema.md`** — Removed hardcoded 0.4 confidence threshold, now references `settings.memory.briefing_confidence_threshold`. Added tier selection table.
- **`/shaktra:doctor`** — Updated expected counts (13 agents, 8 scripts).
- **CI and publish script** — Updated structural validation counts (13 agents, 8 scripts).

---

## [0.1.5] - 2026-02-16

### Changed
- **CLAUDE.md template** — Removed all Shaktra-specific references from the project root CLAUDE.md template. Template is now a pure generic project documentation wireframe following CLAUDE.md best practices.
- **`/shaktra:init` skill** — Updated Step 5 and Step 6 descriptions to reflect cleaned-up template (removed `/init CLAUDE.md` references and Shaktra-specific cross-links).

---

## [0.1.4] - 2026-02-15

### Added
- **`/shaktra-update` command** — Automates plugin updates by fetching latest from marketplace, clearing stale cache, and reinstalling. Works around Claude Code's cache invalidation bug. Supports `--force` flag to reinstall even when already up to date.
- **`update_plugin.py` script** — End-to-end update handler: version check (reuses `check_version.py`), git fetch/reset of marketplace clone, cache cleanup, fresh copy, and `installed_plugins.json` update.
- **`commands/` directory** — New plugin directory for non-namespaced slash commands (simpler than skills for utility operations).

---

## [0.1.3] - 2026-02-15

### Fixed
- **Release branch README** — Root README is now a marketplace catalog (`README-marketplace.md`) instead of a copy of Shaktra's README, fixing broken relative links to `./docs/` and `./diagrams/`
- **Local publish script** — `scripts/publish-release.sh` rewritten to match CI workflow structure (multi-plugin `shaktra/` directory layout instead of flat root promotion)

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
