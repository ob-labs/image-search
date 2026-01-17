# coding: utf-8
"""
CLI helper to load images into OceanBase.
"""

import argparse
import os

from dotenv import load_dotenv

from common.db import build_client
from common.image_store import OBImageStore
from common.logger import get_logger

# Logger for CLI loader
logger = get_logger(__name__)

# Load environment variables for DB configuration
load_dotenv()
logger.info("Environment variables loaded for CLI.")

# Read connection and table configuration from env
table_name = os.getenv("IMG_TABLE_NAME", "image_search")

# Initialize the image store client
store = OBImageStore(
    client=build_client(),
    table_name=table_name,
)
logger.info("Image store initialized for CLI, table '%s'.", table_name)


if __name__ == "__main__":
    # Parse CLI arguments for input directory and batch size
    parser = argparse.ArgumentParser(description="Load images to OB")
    parser.add_argument(
        "--dir",
        type=str,
        required=True,
        help="Directory to load images from",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for loading images",
    )
    args = parser.parse_args()

    # Stream load progress until completion
    for _ in store.load_image_dir(args.dir, args.batch_size):
        pass
    logger.info("Images loaded successfully from %s.", args.dir)
