"""File save utility with correct UTF-8 buffer handling.

Fixes a buffer overrun that caused a segmentation fault when saving files
larger than 64KB containing multibyte UTF-8 characters (e.g., emoji or CJK
characters). The root cause was using character count (len(text)) for buffer
allocation instead of the actual byte length of the encoded content.
"""

# Buffer size threshold in bytes (64KB)
BUFFER_SIZE = 64 * 1024


def save_file(filepath: str, content: str) -> None:
    """Save text content to a file, correctly handling UTF-8 encoding.

    Uses byte length (not character count) to determine buffer sizing,
    preventing buffer overruns when multibyte UTF-8 characters push the
    actual encoded size past the buffer boundary.

    Args:
        filepath: Destination file path. Callers must validate this path;
            passing untrusted input directly risks arbitrary file writes.
        content: Text content to save.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    byte_length = len(encoded)

    with open(filepath, "wb") as f:
        offset = 0
        while offset < byte_length:
            chunk_end = min(offset + BUFFER_SIZE, byte_length)
            f.write(encoded[offset:chunk_end])
            offset = chunk_end
