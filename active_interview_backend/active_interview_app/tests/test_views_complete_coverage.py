"""
Comprehensive tests for views.py to achieve 80%+ coverage
Tests all remaining uncovered code paths in views.py
"""
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock, Mock
import json
import re

from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing,
    Chat
)
from active_interview_app.views import (
    get_openai_client,
    _ai_available,
    _ai_unavailable_json,
    MAX_TOKENS
)


class RegisterViewTest(TestCase):
    """Test user registration functionality"""

    def test_register_valid_form(self):
        """Test successful user registration"""
        client = Client()
        response = client.post(reverse('register_page'), {
            'username': 'newuser',
            'password1': 'testpassword123!@#',
            'password2': 'testpassword123!@#',
            'email': 'newuser@example.com'
        })

        # Should redirect to login after successful registration
        self.assertEqual(response.status_code, 302)

        # User should be created
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # User should be added to average_role group
        user = User.objects.get(username='newuser')
        self.assertTrue(user.groups.filter(name='average_role').exists())


class CreateChatWithoutResumeTest(TestCase):
    """Test chat creation without resume"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Looking for a software engineer with Python experience.',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job_file
        )

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_create_chat_without_resume(self, mock_get_client, mock_ai_available):
        """Test creating a chat without a resume attached"""
        mock_ai_available.return_value = True

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! I'm ready to interview you."

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job_listing.id,
            'resume_choice': '',  # No resume
            'difficulty': 5,
            'type': 'GEN'
        })

        self.assertEqual(response.status_code, 302)

        # Chat should be created
        chat = Chat.objects.filter(owner=self.user).first()
        self.assertIsNotNone(chat)
        self.assertIsNone(chat.resume)

        # System prompt should not mention resume
        system_message = chat.messages[0]['content']
        self.assertNotIn('Resume', system_message)
        self.assertNotIn('resume', system_message)

    @patch('active_interview_app.views._ai_available')
    def test_create_chat_ai_unavailable(self, mock_ai_available):
        """Test creating chat when AI is unavailable"""
        mock_ai_available.return_value = False

        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job_listing.id,
            'resume_choice': '',
            'difficulty': 5,
            'type': 'GEN'
        })

        # Should still create the chat with empty AI message
        chat = Chat.objects.filter(owner=self.user).first()
        self.assertIsNotNone(chat)

        # Check that assistant message is empty when AI unavailable
        assistant_messages = [msg for msg in chat.messages if msg['role'] == 'assistant']
        self.assertTrue(any(msg['content'] == '' for msg in assistant_messages))


class CreateChatKeyQuestionsTest(TestCase):
    """Test key questions generation in chat creation"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Software engineering position',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job_file
        )

        fake_resume_file = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Python developer with 5 years experience',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume_file
        )

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_create_chat_key_questions_with_json(self, mock_get_client, mock_ai_available):
        """Test key questions generation with valid JSON response"""
        mock_ai_available.return_value = True

        # Mock OpenAI responses
        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_response1.choices[0].message.content = "Hello! Ready to start?"

        # Key questions response with JSON
        key_questions_json = json.dumps([
            {"id": 0, "title": "Python Experience", "duration": 120, "content": "Tell me about your Python experience"},
            {"id": 1, "title": "Git Knowledge", "duration": 60, "content": "How do you handle merge conflicts?"}
        ])
        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message.content = f"Here are the questions:\n{key_questions_json}"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [mock_response1, mock_response2]
        mock_get_client.return_value = mock_client

        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job_listing.id,
            'resume_choice': self.resume.id,
            'difficulty': 7,
            'type': 'ISK'
        })

        self.assertEqual(response.status_code, 302)

        chat = Chat.objects.filter(owner=self.user).first()
        self.assertIsNotNone(chat)
        self.assertEqual(len(chat.key_questions), 2)
        self.assertEqual(chat.key_questions[0]['title'], 'Python Experience')

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_create_chat_key_questions_json_extraction_fails(self, mock_get_client, mock_ai_available):
        """Test key questions when JSON extraction fails"""
        mock_ai_available.return_value = True

        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_response1.choices[0].message.content = "Hello!"

        # Invalid JSON response (no array found)
        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message.content = "I cannot generate questions"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [mock_response1, mock_response2]
        mock_get_client.return_value = mock_client

        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job_listing.id,
            'resume_choice': self.resume.id,
            'difficulty': 5,
            'type': 'GEN'
        })

        self.assertEqual(response.status_code, 302)

        chat = Chat.objects.filter(owner=self.user).first()
        self.assertIsNotNone(chat)
        # Should have empty key_questions when extraction fails
        self.assertEqual(chat.key_questions, [])


class ChatViewPostTest(TestCase):
    """Test ChatView POST functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

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
                {"role": "system", "content": "You are an interviewer"},
                {"role": "assistant", "content": "Hello!"}
            ]
        )

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_chat_view_post_message(self, mock_get_client, mock_ai_available):
        """Test posting a message to chat"""
        mock_ai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "That's a good answer!"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': self.chat.id}),
            {'message': 'I have 5 years of Python experience'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertEqual(data['message'], "That's a good answer!")

    @patch('active_interview_app.views._ai_available')
    def test_chat_view_post_ai_unavailable(self, mock_ai_available):
        """Test posting message when AI is unavailable"""
        mock_ai_available.return_value = False

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': self.chat.id}),
            {'message': 'Hello'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 503)
        data = json.loads(response.content)
        self.assertIn('error', data)


class EditChatPostTest(TestCase):
    """Test EditChat POST functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

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
                {"role": "system", "content": "You are an interviewer. Selected level: <<5>>"},
                {"role": "assistant", "content": "Hello!"}
            ]
        )

    def test_edit_chat_update_difficulty(self):
        """Test updating chat difficulty"""
        response = self.client.post(
            reverse('chat-edit', kwargs={'chat_id': self.chat.id}),
            {
                'update': 'true',
                'difficulty': 8
            }
        )

        self.assertEqual(response.status_code, 302)

        self.chat.refresh_from_db()
        self.assertEqual(self.chat.difficulty, 8)

        # Check that difficulty in system prompt was updated
        system_message = self.chat.messages[0]['content']
        self.assertIn('<<8>>', system_message)
        self.assertNotIn('<<5>>', system_message)


class KeyQuestionsViewTest(TestCase):
    """Test KeyQuestionsView functionality"""

    def setUp(self):
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Software engineer position requiring Python skills',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job_file
        )

        fake_resume_file = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Experienced Python developer',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume_file
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            job_listing=self.job_listing,
            resume=self.resume,
            difficulty=5,
            type='TECH',
            messages=[{"role": "system", "content": "test"}],
            key_questions=[
                {
                    "id": 0,
                    "title": "Python Experience",
                    "duration": 120,
                    "content": "Describe your Python experience"
                }
            ]
        )

    def test_key_questions_view_get(self):
        """Test GET request to key questions view"""
        response = self.client.get(
            reverse('key-questions', kwargs={'chat_id': self.chat.id, 'question_id': 0})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'key-questions.html')
        self.assertIn('question', response.context)
        self.assertEqual(response.context['question']['title'], 'Python Experience')

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_key_questions_view_post_with_resume(self, mock_get_client, mock_ai_available):
        """Test POST request to key questions with resume"""
        mock_ai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Good answer! 8/10. You demonstrated solid understanding."

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        response = self.client.post(
            reverse('key-questions', kwargs={'chat_id': self.chat.id, 'question_id': 0}),
            {'message': 'I have 5 years of Python experience working on Django projects'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertIn('8/10', data['message'])

    @patch('active_interview_app.views._ai_available')
    def test_key_questions_view_post_ai_unavailable(self, mock_ai_available):
        """Test POST when AI unavailable"""
        mock_ai_available.return_value = False

        response = self.client.post(
            reverse('key-questions', kwargs={'chat_id': self.chat.id, 'question_id': 0}),
            {'message': 'My answer'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 503)


class KeyQuestionsViewNoResumeTest(TestCase):
    """Test KeyQuestionsView without resume"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Software engineer position',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job_file
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            job_listing=self.job_listing,
            resume=None,  # No resume
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}],
            key_questions=[
                {
                    "id": 0,
                    "title": "General Question",
                    "duration": 60,
                    "content": "Why do you want this job?"
                }
            ]
        )

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_key_questions_post_without_resume(self, mock_get_client, mock_ai_available):
        """Test POST to key questions without resume"""
        mock_ai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "7/10 - Good motivation!"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        response = self.client.post(
            reverse('key-questions', kwargs={'chat_id': self.chat.id, 'question_id': 0}),
            {'message': 'I am passionate about this field'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)


class ResultsChatTest(TestCase):
    """Test ResultsChat view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

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
                {"role": "system", "content": "You are an interviewer"},
                {"role": "assistant", "content": "Hello!"},
                {"role": "user", "content": "Hi there!"},
                {"role": "assistant", "content": "How are you?"}
            ]
        )

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_results_chat_with_ai(self, mock_get_client, mock_ai_available):
        """Test results chat when AI is available"""
        mock_ai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "You did well! Good communication skills."

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        response = self.client.get(
            reverse('chat-results', kwargs={'chat_id': self.chat.id})
        )

        self.assertEqual(response.status_code, 200)
        template_names = [t.name for t in response.templates]
        self.assertTrue(any('chat-results.html' in name for name in template_names))
        self.assertIn('feedback', response.context)
        self.assertEqual(response.context['feedback'], "You did well! Good communication skills.")

    @patch('active_interview_app.views._ai_available')
    def test_results_chat_ai_unavailable(self, mock_ai_available):
        """Test results chat when AI is unavailable"""
        mock_ai_available.return_value = False

        response = self.client.get(
            reverse('chat-results', kwargs={'chat_id': self.chat.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('feedback', response.context)
        self.assertIn('unavailable', response.context['feedback'])


class ResultChartsTest(TestCase):
    """Test ResultCharts view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

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
                {"role": "system", "content": "You are an interviewer"},
                {"role": "assistant", "content": "Hello!"}
            ]
        )

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_result_charts_with_valid_scores(self, mock_get_client, mock_ai_available):
        """Test result charts with valid score response"""
        mock_ai_available.return_value = True

        # First call returns scores
        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_response1.choices[0].message.content = "85\n75\n90\n80"

        # Second call returns explanation
        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message.content = "Great professionalism and clarity!"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [mock_response1, mock_response2]
        mock_get_client.return_value = mock_client

        response = self.client.get(
            reverse('result-charts', kwargs={'chat_id': self.chat.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('scores', response.context)
        self.assertEqual(response.context['scores']['Professionalism'], 85)
        self.assertEqual(response.context['scores']['Subject Knowledge'], 75)
        self.assertEqual(response.context['scores']['Clarity'], 90)
        self.assertEqual(response.context['scores']['Overall'], 80)

    @patch('active_interview_app.views._ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_result_charts_with_invalid_scores(self, mock_get_client, mock_ai_available):
        """Test result charts when score parsing fails"""
        mock_ai_available.return_value = True

        # Invalid score response
        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_response1.choices[0].message.content = "invalid\ndata\nhere"

        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message.content = "Could not generate scores"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [mock_response1, mock_response2]
        mock_get_client.return_value = mock_client

        response = self.client.get(
            reverse('result-charts', kwargs={'chat_id': self.chat.id})
        )

        self.assertEqual(response.status_code, 200)
        # Should default to zeros when parsing fails
        self.assertEqual(response.context['scores']['Professionalism'], 0)
        self.assertEqual(response.context['scores']['Subject Knowledge'], 0)

    @patch('active_interview_app.views._ai_available')
    def test_result_charts_ai_unavailable(self, mock_ai_available):
        """Test result charts when AI is unavailable"""
        mock_ai_available.return_value = False

        response = self.client.get(
            reverse('result-charts', kwargs={'chat_id': self.chat.id})
        )

        self.assertEqual(response.status_code, 200)
        # Scores should be 0 when AI unavailable
        self.assertEqual(response.context['scores']['Professionalism'], 0)
        self.assertEqual(response.context['scores']['Overall'], 0)


class UploadFileGetTest(TestCase):
    """Test upload_file GET request"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_upload_file_get(self):
        """Test GET request to upload_file returns form"""
        response = self.client.get(reverse('upload_file'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')
        self.assertIn('form', response.context)


class CreateChatGetTest(TestCase):
    """Test CreateChat GET request"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_create_chat_get(self):
        """Test GET request to create chat"""
        response = self.client.get(reverse('chat-create'))

        self.assertEqual(response.status_code, 200)
        template_names = [t.name for t in response.templates]
        self.assertTrue(any('chat-create.html' in name for name in template_names))
        self.assertIn('form', response.context)
        self.assertIn('owner_chats', response.context)
