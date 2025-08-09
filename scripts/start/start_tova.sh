#!/bin/bash
set -e

PROJECT_ROOT="/home/anthon/t0v4/tova_v4"
LOG_PATH="$PROJECT_ROOT/data/logs"

echo "🎪 Starting TOVA Core on port 8002..."

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "mistralvenv" ]; then
    source mistralvenv/bin/activate
fi

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
