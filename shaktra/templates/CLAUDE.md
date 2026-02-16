# PROJECT_NAME Development

**Guidance:** This file documents your specific project — architecture decisions, conventions, development workflow, and team context. Fill in each section with details relevant to your project.

---

## Project Overview

**Status:** _(provide current project status)_

**Purpose:** _(what problem does this project solve?)_

**Scope:** _(what's included, what's out of scope)_

### Key Technologies
- **Language:** _(e.g., Python 3.11, TypeScript 5.0)_
- **Framework:** _(e.g., FastAPI, React, Django)_
- **Architecture:** _(e.g., layered, hexagonal, clean, feature-based)_
- **Key Libraries:** _(list major dependencies)_

---

## Development Workflow

### Setup

**Prerequisites:**
- _(List required tools, versions, system requirements)_

**Quick start:**
```bash
# _(provide setup commands)_
```

### Local Development

_(Describe how to run the project locally, run tests, etc.)_

### Code Style

- **Conventions:** _(describe naming, file organization, patterns)_
- **Formatting:** _(linter, formatter settings)_
- **Testing:** _(test naming, organization, coverage expectations)_

---

## Architecture

### System Design

_(Describe the overall system architecture)_

**Key components:**
- _(Component 1: purpose, responsibilities)_
- _(Component 2: purpose, responsibilities)_
- _(Component 3: purpose, responsibilities)_

### Data Model

_(Describe main entities, relationships, data flow)_

### External Dependencies

_(List external services, APIs, integrations and their purpose)_

---

## Quality Standards

### Testing Requirements

- **Unit tests:** _(coverage threshold, scope)_
- **Integration tests:** _(scope, critical paths)_
- **Acceptance criteria:** _(what makes a test pass/fail)_

### Code Review

- **Key focus areas:** _(security, performance, maintainability, etc.)_
- **Required approvals:** _(1 reviewer, 2 reviewers, specific people?)_
- **Common issues:** _(frequent findings, patterns to watch for)_

### Performance

- **Critical paths:** _(operations that must be fast)_
- **Acceptable latencies:** _(target response times, throughput)_
- **Resource constraints:** _(memory, CPU, disk limits)_

---

## Deployment & Operations

### Environments

- **Development:** _(how to deploy locally)_
- **Staging:** _(staging server, deployment process)_
- **Production:** _(production server, deployment process)_

### Deployment Checklist

- [ ] _(All tests passing)_
- [ ] _(Code review approved)_
- [ ] _(Database migrations run)_
- [ ] _(Secrets configured)_
- [ ] _(Deployment documentation updated)_

### Rollback Plan

_(How to rollback a deployment if something goes wrong)_

### Monitoring & Logging

- **Key metrics:** _(what to monitor in production)_
- **Log levels:** _(what gets logged at each level)_
- **Alerting:** _(what warrants an alert)_

---

## Known Limitations & Tech Debt

### Current Limitations

_(List things the project can't do yet or does poorly)_

### Technical Debt

_(List known issues, shortcuts, areas needing refactoring)_

---

## Decision Log

_(Record important architectural and design decisions here, or reference where they are tracked)_

---

## Contributing

### Before You Start

- Familiarize yourself with the architecture (above)
- Read the quality standards (above)
- Review the decision log
- Check for existing issues/PRs

### Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Implement with TDD (tests → code)
3. Submit PR with:
   - Description of what/why
   - Link to relevant issue
   - Evidence of testing
4. Address review feedback
5. Merge when approved
