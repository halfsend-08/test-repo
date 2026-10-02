"""Tests for file_io module.

Covers boundary conditions around the 64KB buffer size with
multibyte UTF-8 characters, ASCII-only text, and mixed content.
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from file_io import BUFFER_SIZE, read_file, save_file


@pytest.fixture
def tmp_path_file(tmp_path):
    """Return a callable that gives a fresh temp file path."""

    def _make(name="output.txt"):
        return str(tmp_path / name)

    return _make


class TestSaveAndReadRoundTrip:
    """Verify files round-trip correctly at various sizes and encodings."""

    def test_small_ascii_file(self, tmp_path_file):
        path = tmp_path_file()
        content = "hello world"
        save_file(path, content)
        assert read_file(path) == content

    def test_multibyte_under_64kb(self, tmp_path_file):
        """63KB of multibyte UTF-8 text should save successfully."""
        path = tmp_path_file()
        # Each emoji is 4 bytes in UTF-8
        emoji = "\U0001F600"  # 😀
        target_bytes = 63 * 1024
        repeat_count = target_bytes // len(emoji.encode("utf-8"))
        content = emoji * repeat_count
        assert len(content.encode("utf-8")) < BUFFER_SIZE

        save_file(path, content)
        assert read_file(path) == content

    def test_multibyte_over_64kb(self, tmp_path_file):
        """65KB of multibyte UTF-8 text should save without crash."""
        path = tmp_path_file()
        emoji = "\U0001F600"
        target_bytes = 65 * 1024
        repeat_count = target_bytes // len(emoji.encode("utf-8"))
        content = emoji * repeat_count
        assert len(content.encode("utf-8")) > BUFFER_SIZE

        save_file(path, content)
        assert read_file(path) == content

    def test_ascii_over_64kb(self, tmp_path_file):
        """65KB of ASCII text should save successfully."""
        path = tmp_path_file()
        content = "A" * (65 * 1024)
        assert len(content.encode("utf-8")) > BUFFER_SIZE

        save_file(path, content)
        assert read_file(path) == content

    def test_mixed_content_at_64kb_boundary(self, tmp_path_file):
        """Exactly 64KB of mixed ASCII and multibyte text."""
        path = tmp_path_file()
        emoji = "\U0001F4A9"  # 💩 — 4 bytes
        # Build content: ASCII padding + emojis to hit exactly 64KB
        emoji_count = 1000
        emoji_bytes = emoji_count * len(emoji.encode("utf-8"))
        ascii_pad = BUFFER_SIZE - emoji_bytes
        content = "x" * ascii_pad + emoji * emoji_count
        assert len(content.encode("utf-8")) == BUFFER_SIZE

        save_file(path, content)
        assert read_file(path) == content

    def test_cjk_characters_over_64kb(self, tmp_path_file):
        """65KB of CJK characters (3 bytes each in UTF-8)."""
        path = tmp_path_file()
        cjk_char = "世"  # 世 — 3 bytes
        target_bytes = 65 * 1024
        repeat_count = target_bytes // len(cjk_char.encode("utf-8"))
        content = cjk_char * repeat_count
        assert len(content.encode("utf-8")) > BUFFER_SIZE

        save_file(path, content)
        assert read_file(path) == content

    def test_empty_file(self, tmp_path_file):
        path = tmp_path_file()
        save_file(path, "")
        assert read_file(path) == ""

    def test_creates_parent_directories(self, tmp_path_file):
        path = tmp_path_file("subdir/nested/output.txt")
        content = "nested file content"
        save_file(path, content)
        assert read_file(path) == content
