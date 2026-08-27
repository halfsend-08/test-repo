"""File saving module with proper UTF-8 support.

Handles saving files of arbitrary size with correct byte-length
buffer allocation for UTF-8 encoded content.
"""

import os

# Buffer size for chunked writes (64KB).
BUFFER_SIZE = 65536


def save_file(content, file_path):
    """Save content to a file with proper UTF-8 encoding.

    Encodes the content to UTF-8 bytes first, then writes in
    chunks sized by byte length (not character count) to avoid
    buffer overruns with multibyte characters.

    Args:
        content: String content to save.
        file_path: Destination file path.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(file_path, "wb") as f:
        offset = 0
        while offset < len(encoded):
            end = offset + BUFFER_SIZE
            f.write(encoded[offset:end])
            offset = end


def load_file(file_path):
    """Load a UTF-8 encoded file and return its string content.

    Args:
        file_path: Path to the file to read.

    Returns:
        The file content as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    with open(file_path, "rb") as f:
        return f.read().decode("utf-8")
