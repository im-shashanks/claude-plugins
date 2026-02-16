#!/usr/bin/env bash
#
# Publish the release branch locally.
# Promotes dist/shaktra/ to root, transforms marketplace.json, validates, and
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

# Promote dist/shaktra/ contents to root
cp -r dist/shaktra/agents "$BUILD/"
cp -r dist/shaktra/skills "$BUILD/"
cp -r dist/shaktra/hooks "$BUILD/"
cp -r dist/shaktra/scripts "$BUILD/"
cp -r dist/shaktra/templates "$BUILD/"
cp dist/shaktra/LICENSE "$BUILD/"

# Copy documentation referenced by README
cp -r dist/shaktra/docs "$BUILD/"
cp -r dist/shaktra/diagrams "$BUILD/"

# Copy workflow diagram for README (legacy path)
mkdir -p "$BUILD/Resources"
cp Resources/workflow.drawio.png "$BUILD/Resources/"

# Remove __pycache__ if copied
find "$BUILD" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# .claude-plugin with both files
mkdir -p "$BUILD/.claude-plugin"
cp dist/shaktra/.claude-plugin/plugin.json "$BUILD/.claude-plugin/"

# Transform marketplace.json: source "./dist/shaktra" -> "."
python3 -c "
import json, pathlib
p = pathlib.Path('.claude-plugin/marketplace.json')
data = json.loads(p.read_text())
for plugin in data.get('plugins', []):
    if plugin.get('source') == './dist/shaktra':
        plugin['source'] = '.'
(pathlib.Path('$BUILD') / '.claude-plugin' / 'marketplace.json').write_text(
    json.dumps(data, indent=2) + '\n')
"

# Copy user-facing README from plugin directory
cp dist/shaktra/README.md "$BUILD/README.md"

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

if [ ! -f "$BUILD/.claude-plugin/plugin.json" ]; then
  echo "  FAIL: plugin.json missing"
  errors=$((errors + 1))
fi

source_val=$(python3 -c "
import json
data = json.load(open('$BUILD/.claude-plugin/marketplace.json'))
print(data['plugins'][0]['source'])
")
if [ "$source_val" != "." ]; then
  echo "  FAIL: marketplace.json source is '$source_val', expected '.'"
  errors=$((errors + 1))
fi

agent_count=$(ls "$BUILD/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$agent_count" -ne 12 ]; then
  echo "  FAIL: expected 12 agents, found $agent_count"
  errors=$((errors + 1))
fi

skill_count=$(ls -d "$BUILD/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')
if [ "$skill_count" -ne 16 ]; then
  echo "  FAIL: expected 16 skills, found $skill_count"
  errors=$((errors + 1))
fi

script_count=$(ls "$BUILD/scripts/"*.py 2>/dev/null | wc -l | tr -d ' ')
if [ "$script_count" -ne 5 ]; then
  echo "  FAIL: expected 5 scripts, found $script_count"
  errors=$((errors + 1))
fi

if [ ! -f "$BUILD/hooks/hooks.json" ]; then
  echo "  FAIL: hooks.json missing"
  errors=$((errors + 1))
fi

if [ ! -d "$BUILD/docs" ]; then
  echo "  FAIL: docs/ missing (README links depend on it)"
  errors=$((errors + 1))
fi

if [ ! -d "$BUILD/diagrams" ]; then
  echo "  FAIL: diagrams/ missing (README links depend on it)"
  errors=$((errors + 1))
fi

for devfile in CLAUDE.md .claude .local .venv; do
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

# Stash current branch name so we can return to it
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
  git push origin release
  echo "Pushed release branch to origin"
else
  echo ""
  echo "Release branch updated locally. To push:"
  echo "  git push origin release"
fi
