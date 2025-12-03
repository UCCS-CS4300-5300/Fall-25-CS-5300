"""
Tests to boost views.py coverage to >80%
Focuses on untested methods and code paths
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from active_interview_app.models import Chat, ExportableReport, UploadedJobListing, UploadedResume
from .test_utils import create_mock_openai_response


class DownloadCSVTest(TestCase):
    """Test CSV download functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123')
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=7,
            messages=[],
            type='GEN'
        )

    def test_download_csv_with_job_and_resume(self):
        """Test CSV includes job listing and resume"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Senior Dev',
            filename='job.pdf',
            content='Description'
        )
        resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Content',
            original_filename='resume.pdf'
        )
        self.chat.job_listing = job
        self.chat.resume = resume
        self.chat.save()

        ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            overall_score=80,
            professionalism_rationale='Good',
            total_questions_asked=10,
            total_responses_given=10,
            interview_duration_minutes=30
        )

        self.client.login(username='testuser', password='pass123')
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Senior Dev', content)
        self.assertIn('My Resume', content)
        self.assertIn('30 minutes', content)

    def test_download_csv_score_ratings(self):
        """Test CSV includes correct score ratings"""
        ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=95,  # Excellent
            subject_knowledge_score=82,  # Good
            clarity_score=68,  # Fair
            overall_score=80,
            total_questions_asked=5,
            total_responses_given=5
        )

        self.client.login(username='testuser', password='pass123')
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        content = response.content.decode('utf-8')
        self.assertIn('Excellent', content)
        self.assertIn('Good', content)
        self.assertIn('Fair', content)


class SimpleViewsTest(TestCase):
    """Test simple static views"""

    def setUp(self):
        self.client = Client()

    def test_index_view(self):
        """Test index page"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_aboutus_view(self):
        """Test about us page"""
        response = self.client.get(reverse('aboutus'))
        self.assertEqual(response.status_code, 200)

    def test_features_view(self):
        """Test features page"""
        response = self.client.get(reverse('features'))
        self.assertEqual(response.status_code, 200)


class ChatManagementViewsTest(TestCase):
    """Test chat CRUD operations"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123')

    def test_chat_list_view(self):
        """Test chat list"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('chat-list'))
        self.assertEqual(response.status_code, 200)

    def test_delete_chat_view(self):
        """Test delete chat"""
        self.client.login(username='testuser', password='pass123')
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        url = reverse('chat-delete', kwargs={'chat_id': chat.id})
        response = self.client.post(url, {'delete': 'true'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Chat.objects.filter(id=chat.id).exists())

    def test_restart_chat_view(self):
        """Test restart chat"""
        self.client.login(username='testuser', password='pass123')
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[
                {'role': 'system', 'content': 'System'},
                {'role': 'assistant', 'content': 'Hi'},
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'How?'}
            ],
            type='GEN'
        )
        url = reverse('chat-restart', kwargs={'chat_id': chat.id})
        response = self.client.post(url, {'restart': 'true'})
        self.assertEqual(response.status_code, 302)
        chat.refresh_from_db()
        self.assertEqual(len(chat.messages), 2)

    def test_edit_chat_get(self):
        """Test edit chat GET"""
        self.client.login(username='testuser', password='pass123')
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[{'role': 'system', 'content': 'Test <<5>>'}],
            type='GEN'
        )
        url = reverse('chat-edit', kwargs={'chat_id': chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_chat_post_update(self):
        """Test edit chat POST with update"""
        self.client.login(username='testuser', password='pass123')
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[{'role': 'system', 'content': 'Test <<5>>'}],
            type='GEN'
        )
        url = reverse('chat-edit', kwargs={'chat_id': chat.id})
        response = self.client.post(url, {
            'update': 'true',
            'title': 'Updated',
            'difficulty': 7
        })
        self.assertEqual(response.status_code, 302)
        chat.refresh_from_db()
        self.assertEqual(chat.difficulty, 7)
        self.assertIn('<<7>>', chat.messages[0]['content'])

    def test_edit_chat_post_no_update(self):
        """Test edit chat POST without update button"""
        self.client.login(username='testuser', password='pass123')
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        url = reverse('chat-edit', kwargs={'chat_id': chat.id})
        response = self.client.post(url, {'title': 'Ignored'})
        self.assertEqual(response.status_code, 302)


class UserManagementViewsTest(TestCase):
    """Test user-related views"""

    def setUp(self):
        self.client = Client()

    def test_register_get(self):
        """Test registration page"""
        response = self.client.get(reverse('register_page'))
        self.assertEqual(response.status_code, 200)

    def test_register_post_valid(self):
        """Test valid registration"""
        response = self.client.post(reverse('register_page'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_profile_view(self):
        """Test profile page"""
        _user = User.objects.create_user(  # noqa: F841
            username='testuser',
            password='pass123'
        )
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_loggedin_view(self):
        """Test logged in view"""
        _user = User.objects.create_user(  # noqa: F841
            username='testuser',
            password='pass123'
        )
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('loggedin'))
        self.assertEqual(response.status_code, 200)

    def test_view_user_profile_own(self):
        """Test viewing own profile"""
        user = User.objects.create_user(
            username='testuser', password='pass123')
        self.client.login(username='testuser', password='pass123')
        url = reverse('view_user_profile', kwargs={'user_id': user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_own_profile'])

    def test_view_user_profile_other(self):
        """Test viewing other user's profile without permission"""
        _user1 = User.objects.create_user(  # noqa: F841
            username='user1',
            password='pass123'
        )
        _user2 = User.objects.create_user(
            username='user2',
            password='pass123'
        )
        self.client.login(username='user1', password='pass123')
        url = reverse('view_user_profile', kwargs={'user_id': _user2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_view_user_profile_notfound(self):
        """Test viewing non-existent profile"""
        _user = User.objects.create_user(  # noqa: F841
            username='testuser',
            password='pass123'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('view_user_profile', kwargs={'user_id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class DocumentViewsTest(TestCase):
    """Test document-related views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123')

    def test_resume_detail(self):
        """Test resume detail view"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Content',
            original_filename='resume.pdf'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('resume_detail', kwargs={'resume_id': resume.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_owner'])

    def test_delete_resume(self):
        """Test delete resume"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Test',
            content='Content',
            original_filename='test.pdf'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('delete_resume', kwargs={'resume_id': resume.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(UploadedResume.objects.filter(id=resume.id).exists())

    def test_edit_resume_get(self):
        """Test edit resume GET"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Original',
            content='Content',
            original_filename='resume.pdf'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('edit_resume', kwargs={'resume_id': resume.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_resume_post(self):
        """Test edit resume POST"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Original',
            content='Content',
            original_filename='resume.pdf'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('edit_resume', kwargs={'resume_id': resume.id})
        response = self.client.post(url, {
            'title': 'Updated',
            'content': 'New content'
        })
        self.assertEqual(response.status_code, 302)

    def test_job_posting_detail(self):
        """Test job posting detail"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            filename='job.pdf',
            content='Content'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('job_posting_detail', kwargs={'job_id': job.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_job(self):
        """Test delete job"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            filename='job.pdf',
            content='Content'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('delete_job', kwargs={'job_id': job.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_edit_job_posting_get(self):
        """Test edit job GET"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Original',
            filename='job.pdf',
            content='Content'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('edit_job_posting', kwargs={'job_id': job.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_job_posting_post(self):
        """Test edit job POST"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Original',
            filename='job.pdf',
            content='Content'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('edit_job_posting', kwargs={'job_id': job.id})
        response = self.client.post(url, {
            'title': 'Updated',
            'content': 'New'
        })
        self.assertEqual(response.status_code, 302)

    def test_document_list_view(self):
        """Test document list"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('document-list'))
        self.assertEqual(response.status_code, 200)

    def test_uploaded_job_listing_post_empty_text(self):
        """Test posting empty text"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': '',
            'title': 'Test'
        })
        self.assertEqual(response.status_code, 302)

    def test_uploaded_job_listing_post_empty_title(self):
        """Test posting empty title"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'Some text',
            'title': ''
        })
        self.assertEqual(response.status_code, 302)

    def test_uploaded_job_listing_post_valid(self):
        """Test posting valid job listing"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'Job description',
            'title': 'Job Title'
        })
        self.assertEqual(response.status_code, 302)


class KeyQuestionsViewTest(TestCase):
    """Test key questions view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123')

    def test_key_questions_get(self):
        """Test key questions GET"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN',
            key_questions=[{'id': 0, 'title': 'Q1',
                            'content': 'Question?', 'duration': 60}]
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('key-questions',
                      kwargs={'chat_id': chat.id, 'question_id': 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_key_questions_with_resume(self):
        """Test key questions with resume"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            original_filename='resume.pdf'
        )
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN',
            resume=resume,
            key_questions=[{'id': 0, 'content': 'Q?', 'duration': 60}]
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('key-questions',
                      kwargs={'chat_id': chat.id, 'question_id': 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_key_questions_without_resume(self):
        """Test key questions without resume"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN',
            key_questions=[{'id': 0, 'content': 'Q?', 'duration': 60}]
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('key-questions',
                      kwargs={'chat_id': chat.id, 'question_id': 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @patch('active_interview_app.views.ai_available', return_value=False)
    def test_key_questions_post_ai_unavailable(self, mock_ai):
        """Test key questions POST when AI unavailable"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            filename='job.pdf',
            content='Job content'
        )
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN',
            job_listing=job,
            key_questions=[{'id': 0, 'content': 'Q?', 'duration': 60}]
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('key-questions',
                      kwargs={'chat_id': chat.id, 'question_id': 0})
        response = self.client.post(url, {'message': 'Answer'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 503)


class ChatViewPostTest(TestCase):
    """Test ChatView POST method"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123')

    @patch('active_interview_app.views.ai_available', return_value=False)
    def test_chat_view_post_ai_unavailable(self, mock_ai):
        """Test chat POST when AI unavailable"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('chat-view', kwargs={'chat_id': chat.id})
        response = self.client.post(url, {'message': 'Hello'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 503)


class CreateChatViewTest(TestCase):
    """Test CreateChat view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123')

    def test_create_chat_get(self):
        """Test CreateChat GET"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('chat-create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    @patch('active_interview_app.views.ai_available', return_value=True)
    @patch('active_interview_app.views.get_client_and_model')
    def test_create_chat_post_with_resume(self, mock_get_client_and_model, mock_ai):
        """Test CreateChat POST with resume"""
        # Mock AI responses
        mock_response = create_mock_openai_response("Hello! Let's begin the interview.")

        mock_questions_response = create_mock_openai_response('[{"id": 0, "title": "Q1", "content": "Question?", "duration": 60}]')

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            mock_response,
            mock_questions_response
        ]
        # get_client_and_model returns (client, model, tier_info)
        mock_get_client_and_model.return_value = (mock_client, "gpt-4o", {"tier": "premium"})

        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            filename='job.pdf',
            content='Job content'
        )
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Resume content',
            original_filename='resume.pdf'
        )
        self.client.login(username='testuser', password='pass123')
        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'title': 'Test Interview',
            'listing_choice': job.id,
            'resume_choice': resume.id,
            'difficulty': 5,
            'type': 'GEN'
        })
        # Should redirect after creation
        self.assertEqual(response.status_code, 302)
        # Check chat was created
        self.assertTrue(Chat.objects.filter(title='Test Interview').exists())

    @patch('active_interview_app.views.ai_available', return_value=True)
    @patch('active_interview_app.views.get_client_and_model')
    def test_create_chat_post_without_resume(self, mock_get_client_and_model, mock_ai):
        """Test CreateChat POST without resume"""
        # Mock AI responses
        mock_response = create_mock_openai_response("Hello! Let's begin the interview.")

        mock_questions_response = create_mock_openai_response('[{"id": 0, "title": "Q1", "content": "Question?", "duration": 60}]')

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            mock_response,
            mock_questions_response
        ]
        # get_client_and_model returns (client, model, tier_info)
        mock_get_client_and_model.return_value = (mock_client, "gpt-4o", {"tier": "premium"})

        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            filename='job.pdf',
            content='Job content'
        )
        self.client.login(username='testuser', password='pass123')
        response = self.client.post(reverse('chat-create'), {
            'create': 'true',
            'title': 'No Resume Interview',
            'listing_choice': job.id,
            'difficulty': 7,
            'type': 'ISK'
        })
        self.assertEqual(response.status_code, 302)


class UploadFileViewTest(TestCase):
    """Test upload_file view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123')

    def test_upload_file_get(self):
        """Test upload file GET"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)


class ExportViewsTest(TestCase):
    """Test export views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123')
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        self.report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80,
            total_questions_asked=10,
            total_responses_given=10
        )

    def test_export_report_view(self):
        """Test ExportReportView"""
        self.client.login(username='testuser', password='pass123')
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_pdf_report_view(self):
        """Test DownloadPDFReportView"""
        self.client.login(username='testuser', password='pass123')
        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_download_pdf_no_report(self):
        """Test downloading PDF when no report exists"""
        chat2 = Chat.objects.create(
            owner=self.user,
            title='No Report',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        self.client.login(username='testuser', password='pass123')
        url = reverse('download_pdf_report', kwargs={'chat_id': chat2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class APIViewsTest(TestCase):
    """Test API views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123')

    def test_job_listing_list_get(self):
        """Test JobListingList GET"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('pasted_text_list'))
        self.assertEqual(response.status_code, 200)

    def test_job_listing_list_post(self):
        """Test JobListingList POST"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.post(reverse('pasted_text_list'), {
            'title': 'API Job',
            'content': 'API Job Content'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)
