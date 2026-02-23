<p align="center">
  <img src="./docs/img-res/shaktra-logo.png" alt="Shaktra" width="300">
</p>
<h1 align="center">S H A K T R A</h1>

<p align="center"><strong>Turn Claude Code into a 15-agent development team — from design to deployment, with zero bugs reaching production.</strong></p>

<p align="center">
  <code>v0.4.1</code> · MIT · Claude Code February 2025+ · macOS, Linux, Windows
</p>

---

## What You Get

<table>
<tr>
<td align="center" width="33%">

### 🎯 Quality Guaranteed

P0 findings **physically blocked** from merge. 70-95% coverage enforced automatically. Two-tier quality system catches issues before they ship.

</td>
<td align="center" width="33%">

### ⚡ Full Lifecycle

From PM → Architect → Developer → QA → Code Reviewer. Complete development workflow in one framework, not scattered across tools.

</td>
<td align="center" width="33%">

### 🔄 Scales With You

Hotfix (XS): 70% coverage, ships fast. Feature (L): 95% coverage, full architecture review. Ceremony matches complexity.

</td>
</tr>
</table>

**Visual workflow:** See the [TDD State Machine](./diagrams/02-tdd-state-machine.md) and [Agent Hierarchy](./diagrams/10-agent-hierarchy.md)

**Get started:** [Installation](#installation) • [Quick Start](#quick-start)

---

## See It In Action (example)

Three commands take you from idea to production-ready code:

```bash
# 1. Plan your feature
/shaktra:tpm "add OAuth 2.0 support to the API"
```
**Result:** Design doc created → 8 stories generated → Sprint planned (26 story points allocated)

```bash
# 2. Implement with TDD
/shaktra:dev ST-001
```
**Result:** PLAN → RED (tests written) → GREEN (code passes) → QUALITY (36 checks) → COMPLETE

```bash
# 3. Review before merge
/shaktra:review ST-001
```
**Result:** 13-dimension analysis → 6 verification tests → **APPROVED** or **BLOCKED** (P0 findings prevent merge)

```bash
# 4. Adversarial testing (optional — mutation + fault injection)
/shaktra:adversarial-review ST-001
```
**Result:** 18 mutations applied → 14 killed (78%) → adversarial input & fault probes → **PASS** or **BLOCKED**

**In 4 commands:** Idea → production code with 90% coverage, zero P0 findings, full design documentation, and adversarial verification.

[See the full decision tree](./diagrams/01-quick-start-decision-tree.md) →

---

## The Problem

❌ **Manual TDD is inconsistent** — Tests written after code (or not at all), coverage spotty, quality varies by developer.
❌ **Code reviews catch issues too late** — After implementation, when fixes are expensive.
❌ **Solo developers lack team capabilities** — No architect, no PM, no dedicated QA. You wear all hats, poorly.

**Shaktra solves this** with enforced quality gates at every phase and 15 specialized AI agents that give you team-level capabilities without the team.

---

## How Shaktra Gives You Superpowers

### 🤖 15-Agent Team. (*pssst! no hiring*)

From Architect to Adversary, specialized agents handle design, planning, implementation, testing, review, adversarial probing, and incident analysis. Solo developers get team-level capabilities; teams get consistency across all members.

**Agents:** Architect (design), Product Manager (requirements), Scrum Master (stories), SW Engineer (planning), Test Agent (TDD), Developer (implementation), SW Quality (story-level QA), Code Reviewer (app-level QA), Bug Diagnostician (root cause analysis), Memory Curator (institutional knowledge), Memory Retriever (briefing generation), CBA Analyzer (brownfield assessment), TPM Quality (artifact review), Adversary (mutation testing & fault injection), Incident Analyst (post-mortem & detection gaps)

[See full agent architecture](./docs/AGENTS.md) →

### 🛡️ Zero Bugs Reach Production

P0 findings **physically cannot merge** — hooks block the commit. P1/P2/P3 severity taxonomy ensures nothing critical slips through. Coverage thresholds (70-95%) enforced automatically per story tier.

**Merge gate logic:**
- Any P0 finding → **BLOCKED**, no exceptions
- P1 count > threshold → **CHANGES_REQUESTED**
- P1 within threshold → **APPROVED_WITH_NOTES**
- Clean → **APPROVED**

[See severity taxonomy](./docs/QUALITY.md) →

### ⚙️ TDD Without Compromise

Strict state machine: **PLAN → RED → GREEN → QUALITY → MEMORY → COMPLETE**. Tests always written before code. Quality gates at every transition. No shortcuts, no skipped phases.

**What gets enforced:**
- RED phase: Tests must fail for valid reasons (ImportError, not SyntaxError)
- GREEN phase: All tests pass + coverage meets tier threshold
- QUALITY phase: 36 checks across 8 dimensions, P0 blocks progress

[See TDD workflow](./docs/workflows/DEV.md) →

### 🧠 Learns From Every Story

Shaktra captures observations during each workflow — what worked, what failed, what surprised — and consolidates them into principles, anti-patterns, and procedures. Before the next story begins, a briefing filters relevant knowledge for each agent. Agents apply that knowledge during implementation, then write new observations that reinforce or challenge existing entries. Confidence scores track how well each piece of knowledge holds up: entries that keep proving true grow stronger, entries that get contradicted fade out and are archived. The result is a framework that genuinely improves the more you use it.

### 📊 Ceremony Scales With Complexity

**Hotfix (XS):** 70% coverage, minimal gates, ships in minutes. **Small (S):** 80% coverage, skip comprehensive review. **Medium (M):** 90% coverage, full TDD state machine. **Large (L):** 95% coverage, full architecture review, expanded quality gates.

You choose the tier, framework enforces the rigor. No one forgets to run tests or skips coverage checks — it's physically impossible. Three quality tiers (Hooks → SW Quality → Code Review) all feed the same P0-P3 severity taxonomy and merge gate.

[See full quality philosophy](./docs/QUALITY.md) →

---

## Who Is This For?

### 👤 Solo Developers
**"I need the rigor of a team without the overhead"**

You get: Architect for design review, PM for requirements clarity, QA for systematic quality checks. No more "I'll test it later" or "I think this edge case works." The framework won't let you skip steps.

**Example:** `/shaktra:pm` → PRD → `/shaktra:tpm` → 12 stories → `/shaktra:dev ST-001` → production code with full test suite, no shortcuts possible.

### 👥 Engineering Teams
**"I need consistent quality across all developers"**

Every story gets 36 checks during TDD + 13-dimension review after completion. P0 findings auto-block merge. Junior and senior devs produce the same quality level because the gates are the same.

**Example:** Every team member follows identical TDD state machine. Quality is enforced by framework, not by code review lottery.

### 📋 Product Managers
**"I need executable artifacts, not just ideas"**

`/shaktra:pm "mobile checkout"` → Personas → Journey maps → PRD → `/shaktra:tpm` → Sprint-ready stories with acceptance criteria, test specs, and RICE prioritization.

**Example:** PM creates PRD, TPM breaks it into 15 stories, Product Manager scores them (RICE), Scrum Master allocates to sprints. You see exactly what ships when.

### 🏗️ Technical Leads
**"I need to scale architecture review without bottlenecking"**

SW Quality agent checks architecture at story level (during TDD). Code Reviewer checks app-level integration (after completion). You only review exceptions (P0 escalations, design decisions).

**Example:** 80% of quality work automated. You focus on strategic decisions, not "did you add tests for this?"

---

## Installation

### Marketplace (recommended)

```bash
/plugin marketplace add https://github.com/im-shashanks/claude-plugins.git
/plugin install shaktra@cc-plugins
```

### Direct from GitHub

```bash
/plugin install https://github.com/im-shashanks/claude-plugins.git
```

### Updating

Claude Code's plugin cache does not always refresh automatically. If you see stale behavior after an update:

```bash
# 1. Clear the cache
rm -rf ~/.claude/plugins/cache/

# 2. Restart Claude Code

# 3. Reinstall
/plugin install shaktra@cc-plugins
```

Check your version with `/shaktra:status-dash` — it compares local vs. latest release.

---

## Quick Start

### 🌱 Greenfield Project

```bash
/shaktra:init                      # Create .shaktra/ config
/shaktra:pm "describe your idea"   # Creates PRD (or skip if you have one)
/shaktra:tpm                       # Design → Stories → Sprint
/shaktra:dev ST-001                # Implement first story with TDD
/shaktra:review ST-001             # 13-dimension review before merge
```

### 🏢 Brownfield Codebase

```bash
/shaktra:init                      # Select "brownfield" type
/shaktra:analyze                   # 9-dimension systematic assessment
/shaktra:tpm                       # Plan next sprint (analysis informs design)
/shaktra:dev ST-001                # Start improving with TDD enforcement
```

### 🔥 Hotfix Needed

```bash
/shaktra:tpm hotfix: "fix NPE in UserService.getProfile"
# Creates XS story (70% coverage, minimal ceremony)
/shaktra:dev ST-010                # Fast TDD path, ships quickly
```

### 🐛 Bug Investigation

```bash
/shaktra:bugfix "checkout fails with 500 error on empty cart"
# 5-step diagnosis: triage → reproduce → root cause → blast radius → story
# Auto-creates remediation story, routes to TDD
```

[See all workflows](./docs/COMMANDS.md) →

---

## What Makes Shaktra Different

| Feature | BMAD | Speckit | GSD | **Shaktra** |
|---------|------|---------|-----|---------|
| **Quality Enforcement** | Adversarial review | Spec precision | Context engineering | **P0-P3 taxonomy + blocking hooks** ✅ |
| **Coverage Guarantees** | Not enforced | Not enforced | Not enforced | **70-95% by tier** ✅ |
| **TDD State Machine** | No | 6-phase spec flow | Flexible workflow | **PLAN→RED→GREEN→QUALITY** ✅ |
| **Agent Count** | 26 ✅ | 0 (commands) | Orchestrator + subagents | 15 |
| **Platform Support** | Any AI assistant ✅ | 15+ tools ✅ | Claude Code, OpenCode | **Claude Code only** ❌ |
| **Customization** | Builder module ✅ | Limited | State management | settings.yml only |
| **Community Size** | Large, established ✅ | Growing (GitHub) ✅ | 8.5k stars ✅ | New, building |
| **Brownfield Analysis** | Modules | Exploration mode | Limited | **9-dimension systematic** ✅ |

### Where Shaktra is Stronger
- **Formalized quality:** P0-P3 severity taxonomy enforced by hooks, blocks merge automatically
- **Enforced coverage:** 70-95% thresholds by tier, not optional
- **Strict TDD:** Tests always before code, state machine prevents shortcuts
- **Two-tier quality safety net:** SW Quality (story-level, 36 checks) + Code Reviewer (app-level, 13 dimensions)

### Where Shaktra is Weaker
- **Platform lock-in:** Claude Code only (vs. BMAD/Speckit multi-platform)
- **No custom agents:** Can't extend like BMAD's Builder module
- **Smaller community:** New framework vs. established competitors
- **Rigid workflow:** TDD state machine less flexible than GSD's "No Agile BS" approach

### Choose Shaktra If
Quality and TDD discipline matter more than platform flexibility or custom workflows. You want P0 findings physically blocked, not just warned.

**Choose BMAD if:** Multi-platform support or custom agents. **Choose Speckit if:** Spec-driven development with GitHub. **Choose GSD if:** Speed over ceremony.

---

## Learn More

### Core Documentation
- 📖 [Complete Command Reference](./docs/COMMANDS.md) — All 15 workflows detailed
- ⚙️ [Configuration Guide](./docs/CONFIGURATION.md) — settings.yml, hooks, thresholds
- 🔍 [Troubleshooting](./docs/TROUBLESHOOTING.md) — Common issues and fixes
- 🎨 [Workflow Diagrams](./diagrams/) — 35 visual workflows

### Workflow Deep Dives
- [TPM Workflow](./docs/workflows/TPM.md) — Design → Stories → Sprint planning
- [Dev Workflow](./docs/workflows/DEV.md) — TDD state machine walkthrough
- [Review Workflow](./docs/workflows/REVIEW.md) — 13-dimension analysis
- [Analyze Workflow](./docs/workflows/ANALYZE.md) — Brownfield assessment

### Advanced Topics
- [Quality Philosophy](./docs/QUALITY.md) — P0-P3 taxonomy, merge gates, severity criteria
- [Agent Architecture](./docs/AGENTS.md) — 15 agents, orchestration, model allocation
- [State Files](./docs/STATE.md) — How Shaktra tracks memory, observations, and knowledge stores

### Community & Support
- [Report Issues](https://github.com/im-shashanks/shaktra-plugin/issues) | [Discussions](https://github.com/im-shashanks/shaktra-plugin/discussions)

**License:** MIT • **Version:** 0.4.1
