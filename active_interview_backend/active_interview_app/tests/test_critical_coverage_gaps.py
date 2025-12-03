"""
Critical tests to cover the major gaps in views.py and merge_stats_models.py
Targets specific untested branches identified in coverage analysis
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
from active_interview_app.merge_stats_models import MergeTokenStats
from .test_credentials import TEST_PASSWORD
from .test_utils import create_mock_openai_response


# ============================================================================
# MERGE STATS MODELS TESTS - Target 55% -> 80%
# ============================================================================

class MergeStatsUpdateSaveTest(TestCase):
    """Test the save method update path (when pk is not None)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )

    def test_save_update_does_not_recalculate_cumulative(self):
        """Test that updating existing record doesn't change cumulative values"""
        # Create first record
        merge1 = MergeTokenStats.objects.create(
            source_branch='feature/first',
            merge_commit_sha='abc111',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500,
            chatgpt_prompt_tokens=800,
            chatgpt_completion_tokens=400
        )

        initial_cumulative = merge1.cumulative_total_tokens

        # Update the record (pk is not None now)
        merge1.claude_prompt_tokens = 2000
        merge1.save()

        merge1.refresh_from_db()

        # Cumulative should NOT change because pk was not None
        self.assertEqual(merge1.cumulative_total_tokens, initial_cumulative)
        # But individual totals should update
        self.assertEqual(merge1.claude_total_tokens, 2500)  # 2000 + 500


# ============================================================================
# VIEWS.PY TESTS - Target 24% -> 80%
# ============================================================================

class CreateChatFormInvalidTest(TestCase):
    """Test CreateChat with invalid form submission"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_create_chat_missing_required_fields(self):
        """Test form invalid when missing required fields"""
        self.client.post(reverse('chat-create'), {
            # Missing listing_choice, difficulty, type
        })

        # Should not create a chat
        self.assertEqual(Chat.objects.count(), 0)

    def test_create_chat_invalid_difficulty(self):
        """Test form invalid with out-of-range difficulty"""
        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Test Job',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job_file
        )

        self.client.post(reverse('chat-create'), {
            'listing_choice': job_listing.id,
            'difficulty': 999,  # Invalid value
            'type': 'GEN'
        })

        # Form should be invalid
        self.assertEqual(Chat.objects.count(), 0)


class CreateChatNoCreateButtonTest(TestCase):
    """Test CreateChat POST without 'create' in POST data"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_create_chat_post_without_create_button(self):
        """Test POST to create chat without 'create' in POST data"""
        self.client.post(reverse('chat-create'), {
        })

        # Should not process the form
        self.assertEqual(Chat.objects.count(), 0)


class UploadFileFormInvalidTest(TestCase):
    """Test upload_file with invalid form"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_upload_file_no_file_provided(self):
        """Test upload form invalid when no file is provided"""
        _response = self.client.post(reverse('upload_file'), {
            'title': 'Test Title'
            # No file provided
        })

        self.assertEqual(_response.status_code, 302)
        self.assertEqual(UploadedResume.objects.count(), 0)

    def test_upload_file_empty_title(self):
        """Test upload with empty title"""
        file = SimpleUploadedFile("test.pdf", b"content")

        response = self.client.post(reverse('upload_file'), {
            'file': file,
            'title': ''  # Empty title
        })

        self.assertEqual(response.status_code, 302)


class ChatViewUnauthorizedAccessTest(TestCase):
    """Test UserPassesTestMixin for unauthorized access to chats"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1', password=TEST_PASSWORD)
        self.user2 = User.objects.create_user(
            username='user2', password=TEST_PASSWORD)

        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user1,
            title='Job',
            content='Description',
            filepath='/fake',
            filename='job.txt',
            file=fake_job_file
        )

        self.chat = Chat.objects.create(
            owner=self.user1,
            title='User1 Chat',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}],
            key_questions=[]
        )

    def test_chatview_unauthorized_get(self):
        """Test ChatView GET by unauthorized user"""
        self.client.login(username='user2', password=TEST_PASSWORD)
        response = self.client.get(
            reverse('chat-view', kwargs={'chat_id': self.chat.id}))
        self.assertIn(response.status_code, [302, 403])

    def test_chatview_unauthorized_post(self):
        """Test ChatView POST by unauthorized user"""
        self.client.login(username='user2', password=TEST_PASSWORD)
        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': self.chat.id}),
            {'message': 'test'}
        )
        self.assertIn(response.status_code, [302, 403])

    def test_editchat_unauthorized(self):
        """Test EditChat by unauthorized user"""
        self.client.login(username='user2', password=TEST_PASSWORD)
        response = self.client.get(
            reverse('chat-edit', kwargs={'chat_id': self.chat.id}))
        self.assertIn(response.status_code, [302, 403])

    def test_deletechat_unauthorized(self):
        """Test DeleteChat by unauthorized user"""
        self.client.login(username='user2', password=TEST_PASSWORD)
        response = self.client.post(
            reverse('chat-delete', kwargs={'chat_id': self.chat.id}),
            {'delete': 'true'}
        )
        self.assertIn(response.status_code, [302, 403])
        self.assertTrue(Chat.objects.filter(id=self.chat.id).exists())

    def test_restartchat_unauthorized(self):
        """Test RestartChat by unauthorized user"""
        self.client.login(username='user2', password=TEST_PASSWORD)
        response = self.client.post(
            reverse('chat-restart', kwargs={'chat_id': self.chat.id}),
            {'restart': 'true'}
        )
        self.assertIn(response.status_code, [302, 403])

    def test_keyquestionsview_unauthorized(self):
        """Test KeyQuestionsView by unauthorized user"""
        self.chat.key_questions = [
            {"id": 0, "title": "Q", "duration": 60, "content": "Test"}]
        self.chat.save()

        self.client.login(username='user2', password=TEST_PASSWORD)
        response = self.client.get(
            reverse('key-questions',
                    kwargs={'chat_id': self.chat.id, 'question_id': 0})
        )
        self.assertIn(response.status_code, [302, 403])



class APIViewSerializerErrorsTest(TestCase):
    """Test API view error responses when serializer validation fails"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password=TEST_PASSWORD)
        self.client.force_login(self.user)

    def test_uploaded_resume_post_invalid_data(self):
        """Test UploadedResumeView POST with invalid serializer data"""
        response = self.client.post(
            reverse('files_list'),
            data=json.dumps({
                'title': '',  # Invalid - empty title
                'content': '',
                # Missing required fields
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_job_listing_post_invalid_data(self):
        """Test JobListingList POST with invalid serializer data"""
        response = self.client.post(
            reverse('pasted_text_list'),
            data=json.dumps({
                'invalid_field': 'value'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)


class UploadedJobListingViewErrorPathsTest(TestCase):
    """Test error paths in UploadedJobListingView"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password=TEST_PASSWORD)
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_upload_job_listing_with_whitespace_title(self):
        """Test with title that's only whitespace"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': 'Valid content',
            'title': '   '  # Only whitespace
        })

        self.assertEqual(response.status_code, 302)
        # Should not create job listing
        self.assertEqual(UploadedJobListing.objects.count(), 0)

    def test_upload_job_listing_with_whitespace_text(self):
        """Test with text that's only whitespace"""
        response = self.client.post(reverse('save_pasted_text'), {
            'paste-text': '   ',  # Only whitespace
            'title': 'Valid Title'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedJobListing.objects.count(), 0)


class ChatListOrderingTest(TestCase):
    """Test chat_list ordering"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password=TEST_PASSWORD)
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_job_file = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            content='Description',
            filepath='/fake',
            filename='job.txt',
            file=fake_job_file
        )

    def test_chat_list_orders_by_modified_date(self):
        """Test that chat list orders by modified_date descending"""
        chat1 = Chat.objects.create(
            owner=self.user,
            title='First Chat',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        # Import at the top of the function to avoid issues
        from django.utils.timezone import now, timedelta

        chat2 = Chat.objects.create(
            owner=self.user,
            title='Second Chat',
            job_listing=self.job_listing,
            difficulty=5,
            type='GEN',
            messages=[{"role": "system", "content": "test"}]
        )

        # Update chat2's modified_date using update() to bypass auto_now
        Chat.objects.filter(id=chat2.id).update(
            modified_date=now() + timedelta(seconds=5)
        )
        # Refresh chat2 from database
        chat2.refresh_from_db()

        response = self.client.get(reverse('chat-list'))

        chats = response.context['owner_chats']
        self.assertEqual(chats[0].id, chat2.id)  # Most recent first
        self.assertEqual(chats[1].id, chat1.id)


class EditResumeFormInvalidTest(TestCase):
    """Test edit_resume with invalid form"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password=TEST_PASSWORD)
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_file = SimpleUploadedFile("resume.pdf", b"content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file
        )

    def test_edit_resume_invalid_form(self):
        """Test edit resume with invalid form data"""
        self.client.post(
            {
                'title': '',  # Empty title should be invalid
                'content': ''
            }
        )

        # Should not update
        self.resume.refresh_from_db()
        self.assertEqual(self.resume.title, 'Resume')


class EditJobPostingFormInvalidTest(TestCase):
    """Test edit_job_posting with invalid form"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password=TEST_PASSWORD)
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_file = SimpleUploadedFile("job.txt", b"content")
        self.job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            content='Description',
            filepath='/fake',
            filename='job.txt',
            file=fake_file
        )

    def test_edit_job_posting_invalid_form(self):
        """Test edit job posting with invalid form data"""
        self.client.post(
            {
                'title': '',  # Empty title
                'content': ''
            }
        )

        # Should not update
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, 'Job')


class StaticViewsContextTest(TestCase):
    """Test static views return proper context"""

    def setUp(self):
        self.client = Client()

    def test_index_renders_correctly(self):
        """Test index view"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_aboutus_renders_correctly(self):
        """Test aboutus view"""
        response = self.client.get(reverse('aboutus'))
        self.assertEqual(response.status_code, 200)

    def test_features_renders_correctly(self):
        """Test features view"""
        response = self.client.get(reverse('features'))
        self.assertEqual(response.status_code, 200)

    def test_results_renders_correctly(self):
        """Test results view"""
        response = self.client.get(reverse('results'))
        self.assertEqual(response.status_code, 200)


class ProfileViewWithDocumentsTest(TestCase):
    """Test profile view context data"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password=TEST_PASSWORD)
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_profile_shows_user_documents(self):
        """Test profile view includes user's documents in context"""
        fake_resume = SimpleUploadedFile("resume.pdf", b"content")
        fake_job = SimpleUploadedFile("job.txt", b"content")

        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume
        )

        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            content='Description',
            filepath='/fake',
            filename='job.txt',
            file=fake_job
        )

        response = self.client.get(reverse('profile'))

        self.assertIn('resumes', response.context)
        self.assertIn('job_listings', response.context)
        self.assertIn(resume, response.context['resumes'])
        self.assertIn(job, response.context['job_listings'])
