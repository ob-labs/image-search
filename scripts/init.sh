#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting project initialization..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.9 or above."
    exit 1
fi

# Install dependencies
echo "Installing dependencies with uv..."
cd "$PROJECT_ROOT"
uv sync

# Check if .env file exists and export environment variables
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Error: .env file not found. Please create .env file first."
    exit 1
fi

echo "Loading environment variables from .env file..."
set -a
source "$PROJECT_ROOT/.env"
set +a
echo "Environment variables loaded successfully."

# Check if Docker is available and running
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo "Docker is available and running."
    else
        echo "Warning: Docker is installed but not running. You may need to start Docker service:"
        echo "  sudo systemctl start docker"
    fi
else
    echo "Warning: Docker is not installed. You may need Docker to run OceanBase database."
fi

echo "Initialization completed!"
