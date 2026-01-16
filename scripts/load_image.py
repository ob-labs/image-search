# coding: utf-8
"""
CLI helper to load images into OceanBase.
"""
import os
import dotenv

# Load environment variables for DB configuration
dotenv.load_dotenv()

from image_search.image_store import OBImageStore


# Read connection and table configuration from env
table_name = os.getenv("IMG_TABLE_NAME", "image_search")
connection_args = {
    "user": os.getenv("DB_USER", ""),
    "host": os.getenv("DB_HOST", ""),
    "port": int(os.getenv("DB_PORT", 2881)),
    "db_name": os.getenv("DB_NAME", ""),
    "password": os.getenv("DB_PASSWORD", ""),
}

# Initialize the image store client
store = OBImageStore(
    uri=f"{connection_args['host']}:{connection_args['port']}",
    **connection_args,
    table_name=table_name,
)


if __name__ == "__main__":

    # Parse CLI arguments for input directory and batch size
    import argparse

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
    print("Images loaded successfully!")
