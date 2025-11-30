"""
Comprehensive tests for views to achieve >80% coverage.
Tests all view functions and classes including edge cases.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
import json

from active_interview_app.models import (
    UploadedResume, UploadedJobListing, Chat
)
from active_interview_app import views


class ViewsHelperFunctionsTest(TestCase):
    """Test helper functions in views"""

    @patch('active_interview_app.openai_utils.settings.OPENAI_API_KEY', '')
    def test_ai_available_no_api_key(self):
        """Test ai_available returns False when no API key"""
        from active_interview_app import openai_utils
        # Reset the cached client
        openai_utils._openai_client = None
        result = openai_utils.ai_available()
        self.assertFalse(result)

    @patch('active_interview_app.openai_utils.settings.OPENAI_API_KEY', 'test-key')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_ai_available_with_api_key(self, mock_openai):
        """Test ai_available returns True with valid API key"""
        from active_interview_app import openai_utils
        # Reset the global client
        openai_utils._openai_client = None

        result = openai_utils.ai_available()
        self.assertTrue(result)

    def test_ai_unavailable_json(self):
        """Test _ai_unavailable_json returns correct response"""
        response = views._ai_unavailable_json()

        self.assertEqual(response.status_code, 503)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('AI features are disabled', data['error'])

    @patch('active_interview_app.openai_utils.settings.OPENAI_API_KEY', 'test-key')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_get_openai_client_success(self, mock_openai):
        """Test get_openai_client successful initialization"""
        from active_interview_app import openai_utils
        # Reset global client
        openai_utils._openai_client = None

        client = openai_utils.get_openai_client()
        self.assertIsNotNone(client)
        mock_openai.assert_called_once_with(api_key='test-key')

    @patch('active_interview_app.openai_utils.settings.OPENAI_API_KEY', '')
    def test_get_openai_client_no_key(self):
        """Test get_openai_client raises error without API key"""
        from active_interview_app import openai_utils
        # Reset global client
        openai_utils._openai_client = None

        with self.assertRaises(ValueError) as context:
            openai_utils.get_openai_client()

        self.assertIn('No OpenAI API key available', str(context.exception))


class StaticViewsTest(TestCase):
    """Test static page views"""

    def test_index_view(self):
        """Test index page"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_aboutus_view(self):
        """Test about us page"""
        response = self.client.get(reverse('about-us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about-us.html')

    def test_features_view(self):
        """Test features page"""
        response = self.client.get(reverse('features'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'features.html')

    def test_results_view(self):
        """Test results page"""
        response = self.client.get(reverse('results'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'results.html')


class AuthenticationViewsTest(TestCase):
    """Test authentication views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        Group.objects.get_or_create(name='average_role')

    def test_register_view_get(self):
        """Test register page GET request"""
        response = self.client.get(reverse('register_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
        self.assertIn('form', response.context)

    def test_register_view_post_valid(self):
        """Test register page POST with valid data"""
        response = self.client.post(reverse('register_page'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!'
        })

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

        # User should be created
        user = User.objects.get(username='newuser')
        self.assertIsNotNone(user)

        # User should be in average_role group
        self.assertTrue(user.groups.filter(name='average_role').exists())

    def test_register_view_post_invalid(self):
        """Test register page POST with invalid data"""
        response = self.client.post(reverse('register_page'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'pass',  # Too weak
            'password2': 'pass'
        })

        # Should stay on register page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

        # User should not be created
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_loggedin_view_requires_login(self):
        """Test loggedin view requires authentication"""
        response = self.client.get(reverse('loggedin'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_loggedin_view_authenticated(self):
        """Test loggedin view with authenticated user"""
        user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.client.force_login(user)

        response = self.client.get(reverse('loggedin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loggedinindex.html')


class ProfileViewTest(TestCase):
    """Test profile view"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        # Create test data
        fake_resume = SimpleUploadedFile("resume.pdf", b"resume")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume
        )

        fake_job = SimpleUploadedFile("job.txt", b"job")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job content',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

    def test_profile_view_authenticated(self):
        """Test profile view with authenticated user"""
        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertIn('resumes', response.context)
        self.assertIn('job_listings', response.context)

        # Check data is filtered by user
        self.assertIn(self.resume, response.context['resumes'])
        self.assertIn(self.job, response.context['job_listings'])

    def test_profile_view_requires_login(self):
        """Test profile view requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('profile'))

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class ChatListViewTest(TestCase):
    """Test chat list view"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            'chatuser', 'chat@example.com', 'pass')
        self.other_user = User.objects.create_user(
            'other', 'other@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_job = SimpleUploadedFile("job.txt", b"job")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Content',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

        # Create chat for this user
        self.user_chat = Chat.objects.create(
            owner=self.user,
            title='My Chat',
            difficulty=5,
            messages=[],
            job_listing=self.job
        )

        # Create chat for other user
        self.other_chat = Chat.objects.create(
            owner=self.other_user,
            title='Other Chat',
            difficulty=5,
            messages=[],
            job_listing=self.job
        )

    def test_chat_list_shows_only_user_chats(self):
        """Test chat list shows only current user's chats"""
        response = self.client.get(reverse('chat-list'))

        self.assertEqual(response.status_code, 200)
        # Check for template using normalized path (works on Windows and Unix)
        template_names = [t.name for t in response.templates]
        self.assertTrue(
            any('chat-list.html' in name for name in template_names),
            f"Expected chat-list.html template, got: {template_names}"
        )

        owner_chats = response.context['owner_chats']
        self.assertIn(self.user_chat, owner_chats)
        self.assertNotIn(self.other_chat, owner_chats)

    def test_chat_list_requires_login(self):
        """Test chat list requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('chat-list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class CreateChatViewTest(TestCase):
    """Test CreateChat view"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            'chatcreator', 'create@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_job = SimpleUploadedFile("job.txt", b"job")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Software Engineer',
            content='Job description',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

        fake_resume = SimpleUploadedFile("resume.pdf", b"resume")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume
        )

    def test_create_chat_get(self):
        """Test CreateChat GET request"""
        response = self.client.get(reverse('chat-create'))

        self.assertEqual(response.status_code, 200)
        template_names = [t.name for t in response.templates]
        self.assertTrue(
            any('chat-create.html' in name for name in template_names),
            f"Expected chat-create.html template, got: {template_names}"
        )
        self.assertIn('form', response.context)
        self.assertIn('owner_chats', response.context)

    @patch('active_interview_app.views.ai_available', return_value=False)
    def test_create_chat_post_ai_disabled(self, mockai_available):
        """Test CreateChat POST when AI is disabled"""
        self.client.post(reverse('chat-create'), {
            'create': 'true',
            'title': 'Test Chat',
            'type': Chat.GENERAL,
            'difficulty': 5,
            'listing_choice': self.job.id,
            'resume_choice': self.resume.id
        })  # noqa: F841

        # Should still create chat but with empty AI message
        self.assertEqual(Chat.objects.filter(title='Test Chat').count(), 1)

    def test_create_chat_requires_login(self):
        """Test CreateChat requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('chat-create'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class EditChatViewTest(TestCase):
    """Test EditChat view"""

    def setUp(self):
        """Set up test data"""
        # Create average_role group (required by signals)
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            'editor', 'edit@example.com', 'pass')
        self.other_user = User.objects.create_user(
            'other', 'other@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_job = SimpleUploadedFile("job.txt", b"job")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            content='Content',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Original Title',
            difficulty=5,
            messages=[
                {"role": "system", "content": "System prompt with difficulty <<5>>"}],
            job_listing=self.job
        )

        self.other_chat = Chat.objects.create(
            owner=self.other_user,
            title='Other Chat',
            difficulty=5,
            messages=[
                {"role": "system", "content": "System prompt with difficulty <<5>>"}],
            job_listing=self.job
        )

    def test_edit_chat_get_owner(self):
        """Test EditChat GET as owner"""
        response = self.client.get(reverse('chat-edit', args=[self.chat.id]))

        self.assertEqual(response.status_code, 200)
        template_names = [t.name for t in response.templates]
        self.assertTrue(
            any('chat-edit.html' in name for name in template_names),
            f"Expected chat-edit.html template, got: {template_names}"
        )
        self.assertIn('form', response.context)
        self.assertIn('chat', response.context)

    def test_edit_chat_get_not_owner(self):
        """Test EditChat GET as non-owner returns 403"""
        response = self.client.get(
            reverse('chat-edit', args=[self.other_chat.id]))

        self.assertEqual(response.status_code, 403)

    def test_edit_chat_post_valid(self):
        """Test EditChat POST with valid data"""
        response = self.client.post(
            reverse('chat-edit', args=[self.chat.id]),
            {
                'update': 'true',
                'title': 'Updated Title',
                'difficulty': 8
            }
        )

        # Should redirect to chat view
        self.assertEqual(response.status_code, 302)

        # Chat should be updated
        self.chat.refresh_from_db()
        self.assertEqual(self.chat.title, 'Updated Title')
        self.assertEqual(self.chat.difficulty, 8)


class DeleteChatViewTest(TestCase):
    """Test DeleteChat view"""

    def setUp(self):
        """Set up test data"""
        # Create average_role group (required by signals)
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            'deleter', 'delete@example.com', 'pass')
        self.other_user = User.objects.create_user(
            'other', 'other@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_job = SimpleUploadedFile("job.txt", b"job")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            content='Content',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='To Delete',
            difficulty=5,
            messages=[],
            job_listing=self.job
        )

        self.other_chat = Chat.objects.create(
            owner=self.other_user,
            title='Other Chat',
            difficulty=5,
            messages=[],
            job_listing=self.job
        )

    def test_delete_chat_post_owner(self):
        """Test DeleteChat POST as owner"""
        chat_id = self.chat.id
        response = self.client.post(reverse('chat-delete', args=[chat_id]), {
            'delete': 'true'
        })

        # Should redirect to chat list
        self.assertEqual(response.status_code, 302)
        self.assertIn('/chat/', response.url)

        # Chat should be deleted
        self.assertFalse(Chat.objects.filter(id=chat_id).exists())

    def test_delete_chat_post_not_owner(self):
        """Test DeleteChat POST as non-owner returns 403"""
        response = self.client.post(
            reverse('chat-delete', args=[self.other_chat.id]))

        self.assertEqual(response.status_code, 403)

        # Chat should still exist
        self.assertTrue(Chat.objects.filter(id=self.other_chat.id).exists())


class DocumentViewsTest(TestCase):
    """Test document-related views"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            'docuser', 'doc@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_resume = SimpleUploadedFile("resume.pdf", b"resume")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume
        )

        fake_job = SimpleUploadedFile("job.txt", b"job")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

    def test_resume_detail_view(self):
        """Test resume detail view"""
        response = self.client.get(
            reverse('resume_detail', args=[self.resume.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/resume_detail.html')
        self.assertIn('resume', response.context)
        self.assertEqual(response.context['resume'], self.resume)

    def test_job_posting_detail_view(self):
        """Test job posting detail view"""
        response = self.client.get(
            reverse('job_posting_detail', args=[self.job.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/job_posting_detail.html')
        self.assertIn('job', response.context)
        self.assertEqual(response.context['job'], self.job)

    def test_delete_resume_post(self):
        """Test delete resume"""
        resume_id = self.resume.id
        response = self.client.post(reverse('delete_resume', args=[resume_id]))

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Resume should be deleted
        self.assertFalse(UploadedResume.objects.filter(id=resume_id).exists())

    def test_delete_job_post(self):
        """Test delete job posting"""
        job_id = self.job.id
        response = self.client.post(reverse('delete_job', args=[job_id]))

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Job should be deleted
        self.assertFalse(UploadedJobListing.objects.filter(id=job_id).exists())

    def test_edit_resume_get(self):
        """Test edit resume GET"""
        response = self.client.get(
            reverse('edit_resume', args=[self.resume.id]))

        self.assertEqual(response.status_code, 200)
        template_names = [t.name for t in response.templates]
        self.assertTrue(
            any('edit_document.html' in name for name in template_names),
            f"Expected edit_document.html template, got: {template_names}"
        )
        self.assertIn('form', response.context)

    def test_edit_resume_post(self):
        """Test edit resume POST"""
        response = self.client.post(reverse('edit_resume', args=[self.resume.id]), {
            'title': 'Updated Resume Title',
            'content': 'Updated resume content'
        })

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Resume should be updated
        self.resume.refresh_from_db()
        self.assertEqual(self.resume.title, 'Updated Resume Title')
        self.assertEqual(self.resume.content, 'Updated resume content')

    def test_edit_job_posting_get(self):
        """Test edit job posting GET"""
        response = self.client.get(
            reverse('edit_job_posting', args=[self.job.id]))

        self.assertEqual(response.status_code, 200)
        template_names = [t.name for t in response.templates]
        self.assertTrue(
            any('edit_job_posting.html' in name for name in template_names),
            f"Expected edit_job_posting.html template, got: {template_names}"
        )
        self.assertIn('form', response.context)

    def test_edit_job_posting_post(self):
        """Test edit job posting POST"""
        response = self.client.post(reverse('edit_job_posting', args=[self.job.id]), {
            'title': 'Updated Job Title',
            'content': 'Updated job content'
        })

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Job should be updated
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, 'Updated Job Title')
        self.assertEqual(self.job.content, 'Updated job content')


class DocumentListViewTest(TestCase):
    """Test DocumentList view"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            'listuser', 'list@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

    def test_document_list_view(self):
        """Test document list view"""
        response = self.client.get(reverse('document-list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')

    def test_document_list_requires_login(self):
        """Test document list requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('document-list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
