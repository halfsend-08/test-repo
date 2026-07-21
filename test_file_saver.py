"""Tests for file_saver module.

Verifies correct handling of UTF-8 multibyte characters in files
at and above the 64KB buffer boundary.
"""

import os
import tempfile

import pytest

from file_saver import save_file


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestSaveFile:
    """Tests for save_file covering the UTF-8 buffer overflow fix."""

    def test_save_ascii_under_64kb(self, tmp_dir):
        """ASCII content under 64KB saves correctly."""
        path = os.path.join(tmp_dir, "small_ascii.txt")
        content = "a" * 60000
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_ascii_over_64kb(self, tmp_dir):
        """ASCII content over 64KB saves correctly."""
        path = os.path.join(tmp_dir, "large_ascii.txt")
        content = "a" * 70000
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_multibyte_under_64kb(self, tmp_dir):
        """Multibyte UTF-8 content under 64KB saves correctly."""
        path = os.path.join(tmp_dir, "small_utf8.txt")
        # Each emoji is 4 bytes; 10000 chars = 40KB
        content = "\U0001f600" * 10000
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_multibyte_over_64kb(self, tmp_dir):
        """Multibyte UTF-8 content over 64KB saves correctly.

        This is the primary regression test for issue #392.
        Characters are 4 bytes each, so 20000 chars = 80KB of
        encoded data, exceeding the 64KB buffer boundary.
        """
        path = os.path.join(tmp_dir, "large_utf8.txt")
        content = "\U0001f600" * 20000  # 80KB encoded
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_mixed_content_over_64kb(self, tmp_dir):
        """Mixed ASCII and multibyte content over 64KB saves correctly."""
        path = os.path.join(tmp_dir, "mixed.txt")
        # Mix of ASCII and emoji to cross 64KB boundary
        content = ("Hello \U0001f600 World \U0001f4a9 " * 5000)
        assert len(content.encode("utf-8")) > 65536
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_cjk_over_64kb(self, tmp_dir):
        """CJK characters (3 bytes each) over 64KB save correctly."""
        path = os.path.join(tmp_dir, "cjk.txt")
        # CJK characters are 3 bytes each; 25000 chars ~ 75KB
        content = "世界你好" * 6250  # 75KB
        assert len(content.encode("utf-8")) > 65536
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_char_count_under_but_bytes_over_64kb(self, tmp_dir):
        """File where char count < 64K but byte count > 64KB.

        This catches the specific bug where buffer was allocated
        based on character count rather than byte count.
        """
        path = os.path.join(tmp_dir, "bytes_over.txt")
        # 20000 chars * 4 bytes = 80KB, but only 20000 chars
        content = "\U0001f680" * 20000
        assert len(content) < 65536  # char count under 64K
        assert len(content.encode("utf-8")) > 65536  # byte count over 64K
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_empty_content(self, tmp_dir):
        """Empty string saves as empty file."""
        path = os.path.join(tmp_dir, "empty.txt")
        save_file(path, "")
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == ""

    def test_save_rejects_non_string(self, tmp_dir):
        """Non-string content raises TypeError."""
        path = os.path.join(tmp_dir, "bad.txt")
        with pytest.raises(TypeError, match="content must be a string"):
            save_file(path, b"bytes are not strings")
