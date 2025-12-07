"""
Tests to improve coverage for views.py - targeting specific uncovered lines
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import json

from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing,
    Chat
)
from active_interview_app.openai_utils import (
    get_openai_client,
    ai_available
)
from active_interview_app.views import _ai_unavailable_json
from .test_credentials import TEST_PASSWORD


class OpenAIClientTest(TestCase):
    """Test OpenAI client initialization and helper functions"""

    @patch('active_interview_app.openai_utils.settings')
    def test_get_openai_client_no_api_key(self, mock_settings):
        """Test get_openai_client when API key is not set"""
        import active_interview_app.openai_utils as openai_utils
        openai_utils._openai_client = None

        mock_settings.OPENAI_API_KEY = None

        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn("No OpenAI API key available", str(context.exception))

    @patch('active_interview_app.openai_utils.OpenAI')
    @patch('active_interview_app.openai_utils.settings')
    def test_get_openai_client_initialization_error(
            self, mock_settings, mock_openai):
        """Test get_openai_client when OpenAI initialization fails"""
        import active_interview_app.openai_utils as openai_utils
        openai_utils._openai_client = None

        mock_settings.OPENAI_API_KEY = 'test-key'
        mock_openai.side_effect = Exception("OpenAI init failed")

        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn("Failed to initialize OpenAI client",
                      str(context.exception))

    @patch('active_interview_app.openai_utils.get_client_and_model')
    def testai_available_returns_true(self, mock_get_client_and_model):
        """Test ai_available when client can be initialized"""
        mock_client = MagicMock()
        # get_client_and_model returns (client, model, tier_info)
        mock_get_client_and_model.return_value = (mock_client, "gpt-4o", {"tier": "premium"})

        self.assertTrue(ai_available())

    @patch('active_interview_app.openai_utils.get_openai_client')
    def testai_available_returns_false_on_error(self, mock_get_client):
        """Test ai_available when client cannot be initialized"""
        mock_get_client.side_effect = ValueError("No API key")

        self.assertFalse(ai_available())

    def test_ai_unavailable_json_response(self):
        """Test _ai_unavailable_json returns proper JSON error"""
        response = _ai_unavailable_json()

        self.assertEqual(response.status_code, 503)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(
            data['error'], 'AI features are disabled on this server.')


class IndexAndStaticViewsTest(TestCase):
    """Test basic static views"""

    def setUp(self):
        self.client = Client()

    def test_index_view(self):
        """Test index page renders"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_features_view(self):
        """Test features page renders"""
        response = self.client.get(reverse('features'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'features.html')


class FileUploadEdgeCasesTest(TestCase):
    """Test edge cases in file upload functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    @patch('active_interview_app.views.filetype.guess')
    def test_upload_file_invalid_filetype(self, mock_filetype):
        """Test uploading a file with invalid type"""
        # Mock filetype to return unsupported type
        mock_file_type = MagicMock()
        mock_file_type.extension = 'exe'
        mock_filetype.return_value = mock_file_type

        file_content = b'fake executable'
        file = SimpleUploadedFile(
            "test.exe",
            file_content,
            content_type="application/x-msdownload"
        )

        response = self.client.post(reverse('upload_file'), {
            'file': file,
            'title': 'Test File'
        })

        self.assertEqual(response.status_code, 302)
        # Should not create resume for invalid file type
        self.assertFalse(UploadedResume.objects.filter(
            title='Test File').exists())

    @patch('active_interview_app.views.filetype.guess')
    def test_upload_file_none_filetype(self, mock_filetype):
        """Test uploading file when filetype.guess returns None"""
        mock_filetype.return_value = None

        file_content = b'unknown file'
        file = SimpleUploadedFile(
            "test.unknown",
            file_content,
            content_type="application/octet-stream"
        )

        response = self.client.post(reverse('upload_file'), {
            'file': file,
            'title': 'Test Unknown'
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(UploadedResume.objects.filter(
            title='Test Unknown').exists())

    @patch('active_interview_app.views.filetype.guess')
    @patch('active_interview_app.views.pymupdf4llm.to_markdown')
    def test_upload_pdf_file_success(self, mock_to_markdown, mock_filetype):
        """Test successfully uploading a PDF file"""
        # Mock filetype to return PDF
        mock_file_type = MagicMock()
        mock_file_type.extension = 'pdf'
        mock_filetype.return_value = mock_file_type

        # Mock PDF parsing
        mock_to_markdown.return_value = '# Resume Content'

        file_content = b'%PDF-1.4 fake pdf content'
        file = SimpleUploadedFile(
            "resume.pdf",
            file_content,
            content_type="application/pdf"
        )

        response = self.client.post(reverse('upload_file'), {
            'file': file,
            'title': 'My PDF Resume'
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(UploadedResume.objects.filter(
            title='My PDF Resume').exists())
        resume = UploadedResume.objects.get(title='My PDF Resume')
        self.assertEqual(resume.content, '# Resume Content')

    @patch('active_interview_app.views.filetype.guess')
    @patch('active_interview_app.views.pymupdf4llm.to_markdown')
    def test_upload_file_processing_error(
            self, mock_to_markdown, mock_filetype):
        """Test upload when file processing raises exception"""
        mock_file_type = MagicMock()
        mock_file_type.extension = 'pdf'
        mock_filetype.return_value = mock_file_type

        # Simulate processing error
        mock_to_markdown.side_effect = Exception("PDF parsing failed")

        file_content = b'%PDF-1.4 corrupted'
        file = SimpleUploadedFile(
            "bad.pdf",
            file_content,
            content_type="application/pdf"
        )

        response = self.client.post(reverse('upload_file'), {
            'file': file,
            'title': 'Bad PDF'
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(UploadedResume.objects.filter(
            title='Bad PDF').exists())

    def test_upload_file_invalid_form(self):
        """Test upload with invalid form data"""
        # Missing required file field
        response = self.client.post(reverse('upload_file'), {
            'title': 'No File'
        })

        self.assertEqual(response.status_code, 302)


class DocumentEditViewsTest(TestCase):
    """Test document editing views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_file = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Original Title',
            content='Original content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

    def test_edit_resume_get(self):
        """Test GET request to edit_resume"""
        response = self.client.get(
            reverse('edit_resume', kwargs={'resume_id': self.resume.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/edit_document.html')

    def test_edit_resume_post(self):
        """Test POST request to edit_resume"""
        response = self.client.post(
            reverse('edit_resume', kwargs={'resume_id': self.resume.id}),
            {
                'title': 'Updated Title',
                'content': 'Updated content'
            }
        )
        self.assertEqual(response.status_code, 302)

        self.resume.refresh_from_db()
        self.assertEqual(self.resume.title, 'Updated Title')
        self.assertEqual(self.resume.content, 'Updated content')


class JobPostingEditTest(TestCase):
    """Test job posting editing"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_file = SimpleUploadedFile("job.txt", b"job content")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Original Job',
            content='Original description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_file
        )

    def test_edit_job_posting_get(self):
        """Test GET request to edit_job_posting"""
        response = self.client.get(
            reverse('edit_job_posting', kwargs={'job_id': self.job.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/edit_job_posting.html')

    def test_edit_job_posting_post(self):
        """Test POST request to edit_job_posting"""
        response = self.client.post(
            reverse('edit_job_posting', kwargs={'job_id': self.job.id}),
            {
                'title': 'Updated Job',
                'content': 'Updated description'
            }
        )
        self.assertEqual(response.status_code, 302)

        self.job.refresh_from_db()
        self.assertEqual(self.job.title, 'Updated Job')
        self.assertEqual(self.job.content, 'Updated description')


class UploadedJobListingViewTest(TestCase):
    """Test UploadedJobListingView for pasted text"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_upload_job_listing_view_success(self):
        """Test successful pasted text job listing creation"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'This is a job description\nWith multiple lines',
            'title': 'Software Engineer'
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            UploadedJobListing.objects.filter(
                title='Software Engineer').exists()
        )

        job = UploadedJobListing.objects.get(title='Software Engineer')
        self.assertIn('job description', job.content)


class DocumentListViewTest(TestCase):
    """Test DocumentList view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_document_list_get(self):
        """Test GET request to DocumentList"""
        response = self.client.get(reverse('document-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')


class JobListingAPITest(TestCase):
    """Test JobListingList API view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.force_login(self.user)

    def test_job_listing_list_get(self):
        """Test GET request to JobListingList API"""
        fake_file = SimpleUploadedFile("job.txt", b"job content")
        UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_file
        )

        response = self.client.get(reverse('pasted_text_list'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Job')

    def test_job_listing_list_post_invalid(self):
        """Test POST with invalid data to JobListingList API"""
        response = self.client.post(
            reverse('pasted_text_list'),
            data=json.dumps({'invalid': 'data'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class ChatViewUserPassesTestTest(TestCase):
    """Test UserPassesTestMixin for chat views"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password=TEST_PASSWORD
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password=TEST_PASSWORD
        )

        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user1,
            title='Test Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job_file
        )

        self.chat = Chat.objects.create(
            owner=self.user1,
            title='User1 Chat',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

    def test_chat_view_unauthorized_user(self):
        """Test that user2 cannot access user1's chat"""
        self.client.login(username='user2', password=TEST_PASSWORD)

        response = self.client.get(
            reverse('chat-view', kwargs={'chat_id': self.chat.id})
        )
        # Should get 403 Forbidden or redirect
        self.assertIn(response.status_code, [302, 403])

    def test_edit_chat_unauthorized_user(self):
        """Test that user2 cannot edit user1's chat"""
        self.client.login(username='user2', password=TEST_PASSWORD)

        response = self.client.get(
            reverse('chat-edit', kwargs={'chat_id': self.chat.id})
        )
        self.assertIn(response.status_code, [302, 403])

    def test_delete_chat_unauthorized_user(self):
        """Test that user2 cannot delete user1's chat"""
        self.client.login(username='user2', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('chat-delete', kwargs={'chat_id': self.chat.id}),
            {'delete': 'true'}
        )
        self.assertIn(response.status_code, [302, 403])
        # Chat should still exist
        self.assertTrue(Chat.objects.filter(id=self.chat.id).exists())


class ProfileViewTest(TestCase):
    """Test profile view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_profile_view(self):
        """Test profile page loads with user's documents"""
        fake_resume = SimpleUploadedFile("resume.pdf", b"resume content")
        fake_job = SimpleUploadedFile("job.txt", b"job content")

        UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume
        )

        UploadedJobListing.objects.create(
            user=self.user,
            title='My Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job
        )

        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertIn('resumes', response.context)
        self.assertIn('job_listings', response.context)
        self.assertEqual(len(response.context['resumes']), 1)
        self.assertEqual(len(response.context['job_listings']), 1)


class DeleteResumeTest(TestCase):
    """Test delete_resume view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_file = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

    def test_delete_resume_post(self):
        """Test deleting resume via POST"""
        response = self.client.post(
            reverse('delete_resume', kwargs={'resume_id': self.resume.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(UploadedResume.objects.filter(
            id=self.resume.id).exists())

    def test_delete_resume_get_redirect(self):
        """Test GET request to delete_resume redirects without deleting"""
        response = self.client.get(
            reverse('delete_resume', kwargs={'resume_id': self.resume.id})
        )

        self.assertEqual(response.status_code, 302)
        # Resume should still exist (only POST deletes)
        self.assertTrue(UploadedResume.objects.filter(
            id=self.resume.id).exists())


class DeleteJobTest(TestCase):
    """Test delete_job view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_file = SimpleUploadedFile("job.txt", b"job content")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='My Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_file
        )

    def test_delete_job_post(self):
        """Test deleting job via POST"""
        response = self.client.post(
            reverse('delete_job', kwargs={'job_id': self.job.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(UploadedJobListing.objects.filter(
            id=self.job.id).exists())

    def test_delete_job_get_redirect(self):
        """Test GET request to delete_job redirects"""
        response = self.client.get(
            reverse('delete_job', kwargs={'job_id': self.job.id})
        )

        self.assertEqual(response.status_code, 302)


class ResumeDetailTest(TestCase):
    """Test resume_detail view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_file = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

    def test_resume_detail_view(self):
        """Test resume detail page renders"""
        response = self.client.get(
            reverse('resume_detail', kwargs={'resume_id': self.resume.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/resume_detail.html')
        self.assertEqual(response.context['resume'], self.resume)


class JobPostingDetailTest(TestCase):
    """Test job_posting_detail view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_file = SimpleUploadedFile("job.txt", b"job content")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='My Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_file
        )

    def test_job_posting_detail_view(self):
        """Test job posting detail page renders"""
        response = self.client.get(
            reverse('job_posting_detail', kwargs={'job_id': self.job.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/job_posting_detail.html')
        self.assertEqual(response.context['job'], self.job)


class LoggedInViewTest(TestCase):
    """Test loggedin view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )

    def test_loggedin_view(self):
        """Test loggedin page renders for authenticated user"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(reverse('loggedin'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loggedinindex.html')


class AboutUsViewTest(TestCase):
    """Test aboutus view"""

    def test_aboutus_view(self):
        """Test about us page renders"""
        client = Client()
        response = client.get(reverse('aboutus'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about-us.html')


class ResultsViewTest(TestCase):
    """Test results view"""

    def test_results_view(self):
        """Test results page renders"""
        client = Client()
        response = client.get(reverse('results'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'results.html')


class UploadedResumeAPIViewTest(TestCase):
    """Test UploadedResumeView API"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.force_login(self.user)

    def test_uploaded_resume_get(self):
        """Test GET request to UploadedResumeView"""
        fake_file = SimpleUploadedFile("resume.pdf", b"resume content")
        UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

        response = self.client.get(reverse('files_list'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Resume')

    def test_uploaded_resume_post_invalid(self):
        """Test POST with invalid data to UploadedResumeView"""
        response = self.client.post(
            reverse('files_list'),
            data=json.dumps({'invalid': 'data'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class ChatListViewTest(TestCase):
    """Test chat_list view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job_file
        )

    def test_chat_list_view(self):
        """Test chat list page renders"""
        Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.get(reverse('chat-list'))
        self.assertEqual(response.status_code, 200)
        template_names = [t.name for t in response.templates]
        self.assertTrue(
            any('chat-list.html' in name for name in template_names))
        self.assertEqual(len(response.context['owner_chats']), 1)


class RestartChatTest(TestCase):
    """Test RestartChat view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job_file
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[
                {"role": "system", "content": "test"},
                {"role": "assistant", "content": "greeting"},
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "response"}
            ]
        )

    def test_restart_chat(self):
        """Test restarting chat clears messages except first 2"""
        response = self.client.post(
            reverse('chat-restart', kwargs={'chat_id': self.chat.id}),
            {'restart': 'true'}
        )

        self.assertEqual(response.status_code, 302)
        self.chat.refresh_from_db()
        self.assertEqual(len(self.chat.messages), 2)
        self.assertEqual(self.chat.messages[0]['role'], 'system')
        self.assertEqual(self.chat.messages[1]['role'], 'assistant')


class UploadedJobListingViewPostTest(TestCase):
    """Test UploadedJobListingView POST edge cases"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_upload_job_listing_empty_text(self):
        """Test posting job listing with empty text"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': '',
            'title': 'Empty Job'
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            UploadedJobListing.objects.filter(title='Empty Job').exists()
        )

    def test_upload_job_listing_empty_title(self):
        """Test posting job listing with empty title"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'Some job description',
            'title': ''
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            UploadedJobListing.objects.filter(
                content='Some job description').exists()
        )

    def test_upload_job_listing_whitespace_only(self):
        """Test posting job listing with whitespace only"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': '   ',
            'title': 'Whitespace Job'
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            UploadedJobListing.objects.filter(title='Whitespace Job').exists()
        )


class DocxFileUploadTest(TestCase):
    """Test DOCX file upload functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    @patch('active_interview_app.views.filetype.guess')
    @patch('active_interview_app.views.Document')
    @patch('active_interview_app.views.md')
    def test_upload_docx_file_success(
            self, mock_md, mock_document, mock_filetype):
        """Test successfully uploading a DOCX file"""
        # Mock filetype to return DOCX
        mock_file_type = MagicMock()
        mock_file_type.extension = 'docx'
        mock_filetype.return_value = mock_file_type

        # Mock DOCX parsing
        mock_doc_instance = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = 'Resume paragraph'
        mock_doc_instance.paragraphs = [mock_paragraph]
        mock_document.return_value = mock_doc_instance

        # Mock markdown conversion
        mock_md.return_value = '# Resume Markdown'

        file_content = b'fake docx content'
        file = SimpleUploadedFile(
            "resume.docx",
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        response = self.client.post(reverse('upload_file'), {
            'file': file,
            'title': 'My DOCX Resume'
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(UploadedResume.objects.filter(
            title='My DOCX Resume').exists())
        resume = UploadedResume.objects.get(title='My DOCX Resume')
        self.assertEqual(resume.content, '# Resume Markdown')
