"""File saving module with UTF-8-aware buffered writing.

Writes files in chunks using a configurable buffer size. The buffer
splitting logic respects UTF-8 multibyte character boundaries so that
a character spanning a chunk edge is never torn apart.
"""

import os
import tempfile

BUFFER_SIZE = 65536  # 64 KB default chunk size


def _find_safe_split(data: bytes, limit: int) -> int:
    """Return the largest index <= *limit* that sits on a UTF-8 character
    boundary.

    UTF-8 continuation bytes have the bit pattern ``10xxxxxx`` (0x80..0xBF).
    Walking backwards from *limit* until we land on a byte that is **not** a
    continuation byte gives us the start of the last character that would be
    split.  We split just before that character so the current chunk contains
    only complete characters.
    """
    if limit >= len(data):
        return len(data)

    pos = limit
    # Walk back over continuation bytes (0x80..0xBF)
    while pos > 0 and 0x80 <= data[pos] <= 0xBF:
        pos -= 1

    # *pos* now points at the leading byte of a multibyte character that
    # would be split.  Split before it so this chunk is clean.
    return pos if pos > 0 else limit


def save_file(content: str, path: str, buffer_size: int = BUFFER_SIZE) -> None:
    """Save *content* to *path* using buffered writes.

    The content is encoded to UTF-8 and written in chunks of at most
    *buffer_size* bytes.  Chunk boundaries are adjusted so that no
    multibyte character is split across two writes.

    A temporary file in the same directory is used for atomicity: the
    data is written to a temp file first, then renamed into place.
    """
    encoded = content.encode("utf-8")
    dir_name = os.path.dirname(os.path.abspath(path))

    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    try:
        offset = 0
        while offset < len(encoded):
            end = min(offset + buffer_size, len(encoded))
            if end < len(encoded):
                end = offset + _find_safe_split(encoded[offset:], buffer_size)
            chunk = encoded[offset:end]
            os.write(fd, chunk)
            offset = end
        os.fsync(fd)
        os.close(fd)
        os.replace(tmp_path, path)
    except BaseException:
        os.close(fd)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
