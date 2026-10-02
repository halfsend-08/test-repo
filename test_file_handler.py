"""Tests for file_handler module.

Covers the regression case from issue #1914: saving files larger than
64KB that contain UTF-8 multibyte characters (emoji, CJK) must not
crash or corrupt data.
"""

import os
import tempfile

from file_handler import BUFFER_SIZE, read_file, save_file


class TestSaveFileUTF8:
    """Test file saving with multibyte UTF-8 content."""

    def _roundtrip(self, content):
        """Save content to a temp file and read it back."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp:
            path = tmp.name
        try:
            save_file(path, content)
            result = read_file(path)
            assert result == content
            # Verify byte-level integrity
            with open(path, "rb") as f:
                raw = f.read()
            assert raw == content.encode("utf-8")
        finally:
            os.unlink(path)

    def test_save_small_ascii(self):
        """Small ASCII file saves correctly."""
        self._roundtrip("Hello, world!\n" * 100)

    def test_save_small_emoji(self):
        """Small file with emoji saves correctly."""
        self._roundtrip("Hello 🌍🎉🚀\n" * 100)

    def test_save_under_64kb_with_emoji(self):
        """File just under 64KB with emoji content saves correctly."""
        # Each emoji is 4 bytes in UTF-8; build content just under 64KB
        emoji_line = "🎉🌍🚀🎊🌈" * 20 + "\n"  # ~401 bytes per line
        lines_needed = (BUFFER_SIZE - 100) // len(emoji_line.encode("utf-8"))
        content = emoji_line * lines_needed
        assert len(content.encode("utf-8")) < BUFFER_SIZE
        self._roundtrip(content)

    def test_save_over_64kb_with_emoji(self):
        """Regression test: file over 64KB with emoji must save correctly."""
        emoji_line = "🎉🌍🚀🎊🌈" * 20 + "\n"
        lines_needed = (BUFFER_SIZE + 10000) // len(emoji_line.encode("utf-8"))
        content = emoji_line * lines_needed
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        self._roundtrip(content)

    def test_save_over_64kb_with_cjk(self):
        """File over 64KB with CJK characters saves correctly."""
        # CJK characters are 3 bytes each in UTF-8
        cjk_line = "漢字テスト文字列確認用" * 10 + "\n"
        lines_needed = (BUFFER_SIZE + 10000) // len(cjk_line.encode("utf-8"))
        content = cjk_line * lines_needed
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        self._roundtrip(content)

    def test_save_over_64kb_mixed_ascii_and_cjk(self):
        """File over 64KB with mixed ASCII and CJK saves correctly."""
        mixed_line = "Hello 世界! Test テスト Data データ\n"
        lines_needed = (BUFFER_SIZE + 10000) // len(mixed_line.encode("utf-8"))
        content = mixed_line * lines_needed
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        self._roundtrip(content)

    def test_multibyte_char_at_buffer_boundary(self):
        """Edge case: multibyte character spanning the 64KB boundary."""
        # Fill with ASCII up to just before the boundary, then add emoji
        padding = "A" * (BUFFER_SIZE - 2)
        # The emoji (4 bytes) will span the 64KB boundary
        content = padding + "🎉" + "B" * 1000
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        self._roundtrip(content)

    def test_empty_content(self):
        """Empty string saves as empty file."""
        self._roundtrip("")

    def test_type_error_on_non_string(self):
        """Passing non-string content raises TypeError."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            path = tmp.name
        try:
            try:
                save_file(path, 12345)
                assert False, "Expected TypeError"
            except TypeError:
                pass
        finally:
            os.unlink(path)
