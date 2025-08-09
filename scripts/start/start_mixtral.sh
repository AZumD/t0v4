#!/bin/bash
set -e

LLAMA_CPP_PATH="/home/anthon/llama.cpp"
MODEL_PATH="/home/anthon/t0v4/tova_v4/data/models/dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf"
LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

# Create logs directory
mkdir -p "$LOG_PATH"

echo "🎭 Starting Mixtral server on port 8000..."

cd "$LLAMA_CPP_PATH"

# Start llama.cpp server with optimized settings for Mixtral
./llama-server \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8000 \
    --ctx-size 24576 \
    --n-gpu-layers 33 \
    --threads 8 \
    --batch-size 512 \
    --ubatch-size 512 \
    --flash-attn \
    --no-mmap \
    --numa isolate \
    --log-format text \
    --verbose \
    2>&1 | tee "$LOG_PATH/mixtral.log" &

MIXTRAL_PID=$!
echo $MIXTRAL_PID > "$LOG_PATH/mixtral.pid"

echo "🎭 Mixtral server started with PID: $MIXTRAL_PID"
echo "📊 Logs: $LOG_PATH/mixtral.log"
echo "🌐 Endpoint: http://localhost:8000"

# Wait a moment for server to start
sleep 3

# Test if server is responding
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Mixtral server is responding"
else
    echo "❌ Mixtral server failed to start properly"
    exit 1
fi
