# coding: utf-8
"""
Database helpers for OceanBase image search.
"""

import argparse
import os
import sys
from warnings import warn

from dotenv import load_dotenv
from pydantic import BaseModel
from pyobvector import ObVecClient, VECTOR
from sqlalchemy import Column, String

from .logger import get_logger
# Logger for database helpers
logger = get_logger(__name__)

# Load environment variables from a .env file if present
load_dotenv()
logger.info("Environment variables loaded for DB helpers.")

# Consolidate connection parameters for reuse across modules
connection_args = {
    "host": os.getenv("DB_HOST", ""),
    "port": os.getenv("DB_PORT", ""),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "db_name": os.getenv("DB_NAME", ""),
}

# Table schema used for image storage
# file_name + file_path as composite primary key
cols = [
    Column("file_name", String(512), primary_key=True),
    Column("file_path", String(512), primary_key=True),
    Column("caption", String(2048)),
    Column("embedding", VECTOR(512)),
]

# Columns to return in ANN search results
output_fields = [
    "file_name",
    "file_path",
    "caption",
    # "embedding",
]
# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------


class ImageData(BaseModel):
    """
    Typed container for image file metadata and embeddings.

    NOTE: This model's fields strictly match the database table schema defined
    in `cols`. Any changes to this model must be synchronized with the
    table schema to ensure proper data insertion and retrieval.
    """

    file_name: str = ""
    file_path: str = ""
    caption: str = ""
    embedding: list[float]


_VECTOR_MEMORY_PARAM = "ob_vector_memory_limit_percentage"


def ensure_vector_memory_limit(client: ObVecClient) -> None:
    values = fetch_vector_memory_percentages(client)
    if not values:
        logger.error("%s not found.", _VECTOR_MEMORY_PARAM)
        raise RuntimeError(f"{_VECTOR_MEMORY_PARAM} not found.")
    if any(value == 0 for value in values):
        logger.warning(
            "%s is 0; manual update may be required.",
            _VECTOR_MEMORY_PARAM,
        )


def fetch_vector_memory_percentages(client: ObVecClient) -> list[int]:
    params = client.perform_raw_text_sql(
        f"SHOW PARAMETERS LIKE '%{_VECTOR_MEMORY_PARAM}%'"
    )
    return [int(row[6]) for row in params]


def set_vector_memory_limit(client: ObVecClient, percent: int) -> None:
    try:
        client.perform_raw_text_sql(
            f"ALTER SYSTEM SET {_VECTOR_MEMORY_PARAM} = {percent}"
        )
        logger.info(
            "Updated %s to %s.",
            _VECTOR_MEMORY_PARAM,
            percent,
        )
    except Exception as exc:
        logger.error(
            "Failed to set %s: %s",
            _VECTOR_MEMORY_PARAM,
            exc,
        )
        raise RuntimeError(
            f"Failed to set {_VECTOR_MEMORY_PARAM} to {percent}.",
        ) from exc


def build_client() -> ObVecClient:
    return ObVecClient(
        user=connection_args["user"],
        uri=f"{connection_args['host']}:{connection_args['port']}",
        db_name=connection_args["db_name"],
        password=connection_args["password"],
    )


def create_table(table_name: str | None = None) -> None:
    table_name = table_name or os.getenv("IMG_TABLE_NAME", "image_search")
    client = build_client()

    if client.check_table_exists(table_name):
        logger.info("Table '%s' already exists. Skipping creation.", table_name)
        return

    logger.info("Creating table '%s'...", table_name)
    client.create_table(table_name, columns=cols)

    logger.info(
        "Creating vector index 'img_embedding_idx' on table '%s'...",
        table_name,
    )
    client.create_index(
        table_name,
        is_vec_index=True,
        index_name="img_embedding_idx",
        column_names=["embedding"],
        vidx_params="distance=l2, type=hnsw, lib=vsag",
    )

    logger.info("Table '%s' created successfully!", table_name)


def check_connection() -> None:
    client = build_client()
    client.perform_raw_text_sql("SELECT 1")
    logger.info("Database connection check executed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="OceanBase DB helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create-table", help="Create the image search table"
    )
    create_parser.add_argument(
        "--table-name",
        type=str,
        default=None,
        help="Table name to create (defaults to IMG_TABLE_NAME)",
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
            logger.error("Failed to create table: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
