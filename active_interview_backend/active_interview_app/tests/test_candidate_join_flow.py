"""
Tests for Phase 4: Candidate Join Flow.

Tests the candidate experience for joining and starting invited interviews:
- invitation_join view - Join link access and redirection
- invited_interview_detail view - Time-gated access and UI states
- start_invited_interview view - Chat creation and template inheritance

Related Issues: #135, #136, #140
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages
from datetime import timedelta
import uuid

from active_interview_app.models import (
    InvitedInterview,
    InterviewTemplate,
    Chat,
    UserProfile
)


def create_user_with_role(username, email, password, role):
    """Helper function to create a user with a specific role"""
    user = User.objects.create_user(username, email, password)
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': role}
    )
    profile.role = role
    profile.save()
    user.refresh_from_db()
    return user


class InvitationJoinViewTests(TestCase):
    """Test invitation_join view (Phase 4.1)"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create interviewer
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@example.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Software Engineer Interview',
            description='Python position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Technical Skills',
                'content': 'Python, Django',
                'order': 0,
                'weight': 100
            }]
        )

        # Create invitation
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=1),
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        # Create candidate user (for authenticated tests)
        self.candidate = User.objects.create_user(
            'candidate',
            'candidate@example.com',
            'pass123'
        )

        # Create wrong user (different email)
        self._wrong_user = User.objects.create_user(
            'wronguser',
            'wrong@example.com',
            'pass123'
        )

    def test_join_unauthenticated_redirects_to_registration(self):
        """Test unauthenticated user redirected to registration with next parameter"""
        url = reverse('invitation_join', args=[self.invitation.id])
        response = self.client.get(url)

        # Should redirect to registration
        self.assertEqual(response.status_code, 302)
        self.assertIn('/register/', response.url)
        self.assertIn('next=', response.url)
        self.assertIn(str(self.invitation.id), response.url)

        # Should have info message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('register or log in', str(messages[0]).lower())

    def test_join_authenticated_correct_email_redirects_to_detail(self):
        """Test authenticated user with correct email redirected to detail page"""
        self.client.login(username='candidate', password='pass123')

        url = reverse('invitation_join', args=[self.invitation.id])
        response = self.client.get(url)

        # Should redirect to interview detail page
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('invited_interview_detail',
                               args=[self.invitation.id])
        self.assertEqual(response.url, expected_url)

    def test_join_authenticated_wrong_email_shows_error(self):
        """Test authenticated user with wrong email sees error and redirected"""
        self.client.login(username='wronguser', password='pass123')

        url = reverse('invitation_join', args=[self.invitation.id])
        response = self.client.get(url)

        # Should redirect to index
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))

        # Should have error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('different email', str(messages[0]).lower())

    def test_join_invalid_invitation_id_returns_404(self):
        """Test invalid invitation ID returns 404"""
        self.client.login(username='candidate', password='pass123')

        invalid_uuid = uuid.uuid4()
        url = reverse('invitation_join', args=[invalid_uuid])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_join_email_case_insensitive(self):
        """Test email matching is case-insensitive"""
        # Create user with uppercase email
        _uppercase_user = User.objects.create_user(
            'CANDIDATE@EXAMPLE.COM',  # Same email, different case
            'pass123'
        )

        self.client.login(username='uppercase', password='pass123')

        url = reverse('invitation_join', args=[self.invitation.id])
        response = self.client.get(url)

        # Should still redirect to detail (case-insensitive match)
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('invited_interview_detail',
                               args=[self.invitation.id])
        self.assertEqual(response.url, expected_url)


class InvitedInterviewDetailViewTests(TestCase):
    """Test invited_interview_detail view (Phase 4.3)"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create interviewer
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@example.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Backend Developer Interview',
            description='Django position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Algorithms',
                'content': 'Problem solving',
                'order': 0,
                'weight': 100
            }]
        )

        # Create candidate
        self.candidate = User.objects.create_user(
            'candidate',
            'candidate@example.com',
            'pass123'
        )

    def test_detail_requires_authentication(self):
        """Test detail view requires login"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=1),
            duration_minutes=60,
        )

        url = reverse('invited_interview_detail', args=[invitation.id])
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_detail_wrong_user_denied_access(self):
        """Test user with different email cannot access detail"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=1),
            duration_minutes=60,
        )

        # Create and login as wrong user
        _wrong_user = User.objects.create_user(
            'wrong@example.com',
            'pass123'
        )
        self.client.login(username='wronguser', password='pass123')

        url = reverse('invited_interview_detail', args=[invitation.id])
        response = self.client.get(url)

        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        self.assertIn('permission', str(messages[0]).lower())

    def test_detail_before_scheduled_time_shows_disabled_start(self):
        """Test detail page before scheduled time shows disabled start button"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=2),
            duration_minutes=60,
        )

        self.client.login(username='candidate', password='pass123')

        url = reverse('invited_interview_detail', args=[invitation.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'invitations/invited_interview_detail.html')

        # Should have context showing cannot start
        self.assertFalse(response.context['can_start'])
        self.assertFalse(response.context['is_expired'])
        self.assertIsNotNone(response.context['time_until_start'])

    def test_detail_during_window_shows_enabled_start(self):
        """Test detail page during valid window shows enabled start button"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(minutes=5),  # Started 5 min ago
            duration_minutes=60,  # 55 minutes remaining
        )

        self.client.login(username='candidate', password='pass123')

        url = reverse('invited_interview_detail', args=[invitation.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Should be able to start
        self.assertTrue(response.context['can_start'])
        self.assertFalse(response.context['is_expired'])
        self.assertTrue(response.context['is_accessible'])

    def test_detail_after_window_shows_expired(self):
        """Test detail page after window shows expired message"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),  # 2 hours ago
            duration_minutes=60,  # Window ended 1 hour ago
        )

        self.client.login(username='candidate', password='pass123')

        url = reverse('invited_interview_detail', args=[invitation.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Should be expired
        self.assertFalse(response.context['can_start'])
        self.assertTrue(response.context['is_expired'])
        self.assertFalse(response.context['is_accessible'])

    def test_detail_already_started_shows_chat_link(self):
        """Test detail page for already started interview shows chat"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(minutes=10),
            duration_minutes=60,
        )

        # Create chat (simulate already started)
        chat = Chat.objects.create(
            owner=self.candidate,
            title='Test Interview',
            interview_type=Chat.INVITED,
            type=Chat.GENERAL,
        )
        invitation.chat = chat
        invitation.save()

        self.client.login(username='candidate', password='pass123')

        url = reverse('invited_interview_detail', args=[invitation.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Context should have the chat
        self.assertEqual(response.context['invitation'].chat, chat)

    def test_detail_context_has_all_required_fields(self):
        """Test detail view context contains all required fields"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(minutes=30),
            duration_minutes=60,
        )

        self.client.login(username='candidate', password='pass123')

        url = reverse('invited_interview_detail', args=[invitation.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Verify all required context fields
        required_fields = [
            'invitation', 'window_end', 'can_start', 'is_expired',
            'is_accessible', 'time_until_start', 'time_remaining', 'now'
        ]
        for field in required_fields:
            self.assertIn(field, response.context)


class StartInvitedInterviewViewTests(TestCase):
    """Test start_invited_interview view (Phase 4.4)"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create interviewer
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@example.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Data Scientist Interview',
            description='ML position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Machine Learning',
                'content': 'ML algorithms',
                'order': 0,
                'weight': 100
            }]
        )

        # Create candidate
        self.candidate = User.objects.create_user(
            'candidate',
            'candidate@example.com',
            'pass123'
        )

    def test_start_requires_authentication(self):
        """Test start view requires login"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(minutes=5),
            duration_minutes=60,
        )

        url = reverse('start_invited_interview', args=[invitation.id])
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_start_wrong_user_denied(self):
        """Test user with different email cannot start interview"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(minutes=5),
            duration_minutes=60,
        )

        # Login as wrong user
        _wrong_user = User.objects.create_user(
            'wrong@example.com',
            'pass123'
        )
        self.client.login(username='wronguser', password='pass123')

        url = reverse('start_invited_interview', args=[invitation.id])
        response = self.client.get(url)

        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        self.assertIn('permission', str(messages[0]).lower())

    def test_start_before_scheduled_time_shows_error(self):
        """Test starting before scheduled time shows error"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=1),  # In the future
            duration_minutes=60,
        )

        self.client.login(username='candidate', password='pass123')

        url = reverse('start_invited_interview', args=[invitation.id])
        response = self.client.get(url)

        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        self.assertIn('cannot be started until', str(messages[0]).lower())

    def test_start_after_window_expired_shows_error(self):
        """Test starting after window expired shows error"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),  # 2 hours ago
            duration_minutes=60,  # Window ended 1 hour ago
        )

        self.client.login(username='candidate', password='pass123')

        url = reverse('start_invited_interview', args=[invitation.id])
        response = self.client.get(url)

        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        self.assertIn('time has passed', str(messages[0]).lower())

    def test_start_during_valid_window_creates_chat(self):
        """Test starting during valid window creates Chat and redirects"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(minutes=5),  # Started 5 min ago
            duration_minutes=60,  # 55 min remaining
        )

        self.client.login(username='candidate', password='pass123')

        # Verify no chat exists yet
        self.assertIsNone(invitation.chat)

        url = reverse('start_invited_interview', args=[invitation.id])
        response = self.client.get(url)

        # Should redirect to chat view
        self.assertEqual(response.status_code, 302)

        # Refresh invitation from DB
        invitation.refresh_from_db()

        # Should have created a chat
        self.assertIsNotNone(invitation.chat)
        self.assertEqual(invitation.chat.owner, self.candidate)
        self.assertEqual(invitation.chat.interview_type, Chat.INVITED)

        # Should redirect to chat view
        expected_url = reverse(
            'chat-view', kwargs={'chat_id': invitation.chat.id})
        self.assertEqual(response.url, expected_url)

        # Should have success message
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        self.assertIn('started', str(messages[0]).lower())

    def test_start_already_started_redirects_to_existing_chat(self):
        """Test starting already-started interview redirects to existing chat"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(minutes=10),
            duration_minutes=60,
        )

        # Create chat (simulate already started)
        chat = Chat.objects.create(
            owner=self.candidate,
            title='Existing Interview',
            interview_type=Chat.INVITED,
            type=Chat.GENERAL,
        )
        invitation.chat = chat
        invitation.save()

        self.client.login(username='candidate', password='pass123')

        url = reverse('start_invited_interview', args=[invitation.id])
        response = self.client.get(url)

        # Should redirect to existing chat
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('chat-view', kwargs={'chat_id': chat.id})
        self.assertEqual(response.url, expected_url)

        # Should have info message
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        self.assertIn('already been started', str(messages[0]).lower())

    def test_start_creates_chat_with_correct_fields(self):
        """Test created Chat has all required fields set correctly"""
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(minutes=5),
            duration_minutes=90,
        )

        self.client.login(username='candidate', password='pass123')

        url = reverse('start_invited_interview', args=[invitation.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        # Refresh and check chat fields
        invitation.refresh_from_db()
        chat = invitation.chat

        self.assertIsNotNone(chat)
        self.assertEqual(chat.owner, self.candidate)
        self.assertEqual(chat.interview_type, Chat.INVITED)
        self.assertIn(self.template.name, chat.title)
        self.assertIsNotNone(chat.started_at)
        self.assertIsNotNone(chat.scheduled_end_at)

        # Verify scheduled_end_at is correct (started_at + duration)
        expected_end = chat.started_at + timedelta(minutes=90)
        # Allow 1 second tolerance for execution time
        time_diff = abs((chat.scheduled_end_at - expected_end).total_seconds())
        self.assertLess(time_diff, 1)

    def test_start_invalid_invitation_id_returns_404(self):
        """Test invalid invitation ID returns 404"""
        self.client.login(username='candidate', password='pass123')

        invalid_uuid = uuid.uuid4()
        url = reverse('start_invited_interview', args=[invalid_uuid])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


class RegistrationFlowWithInvitationTests(TestCase):
    """Test registration flow with ?next= parameter (Phase 4.2)"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create interviewer
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@example.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Full Stack Developer Interview',
            description='React/Django position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Frontend & Backend',
                'content': 'React, Django, PostgreSQL',
                'order': 0,
                'weight': 100
            }]
        )

        # Create invitation
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='newcandidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=1),
            duration_minutes=60,
        )

    def test_join_link_preserves_next_parameter_in_registration_url(self):
        """Test that join link includes next parameter when redirecting to registration"""
        url = reverse('invitation_join', args=[self.invitation.id])
        response = self.client.get(url)

        # Should redirect to registration with next parameter
        self.assertEqual(response.status_code, 302)
        self.assertIn('/register/', response.url)
        self.assertIn('next=', response.url)
        self.assertIn(f'/interview/invite/{self.invitation.id}/', response.url)

    # Note: Full registration flow testing would require testing the entire
    # Django-allauth registration view, which is beyond scope of unit tests.
    # Integration tests would be more appropriate for end-to-end flow testing.
