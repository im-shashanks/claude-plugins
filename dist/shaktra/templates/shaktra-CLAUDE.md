# Shaktra Project State

This project uses **Shaktra**, an opinionated development framework that orchestrates specialized AI agents through TDD workflows with quality gates at every phase. Shaktra enforces test-driven development, maintains design decisions, tracks sprint velocity, and ensures code quality through automated checks.

## What's in `.shaktra/`

The `.shaktra/` directory stores all project-level development state — configuration, stories, decisions, sprint tracking, and analysis. This is where Shaktra agents read and write project information.

```
.shaktra/
├── CLAUDE.md                         # This file — project state documentation
├── settings.yml                      # Project configuration (language, test framework, coverage thresholds)
├── sprints.yml                       # Sprint tracking and velocity history
├── memory/
│   ├── principles.yml               # Synthesized principles (confidence-scored)
│   ├── anti-patterns.yml            # Failure patterns with alternatives
│   └── procedures.yml               # Workflow adaptation learnings
├── stories/                          # User stories (ST-001.md, ST-002.md, etc.)
├── designs/                          # Design documents created by architects
├── pm/                               # Product management artifacts (personas, journeys, research)
└── analysis/                         # Codebase analysis results (brownfield projects)
```

## Key Files Explained

### settings.yml
Project configuration and quality thresholds:
- **project:** Name, type (greenfield/brownfield), language, architecture
- **tdd:** Coverage thresholds by story tier (hotfix: 70%, S: 80%, M: 90%, L: 95%)
- **quality:** P1 findings threshold before blocking merge (default: 2)
- **review:** Verification test requirements, persistence settings
- **sprints:** Duration, velocity tracking, default story points

### sprints.yml
Sprint planning and velocity tracking:
- Current sprint number and status
- Sprint stories and progress
- Velocity history for capacity planning

### memory/principles.yml (confidence-scored)
Synthesized principles from cross-story observations:
- Design patterns, architectural conventions, coding constraints
- Each principle has confidence (0.2-1.0) that strengthens or weakens with evidence
- Categories: correctness, reliability, performance, security, maintainability, etc.
- Written by memory-curator agent after workflow completion

### memory/anti-patterns.yml
Failure patterns detected from repeated quality gate blocks:
- What went wrong, why it fails, what to do instead
- Proactively surfaced in story briefings when trigger patterns match

### memory/procedures.yml
Workflow-level learnings:
- Process adaptations discovered across multiple stories
- Informs orchestration and planning decisions

### stories/
User stories for implementation:
- Files named ST-001.md, ST-002.md, etc.
- Each story has: title, description, acceptance criteria, story point estimate, tier (XS/S/M/L), scope
- Created by `/shaktra:tpm` during planning
- Implemented by `/shaktra:dev` with TDD

### designs/
Design documents created during architecture/design phase:
- Architecture overviews
- API specifications
- Data model diagrams
- Component design docs

### pm/ (if using PM workflow)
Product management artifacts:
- Personas (user types)
- Journey maps (user flows)
- Research findings
- Prioritization frameworks (RICE, weighted)

### analysis/ (brownfield projects only)
Codebase analysis results from `/shaktra:analyze`:
- Architecture analysis (layering, modularity, dependencies)
- Testing assessment (coverage, test quality)
- Code quality metrics
- Security audit results
- Performance findings

## Using This State

The Shaktra agents read and update these files:
- **TPM** reads settings.yml, creates stories, updates sprints.yml
- **Developer** reads/updates stories, writes observations consolidated into principles
- **Code Reviewer** updates stories with review findings
- **Analyzer** generates analysis/ reports

When running Shaktra commands (`/shaktra:tpm`, `/shaktra:dev`, `/shaktra:review`, etc.), agents access this state to maintain project context across conversations.

## For Framework Questions

For complete Shaktra documentation (commands, TDD workflow, quality gates, severity taxonomy):
- See the plugin README.md that comes with Shaktra
- Run `/shaktra:help` in Claude Code
- This `.shaktra/CLAUDE.md` is project state documentation only
