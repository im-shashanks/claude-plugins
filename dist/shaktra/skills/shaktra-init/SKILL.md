---
name: shaktra-init
description: >
  Initialize the Shaktra framework in the current project. Creates the .shaktra/ directory
  structure, populates configuration from templates, and sets up the project CLAUDE.md.
user-invocable: true
---

# /shaktra:init — Project Initialization

## Prerequisites

- Must be run from the root of a project directory
- `.shaktra/` directory must NOT already exist (prevents double-init)

## Execution Steps

### Step 0: Verify Prerequisites

Run `python3 -c "import yaml"` via Bash.

If the command fails (non-zero exit code), stop and report:
  "Shaktra requires PyYAML for its hook scripts.
   Install with: pip install pyyaml
   Then run /shaktra:init again."

Do not proceed to Step 1 until PyYAML is confirmed installed.

### Step 1: Guard Against Double Initialization

Check if `.shaktra/` directory exists in the current working directory.

- If it exists: stop immediately and report — "Shaktra is already initialized in this project. To reinitialize, remove the `.shaktra/` directory first."
- If it does not exist: proceed.

### Step 2: Gather Project Information

Ask the user for the following project details. Present these as a single prompt, offering sensible defaults where possible:

| Field | Prompt | Default | Valid Values |
|---|---|---|---|
| `name` | Project name? | Current directory name | Any string |
| `type` | Greenfield or brownfield? | greenfield | `greenfield`, `brownfield` |
| `language` | Primary language? | _(none)_ | `python`, `typescript`, `javascript`, `go`, `java`, `rust`, `ruby`, `php`, `csharp`, `other` |
| `architecture` | Architecture style? | _(none)_ | `layered`, `hexagonal`, `clean`, `mvc`, `feature-based`, `event-driven`, or blank |
| `test_framework` | Test framework? | Infer from language | `pytest`, `jest`, `vitest`, `mocha`, `go test`, `junit`, `rspec`, `phpunit`, `xunit`, or custom |
| `coverage_tool` | Coverage tool? | Infer from language | `coverage.py`, `istanbul/nyc`, `c8`, `go cover`, `jacoco`, `simplecov`, `phpunit`, `coverlet`, or custom |
| `package_manager` | Package manager? | Infer from language | `pip`, `poetry`, `uv`, `npm`, `yarn`, `pnpm`, `go mod`, `maven`, `gradle`, `cargo`, `bundler`, `composer`, `dotnet`, or custom |

**Inference rules for defaults:**
- `python` → `pytest`, `coverage.py`, `pip`
- `typescript` / `javascript` → `jest`, `istanbul/nyc`, `npm`
- `go` → `go test`, `go cover`, `go mod`
- `java` → `junit`, `jacoco`, `maven`
- `rust` → `cargo test`, `cargo-tarpaulin`, `cargo`
- `ruby` → `rspec`, `simplecov`, `bundler`
- `php` → `phpunit`, `phpunit`, `composer`
- `csharp` → `xunit`, `coverlet`, `dotnet`

### Step 3: Create Directory Structure

Create the following directories:

```
.shaktra/
.shaktra/memory/
.shaktra/stories/
.shaktra/designs/
.shaktra/analysis/
```

### Step 4: Copy and Populate Templates

Read template files from `${CLAUDE_PLUGIN_ROOT}/templates/` and write them into `.shaktra/`:

| Template Source | Destination | Post-Processing |
|---|---|---|
| `templates/settings.yml` | `.shaktra/settings.yml` | Replace empty `project:` fields with user's answers from Step 2 |
| `templates/decisions.yml` | `.shaktra/memory/decisions.yml` | Copy as-is |
| `templates/lessons.yml` | `.shaktra/memory/lessons.yml` | Copy as-is |
| `templates/sprints.yml` | `.shaktra/sprints.yml` | Copy as-is |
| `templates/analysis-manifest.yml` | `.shaktra/analysis/manifest.yml` | Copy as-is |

For `settings.yml`, populate the `project:` section with the gathered values:

```yaml
project:
  name: "<user's project name>"
  type: "<greenfield or brownfield>"
  language: "<user's language>"
  architecture: "<user's architecture style, or empty>"
  test_framework: "<user's test framework>"
  coverage_tool: "<user's coverage tool>"
  package_manager: "<user's package manager>"
```

**Architecture field notes:**
- For **greenfield**: ask user to choose an architecture style. If unsure, leave blank — the architect agent will propose one in the first design doc and it gets recorded in `decisions.yml`.
- For **brownfield**: leave blank at init. The `/shaktra:analyze` workflow detects the existing architecture (D1: structure.yml) and the user can populate this field after analysis.

All other sections (`tdd`, `quality`, `analysis`, `sprints`) retain their template defaults.

### Step 5: Handle Project CLAUDE.md

Read the framework CLAUDE.md template from `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md`.

**If no CLAUDE.md exists** in the project root:
- Create `CLAUDE.md` with the template content.

**If CLAUDE.md already exists** in the project root:
- Append the Shaktra section, wrapped in markers so it can be identified:

```markdown

<!-- SHAKTRA-FRAMEWORK-START -->
<content from templates/CLAUDE.md>
<!-- SHAKTRA-FRAMEWORK-END -->
```

Do NOT overwrite or modify existing CLAUDE.md content — only append.

### Step 6: Report Results

Display a summary of what was created:

```
Shaktra initialized successfully!

Project: <name> (<type>)
Language: <language>
Test Framework: <test_framework>
Coverage Tool: <coverage_tool>
Package Manager: <package_manager>

Created:
  .shaktra/settings.yml
  .shaktra/sprints.yml
  .shaktra/memory/decisions.yml
  .shaktra/memory/lessons.yml
  .shaktra/analysis/manifest.yml
  .shaktra/memory/
  .shaktra/stories/
  .shaktra/designs/
  .shaktra/analysis/
  CLAUDE.md (created | updated)

Next steps:
  1. Review .shaktra/settings.yml and adjust thresholds if needed
  2. Create your PRD: /shaktra:pm (or /shaktra:pm prd for just PRD)
  3. Place architecture doc at .shaktra/architecture.md
  4. For brownfield projects: run /shaktra:analyze to understand the existing codebase
  5. Run /shaktra:tpm to create design docs and stories
```
