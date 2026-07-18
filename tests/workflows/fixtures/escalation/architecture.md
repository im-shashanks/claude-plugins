# Architecture — Collaboration Platform

## Overview

A horizontally-scaled web backend. Multiple identical application server
instances run behind a load balancer; a client may be routed to any instance
on any request or reconnection. Instances are stateless with respect to user
sessions.

## Existing components

- **App servers** (stateless, N instances) — serve the editor and its APIs.
- **Postgres** — durable document storage and the OT/CRDT merge engine.
- **Load balancer** — round-robins client connections; no session affinity.

## Not yet decided / not covered here

This document describes the request/response web tier only. It does not
prescribe any realtime, event-fan-out, or cross-instance messaging mechanism —
none exists in the platform today.
