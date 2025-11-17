"""
Tests for API views and file upload functionality.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock
import json
import io

from active_interview_app.models import UploadedResume, UploadedJobListing, Chat
from active_interview_app.views import (
    UploadedResumeView, UploadedJobListingView, upload_file
)


class UploadedResumeViewTest(TestCase):
    """Test UploadedResumeView API"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            'apiuser', 'api@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_file = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='API Test Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

    def test_get_resumes_list(self):
        """Test GET request to list resumes"""
        response = self.client.get(reverse('file_list'))

        self.assertEqual(response.status_code, 200)
        # Check that response is JSON (APIView returns JSON)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_get_resumes_requires_login(self):
        """Test GET requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('file_list'))

        # APIView with IsAuthenticated returns 403 Forbidden
        self.assertEqual(response.status_code, 403)


class UploadedJobListingViewTest(TestCase):
    """Test UploadedJobListingView API"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            'jobapi', 'jobapi@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_file = SimpleUploadedFile("job.txt", b"job content")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='API Test Job',
            content='Job content',
            filepath='/fake',
            filename='job.txt',
            file=fake_file
        )

    def test_get_job_listings_list(self):
        """Test GET request returns 405 (Method Not Allowed) since view only supports POST"""
        response = self.client.get(reverse('save_pasted_text'))

        self.assertEqual(response.status_code, 405)

    def test_post_job_listing_with_text(self):
        """Test POST to create job listing from pasted text"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'New job description here',
            'title': 'New Job Posting'
        })

        # Should redirect after creation
        self.assertEqual(response.status_code, 302)

        # Job should be created
        self.assertTrue(
            UploadedJobListing.objects.filter(title='New Job Posting').exists()
        )

    def test_post_job_listing_empty_text(self):
        """Test POST with empty text doesn't create job"""
        count_before = UploadedJobListing.objects.count()

        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': '',
            'title': 'Empty Job'
        })

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # No new job should be created
        self.assertEqual(UploadedJobListing.objects.count(), count_before)

    def test_post_job_listing_empty_title(self):
        """Test POST with empty title doesn't create job"""
        count_before = UploadedJobListing.objects.count()

        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'Job content',
            'title': ''
        })

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # No new job should be created
        self.assertEqual(UploadedJobListing.objects.count(), count_before)

    def test_get_specific_job_listing(self):
        """Test GET specific job listing by pk returns 405 (Method Not Allowed)"""
        response = self.client.get(
            reverse('pasted_text_detail', args=[self.job.id])
        )

        self.assertEqual(response.status_code, 405)


class UploadFileViewTest(TestCase):
    """Test file upload view"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            'uploader', 'upload@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

    @patch('active_interview_app.views.filetype.guess')
    def test_upload_file_pdf_success(self, mock_filetype):
        """Test successful PDF file upload"""
        # Mock filetype detection
        mock_guess = Mock()
        mock_guess.extension = 'pdf'
        mock_guess.mime = 'application/pdf'
        mock_filetype.return_value = mock_guess

        # Create test PDF file
        pdf_content = b"%PDF-1.4 test content"
        test_file = SimpleUploadedFile(
            "test_resume.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        with patch('active_interview_app.views.pymupdf4llm.to_markdown') as mock_pdf:
            mock_pdf.return_value = "Extracted text from PDF"

            response = self.client.post(reverse('upload_file'), {
                'file': test_file,
                'title': 'My PDF Resume'
            })

            # Should redirect after successful upload
            self.assertEqual(response.status_code, 302)

            # Resume should be created
            resume = UploadedResume.objects.filter(
                title='My PDF Resume').first()
            self.assertIsNotNone(resume)
            self.assertEqual(resume.user, self.user)

    @patch('active_interview_app.views.filetype.guess')
    def test_upload_file_docx_success(self, mock_filetype):
        """Test successful DOCX file upload"""
        # Mock filetype detection
        mock_guess = Mock()
        mock_guess.extension = 'docx'
        mock_guess.mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        mock_filetype.return_value = mock_guess

        test_file = SimpleUploadedFile(
            "test_resume.docx",
            b"fake docx content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        with patch('active_interview_app.views.Document') as mock_doc:
            # Mock Document reading
            mock_document = Mock()
            mock_paragraph = Mock()
            mock_paragraph.text = "Document text"
            mock_document.paragraphs = [mock_paragraph]
            mock_doc.return_value = mock_document

            response = self.client.post(reverse('upload_file'), {
                'file': test_file,
                'title': 'My DOCX Resume'
            })

            # Should redirect
            self.assertEqual(response.status_code, 302)

            # Resume should be created
            self.assertTrue(
                UploadedResume.objects.filter(title='My DOCX Resume').exists()
            )

    @patch('active_interview_app.views.filetype.guess')
    def test_upload_file_txt_success(self, mock_filetype):
        """Test TXT file upload is rejected (only PDF/DOCX allowed)"""
        # Mock filetype detection
        mock_guess = Mock()
        mock_guess.extension = 'txt'
        mock_guess.mime = 'text/plain'
        mock_filetype.return_value = mock_guess

        test_file = SimpleUploadedFile(
            "test_resume.txt",
            b"Plain text resume content",
            content_type="text/plain"
        )

        response = self.client.post(reverse('upload_file'), {
            'file': test_file,
            'title': 'My TXT Resume'
        })

        # Should redirect with error
        self.assertEqual(response.status_code, 302)

        # Resume should NOT be created (TXT not allowed)
        resume = UploadedResume.objects.filter(title='My TXT Resume').first()
        self.assertIsNone(resume)

    @patch('active_interview_app.views.filetype.guess')
    def test_upload_file_unsupported_type(self, mock_filetype):
        """Test upload with unsupported file type"""
        # Mock filetype detection
        mock_guess = Mock()
        mock_guess.extension = 'exe'
        mock_guess.mime = 'application/x-executable'
        mock_filetype.return_value = mock_guess

        test_file = SimpleUploadedFile(
            "test.exe",
            b"fake exe content",
            content_type="application/x-executable"
        )

        response = self.client.post(reverse('upload_file'), {
            'file': test_file,
            'title': 'Invalid File'
        })

        # Should redirect to document-list with error message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('document-list'))

        # No resume should be created
        self.assertFalse(
            UploadedResume.objects.filter(title='Invalid File').exists()
        )

    def test_upload_file_get(self):
        """Test GET request to upload page"""
        response = self.client.get(reverse('upload_file'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')
        self.assertIn('form', response.context)

    def test_upload_file_requires_login(self):
        """Test upload file requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('upload_file'))

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    @patch('active_interview_app.views.filetype.guess', return_value=None)
    def test_upload_file_unknown_filetype(self, mock_filetype):
        """Test upload when filetype cannot be determined"""
        test_file = SimpleUploadedFile(
            "unknown",
            b"unknown content"
        )

        response = self.client.post(reverse('upload_file'), {
            'file': test_file,
            'title': 'Unknown File'
        })

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)


class ChatViewTest(TestCase):
    """Test ChatView for chat interactions"""

    def setUp(self):
        """Set up test data"""
        # Create average_role group (required by signals)
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            'chatter', 'chat@example.com', 'pass')
        self.other_user = User.objects.create_user(
            'other', 'other@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_job = SimpleUploadedFile("job.txt", b"job")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            difficulty=5,
            messages=[
                {"role": "system", "content": "System prompt"},
                {"role": "assistant", "content": "Hello!"}
            ],
            job_listing=self.job,
            key_questions=[]
        )

        self.other_chat = Chat.objects.create(
            owner=self.other_user,
            title='Other Chat',
            difficulty=5,
            messages=[],
            job_listing=self.job,
            key_questions=[]
        )

    def test_chat_view_get_owner(self):
        """Test GET chat view as owner"""
        response = self.client.get(reverse('chat-view', args=[self.chat.id]))

        self.assertEqual(response.status_code, 200)
        # Check for template name presence instead of exact path match
        template_names = [t.name for t in response.templates]
        self.assertTrue(
            any('chat-view.html' in name for name in template_names),
            f"Expected chat-view.html template, got: {template_names}"
        )
        self.assertIn('chat', response.context)

    def test_chat_view_get_not_owner(self):
        """Test GET chat view as non-owner returns 403"""
        response = self.client.get(
            reverse('chat-view', args=[self.other_chat.id]))

        self.assertEqual(response.status_code, 403)

    @patch('active_interview_app.views.ai_available', return_value=False)
    def test_chat_view_post_ai_disabled(self, mock_ai):
        """Test POST to chat when AI is disabled"""
        response = self.client.post(
            reverse('chat-view', args=[self.chat.id]),
            data=json.dumps({'message': 'Hello AI'}),
            content_type='application/json'
        )

        # Should return error response
        data = json.loads(response.content)
        self.assertIn('error', data)


class RestartChatViewTest(TestCase):
    """Test RestartChat view"""

    def setUp(self):
        """Set up test data"""
        # Create average_role group (required by signals)
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            'restarter', 'restart@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_job = SimpleUploadedFile("job.txt", b"job")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Chat to Restart',
            difficulty=5,
            messages=[
                {"role": "system", "content": "System"},
                {"role": "user", "content": "Message 1"},
                {"role": "assistant", "content": "Response 1"}
            ],
            job_listing=self.job
        )

    @patch('active_interview_app.views.ai_available', return_value=False)
    def test_restart_chat_post(self, mock_ai):
        """Test POST to restart chat"""
        response = self.client.post(
            reverse('chat-restart', args=[self.chat.id]), {'restart': 'true'})

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Messages should be reset (keeping only system message)
        self.chat.refresh_from_db()
        # Will have system message + new AI greeting (or empty if AI disabled)
        self.assertLessEqual(len(self.chat.messages), 2)


class KeyQuestionsViewTest(TestCase):
    """Test KeyQuestionsView"""

    def setUp(self):
        """Set up test data"""
        # Create average_role group (required by signals)
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            'questioner', 'q@example.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        fake_job = SimpleUploadedFile("job.txt", b"job")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Question Chat',
            difficulty=5,
            messages=[],
            job_listing=self.job,
            key_questions=[
                {
                    "id": 0,
                    "title": "Question 1",
                    "content": "What is your experience?",
                    "duration": 60
                },
                {
                    "id": 1,
                    "title": "Question 2",
                    "content": "Tell me about a project",
                    "duration": 120
                }
            ]
        )

    def test_key_questions_view_get(self):
        """Test GET key questions view"""
        response = self.client.get(
            reverse('key-questions', args=[self.chat.id, 0])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'key-questions.html')
        self.assertIn('chat', response.context)
        self.assertIn('question', response.context)

    @patch('active_interview_app.views.ai_available', return_value=False)
    def test_key_questions_view_post_ai_disabled(self, mock_ai):
        """Test POST answer when AI is disabled"""
        response = self.client.post(
            reverse('key-questions', args=[self.chat.id, 0]),
            data=json.dumps({'response': 'My answer'}),
            content_type='application/json'
        )

        # Should return error
        data = json.loads(response.content)
        self.assertIn('error', data)
