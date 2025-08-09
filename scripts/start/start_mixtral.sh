#!/bin/bash
set -e

LLAMA_CPP_PATH="/home/anthon/llama.cpp"
LLAMA_SERVER_PATH="/home/anthon/llama.cpp/build/bin/server"
LOCAL_MODEL_PATH="/home/anthon/t0v4/tova_v4/data/models/dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf"
LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

# Create logs directory
mkdir -p "$LOG_PATH"

echo "🎭 Starting Mixtral server with local model..."

cd "$LLAMA_CPP_PATH"

# Check if local model exists
if [ ! -f "$LOCAL_MODEL_PATH" ]; then
    echo "❌ Mixtral model not found at: $LOCAL_MODEL_PATH"
    exit 1
fi

# Start llama.cpp server (older version - no --hf-repo support)
"$LLAMA_SERVER_PATH" \
    --model "$LOCAL_MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8000 \
    --ctx-size 4096 \
    --threads 8 \
    --batch-size 256 \
    --no-mmap \
    2>&1 | tee "$LOG_PATH/mixtral.log" &

MIXTRAL_PID=$!
echo $MIXTRAL_PID > "$LOG_PATH/mixtral.pid"

echo "🎭 Mixtral server started with PID: $MIXTRAL_PID"
echo "📊 Logs: $LOG_PATH/mixtral.log"
echo "🌐 Endpoint: http://localhost:8000"

# Wait for server to start
sleep 5

# Test if server is responding (use /v1/models instead of /health)
if curl -s http://localhost:8000/v1/models > /dev/null; then
    echo "✅ Mixtral server is responding"
else
    echo "❌ Mixtral server failed to start properly"
    exit 1
fi
