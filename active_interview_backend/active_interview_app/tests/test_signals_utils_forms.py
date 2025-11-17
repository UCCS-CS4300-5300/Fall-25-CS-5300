"""
Comprehensive tests for signals, utils, forms, and serializers to increase coverage.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from unittest.mock import patch, mock_open, MagicMock
import os
import tempfile

from active_interview_app.models import (
    UserProfile, UploadedResume, UploadedJobListing, Chat
)
from active_interview_app.forms import (
    CreateUserForm, DocumentEditForm, JobPostingEditForm,
    CreateChatForm, EditChatForm, UploadFileForm
)
from active_interview_app.serializers import (
    UploadedResumeSerializer, UploadedJobListingSerializer
)
from active_interview_app.signals import ensure_average_role_group
from active_interview_app.utils import handle_uploaded_file


# ============================================================================
# SIGNALS TESTS
# ============================================================================

class SignalsTest(TestCase):
    """Test signal handlers"""

    def test_ensure_average_role_group_creates_group(self):
        """Test that ensure_average_role_group signal creates group"""
        # Delete the group if it exists
        Group.objects.filter(name='average_role').delete()

        # Call the signal handler
        ensure_average_role_group(sender=None)

        # Verify group was created
        self.assertTrue(Group.objects.filter(name='average_role').exists())

    def test_ensure_average_role_group_idempotent(self):
        """Test that calling ensure_average_role_group multiple times is safe"""
        # Ensure group exists
        Group.objects.get_or_create(name='average_role')
        initial_count = Group.objects.filter(name='average_role').count()

        # Call signal handler again
        ensure_average_role_group(sender=None)

        # Should still be only one group
        self.assertEqual(
            Group.objects.filter(name='average_role').count(),
            initial_count
        )

    def test_user_profile_created_on_user_save(self):
        """Test that UserProfile is created when User is saved"""
        # Create a new user
        user = User.objects.create_user(
            username='signaltest',
            email='signal@test.com',
            password='testpass123'
        )

        # Verify UserProfile was created
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.auth_provider, 'local')


# ============================================================================
# UTILS TESTS
# ============================================================================

class UtilsTest(TestCase):
    """Test utility functions"""

    def setUp(self):
        """Set up test environment"""
        self.test_content = b"Test file content"
        self.test_file = SimpleUploadedFile(
            "test_file.txt",
            self.test_content,
            content_type="text/plain"
        )

    @patch('active_interview_app.utils.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_handle_uploaded_file_success(self, mock_makedirs, mock_file_open):
        """Test successful file upload handling"""
        result = handle_uploaded_file(self.test_file)

        # Verify directory creation was called
        mock_makedirs.assert_called_once()

        # Verify file was opened for writing
        mock_file_open.assert_called_once()

        # Verify return path
        self.assertIn('uploads', result)
        self.assertIn('test_file.txt', result)

    @patch('os.makedirs', side_effect=PermissionError("Permission denied"))
    def test_handle_uploaded_file_permission_error(self, mock_makedirs):
        """Test handling of permission error"""
        with self.assertRaises(ValueError) as context:
            handle_uploaded_file(self.test_file)

        self.assertIn("error saving the file", str(context.exception))

    @patch('os.makedirs', side_effect=Exception("Unexpected error"))
    def test_handle_uploaded_file_unexpected_error(self, mock_makedirs):
        """Test handling of unexpected error"""
        with self.assertRaises(ValueError) as context:
            handle_uploaded_file(self.test_file)

        self.assertIn("unexpected error occurred", str(context.exception))


# ============================================================================
# FORMS TESTS
# ============================================================================

class CreateUserFormTest(TestCase):
    """Test CreateUserForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        form = CreateUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_password_mismatch(self):
        """Test form with mismatched passwords"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!'
        }
        form = CreateUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_invalid_weak_password(self):
        """Test form with weak password"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': '123',
            'password2': '123'
        }
        form = CreateUserForm(data=form_data)
        self.assertFalse(form.is_valid())


class DocumentEditFormTest(TestCase):
    """Test DocumentEditForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'title': 'My Resume',
            'content': 'Resume content here'
        }
        form = DocumentEditForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_fields(self):
        """Test that form has correct fields"""
        form = DocumentEditForm()
        self.assertIn('title', form.fields)
        self.assertIn('content', form.fields)
        self.assertEqual(len(form.fields), 2)


class JobPostingEditFormTest(TestCase):
    """Test JobPostingEditForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'title': 'Software Engineer',
            'content': 'Job description here'
        }
        form = JobPostingEditForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_empty_content(self):
        """Test form with empty content"""
        form_data = {
            'title': 'Software Engineer',
            'content': ''
        }
        form = JobPostingEditForm(data=form_data)
        # Content is required
        self.assertFalse(form.is_valid())


class CreateChatFormTest(TestCase):
    """Test CreateChatForm"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='chatuser',
            email='chat@example.com',
            password='testpass123'
        )

        fake_file = SimpleUploadedFile("job.txt", b"content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job content',
            filepath='/fake',
            filename='job.txt',
            file=fake_file
        )

        fake_resume = SimpleUploadedFile("resume.pdf", b"resume")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume
        )

    def test_form_with_user(self):
        """Test that form initializes correctly with user"""
        form = CreateChatForm(user=self.user)

        # Verify querysets are filtered by user
        self.assertEqual(
            list(form.fields['listing_choice'].queryset),
            list(UploadedJobListing.objects.filter(user=self.user))
        )
        self.assertEqual(
            list(form.fields['resume_choice'].queryset),
            list(UploadedResume.objects.filter(user=self.user))
        )

    def test_form_without_user(self):
        """Test that form works without user (empty querysets)"""
        form = CreateChatForm()

        # Querysets should be empty
        self.assertEqual(form.fields['listing_choice'].queryset.count(), 0)
        self.assertEqual(form.fields['resume_choice'].queryset.count(), 0)

    def test_valid_form_data(self):
        """Test form with valid data"""
        form_data = {
            'title': 'Interview Chat',
            'type': Chat.GENERAL,
            'difficulty': 5,
            'listing_choice': self.job_listing.id,
            'resume_choice': self.resume.id
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_resume_optional(self):
        """Test that resume_choice is optional"""
        form_data = {
            'title': 'Interview Chat',
            'type': Chat.GENERAL,
            'difficulty': 5,
            'listing_choice': self.job_listing.id,
            # No resume_choice
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_difficulty_validation(self):
        """Test difficulty field validation"""
        # Test difficulty too low
        form_data = {
            'title': 'Interview Chat',
            'type': Chat.GENERAL,
            'difficulty': 0,  # Below min
            'listing_choice': self.job_listing.id
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

        # Test difficulty too high
        form_data['difficulty'] = 11  # Above max
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())


class EditChatFormTest(TestCase):
    """Test EditChatForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'title': 'Updated Chat Title',
            'difficulty': 7
        }
        form = EditChatForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_difficulty_bounds(self):
        """Test difficulty validation"""
        # Min boundary
        form_data = {'title': 'Test', 'difficulty': 1}
        form = EditChatForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Max boundary
        form_data = {'title': 'Test', 'difficulty': 10}
        form = EditChatForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Below min
        form_data = {'title': 'Test', 'difficulty': 0}
        form = EditChatForm(data=form_data)
        self.assertFalse(form.is_valid())


class UploadFileFormTest(TestCase):
    """Test UploadFileForm"""

    def test_valid_form_with_file(self):
        """Test form with valid file"""
        fake_file = SimpleUploadedFile("test.pdf", b"content")
        form_data = {'title': 'My Resume'}
        form_files = {'file': fake_file}

        form = UploadFileForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())

    def test_clean_file_method(self):
        """Test clean_file method"""
        fake_file = SimpleUploadedFile("test.txt", b"content")
        form_data = {'title': 'Test Doc'}
        form_files = {'file': fake_file}

        form = UploadFileForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())

        # Verify file is cleaned and returned
        cleaned_file = form.cleaned_data.get('file')
        self.assertIsNotNone(cleaned_file)
        self.assertEqual(cleaned_file.name, 'test.txt')


# ============================================================================
# SERIALIZERS TESTS
# ============================================================================

class UploadedResumeSerializerTest(TestCase):
    """Test UploadedResumeSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='serializeruser',
            email='serializer@example.com',
            password='testpass123'
        )

        fake_file = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains expected fields"""
        serializer = UploadedResumeSerializer(instance=self.resume)

        data = serializer.data
        self.assertEqual(set(data.keys()), {
                         'id', 'file', 'user', 'uploaded_at', 'title'})

    def test_serializer_data(self):
        """Test serializer data content"""
        serializer = UploadedResumeSerializer(instance=self.resume)

        data = serializer.data
        self.assertEqual(data['id'], self.resume.id)
        self.assertEqual(data['user'], self.user.id)
        self.assertIn('uploaded_at', data)


class UploadedJobListingSerializerTest(TestCase):
    """Test UploadedJobListingSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='jobuser',
            email='job@example.com',
            password='testpass123'
        )

        fake_file = SimpleUploadedFile("job.txt", b"job content")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Software Engineer',
            content='Job description',
            filepath='/fake',
            filename='job.txt',
            file=fake_file
        )

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains expected fields"""
        serializer = UploadedJobListingSerializer(instance=self.job)

        data = serializer.data
        self.assertEqual(
            set(data.keys()),
            {
                'id', 'user', 'filename', 'content', 'created_at', 'title', 'file',
                # NEW: Parsed data fields (Issues #21, #51, #52, #53)
                'required_skills', 'seniority_level', 'requirements',
                'recommended_template', 'recommended_template_name',
                'parsing_status', 'parsing_error', 'parsed_at'
            }
        )

    def test_serializer_data(self):
        """Test serializer data content"""
        serializer = UploadedJobListingSerializer(instance=self.job)

        data = serializer.data
        self.assertEqual(data['id'], self.job.id)
        self.assertEqual(data['user'], self.user.id)
        self.assertEqual(data['filename'], 'job.txt')
        self.assertEqual(data['content'], 'Job description')
        self.assertIn('created_at', data)
