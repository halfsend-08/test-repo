"""File saver module with proper UTF-8 multibyte character handling.

This module handles saving files of arbitrary size with correct buffer
allocation based on byte count rather than character count, preventing
buffer overflow when saving files containing multibyte UTF-8 characters
(e.g., emoji, CJK characters) that exceed 64KB.
"""

import os
import tempfile

# Buffer size in bytes for chunked writes
WRITE_BUFFER_SIZE = 65536  # 64KB


def save_file(filepath, content):
    """Save content to a file with proper UTF-8 encoding.

    Uses byte-length-aware buffering to correctly handle multibyte
    UTF-8 characters. Writes to a temporary file first, then atomically
    renames to the target path to prevent data corruption on failure.

    Args:
        filepath: Path to the destination file.
        content: String content to save.

    Raises:
        OSError: If the file cannot be written.
        TypeError: If content is not a string.
    """
    if not isinstance(content, str):
        raise TypeError("content must be a string")

    encoded = content.encode("utf-8")

    dir_name = os.path.dirname(os.path.abspath(filepath))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    try:
        offset = 0
        while offset < len(encoded):
            chunk = encoded[offset:offset + WRITE_BUFFER_SIZE]
            os.write(fd, chunk)
            offset += len(chunk)
        os.close(fd)
        os.replace(tmp_path, filepath)
    except Exception:
        os.close(fd)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
