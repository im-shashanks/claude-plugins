# Guided Entry Flow

When user enters just `/shaktra:pm` with no input, use AskUserQuestion to guide them.

## Question 1: Starting Point

```
AskUserQuestion:
  question: "How would you like to start?"
  header: "Start"
  options:
    - label: "Describe my product idea (Recommended)"
      description: "I'll guide you through defining your product from your description"
    - label: "Use my notes document"
      description: "I'll read and structure your existing notes or PRD draft"
    - label: "Start from research data"
      description: "I have interviews, surveys, or feedback — build from evidence"
    - label: "Do something specific"
      description: "Just PRD, personas, journey, or prioritize — not the full workflow"
  # "Other" is automatic — user can type custom input or say "help me figure out"
```

---

## Based on Q1 Response

### → "Describe my product idea"

1. Prompt: "What would you like to build? Describe the problem or product idea."
2. Capture their description as `user_context`
3. Ask **Question 2: Research Check**

### → "Use my notes document"

1. Prompt: "What's the path to your document?"
2. Read the document, use contents as `user_context`
3. Ask **Question 2: Research Check** (phrased as "Does your document contain research?")

### → "Start from research data"

1. Prompt: "What research should I analyze? Provide file paths or describe what you have."
2. Route directly to **research-first path** (skip Q2)

### → "Do something specific"

Ask follow-up:
```
AskUserQuestion:
  question: "Which operation?"
  header: "Operation"
  options:
    - label: "Create PRD"
      description: "Write a product requirements document"
    - label: "Analyze research"
      description: "Extract insights from interviews, surveys, feedback"
    - label: "Create personas"
      description: "Generate user personas from PRD or research"
    - label: "Map user journeys"
      description: "Create journey maps for existing personas"
  # "Other" handles: prioritize, brainstorm
```
Route to the selected standalone workflow.

### → "Other" / Custom Input

If user types something custom:
- If it looks like a product idea → treat as "Describe my product idea" flow
- If it looks like a file path → treat as "Use my notes document" flow
- If it expresses confusion → trigger **Guided Discovery**

---

## Question 2: Research Check

After collecting context (from description or document):

```
AskUserQuestion:
  question: "Do you have user research to inform this?"
  header: "Research"
  options:
    - label: "Yes, I have research data"
      description: "Interviews, surveys, support tickets, or user feedback I can analyze"
    - label: "No, starting fresh"
      description: "I'll work from assumptions — can validate with research later"
```

**If document was provided, adjust phrasing:**
> "Does your document contain research data (interview notes, survey results, user feedback)?"

**Based on answer:**
- **"Yes"** → Ask for research file paths (if not already in document), start **research-first path**
- **"No"** → Start **hypothesis-first path**

---

## Guided Discovery

For users who are confused or unsure where to start.

**Trigger:** User selects "Other" and types something like "I don't know", "help me", "not sure where to start", or expresses confusion.

```
AskUserQuestion:
  question: "What's your current situation?"
  header: "Situation"
  options:
    - label: "I have a problem I want to solve"
      description: "I know the pain point but haven't defined the solution yet"
    - label: "I have a product idea but it's rough"
      description: "I have a concept but need to flesh it out"
    - label: "I have user feedback to make sense of"
      description: "I've talked to users but need to synthesize insights"
    - label: "I have a PRD but need personas/journeys"
      description: "Requirements exist, need to understand users better"
```

**Route based on answer:**

| Answer | Action |
|---|---|
| "Problem to solve" | Start brainstorm (hypothesis-first path) |
| "Rough product idea" | Prompt for description, then hypothesis-first |
| "User feedback" | Prompt for research paths, then research-first |
| "PRD exists" | Check `.shaktra/prd.md`, then personas/journey workflow |

---

## Flow Summary

```
/shaktra:pm (no input)
        │
        ▼
   Q1: Starting Point ─────────────────────────────────┐
        │                                              │
   ┌────┴────┬──────────┬──────────┐                   │
   ▼         ▼          ▼          ▼                   ▼
Describe  Document  Research   Specific            "Other"
   │         │          │          │                   │
   ▼         ▼          │          ▼                   ▼
"What?"   "Path?"       │    Q: Which op?      Confused? → Discovery
   │         │          │          │                   │
   ▼         ▼          │          ▼                   │
   └────┬────┘          │    Route to                  │
        │               │    standalone                │
        ▼               │                              │
  Q2: Research? ────────┴──────────────────────────────┘
        │
   ┌────┴────┐
   ▼         ▼
  Yes        No
   │         │
   ▼         ▼
Research   Hypothesis
  Path       Path
```
