"""
File utility functions for calculating directory size and formatting sizes.
"""

import logging
import os

logger = logging.getLogger(__name__)


def calculate_directory_size(directory: str) -> tuple[int, int]:
    """
    Calculate total size and file count in a directory and its subdirectories.

    :param directory: Directory to calculate size for
    :return: Tuple of (total_size_bytes, file_count)
    """
    total_size = 0
    file_count = 0

    if not os.path.exists(directory):
        return 0, 0

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                total_size += os.path.getsize(file_path)
                file_count += 1
            except OSError as e:
                logger.warning("Could not get size of %s: %s", file_path, e)

    return total_size, file_count


def format_size(size_bytes: int) -> str:
    """
    Format bytes into human-readable format.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
