"""
Focused tests to boost coverage for the 3 failing files to 80%+
Simplified and targeted to ensure they actually run.
"""
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock, Mock
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
# MERGE_STATS_MODELS - Hit the else branch at lines 172-176
# ============================================================================

class MergeStatsFirstRecordCoverageTest(TestCase):
    """Test first record creation to hit else branch"""

    def test_very_first_merge_stat_record(self):
        """First record with no previous - hits else branch lines 172-176"""
        # Ensure no records exist
        MergeTokenStats.objects.all().delete()

        # Create first ever record
        merge = MergeTokenStats.objects.create(
            source_branch='feature/initial',
            merge_commit_sha='first_commit_sha',
            claude_prompt_tokens=100,
            claude_completion_tokens=50,
            chatgpt_prompt_tokens=80,
            chatgpt_completion_tokens=40
        )

        # Verify cumulative equals individual for first record
        self.assertEqual(merge.cumulative_claude_tokens, 150)
        self.assertEqual(merge.cumulative_chatgpt_tokens, 120)
        self.assertEqual(merge.cumulative_total_tokens, 270)
        self.assertGreater(float(merge.cumulative_cost), 0)


# ============================================================================
# TOKEN_USAGE_MODELS - Cover all code paths
# ============================================================================

class TokenUsageCoverageBoostTest(TestCase):
    """Ensure all token usage model paths are covered"""

    def setUp(self):
        self.user = User.objects.create_user(username='tokenuser', password='pass')

    def test_get_branch_summary_cost_paths(self):
        """Test cost calculation paths in get_branch_summary"""
        # Create records to test cost accumulation
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/costs',
            model_name='gpt-4o',
            endpoint='/v1/chat',
            prompt_tokens=1000,
            completion_tokens=500
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/costs',
            model_name='claude-sonnet-4-5-20250929',
            endpoint='/v1/messages',
            prompt_tokens=2000,
            completion_tokens=1000
        )

        summary = TokenUsage.get_branch_summary('feature/costs')

        # Test all paths are hit
        self.assertGreater(summary['total_cost'], 0)
        self.assertGreater(summary['by_model']['gpt-4o']['cost'], 0)
        self.assertGreater(summary['by_model']['claude-sonnet-4-5-20250929']['cost'], 0)
        self.assertEqual(summary['total_tokens'], 4500)

    def test_estimated_cost_all_model_types(self):
        """Test estimated_cost for different model types"""
        # GPT-4o
        gpt_usage = TokenUsage.objects.create(
            git_branch='test',
            model_name='gpt-4o',
            endpoint='/api',
            prompt_tokens=1000,
            completion_tokens=1000
        )
        self.assertAlmostEqual(gpt_usage.estimated_cost, 0.09, places=2)

        # Claude Sonnet 4.5
        claude_usage = TokenUsage.objects.create(
            git_branch='test',
            model_name='claude-sonnet-4-5-20250929',
            endpoint='/api',
            prompt_tokens=1000,
            completion_tokens=1000
        )
        self.assertAlmostEqual(claude_usage.estimated_cost, 0.018, places=3)

        # Claude Sonnet 4
        claude4_usage = TokenUsage.objects.create(
            git_branch='test',
            model_name='claude-sonnet-4',
            endpoint='/api',
            prompt_tokens=1000,
            completion_tokens=1000
        )
        self.assertAlmostEqual(claude4_usage.estimated_cost, 0.018, places=3)

        # Unknown model (uses default)
        unknown_usage = TokenUsage.objects.create(
            git_branch='test',
            model_name='unknown-model',
            endpoint='/api',
            prompt_tokens=1000,
            completion_tokens=1000
        )
        self.assertAlmostEqual(unknown_usage.estimated_cost, 0.09, places=2)


# ============================================================================
# VIEWS.PY - Cover critical uncovered paths
# ============================================================================

class ViewsCriticalPathsTest(TransactionTestCase):
    """Cover the most critical uncovered paths in views.py"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='viewuser', password='testpass')
        self.client.login(username='viewuser', password='testpass')

        # Create test job listing
        fake_file = SimpleUploadedFile("job.txt", b"job content")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            content='Description',
            filepath='/fake',
            filename='job.txt',
            file=fake_file
        )

    def test_get_openai_client_functions(self):
        """Test get_openai_client and related functions"""
        with patch('active_interview_app.openai_utils.settings') as mock_settings:
            # Test missing API key
            mock_settings.OPENAI_API_KEY = None
            import active_interview_app.openai_utils as openai_utils; openai_utils._openai_client = None
            with self.assertRaises(ValueError):
                views.get_openai_client()

            # Test successful initialization
            mock_settings.OPENAI_API_KEY = 'test-key'
            with patch('active_interview_app.openai_utils.OpenAI') as mock_openai:
                mock_openai.return_value = MagicMock()
                import active_interview_app.openai_utils as openai_utils; openai_utils._openai_client = None
                client = views.get_openai_client()
                self.assertIsNotNone(client)

            # Test initialization error
            mock_settings.OPENAI_API_KEY = 'test-key'
            with patch('active_interview_app.openai_utils.OpenAI') as mock_openai:
                mock_openai.side_effect = Exception('Init failed')
                import active_interview_app.openai_utils as openai_utils; openai_utils._openai_client = None
                with self.assertRaises(ValueError):
                    views.get_openai_client()

    def testai_available_and_unavailable(self):
        """Test ai_available and _ai_unavailable_json"""
        # Test ai_available returns True
        with patch('active_interview_app.openai_utils.get_openai_client', return_value=MagicMock()):
            self.assertTrue(views.ai_available())

        # Test ai_available returns False
        with patch('active_interview_app.openai_utils.get_openai_client', side_effect=ValueError()):
            self.assertFalse(views.ai_available())

        # Test _ai_unavailable_json
        response = views._ai_unavailable_json()
        self.assertEqual(response.status_code, 503)

    def test_static_views(self):
        """Test all static views"""
        self.assertEqual(self.client.get(reverse('index')).status_code, 200)
        self.assertEqual(self.client.get(reverse('aboutus')).status_code, 200)
        self.assertEqual(self.client.get(reverse('features')).status_code, 200)
        self.assertEqual(self.client.get(reverse('results')).status_code, 200)
        self.assertEqual(self.client.get(reverse('loggedin')).status_code, 200)

    def test_register_user(self):
        """Test user registration"""
        self.client.logout()
        response = self.client.post(reverse('register_page'), {
            'username': 'newuser123',
            'email': 'new@test.com',
            'password1': 'SuperSecure123!',
            'password2': 'SuperSecure123!',
        })

        # Check user created and added to group
        user = User.objects.get(username='newuser123')
        self.assertTrue(user.groups.filter(name='average_role').exists())

    @patch('active_interview_app.views.ai_available', return_value=True)
    @patch('active_interview_app.views.get_client_and_model')
    def test_create_chat_with_ai(self, mock_get_client, mock_ai):
        """Test CreateChat with AI available"""
        mock_resp1 = MagicMock()
        mock_resp1.choices = [MagicMock()]
        mock_resp1.choices[0].message.content = "Hello"

        mock_resp2 = MagicMock()
        mock_resp2.choices = [MagicMock()]
        mock_resp2.choices[0].message.content = '[{"id":0,"title":"Q","duration":60,"content":"Q1"}]'

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [mock_resp1, mock_resp2]
        mock_get_client.return_value = (mock_client, 'gpt-4o', {'tier': 'premium'})

        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job.id,
            'difficulty': 5,
            'type': 'GEN'
        })

        self.assertEqual(Chat.objects.count(), 1)

    @patch('active_interview_app.views.ai_available', return_value=False)
    def test_create_chat_without_ai(self, mock_ai):
        """Test CreateChat when AI unavailable"""
        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job.id,
            'difficulty': 5,
            'type': 'GEN'
        })

        # Should still create chat
        self.assertEqual(Chat.objects.count(), 1)

    @patch('active_interview_app.views.ai_available', return_value=True)
    @patch('active_interview_app.views.get_client_and_model')
    def test_create_chat_regex_failure(self, mock_get_client, mock_ai):
        """Test CreateChat when regex doesn't match"""
        mock_resp1 = MagicMock()
        mock_resp1.choices = [MagicMock()]
        mock_resp1.choices[0].message.content = "Hello"

        mock_resp2 = MagicMock()
        mock_resp2.choices = [MagicMock()]
        mock_resp2.choices[0].message.content = "Not valid JSON"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [mock_resp1, mock_resp2]
        mock_get_client.return_value = (mock_client, 'gpt-4o', {'tier': 'premium'})

        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'listing_choice': self.job.id,
            'difficulty': 5,
            'type': 'GEN'
        })

        chat = Chat.objects.first()
        self.assertEqual(chat.key_questions, [])

    @patch('active_interview_app.views.ai_available', return_value=True)
    @patch('active_interview_app.views.get_client_and_model')
    def test_chat_view_post(self, mock_get_client, mock_ai):
        """Test ChatView POST"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "Response"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get_client.return_value = (mock_client, 'gpt-4o', {'tier': 'premium'})

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': chat.id}),
            {'message': 'Hello'}
        )
        self.assertEqual(response.status_code, 200)

    @patch('active_interview_app.views.ai_available', return_value=False)
    def test_chat_view_post_no_ai(self, mock_ai):
        """Test ChatView POST without AI"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': chat.id}),
            {'message': 'Hello'}
        )
        self.assertEqual(response.status_code, 503)

    def test_edit_chat_post(self):
        """Test EditChat POST with update"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "Selected level: <<5>>"}]
        )

        self.client.post(
            reverse('chat-edit', kwargs={'chat_id': chat.id}),
            {'update': 'true', 'difficulty': 7}
        )

        chat.refresh_from_db()
        self.assertEqual(chat.difficulty, 7)

    def test_delete_chat(self):
        """Test DeleteChat"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job,
            difficulty=5,
            type='GEN',
            messages=[]
        )
        chat_id = chat.id

        self.client.post(
            reverse('chat-delete', kwargs={'chat_id': chat_id}),
            {'delete': 'true'}
        )

        self.assertFalse(Chat.objects.filter(id=chat_id).exists())

    def test_restart_chat(self):
        """Test RestartChat"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job,
            difficulty=5,
            type='GEN',
            messages=[
                {"role": "system", "content": "sys"},
                {"role": "assistant", "content": "first"},
                {"role": "user", "content": "user"},
                {"role": "assistant", "content": "ai"}
            ]
        )

        self.client.post(
            reverse('chat-restart', kwargs={'chat_id': chat.id}),
            {'restart': 'true'}
        )

        chat.refresh_from_db()
        self.assertEqual(len(chat.messages), 2)

    @patch('active_interview_app.views.ai_available', return_value=True)
    @patch('active_interview_app.views.get_client_and_model')
    def test_key_questions_view(self, mock_get_client, mock_ai):
        """Test KeyQuestionsView"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}],
            key_questions=[{"id": 0, "title": "Q", "duration": 60, "content": "Q1"}]
        )

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "Feedback"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get_client.return_value = (mock_client, 'gpt-4o', {'tier': 'premium'})

        response = self.client.post(
            reverse('key-questions', kwargs={'chat_id': chat.id, 'question_id': 0}),
            {'message': 'Answer'}
        )
        self.assertEqual(response.status_code, 200)

    @patch('active_interview_app.views.ai_available', return_value=True)
    @patch('active_interview_app.views.get_client_and_model')
    def test_results_chat(self, mock_get_client, mock_ai):
        """Test ResultsChat"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "Feedback"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get_client.return_value = (mock_client, 'gpt-4o', {'tier': 'premium'})

        response = self.client.get(reverse('chat-results', kwargs={'chat_id': chat.id}))
        self.assertEqual(response.status_code, 200)

    @patch('active_interview_app.views.ai_available', return_value=False)
    def test_results_chat_no_ai(self, mock_ai):
        """Test ResultsChat without AI"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        response = self.client.get(reverse('chat-results', kwargs={'chat_id': chat.id}))
        self.assertIn('unavailable', response.context['feedback'])

    @patch('active_interview_app.views.ai_available', return_value=True)
    @patch('active_interview_app.views.get_client_and_model')
    def test_result_charts(self, mock_get_client, mock_ai):
        """Test ResultCharts"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            job_listing=self.job,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        mock_resp1 = MagicMock()
        mock_resp1.choices = [MagicMock()]
        mock_resp1.choices[0].message.content = "80\n70\n90\n75"

        mock_resp2 = MagicMock()
        mock_resp2.choices = [MagicMock()]
        mock_resp2.choices[0].message.content = "Good"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [mock_resp1, mock_resp2]
        mock_get_client.return_value = (mock_client, 'gpt-4o', {'tier': 'premium'})

        response = self.client.get(reverse('result-charts', kwargs={'chat_id': chat.id}))
        self.assertEqual(response.context['scores']['Professionalism'], 80)

    @patch('active_interview_app.views.filetype')
    @patch('active_interview_app.views.pymupdf4llm')
    def test_upload_file_pdf(self, mock_pdf, mock_filetype):
        """Test upload_file with PDF"""
        mock_ft = MagicMock()
        mock_ft.extension = 'pdf'
        mock_filetype.guess.return_value = mock_ft
        mock_pdf.to_markdown.return_value = "Content"

        pdf = SimpleUploadedFile("test.pdf", b"PDF")
        response = self.client.post(reverse('upload_file'), {
            'file': pdf,
            'title': 'Test'
        })

        self.assertEqual(UploadedResume.objects.count(), 1)

    @patch('active_interview_app.views.filetype')
    @patch('active_interview_app.views.Document')
    def test_upload_file_docx(self, mock_doc, mock_filetype):
        """Test upload_file with DOCX"""
        mock_ft = MagicMock()
        mock_ft.extension = 'docx'
        mock_filetype.guess.return_value = mock_ft

        mock_d = MagicMock()
        mock_d.paragraphs = [MagicMock(text="Text")]
        mock_doc.return_value = mock_d

        docx = SimpleUploadedFile("test.docx", b"DOCX")
        response = self.client.post(reverse('upload_file'), {
            'file': docx,
            'title': 'Test'
        })

        self.assertEqual(UploadedResume.objects.count(), 1)

    @patch('active_interview_app.views.filetype')
    def test_upload_file_invalid(self, mock_filetype):
        """Test upload_file with invalid type"""
        mock_ft = MagicMock()
        mock_ft.extension = 'exe'
        mock_filetype.guess.return_value = mock_ft

        exe = SimpleUploadedFile("test.exe", b"EXE")
        self.client.post(reverse('upload_file'), {
            'file': exe,
            'title': 'Test'
        })

        self.assertEqual(UploadedResume.objects.count(), 0)

    def test_document_operations(self):
        """Test various document operations"""
        fake = SimpleUploadedFile("resume.pdf", b"content")
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake
        )

        # Test resume_detail
        self.assertEqual(
            self.client.get(reverse('resume_detail', kwargs={'resume_id': resume.id})).status_code,
            200
        )

        # Test delete_resume
        self.client.post(reverse('delete_resume', kwargs={'resume_id': resume.id}))
        self.assertFalse(UploadedResume.objects.filter(id=resume.id).exists())

    def test_job_operations(self):
        """Test job listing operations"""
        # Test job_posting_detail
        self.assertEqual(
            self.client.get(reverse('job_posting_detail', kwargs={'job_id': self.job.id})).status_code,
            200
        )

        # Test delete_job
        job_id = self.job.id
        self.client.post(reverse('delete_job', kwargs={'job_id': job_id}))
        self.assertFalse(UploadedJobListing.objects.filter(id=job_id).exists())

    def test_uploaded_job_listing_view(self):
        """Test UploadedJobListingView"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'Content',
            'title': 'Title'
        })

        self.assertEqual(UploadedJobListing.objects.filter(title='Title').count(), 1)

    def test_api_views(self):
        """Test API views"""
        # GET files_list
        self.assertEqual(self.client.get(reverse('files_list')).status_code, 200)

        # GET pasted_text_list
        self.assertEqual(self.client.get(reverse('pasted_text_list')).status_code, 200)

        # GET document-list
        self.assertEqual(self.client.get(reverse('document-list')).status_code, 200)
