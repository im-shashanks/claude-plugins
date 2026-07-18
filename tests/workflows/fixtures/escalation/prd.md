---
id: PRD-ESC-001
title: "Realtime Collaboration Cursors"
version: "1.0.0"
status: approved
---

# Realtime Collaboration Cursors

## 1. Problem Statement

Users editing the same document cannot see each other's cursor positions,
causing edit collisions and duplicated work. We want live presence: each
user sees the others' cursors and selections update in real time.

## 2. Users & Personas

- **Co-editor Casey** — edits shared docs with 2-10 collaborators at once.

## 3. Goals & Success Metrics

- Cursor updates visible to peers within 200ms (p95).
- Support at least 25 concurrent editors per document.

## 4. Functional Requirements

- REQ-1 (must): Broadcast each user's cursor position and selection range to
  all other users viewing the same document.
- REQ-2 (must): Show a labeled colored caret for every remote user.
- REQ-3 (must): Remove a user's caret within 2s of them leaving.
- REQ-4 (should): Reflect selection ranges, not just caret points.

## 5. Scope

- In scope: presence broadcast, caret rendering, join/leave lifecycle.
- Out of scope: operational-transform/CRDT document merging (already exists).

## 6. Assumptions & Constraints

- Must run on the existing horizontally-scaled, multi-instance backend (many
  server processes behind a load balancer; a client may connect to any
  instance).

<!--
  DELIBERATE GAP for the escalation test: the PRD mandates a horizontally
  scaled, multi-instance backend and sub-200ms fan-out to peers, but it does
  NOT specify the realtime transport/fan-out mechanism (how presence events
  reach users connected to *different* server instances — e.g. a shared
  pub/sub bus, sticky sessions, a dedicated realtime service). The architect
  cannot design the broadcast path without this decision, and it is not
  answerable from the PRD or architecture doc — it must escalate.
-->
