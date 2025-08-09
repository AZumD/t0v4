#!/bin/bash
set -e

LLAMA_CPP_PATH="/home/anthon/llama.cpp"
LLAMA_SERVER_PATH="/home/anthon/llama.cpp/build/bin/llama-server"
PHI_MODEL_PATH="/home/anthon/llama.cpp/models/Phi-3.5-mini-instruct-Q4_K_M.gguf"
LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

# Create logs directory
mkdir -p "$LOG_PATH"

# Check if Phi model exists
if [ ! -f "$PHI_MODEL_PATH" ]; then
    echo "❌ Phi model not found at: $PHI_MODEL_PATH"
    echo "   Please ensure the Phi model is downloaded to the correct location"
    exit 1
fi

echo "🔍 Starting Phi server on port 8001 with model: $PHI_MODEL_PATH"

cd "$LLAMA_CPP_PATH"

# Start llama.cpp server with CPU-optimized settings for Phi
"$LLAMA_SERVER_PATH" \
    --model "$PHI_MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8001 \
    --ctx-size 4096 \
    --n-gpu-layers 0 \
    --threads 12 \
    --batch-size 256 \
    --ubatch-size 256 \
    --no-mmap \
    2>&1 | tee "$LOG_PATH/phi.log" &

PHI_PID=$!
echo $PHI_PID > "$LOG_PATH/phi.pid"

echo "🔍 Phi server started with PID: $PHI_PID"
echo "📊 Logs: $LOG_PATH/phi.log"
echo "🌐 Endpoint: http://localhost:8001"

# Wait a moment for server to start
sleep 3

# Test if server is responding
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Phi server is responding"
else
    echo "❌ Phi server failed to start properly"
    exit 1
fi
