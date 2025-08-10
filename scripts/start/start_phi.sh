#!/bin/bash
set -e

LLAMA_SERVER_BIN="$HOME/llm/bin/llama-server"
PHI_MODEL_PATH="/home/anthon/llama.cpp/models/Phi-3.5-mini-instruct-Q4_K_M.gguf"
LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

# Create logs directory
mkdir -p "$LOG_PATH"

# Check binary
if [ ! -x "$LLAMA_SERVER_BIN" ]; then
    echo "❌ llama-server not found at: $LLAMA_SERVER_BIN"
    exit 1
fi

# Check if Phi model exists
if [ ! -f "$PHI_MODEL_PATH" ]; then
    echo "❌ Phi model not found at: $PHI_MODEL_PATH"
    echo "   Please ensure the Phi model is downloaded to the correct location"
    exit 1
fi

echo "🔍 Starting Phi server on port 8001 with model: $PHI_MODEL_PATH"

# Start llama.cpp server with CPU-only settings for Phi
"$LLAMA_SERVER_BIN" \
    --model "$PHI_MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8001 \
    -c 4096 \
    -t "$(nproc)" \
    --batch-size 256 \
    -ngl 0 \
    2>&1 | tee "$LOG_PATH/phi.log" &

PHI_PID=$!
echo $PHI_PID > "$LOG_PATH/phi.pid"

echo "🔍 Phi server started with PID: $PHI_PID"
echo "📊 Logs: $LOG_PATH/phi.log"
echo "🌐 Endpoint: http://localhost:8001"

# Wait a moment for server to start
sleep 3

# Test if server is responding using /completion
if curl -s "http://localhost:8001/completion" -H 'Content-Type: application/json' -d '{"prompt":"ping","n_predict":4}' > /dev/null; then
    echo "✅ Phi server is responding"
else
    echo "❌ Phi server failed to start properly"
    exit 1
fi
