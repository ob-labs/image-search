"""
Image embedding utilities and dataset loaders.

This module provides:
- EmbeddingEngine: Generates image embeddings via API (DashScope etc.)
- ImageScanner: Scans directories for valid image files
"""

import base64
import os
import re
from http import HTTPStatus
from typing import FrozenSet, Iterator, Optional

from .db import ImageData
from .logger import get_logger

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Supported image file extensions
SUPPORTED_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png"})

# Pattern to filter non-ASCII printable characters in paths
_NON_ASCII_PATTERN = re.compile(r"[^ -~]")

# Logger for this module
_logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Embedding Engine
# -----------------------------------------------------------------------------


class EmbeddingEngine:
    """
    Generates image/text embeddings via API calls.

    Supports configurable backends via EMBEDDING_TYPE env var:
    - dashscope: DashScope Multimodal-Embedding API (default)

    Example:
        engine = EmbeddingEngine()
        embedding = engine.embed("/path/to/image.jpg")
    """

    def __init__(self):
        self._type = os.getenv("EMBEDDING_TYPE", "dashscope")
        self._model = os.getenv(
            "EMBEDDING_MODEL", "tongyi-embedding-vision-plus"
        )
        self._dimension = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
        self._api_key = os.getenv("EMBEDDING_API_KEY", "")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def embed(self, image_path: str) -> list[float]:
        """
        Generate an embedding vector for the given image file.

        Args:
            image_path: Path to the image file.

        Returns:
            A list of floats representing the image embedding.
        """
        if self._type == "dashscope":
            return self._embed_image_dashscope(image_path)
        else:
            raise ValueError(f"Unsupported EMBEDDING_TYPE: {self._type}")

    def embed_text(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Input text to embed.

        Returns:
            A list of floats representing the text embedding.
        """
        if self._type == "dashscope":
            return self._embed_text_dashscope(text)
        else:
            raise ValueError(f"Unsupported EMBEDDING_TYPE: {self._type}")

    # -------------------------------------------------------------------------
    # DashScope Backend
    # -------------------------------------------------------------------------

    def _embed_image_dashscope(self, image_path: str) -> list[float]:
        """Generate image embedding via DashScope Multimodal-Embedding API."""
        import dashscope
        from dashscope import MultiModalEmbedding

        dashscope.api_key = self._api_key

        b64_image = self._image_to_base64(image_path)
        ext = os.path.splitext(image_path)[1].lstrip(".").lower()
        if ext == "jpg":
            ext = "jpeg"
        data_uri = f"data:image/{ext};base64,{b64_image}"

        _logger.info("Generating image embedding via DashScope: %s", image_path)
        resp = MultiModalEmbedding.call(
            model=self._model,
            input=[{"image": data_uri}],
            dimension=self._dimension,
        )

        if resp.status_code != HTTPStatus.OK:
            error_msg = getattr(resp, "message", str(resp))
            _logger.error("DashScope embedding failed: %s", error_msg)
            raise RuntimeError(f"DashScope embedding failed: {error_msg}")

        embedding = resp.output["embeddings"][0]["embedding"]
        _logger.info("Generated image embedding (%d dims) for %s", len(embedding), image_path)
        return embedding

    def _embed_text_dashscope(self, text: str) -> list[float]:
        """Generate text embedding via DashScope Multimodal-Embedding API."""
        import dashscope
        from dashscope import MultiModalEmbedding

        dashscope.api_key = self._api_key

        _logger.info("Generating text embedding via DashScope: %s", text[:50])
        resp = MultiModalEmbedding.call(
            model=self._model,
            input=[{"text": text}],
            dimension=self._dimension,
        )

        if resp.status_code != HTTPStatus.OK:
            error_msg = getattr(resp, "message", str(resp))
            _logger.error("DashScope text embedding failed: %s", error_msg)
            raise RuntimeError(f"DashScope text embedding failed: {error_msg}")

        embedding = resp.output["embeddings"][0]["embedding"]
        _logger.info("Generated text embedding (%d dims)", len(embedding))
        return embedding

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _image_to_base64(image_path: str) -> str:
        """Read image file and return Base64-encoded string."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")


# -----------------------------------------------------------------------------
# Image Scanner
# -----------------------------------------------------------------------------


class ImageScanner:
    """
    Scans directories for valid image files.

    Filters out:
    - Hidden files (starting with '.')
    - macOS metadata folders (__MACOSX)
    - Paths containing non-ASCII characters
    - Files with unsupported extensions

    Example:
        scanner = ImageScanner("/path/to/images")
        print(f"Found {scanner.count()} images")
        for path in scanner.scan():
            print(path)
    """

    def __init__(
        self,
        directory: str,
        extensions: FrozenSet[str] = SUPPORTED_IMAGE_EXTENSIONS,
    ):
        self._directory = directory
        self._extensions = extensions

    def count(self) -> int:
        """Count the number of valid image files in the directory."""
        total = sum(1 for _ in self.scan())
        _logger.info("Counted %d images in %s", total, self._directory)
        return total

    def scan(self) -> Iterator[str]:
        """Yield absolute paths to valid image files."""
        for root, _, files in os.walk(self._directory):
            if not self._is_valid_directory(root):
                continue
            for filename in files:
                if self._is_valid_image_file(filename):
                    yield os.path.abspath(os.path.join(root, filename))

    def _is_valid_directory(self, path: str) -> bool:
        if "MACOSX" in path:
            return False
        if _NON_ASCII_PATTERN.match(path):
            return False
        return True

    def _is_valid_image_file(self, filename: str) -> bool:
        if filename.startswith("."):
            return False
        ext = os.path.splitext(filename)[1].lower()
        return ext in self._extensions


# -----------------------------------------------------------------------------
# Convenience Functions (Module-Level API)
# -----------------------------------------------------------------------------

_default_engine: Optional[EmbeddingEngine] = None


def _get_default_engine() -> EmbeddingEngine:
    """Get or create the default embedding engine."""
    global _default_engine
    if _default_engine is None:
        _default_engine = EmbeddingEngine()
    return _default_engine


def embed_img(path: str) -> list[float]:
    """
    Generate an embedding vector for the given image file.

    Args:
        path: Path to the image file.

    Returns:
        A list of floats representing the image embedding.
    """
    return _get_default_engine().embed(path)


def embed_text(text: str) -> list[float]:
    """
    Generate an embedding vector for the given text.

    Args:
        text: Input text to embed.

    Returns:
        A list of floats representing the text embedding.
    """
    return _get_default_engine().embed_text(text)


def caption_img(path: str) -> str:
    """
    Generate image caption using OpenAI-compatible API (Qwen/OpenAI/Azure etc).

    Args:
        path: Path to the image file.

    Returns:
        A text description of the image, or error message if generation fails.
    """
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.getenv("MODEL", "qwen-vl-max")

    if not api_key:
        return "[Error: LLM_API_KEY not set]"

    try:
        with open(path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        import openai
        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Identify the main object category/type in this image. "
                            "Answer with 1-2 words describing the species or object type only (e.g., 'dog', 'car', 'tree', 'building'). "
                            "Focus on WHAT it is, not how it looks."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                ]
            }],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        if content is None:
            _logger.warning("No caption generated for %s", path)
            return "[No caption]"
        caption = content.strip()
        _logger.info("Generated caption for %s: %s", path, caption)
        return caption
    except Exception as e:
        _logger.error("Failed to generate caption for %s: %s", path, e)
        return f"[Error: {str(e)}]"


def load_amount(dir_path: str) -> int:
    """Count how many valid image files exist under the directory."""
    return ImageScanner(dir_path).count()


def load_imgs(dir_path: str) -> Iterator[ImageData]:
    """Yield ImageData objects for each valid image in the directory."""
    engine = _get_default_engine()
    scanner = ImageScanner(dir_path)

    for file_path in scanner.scan():
        embedding = engine.embed(file_path)
        caption = caption_img(file_path)
        yield ImageData(
            file_name=os.path.basename(file_path),
            file_path=file_path,
            caption=caption,
            embedding=embedding,
        )
