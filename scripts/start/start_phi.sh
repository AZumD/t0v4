#!/bin/bash
set -e

LLAMA_CPP_PATH="/home/anthon/llama.cpp"
PHI_MODEL_PATH="/home/anthon/Phi-3.5-mini-instruct-Q4_K_M.gguf"
LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

# Create logs directory
mkdir -p "$LOG_PATH"

echo "🔍 Starting Phi server on port 8001..."

cd "$LLAMA_CPP_PATH"

# Start llama.cpp server with CPU-optimized settings for Phi
./llama-server \
    --model "$PHI_MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8001 \
    --ctx-size 4096 \
    --n-gpu-layers 0 \
    --threads 12 \
    --batch-size 256 \
    --ubatch-size 256 \
    --no-mmap \
    --numa isolate \
    --log-format text \
    --verbose \
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
