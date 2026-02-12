#!/bin/bash
#
# test-fixture-setup.sh
# Copies dist/ contents to the test directory for manual testing
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="${REPO_ROOT}/dist"
TEST_DIR="${HOME}/workspace/project_tests/shaktra-plugin-test"
CLAUDE_DIR="${TEST_DIR}/.claude"

echo "=== Shaktra Plugin Test Fixture Setup ==="
echo ""

# Check dist/ exists
if [ ! -d "$DIST_DIR" ]; then
    echo "Error: dist/ directory not found at ${DIST_DIR}"
    exit 1
fi

# Create test directory if it doesn't exist
if [ ! -d "$TEST_DIR" ]; then
    echo "Creating test directory: ${TEST_DIR}"
    mkdir -p "$TEST_DIR"
fi

# Clear existing .claude/ directory
if [ -d "$CLAUDE_DIR" ]; then
    echo "Clearing existing .claude/ directory..."
    rm -rf "$CLAUDE_DIR"
fi

# Create .claude/ directory
mkdir -p "$CLAUDE_DIR"

# Copy all contents from dist/ to .claude/
echo "Copying from dist/ to .claude/..."
cp -r "${DIST_DIR}/agents" "$CLAUDE_DIR/"
cp -r "${DIST_DIR}/skills" "$CLAUDE_DIR/"
cp -r "${DIST_DIR}/templates" "$CLAUDE_DIR/"
cp -r "${DIST_DIR}/hooks" "$CLAUDE_DIR/"
cp -r "${DIST_DIR}/scripts" "$CLAUDE_DIR/"

# Create sample test file if it doesn't exist
if [ ! -f "${TEST_DIR}/product-idea.md" ]; then
    echo "Creating sample product-idea.md..."
    cat > "${TEST_DIR}/product-idea.md" << 'EOF'
# Product Idea: TaskFlow

## Problem
Developers waste hours managing background job queues across multiple services.
Current solutions are either too complex (Celery) or too limited (simple Redis queues).

## Target Users
- Backend developers at startups (10-50 engineers)
- DevOps engineers managing distributed systems

## Proposed Solution
A simple, developer-friendly distributed task queue that:
- Works out of the box with minimal config
- Scales horizontally
- Has built-in observability

## Research Notes (from 5 developer interviews)
- "I spend 2 hours/week debugging failed jobs" - Dev at Series A startup
- "Celery docs are a nightmare" - Senior engineer
- "I just want something that works" - DevOps lead
- "Monitoring is always an afterthought" - Platform engineer
- "We ended up building our own because nothing fit" - CTO

## Competitors
- Celery: Powerful but complex, poor DX
- RQ: Simple but doesn't scale
- Sidekiq: Ruby-only
- Bull: Node-only
EOF
fi

# Summary
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Test directory: ${TEST_DIR}"
echo ""
echo "Contents of .claude/:"
ls -la "$CLAUDE_DIR"
echo ""
echo "To test:"
echo "  cd ${TEST_DIR}"
echo "  /shaktra:init"
echo "  /shaktra:pm"
echo ""
