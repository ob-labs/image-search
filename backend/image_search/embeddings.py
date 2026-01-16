import os
import re
from typing import Iterator
from towhee import AutoPipes
from pydantic import BaseModel

pattern = re.compile(r"[^ -~]")

class ImageData(BaseModel):
    file_name: str = ""
    file_path: str = ""
    embedding: list[float]


img_pipe = AutoPipes.pipeline("text_image_embedding")


def embed_img(path) -> list[float]:
    return img_pipe(path).get()[0]


supported_img_types = [".jpg", ".jpeg", ".png"]


def load_amount(dir_path: str) -> int:
    total = 0
    for root, _, files in os.walk(dir_path):
        if "MACOSX" in root:
            continue
        if pattern.match(root):
            continue
        for f in files:
            if f.startswith("."):
                continue
            if not any([f.casefold().endswith(ext) for ext in supported_img_types]):
                continue
            total += 1
    return total


def load_imgs(dir_path: str) -> Iterator[ImageData]:
    for root, _, files in os.walk(dir_path):
        if "MACOSX" in root:
            continue
        if pattern.match(root):
            continue
        for f in files:
            if f.startswith("."):
                continue
            if not any([f.casefold().endswith(ext) for ext in supported_img_types]):
                continue
            file_path = os.path.abspath(os.path.join(root, f))
            embedding = embed_img(file_path)
            yield ImageData(
                file_name=f,
                file_path=file_path,
                embedding=embedding,
            )
