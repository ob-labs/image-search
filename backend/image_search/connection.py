"""
Database connection configuration loaded from environment variables.
"""

import os
import dotenv

# Load environment variables from a .env file if present
dotenv.load_dotenv()

# Consolidate connection parameters for reuse across modules
connection_args = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db_name": os.getenv("DB_NAME"),
}
