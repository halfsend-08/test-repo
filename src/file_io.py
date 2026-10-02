"""File I/O module with proper UTF-8 handling.

Provides buffered file saving that correctly calculates buffer sizes
using byte length rather than character count, ensuring safe handling
of multibyte UTF-8 characters at any file size.
"""

import os

BUFFER_SIZE = 64 * 1024  # 64KB


def save_file(filepath: str, content: str) -> None:
    """Save content to a file using buffered writes.

    Splits content into chunks based on byte length (not character
    count) to avoid buffer overflows with multibyte UTF-8 characters.

    Args:
        filepath: Path to the output file.
        content: The text content to write.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(filepath, "wb") as f:
        offset = 0
        while offset < len(encoded):
            end = offset + BUFFER_SIZE
            chunk = encoded[offset:end]
            f.write(chunk)
            offset = end


def read_file(filepath: str) -> str:
    """Read a UTF-8 encoded file and return its content as a string.

    Args:
        filepath: Path to the input file.

    Returns:
        The file content decoded as UTF-8.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    with open(filepath, "rb") as f:
        return f.read().decode("utf-8")
