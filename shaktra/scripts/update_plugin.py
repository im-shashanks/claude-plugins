#!/usr/bin/env python3
"""Update Shaktra plugin: fetch latest, clear cache, reinstall."""

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_NAME = "shaktra"


def find_install_entry(plugins_file: Path) -> tuple[str, dict]:
    """Find the shaktra@* entry in installed_plugins.json. Returns (key, entry)."""
    if not plugins_file.exists():
        return "", {}
    data = json.loads(plugins_file.read_text())
    for key, entries in data.get("plugins", {}).items():
        if key.startswith(f"{PLUGIN_NAME}@") and entries:
            return key, entries[0]
    return "", {}


def find_marketplace(marketplaces_file: Path, mkt_name: str) -> str:
    """Return the installLocation for a marketplace. Empty string if not found."""
    if not marketplaces_file.exists():
        return ""
    data = json.loads(marketplaces_file.read_text())
    entry = data.get(mkt_name, {})
    return entry.get("installLocation", "")


def check_for_update(plugin_root: str) -> dict:
    """Run check_version.py and return parsed result."""
    script = Path(plugin_root) / "scripts" / "check_version.py"
    if not script.exists():
        return {"status": "error", "message": "check_version.py not found"}
    try:
        result = subprocess.run(
            [sys.executable, str(script), plugin_root],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "check_version.py failed"}


def git_fetch_reset(mkt_path: str) -> bool:
    """Fetch and hard-reset the marketplace clone to origin/release."""
    try:
        subprocess.run(
            ["git", "-C", mkt_path, "fetch", "origin"],
            capture_output=True, text=True, timeout=30, check=True
        )
        subprocess.run(
            ["git", "-C", mkt_path, "reset", "--hard", "origin/release"],
            capture_output=True, text=True, timeout=15, check=True
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False


def get_commit_sha(mkt_path: str) -> str:
    """Get HEAD commit SHA from the marketplace clone."""
    try:
        result = subprocess.run(
            ["git", "-C", mkt_path, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, OSError):
        return ""


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Usage: update_plugin.py <plugin_root> [--force]"}))
        sys.exit(0)

    plugin_root = sys.argv[1]
    force = "--force" in sys.argv

    # Read local version
    local_plugin_json = Path(plugin_root) / ".claude-plugin" / "plugin.json"
    if not local_plugin_json.exists():
        print(json.dumps({"status": "error", "message": "plugin.json not found"}))
        sys.exit(0)
    local_version = json.loads(local_plugin_json.read_text()).get("version", "")

    # Find install entry
    plugins_dir = Path.home() / ".claude" / "plugins"
    plugins_file = plugins_dir / "installed_plugins.json"
    install_key, install_entry = find_install_entry(plugins_file)
    if not install_key:
        print(json.dumps({"status": "error", "message": "Shaktra not found in installed_plugins.json"}))
        sys.exit(0)

    mkt_name = install_key.split("@", 1)[1] if "@" in install_key else ""
    if not mkt_name:
        print(json.dumps({"status": "error", "message": "Cannot determine marketplace name"}))
        sys.exit(0)

    # Find marketplace clone path
    mkt_path = find_marketplace(plugins_dir / "known_marketplaces.json", mkt_name)
    if not mkt_path or not Path(mkt_path).exists():
        print(json.dumps({"status": "error", "message": f"Marketplace '{mkt_name}' clone not found"}))
        sys.exit(0)

    # Check for update (unless --force)
    if not force:
        version_info = check_for_update(plugin_root)
        if version_info.get("status") == "up_to_date":
            print(json.dumps({"status": "up_to_date", "version": local_version}))
            sys.exit(0)

    # Fetch latest from marketplace
    if not git_fetch_reset(mkt_path):
        print(json.dumps({"status": "error", "message": "Failed to fetch latest from marketplace"}))
        sys.exit(0)

    # Read marketplace.json to find source path
    mkt_manifest = Path(mkt_path) / ".claude-plugin" / "marketplace.json"
    if not mkt_manifest.exists():
        print(json.dumps({"status": "error", "message": "marketplace.json not found in clone"}))
        sys.exit(0)
    mkt_data = json.loads(mkt_manifest.read_text())
    source_rel = ""
    for plugin in mkt_data.get("plugins", []):
        if plugin.get("name") == PLUGIN_NAME:
            source_rel = plugin.get("source", "")
            break
    if not source_rel:
        print(json.dumps({"status": "error", "message": "Shaktra not found in marketplace.json"}))
        sys.exit(0)

    source_path = Path(mkt_path) / source_rel.lstrip("./")

    # Read new version
    new_plugin_json = source_path / ".claude-plugin" / "plugin.json"
    if not new_plugin_json.exists():
        print(json.dumps({"status": "error", "message": "plugin.json not found in fetched source"}))
        sys.exit(0)
    new_version = json.loads(new_plugin_json.read_text()).get("version", "")

    # Get commit SHA
    commit_sha = get_commit_sha(mkt_path)

    # Clear old cache and copy fresh files
    cache_base = plugins_dir / "cache" / mkt_name / PLUGIN_NAME
    if cache_base.exists():
        shutil.rmtree(cache_base)
    new_cache = cache_base / new_version
    shutil.copytree(str(source_path), str(new_cache))

    # Update installed_plugins.json
    installed_data = json.loads(plugins_file.read_text())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    updated_entry = {
        "scope": install_entry.get("scope", "local"),
        "installPath": str(new_cache),
        "version": new_version,
        "installedAt": install_entry.get("installedAt", now),
        "lastUpdated": now,
        "gitCommitSha": commit_sha,
    }
    if "projectPath" in install_entry:
        updated_entry["projectPath"] = install_entry["projectPath"]
    installed_data["plugins"][install_key] = [updated_entry]
    plugins_file.write_text(json.dumps(installed_data, indent=4) + "\n")

    print(json.dumps({
        "status": "updated",
        "old_version": local_version,
        "new_version": new_version,
        "restart_required": True,
    }))


if __name__ == "__main__":
    main()
