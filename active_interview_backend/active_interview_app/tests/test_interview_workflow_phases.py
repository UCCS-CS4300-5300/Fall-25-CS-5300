"""
Tests for Interview Workflow Phases 6-8 and Coverage Boost

This test file covers:
- Phase 6-7: Graceful ending with T-5 minute warning and auto-finalization
- Phase 7: Automatic invitation status updates
- Phase 8: Auto-finalization when all questions answered (practice interviews)
- FinalizeInterviewView
- Report generation workflow
- Exception handling in graceful ending (lines 613-619)
- _extract_rationales_from_chat method (lines 1863-1952)
- ChatCreate exception paths (lines 182-188, 193-198)
- UploadFileView GET for interviewers (lines 1349-1353)
- InvitedInterview.DoesNotExist exception paths

Related Issues: #137 (Interview Categorization), Interview Workflow Phases
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
import json

from active_interview_app.models import (
    UserProfile, Chat, InvitedInterview, InterviewTemplate,
    ExportableReport
)
from .test_credentials import TEST_PASSWORD

User = get_user_model()


class GracefulEndingTests(TestCase):
    """Test Phase 6-7: Graceful ending with T-5 minute warning"""

    def setUp(self):
        self.client = Client()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password=TEST_PASSWORD
        )
        self.interviewer.profile.role = 'interviewer'
        self.interviewer.profile.save()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )
        self.candidate.profile.role = 'candidate'
        self.candidate.profile.save()

        # Create interview template
        self.template = InterviewTemplate.objects.create(
            name='Test Template',
            description='Test',
            user=self.interviewer
        )

        # Create invited interview chat with less than 5 minutes remaining
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Invited Interview',
            type='GEN',
            interview_type=Chat.INVITED,
            difficulty=5,
            messages=[
                {"role": "system", "content": "Test"},
                {"role": "assistant", "content": "Hello"}
            ],
            started_at=timezone.now() - timedelta(minutes=56),
            scheduled_end_at=timezone.now() + timedelta(minutes=4)
        )

        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            template=self.template,
            candidate_email=self.candidate.email,
            scheduled_time=timezone.now() - timedelta(minutes=56),
            status=InvitedInterview.PENDING,
            chat=self.chat
        )

    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_client_and_model')
    @patch('active_interview_app.views.record_openai_usage')
    @patch('active_interview_app.invitation_utils.send_completion_notification_email')
    def test_graceful_ending_triggers_at_t_minus_5(
        self, mock_email, mock_usage, mock_client, mock_ai
    ):
        """Test that graceful ending triggers when less than 5 minutes remain"""
        # Mock AI availability
        mock_ai.return_value = True

        # Mock AI client for report generation
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="85"))]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        mock_client.return_value = (MagicMock(
            chat=MagicMock(
                completions=MagicMock(
                    create=MagicMock(return_value=mock_response)
                )
            )
        ), 'gpt-4', {'name': 'Premium', 'model': 'gpt-4'})

        self.client.login(username='candidate@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': self.chat.id}),
            data=json.dumps({'message': 'My answer'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Check graceful ending message
        # The response should have 'content' or 'message' key
        message_text = data.get('message') or data.get('content', '')
        self.assertIn('interview time window is ending', message_text.lower())
        self.assertIn('thank you', message_text.lower())

        # Refresh chat
        self.chat.refresh_from_db()

        # Verify auto-finalization
        self.assertTrue(self.chat.is_finalized)
        self.assertIsNotNone(self.chat.finalized_at)

        # Verify invitation status updated
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, InvitedInterview.COMPLETED)
        self.assertIsNotNone(self.invitation.completed_at)

        # Verify report was generated
        self.assertTrue(ExportableReport.objects.filter(chat=self.chat).exists())

    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_client_and_model')
    @patch('active_interview_app.views.record_openai_usage')
    def test_graceful_ending_does_not_trigger_before_t_minus_5(
        self, mock_usage, mock_client, mock_ai
    ):
        """Test that graceful ending doesn't trigger with more than 5 minutes remaining"""
        mock_ai.return_value = True

        # Mock AI response for normal conversation
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Good answer, let me ask another question."))]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        mock_client.return_value = (MagicMock(
            chat=MagicMock(
                completions=MagicMock(
                    create=MagicMock(return_value=mock_response)
                )
            )
        ), 'gpt-4', {'name': 'Premium', 'model': 'gpt-4'})

        # Update chat to have 6 minutes remaining
        self.chat.started_at = timezone.now() - timedelta(minutes=54)
        self.chat.scheduled_end_at = timezone.now() + timedelta(minutes=6)
        self.chat.save()

        self.client.login(username='candidate@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': self.chat.id}),
            data=json.dumps({'message': 'My answer'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should not contain graceful ending message
        self.assertNotIn('interview time window is ending', data['message'].lower())

        # Should not be finalized
        self.chat.refresh_from_db()
        self.assertFalse(self.chat.is_finalized)


class AutoFinalizationTests(TestCase):
    """Test Phase 8: Auto-finalization for practice interviews"""

    def setUp(self):
        self.client = Client()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )
        self.candidate.profile.role = 'candidate'
        self.candidate.profile.save()

        # Create practice interview with key questions
        # User has already answered first question, about to answer second
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Practice Interview',
            type='GEN',
            interview_type=Chat.PRACTICE,
            difficulty=5,
            messages=[
                {"role": "system", "content": "Test"},
                {"role": "assistant", "content": "Question 1?"},
                {"role": "user", "content": "Answer 1"},
                {"role": "assistant", "content": "Question 2?"}
            ],
            key_questions=[
                {
                    "id": 0,
                    "title": "Question 1",
                    "content": "First question",
                    "duration": 60,
                    "answered": True
                },
                {
                    "id": 1,
                    "title": "Question 2",
                    "content": "Second question",
                    "duration": 60,
                    "answered": True
                }
            ]
        )

    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_client_and_model')
    @patch('active_interview_app.views.record_openai_usage')
    def test_completion_signal_when_all_questions_answered(
        self, mock_usage, mock_client, mock_ai
    ):
        """Test that completion signal is sent when all practice questions answered"""
        mock_ai.return_value = True

        # Mock AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Thank you for your answer."))]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        mock_client.return_value = (MagicMock(
            chat=MagicMock(
                completions=MagicMock(
                    create=MagicMock(return_value=mock_response)
                )
            )
        ), 'gpt-4', {'name': 'Premium', 'model': 'gpt-4'})

        self.client.login(username='candidate@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': self.chat.id}),
            data=json.dumps({'message': 'Final answer'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Check for completion signal
        self.assertTrue(data.get('all_questions_answered', False))
        self.assertTrue(data.get('show_completion_message', False))


class FinalizeInterviewViewTests(TestCase):
    """Test FinalizeInterviewView functionality"""

    def setUp(self):
        self.client = Client()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )
        self.candidate.profile.role = 'candidate'
        self.candidate.profile.save()

        # Create practice interview
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Practice Interview',
            type='GEN',
            interview_type=Chat.PRACTICE,
            difficulty=5,
            messages=[
                {"role": "system", "content": "Test"},
                {"role": "assistant", "content": "Question?"},
                {"role": "user", "content": "Answer"}
            ]
        )

    def test_unauthorized_access_redirects(self):
        """Test that non-owners cannot finalize interviews"""
        other_user = User.objects.create_user(
            username='other@test.com',
            email='other@test.com',
            password=TEST_PASSWORD
        )

        self.client.login(username='other@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('finalize_interview', kwargs={'chat_id': self.chat.id})
        )

        # Should get forbidden or redirect
        self.assertIn(response.status_code, [302, 403])

    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_client_and_model')
    @patch('active_interview_app.views.record_openai_usage')
    def test_finalize_interview_generates_report(
        self, mock_usage, mock_client, mock_ai
    ):
        """Test that finalization generates report and marks chat as finalized"""
        mock_ai.return_value = True

        # Mock AI responses for report generation (4 calls)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="85"))]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        mock_client.return_value = (MagicMock(
            chat=MagicMock(
                completions=MagicMock(
                    create=MagicMock(return_value=mock_response)
                )
            )
        ), 'gpt-4', {'name': 'Premium', 'model': 'gpt-4'})

        self.client.login(username='candidate@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('finalize_interview', kwargs={'chat_id': self.chat.id})
        )

        # Should redirect to export report
        self.assertEqual(response.status_code, 302)
        self.assertIn('export-report', response.url)

        # Refresh chat
        self.chat.refresh_from_db()

        # Verify finalization
        self.assertTrue(self.chat.is_finalized)
        self.assertIsNotNone(self.chat.finalized_at)

        # Verify report exists
        self.assertTrue(ExportableReport.objects.filter(chat=self.chat).exists())

    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_client_and_model')
    @patch('active_interview_app.views.record_openai_usage')
    @patch('active_interview_app.invitation_utils.send_completion_notification_email')
    def test_finalize_invited_interview_updates_status(
        self, mock_email, mock_usage, mock_client, mock_ai
    ):
        """Test that finalizing invited interview updates invitation status"""
        mock_ai.return_value = True

        # Mock AI responses
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="85"))]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        mock_client.return_value = (MagicMock(
            chat=MagicMock(
                completions=MagicMock(
                    create=MagicMock(return_value=mock_response)
                )
            )
        ), 'gpt-4', {'name': 'Premium', 'model': 'gpt-4'})

        # Create interviewer and invitation
        interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password=TEST_PASSWORD
        )
        interviewer.profile.role = 'interviewer'
        interviewer.profile.save()

        template = InterviewTemplate.objects.create(
            name='Test Template',
            description='Test',
            user=interviewer
        )

        # Update chat to invited type
        self.chat.interview_type = Chat.INVITED
        self.chat.save()

        invitation = InvitedInterview.objects.create(
            interviewer=interviewer,
            template=template,
            candidate_email=self.candidate.email,
            scheduled_time=timezone.now(),
            status=InvitedInterview.PENDING,
            chat=self.chat
        )

        self.client.login(username='candidate@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('finalize_interview', kwargs={'chat_id': self.chat.id})
        )

        self.assertEqual(response.status_code, 302)

        # Verify invitation status updated
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitedInterview.COMPLETED)
        self.assertIsNotNone(invitation.completed_at)

        # Verify email sent
        mock_email.assert_called_once()

    def test_finalize_already_finalized_shows_message(self):
        """Test that attempting to finalize already finalized interview shows info message"""
        # Mark chat as finalized
        self.chat.is_finalized = True
        self.chat.finalized_at = timezone.now()
        self.chat.save()

        # Create a report
        ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=85,
            clarity_score=85,
            overall_score=85
        )

        self.client.login(username='candidate@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('finalize_interview', kwargs={'chat_id': self.chat.id}),
            follow=True
        )

        # Should redirect to export report
        self.assertEqual(response.status_code, 200)

        # Check for info message
        messages = list(response.context['messages'])
        self.assertTrue(
            any('already been finalized' in str(m) for m in messages)
        )


class GracefulEndingExceptionTests(TestCase):
    """Test exception handling in graceful ending (lines 613-619)"""

    def setUp(self):
        self.client = Client()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )
        self.candidate.profile.role = 'candidate'
        self.candidate.profile.save()

        # Create invited interview chat WITHOUT an InvitedInterview record
        # This will trigger the InvitedInterview.DoesNotExist exception
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Invited Interview',
            type='GEN',
            interview_type=Chat.INVITED,
            difficulty=5,
            messages=[
                {"role": "system", "content": "Test"},
                {"role": "assistant", "content": "Hello"}
            ],
            started_at=timezone.now() - timedelta(minutes=56),
            scheduled_end_at=timezone.now() + timedelta(minutes=4)  # Less than 5 mins
        )

    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_client_and_model')
    @patch('active_interview_app.views.record_openai_usage')
    def test_graceful_ending_without_invitation_record(
        self, mock_usage, mock_client, mock_ai
    ):
        """Test graceful ending when InvitedInterview.DoesNotExist (line 613-614)"""
        mock_ai.return_value = True

        # Mock AI client for report generation
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="85"))]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        mock_client.return_value = (MagicMock(
            chat=MagicMock(
                completions=MagicMock(
                    create=MagicMock(return_value=mock_response)
                )
            )
        ), 'gpt-4', {'name': 'Premium', 'model': 'gpt-4'})

        self.client.login(username='candidate@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': self.chat.id}),
            data=json.dumps({'message': 'My answer'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should still get graceful ending message
        message_text = data.get('content', '')
        self.assertIn('interview time window is ending', message_text.lower())

        # Verify auto-finalization happened despite missing invitation
        self.chat.refresh_from_db()
        self.assertTrue(self.chat.is_finalized)

        # Verify report was still generated
        self.assertTrue(ExportableReport.objects.filter(chat=self.chat).exists())

    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.report_utils.generate_and_save_report')
    def test_graceful_ending_report_generation_fails(
        self, mock_generate_report, mock_ai
    ):
        """Test graceful ending when report generation fails (lines 615-619)"""
        mock_ai.return_value = True

        # Mock report generation to raise an exception
        mock_generate_report.side_effect = Exception("Report generation failed")

        self.client.login(username='candidate@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('chat-view', kwargs={'chat_id': self.chat.id}),
            data=json.dumps({'message': 'My answer'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # Verify chat is still marked as finalized even though report generation failed
        self.chat.refresh_from_db()
        self.assertTrue(self.chat.is_finalized)
        self.assertIsNotNone(self.chat.finalized_at)


class ExtractRationalesTests(TestCase):
    """Test _extract_rationales_from_chat method via FinalizeInterviewView (lines 1863-1952)"""

    def setUp(self):
        self.client = Client()

        # Create user
        self.user = User.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            password=TEST_PASSWORD
        )

        # Create chat
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            type='GEN',
            interview_type=Chat.PRACTICE,
            difficulty=5,
            messages=[
                {"role": "system", "content": "Test"},
                {"role": "assistant", "content": "Question?"},
                {"role": "user", "content": "Answer"}
            ]
        )

    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_client_and_model')
    @patch('active_interview_app.views.record_openai_usage')
    def test_extract_rationales_via_finalize(
        self, mock_usage, mock_client, mock_ai
    ):
        """Test rationales extraction via FinalizeInterviewView"""
        mock_ai.return_value = True

        # Mock AI response with properly formatted rationales
        rationale_response = MagicMock()
        rationale_response.choices = [MagicMock(message=MagicMock(content="""
Professionalism: The candidate demonstrated excellent professionalism.

Subject Knowledge: Strong understanding of the subject matter.

Clarity: Responses were clear and well-articulated.

Overall: Excellent performance overall.
        """))]
        rationale_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )

        # Mock other AI responses for the full report generation
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="85\n80\n90\n85"))]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )

        # Return different responses based on call order
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.side_effect = [
            mock_response,  # scores
            mock_response,  # feedback
            rationale_response,  # rationales
        ]
        mock_client.return_value = (
            mock_client_instance,
            'gpt-4',
            {'name': 'Premium', 'model': 'gpt-4'}
        )

        self.client.login(username='user@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('finalize_interview', kwargs={'chat_id': self.chat.id})
        )

        # Should succeed
        self.assertEqual(response.status_code, 302)

        # Check report has rationales
        report = ExportableReport.objects.get(chat=self.chat)
        self.assertIsNotNone(report.professionalism_rationale)
        self.assertIsNotNone(report.subject_knowledge_rationale)
        self.assertIsNotNone(report.clarity_rationale)
        self.assertIsNotNone(report.overall_rationale)


class FinalizeInvitedInterviewWithoutInvitationTests(TestCase):
    """Test FinalizeInterviewView with invited chat but no InvitedInterview record"""

    def setUp(self):
        self.client = Client()

        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )

        # Create INVITED chat WITHOUT InvitedInterview record
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Invited Interview',
            type='GEN',
            interview_type=Chat.INVITED,
            difficulty=5,
            messages=[
                {"role": "system", "content": "Test"},
                {"role": "assistant", "content": "Question?"},
                {"role": "user", "content": "Answer"}
            ]
        )

    @patch('active_interview_app.views.ai_available')
    @patch('active_interview_app.views.get_client_and_model')
    @patch('active_interview_app.views.record_openai_usage')
    def test_finalize_invited_missing_invitation(
        self, mock_usage, mock_client, mock_ai
    ):
        """Test finalize when InvitedInterview doesn't exist"""
        mock_ai.return_value = True

        # Mock AI responses
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="85"))]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        mock_client.return_value = (MagicMock(
            chat=MagicMock(
                completions=MagicMock(
                    create=MagicMock(return_value=mock_response)
                )
            )
        ), 'gpt-4', {'name': 'Premium', 'model': 'gpt-4'})

        self.client.login(username='candidate@test.com', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('finalize_interview', kwargs={'chat_id': self.chat.id})
        )

        # Should still succeed despite missing InvitedInterview
        self.assertEqual(response.status_code, 302)

        # Verify report was created
        self.assertTrue(ExportableReport.objects.filter(chat=self.chat).exists())

        # Verify chat is finalized
        self.chat.refresh_from_db()
        self.assertTrue(self.chat.is_finalized)


class ChatCreateExceptionTests(TestCase):
    """Test exception paths in ChatCreate view"""

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            password=TEST_PASSWORD
        )
        self.user.profile.role = 'candidate'
        self.user.profile.save()

    def test_chat_create_with_invalid_job_id(self):
        """Test ChatCreate GET with invalid job_id (lines 182-188)"""
        self.client.login(username='user@test.com', password=TEST_PASSWORD)

        # Request with non-existent job_id
        response = self.client.get(reverse('chat-create'), {'job_id': 99999})

        # Should still render successfully, just ignoring invalid job_id
        self.assertEqual(response.status_code, 200)

        # Form should not have listing_choice pre-selected
        form = response.context['form']
        self.assertNotIn('listing_choice', form.initial)

    def test_chat_create_with_invalid_template_id(self):
        """Test ChatCreate GET with invalid template_id (lines 193-198)"""
        self.client.login(username='user@test.com', password=TEST_PASSWORD)

        # Request with non-existent template_id
        response = self.client.get(reverse('chat-create'), {'template_id': 99999})

        # Should still render successfully
        self.assertEqual(response.status_code, 200)

        # Suggested template should be None
        self.assertIsNone(response.context.get('suggested_template'))

    def test_chat_create_with_both_invalid_params(self):
        """Test ChatCreate GET with both invalid job_id and template_id"""
        self.client.login(username='user@test.com', password=TEST_PASSWORD)

        response = self.client.get(
            reverse('chat-create'),
            {'job_id': 99999, 'template_id': 88888}
        )

        # Should still render successfully
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('suggested_template'))


class UploadFileViewTests(TestCase):
    """Test GET path in UploadFileView for interviewers"""

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            password=TEST_PASSWORD
        )

    def test_upload_file_view_get_for_interviewer(self):
        """Test UploadFileView GET for interviewer shows templates (lines 1349-1353)"""
        # Make user an interviewer
        self.user.profile.role = 'interviewer'
        self.user.profile.save()

        # Create a template
        template = InterviewTemplate.objects.create(
            name='Test Template',
            description='Test',
            user=self.user
        )

        self.client.login(username='user@test.com', password=TEST_PASSWORD)

        response = self.client.get(reverse('document-list'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('templates', response.context)
        self.assertIn(template, response.context['templates'])
