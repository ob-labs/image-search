"""
Archive extraction helpers for loading image bundles.
"""

import tarfile
import zipfile
from os import path

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
        with zipfile.ZipFile(source, "r") as zip_ref:
            zip_ref.extractall(target)

    # Handle tar-based archives
    elif file_ext in [
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
    ]:
        with tarfile.open(source, tar_mode_mapping[file_ext]) as tar:
            tar.extractall(target)
    else:
        raise ValueError("Unsupported file type")
