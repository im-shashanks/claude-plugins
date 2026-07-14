# Review Document Anatomy

How to generate an annotatable HTML review document from `templates/review-doc.html`.
Consumed by agents producing review docs (plans, designs, PRDs, analysis reports).

## Rules

1. **Start from the template verbatim.** Copy `review-doc.html`; never rewrite the
   `<style>` or `<script>` blocks. All behavior (annotation popover, question widgets,
   sidebar, Review Complete) lives there and matches `scripts/review_server.py`'s API.
2. **Replace the marker blocks:**
   - `<!-- SHAKTRA:TITLE -->…<!-- /SHAKTRA:TITLE -->` → document title (plain text).
   - `<!-- SHAKTRA:HEADER -->…<!-- /SHAKTRA:HEADER -->` → header text (plain text).
   - `<!-- SHAKTRA:CONTENT -->…<!-- /SHAKTRA:CONTENT -->` → the document body,
     including the markers themselves.
3. **Sections.** Wrap every logical section in:
   ```html
   <section class="rev-section" data-section-id="kebab-case-id">
     <h2>Section title</h2>
     ...content...
   </section>
   ```
   `data-section-id` values must be unique — annotations anchor to them. Choose ids
   that stay meaningful when read back from the annotations JSON (e.g. `target-architecture`,
   `phase-2-dev-slice`), because Claude sees only ids and quoted text, not the HTML.
4. **Inline questions.** Embed every open question for the reviewer as:
   ```html
   <div class="rev-question" data-question-id="q-unique-id">
     <span class="q-label">Open question</span>
     <p>The question text.</p>
     <textarea placeholder="Your answer…"></textarea>
     <button>Save answer</button><span class="q-saved"></span>
   </div>
   ```
   Place it inside the section it concerns. `data-question-id` values must be unique.
5. **Content markup.** Plain HTML only — `<p>`, `<ul>`, `<table>`, `<pre><code>`,
   `<code>`. No external resources (images, fonts, scripts, stylesheets): the server
   serves exactly one file. Escape `<`, `>`, `&` inside code blocks.
6. **Canonical artifact rule.** The HTML doc always *accompanies* a canonical
   markdown/YAML artifact — never replaces it. Generate the HTML from the canonical
   file's content; after review, apply changes to the canonical file first.

## Annotations JSON (what Claude reads back)

Written by `review_server.py` next to the doc (default
`.shaktra/reviews/<doc-stem>.annotations.json`):

```json
{
  "doc": "plan.html",
  "complete": true,
  "annotations": [
    { "id": "a1-3f9c2e", "created": "2026-07-14T10:15:00+00:00",
      "type": "annotation", "section_id": "target-architecture",
      "quote": "the selected text", "text": "reviewer comment",
      "question_id": null },
    { "id": "a2-77ab01", "created": "2026-07-14T10:16:00+00:00",
      "type": "question_response", "section_id": "phase-2-dev-slice",
      "quote": null, "text": "reviewer answer", "question_id": "q-plugin-root" }
  ]
}
```

- `type: "annotation"` — reviewer selected `quote` inside `section_id` and commented.
- `type: "question_response"` — reviewer answered the inline question `question_id`.
- A sibling `<doc-stem>.complete` flag file exists once Review Complete was clicked.
