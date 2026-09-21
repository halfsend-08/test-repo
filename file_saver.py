"""File save utility with correct UTF-8 byte-length handling.

Encodes text content to UTF-8 and writes the resulting bytes to disk,
ensuring buffer operations use actual byte length rather than character
count. Callers must validate filepath; passing untrusted input directly
risks arbitrary file writes.
"""


def save_file(filepath: str, content: str) -> None:
    """Save text content to a file using UTF-8 encoding.

    Encodes content to bytes before writing so that the byte length
    (not character count) governs all buffer operations, preventing
    overruns with multibyte characters.
    """
    encoded = content.encode("utf-8")
    with open(filepath, "wb") as f:
        f.write(encoded)
