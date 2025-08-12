#!/bin/bash
set -e

LLAMA_CPP_PATH="/home/anthon/llama.cpp"
LLAMA_SERVER_PATH="/home/anthon/llama.cpp/build/bin/server"
# Prefer external model locations; allow override via MIXTRAL_MODEL_PATH
LOCAL_MODEL_PATH=""
DEFAULT_MODEL_NAME="dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf"
EXTERNAL_DEFAULT="/home/anthon/llm/models/mixtral/${DEFAULT_MODEL_NAME}"
CACHE_GLOB="/home/anthon/.cache/llama.cpp/*${DEFAULT_MODEL_NAME}"
LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

mkdir -p "$LOG_PATH"
cd "$LLAMA_CPP_PATH"

# Resolve model path
if [ -n "${MIXTRAL_MODEL_PATH:-}" ] && [ -f "$MIXTRAL_MODEL_PATH" ]; then
  LOCAL_MODEL_PATH="$MIXTRAL_MODEL_PATH"
elif [ -f "$EXTERNAL_DEFAULT" ]; then
  LOCAL_MODEL_PATH="$EXTERNAL_DEFAULT"
else
  # Try cache fallback
  FALLBACK_PATH=$(ls -1 $CACHE_GLOB 2>/dev/null | head -n1 || true)
  if [ -n "$FALLBACK_PATH" ] && [ -f "$FALLBACK_PATH" ]; then
    LOCAL_MODEL_PATH="$FALLBACK_PATH"
  fi
fi

if [ -z "$LOCAL_MODEL_PATH" ] || [ ! -f "$LOCAL_MODEL_PATH" ]; then
  echo "❌ Mixtral model not found. Set MIXTRAL_MODEL_PATH or place model at:"
  echo "   $EXTERNAL_DEFAULT"
  echo "   or ensure cache contains: $CACHE_GLOB"
  exit 1
fi

echo "🎭 Using Mixtral model: $LOCAL_MODEL_PATH"

THREADS="${MIXTRAL_THREADS:-$(nproc)}"
BATCH="${MIXTRAL_BATCH:-64}"
NGL="${MIXTRAL_NGL:-24}"   # 3080 12GB baseline

echo "Starting Mixtral on CUDA | THREADS=$THREADS BATCH=$BATCH NGL=$NGL"

start_server() {
  "$LLAMA_SERVER_PATH" \
    --model "$LOCAL_MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8000 \
    --ctx-size 4096 \
    --threads "$THREADS" \
    --batch-size "$BATCH" \
    --n-gpu-layers "$1" \
    2>&1 | tee "$LOG_PATH/mixtral.log" &
  echo $! > "$LOG_PATH/mixtral.pid"
}

ATTEMPT_NGL="$NGL"
ATTEMPTS=0
MAX_ATTEMPTS=6  # 24 -> 22 -> ... -> 14

while true; do
  echo "→ Attempting start with --n-gpu-layers $ATTEMPT_NGL"
  start_server "$ATTEMPT_NGL"
  sleep 5
  if curl -s http://127.0.0.1:8000/v1/models > /dev/null; then
    echo "✅ Mixtral server is responding with NGL=$ATTEMPT_NGL"
    break
  fi
  echo "❌ Mixtral failed with NGL=$ATTEMPT_NGL, retrying lower..."
  if [ -f "$LOG_PATH/mixtral.pid" ]; then kill $(cat "$LOG_PATH/mixtral.pid") 2>/dev/null || true; fi
  ATTEMPTS=$((ATTEMPTS+1))
  if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
    echo "❌ Exhausted attempts. Bailing."
    exit 1
  fi
  ATTEMPT_NGL=$((ATTEMPT_NGL-2))
  if [ $ATTEMPT_NGL -lt 14 ]; then
    echo "❌ Reached guard NGL < 14. Bailing."
    exit 1
  fi
done

echo "Logs: $LOG_PATH/mixtral.log | Endpoint: http://localhost:8000"
