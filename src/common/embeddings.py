"""
Image embedding utilities and dataset loaders.

This module provides:
- EmbeddingEngine: Generates image embeddings using Towhee or CLIP
- ImageScanner: Scans directories for valid image files
"""

import os
import re
import warnings
from typing import FrozenSet, Iterator, Optional

import cv2
import torch
from towhee import AutoPipes
from transformers import CLIPModel, CLIPProcessor

from .db import ImageData
from .logger import get_logger

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Supported image file extensions
SUPPORTED_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png"})

# Default CLIP model identifier
DEFAULT_CLIP_MODEL = "openai/clip-vit-base-patch16"

# Pattern to filter non-ASCII printable characters in paths
_NON_ASCII_PATTERN = re.compile(r"[^ -~]")

# Logger for this module
_logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Embedding Engine
# -----------------------------------------------------------------------------


class EmbeddingEngine:
    """
    Generates image embeddings using Towhee pipeline or CLIP model.

    The engine lazily initializes the underlying models on first use.
    It first attempts to use Towhee pipeline, falling back to CLIP if unavailable.

    Example:
        engine = EmbeddingEngine()
        embedding = engine.embed("/path/to/image.jpg")
    """

    def __init__(self, clip_model_name: str = DEFAULT_CLIP_MODEL):
        """
        Initialize the embedding engine.

        Args:
            clip_model_name: HuggingFace model identifier for CLIP fallback.
        """
        self._clip_model_name = clip_model_name
        self._towhee_pipe = None
        self._towhee_available: Optional[bool] = None
        self._clip_model: Optional[CLIPModel] = None
        self._clip_processor: Optional[CLIPProcessor] = None

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

        Raises:
            ValueError: If the image cannot be read.
        """
        if self._is_towhee_available():
            embedding = self._embed_with_towhee(image_path)
            if embedding is not None:
                return embedding

        return self._embed_with_clip(image_path)

    # -------------------------------------------------------------------------
    # Towhee Backend
    # -------------------------------------------------------------------------

    def _is_towhee_available(self) -> bool:
        """Check if Towhee pipeline is available."""
        if self._towhee_available is None:
            self._init_towhee()
        return bool(self._towhee_available)

    def _init_towhee(self) -> None:
        """Initialize Towhee pipeline for image embedding."""
        try:
            self._towhee_pipe = AutoPipes.pipeline("text_image_embedding")
            self._towhee_available = True
            _logger.info("Towhee pipeline initialized successfully.")
        except Exception as exc:
            self._towhee_available = False
            self._log_fallback_warning("Towhee pipeline initialization failed", exc)

    def _embed_with_towhee(self, image_path: str) -> Optional[list]:
        """
        Generate embedding using Towhee pipeline.

        Returns None if embedding fails, allowing fallback to CLIP.
        """
        if self._towhee_pipe is None:
            return None

        try:
            _logger.info("Generating embedding with Towhee: %s", image_path)
            result = self._towhee_pipe(image_path).get()[0]
            return list(result) if result is not None else None
        except Exception as exc:
            self._log_fallback_warning("Towhee embedding failed", exc)
            return None

    # -------------------------------------------------------------------------
    # CLIP Backend
    # -------------------------------------------------------------------------

    def _ensure_clip_loaded(self) -> None:
        """Ensure CLIP model and processor are loaded."""
        if self._clip_model is not None:
            return

        _logger.info("Loading CLIP model: %s", self._clip_model_name)
        model = CLIPModel.from_pretrained(self._clip_model_name)
        model.eval()
        model.to("cpu")
        self._clip_model = model
        self._clip_processor = CLIPProcessor.from_pretrained(self._clip_model_name)

    def _embed_with_clip(self, image_path: str) -> list:
        """
        Generate embedding using CLIP model.

        Raises:
            ValueError: If the image cannot be read.
            RuntimeError: If CLIP model fails to load.
        """
        image = self._load_image(image_path)
        self._ensure_clip_loaded()

        if self._clip_processor is None or self._clip_model is None:
            raise RuntimeError("Failed to load CLIP model")

        inputs = self._clip_processor(images=image, return_tensors="pt")
        with torch.no_grad():
            features = self._clip_model.get_image_features(**inputs)
            features = features / features.norm(p=2, dim=-1, keepdim=True)

        _logger.info("Generated embedding with CLIP: %s", image_path)
        return features.squeeze(0).cpu().tolist()

    def embed_text(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text using CLIP.

        Args:
            text: Input text to embed.

        Returns:
            A list of floats representing the text embedding.

        Raises:
            RuntimeError: If CLIP model fails to load.
        """
        self._ensure_clip_loaded()

        if self._clip_processor is None or self._clip_model is None:
            raise RuntimeError("Failed to load CLIP model")

        inputs = self._clip_processor(text=[text], return_tensors="pt", padding=True)
        with torch.no_grad():
            features = self._clip_model.get_text_features(**inputs)
            features = features / features.norm(p=2, dim=-1, keepdim=True)

        _logger.info("Generated text embedding with CLIP: %s", text[:50])
        return features.squeeze(0).cpu().tolist()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _load_image(image_path: str):
        """Load and convert image to RGB format."""
        image = cv2.imread(image_path)
        if image is None:
            _logger.error("Failed to read image: %s", image_path)
            raise ValueError(f"Failed to read image: {image_path}")
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    @staticmethod
    def _log_fallback_warning(message: str, exc: Exception) -> None:
        """Log warning about fallback to CLIP."""
        full_message = f"{message}, falling back to CLIP. Error: {exc}"
        warnings.warn(full_message)
        _logger.warning(full_message)


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
        """
        Initialize the image scanner.

        Args:
            directory: Root directory to scan.
            extensions: Set of valid file extensions (lowercase, with dot).
        """
        self._directory = directory
        self._extensions = extensions

    def count(self) -> int:
        """Count the number of valid image files in the directory."""
        total = sum(1 for _ in self.scan())
        _logger.info("Counted %d images in %s", total, self._directory)
        return total

    def scan(self) -> Iterator[str]:
        """
        Yield absolute paths to valid image files.

        Yields:
            Absolute path to each valid image file.
        """
        for root, _, files in os.walk(self._directory):
            if not self._is_valid_directory(root):
                continue

            for filename in files:
                if self._is_valid_image_file(filename):
                    yield os.path.abspath(os.path.join(root, filename))

    def _is_valid_directory(self, path: str) -> bool:
        """Check if directory should be scanned."""
        if "MACOSX" in path:
            return False
        if _NON_ASCII_PATTERN.match(path):
            return False
        return True

    def _is_valid_image_file(self, filename: str) -> bool:
        """Check if file is a valid image file."""
        if filename.startswith("."):
            return False
        ext = os.path.splitext(filename)[1].lower()
        return ext in self._extensions


# -----------------------------------------------------------------------------
# Convenience Functions (Module-Level API)
# -----------------------------------------------------------------------------

# Default engine instance (lazily created)
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

    This is a convenience function using the default engine.

    Args:
        path: Path to the image file.

    Returns:
        A list of floats representing the image embedding.
    """
    return _get_default_engine().embed(path)


def embed_text(text: str) -> list[float]:
    """
    Generate an embedding vector for the given text.

    This is a convenience function using the default engine with CLIP.

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
    import base64

    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.getenv("MODEL", "qwen-vl-max")

    if not api_key:
        return "[Error: API_KEY not set]"

    try:
        with open(path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        # Initialize OpenAI client
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
    """
    Count how many valid image files exist under the directory.

    Args:
        dir_path: Root directory to scan.

    Returns:
        Number of valid image files.
    """
    return ImageScanner(dir_path).count()


def load_imgs(dir_path: str) -> Iterator[ImageData]:
    """
    Yield ImageData objects for each valid image in the directory.

    Args:
        dir_path: Root directory to scan.

    Yields:
        ImageData with file metadata, caption, and embedding.
    """
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
