import tarfile
import zipfile
from os import path

tar_mode_mapping = {
    "application/x-tar": "r",
    "application/gzip": "r:gz",
    "application/x-bzip2": "r:bz2",
    "application/x-xz": "r:xz",
}


def extract_bundle(source: str, target: str):
    """
    extract_bundle extracts the contents of a compressed file to a directory
    Support file types: zip, tar, gz, bz2, xz
    @param file_path: path to the compressed file
    @return: path to the extracted directory
    """
    file_ext = path.splitext(source)[1]
    if file_ext == ".zip":
        with zipfile.ZipFile(source, "r") as zip_ref:
            zip_ref.extractall(target)
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
