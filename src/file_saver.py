"""File saving module with chunked write support.

Saves content to disk in chunks, correctly handling UTF-8 multibyte
characters by sizing the write buffer in bytes rather than characters.
"""

import os

# Default chunk size for buffered writes (64 KiB).
CHUNK_SIZE = 65536


def save_file(path: str, content: str) -> int:
    """Save text content to a file using chunked byte writes.

    The content is encoded to UTF-8 and written in byte-sized chunks so
    that files of any size — including those with multibyte characters —
    are handled correctly.

    Args:
        path: Destination file path.
        content: The text content to save.

    Returns:
        The number of bytes written.

    Raises:
        OSError: If the file cannot be opened or written.
        TypeError: If *content* is not a string.
    """
    if not isinstance(content, str):
        raise TypeError(f"content must be str, got {type(content).__name__}")

    encoded = content.encode("utf-8")
    total = len(encoded)

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    bytes_written = 0
    with open(path, "wb") as fh:
        offset = 0
        while offset < total:
            end = min(offset + CHUNK_SIZE, total)
            fh.write(encoded[offset:end])
            bytes_written += end - offset
            offset = end

    return bytes_written
