#!/bin/bash
set -e

LLAMA_CPP_PATH="/home/anthon/llama.cpp"
LLAMA_SERVER_PATH="/home/anthon/llama.cpp/build/bin/llama-server"
MODEL_PATH="/home/anthon/t0v4/tova_v4/data/models/dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf"
FALLBACK_MODEL_PATH="/home/anthon/llama.cpp/models/Phi-3.5-mini-instruct-Q4_K_M.gguf"
LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

# Create logs directory
mkdir -p "$LOG_PATH"

# Check if primary model exists, otherwise use fallback
if [ ! -f "$MODEL_PATH" ]; then
    if [ -f "$FALLBACK_MODEL_PATH" ]; then
        echo "⚠️  Primary Mixtral model not found, using fallback Phi model..."
        MODEL_PATH="$FALLBACK_MODEL_PATH"
    else
        echo "❌ No suitable model found. Please download a model to: $MODEL_PATH"
        echo "   Or place a compatible model at: $FALLBACK_MODEL_PATH"
        exit 1
    fi
fi

echo "🎭 Starting Mixtral server on port 8000 with model: $MODEL_PATH"

cd "$LLAMA_CPP_PATH"

# Start llama.cpp server with optimized settings for Mixtral
"$LLAMA_SERVER_PATH" \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8000 \
    --ctx-size 4096 \
    --n-gpu-layers 0 \
    --threads 8 \
    --batch-size 256 \
    --ubatch-size 256 \
    --no-mmap \
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
