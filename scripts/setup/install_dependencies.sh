#!/usr/bin/env bash
set -euo pipefail
python3 -m venv "$HOME/.venvs/mistralvenv" || true
source "$HOME/.venvs/mistralvenv/bin/activate"
pip install -U pip wheel
pip install -r requirements.txt || true
echo "Dependencies installed into $HOME/.venvs/mistralvenv" 