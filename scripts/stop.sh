#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Stopping all processes..."

# Stop Streamlit processes
echo "Stopping Streamlit processes..."
pkill -f "streamlit run" || true

# Stop FastAPI/uvicorn backend processes
echo "Stopping backend FastAPI server..."
pkill -f "uvicorn.*src.backend.app" || true
pkill -f "uvicorn src.backend.app" || true

# Check if .env file exists to read REUSE_CURRENT_DB
if [ -f "$PROJECT_ROOT/.env" ]; then
    # Load environment variables from .env file
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
    
    # Only stop docker if REUSE_CURRENT_DB is false
    if [ "${REUSE_CURRENT_DB}" != "true" ]; then
        echo "REUSE_CURRENT_DB is false, stopping Docker containers..."
        
        # Determine docker_name based on DB_STORE
        if [ "${DB_STORE}" = "seekdb" ]; then
            docker_name="seekdb"
        elif [ "${DB_STORE}" = "oceanbase" ]; then
            docker_name="oceanbase-ce"
        else
            echo "Warning: Unknown DB_STORE value: ${DB_STORE}. Skipping docker stop."
            echo "All processes stopped."
            exit 0
        fi
        
        # Stop the specific docker container
        if sudo docker ps --format "{{.Names}}" | grep -q "^${docker_name}$"; then
            echo "Stopping Docker container: ${docker_name}"
            sudo docker stop "${docker_name}" || true
        else
            echo "Docker container '${docker_name}' is not running."
        fi
    else
        echo "REUSE_CURRENT_DB is true, skipping Docker container stop."
    fi
else
    echo "Warning: .env file not found. Stopping all Docker containers..."
    # Fallback: stop all docker containers if .env is not found
    sudo docker ps -q | xargs -r sudo docker stop || true
    sudo docker ps -aq | xargs -r sudo docker rm || true
fi

echo "All processes stopped."
