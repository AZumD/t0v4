#!/usr/bin/env bash
set -euo pipefail
# Create venv and install dependencies
python3 -m venv mistralvenv
./mistralvenv/bin/python -m pip install --upgrade pip
./mistralvenv/bin/python -m pip install -r requirements.txt 