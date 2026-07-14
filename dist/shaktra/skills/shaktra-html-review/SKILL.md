---
name: shaktra-html-review
description: >
  Generate an annotatable HTML review document from a canonical artifact (plan,
  design, PRD, analysis report), serve it on a local review server, and turn the
  reviewer's annotations into actionable items. Internal skill — invoked by
  tpm/pm/analyze or directly when the user asks for an HTML review of a document.
user-invocable: true
---

# HTML Review Loop

Turns a canonical markdown/YAML artifact into a locally-served annotatable HTML
page, waits for the reviewer to finish, then converts every annotation into an
actionable item. The HTML doc **accompanies** the canonical artifact — it never
replaces it. After review, changes land in the canonical file first; regenerate
the HTML only if another review round is requested.

## Inputs

- `doc`: path to the canonical artifact to review (required).
- `output`: path for the generated HTML (default: same directory, same stem, `.html`).

## Step 1 — Generate the review document

Dispatch the **shaktra-doc-writer** agent in `review-doc` mode. Its prompt
names: the canonical artifact path, the output path, the template and spec
paths (`${CLAUDE_PLUGIN_ROOT}/templates/review-doc.html`,
`${CLAUDE_PLUGIN_ROOT}/templates/review-doc-spec.md`), and every open question
you want embedded as an inline widget (each with a unique id). The agent
writes the HTML to `output`; verify the file exists before serving.

## Step 2 — Serve and hand off to the reviewer

1. Launch the server as a **background** Bash task (never foreground — it blocks
   until the reviewer clicks Review Complete):

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_server.py <output>
   ```

2. Read the URL from the task's first stdout lines (`Review server running: http://127.0.0.1:<port>/<token>/`)
   and the annotations path from the second line.
3. Tell the user: the URL to open, that they can select text to annotate, answer
   the inline questions, and click **Review Complete** when done.
4. **End the turn.** Do not poll. The server process exiting is the completion
   signal — the background task's completion notification re-invokes you.
   (This is a local-machine feature: the browser must be able to reach
   127.0.0.1 on the machine running the server.)

## Step 3 — Read annotations and act

When the background task exits:

1. Read the annotations JSON (default `.shaktra/reviews/<doc-stem>.annotations.json`).
   Confirm `complete: true` and the sibling `<doc-stem>.complete` flag exists. If the
   process exited without the flag (crash, user killed it), report that and offer to relaunch.
2. Convert **every** annotation into exactly one actionable item:
   - `type: "annotation"` → a change request against `section_id` (the `quote` shows
     what the reviewer selected; `text` is their comment).
   - `type: "question_response"` → the answer to your inline question `question_id`;
     fold it into the pending decision it was blocking.
3. Present the full item list to the user, then apply agreed changes to the
   **canonical artifact** (not the HTML).
4. If the caller wants another round, regenerate the HTML from the updated
   canonical file and repeat from Step 2 (the server starts fresh; prior
   annotations stay on disk for the record).

## Failure modes

- **Server fails to bind / port conflict:** rerun with `--port 0` (default) —
  it picks a random free port.
- **No annotations but complete flag set:** the reviewer approved as-is; say so
  and proceed with zero changes.
- **Reviewer never finishes:** the background task stays alive. If the user asks
  to cancel, kill the task; partial annotations already on disk are still readable.

## Integration points

- `/shaktra:tpm` — offer an HTML design review after the design doc passes quality.
- `/shaktra:pm` — offer an HTML PRD review after PRD generation.
- `/shaktra:analyze` — offer an HTML report review after analysis completes.
  Each offers via AskUserQuestion; on acceptance, run this skill with the
  artifact path.
