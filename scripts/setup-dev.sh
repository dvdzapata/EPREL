#!/usr/bin/env bash
set -euo pipefail

# Install node deps for the mock server and create logs dir
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/tools/mcp-mock" || exit 0
if [ -f package.json ]; then
  echo "Installing npm deps for mcp-mock..."
  npm ci || npm install
fi
mkdir -p "$ROOT_DIR/logs"

echo "Setup complete."
