#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting image search application..."

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Error: .env file not found. Please create .env file first."
    exit 1
fi

# Load environment variables from .env file
echo "Loading environment variables from .env file..."
set -a
source "$PROJECT_ROOT/.env"
set +a

# Start the backend FastAPI server
echo "Starting backend FastAPI server..."
BACKEND_PORT=${BACKEND_PORT:-8000}
uv run uvicorn src.backend.app:app --host 0.0.0.0 --port "$BACKEND_PORT" > /tmp/image-search-backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend server started with PID: $BACKEND_PID (port: $BACKEND_PORT)"
echo "Backend logs: /tmp/image-search-backend.log"

# Wait a moment for backend to start
sleep 2

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Error: Backend server failed to start. Check logs: /tmp/image-search-backend.log"
    cat /tmp/image-search-backend.log
    exit 1
fi

# Start the frontend Streamlit application
echo "Starting frontend Streamlit application..."
echo "Press Ctrl+C to stop both services"
trap "kill $BACKEND_PID 2>/dev/null; exit" INT TERM
uv run streamlit run --server.runOnSave false src/frontend/streamlit_app.py
