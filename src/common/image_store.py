"""
OceanBase image vector store wrapper (pyseekdb).
"""

from typing import Any, Iterable, Iterator, Optional

from tqdm import tqdm

from .db import (
    ImageData,
    get_or_create_collection,
)
from .embeddings import embed_img, load_imgs, load_amount
from .logger import get_logger

# Logger for image store operations
logger = get_logger(__name__)

# Separator for building composite IDs from file_name + file_path
_ID_SEP = "|"


def _make_composite_id(file_name: str, file_path: str) -> str:
    """Build a single string ID from the composite primary key."""
    return f"{file_name}{_ID_SEP}{file_path}"


def _split_composite_id(composite_id: str) -> tuple[str, str]:
    """Recover file_name and file_path from a composite ID."""
    parts = composite_id.split(_ID_SEP, 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


class OBImageStore:
    """
    High-level helper for loading and searching image vectors.
    """

    _DEFAULT_TABLE_NAME = "image_search"
    _DEFAULT_BATCH_SIZE = 320

    def __init__(
        self,
        client,
        table_name: str = _DEFAULT_TABLE_NAME,
    ):
        self.client = client
        self.table_name = table_name
        # Cache for Collection objects keyed by name
        self._collections: dict[str, Any] = {}

    def _get_collection(self, collection_name: str):
        """Get or create a collection, with local caching."""
        if collection_name not in self._collections:
            self._collections[collection_name] = get_or_create_collection(
                self.client, collection_name
            )
        return self._collections[collection_name]

    def _insert_batches(
        self,
        collection_name: str,
        rows: Iterable[ImageData],
        batch_size: int,
    ) -> Iterator[None]:
        collection = self._get_collection(collection_name)
        batch_ids: list[str] = []
        batch_embeddings: list[list[float]] = []
        batch_metadatas: list[dict[str, Any]] = []
        batch_documents: list[str] = []

        for img in rows:
            composite_id = _make_composite_id(img.file_name, img.file_path)
            batch_ids.append(composite_id)
            batch_embeddings.append(img.embedding)
            batch_metadatas.append(
                {"file_name": img.file_name, "file_path": img.file_path}
            )
            batch_documents.append(img.caption)
            yield
            if len(batch_ids) == batch_size:
                collection.upsert(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    documents=batch_documents,
                )
                logger.info("Upserted batch of %s images.", batch_size)
                batch_ids, batch_embeddings, batch_metadatas, batch_documents = (
                    [],
                    [],
                    [],
                    [],
                )
        if batch_ids:
            collection.upsert(
                ids=batch_ids,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                documents=batch_documents,
            )
            logger.info("Upserted final batch of %s images.", len(batch_ids))

    def load_amount(self, dir_path: str) -> int:
        """
        Return the number of images under a directory.
        """
        logger.info("Counting images under directory: %s", dir_path)
        return load_amount(dir_path)

    def load_image_dir(
        self,
        dir_path: str,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        table_name: Optional[str] = None,
    ) -> Iterator:
        """
        Load images from a directory, creating collection if missing.
        """
        table_name = table_name or self.table_name
        # Ensure collection exists
        self._get_collection(table_name)
        total = load_amount(dir_path)
        logger.info(
            "Loading images from %s with batch size %s (total=%s).",
            dir_path,
            batch_size,
            total,
        )
        rows = tqdm(load_imgs(dir_path), total=total)
        yield from self._insert_batches(table_name, rows, batch_size)

    # -------------------------------------------------------------------------
    # Search methods
    # -------------------------------------------------------------------------

    def search(
        self,
        image_path: str,
        limit: int = 10,
        table_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Search similar images by embedding distance (vector-only).
        """
        table_name = table_name or self.table_name
        collection = self._get_collection(table_name)

        logger.info("Searching similar images for %s.", image_path)
        target_embedding = embed_img(image_path)

        results = collection.query(
            query_embeddings=[target_embedding],
            n_results=limit,
            include=["metadatas", "documents"],
        )

        ids = results.get("ids", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]

        logger.info("ANN search returned %s results.", len(ids))
        return self._format_query_results(ids, metadatas, documents, distances)

    def text_search(
        self,
        query_text: str,
        limit: int = 50,
        table_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Full-text search based on caption via collection.get + $contains.

        Args:
            query_text: Text query for searching captions.
            limit: Maximum number of results to return.
            table_name: Optional collection name override.

        Returns:
            List of matching images.
        """
        table_name = table_name or self.table_name
        collection = self._get_collection(table_name)

        logger.info("Performing text search with query: %s", query_text)
        results = collection.get(
            where_document={"$contains": query_text},
            limit=limit,
            include=["metadatas", "documents"],
        )

        ids = results.get("ids", [])
        metadatas = results.get("metadatas", [])
        documents = results.get("documents", [])

        logger.info("Text search returned %s results.", len(ids))
        return self._format_get_results(ids, metadatas, documents)

    def hybrid_search(
        self,
        image_path: str,
        limit: int = 10,
        vector_weight: float = 0.7,
        distance_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search: vector + text with weighted fusion.

        Uses pyseekdb's native hybrid_search (RRF ranking) when both
        vector and text channels are active.

        Args:
            image_path: Path to the query image.
            limit: Number of final results to return.
            vector_weight: Weight for vector search (0.0=text only, 1.0=vector only).
            distance_threshold: Optional threshold to filter vector results.

        Returns:
            Search results sorted by relevance.
        """
        # Pure vector search
        if vector_weight == 1.0:
            results = self.search(image_path, limit=limit)
            if distance_threshold is not None:
                results = [
                    r for r in results if r.get("distance", 0) <= distance_threshold
                ]
            logger.info("Pure vector search returned %s results.", len(results))
            return results

        # Pure text search
        if vector_weight == 0.0:
            from .embeddings import caption_img

            query_caption = caption_img(image_path)
            results = self.text_search(query_caption, limit=limit)
            for r in results:
                r["distance"] = None
            logger.info("Pure text search returned %s results.", len(results))
            return results

        # Hybrid: use pyseekdb native hybrid_search with RRF
        from .embeddings import caption_img

        logger.info("Performing hybrid search for %s.", image_path)
        target_embedding = embed_img(image_path)
        query_caption = caption_img(image_path)

        table_name = self.table_name
        collection = self._get_collection(table_name)

        recall_limit = limit * 5
        results = collection.hybrid_search(
            query={
                "where_document": {"$contains": query_caption},
                "n_results": recall_limit,
            },
            knn={
                "query_embeddings": [target_embedding],
                "n_results": recall_limit,
            },
            rank={"rrf": {}},
            n_results=limit,
            include=["metadatas", "documents"],
        )

        ids = results.get("ids", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0] if results.get("distances") else []

        formatted = self._format_query_results(ids, metadatas, documents, distances)

        # Apply distance threshold filter if provided
        if distance_threshold is not None:
            formatted = [
                r for r in formatted
                if r.get("distance") is None or r.get("distance", 0) <= distance_threshold
            ]
            logger.info(
                "Filtered hybrid results by threshold %.2f: %s remaining.",
                distance_threshold,
                len(formatted),
            )

        logger.info("Hybrid search returned %s results.", len(formatted))
        return formatted

    # -------------------------------------------------------------------------
    # Result formatting helpers
    # -------------------------------------------------------------------------

    def _format_query_results(
        self,
        ids: list[str],
        metadatas: list[dict[str, Any]],
        documents: list[str],
        distances: list[float],
    ) -> list[dict[str, Any]]:
        """Format pyseekdb query/hybrid_search results (nested list already unpacked)."""
        results = []
        for i, cid in enumerate(ids):
            meta = metadatas[i] if i < len(metadatas) else {}
            file_name = meta.get("file_name", "")
            file_path = meta.get("file_path", "")
            if not file_name and not file_path:
                file_name, file_path = _split_composite_id(cid)
            caption = documents[i] if i < len(documents) else ""
            distance = distances[i] if i < len(distances) else None
            results.append(
                {
                    "file_name": file_name,
                    "file_path": file_path,
                    "caption": caption,
                    "distance": distance,
                }
            )
        return results

    def _format_get_results(
        self,
        ids: list[str],
        metadatas: list[dict[str, Any]],
        documents: list[str],
    ) -> list[dict[str, Any]]:
        """Format pyseekdb collection.get results (flat lists, no distances)."""
        results = []
        for i, cid in enumerate(ids):
            meta = metadatas[i] if i < len(metadatas) else {}
            file_name = meta.get("file_name", "")
            file_path = meta.get("file_path", "")
            if not file_name and not file_path:
                file_name, file_path = _split_composite_id(cid)
            caption = documents[i] if i < len(documents) else ""
            results.append(
                {
                    "file_name": file_name,
                    "file_path": file_path,
                    "caption": caption,
                    "distance": None,
                }
            )
        return results
