#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "=== Installing openai SDK (switched from anthropic) ==="
.venv/bin/pip install -q -r requirements.txt
echo "=== Compile check ==="
.venv/bin/python -m compileall -q app
echo "=== Running agent (AUTO_APPROVE=1 for T6/T7) ==="
AUTO_APPROVE=1 .venv/bin/python -m app.main --goal "Review papers on long-running AI agents" --count 2
