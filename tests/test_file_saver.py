"""Tests for file_saver module.

Verifies that files of various sizes and character encodings are
saved and read back correctly, including edge cases around the
64KB buffer boundary with UTF-8 multibyte characters.
"""

import os
import tempfile

import pytest

from src.file_saver import BUFFER_SIZE, load_file, save_file


@pytest.fixture
def tmp_path_file(tmp_path):
    """Return a temporary file path for saving."""
    return str(tmp_path / "output.txt")


class TestSaveFileASCII:
    """Tests for ASCII-only content."""

    def test_ascii_at_64kb(self, tmp_path_file):
        content = "a" * BUFFER_SIZE
        save_file(content, tmp_path_file)
        assert os.path.getsize(tmp_path_file) == BUFFER_SIZE
        assert load_file(tmp_path_file) == content

    def test_ascii_over_64kb(self, tmp_path_file):
        content = "b" * (BUFFER_SIZE + 1024)
        save_file(content, tmp_path_file)
        assert os.path.getsize(tmp_path_file) == BUFFER_SIZE + 1024
        assert load_file(tmp_path_file) == content


class TestSaveFileMultibyte:
    """Tests for UTF-8 multibyte content exceeding buffer size."""

    def test_emoji_byte_count_exceeds_buffer(self, tmp_path_file):
        # Each emoji is 4 bytes in UTF-8.  Use enough emoji so the
        # byte count exceeds 64KB while the character count stays below.
        emoji_count = (BUFFER_SIZE // 4) + 256
        content = "\U0001f600" * emoji_count  # grinning face
        encoded_len = len(content.encode("utf-8"))
        assert encoded_len > BUFFER_SIZE
        assert len(content) < BUFFER_SIZE

        save_file(content, tmp_path_file)
        assert os.path.getsize(tmp_path_file) == encoded_len
        assert load_file(tmp_path_file) == content

    def test_cjk_byte_count_exceeds_buffer(self, tmp_path_file):
        # CJK characters are 3 bytes each in UTF-8.
        char_count = (BUFFER_SIZE // 3) + 256
        content = "世" * char_count  # 世
        encoded_len = len(content.encode("utf-8"))
        assert encoded_len > BUFFER_SIZE

        save_file(content, tmp_path_file)
        assert os.path.getsize(tmp_path_file) == encoded_len
        assert load_file(tmp_path_file) == content

    def test_mixed_ascii_and_multibyte_over_64kb(self, tmp_path_file):
        # Mix ASCII and emoji to exceed 64KB total bytes.
        ascii_part = "x" * (BUFFER_SIZE - 100)
        emoji_part = "\U0001f680" * 100  # 400 bytes of rocket emoji
        content = ascii_part + emoji_part
        encoded_len = len(content.encode("utf-8"))
        assert encoded_len > BUFFER_SIZE

        save_file(content, tmp_path_file)
        assert os.path.getsize(tmp_path_file) == encoded_len
        assert load_file(tmp_path_file) == content


class TestSaveFileEdgeCases:
    """Edge cases and content integrity checks."""

    def test_empty_file(self, tmp_path_file):
        save_file("", tmp_path_file)
        assert os.path.getsize(tmp_path_file) == 0
        assert load_file(tmp_path_file) == ""

    def test_exactly_at_buffer_boundary_multibyte(self, tmp_path_file):
        # Build content whose UTF-8 encoding is exactly BUFFER_SIZE
        # bytes: fill with ASCII then pad with 2-byte chars.
        base = "a" * (BUFFER_SIZE - 2)
        content = base + "é"  # é is 2 bytes in UTF-8
        assert len(content.encode("utf-8")) == BUFFER_SIZE

        save_file(content, tmp_path_file)
        assert os.path.getsize(tmp_path_file) == BUFFER_SIZE
        assert load_file(tmp_path_file) == content

    def test_content_integrity_large_diverse(self, tmp_path_file):
        # >130KB of diverse characters: ASCII, accented, CJK, emoji.
        parts = [
            "Hello world! " * 4000,
            "éèê" * 5000,
            "世界" * 6000,
            "\U0001f600\U0001f680\U0001f30d" * 3000,
        ]
        content = "".join(parts)
        encoded_len = len(content.encode("utf-8"))
        assert encoded_len > 2 * BUFFER_SIZE

        save_file(content, tmp_path_file)
        assert os.path.getsize(tmp_path_file) == encoded_len
        assert load_file(tmp_path_file) == content

    def test_creates_parent_directories(self, tmp_path):
        nested = str(tmp_path / "a" / "b" / "c" / "file.txt")
        save_file("test", nested)
        assert load_file(nested) == "test"
