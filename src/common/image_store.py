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

        res = self.client.ann_search(
            table_name,
            vec_data=target_embedding,
            vec_column_name="embedding",
            topk=limit,
            distance_func=func.l2_distance,
            output_column_names=output_fields,
            with_dist=True,
        )

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
                "distance": row[2],
            }
            for row in rows
        ]
