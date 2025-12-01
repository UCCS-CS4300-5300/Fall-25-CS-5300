import os
import tempfile
import shutil
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from ..utils import handle_uploaded_file


def create_mock_openai_response(content, model='gpt-4o', prompt_tokens=100, completion_tokens=50):
    """
    Create a properly configured mock OpenAI response for testing.

    This helper ensures that mock responses have all the attributes needed
    for token tracking (model, usage.prompt_tokens, usage.completion_tokens).

    Args:
        content: The response content (string)
        model: Model name (default 'gpt-4o')
        prompt_tokens: Number of prompt tokens (default 100)
        completion_tokens: Number of completion tokens (default 50)

    Returns:
        MagicMock configured with proper attributes for token tracking

    Example:
        mock_response = create_mock_openai_response("Hello world!")
        mock_client.chat.completions.create.return_value = mock_response
    """
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    mock_response.model = model

    # Configure usage tracking
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = prompt_tokens
    mock_usage.completion_tokens = completion_tokens
    mock_usage.total_tokens = prompt_tokens + completion_tokens
    mock_response.usage = mock_usage

    return mock_response


class TestFileUploadUtils(TestCase):
    def setUp(self):
        # Create a temporary directory for test uploads
        self.test_upload_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_upload_dir)

    # @override_settings(MEDIA_ROOT=property(lambda s: s.test_upload_dir))
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
