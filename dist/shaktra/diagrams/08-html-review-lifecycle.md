# 8. HTML Review Lifecycle (shaktra-html-review)

Annotatable HTML docs give the user a structured way to review plans, designs,
PRDs, and analysis reports. The HTML always accompanies a canonical
markdown/YAML artifact — never replaces it.

```mermaid
sequenceDiagram
    participant U as User (browser)
    participant C as Claude (skill)
    participant S as review_server.py<br/>(127.0.0.1, background)
    participant F as .shaktra/reviews/

    C->>C: generate HTML from canonical artifact<br/>(templates/review-doc.html + spec)
    C->>S: launch in background Bash
    S-->>C: URL with random token
    C->>U: "open http://127.0.0.1:PORT/token/"
    Note over C: turn ends — no polling
    U->>S: annotate selections, answer inline questions
    S->>F: atomic writes to <doc>.annotations.json
    U->>S: click "Review Complete"
    S->>F: write <doc>.complete flag
    S-->>C: process exit → task notification re-invokes Claude
    C->>F: read annotations JSON
    C->>C: one actionable item per annotation
    C->>U: apply agreed changes to the CANONICAL artifact
```

**Notes:** the server binds localhost only and serves exactly one document
under a random URL token; `POST /api/complete` is the only exit path besides
killing the task. Offered from tpm (design), pm (PRD), and analyze (report)
via AskUserQuestion.

**Source:** `dist/shaktra/scripts/review_server.py`, `dist/shaktra/skills/shaktra-html-review/SKILL.md`, `dist/shaktra/templates/review-doc-spec.md`
