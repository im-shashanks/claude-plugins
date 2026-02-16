---
description: Update Shaktra plugin (fetches latest, clears cache, reinstalls)
allowed-tools: Bash(python3 *)
---

# /shaktra-update

Run the Shaktra update script to check for and apply plugin updates.

Pass through any arguments the user provided (e.g., `--force`).

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/update_plugin.py ${CLAUDE_PLUGIN_ROOT} <args>
```

Parse the JSON output and present results to the user:

- **`"status": "up_to_date"`** — "Shaktra v{version} is already up to date."
- **`"status": "updated"`** — "Updated Shaktra v{old_version} → v{new_version}. **Restart Claude Code** (`/exit` then relaunch) to load the new version."
- **`"status": "error"`** — "Update failed: {message}"
