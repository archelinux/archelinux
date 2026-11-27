#!/usr/bin/env bash
# Smoke-test installed workflow tools in a disposable Arch environment.
set -euo pipefail

wt --version
herdr --version
lazyagents --version
difft --version
playwright --version
openspec --version
bd --version
ccusage --version

# The system CLI must resolve its pinned test runner without npm or browsers.
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
cd "$work"
cat > example.spec.js <<'TEST'
const { test, expect } = require('@playwright/test');
test('runner can load a test', () => expect(true).toBe(true));
TEST
playwright_cli=$(readlink -f "$(command -v playwright)")
NODE_PATH="$(dirname -- "$playwright_cli")/.." playwright test
