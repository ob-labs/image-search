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

# Check Python version
echo "Checking Python version..."
REQUIRED_PYTHON_MAJOR=3
REQUIRED_PYTHON_MINOR=10

# Get current Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    echo "Current Python version: $PYTHON_VERSION"
else
    PYTHON_MAJOR=0
    PYTHON_MINOR=0
    echo "Python 3 is not installed."
fi

# Check if Python version is less than 3.10
if [ "$PYTHON_MAJOR" -lt "$REQUIRED_PYTHON_MAJOR" ] || \
   { [ "$PYTHON_MAJOR" -eq "$REQUIRED_PYTHON_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$REQUIRED_PYTHON_MINOR" ]; }; then
    echo "Python version is below 3.10. Installing Python 3.12 using uv..."
    
    # Install Python 3.12 using uv
    uv python install 3.12
    
    # Create virtual environment with Python 3.12
    echo "Creating virtual environment with Python 3.12..."
    cd "$PROJECT_ROOT"
    uv venv --python 3.12
    
    # Activate the virtual environment
    if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
        echo "Virtual environment activated with Python 3.12"
    else
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
    
    # Verify Python version in venv
    VENV_PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "Virtual environment Python version: $VENV_PYTHON_VERSION"
else
    echo "Python version check passed: $PYTHON_VERSION"
fi

# Check system memory (at least 4GB)
echo "Checking system memory..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    TOTAL_MEM_BYTES=$(sysctl -n hw.memsize)
    TOTAL_MEM_GB=$((TOTAL_MEM_BYTES / 1024 / 1024 / 1024))
else
    # Linux
    TOTAL_MEM_GB=$(free -g | awk '/^Mem:/{print $2}')
fi
if [ -z "$TOTAL_MEM_GB" ] || [ "$TOTAL_MEM_GB" -lt 4 ]; then
    echo "Error: System memory is insufficient. Required: at least 4GB, Current: ${TOTAL_MEM_GB}GB"
    exit 1
fi
echo "System memory check passed: ${TOTAL_MEM_GB}GB"

# Check disk space (at least 10GB available)
echo "Checking disk space..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: df -g returns space in 1GB blocks
    AVAILABLE_SPACE_GB=$(df -g "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
else
    # Linux: df -BG returns space in GB
    AVAILABLE_SPACE_GB=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
fi
if [ -z "$AVAILABLE_SPACE_GB" ] || [ "$AVAILABLE_SPACE_GB" -lt 10 ]; then
    echo "Error: Disk space is insufficient. Required: at least 10GB, Current: ${AVAILABLE_SPACE_GB}GB"
    exit 1
fi
echo "Disk space check passed: ${AVAILABLE_SPACE_GB}GB available"

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


if [ "${REUSE_CURRENT_DB}" != "true" ]; then
    bash "$SCRIPT_DIR/init_docker.sh"
fi

# Create table
echo "Creating database table..."
if ! uv run python -m src.common.db create-table 2>&1; then
    echo "Failed to create table!"
    exit 1
fi

echo "Initialization completed!"
