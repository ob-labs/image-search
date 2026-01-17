# coding: utf-8
"""
FastAPI entrypoint that serves static assets and image search APIs.
"""

import os
import tempfile
from pathlib import Path

import fastapi_cdn_host
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from starlette import staticfiles

from common.db import build_client
from common.image_store import OBImageStore
from common.logger import get_logger

# Logger for backend app
logger = get_logger(__name__)

# Load environment variables for DB and app initialization
load_dotenv()
logger.info("Environment variables loaded for backend.")

# Create the FastAPI app and patch docs to use CDN assets
app = FastAPI(title="Image Search App", version="0.1.0")
fastapi_cdn_host.patch_docs(app)
logger.info("FastAPI app initialized.")

# Resolve and mount the frontend build output as static assets
base_dir = Path(__file__).resolve().parents[2]
dist_dir = base_dir / "dist"
app.mount("/static", staticfiles.StaticFiles(directory=str(dist_dir)), name="static")
logger.info("Mounted static assets from %s.", dist_dir)

# Create an API router and mount it under /api
router = APIRouter()

# Read image table name (default: image_search)
table_name = os.getenv("IMG_TABLE_NAME", "image_search")

# Track mounted image directories to avoid duplicate mounts
image_dirs: dict[str, int] = {}

# Initialize the image vector store client
store = OBImageStore(
    client=build_client(),
    table_name=table_name,
)
logger.info("Image store initialized for table '%s'.", table_name)


def replace_path(path: str) -> str:
    """
    Map a local directory to a static URL prefix and return it.
    """

    # Mount the directory the first time it appears
    if path not in image_dirs:
        image_dirs[path] = len(image_dirs) + 1
        logger.info("Mounting image directory %s.", path)
        app.mount(
            f"/images/{image_dirs[path]}",
            staticfiles.StaticFiles(directory=path),
            name=f"static_{image_dirs[path]}",
        )

    # Return the static URL prefix for this directory
    return f"/images/{image_dirs[path]}/"


@app.get("/")
async def read_index() -> FileResponse:
    """
    Return the frontend index page.
    """
    return FileResponse(str(dist_dir / "index.html"))


@router.post("/search")
async def search_image(
    file: UploadFile = File(...),
    top_k: int = 10,
) -> list[dict[str, object]]:
    """
    Accept an uploaded image and return top-k similar results.
    """

    # Save the uploaded image to a temp file for embedding
    content = await file.read()
    file_type = os.path.splitext(file.filename)[1]
    tf = tempfile.NamedTemporaryFile(suffix=file_type)
    tf.write(content)
    tf.flush()
    logger.info("Received image %s for search (top_k=%s).", file.filename, top_k)

    # Search similar images in the vector store
    res = store.search(tf.name, limit=top_k)

    # Replace local paths with mounted static paths
    for r in res:
        file_path = os.path.abspath(r["file_path"])
        dst = os.path.dirname(file_path)
        r["file_path"] = replace_path(dst) + os.path.basename(file_path)
    logger.info("Search completed with %s results.", len(res))
    return res


# Mount API routes
app.include_router(router, prefix="/api", tags=["api"])
