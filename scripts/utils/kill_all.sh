#!/bin/bash
set -e

LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"
SCRIPT_DIR="/home/anthon/t0v4/scripts/start"

echo "🛑 Killing all TOVA-related services (mixtral, phi, core)..."

# 1) Use existing stop script for PID-based shutdowns
if [ -x "$SCRIPT_DIR/stop_all.sh" ]; then
  "$SCRIPT_DIR/stop_all.sh" || true
fi

# 2) Extra safety: kill by process signature (non-fatal if not found)
# Mixtral (llama.cpp server on 8000)
pkill -f "/home/anthon/llama.cpp/build/bin/server.*--port 8000" 2>/dev/null || true

# Phi (llama-server on 8001)
pkill -f "llama-server.*--port 8001" 2>/dev/null || true

# TOVA core (uvicorn fastapi)
pkill -f "uvicorn.*tova.main:app" 2>/dev/null || true
pkill -f "python.*tova/main.py" 2>/dev/null || true
pkill -f "python.*tova.main" 2>/dev/null || true

# 3) Remove stale PID files
rm -f "$LOG_PATH/mixtral.pid" "$LOG_PATH/phi.pid" "$LOG_PATH/tova.pid" 2>/dev/null || true

echo "✅ All TOVA services terminated (or were not running)." 