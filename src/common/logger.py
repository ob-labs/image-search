"""
Shared logging setup for the image search project.
"""

from __future__ import annotations

import logging
from pathlib import Path


_LOG_FORMAT = "[%(name)s-%(asctime)s-%(levelname)s] %(message)s"
_LOG_LEVEL = logging.INFO
_BASE_LOGGER_NAME = "image-search"
_CONFIGURED = False


def _build_log_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "image.log"


def _configure_base_logger() -> logging.Logger:
    global _CONFIGURED
    base_logger = logging.getLogger(_BASE_LOGGER_NAME)
    if _CONFIGURED:
        return base_logger

    base_logger.setLevel(_LOG_LEVEL)
    base_logger.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(_LOG_LEVEL)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(_build_log_path(), encoding="utf-8")
    file_handler.setLevel(_LOG_LEVEL)
    file_handler.setFormatter(formatter)

    base_logger.addHandler(console_handler)
    base_logger.addHandler(file_handler)
    _CONFIGURED = True
    return base_logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a configured logger with console and file handlers.
    """
    base_logger = _configure_base_logger()
    if not name:
        return base_logger

    if name.startswith(_BASE_LOGGER_NAME):
        logger_name = name
    else:
        logger_name = f"{_BASE_LOGGER_NAME}.{name}"

    logger = logging.getLogger(logger_name)
    logger.setLevel(_LOG_LEVEL)
    logger.propagate = True
    return logger
