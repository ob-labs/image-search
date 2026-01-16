# coding: utf-8
"""
FastAPI entrypoint that serves static assets and image search APIs.
"""
import os
import tempfile
from pathlib import Path
import dotenv

# Load environment variables for DB and app initialization
dotenv.load_dotenv()

from image_search.connection import connection_args

from fastapi import FastAPI, APIRouter, File, UploadFile
from fastapi.responses import FileResponse
from starlette import staticfiles
import fastapi_cdn_host


# Create the FastAPI app and patch docs to use CDN assets
app = FastAPI(title="Image Search App", version="0.1.0")
fastapi_cdn_host.patch_docs(app)

# Resolve and mount the frontend build output as static assets
base_dir = Path(__file__).resolve().parents[2]
dist_dir = base_dir / "dist"
app.mount("/static", staticfiles.StaticFiles(directory=str(dist_dir)), name="static")

# Create an API router and mount it under /api
router = APIRouter()

# Read image table name (default: image_search)
table_name = os.getenv("IMG_TABLE_NAME", "image_search")

# Track mounted image directories to avoid duplicate mounts
image_dirs: dict[str, int] = {}


from image_search.image_store import OBImageStore

# Initialize the image vector store client
store = OBImageStore(
    uri=f"{connection_args['host']}:{connection_args['port']}",
    **connection_args,
    table_name=table_name,
)


def replace_path(path: str) -> str:
    """
    Map a local directory to a static URL prefix and return it.
    """

    # Mount the directory the first time it appears
    if path not in image_dirs:
        image_dirs[path] = len(image_dirs) + 1
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

    # Search similar images in the vector store
    res = store.search(tf.name, limit=top_k)

    # Replace local paths with mounted static paths
    for r in res:
        file_path = os.path.abspath(r["file_path"])
        dst = os.path.dirname(file_path)
        r["file_path"] = replace_path(dst) + os.path.basename(file_path)
    return res


# Mount API routes
app.include_router(router, prefix="/api", tags=["api"])
