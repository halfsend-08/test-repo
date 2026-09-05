"""Tests for file_saver module.

Verifies correct handling of UTF-8 multibyte content at and around the
64KB buffer boundary, matching the test cases from the triage analysis.
"""

import os
import tempfile

from file_saver import BUFFER_SIZE, calculate_buffer_size, save_file


def _make_multibyte_text(target_bytes: int) -> str:
    """Generate a string of emoji characters whose UTF-8 encoding is
    approximately target_bytes in size. Each emoji is 4 bytes in UTF-8."""
    # U+1F600 (😀) is 4 bytes in UTF-8
    char = "\U0001F600"
    char_bytes = len(char.encode("utf-8"))  # 4
    count = target_bytes // char_bytes
    return char * count


def _make_ascii_text(target_bytes: int) -> str:
    """Generate ASCII text of exactly target_bytes."""
    return "A" * target_bytes


class TestCalculateBufferSize:
    def test_ascii_byte_length_equals_char_count(self):
        text = "hello"
        assert calculate_buffer_size(text) == len(text) == 5

    def test_multibyte_byte_length_exceeds_char_count(self):
        text = "\U0001F600"  # 😀 — 1 character, 4 bytes in UTF-8
        assert len(text) == 1
        assert calculate_buffer_size(text) == 4

    def test_cjk_characters(self):
        text = "世界"  # 世界 — 2 characters, 6 bytes in UTF-8
        assert len(text) == 2
        assert calculate_buffer_size(text) == 6

    def test_empty_string(self):
        assert calculate_buffer_size("") == 0

    def test_mixed_ascii_and_multibyte(self):
        text = "hello \U0001F600"  # 6 ASCII bytes + 4 emoji bytes = 10
        assert calculate_buffer_size(text) == 10


class TestSaveFile:
    def test_save_small_ascii_file(self, tmp_path):
        filepath = str(tmp_path / "small_ascii.txt")
        content = "Hello, world!"
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_small_multibyte_file(self, tmp_path):
        filepath = str(tmp_path / "small_multibyte.txt")
        content = "\U0001F600\U0001F601\U0001F602"
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_63kb_multibyte_succeeds(self, tmp_path):
        """Save 63KB of multibyte UTF-8 text — expect success."""
        filepath = str(tmp_path / "63kb_multibyte.txt")
        content = _make_multibyte_text(63 * 1024)
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_65kb_multibyte_succeeds(self, tmp_path):
        """Save 65KB of multibyte UTF-8 text — expect success, no crash.

        This is the primary regression test: the old code used character
        count for buffer allocation, causing a buffer overrun when
        multibyte characters pushed the byte count past 64KB.
        """
        filepath = str(tmp_path / "65kb_multibyte.txt")
        content = _make_multibyte_text(65 * 1024)
        byte_len = len(content.encode("utf-8"))
        assert byte_len >= 65 * 1024  # confirm we exceed the boundary
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_save_65kb_ascii_succeeds(self, tmp_path):
        """Save 65KB of ASCII text — expect success (control case)."""
        filepath = str(tmp_path / "65kb_ascii.txt")
        content = _make_ascii_text(65 * 1024)
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_saved_content_matches_input(self, tmp_path):
        """Verify saved file content matches input for mixed content."""
        filepath = str(tmp_path / "mixed.txt")
        content = "ASCII prefix " + _make_multibyte_text(70 * 1024) + " ASCII suffix"
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_buffer_size_constant(self):
        """Verify buffer size is 64KB."""
        assert BUFFER_SIZE == 64 * 1024

    def test_atomic_write_no_partial_file_on_error(self, tmp_path):
        """If the directory is read-only, the file should not be created."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        filepath = str(readonly_dir / "test.txt")
        # Make the directory read-only to force a write failure
        os.chmod(str(readonly_dir), 0o444)
        try:
            save_file(filepath, "content")
            assert False, "Expected OSError"
        except OSError:
            pass
        finally:
            os.chmod(str(readonly_dir), 0o755)
        assert not os.path.exists(filepath)
