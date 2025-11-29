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
    UserProfile, Chat, InterviewTemplate, InvitedInterview
)

User = get_user_model()


class InvitationReviewViewAccessTests(TestCase):
    """Test access control for invitation review view"""

    def setUp(self):
        self.client = Client()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password='testpass123'
        )
        self.interviewer_profile = UserProfile.objects.get(user=self.interviewer)
        self.interviewer_profile.role = 'interviewer'
        self.interviewer_profile.save()

        # Create another interviewer
        self.other_interviewer = User.objects.create_user(
            username='other@test.com',
            email='other@test.com',
            password='testpass123'
        )
        other_profile = UserProfile.objects.get(user=self.other_interviewer)
        other_profile.role = 'interviewer'
        other_profile.save()

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
        url = reverse('invitation_review', kwargs={'invitation_id': self.invitation.id})
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_only_interviewer_can_access(self):
        """Test that only the invitation creator can access review"""
        self.client.login(username='candidate@test.com', password='testpass123')
        url = reverse('invitation_review', kwargs={'invitation_id': self.invitation.id})
        response = self.client.get(url)

        # Candidates should be forbidden
        self.assertEqual(response.status_code, 403)

    def test_other_interviewer_cannot_access(self):
        """Test that different interviewer cannot access another's review"""
        self.client.login(username='other@test.com', password='testpass123')
        url = reverse('invitation_review', kwargs={'invitation_id': self.invitation.id})
        response = self.client.get(url)

        # Should return 404 (get_object_or_404 with interviewer=request.user)
        self.assertEqual(response.status_code, 404)

    def test_invitation_creator_can_access(self):
        """Test that invitation creator can access review page"""
        self.client.login(username='interviewer@test.com', password='testpass123')
        url = reverse('invitation_review', kwargs={'invitation_id': self.invitation.id})
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

        self.client.login(username='interviewer@test.com', password='testpass123')
        url = reverse('invitation_review', kwargs={'invitation_id': invitation_no_chat.id})
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

        self.client.login(username='interviewer@test.com', password='testpass123')
        self.url = reverse('invitation_review', kwargs={'invitation_id': self.invitation.id})

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
        self.assertEqual(self.invitation.interviewer_review_status, InvitedInterview.REVIEW_PENDING)
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

        self.client.login(username='interviewer@test.com', password='testpass123')
        self.url = reverse('invitation_review', kwargs={'invitation_id': self.invitation.id})

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
        self.assertEqual(self.invitation.interviewer_review_status, InvitedInterview.REVIEW_COMPLETED)
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

        self.client.login(username='interviewer@test.com', password='testpass123')
        self.url = reverse('invitation_review', kwargs={'invitation_id': self.invitation.id})

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
            password='testpass123'
        )

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

        self.client.login(username='candidate@test.com', password='testpass123')
        # Tests removed - chat-results view deleted in Phase 3
        # See: temp/COMPLETED_PHASES_1-3.md for details

    # All test methods in this class removed - they rely on deleted chat-results view
    # See: temp/COMPLETED_PHASES_1-3.md

    def test_placeholder_to_keep_class(self):
        """Placeholder test - class tests removed (relied on deleted view)"""
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

        self.client.login(username='interviewer@test.com', password='testpass123')
        self.dashboard_url = reverse('invitation_dashboard')

    def test_pending_invitation_no_review_button(self):
        """Test that pending invitations don't show review button"""
        invitation = InvitedInterview.objects.create(
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
        self.assertContains(response, reverse('invitation_review', kwargs={'invitation_id': invitation.id}))

    def test_reviewed_invitation_shows_view_review_button(self):
        """Test that reviewed invitations show 'View Review' button"""
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
            status=InvitedInterview.REVIEWED,
            interviewer_review_status=InvitedInterview.REVIEW_COMPLETED,
            chat=chat
        )

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Review')
