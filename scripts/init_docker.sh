#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Error: .env file not found. Please create .env file first."
    exit 1
fi

echo "Loading environment variables from .env file..."
set -a
source "$PROJECT_ROOT/.env"
set +a
echo "Environment variables loaded successfully."

# Check if Docker is available and running (only needed if not reusing current DB)

if command -v docker &> /dev/null; then
    if sudo docker info &> /dev/null; then
        echo "Docker is available and running."
    else
        echo "Warning: Docker is installed but not running. You may need to start Docker service:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "  Open Docker Desktop application"
        else
            echo "  sudo systemctl start docker"
            exit 1
        fi
    fi
else
    echo "Warning: Docker is not installed. You may need Docker to run OceanBase database."
fi

# Download Docker images based on DB_STORE
if [ "${DB_STORE}" = "seekdb" ]; then
    echo "Downloading latest seekdb docker image..."
    export ROOT_PASSWORD=${DB_PASSWORD}
    sudo docker run --name seekdb -d -p 2881:2881 -p 2886:2886 oceanbase/seekdb
elif [ "${DB_STORE}" = "oceanbase" ]; then
    echo "Downloading latest oceanbase-ce docker image..."
    export OB_TENANT_PASSWORD=${DB_PASSWORD}
    sudo docker run -p 2881:2881 --name oceanbase-ce -e MODE=normal -d oceanbase/oceanbase-ce
else
    echo "Warning: Unknown DB_STORE value: ${DB_STORE}. Skipping docker image download."
fi

# Wait for download to complete
echo "Waiting for docker image download to complete..."
sleep 60s

# Check database connection
echo "Checking database connection..."
cd "$PROJECT_ROOT"

# Run the database connection check
if ! uv run python src/common/db.py check-connection 2>&1; then
    echo "Database connection check failed!"
    echo "Please ensure that Docker is running properly."
    echo "Please wait for 60 seconds and rerun this script with sudo bash scripts/init_docker.sh."
    
    # Determine docker_name based on DB_STORE
    if [ "${DB_STORE}" = "seekdb" ]; then
        docker_name="seekdb"
    elif [ "${DB_STORE}" = "oceanbase" ]; then
        docker_name="oceanbase-ce"
    else
        echo "Warning: Unknown DB_STORE value: ${DB_STORE}. Cannot determine docker name."
        exit 1
    fi
    
    # Check if docker container exists and is running
    if ! sudo docker ps --format "{{.Names}}" | grep -q "^${docker_name}$"; then
        echo "Docker container '${docker_name}' is not running."
        echo "Checking if container exists..."
        if sudo docker ps -a --format "{{.Names}}" | grep -q "^${docker_name}$"; then
            echo "Container exists but is not running. Attempting to start it..."
            sudo docker start "${docker_name}" || true
            echo "Waiting for container to be ready..."
            sleep 5
        else
            echo "Container '${docker_name}' does not exist."
            echo "Please run 'make init' first to create the container."
            exit 1
        fi
    fi
    
    echo "Checking Docker logs for errors..."
    echo "=========================================="
    sudo docker logs --tail 50 "${docker_name}" 2>&1 || true
    echo "=========================================="
    echo ""
    echo "If you see errors above, please fix them before continuing."
    echo "You can monitor the logs with: sudo docker logs -f ${docker_name}"
    echo ""
    echo "After fixing the issues, please run this script again."
    exit 1
    
fi
