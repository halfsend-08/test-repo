"""File handler module for saving documents.

Handles file save operations with proper UTF-8 encoding support,
including multibyte characters (emoji, CJK, etc.) in files of any size.
"""

import os

# Buffer size for chunked file writing (64KB)
BUFFER_SIZE = 65536


def save_file(filepath, content):
    """Save content to a file with proper UTF-8 encoding.

    Allocates write buffer based on byte length of the encoded content,
    not the character count. This ensures multibyte UTF-8 characters
    (emoji, CJK, accented characters) are handled correctly regardless
    of file size.

    Args:
        filepath: Path to the output file.
        content: String content to save.

    Raises:
        OSError: If the file cannot be written.
        TypeError: If content is not a string.
    """
    if not isinstance(content, str):
        raise TypeError("content must be a string")

    encoded = content.encode("utf-8")
    byte_length = len(encoded)

    # Write in chunks to handle large files efficiently
    with open(filepath, "wb") as f:
        offset = 0
        while offset < byte_length:
            end = min(offset + BUFFER_SIZE, byte_length)
            # Avoid splitting a multibyte character at the chunk boundary
            if end < byte_length:
                # Back up to the start of any split multibyte sequence
                while end > offset and (encoded[end] & 0xC0) == 0x80:
                    end -= 1
            f.write(encoded[offset:end])
            offset = end


def read_file(filepath):
    """Read a file and return its content as a string.

    Args:
        filepath: Path to the input file.

    Returns:
        The file content as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
