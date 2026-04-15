#!/usr/bin/env bash
set -euo pipefail

# Ensure Node version via nvm (>= 18.19.0)
REQUIRED="18.19.0"

if command -v nvm >/dev/null 2>&1; then
  echo "Using nvm to select Node ${REQUIRED}..."
  # shellcheck disable=SC1090
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" || true
  nvm use || nvm install
else
  echo "nvm not found. Please install nvm and run:"
  echo "  nvm install ${REQUIRED} && nvm use"
fi

echo "Node version: $(node -v)"
