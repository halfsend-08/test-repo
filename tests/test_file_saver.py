"""Tests for the file_saver module.

Covers the scenarios from issue #1320: saving files larger than 64 KB
that contain UTF-8 multibyte characters must succeed and preserve
content byte-for-byte.
"""

import os
import tempfile

import pytest

from src.file_saver import CHUNK_SIZE, save_file


@pytest.fixture
def tmp_path_file(tmp_path):
    """Return a path inside a temporary directory."""
    return str(tmp_path / "output.txt")


class TestSaveFileBasic:
    """Basic save operations."""

    def test_save_small_ascii(self, tmp_path_file):
        content = "hello world"
        written = save_file(tmp_path_file, content)
        assert written == len(content.encode("utf-8"))
        with open(tmp_path_file, "rb") as f:
            assert f.read() == content.encode("utf-8")

    def test_save_empty(self, tmp_path_file):
        written = save_file(tmp_path_file, "")
        assert written == 0
        with open(tmp_path_file, "rb") as f:
            assert f.read() == b""


class TestSaveFileUTF8:
    """UTF-8 multibyte character handling."""

    def test_save_under_64kb_with_emoji(self, tmp_path_file):
        # Each emoji is 4 bytes in UTF-8; create content just under 64 KB.
        emoji = "\U0001F600"  # 😀
        count = (CHUNK_SIZE // len(emoji.encode("utf-8"))) - 1
        content = emoji * count
        assert len(content.encode("utf-8")) < CHUNK_SIZE

        written = save_file(tmp_path_file, content)
        with open(tmp_path_file, "rb") as f:
            assert f.read() == content.encode("utf-8")
        assert written == len(content.encode("utf-8"))

    def test_save_over_64kb_with_emoji(self, tmp_path_file):
        # Each emoji is 4 bytes in UTF-8; create content just over 64 KB.
        emoji = "\U0001F600"  # 😀
        count = (CHUNK_SIZE // len(emoji.encode("utf-8"))) + 100
        content = emoji * count
        assert len(content.encode("utf-8")) > CHUNK_SIZE

        written = save_file(tmp_path_file, content)
        with open(tmp_path_file, "rb") as f:
            assert f.read() == content.encode("utf-8")
        assert written == len(content.encode("utf-8"))

    def test_save_over_64kb_mixed_ascii_multibyte(self, tmp_path_file):
        # Mix ASCII text with CJK characters exceeding 64 KB.
        block = "Hello 世界! " * 100  # mix of 1-byte and 3-byte chars
        repeat = (CHUNK_SIZE // len(block.encode("utf-8"))) + 10
        content = block * repeat
        assert len(content.encode("utf-8")) > CHUNK_SIZE

        written = save_file(tmp_path_file, content)
        with open(tmp_path_file, "rb") as f:
            assert f.read() == content.encode("utf-8")
        assert written == len(content.encode("utf-8"))

    def test_multibyte_at_chunk_boundary(self, tmp_path_file):
        # Place a multibyte character exactly at the 64 KB boundary.
        # Fill with ASCII up to CHUNK_SIZE - 1 byte, then add a 4-byte emoji.
        padding = "A" * (CHUNK_SIZE - 1)
        emoji = "\U0001F600"  # 4-byte character
        content = padding + emoji + "tail"

        encoded = content.encode("utf-8")
        assert len(encoded) > CHUNK_SIZE

        written = save_file(tmp_path_file, content)
        with open(tmp_path_file, "rb") as f:
            saved = f.read()
        assert saved == encoded
        assert written == len(encoded)

    def test_save_well_over_64kb_emoji(self, tmp_path_file):
        # ~256 KB of emoji content (multiple chunks).
        emoji = "\U0001F4A9"  # 💩 4-byte emoji
        count = (CHUNK_SIZE * 4) // len(emoji.encode("utf-8"))
        content = emoji * count
        assert len(content.encode("utf-8")) > CHUNK_SIZE * 3

        written = save_file(tmp_path_file, content)
        with open(tmp_path_file, "rb") as f:
            assert f.read() == content.encode("utf-8")
        assert written == len(content.encode("utf-8"))


class TestSaveFileEdgeCases:
    """Error handling and edge cases."""

    def test_type_error_on_bytes(self, tmp_path_file):
        with pytest.raises(TypeError):
            save_file(tmp_path_file, b"bytes input")

    def test_creates_parent_directories(self, tmp_path):
        nested = str(tmp_path / "a" / "b" / "c" / "file.txt")
        save_file(nested, "nested content")
        with open(nested, "rb") as f:
            assert f.read() == b"nested content"

    def test_overwrites_existing_file(self, tmp_path_file):
        save_file(tmp_path_file, "first")
        save_file(tmp_path_file, "second")
        with open(tmp_path_file, "rb") as f:
            assert f.read() == b"second"
