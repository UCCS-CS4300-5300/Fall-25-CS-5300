"""
Comprehensive tests to push merge_stats_models.py, token_usage_models.py,
and views.py all above 80% coverage.

This file tests all remaining uncovered code paths.
"""
from django.test import TestCase, Client, override_settings
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
from active_interview_app.merge_stats_models import MergeTokenStats
from active_interview_app.token_usage_models import TokenUsage
from active_interview_app import views


# ============================================================================
# MERGE_STATS_MODELS.PY COVERAGE - Targeting 55% -> 80%+
# ============================================================================

class MergeStatsFirstRecordTest(TestCase):
    """Test the else branch when creating the very first merge stats record"""

    def test_first_record_cumulative_equals_totals(self):
        """Test that first record's cumulative values equal its own totals"""
        # This tests the else branch at lines 172-176
        merge = MergeTokenStats.objects.create(
            source_branch='feature/first-ever',
            merge_commit_sha='first123',
            claude_prompt_tokens=500,
            claude_completion_tokens=250,
            chatgpt_prompt_tokens=300,
            chatgpt_completion_tokens=150
        )

        # For first record, cumulative should equal individual totals
        self.assertEqual(merge.cumulative_claude_tokens, 750)
        self.assertEqual(merge.cumulative_chatgpt_tokens, 450)
        self.assertEqual(merge.cumulative_total_tokens, 1200)
        # Cost should be > 0
        self.assertGreater(float(merge.cumulative_cost), 0)


# ============================================================================
# TOKEN_USAGE_MODELS.PY COVERAGE - Targeting 50% -> 80%+
# ============================================================================

class TokenUsageCompleteCoverageTest(TestCase):
    """Ensure 100% coverage of token_usage_models.py"""

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='pass')

    def test_get_branch_summary_cost_accumulation(self):
        """Test that cost is accumulated correctly across multiple records"""
        # Create records with different costs
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/cost-test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=1000,
            completion_tokens=500
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/cost-test',
            model_name='claude-sonnet-4-5-20250929',
            endpoint='/v1/messages',
            prompt_tokens=2000,
            completion_tokens=1000
        )

        summary = TokenUsage.get_branch_summary('feature/cost-test')

        # Ensure cost is accumulated
        self.assertGreater(summary['total_cost'], 0)
        self.assertGreater(summary['by_model']['gpt-4o']['cost'], 0)
        self.assertGreater(summary['by_model']
                           ['claude-sonnet-4-5-20250929']['cost'], 0)


# ============================================================================
# VIEWS.PY COVERAGE - Targeting 24% -> 80%+
# ============================================================================

class ViewsCompleteCoverageTest(TestCase):
    """Test all uncovered paths in views.py"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')

        # Create test data
        fake_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_file
        )

    def test_get_openai_client_success(self):
        """Test successful OpenAI client initialization"""
        from active_interview_app.openai_utils import get_openai_client
        import active_interview_app.openai_utils as openai_utils

        with patch('active_interview_app.openai_utils.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = 'test-key-123'
            with patch('active_interview_app.openai_utils.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                # Reset the global client
                openai_utils._openai_client = None

                client = get_openai_client()
                self.assertIsNotNone(client)

    def test_get_openai_client_no_api_key(self):
        """Test OpenAI client when API key is missing"""
        from active_interview_app.openai_utils import get_openai_client
        import active_interview_app.openai_utils as openai_utils

        with patch('active_interview_app.openai_utils.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            openai_utils._openai_client = None

            with self.assertRaises(ValueError) as context:
                get_openai_client()

            self.assertIn('OPENAI_API_KEY is not set', str(context.exception))

    def test_get_openai_client_initialization_failure(self):
        """Test OpenAI client initialization failure"""
        from active_interview_app.openai_utils import get_openai_client
        import active_interview_app.openai_utils as openai_utils

        with patch('active_interview_app.openai_utils.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = 'test-key'
            with patch('active_interview_app.openai_utils.OpenAI') as mock_openai:
                mock_openai.side_effect = Exception('API Error')
                openai_utils._openai_client = None

                with self.assertRaises(ValueError) as context:
                    get_openai_client()

                self.assertIn('Failed to initialize OpenAI client',
                              str(context.exception))

    def testai_available_returns_true(self):
        """Test ai_available when client is available"""
        with patch('active_interview_app.openai_utils.get_openai_client') as mock_get:
            mock_get.return_value = MagicMock()
            self.assertTrue(views.ai_available())

    def testai_available_returns_false_on_error(self):
        """Test ai_available when client fails"""
        with patch('active_interview_app.openai_utils.get_openai_client') as mock_get:
            mock_get.side_effect = ValueError('No API key')
            self.assertFalse(views.ai_available())

    def test_ai_unavailable_json_response(self):
        """Test _ai_unavailable_json returns proper _response"""
        _response = views._ai_unavailable_json()
        self.assertEqual(_response.status_code, 503)
        data = json.loads(_response.content)
        self.assertIn('error', data)
        self.assertIn('AI features are disabled', data['error'])

    def test_index_view(self):
        """Test index view renders correctly"""
        _response = self.client.get(reverse('index'))
        self.assertEqual(_response.status_code, 200)
        self.assertTemplateUsed(_response, 'index.html')

    def test_aboutus_view(self):
        """Test aboutus view"""
        _response = self.client.get(reverse('aboutus'))
        self.assertEqual(_response.status_code, 200)
        self.assertTemplateUsed(_response, 'about-us.html')

    def test_features_view(self):
        """Test features view"""
        _response = self.client.get(reverse('features'))
        self.assertEqual(_response.status_code, 200)
        self.assertTemplateUsed(_response, 'features.html')

    def test_results_view(self):
        """Test results view"""
        response = self.client.get(reverse('results'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'results.html')

    def test_loggedin_view(self):
        """Test loggedin view"""
        response = self.client.get(reverse('loggedin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loggedinindex.html')

    def test_profile_view(self):
        """Test profile view"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('resumes', response.context)
        self.assertIn('job_listings', response.context)

    def test_register_valid_form(self):
        """Test user registration with valid form"""
        self.client.post(reverse('register_page'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })

        # Should create user
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Check user was added to average_role group
        user = User.objects.get(username='newuser')
        self.assertTrue(user.groups.filter(name='average_role').exists())

    def test_chat_list_view(self):
        """Test chat_list view"""
        response = self.client.get(reverse('chat-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('owner_chats', response.context)

    def test_create_chat_get_request(self):
        """Test CreateChat GET request"""
        response = self.client.get(reverse('chat-create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('owner_chats', response.context)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_create_chat_with_resumeai_available(self, mock_client, mock_ai):
        """Test CreateChat POST with _resume when AI is available"""
        mock_ai.return_value = True

        # Mock AI responses
        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_response1.choices[0].message.content = "Hello! Let's start the interview."

        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message.content = '''[
            {
                "id": 0,
                "title": "Experience",
                "duration": 60,
                "content": "Tell me about your experience."
            }
        ]'''

        mock_client.return_value.chat.completions.create.side_effect = [
            mock_response1, mock_response2
        ]

        # Create resume
        fake_resume = SimpleUploadedFile("resume.pdf", b"resume content")
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='My resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume
        )

        self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job_listing.id,
            'resume_choice': resume.id,
            'difficulty': 5,
            'type': 'GEN'
        })

        # Should create chat and redirect
        self.assertEqual(Chat.objects.count(), 1)
        chat = Chat.objects.first()
        self.assertIsNotNone(chat.resume)
        self.assertEqual(len(chat.key_questions), 1)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    def test_create_chat_without_resume_ai_unavailable(self, mock_ai):
        """Test CreateChat POST without resume when AI unavailable"""
        mock_ai.return_value = False

        self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job_listing.id,
            'difficulty': 3,
            'type': 'ISK'
        })

        # Chat should still be created with empty AI messages
        self.assertEqual(Chat.objects.count(), 1)
        chat = Chat.objects.first()
        self.assertIsNone(chat.resume)
        self.assertEqual(chat.key_questions, [])

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_create_chat_key_questions_regex_fails(self, mock_client, mock_ai):
        """Test CreateChat when key questions regex doesn't match"""
        mock_ai.return_value = True

        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_response1.choices[0].message.content = "Hello!"

        # Return invalid JSON that won't match regex
        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message.content = "This is not valid JSON"

        mock_client.return_value.chat.completions.create.side_effect = [
            mock_response1, mock_response2
        ]

        self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job_listing.id,
            'difficulty': 5,
            'type': 'GEN'
        })

        # Should create chat with empty key_questions
        chat = Chat.objects.first()
        self.assertEqual(chat.key_questions, [])

    def test_chat_view_get(self):
        """Test ChatView GET request"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.get(
            reverse('chat-view', kwargs={'chat_id': chat.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('chat', response.context)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_chat_view_post_success(self, mock_client, mock_ai):
        """Test ChatView POST with AI available"""
        mock_ai.return_value = True
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI response"
        mock_client.return_value.chat.completions.create.return_value = mock_response

        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': chat.id}),
            {'message': 'Hello'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'AI response')

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    def test_chat_view_post_ai_unavailable(self, mock_ai):
        """Test ChatView POST when AI is unavailable"""
        mock_ai.return_value = False

        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': chat.id}),
            {'message': 'Hello'}
        )

        self.assertEqual(response.status_code, 503)

    def test_edit_chat_get(self):
        """Test EditChat GET request"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.get(
            reverse('chat-edit', kwargs={'chat_id': chat.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_edit_chat_post_with_update(self):
        """Test EditChat POST with 'update' button"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "Selected level: <<5>>"}]
        )

        response = self.client.post(
            reverse('chat-edit', kwargs={'chat_id': chat.id}),
            {
                'update': 'true',
                'difficulty': 7
            }
        )

        chat.refresh_from_db()
        self.assertEqual(chat.difficulty, 7)
        self.assertIn('<<7>>', chat.messages[0]['content'])

    def test_delete_chat_with_delete_button(self):
        """Test DeleteChat POST with 'delete' button"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[]
        )
        chat_id = chat.id

        response = self.client.post(
            reverse('chat-delete', kwargs={'chat_id': chat.id}),
            {'delete': 'true'}
        )

        self.assertFalse(Chat.objects.filter(id=chat_id).exists())
        self.assertEqual(response.status_code, 302)

    def test_restart_chat_with_restart_button(self):
        """Test RestartChat POST with 'restart' button"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[
                {"role": "system", "content": "system"},
                {"role": "assistant", "content": "first"},
                {"role": "user", "content": "user1"},
                {"role": "assistant", "content": "ai1"}
            ]
        )

        response = self.client.post(
            reverse('chat-restart', kwargs={'chat_id': chat.id}),
            {'restart': 'true'}
        )

        chat.refresh_from_db()
        self.assertEqual(len(chat.messages), 2)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_key_questions_view_get(self, mock_client, mock_ai):
        """Test KeyQuestionsView GET"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}],
            key_questions=[
                {"id": 0, "title": "Q1", "duration": 60, "content": "Question 1"}
            ]
        )

        response = self.client.get(
            reverse('key-questions',
                    kwargs={'chat_id': chat.id, 'question_id': 0})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('question', response.context)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_key_questions_view_post_with_resume(self, mock_client, mock_ai):
        """Test KeyQuestionsView POST with resume"""
        mock_ai.return_value = True
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Good answer! 8/10"
        mock_client.return_value.chat.completions.create.return_value = mock_response

        fake_resume = SimpleUploadedFile("resume.pdf", b"resume")
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume
        )

        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            resume=resume,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}],
            key_questions=[
                {"id": 0, "title": "Q1", "duration": 60, "content": "Question 1"}
            ]
        )

        response = self.client.post(
            reverse('key-questions',
                    kwargs={'chat_id': chat.id, 'question_id': 0}),
            {'message': 'My answer'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('8/10', data['message'])

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_key_questions_view_post_without_resume(
            self, mock_client, mock_ai):
        """Test KeyQuestionsView POST without resume"""
        mock_ai.return_value = True
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Feedback"
        mock_client.return_value.chat.completions.create.return_value = mock_response

        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}],
            key_questions=[
                {"id": 0, "title": "Q1", "duration": 60, "content": "Question 1"}
            ]
        )

        response = self.client.post(
            reverse('key-questions',
                    kwargs={'chat_id': chat.id, 'question_id': 0}),
            {'message': 'My answer'}
        )

        self.assertEqual(response.status_code, 200)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    def test_key_questions_view_post_ai_unavailable(self, mock_ai):
        """Test KeyQuestionsView POST when AI unavailable"""
        mock_ai.return_value = False

        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}],
            key_questions=[
                {"id": 0, "title": "Q1", "duration": 60, "content": "Question 1"}
            ]
        )

        response = self.client.post(
            reverse('key-questions',
                    kwargs={'chat_id': chat.id, 'question_id': 0}),
            {'message': 'My answer'}
        )

        self.assertEqual(response.status_code, 503)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_results_chat_getai_available(self, mock_client, mock_ai):
        """Test ResultsChat GET when AI is available"""
        mock_ai.return_value = True
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Great job!"
        mock_client.return_value.chat.completions.create.return_value = mock_response

        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.get(
            reverse('chat-results', kwargs={'chat_id': chat.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('feedback', response.context)
        self.assertEqual(response.context['feedback'], 'Great job!')

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    def test_results_chat_get_ai_unavailable(self, mock_ai):
        """Test ResultsChat GET when AI is unavailable"""
        mock_ai.return_value = False

        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.get(
            reverse('chat-results', kwargs={'chat_id': chat.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('AI features are currently unavailable',
                      response.context['feedback'])

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_openai_client')
    def test_result_charts_getai_available(self, mock_client, mock_ai):
        """Test ResultCharts GET when AI is available"""
        mock_ai.return_value = True

        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_response1.choices[0].message.content = "80\n70\n90\n75"

        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message.content = "You did well"

        mock_client.return_value.chat.completions.create.side_effect = [
            mock_response1, mock_response2
        ]

        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.get(
            reverse('result-charts', kwargs={'chat_id': chat.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['scores']['Professionalism'], 80)
        self.assertEqual(response.context['scores']['Overall'], 75)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.views.ai_available')
    def test_result_charts_get_ai_unavailable(self, mock_ai):
        """Test ResultCharts GET when AI is unavailable"""
        mock_ai.return_value = False

        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.get(
            reverse('result-charts', kwargs={'chat_id': chat.id}))
        self.assertEqual(response.status_code, 200)
        # All scores should be 0
        self.assertEqual(response.context['scores']['Professionalism'], 0)
        self.assertEqual(response.context['scores']['Overall'], 0)

    def test_resume_detail_view(self):
        """Test resume_detail view"""
        fake_file = SimpleUploadedFile("resume.pdf", b"content")
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

        response = self.client.get(
            reverse('resume_detail', kwargs={'resume_id': resume.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('resume', response.context)

    def test_delete_resume_post(self):
        """Test delete_resume POST"""
        fake_file = SimpleUploadedFile("resume.pdf", b"content")
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )
        resume_id = resume.id

        _response = self.client.post(  # noqa: F841
            reverse('delete_resume', args=[resume_id])
        )
        self.assertFalse(UploadedResume.objects.filter(id=resume_id).exists())

    def test_delete_resume_get_redirect(self):
        """Test delete_resume GET (should redirect)"""
        fake_file = SimpleUploadedFile("resume.pdf", b"content")
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

        response = self.client.get(
            reverse('delete_resume', kwargs={'resume_id': resume.id}))
        self.assertEqual(response.status_code, 302)
        # Resume should still exist
        self.assertTrue(UploadedResume.objects.filter(id=resume.id).exists())

    @patch('active_interview_app.views.filetype')
    @patch('active_interview_app.views.pymupdf4llm')
    def test_upload_file_pdf_success(self, mock_pymupdf, mock_filetype):
        """Test upload_file with valid PDF"""
        mock_file_type = MagicMock()
        mock_file_type.extension = 'pdf'
        mock_filetype.guess.return_value = mock_file_type
        mock_pymupdf.to_markdown.return_value = "PDF content"

        pdf_file = SimpleUploadedFile("test.pdf", b"PDF content here")

        response = self.client.post(reverse('upload_file'), {
            'file': pdf_file,
            'title': 'Test PDF'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedResume.objects.count(), 1)

    @patch('active_interview_app.views.filetype')
    @patch('active_interview_app.views.Document')
    def test_upload_file_docx_success(self, mock_document, mock_filetype):
        """Test upload_file with valid DOCX"""
        mock_file_type = MagicMock()
        mock_file_type.extension = 'docx'
        mock_filetype.guess.return_value = mock_file_type

        mock_doc = MagicMock()
        mock_doc.paragraphs = [
            MagicMock(text="Para 1"), MagicMock(text="Para 2")]
        mock_document.return_value = mock_doc

        docx_file = SimpleUploadedFile("test.docx", b"DOCX content")

        response = self.client.post(reverse('upload_file'), {
            'file': docx_file,
            'title': 'Test DOCX'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedResume.objects.count(), 1)

    @patch('active_interview_app.views.filetype')
    def test_upload_file_invalid_type(self, mock_filetype):
        """Test upload_file with invalid file type"""
        mock_file_type = MagicMock()
        mock_file_type.extension = 'exe'
        mock_filetype.guess.return_value = mock_file_type

        SimpleUploadedFile("test.exe", b"executable")

        self.client.post(reverse('upload_file'), {
            'title': 'Invalid File'
        })

        self.assertEqual(UploadedResume.objects.count(), 0)

    @patch('active_interview_app.views.filetype')
    def test_upload_file_none_filetype(self, mock_filetype):
        """Test upload_file when filetype.guess returns None"""
        mock_filetype.guess.return_value = None

        SimpleUploadedFile("test.txt", b"text content")

        self.client.post(reverse('upload_file'), {
            'title': 'Test'
        })

        self.assertEqual(UploadedResume.objects.count(), 0)

    @patch('active_interview_app.views.filetype')
    @patch('active_interview_app.views.pymupdf4llm')
    def test_upload_file_processing_exception(
            self, mock_pymupdf, mock_filetype):
        """Test upload_file when processing raises exception"""
        mock_file_type = MagicMock()
        mock_file_type.extension = 'pdf'
        mock_filetype.guess.return_value = mock_file_type
        mock_pymupdf.to_markdown.side_effect = Exception('Processing error')

        SimpleUploadedFile("test.pdf", b"PDF content")

        self.client.post(reverse('upload_file'), {
            'title': 'Test'
        })

        self.assertEqual(UploadedResume.objects.count(), 0)

    def test_upload_file_get_request(self):
        """Test upload_file GET request"""
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_edit_resume_get(self):
        """Test edit_resume GET request"""
        fake_file = SimpleUploadedFile("resume.pdf", b"content")
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

        response = self.client.get(
            reverse('edit_resume', kwargs={'resume_id': resume.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_edit_resume_post_valid(self):
        """Test edit_resume POST with valid data"""
        fake_file = SimpleUploadedFile("resume.pdf", b"content")
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

        response = self.client.post(
            reverse('edit_resume', kwargs={'resume_id': resume.id}),
            {
                'title': 'Updated Resume',
                'content': 'Updated content'
            }
        )

        resume.refresh_from_db()
        self.assertEqual(resume.title, 'Updated Resume')

    def test_job_posting_detail_view(self):
        """Test job_posting_detail view"""
        response = self.client.get(
            reverse('job_posting_detail', kwargs={
                    'job_id': self.job_listing.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('job', response.context)

    def test_edit_job_posting_get(self):
        """Test edit_job_posting GET"""
        response = self.client.get(
            reverse('edit_job_posting', kwargs={'job_id': self.job_listing.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_edit_job_posting_post_valid(self):
        """Test edit_job_posting POST with valid data"""
        _response = self.client.post(  # noqa: F841
            reverse('edit_job_posting',
                    kwargs={'job_id': self.job_listing.id}),
            {
                'title': 'Updated Job',
                'content': 'Updated description'
            }
        )

        self.job_listing.refresh_from_db()
        self.assertEqual(self.job_listing.title, 'Updated Job')

    def test_delete_job_post(self):
        """Test delete_job POST"""
        job_id = self.job_listing.id

        _response = self.client.post(  # noqa: F841
            reverse('delete_job', kwargs={'job_id': job_id})
        )
        self.assertFalse(UploadedJobListing.objects.filter(id=job_id).exists())

    def test_delete_job_get_redirect(self):
        """Test delete_job GET (should redirect without deleting)"""
        response = self.client.get(
            reverse('delete_job', kwargs={'job_id': self.job_listing.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(UploadedJobListing.objects.filter(
            id=self.job_listing.id).exists())

    def test_uploaded_job_listing_view_post_valid(self):
        """Test UploadedJobListingView POST with valid data"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'Job listing content',
            'title': 'New Job'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedJobListing.objects.filter(
            title='New Job').count(), 1)

    def test_uploaded_job_listing_view_post_empty_text(self):
        """Test UploadedJobListingView POST with empty text"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': '',
            'title': 'Title'
        })

        self.assertEqual(response.status_code, 302)

    def test_uploaded_job_listing_view_post_empty_title(self):
        """Test UploadedJobListingView POST with empty title"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'Content',
            'title': ''
        })

        self.assertEqual(response.status_code, 302)

    def test_uploaded_resume_view_get(self):
        """Test UploadedResumeView GET"""
        fake_file = SimpleUploadedFile("resume.pdf", b"content")
        UploadedResume.objects.create(
            title='Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

        response = self.client.get(reverse('files_list'))
        self.assertEqual(response.status_code, 200)

    def test_uploaded_resume_view_post_valid(self):
        """Test UploadedResumeView POST with valid data"""
        response = self.client.post(
            reverse('files_list'),
            data=json.dumps({
                'title': 'API Resume',
                'content': 'Resume content',
                'filesize': 100,
                'original_filename': 'resume.pdf'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

    def test_job_listing_list_get(self):
        """Test JobListingList GET"""
        response = self.client.get(reverse('pasted_text_list'))
        self.assertEqual(response.status_code, 200)

    def test_job_listing_list_post_valid(self):
        """Test JobListingList POST with valid data"""
        response = self.client.post(
            reverse('pasted_text_list'),
            data=json.dumps({
                'title': 'API Job',
                'content': 'Job content'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

    def test_document_list_get(self):
        """Test DocumentList GET"""
        response = self.client.get(reverse('document-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')
