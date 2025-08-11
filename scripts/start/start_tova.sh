#!/bin/bash
set -e

PROJECT_ROOT="/home/anthon/t0v4"
LOG_PATH="$PROJECT_ROOT/data/logs"

mkdir -p "$LOG_PATH"

echo "🎪 Starting TOVA Core on port 8002..."

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists (~/.venvs/mistralvenv)
if [ -f "$HOME/.venvs/mistralvenv/bin/activate" ]; then
    source "$HOME/.venvs/mistralvenv/bin/activate"
fi

# Resolve Mixtral & Phi base URLs (prefer Tailscale IPv4)
TSIP=$(tailscale ip -4 2>/dev/null | head -n1 || true)
if [ -n "$TSIP" ]; then
  export MIXTRAL_BASE_URL="http://$TSIP:8000"
  export PHI_BASE_URL="http://$TSIP:8001"
else
  export MIXTRAL_BASE_URL="http://127.0.0.1:8000"
  export PHI_BASE_URL="http://127.0.0.1:8001"
fi

echo "Using MIXTRAL_BASE_URL=$MIXTRAL_BASE_URL"
echo "Using PHI_BASE_URL=$PHI_BASE_URL"

# Start TOVA Core FastAPI application
uvicorn tova.main:app \
    --host 0.0.0.0 \
    --port 8002 \
    --reload \
    --log-level info \
    2>&1 | tee "$LOG_PATH/tova.log" &

TOVA_PID=$!
echo $TOVA_PID > "$LOG_PATH/tova.pid"

echo "🎪 TOVA Core started with PID: $TOVA_PID"
echo "📊 Logs: $LOG_PATH/tova.log"
echo "🌐 Endpoint: http://localhost:8002"

# Wait a moment for server to start
sleep 3

# Test if server is responding
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✅ TOVA Core is responding"
else
    echo "❌ TOVA Core failed to start properly"
    exit 1
fi
