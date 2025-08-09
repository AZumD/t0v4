#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

echo "🎪 Starting TOVA v4 Complete System..."

# Create logs directory
mkdir -p "$LOG_PATH"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down TOVA v4..."
    
    # Kill servers using PID files
    if [ -f "$LOG_PATH/mixtral.pid" ]; then
        kill $(cat "$LOG_PATH/mixtral.pid") 2>/dev/null || true
        rm -f "$LOG_PATH/mixtral.pid"
    fi
    
    if [ -f "$LOG_PATH/phi.pid" ]; then
        kill $(cat "$LOG_PATH/phi.pid") 2>/dev/null || true
        rm -f "$LOG_PATH/phi.pid"
    fi
    
    if [ -f "$LOG_PATH/tova.pid" ]; then
        kill $(cat "$LOG_PATH/tova.pid") 2>/dev/null || true
        rm -f "$LOG_PATH/tova.pid"
    fi
    
    echo "✅ TOVA v4 shutdown complete"
}

# Setup cleanup on script exit
trap cleanup EXIT INT TERM

# Start Mixtral (Primary Brain)
echo "1/3 Starting Mixtral..."
"$SCRIPT_DIR/start_mixtral.sh"

# Start Phi (Background Brain)
echo "2/3 Starting Phi..."
"$SCRIPT_DIR/start_phi.sh"

# Start TOVA Core
echo "3/3 Starting TOVA Core..."
"$SCRIPT_DIR/start_tova.sh"

echo ""
echo "🎉 TOVA v4 System Online!"
echo "🎭 Mixtral (Primary): http://localhost:8000"
echo "🔍 Phi (Background): http://localhost:8001"
echo "🎪 TOVA Core: http://localhost:8002"
echo ""
echo "Press Ctrl+C to shutdown all services..."

# Keep script running and wait for shutdown signal
wait
