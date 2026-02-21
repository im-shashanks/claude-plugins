# Claude Plugins

A curated collection of production-grade plugins for Claude Code.

## Shaktra -- AI Development Framework

What if Claude Code had a 14-agent engineering team behind every command? Shaktra gives you an Architect, PM, QA, Adversary, and 10 more specialized agents that enforce TDD, block bugs from merging, and scale ceremony to match complexity. Solo developers get team-level rigor; teams get consistency across every contributor.

### See it in action

Three commands take you from idea to production-ready, fully tested code:

```bash
# 1. Plan your feature
/shaktra:tpm "add OAuth 2.0 support to the API"
# -> Design doc, 8 stories generated, sprint planned

# 2. Implement with TDD enforcement
/shaktra:dev ST-001
# -> Tests written first, code passes, 36 quality checks, done

# 3. Review before merge
/shaktra:review ST-001
# -> 13-dimension analysis, P0 findings block merge automatically
```

### Highlights

- **14 specialized agents** -- Architect, PM, QA, Developer, Code Reviewer, Memory Retriever, Adversary, and more
- **TDD state machine** -- tests before code, enforced at every transition
- **P0 findings blocked from merge** -- hooks, not warnings
- **70-95% coverage by story tier** -- hotfix ships fast, features ship thoroughly
- **Brownfield + greenfield** -- 9-dimension codebase analysis for existing projects

### Install

```bash
# Marketplace
/plugin marketplace add https://github.com/im-shashanks/claude-plugins.git
/plugin install shaktra@cc-plugins

# Direct
/plugin install https://github.com/im-shashanks/claude-plugins.git
```

v0.3.0 | MIT License | [Full documentation](./shaktra/README.md)

---

*More plugins coming soon. Watch this space.*
