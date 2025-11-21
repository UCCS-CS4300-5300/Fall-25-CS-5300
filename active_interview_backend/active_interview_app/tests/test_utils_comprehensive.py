"""
Comprehensive tests for utility functions

This module provides extensive coverage of all utility functions.
"""

import os
import tempfile
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from unittest.mock import patch, MagicMock, mock_open
from active_interview_app.utils import handle_uploaded_file
from io import BytesIO


class HandleUploadedFileTest(TestCase):
    """Test handle_uploaded_file utility function"""

    def setUp(self):
        """Set up temporary directory for uploads"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files"""
        try:
            # Clean up temporary files
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(self.temp_dir)
        except Exception:
            pass

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_success(self):
        """Test successful file upload"""
        # Create a simple uploaded file
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile(
            "test.txt",
            file_content,
            content_type="text/plain"
        )

        # Handle the upload
        file_path = handle_uploaded_file(uploaded_file)

        # Verify file was created
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith("test.txt"))

        # Verify content
        with open(file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, file_content)

        # Cleanup
        os.remove(file_path)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_creates_directory(self):
        """Test that handle_uploaded_file creates uploads directory if it doesn't exist"""
        # Ensure uploads directory doesn't exist
        uploads_dir = os.path.join(tempfile.gettempdir(), "uploads")
        if os.path.exists(uploads_dir):
            for file in os.listdir(uploads_dir):
                os.remove(os.path.join(uploads_dir, file))
            os.rmdir(uploads_dir)

        uploaded_file = SimpleUploadedFile(
            "test_create_dir.txt",
            b"Content",
            content_type="text/plain"
        )

        file_path = handle_uploaded_file(uploaded_file)

        # Verify directory was created
        self.assertTrue(os.path.exists(uploads_dir))
        self.assertTrue(os.path.exists(file_path))

        # Cleanup
        os.remove(file_path)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_binary_content(self):
        """Test handling binary file uploads"""
        # Create binary content (simulating PDF, image, etc.)
        binary_content = bytes([i % 256 for i in range(1000)])
        uploaded_file = SimpleUploadedFile(
            "binary_file.bin",
            binary_content,
            content_type="application/octet-stream"
        )

        file_path = handle_uploaded_file(uploaded_file)

        # Verify binary content is preserved
        with open(file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, binary_content)

        # Cleanup
        os.remove(file_path)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_large_file(self):
        """Test handling large file uploads in chunks"""
        # Create a larger file
        large_content = b"Large content " * 10000
        uploaded_file = SimpleUploadedFile(
            "large_file.txt",
            large_content,
            content_type="text/plain"
        )

        file_path = handle_uploaded_file(uploaded_file)

        # Verify file was saved correctly
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(len(content), len(large_content))

        # Cleanup
        os.remove(file_path)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_special_characters_in_name(self):
        """Test handling files with special characters in name"""
        uploaded_file = SimpleUploadedFile(
            "test file with spaces & special.txt",
            b"Content",
            content_type="text/plain"
        )

        file_path = handle_uploaded_file(uploaded_file)

        # Verify file was created
        self.assertTrue(os.path.exists(file_path))

        # Cleanup
        os.remove(file_path)

    @override_settings(MEDIA_ROOT='/invalid/readonly/path')
    @patch('active_interview_app.utils.os.makedirs')
    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    def test_handle_uploaded_file_permission_error(self, mock_open, mock_makedirs):
        """Test handling PermissionError during file save"""
        uploaded_file = SimpleUploadedFile(
            "test.txt",
            b"Content",
            content_type="text/plain"
        )

        with self.assertRaises(ValueError) as context:
            handle_uploaded_file(uploaded_file)

        self.assertIn("error saving the file", str(context.exception))

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('builtins.open', side_effect=OSError("Disk full"))
    def test_handle_uploaded_file_unexpected_error(self, mock_open):
        """Test handling unexpected errors during file save"""
        uploaded_file = SimpleUploadedFile(
            "test.txt",
            b"Content",
            content_type="text/plain"
        )

        with self.assertRaises(ValueError) as context:
            handle_uploaded_file(uploaded_file)

        self.assertIn("unexpected error", str(context.exception))

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_empty_file(self):
        """Test handling empty file upload"""
        uploaded_file = SimpleUploadedFile(
            "empty.txt",
            b"",
            content_type="text/plain"
        )

        file_path = handle_uploaded_file(uploaded_file)

        # Verify file was created even if empty
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b"")

        # Cleanup
        os.remove(file_path)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_multiple_files_same_name(self):
        """Test handling multiple files with the same name (overwrites)"""
        file1 = SimpleUploadedFile("same_name.txt", b"First content")
        file2 = SimpleUploadedFile("same_name.txt", b"Second content")

        # Upload first file
        path1 = handle_uploaded_file(file1)

        # Upload second file with same name
        path2 = handle_uploaded_file(file2)

        # Paths should be the same
        self.assertEqual(path1, path2)

        # Content should be from second file (overwritten)
        with open(path2, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b"Second content")

        # Cleanup
        os.remove(path2)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_returns_correct_path(self):
        """Test that handle_uploaded_file returns correct file path"""
        uploaded_file = SimpleUploadedFile(
            "path_test.txt",
            b"Content",
            content_type="text/plain"
        )

        file_path = handle_uploaded_file(uploaded_file)

        # Verify path structure
        self.assertIn("uploads", file_path)
        self.assertIn("path_test.txt", file_path)
        self.assertTrue(file_path.startswith(tempfile.gettempdir()))

        # Cleanup
        os.remove(file_path)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_pdf(self):
        """Test handling PDF file upload"""
        # Simulate PDF header
        pdf_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\nTest PDF content"
        uploaded_file = SimpleUploadedFile(
            "document.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        file_path = handle_uploaded_file(uploaded_file)

        # Verify file was saved
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith(".pdf"))

        # Verify content
        with open(file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, pdf_content)

        # Cleanup
        os.remove(file_path)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_handle_uploaded_file_unicode_content(self):
        """Test handling files with unicode content"""
        unicode_content = "Hello 世界 🌍".encode('utf-8')
        uploaded_file = SimpleUploadedFile(
            "unicode.txt",
            unicode_content,
            content_type="text/plain"
        )

        file_path = handle_uploaded_file(uploaded_file)

        # Verify unicode content is preserved
        with open(file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, unicode_content)

        # Cleanup
        os.remove(file_path)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('active_interview_app.utils.logging.getLogger')
    def test_handle_uploaded_file_logs_permission_error(self, mock_logger):
        """Test that PermissionError is logged"""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            uploaded_file = SimpleUploadedFile("test.txt", b"Content")

            with self.assertRaises(ValueError):
                handle_uploaded_file(uploaded_file)

            # Verify logging was called
            mock_log.error.assert_called()
            error_message = mock_log.error.call_args[0][0]
            self.assertIn("Permission error", error_message)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('active_interview_app.utils.logging.getLogger')
    def test_handle_uploaded_file_logs_unexpected_error(self, mock_logger):
        """Test that unexpected errors are logged"""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        with patch('builtins.open', side_effect=OSError("Disk error")):
            uploaded_file = SimpleUploadedFile("test.txt", b"Content")

            with self.assertRaises(ValueError):
                handle_uploaded_file(uploaded_file)

            # Verify logging was called
            mock_log.error.assert_called()
            error_message = mock_log.error.call_args[0][0]
            self.assertIn("Unexpected error", error_message)
