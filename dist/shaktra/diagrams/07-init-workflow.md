# 7. Init Workflow

Project initialization follows a 6-step sequence that guards against double initialization, gathers project configuration interactively, creates the `.shaktra/` directory structure, and populates it from templates. The workflow produces a fully configured project ready for TPM planning or brownfield analysis.

```mermaid
flowchart TD
    Start(["/shaktra:init"]) --> PyYAML{"Step 0:\nPyYAML\ninstalled?"}

    PyYAML -->|No| BlockPy["Block: Install PyYAML\npip install pyyaml"]
    PyYAML -->|Yes| Guard{"Step 1:\n.shaktra/\nexists?"}

    Guard -->|Yes| BlockInit["Block: Already\ninitialized"]
    Guard -->|No| Gather["Step 2: Gather Info\nname, type, language,\narchitecture, test framework,\ncoverage tool, package manager"]

    Gather --> CreateDirs["Step 3: Create Directories\n.shaktra/\n.shaktra/memory/\n.shaktra/stories/\n.shaktra/designs/\n.shaktra/analysis/"]

    CreateDirs --> Templates["Step 4: Copy Templates\nsettings.yml (populated)\ndecisions.yml\nlessons.yml\nsprints.yml\nanalysis-manifest.yml\nshaktra-CLAUDE.md"]

    Templates --> ClaudeMD{"Step 5:\nCLAUDE.md\nexists?"}

    ClaudeMD -->|No| CreateMD["Create project\nCLAUDE.md from template"]
    ClaudeMD -->|Yes| SkipMD["Skip: report\nexisting file"]

    CreateMD --> Report["Step 6: Report Results\nProject summary\n+ next steps"]
    SkipMD --> Report

    Report --> Done([Done])
```

**Source:** `dist/shaktra/skills/shaktra-init/SKILL.md`
