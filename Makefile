.PHONY: init clean start stop help

# Default target
help:
	@echo "Available targets:"
	@echo "  make init    - Initialize the project (install dependencies, setup .env)"
	@echo "  make clean   - Clean up generated files and caches"
	@echo "  make start   - Start the image search application"
	@echo "  make stop    - Stop all processes including Docker containers"

# Initialize the project
init:
	@echo "Initializing project..."
	@bash scripts/init.sh

# Clean up generated files
clean:
	@echo "Cleaning up..."
	@bash scripts/clean.sh

# Start the application
start:
	@echo "Starting image search application..."
	@uv run streamlit run --server.runOnSave false src/frontend/streamlit_app.py

# Stop all processes
stop:
	@bash scripts/stop.sh
