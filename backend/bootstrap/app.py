# coding: utf-8
import os
import tempfile
from pathlib import Path
import dotenv

dotenv.load_dotenv()

from image_search.connection import connection_args

from fastapi import FastAPI, APIRouter, File, UploadFile
from fastapi.responses import FileResponse
from starlette import staticfiles
import fastapi_cdn_host



app = FastAPI(title="Image Search App", version="0.1.0")
fastapi_cdn_host.patch_docs(app)
base_dir = Path(__file__).resolve().parents[2]
dist_dir = base_dir / "dist"
app.mount("/static", staticfiles.StaticFiles(directory=str(dist_dir)), name="static")
router = APIRouter()
table_name = os.getenv("IMG_TABLE_NAME", "image_search")
image_dirs = {}


from image_search.image_store import OBImageStore

store = OBImageStore(
    uri=f"{connection_args['host']}:{connection_args['port']}",
    **connection_args,
    table_name=table_name,
)


def replace_path(path):
    if path not in image_dirs:
        image_dirs[path] = len(image_dirs) + 1
        app.mount(f"/images/{image_dirs[path]}", staticfiles.StaticFiles(directory=path), name=f"static_{image_dirs[path]}")
    return f"/images/{image_dirs[path]}/"


@app.get("/")
async def read_index():
    return FileResponse(str(dist_dir / "index.html"))


@router.post("/search")
async def search_image(
    file: UploadFile = File(...),
    top_k: int = 10,
):
    content = await file.read()
    file_type = os.path.splitext(file.filename)[1]
    tf = tempfile.NamedTemporaryFile(suffix=file_type)
    tf.write(content)
    tf.flush()

    res = store.search(tf.name, limit=top_k)
    for r in res:
        file_path = os.path.abspath(r["file_path"])
        dst = os.path.dirname(file_path)
        r["file_path"] = replace_path(dst) + os.path.basename(file_path)
    return res


app.include_router(router, prefix="/api", tags=["api"])
