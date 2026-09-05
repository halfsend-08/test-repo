"""Tests for file_saver module.

Verifies correct handling of UTF-8 multibyte content at and around the
64KB buffer boundary, matching the test cases from the triage analysis.
"""

import os
import shutil
import tempfile
import unittest

from file_saver import BUFFER_SIZE, save_file


def _make_multibyte_text(target_bytes: int) -> str:
    """Generate a string of emoji characters whose UTF-8 encoding is
    approximately target_bytes in size. Each emoji is 4 bytes in UTF-8."""
    char = "\U0001F600"
    char_bytes = len(char.encode("utf-8"))  # 4
    count = target_bytes // char_bytes
    return char * count


def _make_ascii_text(target_bytes: int) -> str:
    """Generate ASCII text of exactly target_bytes."""
    return "A" * target_bytes


class TestSaveFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_small_ascii_file(self):
        filepath = os.path.join(self.tmpdir, "small_ascii.txt")
        content = "Hello, world!"
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_save_small_multibyte_file(self):
        filepath = os.path.join(self.tmpdir, "small_multibyte.txt")
        content = "\U0001F600\U0001F601\U0001F602"
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_save_63kb_multibyte_succeeds(self):
        """Save 63KB of multibyte UTF-8 text — expect success."""
        filepath = os.path.join(self.tmpdir, "63kb_multibyte.txt")
        content = _make_multibyte_text(63 * 1024)
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_save_exact_64kb_multibyte_succeeds(self):
        """Save exactly 64KB of multibyte UTF-8 text — boundary case."""
        filepath = os.path.join(self.tmpdir, "64kb_multibyte.txt")
        content = _make_multibyte_text(BUFFER_SIZE)
        byte_len = len(content.encode("utf-8"))
        self.assertEqual(byte_len, BUFFER_SIZE)
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_save_empty_content(self):
        """Save empty string — edge case for chunked write loop."""
        filepath = os.path.join(self.tmpdir, "empty.txt")
        save_file(filepath, "")
        with open(filepath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "")

    def test_save_65kb_multibyte_succeeds(self):
        """Save 65KB of multibyte UTF-8 text — expect success, no crash.

        This is the primary regression test: the old code used character
        count for buffer allocation, causing a buffer overrun when
        multibyte characters pushed the byte count past 64KB.
        """
        filepath = os.path.join(self.tmpdir, "65kb_multibyte.txt")
        content = _make_multibyte_text(65 * 1024)
        byte_len = len(content.encode("utf-8"))
        self.assertGreaterEqual(byte_len, 65 * 1024)
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_save_65kb_ascii_succeeds(self):
        """Save 65KB of ASCII text — expect success (control case)."""
        filepath = os.path.join(self.tmpdir, "65kb_ascii.txt")
        content = _make_ascii_text(65 * 1024)
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_saved_content_matches_input(self):
        """Verify saved file content matches input for mixed content."""
        filepath = os.path.join(self.tmpdir, "mixed.txt")
        content = "ASCII prefix " + _make_multibyte_text(70 * 1024) + " ASCII suffix"
        save_file(filepath, content)
        with open(filepath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_buffer_size_constant(self):
        """Verify buffer size is 64KB."""
        self.assertEqual(BUFFER_SIZE, 64 * 1024)

    def test_write_error_raises_oserror(self):
        """Verify that write failures propagate as OSError."""
        readonly_dir = os.path.join(self.tmpdir, "readonly")
        os.makedirs(readonly_dir)
        filepath = os.path.join(readonly_dir, "test.txt")
        os.chmod(readonly_dir, 0o444)
        try:
            with self.assertRaises(OSError):
                save_file(filepath, "content")
        finally:
            os.chmod(readonly_dir, 0o755)


if __name__ == "__main__":
    unittest.main()
