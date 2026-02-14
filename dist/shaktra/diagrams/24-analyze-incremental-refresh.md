# 24. Analyze Incremental Refresh

When the user requests an analysis refresh, the analyzer compares stored file checksums against current state to detect which source files have changed. Changed files are mapped to their affected dimensions (D1-D9), and only the stale dimensions are re-analyzed after user confirmation. This avoids re-running the full 2-stage pipeline for minor code changes.

```mermaid
flowchart TD
    Start(["User: 'refresh analysis'"]) --> ReadChecksums["Read\nchecksum.yml\n(stored file hashes)"]

    ReadChecksums --> Recompute["Recompute hashes\nfor all source files"]

    Recompute --> Compare{"Compare\nstored vs current\nhashes"}

    Compare -->|All match| UpToDate["All dimensions current\nNo refresh needed"]

    Compare -->|Differences found| MapFiles["Identify changed files\nand map to affected\ndimensions"]

    MapFiles --> Report["Report stale dimensions\ne.g. D1, D4, D7\nare affected by changes"]

    Report --> Confirm{"User confirms\nwhich dimensions\nto re-analyze"}

    Confirm -->|Selected| Rerun["Re-run selected\ndimensions only\n(CBA Analyzer per dimension)"]
    Confirm -->|Cancel| Cancel["Skip refresh"]

    Rerun --> UpdateHash["Update checksums\nfor re-analyzed files\nin checksum.yml"]

    UpdateHash --> UpdateManifest["Update manifest.yml\nwith new completion\ntimestamps"]

    UpdateManifest --> Done([Done])
    UpToDate --> Done
    Cancel --> Done
```

### Reading Guide

- **Top:** Reads stored checksums from the previous full or incremental analysis run
- **Center:** File-level hash comparison identifies which source files changed, then maps those files to the analysis dimensions they affect
- **Bottom:** Only user-confirmed stale dimensions are re-run, keeping the refresh targeted and efficient
- The file-to-dimension mapping uses the same static extraction logic from Stage 1 to determine which dimensions depend on which files

**Source:** `dist/shaktra/skills/shaktra-analyze/SKILL.md` (Incremental Refresh section)
