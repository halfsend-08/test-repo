"""File save utility with correct UTF-8 buffer handling.

Fixes a buffer overrun that caused a segmentation fault when saving files
larger than 64KB containing multibyte UTF-8 characters (e.g., emoji or CJK
characters). The root cause was using character count (len(text)) for buffer
allocation instead of the actual byte length of the encoded content.
"""

import os
import tempfile

# Buffer size threshold in bytes (64KB)
BUFFER_SIZE = 64 * 1024


def save_file(filepath: str, content: str) -> None:
    """Save text content to a file, correctly handling UTF-8 encoding.

    Uses byte length (not character count) to determine buffer sizing,
    preventing buffer overruns when multibyte UTF-8 characters push the
    actual encoded size past the buffer boundary.

    Args:
        filepath: Destination file path.
        content: Text content to save.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    byte_length = len(encoded)

    # Write atomically via temp file to prevent data loss on failure
    dir_name = os.path.dirname(os.path.abspath(filepath))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    try:
        offset = 0
        while offset < byte_length:
            chunk_end = min(offset + BUFFER_SIZE, byte_length)
            os.write(fd, encoded[offset:chunk_end])
            offset = chunk_end
        os.close(fd)
        os.replace(tmp_path, filepath)
    except Exception:
        os.close(fd)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def calculate_buffer_size(content: str) -> int:
    """Return the byte length of content when encoded as UTF-8.

    This must be used instead of len(content) for buffer allocation,
    because multibyte UTF-8 characters occupy more than one byte per
    character.

    Args:
        content: Text string to measure.

    Returns:
        The number of bytes in the UTF-8-encoded representation.
    """
    return len(content.encode("utf-8"))
