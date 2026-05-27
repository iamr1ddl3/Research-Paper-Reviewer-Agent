#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "=== Resetting agent state ==="
rm -f workspace/agent_state.db
rm -rf workspace/project/*
rm -f workspace/artifacts/*.md
echo "=== Reinstalling deps (idempotent) ==="
.venv/bin/pip install -q -r requirements.txt
echo "=== Compile check ==="
.venv/bin/python -m compileall -q app
echo "=== Running agent (AUTO_APPROVE=1) ==="
# WeasyPrint (T7) needs pango/cairo dylibs from Homebrew at runtime.
# DYLD_FALLBACK_LIBRARY_PATH hint avoids "could not import some external
# libraries" failure on macOS Apple Silicon. Harmless on Linux.
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}
AUTO_APPROVE=1 .venv/bin/python -m app.main --goal "Review papers on long-running AI agents" --count 2
