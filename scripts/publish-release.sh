#!/usr/bin/env bash
#
# Publish the release branch locally.
# Mirrors the CI workflow (.github/workflows/publish-release.yml) for local use.
# Copies dist/ structure as-is, transforms marketplace.json, validates, and
# creates/updates the local 'release' branch.
#
# Usage: ./scripts/publish-release.sh [--push]
#   --push  Also push the release branch to origin after building

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

PUSH=false
if [[ "${1:-}" == "--push" ]]; then
  PUSH=true
fi

# --- Pre-flight checks ---

current_branch=$(git branch --show-current)
if [[ "$current_branch" != "main" ]]; then
  echo "Error: must be on the 'main' branch (currently on '$current_branch')"
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: working tree is not clean — commit or stash changes first"
  exit 1
fi

# --- Build ---

BUILD="$REPO_ROOT/release-build"
rm -rf "$BUILD"
mkdir "$BUILD"

echo "Building release tree..."

# Copy entire dist/ structure as-is (preserves plugin organization)
cp -r dist/* "$BUILD/"

# Remove __pycache__ if copied
find "$BUILD" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Transform marketplace.json: source "./dist/shaktra" -> "./shaktra"
mkdir -p "$BUILD/.claude-plugin"
python3 -c "
import json, pathlib
p = pathlib.Path('.claude-plugin/marketplace.json')
data = json.loads(p.read_text())
for plugin in data.get('plugins', []):
    if plugin.get('source') == './dist/shaktra':
        plugin['source'] = './shaktra'
(pathlib.Path('$BUILD') / '.claude-plugin' / 'marketplace.json').write_text(
    json.dumps(data, indent=2) + '\n')
"

# Copy marketplace README for release branch root
cp README-marketplace.md "$BUILD/README.md"

# Copy CHANGELOG for user visibility
cp CHANGELOG.md "$BUILD/CHANGELOG.md"

# Minimal .gitignore
cat > "$BUILD/.gitignore" << 'GITIGNORE'
.DS_Store
__pycache__/
*.py[codz]
.claude/
.local/
.venv/
GITIGNORE

# --- Validate ---

echo "Validating release structure..."
errors=0

# marketplace.json exists at root
if [ ! -f "$BUILD/.claude-plugin/marketplace.json" ]; then
  echo "  FAIL: marketplace.json missing"
  errors=$((errors + 1))
fi

# Validate each plugin listed in marketplace.json
plugin_count=$(python3 -c "
import json
data = json.load(open('$BUILD/.claude-plugin/marketplace.json'))
print(len(data.get('plugins', [])))
")
echo "Found $plugin_count plugin(s)"

# Check shaktra plugin structure
if [ ! -f "$BUILD/shaktra/.claude-plugin/plugin.json" ]; then
  echo "  FAIL: shaktra/plugin.json missing"
  errors=$((errors + 1))
fi

# Count agents in shaktra (15 expected)
agent_count=$(ls "$BUILD/shaktra/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$agent_count" -ne 15 ]; then
  echo "  FAIL: expected 15 agents in shaktra, found $agent_count"
  errors=$((errors + 1))
fi

# Count skills in shaktra (20 expected)
skill_count=$(ls -d "$BUILD/shaktra/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')
if [ "$skill_count" -ne 20 ]; then
  echo "  FAIL: expected 20 skills in shaktra, found $skill_count"
  errors=$((errors + 1))
fi

# Count scripts in shaktra (8 expected)
script_count=$(ls "$BUILD/shaktra/scripts/"*.py 2>/dev/null | wc -l | tr -d ' ')
if [ "$script_count" -ne 8 ]; then
  echo "  FAIL: expected 8 scripts in shaktra, found $script_count"
  errors=$((errors + 1))
fi

# hooks.json present in shaktra
if [ ! -f "$BUILD/shaktra/hooks/hooks.json" ]; then
  echo "  FAIL: shaktra/hooks.json missing"
  errors=$((errors + 1))
fi

# No dev-only files
for devfile in CLAUDE.md docs tests Resources .shaktra-test.log .claude .local .venv dist; do
  if [ -e "$BUILD/$devfile" ]; then
    echo "  FAIL: dev-only '$devfile' found in release build"
    errors=$((errors + 1))
  fi
done

if [ "$errors" -gt 0 ]; then
  echo "Validation failed with $errors error(s)"
  rm -rf "$BUILD"
  exit 1
fi

echo "Validation passed"

# --- Create/update release branch ---

MAIN_SHA=$(git rev-parse HEAD)

if git rev-parse --verify release >/dev/null 2>&1; then
  git checkout release
  # Remove all tracked files to start clean
  git rm -rf . >/dev/null 2>&1 || true
else
  git checkout --orphan release
  git rm -rf . >/dev/null 2>&1 || true
fi

# Copy build contents and clean up
cp -r "$BUILD"/. .
rm -rf "$BUILD"

# Stage and commit
git add -A
if git diff --cached --quiet; then
  echo "No changes to release branch"
else
  git commit -m "Release from main@${MAIN_SHA:0:7}"
  echo "Committed release from main@${MAIN_SHA:0:7}"
fi

# Return to main
git checkout main

if $PUSH; then
  # Force push required — release is an orphan branch rebuilt from scratch each time
  git push --force origin release
  echo "Pushed release branch to origin"
else
  echo ""
  echo "Release branch updated locally. To push:"
  echo "  git push --force origin release"
fi
