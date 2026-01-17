"""
Archive extraction helpers for loading image bundles.
"""

import tarfile
import zipfile
from os import path

from .logger import get_logger

# Logger for archive utilities
logger = get_logger(__name__)

# Mapping from mime-like extensions to tarfile read modes
tar_mode_mapping = {
    "application/x-tar": "r",
    "application/gzip": "r:gz",
    "application/x-bzip2": "r:bz2",
    "application/x-xz": "r:xz",
}


def extract_bundle(source: str, target: str) -> None:
    """
    Extract an archive to a target directory.

    Supported formats: zip, tar, gz, bz2, xz.
    """
    file_ext = path.splitext(source)[1]

    # Handle zip files
    if file_ext == ".zip":
        logger.info("Extracting zip archive %s to %s", source, target)
        with zipfile.ZipFile(source, "r") as zip_ref:
            zip_ref.extractall(target)

    # Handle tar-based archives
    elif file_ext in [
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
    ]:
        logger.info("Extracting tar archive %s to %s", source, target)
        with tarfile.open(source, tar_mode_mapping[file_ext]) as tar:
            tar.extractall(target)
    else:
        logger.error("Unsupported archive type: %s", file_ext)
        raise ValueError("Unsupported file type")
