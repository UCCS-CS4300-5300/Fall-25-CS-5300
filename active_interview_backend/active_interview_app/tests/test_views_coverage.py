"""
Additional tests to improve coverage for views.py
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import json
import io

from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing,
    Chat
)


class BasicViewsCoverageTest(TestCase):
    """Test basic views that were not covered"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_aboutus_view(self):
        """Test the about us page"""
        response = self.client.get(reverse('about-us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about-us.html')

    # Skipping test_results_view because the template doesn't exist
    # and line 105 is just a simple render

    def test_loggedin_view(self):
        """Test the logged in view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('loggedin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loggedinindex.html')


class RegisterViewCoverageTest(TestCase):
    """Test register view"""

    def setUp(self):
        self.client = Client()
        # Create the required group
        Group.objects.create(name='average_role')

    def test_register_success(self):
        """Test successful user registration"""
        response = self.client.post(reverse('register_page'), {
            'username': 'newuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        # Check redirect after successful registration
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # Check user was added to group
        user = User.objects.get(username='newuser')
        self.assertTrue(user.groups.filter(name='average_role').exists())


class FileUploadCoverageTest(TestCase):
    """Test file upload views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_upload_file_get(self):
        """Test GET request to upload_file view"""
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')

    @patch('active_interview_app.views.filetype.guess')
    @patch('active_interview_app.views.Document')
    def test_upload_docx_file(self, mock_document, mock_filetype):
        """Test uploading a DOCX file"""
        # Create mock file type
        mock_file_type = MagicMock()
        mock_file_type.extension = 'docx'
        mock_filetype.return_value = mock_file_type

        # Mock Document class
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = 'Test paragraph'
        mock_doc.paragraphs = [mock_para]
        mock_document.return_value = mock_doc

        # Create a fake DOCX file
        file_content = b'fake docx content'
        file = SimpleUploadedFile(
            "test_resume.docx",
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        response = self.client.post(reverse('upload_file'), {
            'file': file,
            'title': 'Test DOCX Resume'
        })

        # Check redirect after successful upload
        self.assertEqual(response.status_code, 302)
        self.assertTrue(UploadedResume.objects.filter(title='Test DOCX Resume').exists())


class JobListingViewCoverageTest(TestCase):
    """Test job listing views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        # UploadedJobListing requires a file field
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_file = SimpleUploadedFile("test.txt", b"test content")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake/path',
            filename='test.txt',
            file=fake_file
        )

    def test_delete_job(self):
        """Test deleting a job listing"""
        response = self.client.post(
            reverse('delete_job', kwargs={'job_id': self.job.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(UploadedJobListing.objects.filter(id=self.job.id).exists())

    def test_uploaded_job_listing_view_empty_text(self):
        """Test UploadedJobListingView with empty text"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': '',
            'title': 'Test Title'
        })
        self.assertEqual(response.status_code, 302)

    def test_uploaded_job_listing_view_empty_title(self):
        """Test UploadedJobListingView with empty title"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'Some job description',
            'title': ''
        })
        self.assertEqual(response.status_code, 302)


class ChatViewsCoverageTest(TestCase):
    """Test chat-related views for better coverage"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        # Create job listing and resume with proper fields
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        fake_resume_file = SimpleUploadedFile("resume.pdf", b"resume content")

        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job_file
        )
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume_file
        )

    @patch('active_interview_app.views._ai_available')
    def test_create_chat_ai_unavailable(self, mock_ai_available):
        """Test creating chat when AI is unavailable"""
        mock_ai_available.return_value = False

        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'title': 'Test Chat',
            'listing_choice': self.job_listing.id,
            'resume_choice': self.resume.id,
            'difficulty': 5,
            'type': 'GEN'  # Use actual choice value
        })
        # Should still create chat but with empty AI message
        self.assertEqual(response.status_code, 302)

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_create_chat_without_resume_ai_unavailable(self, mock_client, mock_ai_available):
        """Test creating chat without resume when AI is unavailable"""
        mock_ai_available.return_value = False

        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'title': 'Test Chat No Resume',
            'listing_choice': self.job_listing.id,
            'resume_choice': '',
            'difficulty': 7,
            'type': 'ISK'  # Use actual choice value
        })
        self.assertEqual(response.status_code, 302)

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_create_chat_key_questions_regex_fail(self, mock_client, mock_ai_available):
        """Test creating chat when key questions regex doesn't match"""
        mock_ai_available.return_value = True
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid response without JSON array"

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai

        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'title': 'Test Chat',
            'listing_choice': self.job_listing.id,
            'resume_choice': self.resume.id,
            'difficulty': 5,
            'type': 'GEN'  # Use actual choice value
        })
        self.assertEqual(response.status_code, 302)

    @patch('active_interview_app.views._ai_available')
    def test_chat_view_post_ai_unavailable(self, mock_ai_available):
        """Test ChatView POST when AI is unavailable"""
        mock_ai_available.return_value = False

        chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            job_listing=self.job_listing,
            resume=self.resume,
            difficulty=5,
            type='GEN',  # Use actual choice value
            messages=[
                {"role": "system", "content": "System prompt"},
                {"role": "assistant", "content": "Hello"}
            ]
        )

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': chat.id}),
            {'message': 'Test message'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        json_response = json.loads(response.content)
        self.assertIn('error', json_response)

    @patch('active_interview_app.views._ai_available')
    def test_key_questions_view_ai_unavailable(self, mock_ai_available):
        """Test KeyQuestionsView POST when AI is unavailable"""
        mock_ai_available.return_value = False

        chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            job_listing=self.job_listing,
            resume=self.resume,
            difficulty=5,
            type='GEN',  # Use actual choice value
            messages=[{"role": "system", "content": "System prompt"}],
            key_questions=[
                {
                    "id": 0,
                    "title": "Test Question",
                    "duration": 60,
                    "content": "What is your experience?"
                }
            ]
        )

        response = self.client.post(
            reverse('key-questions', kwargs={'chat_id': chat.id, 'question_id': 0}),
            {'message': 'My answer'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        json_response = json.loads(response.content)
        self.assertIn('error', json_response)

    @patch('active_interview_app.views._ai_available')
    def test_key_questions_view_without_resume(self, mock_ai_available):
        """Test KeyQuestionsView with chat that has no resume"""
        mock_ai_available.return_value = False

        chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            job_listing=self.job_listing,
            resume=None,  # No resume
            difficulty=5,
            type='GEN',  # Use actual choice value
            messages=[{"role": "system", "content": "System prompt"}],
            key_questions=[
                {
                    "id": 0,
                    "title": "Test Question",
                    "duration": 60,
                    "content": "What is your experience?"
                }
            ]
        )

        response = self.client.post(
            reverse('key-questions', kwargs={'chat_id': chat.id, 'question_id': 0}),
            {'message': 'My answer'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        json_response = json.loads(response.content)
        self.assertIn('error', json_response)


class ResultsViewsCoverageTest(TestCase):
    """Test results-related views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        # Create job listing with proper fields
        from django.core.files.uploadedfile import SimpleUploadedFile
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
            type='GEN',  # Use the actual choice value, not 'behavioral'
            messages=[
                {"role": "system", "content": "System prompt"},
                {"role": "assistant", "content": "Hello"},
                {"role": "user", "content": "Hi there"}
            ]
        )

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_result_charts_view(self, mock_client, mock_ai_available):
        """Test ResultCharts view (which is what chat-results URL points to)"""
        mock_ai_available.return_value = True
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]

        # First call returns scores, second call returns explanation
        mock_response.choices[0].message.content = "85\n90\n80\n88"

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai

        response = self.client.get(
            reverse('chat-results', kwargs={'chat_id': self.chat.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['scores']['Professionalism'], 85)
        self.assertEqual(response.context['scores']['Subject Knowledge'], 90)

    @patch('active_interview_app.views._ai_available')
    def test_result_charts_view_ai_unavailable(self, mock_ai_available):
        """Test ResultCharts view when AI is unavailable"""
        mock_ai_available.return_value = False

        response = self.client.get(
            reverse('chat-results', kwargs={'chat_id': self.chat.id})
        )
        self.assertEqual(response.status_code, 200)
        # All scores should be 0 when AI is unavailable
        self.assertEqual(response.context['scores']['Professionalism'], 0)
        self.assertEqual(response.context['scores']['Overall'], 0)

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_result_charts_invalid_scores(self, mock_client, mock_ai_available):
        """Test ResultCharts view with invalid score format"""
        mock_ai_available.return_value = True
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]

        # Return invalid scores (not 4 values)
        mock_response.choices[0].message.content = "85\n90"

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai

        response = self.client.get(
            reverse('chat-results', kwargs={'chat_id': self.chat.id})
        )
        self.assertEqual(response.status_code, 200)
        # Should default to 0s when scores are invalid
        self.assertEqual(response.context['scores']['Professionalism'], 0)


class APIViewsCoverageTest(TestCase):
    """Test API views for coverage"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_login(self.user)

    def test_uploaded_resume_view_get(self):
        """Test UploadedResumeView GET endpoint"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_file = SimpleUploadedFile("resume.pdf", b"resume content")

        UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

        response = self.client.get(reverse('file_list'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)

    def test_uploaded_resume_view_post_invalid(self):
        """Test UploadedResumeView POST with invalid data"""
        response = self.client.post(
            reverse('file_list'),
            data=json.dumps({'invalid': 'data'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

