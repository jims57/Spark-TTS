#!/bin/bash

echo "=== Spark TTS Service Restart Script ==="
echo "Starting service cleanup..."

# Function to kill process on a specific port
kill_process_on_port() {
    local port=$1
    echo "Checking for process on port $port..."
    
    pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "Found process (PID: $pid) running on port $port. Terminating..."
        kill -9 $pid
        echo "Process on port $port has been terminated."
    else
        echo "No process found running on port $port."
    fi
}

# Kill processes on ports 9002 and 9003
kill_process_on_port 9002
kill_process_on_port 9003

# Wait a moment to ensure ports are released
echo "Waiting for ports to be fully released..."
sleep 2

# Verify ports are free
verify_port() {
    local port=$1
    if lsof -i:$port >/dev/null 2>&1; then
        echo "ERROR: Port $port is still in use. Please check manually."
        exit 1
    fi
}

echo "Verifying ports are free..."
verify_port 9002
verify_port 9003

echo "Ports 9002 and 9003 are clear. Starting Spark TTS service..."

# Start the service
if [ -f /root/.jupyter_startup.sh ]; then
    bash /root/.jupyter_startup.sh
    echo "Spark TTS service startup initiated."
else
    echo "ERROR: Startup script not found at /root/.jupyter_startup.sh"
    exit 1
fi

echo "=== Service restart process completed ===" 