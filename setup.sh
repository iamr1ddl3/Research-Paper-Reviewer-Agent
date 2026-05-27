#!/bin/bash
set -e
echo "=== Creating venv ==="
python3 -m venv .venv
echo "=== Upgrading pip ==="
.venv/bin/pip install --upgrade pip
echo "=== Installing requirements ==="
.venv/bin/pip install -r requirements.txt
echo "=== Compile check ==="
.venv/bin/python -m compileall -q app
echo "=== DONE ==="
