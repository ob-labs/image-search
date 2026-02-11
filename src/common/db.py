# coding: utf-8
"""
Database helpers for OceanBase image search.
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from pydantic import BaseModel

import pyseekdb
from pyseekdb import Configuration, HNSWConfiguration

from .logger import get_logger

# Logger for database helpers
logger = get_logger(__name__)

# Load environment variables from a .env file if present
load_dotenv()
logger.info("Environment variables loaded for DB helpers.")

# Consolidate connection parameters for reuse across modules
connection_args = {
    "host": os.getenv("DB_HOST", ""),
    "port": os.getenv("DB_PORT", "2881"),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "db_name": os.getenv("DB_NAME", ""),
}

# Embedding dimension (must match the embedding API output)
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))

# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------


class ImageData(BaseModel):
    """
    Typed container for image file metadata and embeddings.
    """

    file_name: str = ""
    file_path: str = ""
    caption: str = ""
    embedding: list[float]


def _get_raw_connection(client):
    """Get the underlying pymysql connection from a pyseekdb client (or proxy)."""
    # _ClientProxy wraps the real client in _server
    real_client = getattr(client, "_server", client)
    return real_client.get_raw_connection()


def _execute_raw_sql(client, sql: str) -> list:
    """Execute raw SQL via the underlying pymysql connection."""
    conn = _get_raw_connection(client)
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def build_client():
    """Build a pyseekdb Client in remote server mode."""
    return pyseekdb.Client(
        host=connection_args["host"],
        port=int(connection_args["port"]),
        database=connection_args["db_name"],
        user=connection_args["user"],
        password=connection_args["password"],
    )


def get_or_create_collection(client, collection_name: str):
    """Get or create a collection with HNSW + fulltext config."""
    config = Configuration(
        hnsw=HNSWConfiguration(dimension=EMBEDDING_DIMENSION, distance="l2"),
    )
    return client.get_or_create_collection(
        name=collection_name,
        configuration=config,
        embedding_function=None,
    )


def create_table(table_name: str | None = None) -> None:
    """Create the image search collection (table) if it doesn't exist."""
    table_name = table_name or os.getenv("IMG_TABLE_NAME", "image_search")
    client = build_client()

    if client.has_collection(table_name):
        logger.info("Collection '%s' already exists. Skipping creation.", table_name)
        return

    logger.info("Creating collection '%s'...", table_name)
    get_or_create_collection(client, table_name)
    logger.info("Collection '%s' created successfully!", table_name)


def check_connection() -> None:
    client = build_client()
    _execute_raw_sql(client, "SELECT 1")
    logger.info("Database connection check executed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="OceanBase DB helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create-table", help="Create the image search collection"
    )
    create_parser.add_argument(
        "--table-name",
        type=str,
        default=None,
        help="Collection name to create (defaults to IMG_TABLE_NAME)",
    )

    subparsers.add_parser("check-connection", help="Check database connection")

    args = parser.parse_args()

    try:
        if args.command == "create-table":
            create_table(args.table_name)
        elif args.command == "check-connection":
            check_connection()
            logger.info("Database connection successful!")
        else:
            parser.error(f"Unknown command: {args.command}")
    except Exception as e:
        if args.command == "check-connection":
            logger.error("Database connection failed: %s", e)
        else:
            logger.error("Failed to create collection: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
