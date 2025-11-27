"""
Comprehensive tests to maximize views.py coverage
Targets all remaining untested code paths
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing,
    Chat
)
from unittest.mock import patch, Mock
import json
from .test_credentials import TEST_PASSWORD


class AboutUsViewTest(TestCase):
    """Test aboutus view"""

    def test_about_us_get(self):
        """Test GET request to about us page"""
        response = self.client.get(reverse('about-us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about-us.html')


class RestartChatViewTest(TestCase):
    """Test restart chat functionality"""

    def setUp(self):
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
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
                {"role": "system", "content": "System"},
                {"role": "assistant", "content": "Hello"},
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "How are you?"},
            ],
            job_listing=self.job_listing
        )
        self.client = Client()
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_restart_chat_post(self):
        """Test restarting a chat"""
        self.assertEqual(len(self.chat.messages), 4)

        response = self.client.post(
            reverse('chat-restart', args=[self.chat.id]),
            {'restart': 'true'}
        )

        self.assertRedirects(response, reverse(
            'chat-view', args=[self.chat.id]))

        # Check that chat was restarted
        self.chat.refresh_from_db()
        self.assertEqual(len(self.chat.messages), 2)

    def test_restart_chat_requires_ownership(self):
        """Test user can only restart their own chats"""
        User.objects.create_user(
            username='otheruser',
            password=TEST_PASSWORD
        )
        self.client.login(username='otheruser', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('chat-restart', args=[self.chat.id]),
            {'restart': 'true'}
        )
        self.assertEqual(response.status_code, 403)


class KeyQuestionsViewTest(TestCase):
    """Test key questions functionality"""

    def setUp(self):
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content='Job content',
            filename='job.txt'
        )
        self.resume = UploadedResume.objects.create(
            user=self.user,
            content='Resume content',
            title='My Resume'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            messages=[{"role": "system", "content": "System"}],
            job_listing=self.job_listing,
            resume=self.resume,
            key_questions=[
                {
                    "id": 0,
                    "title": "Python",
                    "duration": 60,
                    "content": "What is Python?"
                }
            ]
        )
        self.client = Client()
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_key_questions_get(self):
        """Test GET request to key questions view"""
        response = self.client.get(
            reverse('key-questions', args=[self.chat.id, 0])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'key-questions.html')
        self.assertIn('question', response.context)
        self.assertEqual(
            response.context['question']['content'], "What is Python?")

    @patch('active_interview_app.views.get_openai_client')
    @patch('active_interview_app.views.ai_available')
    def test_key_questions_post_with_resume(
            self, mockai_available, mock_get_client):
        """Test POST to key questions with resume"""
        mockai_available.return_value = True

        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Great answer! 8/10"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        data = {'message': 'Python is a programming language'}

        response = self.client.post(
            reverse('key-questions', args=[self.chat.id, 0]),
            data
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], "Great answer! 8/10")

    @patch('active_interview_app.views.ai_available')
    def test_key_questions_post_ai_unavailable(self, mockai_available):
        """Test POST to key questions when AI unavailable"""
        mockai_available.return_value = False

        data = {'message': 'Python is a programming language'}

        response = self.client.post(
            reverse('key-questions', args=[self.chat.id, 0]),
            data
        )

        self.assertEqual(response.status_code, 503)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)

    @patch('active_interview_app.views.get_openai_client')
    @patch('active_interview_app.views.ai_available')
    def test_key_questions_post_without_resume(
            self, mockai_available, mock_get_client):
        """Test POST to key questions without resume"""
        # Create chat without resume
        chat_no_resume = Chat.objects.create(
            owner=self.user,
            title='Test Chat No Resume',
            messages=[{"role": "system", "content": "System"}],
            job_listing=self.job_listing,
            resume=None,
            key_questions=[
                {
                    "id": 0,
                    "title": "Python",
                    "duration": 60,
                    "content": "What is Python?"
                }
            ]
        )

        mockai_available.return_value = True

        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Good answer! 7/10"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        data = {'message': 'Python is a programming language'}

        response = self.client.post(
            reverse('key-questions', args=[chat_no_resume.id, 0]),
            data
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], "Good answer! 7/10")


class EditChatViewTest(TestCase):
    """Test edit chat functionality"""

    def setUp(self):
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content='Job content',
            filename='job.txt'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Original Title',
            difficulty=5,
            type=Chat.GENERAL,
            messages=[
                {"role": "system", "content": "System prompt with difficulty <<5>>"}
            ],
            job_listing=self.job_listing
        )
        self.client = Client()
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_edit_chat_updates_difficulty_in_messages(self):
        """Test that difficulty update also updates messages"""
        data = {
            'update': 'true',
            'title': 'Updated Title',
            'difficulty': 8
        }

        response = self.client.post(
            reverse('chat-edit', args=[self.chat.id]),
            data
        )

        self.assertRedirects(response, reverse(
            'chat-view', args=[self.chat.id]))

        # Check that chat was updated
        self.chat.refresh_from_db()
        self.assertEqual(self.chat.title, 'Updated Title')
        self.assertEqual(self.chat.difficulty, 8)
        # Check that difficulty in messages was updated
        self.assertIn('<<8>>', self.chat.messages[0]['content'])
        self.assertNotIn('<<5>>', self.chat.messages[0]['content'])


class ChatViewPostTest(TestCase):
    """Test ChatView POST functionality"""

    def setUp(self):
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
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
                {"role": "system", "content": "System"}
            ],
            job_listing=self.job_listing
        )
        self.client = Client()
        self.client.login(username='testuser', password=TEST_PASSWORD)

    @patch('active_interview_app.views.get_openai_client')
    @patch('active_interview_app.views.ai_available')
    def test_chat_view_post(self, mockai_available, mock_get_client):
        """Test posting a message to chat"""
        mockai_available.return_value = True

        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "AI response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        data = {'message': 'User message'}

        response = self.client.post(
            reverse('chat-view', args=[self.chat.id]),
            data
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], "AI response")

        # Check that messages were saved
        self.chat.refresh_from_db()
        self.assertEqual(len(self.chat.messages), 3)
        self.assertEqual(self.chat.messages[1]['content'], 'User message')
        self.assertEqual(self.chat.messages[2]['content'], 'AI response')


class CreateChatViewComprehensiveTest(TestCase):
    """Comprehensive tests for CreateChat view covering all branches"""

    def setUp(self):
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content='Job description',
            filename='job.txt',
            title='Job Title'
        )
        self.resume = UploadedResume.objects.create(
            user=self.user,
            content='Resume content',
            title='Resume Title'
        )
        self.client = Client()
        self.client.login(username='testuser', password=TEST_PASSWORD)

    @patch('active_interview_app.views.get_openai_client')
    @patch('active_interview_app.views.ai_available')
    def test_create_chat_with_resume_all_types(
            self, mockai_available, mock_get_client):
        """Test creating chat with all interview types"""
        mockai_available.return_value = True

        # Mock OpenAI responses
        mock_client = Mock()

        for interview_type in [
                Chat.GENERAL,
                Chat.SKILLS,
                Chat.PERSONALITY,
                Chat.FINAL_SCREENING]:
            mock_response1 = Mock()
            mock_choice1 = Mock()
            mock_message1 = Mock()
            mock_message1.content = "Greeting message"
            mock_choice1.message = mock_message1
            mock_response1.choices = [mock_choice1]

            mock_response2 = Mock()
            mock_choice2 = Mock()
            mock_message2 = Mock()
            mock_message2.content = '[{"id": 0, "title": "Q1", "duration": 60, "content": "Question 1"}]'
            mock_choice2.message = mock_message2
            mock_response2.choices = [mock_choice2]

            mock_client.chat.completions.create.side_effect = [
                mock_response1, mock_response2]
            mock_get_client.return_value = mock_client

            data = {
                'create': 'true',
                'title': f'Chat {interview_type}',
                'type': interview_type,
                'difficulty': 5,
                'listing_choice': self.job_listing.id,
                'resume_choice': self.resume.id
            }

            response = self.client.post(reverse('chat-create'), data)
            self.assertEqual(response.status_code, 302)

            # Verify chat was created
            chat = Chat.objects.get(title=f'Chat {interview_type}')
            self.assertEqual(chat.type, interview_type)
            self.assertEqual(len(chat.key_questions), 1)

    @patch('active_interview_app.views.get_openai_client')
    @patch('active_interview_app.views.ai_available')
    def test_create_chat_key_questions_no_json_match(
            self, mockai_available, mock_get_client):
        """Test when key questions response doesn't match JSON pattern"""
        mockai_available.return_value = True

        # Mock OpenAI responses
        mock_client = Mock()
        mock_response1 = Mock()
        mock_choice1 = Mock()
        mock_message1 = Mock()
        mock_message1.content = "Greeting"
        mock_choice1.message = mock_message1
        mock_response1.choices = [mock_choice1]

        # Second response without valid JSON
        mock_response2 = Mock()
        mock_choice2 = Mock()
        mock_message2 = Mock()
        mock_message2.content = "This is not valid JSON"
        mock_choice2.message = mock_message2
        mock_response2.choices = [mock_choice2]

        mock_client.chat.completions.create.side_effect = [
            mock_response1, mock_response2]
        mock_get_client.return_value = mock_client

        data = {
            'create': 'true',
            'title': 'Chat No JSON',
            'type': Chat.GENERAL,
            'difficulty': 5,
            'listing_choice': self.job_listing.id,
            'resume_choice': self.resume.id
        }

        self.client.post(reverse('chat-create'), data)
        # Should still create chat but with empty key_questions
        chat = Chat.objects.get(title='Chat No JSON')
        self.assertEqual(chat.key_questions, [])


class UploadFileViewComprehensiveTest(TestCase):
    """Comprehensive file upload tests"""

    def setUp(self):
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client = Client()
        self.client.login(username='testuser', password=TEST_PASSWORD)

    @patch('active_interview_app.views.filetype')
    @patch('active_interview_app.views.pymupdf4llm')
    def test_upload_pdf_with_exception(self, mock_pymupdf, mock_filetype):
        """Test PDF upload when processing raises exception"""
        mock_file_type = Mock()
        mock_file_type.extension = 'pdf'
        mock_filetype.guess.return_value = mock_file_type

        # Mock PDF conversion to raise exception
        mock_pymupdf.to_markdown.side_effect = Exception(
            "PDF processing error")

        pdf_content = b'%PDF fake content'
        uploaded_file = SimpleUploadedFile(
            "error.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        data = {
            'title': 'Error PDF',
            'file': uploaded_file
        }

        response = self.client.post(reverse('upload_file'), data)

        # Should redirect with error
        self.assertRedirects(response, reverse('document-list'))

        # Resume should NOT be created
        self.assertFalse(UploadedResume.objects.filter(
            title='Error PDF').exists())

    @patch('active_interview_app.views.filetype')
    def test_upload_invalid_form(self, mock_filetype):
        """Test upload with invalid form"""
        # Don't provide required file
        data = {
            'title': 'No File'
        }

        response = self.client.post(reverse('upload_file'), data)

        # Should redirect with error message
        self.assertRedirects(response, reverse('document-list'))


class DocumentListViewTest(TestCase):
    """Test DocumentList view"""

    def setUp(self):
        """Set up test user"""
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            username='testuser', password=TEST_PASSWORD)
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_document_list_get(self):
        """Test GET request to document list"""
        response = self.client.get(reverse('document-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')


class ResultsChatViewComprehensiveTest(TestCase):
    """Comprehensive tests for ResultsChat view (not ResultCharts)"""

    def setUp(self):
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content='Job content',
            filename='job.txt'
        )
        # Note: There's a ResultsChat view that's not tested yet
        # It's different from ResultCharts


class AllInterviewTypesTest(TestCase):
    """Test get_type_display for all interview types"""

    def setUp(self):
        # Create average_role group (required by signals)
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name='average_role')

        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content='Job',
            filename='job.txt'
        )

    def test_all_interview_type_displays(self):
        """Test that all interview types have proper display names"""
        types_map = {
            Chat.GENERAL: "General",
            Chat.SKILLS: "Industry Skills",
            Chat.PERSONALITY: "Personality/Preliminary",
            Chat.FINAL_SCREENING: "Final Screening"
        }

        for type_code, expected_display in types_map.items():
            chat = Chat.objects.create(
                owner=self.user,
                title=f'Chat {type_code}',
                type=type_code,
                messages=[],
                job_listing=self.job_listing
            )
            self.assertEqual(chat.get_type_display(), expected_display)
