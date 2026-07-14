# Guided Entry Flow

When the user enters just `/shaktra:pm` with no input, guide them with
AskUserQuestion. Two questions maximum before routing; "Other" is always
available for custom input.

## Question 1 — Starting Point ("How would you like to start?")

| Option | Description | Then |
|---|---|---|
| Describe my product idea (Recommended) | Guide the user from their description | Prompt "What would you like to build?"; capture as `user_context`; ask Q2 |
| Use my notes document | Read and structure existing notes or a PRD draft | Prompt for the path; read it as `user_context`; ask Q2 ("Does your document contain research?") |
| Start from research data | Build from interviews, surveys, or feedback | Prompt for research paths; route to **research-first** (skip Q2) |
| Do something specific | Just PRD, personas, journey, or prioritize | Ask which operation (PRD / analyze research / personas / journeys; "Other" covers prioritize, brainstorm); route to that standalone target |

**"Other" / custom input:** looks like a product idea → treat as "Describe";
looks like a file path → treat as "notes document"; expresses confusion
("I don't know", "help me") → **Guided Discovery** below.

## Question 2 — Research Check ("Do you have user research to inform this?")

| Answer | Route |
|---|---|
| Yes — interviews, surveys, tickets, feedback | Ask for research paths (if not already in the document) → **research-first** path |
| No — starting fresh | **hypothesis-first** path (assumptions marked explicitly, validate later) |

## Guided Discovery (for confused users)

Ask "What's your current situation?":

| Answer | Route |
|---|---|
| I have a problem I want to solve | Brainstorm → hypothesis-first |
| I have a rough product idea | Prompt for description → hypothesis-first |
| I have user feedback to make sense of | Prompt for research paths → research-first |
| I have a PRD but need personas/journeys | Check `.shaktra/prd.md` → personas/journeys targets |

## Paths

- **research-first** targets: `['research','personas','journeys','prd']`
- **hypothesis-first** targets: `['personas','journeys','prd']`

Both invoke `workflows/pm-artifacts.js` per the SKILL; the PRD is always
created last so personas and journeys inform it.
