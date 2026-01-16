"""
Image embedding utilities and dataset loaders.
"""

import os
import re
from typing import Iterator
from towhee import AutoPipes
from pydantic import BaseModel

# Match non-ASCII printable characters to filter problematic paths
pattern = re.compile(r"[^ -~]")


class ImageData(BaseModel):
    """
    Typed container for image file metadata and embeddings.
    """

    file_name: str = ""
    file_path: str = ""
    embedding: list[float]


# Initialize the Towhee pipeline for image embedding
img_pipe = AutoPipes.pipeline("text_image_embedding")


def embed_img(path: str) -> list[float]:
    """
    Generate an embedding vector for the given image file.
    """
    return img_pipe(path).get()[0]


# Supported image file extensions
supported_img_types = [".jpg", ".jpeg", ".png"]


def load_amount(dir_path: str) -> int:
    """
    Count how many valid image files exist under the directory.
    """
    total = 0
    for root, _, files in os.walk(dir_path):

        # Skip macOS metadata folders and non-ASCII paths
        if "MACOSX" in root:
            continue
        if pattern.match(root):
            continue
        for f in files:

            # Skip hidden files and non-image extensions
            if f.startswith("."):
                continue
            if not any([f.casefold().endswith(ext) for ext in supported_img_types]):
                continue
            total += 1
    return total


def load_imgs(dir_path: str) -> Iterator[ImageData]:
    """
    Yield ImageData objects for each valid image in the directory.
    """
    for root, _, files in os.walk(dir_path):

        # Skip macOS metadata folders and non-ASCII paths
        if "MACOSX" in root:
            continue
        if pattern.match(root):
            continue
        for f in files:

            # Skip hidden files and non-image extensions
            if f.startswith("."):
                continue
            if not any([f.casefold().endswith(ext) for ext in supported_img_types]):
                continue

            # Build absolute path and compute embeddings
            file_path = os.path.abspath(os.path.join(root, f))
            embedding = embed_img(file_path)
            yield ImageData(
                file_name=f,
                file_path=file_path,
                embedding=embedding,
            )
