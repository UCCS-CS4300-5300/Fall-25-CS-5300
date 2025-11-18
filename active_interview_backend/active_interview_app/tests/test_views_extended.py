"""
Extended comprehensive tests for views.py to maximize coverage
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing,
    Chat
)
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock
from unittest import skip
import json


class RegisterViewTest(TestCase):
    """Extended tests for register view"""

    def test_register_post_valid(self):
        """Test POST request with valid registration data"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!'
        }
        response = self.client.post(reverse('register_page'), data)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)

        # User should be created
        user = User.objects.get(username='newuser')
        self.assertIsNotNone(user)

        # User should be added to average_role group
        self.assertTrue(user.groups.filter(name='average_role').exists())

    def test_register_post_invalid(self):
        """Test POST request with invalid registration data"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpass123!',
            'password2': 'differentpass!'
        }
        response = self.client.post(reverse('register_page'), data)

        # Should return the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
        self.assertIn('form', response.context)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class UploadFileViewTest(TestCase):
    """Extended tests for upload_file view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    @patch('active_interview_app.views.filetype')
    @patch('active_interview_app.views.pymupdf4llm')
    def test_upload_pdf_file(self, mock_pymupdf, mock_filetype):
        """Test uploading a PDF file"""
        # Mock filetype detection
        mock_file_type = Mock()
        mock_file_type.extension = 'pdf'
        mock_filetype.guess.return_value = mock_file_type

        # Mock PDF conversion
        mock_pymupdf.to_markdown.return_value = "# PDF Content"

        pdf_content = b'%PDF-1.4 fake pdf content'
        uploaded_file = SimpleUploadedFile(
            "test_resume.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        data = {
            'title': 'Test PDF Resume',
            'file': uploaded_file
        }

        response = self.client.post(reverse('upload_file'), data)

        # Should redirect to document list
        self.assertRedirects(response, reverse('document-list'))

        # Resume should be created
        resume = UploadedResume.objects.get(title='Test PDF Resume')
        self.assertEqual(resume.content, "# PDF Content")

    @patch('active_interview_app.views.filetype')
    @patch('active_interview_app.views.Document')
    @patch('active_interview_app.views.md')
    def test_upload_docx_file(
            self,
            mock_md,
            mock_document_class,
            mock_filetype):
        """Test uploading a DOCX file"""
        # Mock filetype detection
        mock_file_type = Mock()
        mock_file_type.extension = 'docx'
        mock_filetype.guess.return_value = mock_file_type

        # Mock DOCX processing
        mock_doc = Mock()
        mock_para1 = Mock()
        mock_para1.text = "First paragraph"
        mock_para2 = Mock()
        mock_para2.text = "Second paragraph"
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document_class.return_value = mock_doc

        # Mock markdown conversion
        mock_md.return_value = "First paragraph\nSecond paragraph"

        docx_content = b'PK\x03\x04 fake docx content'
        uploaded_file = SimpleUploadedFile(
            "test_resume.docx",
            docx_content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        data = {
            'title': 'Test DOCX Resume',
            'file': uploaded_file
        }

        response = self.client.post(reverse('upload_file'), data)

        # Should redirect to document list
        self.assertRedirects(response, reverse('document-list'))

        # Resume should be created
        resume = UploadedResume.objects.get(title='Test DOCX Resume')
        self.assertIsNotNone(resume)

    @patch('active_interview_app.views.filetype')
    def test_upload_invalid_file_type(self, mock_filetype):
        """Test uploading invalid file type"""
        # Mock filetype detection as invalid type
        mock_file_type = Mock()
        mock_file_type.extension = 'txt'
        mock_filetype.guess.return_value = mock_file_type

        txt_content = b'plain text content'
        uploaded_file = SimpleUploadedFile(
            "test.txt",
            txt_content,
            content_type="text/plain"
        )

        data = {
            'title': 'Test TXT File',
            'file': uploaded_file
        }

        response = self.client.post(reverse('upload_file'), data)

        # Should redirect to document list with error message
        self.assertRedirects(response, reverse('document-list'))

        # Resume should NOT be created
        self.assertFalse(UploadedResume.objects.filter(
            title='Test TXT File').exists())

    def test_upload_file_get_request(self):
        """Test GET request to upload_file returns form"""
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')
        self.assertIn('form', response.context)


class UploadedJobListingViewTest(TestCase):
    """Extended tests for UploadedJobListingView API"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_post_valid_job_listing(self):
        """Test POST with valid job listing text"""
        data = {
            'paste-text': 'Software Engineer position available',
            'title': 'Software Engineer'
        }

        response = self.client.post(reverse('save_pasted_text'), data)

        # Should redirect to document list
        self.assertRedirects(response, reverse('document-list'))

        # Job listing should be created
        job_listing = UploadedJobListing.objects.get(title='Software Engineer')
        self.assertEqual(job_listing.content,
                         'Software Engineer position available')
        self.assertEqual(job_listing.user, self.user)

    def test_post_empty_text(self):
        """Test POST with empty text field"""
        data = {
            'paste-text': '',
            'title': 'Empty Job'
        }

        response = self.client.post(reverse('save_pasted_text'), data)

        # Should redirect with error
        self.assertRedirects(response, reverse('document-list'))

        # Job listing should NOT be created
        self.assertFalse(UploadedJobListing.objects.filter(
            title='Empty Job').exists())

    def test_post_empty_title(self):
        """Test POST with empty title field"""
        data = {
            'paste-text': 'Some job content',
            'title': ''
        }

        response = self.client.post(reverse('save_pasted_text'), data)

        # Should redirect with error
        self.assertRedirects(response, reverse('document-list'))

        # Job listing should NOT be created
        self.assertFalse(UploadedJobListing.objects.filter(
            content='Some job content').exists())


class UploadedResumeViewAPITest(TestCase):
    """Extended tests for UploadedResumeView REST API"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

    def test_get_resumes_authenticated(self):
        """Test GET request returns user's resumes"""
        self.client.login(username='testuser', password='testpass123')

        # Create some resumes
        UploadedResume.objects.create(
            user=self.user,
            content='Resume 1 content',
            title='Resume 1'
        )
        UploadedResume.objects.create(
            user=self.user,
            content='Resume 2 content',
            title='Resume 2'
        )

        response = self.client.get(reverse('file_list'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)

    def test_get_resumes_unauthenticated(self):
        """Test GET request requires authentication"""
        response = self.client.get(reverse('file_list'))
        self.assertEqual(response.status_code, 403)


# JobListingList API is not exposed in URLs, removing these tests


class ChatListViewTest(TestCase):
    """Extended tests for chat_list view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

    def test_chat_list_requires_login(self):
        """Test chat list requires authentication"""
        response = self.client.get(reverse('chat-list'))
        self.assertEqual(response.status_code, 302)

    def test_chat_list_shows_user_chats(self):
        """Test chat list shows only user's chats"""
        self.client.login(username='testuser', password='testpass123')

        # Create chats for user
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content='Job content',
            filename='job.txt'
        )

        chat1 = Chat.objects.create(
            owner=self.user,
            title='Chat 1',
            messages=[],
            job_listing=job_listing
        )
        chat2 = Chat.objects.create(
            owner=self.user,
            title='Chat 2',
            messages=[],
            job_listing=job_listing
        )

        # Create chat for other user
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_job = UploadedJobListing.objects.create(
            user=other_user,
            content='Other job',
            filename='other.txt'
        )
        Chat.objects.create(
            owner=other_user,
            title='Other Chat',
            messages=[],
            job_listing=other_job
        )

        response = self.client.get(reverse('chat-list'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('owner_chats', response.context)
        chats = list(response.context['owner_chats'])
        self.assertEqual(len(chats), 2)
        self.assertIn(chat1, chats)
        self.assertIn(chat2, chats)


class ResultsChatViewTest(TestCase):
    """Extended tests for ResultsChat view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content='Job content',
            filename='job.txt'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            messages=[
                {"role": "system", "content": "You are an interviewer"},
                {"role": "assistant", "content": "Hello"},
                {"role": "user", "content": "Hi there"}
            ],
            job_listing=self.job_listing
        )
        self.client = Client()

    def test_results_chat_requires_login(self):
        """Test results chat requires authentication"""
        response = self.client.get(
            reverse('chat-results', args=[self.chat.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_results_chat_requires_ownership(self):
        """Test user can only view their own chat results"""
        User.objects.create_user(
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')

        response = self.client.get(
            reverse('chat-results', args=[self.chat.id])
        )
        self.assertEqual(response.status_code, 403)

    @patch('active_interview_app.views.ai_available')
    def test_results_chat_ai_unavailable(self, mockai_available):
        """Test results chat when AI is unavailable"""
        mockai_available.return_value = False
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('chat-results', args=[self.chat.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('feedback', response.context)
        self.assertEqual(response.context['feedback'],
                         'AI features are currently unavailable.')

    @patch('active_interview_app.views.get_openai_client')
    @patch('active_interview_app.views.ai_available')
    def test_results_chatai_available(self, mockai_available, mock_get_client):
        """Test results chat when AI is available"""
        mockai_available.return_value = True

        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Great interview performance!"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('chat-results', args=[self.chat.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('feedback', response.context)
        self.assertEqual(response.context['feedback'],
                         'Great interview performance!')


class ResultChartsViewTest(TestCase):
    """Extended tests for ResultCharts view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content='Job content',
            filename='job.txt'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            messages=[
                {"role": "system", "content": "You are an interviewer"},
                {"role": "assistant", "content": "Hello"},
                {"role": "user", "content": "Hi there"}
            ],
            job_listing=self.job_listing
        )
        self.client = Client()

    @skip("chat-results-charts URL not implemented yet")
    @patch('active_interview_app.views.ai_available')
    def test_result_charts_ai_unavailable(self, mockai_available):
        """Test result charts when AI is unavailable"""
        mockai_available.return_value = False
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('chat-results-charts', args=[self.chat.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('scores', response.context)
        scores = response.context['scores']
        self.assertEqual(scores['Professionalism'], 0)
        self.assertEqual(scores['Subject Knowledge'], 0)
        self.assertEqual(scores['Clarity'], 0)
        self.assertEqual(scores['Overall'], 0)

    @skip("chat-results-charts URL not implemented yet")
    @patch('active_interview_app.views.get_openai_client')
    @patch('active_interview_app.views.ai_available')
    def test_result_chartsai_available_valid_scores(
            self, mockai_available, mock_get_client):
        """Test result charts with valid AI scores"""
        mockai_available.return_value = True

        # Mock OpenAI response
        mock_client = Mock()
        mock_response1 = Mock()
        mock_choice1 = Mock()
        mock_message1 = Mock()
        mock_message1.content = "85\n78\n92\n88"
        mock_choice1.message = mock_message1
        mock_response1.choices = [mock_choice1]

        mock_response2 = Mock()
        mock_choice2 = Mock()
        mock_message2 = Mock()
        mock_message2.content = "You performed well overall."
        mock_choice2.message = mock_message2
        mock_response2.choices = [mock_choice2]

        mock_client.chat.completions.create.side_effect = [
            mock_response1, mock_response2]
        mock_get_client.return_value = mock_client

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('chat-results-charts', args=[self.chat.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('scores', response.context)
        scores = response.context['scores']
        self.assertEqual(scores['Professionalism'], 85)
        self.assertEqual(scores['Subject Knowledge'], 78)
        self.assertEqual(scores['Clarity'], 92)
        self.assertEqual(scores['Overall'], 88)

    @skip("chat-results-charts URL not implemented yet")
    @patch('active_interview_app.views.get_openai_client')
    @patch('active_interview_app.views.ai_available')
    def test_result_charts_ai_invalid_scores(
            self, mockai_available, mock_get_client):
        """Test result charts with invalid AI response"""
        mockai_available.return_value = True

        # Mock OpenAI response with invalid format
        mock_client = Mock()
        mock_response1 = Mock()
        mock_choice1 = Mock()
        mock_message1 = Mock()
        mock_message1.content = "Not a valid score format"
        mock_choice1.message = mock_message1
        mock_response1.choices = [mock_choice1]

        mock_response2 = Mock()
        mock_choice2 = Mock()
        mock_message2 = Mock()
        mock_message2.content = "Feedback"
        mock_choice2.message = mock_message2
        mock_response2.choices = [mock_choice2]

        mock_client.chat.completions.create.side_effect = [
            mock_response1, mock_response2]
        mock_get_client.return_value = mock_client

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('chat-results-charts', args=[self.chat.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('scores', response.context)
        # Should default to zeros when parsing fails
        scores = response.context['scores']
        self.assertEqual(scores['Professionalism'], 0)
        self.assertEqual(scores['Subject Knowledge'], 0)
        self.assertEqual(scores['Clarity'], 0)
        self.assertEqual(scores['Overall'], 0)


class CreateChatViewExtendedTest(TestCase):
    """Extended tests for CreateChat view to increase coverage"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content='Software Engineer position available',
            filename='job.txt',
            title='Software Engineer'
        )
        self.resume = UploadedResume.objects.create(
            user=self.user,
            content='John Doe resume content',
            title='My Resume'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    @patch('active_interview_app.views.get_openai_client')
    @patch('active_interview_app.views.ai_available')
    def test_create_chat_without_resumeai_available(
            self, mockai_available, mock_get_client):
        """Test creating chat without resume when AI is available"""
        mockai_available.return_value = True

        # Mock OpenAI responses
        mock_client = Mock()
        mock_response1 = Mock()
        mock_choice1 = Mock()
        mock_message1 = Mock()
        mock_message1.content = "Hello, welcome to the interview!"
        mock_choice1.message = mock_message1
        mock_response1.choices = [mock_choice1]

        mock_response2 = Mock()
        mock_choice2 = Mock()
        mock_message2 = Mock()
        mock_message2.content = '[{"id": 0, "title": "Test Question", "duration": 60, "content": "What is Python?"}]'
        mock_choice2.message = mock_message2
        mock_response2.choices = [mock_choice2]

        mock_client.chat.completions.create.side_effect = [
            mock_response1, mock_response2]
        mock_get_client.return_value = mock_client

        data = {
            'create': 'true',
            'title': 'Interview without Resume',
            'type': Chat.GENERAL,
            'difficulty': 5,
            'listing_choice': self.job_listing.id
        }

        response = self.client.post(reverse('chat-create'), data)

        # Should redirect to chat view
        self.assertEqual(response.status_code, 302)

        # Chat should be created without resume
        chat = Chat.objects.get(title='Interview without Resume')
        self.assertIsNone(chat.resume)
        self.assertEqual(chat.job_listing, self.job_listing)

    @patch('active_interview_app.views.ai_available')
    def test_create_chat_ai_unavailable(self, mockai_available):
        """Test creating chat when AI is unavailable"""
        mockai_available.return_value = False

        data = {
            'create': 'true',
            'title': 'Interview No AI',
            'type': Chat.GENERAL,
            'difficulty': 5,
            'listing_choice': self.job_listing.id,
            'resume_choice': self.resume.id
        }

        response = self.client.post(reverse('chat-create'), data)

        # Should redirect to chat view
        self.assertEqual(response.status_code, 302)

        # Chat should be created with empty AI message
        chat = Chat.objects.get(title='Interview No AI')
        self.assertEqual(len(chat.messages), 2)
        self.assertEqual(chat.messages[1]['content'], '')
        self.assertEqual(chat.key_questions, [])
