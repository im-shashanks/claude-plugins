# Design Doc Schema

Defines the structure of design documents in `.shaktra/designs/`. Sections scale by story tier — simpler stories need fewer sections.

## Sections

| # | Section | Content | Required At |
|---|---|---|---|
| 1 | **Problem Statement** | What problem this solves and why it matters now | Core |
| 2 | **Goals & Non-Goals** | Explicit scope boundaries — what this does and does not do | Core |
| 3 | **Proposed Solution** | Technical approach, key components, data flow, pattern justification | Core |
| 4 | **API / Interface** | Public contracts — signatures, request/response shapes, error codes | Core |
| 5 | **Data Model** | Schema changes, new entities, storage decisions | Core |
| 6 | **Testing Strategy** | Test types, coverage targets, key test scenarios | Core |
| 7 | **Open Questions** | Unresolved decisions — each with owner and deadline | Core |
| 8 | **Alternatives Considered** | Other approaches evaluated with trade-off summary | Extended |
| 9 | **Migration Plan** | How to move from current state to target state safely | Extended |
| 10 | **Security Considerations** | Threat model, auth requirements, data sensitivity | Extended |
| 11 | **Observability Plan** | Logging, metrics, alerts, dashboards | Extended |
| 12 | **Performance Budget** | Latency targets, throughput, resource limits | Advanced |
| 13 | **Failure Modes & Recovery** | What can break, blast radius, recovery steps | Advanced |
| 14 | **Rollback Plan** | How to undo the change safely if issues arise | Advanced |
| 15 | **Dependencies & Risks** | External dependencies, timeline risks, mitigation | Advanced |

## Section 3 — Pattern Justification Requirements

Section 3 "Proposed Solution" must include a **Pattern Justification** subsection that documents architectural and design pattern choices. This ensures patterns are selected deliberately and persist via `decisions.yml`.

**Required content:**
- **Architecture alignment** — how this feature fits the project's architecture style (from `settings.project.architecture` or `structure.yml`). If introducing a new layer or module, explain where it sits in the existing structure.
- **Design patterns used** — name each pattern (repository, factory, strategy, adapter, etc.), which component uses it, and why it's the right fit. Reference `practices.yml` canonical examples when they exist.
- **Pattern consistency** — for brownfield: how does this align with existing patterns detected in `structure.yml` and `practices.yml`? If deviating from established patterns, justify the deviation.

**What NOT to include:**
- Don't catalog every GoF pattern — only document patterns you're actively choosing for this feature.
- Don't repeat quality principles (those are applied during implementation, not design).

### Architecture Style Selection Guide

When `settings.project.architecture` is empty (greenfield, first design), use this matrix to evaluate which style fits the project. Match the project's dominant characteristics — not every row needs to match, but the strongest signals should align.

| Characteristic | Layered | Hexagonal / Clean | MVC | Feature-Based | Event-Driven |
|---|---|---|---|---|---|
| **Best for** | CRUD apps, internal tools, scripts | Domain-heavy apps, external integrations | Web apps with server rendering | Large apps with independent features | Async processing, real-time, workflows |
| **Team size** | 1-3 devs | 3-10 devs | 1-5 devs | 5+ devs (parallel feature work) | 3+ devs |
| **Domain complexity** | Low-medium | Medium-high | Low-medium | Varies per feature | Medium-high |
| **External integrations** | Few, stable | Many or changing | Few | Per-feature | Many async sources |
| **Testability need** | Standard | High (ports mockable) | Standard | Per-feature isolation | High (handler isolation) |
| **Example** | Admin dashboard, CLI tool | Payment service, marketplace | Blog, CMS, traditional web | SaaS platform, large monolith | Order pipeline, notification system |

**Decision process for the architect:**
1. If `project.architecture` is set → use it. Justify alignment in Section 3.
2. If brownfield with `structure.yml` → match detected patterns. Justify any deviation.
3. If greenfield with no architecture set → evaluate the matrix against PRD requirements. Propose the best fit in Section 3 and record as an `important_decision` (category: consistency) so all future designs inherit it.

## Tier Mapping

| Story Tier | Required Sections |
|---|---|
| Trivial | No design doc |
| Small | No design doc |
| Medium | Core (sections 1-7) |
| Large | Core + Extended (1-11); Advanced (12-15) recommended |

## Format

Each section is a markdown heading (`## Section Name`) followed by prose. Sections should be concise — if a section exceeds 50 lines, consider splitting into sub-sections or linking to external detail.

## Storage

Design docs are stored as `<story_id>-design.md` in `.shaktra/designs/`. The story file does not duplicate design doc content — it references the design doc by path.
