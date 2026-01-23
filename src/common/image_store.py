"""
OceanBase image vector store wrapper.
"""

from typing import Any, Iterable, Iterator, Optional, Sequence

from pyobvector import ObVecClient
from sqlalchemy import func
from tqdm import tqdm

from .db import ImageData, cols, output_fields
from .embeddings import embed_img, load_imgs, load_amount
from .logger import get_logger

# Logger for image store operations
logger = get_logger(__name__)


class OBImageStore:
    """
    High-level helper for loading and searching image vectors.
    """

    _DEFAULT_TABLE_NAME = "image_search"
    _DEFAULT_BATCH_SIZE = 320
    _DEFAULT_QUERY_TIMEOUT = 100000000
    def __init__(
        self,
        client: ObVecClient,
        table_name: str = _DEFAULT_TABLE_NAME,
    ):
        self.client = client
        self.table_name = table_name

    def _ensure_table(self, table_name: str) -> None:
        if self.client.check_table_exists(table_name):
            return
        logger.info("Table '%s' missing; creating schema.", table_name)
        self.client.create_table(table_name, columns=cols)
        self._create_ann_index(table_name)

    def _create_ann_index(self, table_name: str) -> None:
        logger.info("Creating ANN index for table '%s'.", table_name)
        self.client.create_index(
            table_name,
            is_vec_index=True,
            index_name="img_embedding_idx",
            column_names=["embedding"],
            vidx_params="distance=l2, type=hnsw, lib=vsag",
        )
        # Create fulltext index for caption
        logger.info("Creating fulltext index for caption on table '%s'.", table_name)
        self.client.perform_raw_text_sql(
            f"ALTER TABLE {table_name} ADD FULLTEXT INDEX caption_idx (caption)"
        )

    def _set_query_timeout(self, timeout: int) -> None:
        self.client.perform_raw_text_sql(f"SET ob_query_timeout={timeout}")

    def _insert_batches(
        self,
        table_name: str,
        rows: Iterable[ImageData],
        batch_size: int,
    ) -> Iterator[None]:
        batch: list[dict[str, Any]] = []
        for img in rows:
            batch.append(img.model_dump())
            yield
            if len(batch) == batch_size:
                self.client.upsert(table_name, batch)
                logger.info("Upserted batch of %s images.", batch_size)
                batch = []
        if batch:
            self.client.upsert(table_name, batch)
            logger.info("Upserted final batch of %s images .", len(batch))

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
        Load images from a directory, creating table/index if missing.
        """
        table_name = table_name or self.table_name
        self._ensure_table(table_name)
        self._set_query_timeout(self._DEFAULT_QUERY_TIMEOUT)
        total = load_amount(dir_path)
        logger.info(
            "Loading images from %s with batch size %s (total=%s).",
            dir_path,
            batch_size,
            total,
        )
        rows = tqdm(load_imgs(dir_path), total=total)
        yield from self._insert_batches(table_name, rows, batch_size)

    def search(
        self,
        image_path: str,
        limit: int = 10,
        table_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Search similar images by embedding distance.
        """
        table_name = table_name or self.table_name

        # Embed the target image for ANN search
        logger.info("Searching similar images for %s.", image_path)
        target_embedding = embed_img(image_path)

        cursor_result = self.client.ann_search(
            table_name,
            vec_data=target_embedding,
            vec_column_name="embedding",
            topk=limit,
            distance_func=func.l2_distance,
            output_column_names=output_fields,
            with_dist=True,
        )

        # Fetch all rows from cursor result
        res = cursor_result.fetchall()

        # Map raw tuples into dictionaries
        logger.info("ANN search returned %s results.", len(res))
        return self._format_search_results(res)

    def _format_search_results(
        self,
        rows: Sequence[Sequence[Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "file_name": row[0],
                "file_path": row[1],
                "caption": row[2],
                "distance": row[3],
            }
            for row in rows
        ]

    def text_search(self, query_text: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Full-text search based on caption using MATCH...AGAINST.

        Args:
            query_text: Text query for searching captions.
            limit: Maximum number of results to return.

        Returns:
            List of matching images with text scores.
        """
        # Escape single quotes in query text
        escaped_query = query_text.replace("'", "''")
        sql = f"""
            SELECT file_name, file_path, caption,
                   MATCH(caption) AGAINST('{escaped_query}' IN NATURAL LANGUAGE MODE) as text_score
            FROM {self.table_name}
            WHERE MATCH(caption) AGAINST('{escaped_query}' IN NATURAL LANGUAGE MODE)
            ORDER BY text_score DESC
            LIMIT {limit}
        """
        logger.info("Performing text search with query: %s", query_text)
        results = self.client.perform_raw_text_sql(sql)
        return [
            {
                "file_name": r[0],
                "file_path": r[1],
                "caption": r[2],
                "text_score": float(r[3]),
            }
            for r in results
        ]

    def _fuse_results(
        self,
        vector_results: list[dict[str, Any]],
        text_results: list[dict[str, Any]],
        vector_weight: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        """
        Normalize scores and fuse results with weighted sum.

        Args:
            vector_results: Results from vector search.
            text_results: Results from text search.
            vector_weight: Weight for vector search (0.0-1.0).
            limit: Maximum number of results to return.

        Returns:
            Fused and sorted results.
        """
        # Build ID mapping using file_name + file_path as composite key
        def make_id(item: dict) -> tuple:
            return (item["file_name"], item["file_path"])

        # Normalize vector distances to similarities [0, 1]
        vec_dict = {make_id(r): r["distance"] for r in vector_results}
        if vec_dict:
            max_dist = max(vec_dict.values()) or 1.0
            vec_norm = {img_id: 1 - (d / max_dist) for img_id, d in vec_dict.items()}
        else:
            vec_norm = {}

        # Normalize text scores to [0, 1]
        txt_dict = {make_id(r): r["text_score"] for r in text_results}
        if txt_dict:
            max_score = max(txt_dict.values()) or 1.0
            txt_norm = {img_id: s / max_score for img_id, s in txt_dict.items()}
        else:
            txt_norm = {}

        # Weighted fusion
        final_scores = {}
        all_ids = set(vec_norm.keys()) | set(txt_norm.keys())
        text_weight = 1 - vector_weight

        for img_id in all_ids:
            vec_sim = vec_norm.get(img_id, 0)
            txt_sim = txt_norm.get(img_id, 0)
            final_scores[img_id] = vector_weight * vec_sim + text_weight * txt_sim

        # Sort by fusion score
        sorted_ids = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[
            :limit
        ]

        # Build full result with complete info
        id_to_info = {}
        for r in vector_results + text_results:
            img_id = make_id(r)
            if img_id not in id_to_info:
                id_to_info[img_id] = r

        logger.info("Fused %s results from vector and text search.", len(sorted_ids))
        return [
            {
                **id_to_info[img_id],
                "fusion_score": score,
                "distance": id_to_info[img_id].get("distance"),
            }
            for img_id, score in sorted_ids
            if img_id in id_to_info
        ]

    def hybrid_search(
        self,
        image_path: str,
        limit: int = 10,
        vector_weight: float = 0.7,
        distance_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search: vector + text with weighted fusion.

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
            # Apply distance threshold filter
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
            # Add distance field as None for consistency
            for r in results:
                r["distance"] = None
            logger.info("Pure text search returned %s results.", len(results))
            return results

        # Hybrid: recall 5x, then fuse
        recall_limit = limit * 5
        vector_results = self.search(image_path, limit=recall_limit)

        # Filter vector results by distance threshold before fusion
        if distance_threshold is not None:
            vector_results = [
                r for r in vector_results if r.get("distance", 0) <= distance_threshold
            ]
            logger.info(
                "Filtered vector results by threshold %.2f: %s remaining.",
                distance_threshold,
                len(vector_results),
            )

        from .embeddings import caption_img

        query_caption = caption_img(image_path)
        text_results = self.text_search(query_caption, limit=recall_limit)

        logger.info(
            "Hybrid search: %s vector + %s text results before fusion.",
            len(vector_results),
            len(text_results),
        )
        return self._fuse_results(vector_results, text_results, vector_weight, limit)
