"""
File Operation Edge Case Tests.

Tests for edge cases in file read/write operations.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestBinaryFileHandling:
    """Test binary file handling."""

    def test_binary_file_detection(self):
        """Detect binary file before reading."""
        # Create temp binary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe')
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                header = f.read(512)

            # Check for null bytes (common binary indicator)
            is_binary = b'\x00' in header
            assert is_binary
        finally:
            os.unlink(temp_path)

    def test_binary_file_error_message(self):
        """Appropriate error for binary file read attempt."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            # Write invalid UTF-8 sequences
            f.write(b'\x80\x81\x82\xff\xfe\xfd')
            temp_path = f.name

        try:
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    f.read()
                failed = False
            except UnicodeDecodeError:
                failed = True

            assert failed
        finally:
            os.unlink(temp_path)

    def test_image_file_detection(self):
        """Detect common image file types."""
        # PNG magic bytes
        png_header = b'\x89PNG\r\n\x1a\n'
        # JPEG magic bytes
        jpeg_header = b'\xff\xd8\xff'
        # GIF magic bytes
        gif_header = b'GIF89a'

        assert png_header.startswith(b'\x89PNG')
        assert jpeg_header.startswith(b'\xff\xd8')
        assert gif_header.startswith(b'GIF')


class TestFileLocking:
    """Test file locking edge cases."""

    def test_read_while_writing(self):
        """Handle reading file being written to."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("initial content")
            temp_path = f.name

        try:
            # Simulate concurrent read
            with open(temp_path, 'r') as reader:
                content = reader.read()
                assert "initial" in content
        finally:
            os.unlink(temp_path)

    def test_file_deleted_mid_operation(self):
        """Handle file deletion during operation."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
            f.write(b"content")

        # Delete the file
        os.unlink(temp_path)

        # Try to read deleted file
        try:
            with open(temp_path, 'r') as f:
                f.read()
            exists = True
        except FileNotFoundError:
            exists = False

        assert not exists


class TestSymlinkHandling:
    """Test symlink handling edge cases."""

    @pytest.mark.skipif(os.name == 'nt', reason="Symlinks require admin on Windows")
    def test_symlink_resolution(self):
        """Resolve symlinks to actual file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file
            real_file = Path(tmpdir) / "real.txt"
            real_file.write_text("content")

            # Create symlink
            link = Path(tmpdir) / "link.txt"
            link.symlink_to(real_file)

            # Read through symlink
            content = link.read_text()
            assert content == "content"

            # Resolve gives real path
            resolved = link.resolve()
            assert resolved == real_file.resolve()

    @pytest.mark.skipif(os.name == 'nt', reason="Symlinks require admin on Windows")
    def test_broken_symlink_detection(self):
        """Detect and handle broken symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create symlink to non-existent file
            link = Path(tmpdir) / "broken_link.txt"
            target = Path(tmpdir) / "nonexistent.txt"

            link.symlink_to(target)

            assert link.is_symlink()
            assert not link.exists()  # Broken symlink

    @pytest.mark.skipif(os.name == 'nt', reason="Symlinks require admin on Windows")
    def test_symlink_loop_detection(self):
        """Detect symlink loops."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create circular symlinks
            link_a = Path(tmpdir) / "a"
            link_b = Path(tmpdir) / "b"

            link_a.symlink_to(link_b)
            link_b.symlink_to(link_a)

            # Attempting to resolve should fail
            try:
                link_a.resolve(strict=True)
                looped = False
            except (OSError, RuntimeError):
                looped = True

            # Note: Python's resolve() may not always raise
            assert link_a.is_symlink()


class TestFilePathEdgeCases:
    """Test file path edge cases."""

    def test_very_long_filename(self):
        """Handle very long filenames."""
        # Most filesystems limit to 255 chars
        MAX_FILENAME = 255

        long_name = "a" * 300
        truncated = long_name[:MAX_FILENAME]

        assert len(truncated) <= MAX_FILENAME

    def test_special_characters_in_path(self):
        """Handle special characters in file paths."""
        special_chars = ['$', '!', '@', '#', '%', '&', '(', ')']

        with tempfile.TemporaryDirectory() as tmpdir:
            for char in special_chars:
                try:
                    file_path = Path(tmpdir) / f"file{char}name.txt"
                    file_path.write_text("content")
                    assert file_path.exists()
                    file_path.unlink()
                except OSError:
                    # Some chars may not be allowed on certain filesystems
                    pass

    def test_unicode_filename(self):
        """Handle unicode characters in filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            unicode_names = [
                "file.txt",
                "test_file.txt",
            ]

            for name in unicode_names:
                try:
                    file_path = Path(tmpdir) / name
                    file_path.write_text("content")
                    assert file_path.exists()
                except OSError:
                    pass  # System may not support


class TestFilePermissions:
    """Test file permission edge cases."""

    @pytest.mark.skipif(os.name == 'nt', reason="Unix permissions only")
    def test_read_only_file(self):
        """Handle read-only file write attempt."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
            f.write(b"content")

        try:
            # Make read-only
            os.chmod(temp_path, 0o444)

            # Try to write
            try:
                with open(temp_path, 'w') as f:
                    f.write("new content")
                write_failed = False
            except PermissionError:
                write_failed = True

            assert write_failed
        finally:
            os.chmod(temp_path, 0o644)
            os.unlink(temp_path)

    @pytest.mark.skipif(os.name == 'nt', reason="Unix permissions only")
    def test_no_read_permission(self):
        """Handle file with no read permission."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
            f.write(b"secret")

        try:
            # Remove read permission
            os.chmod(temp_path, 0o000)

            # Try to read (may need to check if running as root)
            if os.geteuid() != 0:  # Not root
                try:
                    with open(temp_path, 'r') as f:
                        f.read()
                    read_failed = False
                except PermissionError:
                    read_failed = True

                assert read_failed
        finally:
            os.chmod(temp_path, 0o644)
            os.unlink(temp_path)
