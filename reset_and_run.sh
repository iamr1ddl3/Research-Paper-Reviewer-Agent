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
AUTO_APPROVE=1 .venv/bin/python -m app.main --goal "Review papers on long-running AI agents" --count 2
