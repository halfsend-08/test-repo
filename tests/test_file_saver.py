"""Tests for the file_saver module.

Covers UTF-8 multibyte handling around the buffer boundary to prevent
regressions on the segfault reported in issue #33.
"""

import os
import tempfile

import pytest

from src.file_saver import BUFFER_SIZE, _find_safe_split, save_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# _find_safe_split unit tests
# ---------------------------------------------------------------------------

class TestFindSafeSplit:
    """Verify that _find_safe_split never tears a multibyte character."""

    def test_ascii_only(self):
        data = b"hello world"
        assert _find_safe_split(data, 5) == 5

    def test_limit_beyond_data(self):
        data = b"short"
        assert _find_safe_split(data, 100) == len(data)

    def test_split_before_2byte_char(self):
        # U+00E9 (é) is 2 bytes: 0xC3 0xA9
        data = b"aaa" + "é".encode("utf-8")  # 3 + 2 = 5 bytes
        # Splitting at index 4 would land on continuation byte 0xA9
        assert _find_safe_split(data, 4) == 3

    def test_split_before_3byte_char(self):
        # U+4E16 (世) is 3 bytes: 0xE4 0xB8 0x96
        data = b"ab" + "世".encode("utf-8")  # 2 + 3 = 5 bytes
        # Splitting at index 3 lands on continuation byte 0xB8
        assert _find_safe_split(data, 3) == 2

    def test_split_before_4byte_char(self):
        # U+1F600 (😀) is 4 bytes: 0xF0 0x9F 0x98 0x80
        data = b"x" + "😀".encode("utf-8")  # 1 + 4 = 5 bytes
        # Splitting at index 2, 3, or 4 should back up to index 1
        assert _find_safe_split(data, 2) == 1
        assert _find_safe_split(data, 3) == 1
        assert _find_safe_split(data, 4) == 1

    def test_exact_char_boundary(self):
        # Split right after a complete character
        data = "é".encode("utf-8") + b"abc"  # 2 + 3 = 5
        assert _find_safe_split(data, 2) == 2


# ---------------------------------------------------------------------------
# save_file integration tests
# ---------------------------------------------------------------------------

class TestSaveFile:
    """End-to-end tests for save_file with various sizes and encodings."""

    def test_small_ascii_file(self, tmp_path):
        path = str(tmp_path / "small.txt")
        content = "Hello, world!"
        save_file(content, path)
        assert _read_bytes(path) == content.encode("utf-8")

    def test_file_under_64kb_with_emoji(self, tmp_path):
        path = str(tmp_path / "under64.txt")
        # ~60KB of emoji-laden text
        content = ("Hello 😀🌍🎉 " * 2000)[:60000]
        save_file(content, path)
        assert _read_bytes(path) == content.encode("utf-8")

    def test_file_over_64kb_with_emoji(self, tmp_path):
        """Core regression test for issue #33: >64KB + multibyte chars."""
        path = str(tmp_path / "over64.txt")
        # Build content that is well over 64KB when encoded
        content = ("Test 😀🌍🎉 data " * 5000)
        encoded = content.encode("utf-8")
        assert len(encoded) > BUFFER_SIZE, "test content must exceed 64KB"
        save_file(content, path)
        assert _read_bytes(path) == encoded

    def test_emoji_straddles_buffer_boundary(self, tmp_path):
        """Emoji (4 bytes) placed exactly at the 64KB boundary."""
        path = str(tmp_path / "straddle.txt")
        # Fill with ASCII up to 2 bytes before the boundary, then a 4-byte emoji
        padding = "x" * (BUFFER_SIZE - 2)
        content = padding + "😀" + "y" * 100
        encoded = content.encode("utf-8")
        # The emoji bytes span positions 65534..65537, straddling the 65536 boundary
        save_file(content, path)
        assert _read_bytes(path) == encoded

    def test_cjk_over_64kb(self, tmp_path):
        """CJK characters (3 bytes each) in a file exceeding 64KB."""
        path = str(tmp_path / "cjk.txt")
        content = "世界你好" * 6000  # 4 chars * 3 bytes * 6000 = 72000 bytes
        encoded = content.encode("utf-8")
        assert len(encoded) > BUFFER_SIZE
        save_file(content, path)
        assert _read_bytes(path) == encoded

    def test_ascii_over_64kb(self, tmp_path):
        """ASCII-only file over 64KB — regression guard."""
        path = str(tmp_path / "ascii_large.txt")
        content = "a" * (BUFFER_SIZE + 1000)
        save_file(content, path)
        assert _read_bytes(path) == content.encode("utf-8")

    def test_small_buffer_with_multibyte(self, tmp_path):
        """Use a tiny buffer to force many splits across multibyte chars."""
        path = str(tmp_path / "tiny_buf.txt")
        content = "Hello 😀 World 🌍 Test 🎉" * 10
        save_file(content, path, buffer_size=16)
        assert _read_bytes(path) == content.encode("utf-8")

    def test_empty_content(self, tmp_path):
        path = str(tmp_path / "empty.txt")
        save_file("", path)
        assert _read_bytes(path) == b""
