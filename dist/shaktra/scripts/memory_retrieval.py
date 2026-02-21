#!/usr/bin/env python3
"""Determine memory retrieval tier and prepare chunks for Tier 3 retrieval."""

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def count_active_entries(memory_dir):
    """Count total active entries across all memory stores."""
    total = 0
    for filename in ("principles.yml", "anti-patterns.yml", "procedures.yml"):
        path = memory_dir / filename
        if not path.exists():
            continue
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        # Each file uses its own top-level key
        for key in data:
            entries = data[key]
            if isinstance(entries, list):
                total += sum(1 for e in entries if e.get("status", "active") == "active")
    return total


def read_settings(settings_path):
    """Read retrieval-related settings."""
    defaults = {
        "retrieval_tier1_max": 100,
        "retrieval_tier2_max": 500,
        "retrieval_chunk_size": 150,
    }
    if not Path(settings_path).exists():
        return defaults
    with open(settings_path) as f:
        data = yaml.safe_load(f) or {}
    memory = data.get("memory", {})
    return {k: memory.get(k, v) for k, v in defaults.items()}


def collect_all_entries(memory_dir):
    """Collect all active entries from all memory stores."""
    entries = []
    for filename, key_hint in [("principles.yml", "principles"),
                                ("anti-patterns.yml", "anti_patterns"),
                                ("procedures.yml", "procedures")]:
        path = memory_dir / filename
        if not path.exists():
            continue
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        for key in data:
            items = data[key]
            if isinstance(items, list):
                for item in items:
                    if item.get("status", "active") == "active":
                        item["_source_file"] = filename
                        entries.append(item)
    return entries


def write_chunks(story_dir, entries, chunk_size):
    """Split entries into chunks and write manifest for Tier 3."""
    chunks_dir = Path(story_dir) / ".chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    chunk_paths = []
    for i in range(0, len(entries), chunk_size):
        chunk_num = (i // chunk_size) + 1
        chunk_entries = entries[i:i + chunk_size]
        chunk_filename = f"chunk-{chunk_num:03d}.yml"
        chunk_path = chunks_dir / chunk_filename

        with open(chunk_path, "w") as f:
            yaml.dump({"entries": chunk_entries}, f, default_flow_style=False, sort_keys=False)

        chunk_paths.append({
            "path": f".chunks/{chunk_filename}",
            "entry_count": len(chunk_entries),
        })

    # Write manifest
    manifest = {"chunk_count": len(chunk_paths), "chunks": chunk_paths}
    with open(chunks_dir / "manifest.yml", "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

    return chunk_paths


def main():
    if len(sys.argv) < 3:
        print("Usage: memory_retrieval.py <story_dir> <settings_path>", file=sys.stderr)
        sys.exit(1)

    story_dir = Path(sys.argv[1])
    settings_path = sys.argv[2]
    memory_dir = story_dir.parents[1] / "memory"  # .shaktra/stories/<id> → .shaktra/memory

    settings = read_settings(settings_path)
    total = count_active_entries(memory_dir)

    if total <= settings["retrieval_tier1_max"]:
        tier = 1
        chunks = []
    elif total <= settings["retrieval_tier2_max"]:
        tier = 2
        chunks = []
    else:
        tier = 3
        all_entries = collect_all_entries(memory_dir)
        chunks = write_chunks(story_dir, all_entries, settings["retrieval_chunk_size"])

    result = {"tier": tier, "total_entries": total, "chunks": chunks}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
