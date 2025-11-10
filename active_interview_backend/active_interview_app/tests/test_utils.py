import os
import tempfile
import shutil
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from unittest.mock import patch
from ..utils import handle_uploaded_file


class TestFileUploadUtils(TestCase):
    def setUp(self):
        # Create a temporary directory for test uploads
        self.test_upload_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_upload_dir)

    #@override_settings(MEDIA_ROOT=property(lambda s: s.test_upload_dir))
    def test_successful_file_upload(self):
        """Test that files are uploaded and saved correctly"""
        # Create a test file
        content = b"test file content"
        test_file = SimpleUploadedFile("test.txt", content)

        # Handle the upload
        file_path = handle_uploaded_file(test_file)

        # Verify file exists and content is correct
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'rb') as f:
            saved_content = f.read()
        self.assertEqual(saved_content, content)

    @patch('builtins.open')
    def test_permission_error_handling(self, mock_open):
        """Test handling of permission errors during file upload"""
        # Mock open to raise PermissionError
        mock_open.side_effect = PermissionError("Permission denied")

        test_file = SimpleUploadedFile("test.txt", b"test content")

        # Check if appropriate error is raised
        with self.assertRaisesRegex(ValueError, "There was an error saving the file"):
            handle_uploaded_file(test_file)

    @patch('os.makedirs')
    def test_generic_error_handling(self, mock_makedirs):
        """Test handling of generic errors during file upload"""
        # Mock makedirs to raise OSError
        mock_makedirs.side_effect = OSError("Generic error")

        test_file = SimpleUploadedFile("test.txt", b"test content")

        # Check if appropriate error is raised
        with self.assertRaisesRegex(ValueError, "An unexpected error occurred"):
            handle_uploaded_file(test_file)