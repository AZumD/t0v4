#!/bin/bash
set -e

LLAMA_CPP_PATH="/home/anthon/llama.cpp"
LLAMA_SERVER_PATH="/home/anthon/llama.cpp/build/bin/llama-server"
LOCAL_MODEL_PATH="/home/anthon/t0v4/tova_v4/data/models/dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf"
FALLBACK_MODEL_PATH="/home/anthon/llama.cpp/models/Phi-3.5-mini-instruct-Q4_K_M.gguf"
LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

# Create logs directory
mkdir -p "$LOG_PATH"

echo "🎭 Starting Mixtral server with HF repo integration..."

cd "$LLAMA_CPP_PATH"

# Try HF repo approach first (most reliable for compatibility)
echo "🎭 Attempting to use HF repo for Mixtral model..."

# Start HF repo server in background
"$LLAMA_SERVER_PATH" \
    --hf-repo TheBloke/dolphin-2.7-mixtral-8x7b-GGUF:dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf \
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

echo "🎭 Mixtral server started with PID: $MIXTRAL_PID (HF repo)"
echo "📊 Logs: $LOG_PATH/mixtral.log"
echo "🌐 Endpoint: http://localhost:8000"

# Wait for server to start
sleep 10

# Test if server is responding
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Mixtral server is responding (HF repo)"
    exit 0
else
    echo "⚠️  HF repo approach failed, trying local model..."
    kill $MIXTRAL_PID 2>/dev/null || true
    
    # Fallback to local model
    echo "🎭 Starting Mixtral server with local model: $LOCAL_MODEL_PATH"
    
    # Check if local model exists, otherwise use fallback
    if [ ! -f "$LOCAL_MODEL_PATH" ]; then
        if [ -f "$FALLBACK_MODEL_PATH" ]; then
            echo "⚠️  Primary Mixtral model not found, using fallback Phi model..."
            LOCAL_MODEL_PATH="$FALLBACK_MODEL_PATH"
        else
            echo "❌ No suitable model found. Please download a model to: $LOCAL_MODEL_PATH"
            echo "   Or place a compatible model at: $FALLBACK_MODEL_PATH"
            exit 1
        fi
    fi
    
    # Start llama.cpp server with local model
    "$LLAMA_SERVER_PATH" \
        --model "$LOCAL_MODEL_PATH" \
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
    
    echo "🎭 Mixtral server started with PID: $MIXTRAL_PID (local model)"
    echo "📊 Logs: $LOG_PATH/mixtral.log"
    echo "🌐 Endpoint: http://localhost:8000"
    
    # Wait a moment for server to start
    sleep 3
    
    # Test if server is responding
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Mixtral server is responding (local model)"
    else
        echo "❌ Mixtral server failed to start properly"
        exit 1
    fi
fi
