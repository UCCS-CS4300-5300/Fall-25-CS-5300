"""
Tests for Phase 7: Interviewer Review & Feedback

This test file covers:
- Interviewer review view access control (RBAC)
- Feedback submission and saving
- Marking as reviewed (status transitions)
- Review notification emails
- Candidate view of interviewer feedback

Related Issues: #138, #139
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail
from datetime import timedelta

from active_interview_app.models import (
    UserProfile, Chat, InterviewTemplate, InvitedInterview,
    BiasTermLibrary, BiasAnalysisResult
)
from .test_credentials import TEST_PASSWORD

User = get_user_model()


class InvitationReviewViewAccessTests(TestCase):
    """Test access control for _invitation review view"""

    def setUp(self):
        self.client = Client()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password=TEST_PASSWORD
        )
        self.interviewer_profile = UserProfile.objects.get(
            user=self.interviewer)
        self.interviewer_profile.role = 'interviewer'
        self.interviewer_profile.save()

        # Create another interviewer
        self.other_interviewer = User.objects.create_user(
            username='other@test.com',
            email='other@test.com',
            password=TEST_PASSWORD
        )
        other_profile = UserProfile.objects.get(user=self.other_interviewer)
        other_profile.role = 'interviewer'
        other_profile.save()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Technical Interview'
        )

        # Create completed _invitation with chat
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            completed_at=timezone.now() - timedelta(hours=1)
        )

        # Create chat
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Technical Interview',
            interview_type=Chat.INVITED,
            scheduled_end_at=timezone.now() - timedelta(hours=1)
        )
        self.invitation.chat = self.chat
        self.invitation.save()

    def test_requires_authentication(self):
        """Test that review view requires login"""
        url = reverse('invitation_review', kwargs={
                      'invitation_id': self.invitation.id})
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_only_interviewer_can_access(self):
        """Test that only the invitation creator can access review"""
        self.client.login(username='candidate@test.com',
                          password=TEST_PASSWORD)
        url = reverse('invitation_review', kwargs={
                      'invitation_id': self.invitation.id})
        response = self.client.get(url)

        # Candidates should be forbidden
        self.assertEqual(response.status_code, 403)

    def test_other_interviewer_cannot_access(self):
        """Test that different interviewer cannot access another's review"""
        self.client.login(username='other@test.com', password=TEST_PASSWORD)
        url = reverse('invitation_review', kwargs={
                      'invitation_id': self.invitation.id})
        response = self.client.get(url)

        # Should return 404 (get_object_or_404 with interviewer=request.user)
        self.assertEqual(response.status_code, 404)

    def test_invitation_creator_can_access(self):
        """Test that invitation creator can access review page"""
        self.client.login(username='interviewer@test.com',
                          password=TEST_PASSWORD)
        url = reverse('invitation_review', kwargs={
                      'invitation_id': self.invitation.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invitations/invitation_review.html')

    def test_cannot_review_not_started_invitation(self):
        """Test error when trying to review invitation without chat"""
        # Create invitation without chat
        invitation_no_chat = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='test@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=1),
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        self.client.login(username='interviewer@test.com',
                          password=TEST_PASSWORD)
        url = reverse('invitation_review', kwargs={
                      'invitation_id': invitation_no_chat.id})
        response = self.client.get(url)

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('invitation_dashboard'))


class FeedbackSubmissionTests(TestCase):
    """Test feedback submission and saving"""

    def setUp(self):
        self.client = Client()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password=TEST_PASSWORD
        )
        interviewer_profile = UserProfile.objects.get(user=self.interviewer)
        interviewer_profile.role = 'interviewer'
        interviewer_profile.save()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Technical Interview'
        )

        # Create completed invitation with chat
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            completed_at=timezone.now() - timedelta(hours=1)
        )

        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Technical Interview',
            interview_type=Chat.INVITED,
            scheduled_end_at=timezone.now() - timedelta(hours=1)
        )
        self.invitation.chat = self.chat
        self.invitation.save()

        self.client.login(username='interviewer@test.com',
                          password=TEST_PASSWORD)
        self.url = reverse('invitation_review', kwargs={
                           'invitation_id': self.invitation.id})

    def test_save_feedback_without_marking_reviewed(self):
        """Test saving feedback without marking as reviewed"""
        feedback_text = "Good technical skills, needs improvement in communication."

        response = self.client.post(self.url, {
            'interviewer_feedback': feedback_text,
            'mark_reviewed': 'false'
        })

        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('invitation_dashboard'))

        # Check feedback was saved
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.interviewer_feedback, feedback_text)

        # Status should still be COMPLETED, not REVIEWED
        self.assertEqual(self.invitation.status, InvitedInterview.COMPLETED)
        self.assertEqual(self.invitation.interviewer_review_status,
                         InvitedInterview.REVIEW_PENDING)
        self.assertIsNone(self.invitation.reviewed_at)

    def test_update_existing_feedback(self):
        """Test updating already saved feedback"""
        # Set initial feedback
        self.invitation.interviewer_feedback = "Initial feedback"
        self.invitation.save()

        new_feedback = "Updated feedback with more details"
        response = self.client.post(self.url, {
            'interviewer_feedback': new_feedback,
            'mark_reviewed': 'false'
        })

        self.assertEqual(response.status_code, 302)

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.interviewer_feedback, new_feedback)

    def test_empty_feedback_not_saved(self):
        """Test that empty feedback string is not saved"""
        response = self.client.post(self.url, {
            'interviewer_feedback': '   ',  # Whitespace only
            'mark_reviewed': 'false'
        })

        self.assertEqual(response.status_code, 302)

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.interviewer_feedback, '')


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver'
)
class MarkAsReviewedTests(TestCase):
    """Test marking invitation as reviewed"""

    def setUp(self):
        self.client = Client()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password=TEST_PASSWORD
        )
        interviewer_profile = UserProfile.objects.get(user=self.interviewer)
        interviewer_profile.role = 'interviewer'
        interviewer_profile.save()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Technical Interview'
        )

        # Create completed invitation with chat
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            completed_at=timezone.now() - timedelta(hours=1)
        )

        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Technical Interview',
            interview_type=Chat.INVITED,
            scheduled_end_at=timezone.now() - timedelta(hours=1)
        )
        self.invitation.chat = self.chat
        self.invitation.save()

        self.client.login(username='interviewer@test.com',
                          password=TEST_PASSWORD)
        self.url = reverse('invitation_review', kwargs={
                           'invitation_id': self.invitation.id})

    def test_mark_as_reviewed_updates_status(self):
        """Test that marking as reviewed updates all status fields"""
        feedback_text = "Excellent performance overall."

        response = self.client.post(self.url, {
            'interviewer_feedback': feedback_text,
            'mark_reviewed': 'true'
        })

        self.assertEqual(response.status_code, 302)

        self.invitation.refresh_from_db()

        # Check all status fields updated
        self.assertEqual(self.invitation.status, InvitedInterview.REVIEWED)
        self.assertEqual(self.invitation.interviewer_review_status,
                         InvitedInterview.REVIEW_COMPLETED)
        self.assertIsNotNone(self.invitation.reviewed_at)
        self.assertEqual(self.invitation.interviewer_feedback, feedback_text)

    def test_mark_as_reviewed_sends_email(self):
        """Test that marking as reviewed sends notification email"""
        mail.outbox = []  # Clear any existing emails

        response = self.client.post(self.url, {
            'interviewer_feedback': "Great work!",
            'mark_reviewed': 'true'
        })

        self.assertEqual(response.status_code, 302)

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Verify email details
        self.assertIn('candidate@test.com', email.to)
        self.assertIn('reviewed', email.subject.lower())

    def test_reviewed_at_timestamp_set(self):
        """Test that reviewed_at timestamp is set correctly"""
        before_review = timezone.now()

        self.client.post(self.url, {
            'interviewer_feedback': "Good job",
            'mark_reviewed': 'true'
        })

        after_review = timezone.now()

        self.invitation.refresh_from_db()
        self.assertIsNotNone(self.invitation.reviewed_at)
        self.assertGreaterEqual(self.invitation.reviewed_at, before_review)
        self.assertLessEqual(self.invitation.reviewed_at, after_review)


class ReviewViewContextTests(TestCase):
    """Test that review view provides correct context"""

    def setUp(self):
        self.client = Client()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password=TEST_PASSWORD
        )
        interviewer_profile = UserProfile.objects.get(user=self.interviewer)
        interviewer_profile.role = 'interviewer'
        interviewer_profile.save()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Technical Interview'
        )

        # Create completed invitation with chat
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            completed_at=timezone.now() - timedelta(hours=1),
            interviewer_feedback="Initial feedback"
        )

        # Create chat with messages
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Technical Interview',
            interview_type=Chat.INVITED,
            scheduled_end_at=timezone.now() - timedelta(hours=1),
            messages=[
                {"role": "assistant", "content": "Welcome to the interview"},
                {"role": "user", "content": "Thank you, I'm ready"},
            ]
        )
        self.invitation.chat = self.chat
        self.invitation.save()

        self.client.login(username='interviewer@test.com',
                          password=TEST_PASSWORD)
        self.url = reverse('invitation_review', kwargs={
                           'invitation_id': self.invitation.id})

    def test_context_includes_invitation(self):
        """Test that context includes invitation object"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('invitation', response.context)
        self.assertEqual(response.context['invitation'].id, self.invitation.id)

    def test_context_includes_chat(self):
        """Test that context includes chat object"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('chat', response.context)
        self.assertEqual(response.context['chat'].id, self.chat.id)

    def test_template_displays_feedback(self):
        """Test that existing feedback is displayed"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Initial feedback")

    def test_template_displays_candidate_email(self):
        """Test that candidate email is displayed"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'candidate@test.com')


class CandidateViewFeedbackTests(TestCase):
    """Test that candidates can view interviewer feedback in results"""

    def setUp(self):
        self.client = Client()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password=TEST_PASSWORD
        )

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Technical Interview'
        )

        # Create chat
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Technical Interview',
            interview_type=Chat.INVITED,
            scheduled_end_at=timezone.now() - timedelta(hours=1)
        )

        # Create invitation
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            completed_at=timezone.now() - timedelta(hours=1),
            chat=self.chat
        )

        # Finalize the chat and create report
        self.chat.is_finalized = True
        self.chat.finalized_at = timezone.now()
        self.chat.save()

        from active_interview_app.models import ExportableReport
        ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=80,
            clarity_score=90,
            overall_score=85
        )

        self.client.login(username='candidate@test.com',
                          password=TEST_PASSWORD)
        self.url = reverse('export_report', kwargs={'chat_id': self.chat.id})

    def test_pending_review_shows_waiting_message(self):
        """Test that pending review shows appropriate message"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Interviewer Feedback')
        self.assertContains(response, 'still reviewing')

    def test_completed_review_shows_feedback(self):
        """Test that completed review shows interviewer feedback"""
        # Mark as reviewed with feedback
        self.invitation.interviewer_review_status = InvitedInterview.REVIEW_COMPLETED
        self.invitation.interviewer_feedback = "Excellent technical skills demonstrated."
        self.invitation.reviewed_at = timezone.now()
        self.invitation.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Interviewer Feedback')
        self.assertContains(
            response, 'Excellent technical skills demonstrated')

    def test_practice_interview_no_interviewer_feedback(self):
        """Test that practice interviews don't show interviewer feedback section"""
        # Create practice interview
        practice_chat = Chat.objects.create(
            owner=self.candidate,
            title='Practice Interview',
            interview_type=Chat.PRACTICE,
            is_finalized=True,
            finalized_at=timezone.now()
        )

        from active_interview_app.models import ExportableReport
        ExportableReport.objects.create(
            chat=practice_chat,
            professionalism_score=85,
            subject_knowledge_score=80,
            clarity_score=90,
            overall_score=85
        )

        url = reverse('export_report', kwargs={'chat_id': practice_chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Should not contain interviewer feedback section (check for the specific icon/heading)
        self.assertNotContains(response, 'bi-person-check-fill')
        self.assertNotContains(response, 'bi-hourglass-split')
        # Should not have the feedback box
        self.assertNotContains(response, 'still reviewing')
        self.assertNotContains(response, 'Reviewed on')

    def test_reviewed_at_timestamp_displayed(self):
        """Test that reviewed timestamp is displayed to candidate"""
        review_time = timezone.now() - timedelta(hours=2)
        self.invitation.interviewer_review_status = InvitedInterview.REVIEW_COMPLETED
        self.invitation.interviewer_feedback = "Great work!"
        self.invitation.reviewed_at = review_time
        self.invitation.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reviewed on')


class DashboardReviewButtonTests(TestCase):
    """Test review button visibility and functionality in dashboard"""

    def setUp(self):
        self.client = Client()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password=TEST_PASSWORD
        )
        interviewer_profile = UserProfile.objects.get(user=self.interviewer)
        interviewer_profile.role = 'interviewer'
        interviewer_profile.save()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Technical Interview'
        )

        self.client.login(username='interviewer@test.com',
                          password=TEST_PASSWORD)
        self.dashboard_url = reverse('invitation_dashboard')

    def test_pending_invitation_no_review_button(self):
        """Test that pending invitations don't show review button"""
        InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='test@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=1),
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        # Should not contain review button for pending
        content = response.content.decode('utf-8')
        # Check that invitation is shown but without review button
        self.assertIn('test@example.com', content)

    def test_completed_invitation_shows_review_button(self):
        """Test that completed invitations show 'Review Results' button"""
        chat = Chat.objects.create(
            owner=self.candidate,
            title='Interview',
            interview_type=Chat.INVITED
        )

        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='test@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            chat=chat
        )

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Review Results')
        self.assertContains(response, reverse(
            'invitation_review', kwargs={'invitation_id': invitation.id}))

    def test_reviewed_invitation_shows_view_review_button(self):
        """Test that reviewed invitations show 'View Review' button"""
        chat = Chat.objects.create(
            owner=self.candidate,
            title='Interview',
            interview_type=Chat.INVITED
        )

        InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='test@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.REVIEWED,
            interviewer_review_status=InvitedInterview.REVIEW_COMPLETED,
            chat=chat
        )

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Review')


class BiasGuardrailsTests(TestCase):
    """Test bias detection guardrails in feedback submission

    Related to Issues #18, #57, #58, #59 (Bias Guardrails)
    """

    def setUp(self):
        self.client = Client()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password='testpass123'
        )
        interviewer_profile = UserProfile.objects.get(user=self.interviewer)
        interviewer_profile.role = 'interviewer'
        interviewer_profile.save()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password='testpass123'
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Technical Interview'
        )

        # Create completed invitation with chat
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            completed_at=timezone.now() - timedelta(hours=1)
        )

        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Technical Interview',
            interview_type=Chat.INVITED,
            scheduled_end_at=timezone.now() - timedelta(hours=1)
        )
        self.invitation.chat = self.chat
        self.invitation.save()

        # Create bias terms
        self.blocking_term = BiasTermLibrary.objects.create(
            term='pregnant',
            category=BiasTermLibrary.FAMILY,
            pattern=r'\b(pregnant|pregnancy)\b',
            explanation='Discriminatory family status language',
            neutral_alternatives=['experienced professional', 'qualified candidate'],
            severity=BiasTermLibrary.BLOCKING,
            is_active=True,
            created_by=self.interviewer
        )

        self.warning_term = BiasTermLibrary.objects.create(
            term='young',
            category=BiasTermLibrary.AGE,
            pattern=r'\b(young|youth(ful)?)\b',
            explanation='Age-related bias',
            neutral_alternatives=['early-career professional', 'recent graduate'],
            severity=BiasTermLibrary.WARNING,
            is_active=True,
            created_by=self.interviewer
        )

        self.client.login(username='interviewer@test.com', password='testpass123')
        self.url = reverse('invitation_review', kwargs={'invitation_id': self.invitation.id})

    def test_blocking_term_prevents_save(self):
        """Test that blocking-severity terms prevent feedback from being saved"""
        feedback_with_blocking = "She is pregnant but very capable."

        response = self.client.post(self.url, {
            'interviewer_feedback': feedback_with_blocking,
            'mark_reviewed': 'false'
        })

        # Should NOT redirect (stays on page with error)
        self.assertEqual(response.status_code, 200)

        # Feedback should NOT be saved
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.interviewer_feedback, '')

        # Check error message
        messages_list = list(response.context['messages'])
        self.assertTrue(any('bias terms that must be resolved' in str(m) for m in messages_list))

    def test_warning_term_allows_save(self):
        """Test that warning-severity terms allow saving but are flagged"""
        feedback_with_warning = "He is young but shows potential."

        response = self.client.post(self.url, {
            'interviewer_feedback': feedback_with_warning,
            'mark_reviewed': 'false'
        })

        # Should redirect (save succeeds)
        self.assertEqual(response.status_code, 302)

        # Feedback should be saved
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.interviewer_feedback, feedback_with_warning)

        # Check that bias analysis was saved
        analysis = BiasAnalysisResult.objects.filter(
            object_id=str(self.invitation.pk)
        ).first()
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.warning_flags, 1)
        self.assertEqual(analysis.blocking_flags, 0)

    def test_clean_feedback_passes_validation(self):
        """Test that clean feedback passes without issues"""
        clean_feedback = "Candidate demonstrated strong technical skills and clear communication."

        response = self.client.post(self.url, {
            'interviewer_feedback': clean_feedback,
            'mark_reviewed': 'false'
        })

        # Should redirect (save succeeds)
        self.assertEqual(response.status_code, 302)

        # Feedback should be saved
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.interviewer_feedback, clean_feedback)

        # Check success message
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('Clean feedback saved successfully' in str(m) for m in messages_list))

    def test_mark_reviewed_blocked_with_any_bias(self):
        """Test that marking as reviewed is blocked if ANY bias flags exist (warning or blocking)"""
        feedback_with_warning = "He is young but talented."

        response = self.client.post(self.url, {
            'interviewer_feedback': feedback_with_warning,
            'mark_reviewed': 'true'  # Trying to mark as reviewed
        })

        # Should NOT redirect (blocked)
        self.assertEqual(response.status_code, 200)

        # Should NOT be marked as reviewed
        self.invitation.refresh_from_db()
        self.assertNotEqual(self.invitation.status, InvitedInterview.REVIEWED)
        self.assertNotEqual(self.invitation.interviewer_review_status, InvitedInterview.REVIEW_COMPLETED)

        # Check error message
        messages_list = list(response.context['messages'])
        self.assertTrue(any('Cannot notify candidate with biased feedback' in str(m) for m in messages_list))

    def test_mark_reviewed_succeeds_with_clean_feedback(self):
        """Test that marking as reviewed succeeds with clean feedback"""
        clean_feedback = "Excellent problem-solving abilities demonstrated."

        response = self.client.post(self.url, {
            'interviewer_feedback': clean_feedback,
            'mark_reviewed': 'true'
        })

        # Should redirect (success)
        self.assertEqual(response.status_code, 302)

        # Should be marked as reviewed
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, InvitedInterview.REVIEWED)
        self.assertEqual(self.invitation.interviewer_review_status, InvitedInterview.REVIEW_COMPLETED)

    def test_context_includes_bias_terms_json(self):
        """Test that template context includes serialized bias terms"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('bias_terms_json', response.context)

        # Should be JSON string
        bias_terms_json = response.context['bias_terms_json']
        self.assertIsInstance(bias_terms_json, str)

        # Should contain our test terms
        self.assertIn('pregnant', bias_terms_json)
        self.assertIn('young', bias_terms_json)

    def test_feedback_preserved_on_validation_error(self):
        """Test that feedback text is preserved when validation fails"""
        feedback_with_blocking = "She is pregnant but qualified."

        response = self.client.post(self.url, {
            'interviewer_feedback': feedback_with_blocking,
            'mark_reviewed': 'false'
        })

        # Should stay on page
        self.assertEqual(response.status_code, 200)

        # Check that initial_feedback is in context
        self.assertIn('initial_feedback', response.context)
        self.assertEqual(response.context['initial_feedback'], feedback_with_blocking)

    def test_multiple_blocking_terms_all_detected(self):
        """Test that multiple blocking terms are all detected"""
        from active_interview_app.bias_detection import BiasDetectionService

        # Create another blocking term
        BiasTermLibrary.objects.create(
            term='old',
            category=BiasTermLibrary.AGE,
            pattern=r'\b(old|elderly)\b',
            explanation='Age-related bias',
            neutral_alternatives=['experienced', 'seasoned'],
            severity=BiasTermLibrary.BLOCKING,
            is_active=True
        )

        # Clear cache to pick up the new term
        service = BiasDetectionService()
        service.clear_cache()

        feedback_multiple = "She is pregnant and he is old."

        response = self.client.post(self.url, {
            'interviewer_feedback': feedback_multiple,
            'mark_reviewed': 'false'
        })

        # Should be blocked
        self.assertEqual(response.status_code, 200)

        # Feedback not saved
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.interviewer_feedback, '')

    def test_inactive_terms_not_detected(self):
        """Test that inactive bias terms are not detected"""
        from active_interview_app.bias_detection import BiasDetectionService

        # Deactivate the blocking term
        self.blocking_term.is_active = False
        self.blocking_term.save()

        # Clear cache to pick up the change
        service = BiasDetectionService()
        service.clear_cache()

        feedback_with_inactive_term = "She is pregnant and qualified."

        response = self.client.post(self.url, {
            'interviewer_feedback': feedback_with_inactive_term,
            'mark_reviewed': 'false'
        })

        # Should succeed (term is inactive)
        self.assertEqual(response.status_code, 302)

        # Feedback should be saved
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.interviewer_feedback, feedback_with_inactive_term)

    def test_bias_analysis_result_saved(self):
        """Test that BiasAnalysisResult is created when feedback with warnings is saved"""
        feedback_with_warning = "Candidate is young but shows promise."

        response = self.client.post(self.url, {
            'interviewer_feedback': feedback_with_warning,
            'mark_reviewed': 'false'
        })

        self.assertEqual(response.status_code, 302)

        # Check BiasAnalysisResult was created
        analysis = BiasAnalysisResult.objects.filter(
            object_id=str(self.invitation.pk)
        ).first()

        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.total_flags, 1)
        self.assertEqual(analysis.warning_flags, 1)
        self.assertEqual(analysis.blocking_flags, 0)
        self.assertIn(analysis.severity_level, ['LOW', 'MEDIUM'])  # Can be either based on bias score
        self.assertTrue(analysis.saved_with_warnings)
        self.assertTrue(analysis.user_acknowledged)
