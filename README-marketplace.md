# Claude Plugins

A curated collection of production-grade plugins for Claude Code.

---

<p align="center">
  <img src="./dist/shaktra/docs/img-res/shaktra-logo.png" alt="Shaktra" width="150">
</p>

## Shaktra — AI Development Framework · [Full documentation](./dist/shaktra/README.md)

What if Claude Code had a 15-agent engineering team behind every command?

Shaktra is a Claude Code plugin that runs a full agile engineering team inside your editor — planning, coding, reviewing, and blocking bad merges automatically. Solo developers get team-level rigor; teams get consistency across every contributor.

### See it in action

Three commands take you from idea to production-ready, fully tested code:

```bash
# 1. Plan your feature
/shaktra:tpm "add OAuth 2.0 support to the API"
# -> Design doc written. 8 stories created. Sprint ready to go.

# 2. Implement with TDD
/shaktra:dev ST-001
# -> Tests written first. Code written to pass them. 36 quality checks cleared.

# 3. Review before merge
/shaktra:review ST-001
# -> Found 2 P0 bugs. Merge blocked before they hit main.
```

All 9 workflows, agent roster, and configuration guide on the [plugin page](./dist/shaktra/README.md) →

### Highlights

- **15 specialized agents** — an Architect who designs, a QA who enforces, an Adversary who tries to break it, all working automatically
- **Tests always come first** — the workflow won't let you skip ahead, so coverage gaps never sneak into review
- **Critical bugs can't merge** — not flagged, not warned, physically blocked
- **Coverage scales with stakes** — a hotfix ships at 70%, a feature ships at 95%, automatically
- **Works on existing codebases** — 9-dimension analysis maps what you have before touching anything

### Install

```bash
/plugin marketplace add https://github.com/im-shashanks/claude-plugins.git
/plugin install shaktra@cc-plugins
```

`v0.4.1` · MIT License
