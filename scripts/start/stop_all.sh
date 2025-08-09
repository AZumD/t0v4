#!/bin/bash

LOG_PATH="/home/anthon/t0v4/tova_v4/data/logs"

echo "🛑 Stopping TOVA v4 services..."

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file="$LOG_PATH/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            sleep 2
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "Force killing $service_name..."
                kill -9 "$pid"
            fi
        fi
        rm -f "$pid_file"
        echo "✅ $service_name stopped"
    else
        echo "⚠️  No PID file found for $service_name"
    fi
}

stop_service "tova"
stop_service "phi" 
stop_service "mixtral"

echo "🎪 TOVA v4 shutdown complete"
