# Design Doc Schema

Defines the structure of design documents in `.shaktra/designs/`. Sections scale by story tier — simpler stories need fewer sections.

## Sections

| # | Section | Content | Required At |
|---|---|---|---|
| 1 | **Problem Statement** | What problem this solves and why it matters now | Core |
| 2 | **Goals & Non-Goals** | Explicit scope boundaries — what this does and does not do | Core |
| 3 | **Proposed Solution** | Technical approach, key components, data flow | Core |
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
