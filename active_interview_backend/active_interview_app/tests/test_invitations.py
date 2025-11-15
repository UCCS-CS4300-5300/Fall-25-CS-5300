"""
Tests for invitation workflow (Phases 2-5).

Covers:
- Phase 2: Invitation creation, confirmation, dashboard
- Phase 3: Email and calendar integration
- Phase 4: Candidate join flow
- Phase 5: Duration enforcement

Related Issues: #4, #5, #6, #7, #8, #9, #134-141
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from unittest.mock import patch, Mock, MagicMock
from datetime import timedelta
import uuid

from active_interview_app.models import (
    InvitedInterview,
    InterviewTemplate,
    Chat,
    UserProfile
)
from active_interview_app.forms import InvitationCreationForm


def create_user_with_role(username, email, password, role):
    """Helper function to create a user with a specific role"""
    user = User.objects.create_user(username, email, password)
    # Get or create profile (in case signal already created it)
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': role}
    )
    # Always set the role explicitly (even if just created, to be sure)
    profile.role = role
    profile.save()
    # Refresh user from DB to ensure profile is loaded
    user.refresh_from_db()
    return user


class InvitationModelTests(TestCase):
    """Test InvitedInterview model and helper methods"""

    def setUp(self):
        """Set up test data"""
        # Create interviewer user with profile
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@example.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Test Template',
            description='Software Engineer position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Technical Skills',
                'content': 'Python, Django',
                'order': 0,
                'weight': 100
            }]
        )

        # Create invitation
        self.scheduled_time = timezone.now() + timedelta(hours=2)
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=self.scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

    def test_invitation_creation(self):
        """Test creating an invitation"""
        self.assertIsNotNone(self.invitation.id)
        self.assertEqual(self.invitation.interviewer, self.interviewer)
        self.assertEqual(self.invitation.candidate_email, 'candidate@example.com')
        self.assertEqual(self.invitation.template, self.template)
        self.assertEqual(self.invitation.status, InvitedInterview.PENDING)

    def test_is_accessible_before_scheduled_time(self):
        """Test is_accessible returns False before scheduled time"""
        self.assertFalse(self.invitation.is_accessible())

    def test_is_accessible_during_window(self):
        """Test is_accessible returns True during the time window"""
        # Set scheduled_time to now
        self.invitation.scheduled_time = timezone.now() - timedelta(minutes=5)
        self.invitation.save()
        self.assertTrue(self.invitation.is_accessible())

    def test_is_accessible_after_window(self):
        """Test is_accessible returns False after window expires"""
        # Set scheduled_time to past and duration expired
        self.invitation.scheduled_time = timezone.now() - timedelta(hours=2)
        self.invitation.save()
        self.assertFalse(self.invitation.is_accessible())

    def test_is_expired_before_window(self):
        """Test is_expired returns False before window starts"""
        self.assertFalse(self.invitation.is_expired())

    def test_is_expired_during_window(self):
        """Test is_expired returns False during window"""
        self.invitation.scheduled_time = timezone.now() - timedelta(minutes=5)
        self.invitation.save()
        self.assertFalse(self.invitation.is_expired())

    def test_is_expired_after_window(self):
        """Test is_expired returns True after window ends"""
        self.invitation.scheduled_time = timezone.now() - timedelta(hours=2)
        self.invitation.save()
        self.assertTrue(self.invitation.is_expired())

    def test_get_window_end(self):
        """Test get_window_end calculates correct end time"""
        expected_end = self.scheduled_time + timedelta(minutes=60)
        self.assertEqual(self.invitation.get_window_end(), expected_end)

    def test_get_join_url(self):
        """Test get_join_url generates correct URL"""
        url = self.invitation.get_join_url()
        self.assertIn(str(self.invitation.id), url)
        self.assertIn('/interview/invite/', url)

    def test_str_representation(self):
        """Test string representation"""
        expected = f"Test Template → candidate@example.com (pending)"
        self.assertEqual(str(self.invitation), expected)


class InvitationFormTests(TestCase):
    """Test InvitationCreationForm validation"""

    def setUp(self):
        """Set up test data"""
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@example.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Test Template',
            description='Software Engineer position'
        )

    def test_form_valid_data(self):
        """Test form with valid data"""
        future_time = timezone.now() + timedelta(hours=2)
        form_data = {
            'template': str(self.template.id),
            'candidate_email': 'candidate@example.com',
            'scheduled_date': future_time.strftime('%Y-%m-%d'),
            'scheduled_time': future_time.strftime('%H:%M'),
            'duration_minutes': '60'
        }
        form = InvitationCreationForm(data=form_data, user=self.interviewer)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        self.assertTrue(form.is_valid())

    def test_form_invalid_email(self):
        """Test form with invalid email"""
        future_time = timezone.now() + timedelta(hours=2)
        form_data = {
            'template': str(self.template.id),
            'candidate_email': 'not-an-email',
            'scheduled_date': future_time.strftime('%Y-%m-%d'),
            'scheduled_time': future_time.strftime('%H:%M'),
            'duration_minutes': '60'
        }
        form = InvitationCreationForm(data=form_data, user=self.interviewer)
        self.assertFalse(form.is_valid())
        self.assertIn('candidate_email', form.errors)

    def test_form_past_datetime(self):
        """Test form with past datetime"""
        # Use 2 hours ago to ensure it's clearly in the past
        past_time = timezone.now() - timedelta(hours=2)
        form_data = {
            'template': str(self.template.id),
            'candidate_email': 'candidate@example.com',
            'scheduled_date': past_time.strftime('%Y-%m-%d'),
            'scheduled_time': past_time.strftime('%H:%M'),
            'duration_minutes': '60'
        }
        form = InvitationCreationForm(data=form_data, user=self.interviewer)
        self.assertFalse(form.is_valid())
        # Form.clean() method raises ValidationError which appears in __all__
        self.assertTrue('__all__' in form.errors or 'scheduled_date' in form.errors)

    def test_form_template_from_different_user(self):
        """Test form rejects template from different user"""
        other_user = create_user_with_role('other', 'other@example.com', 'pass', UserProfile.INTERVIEWER)
        other_template = InterviewTemplate.objects.create(
            user=other_user,
            name='Other Template',
            description='Manager position'
        )

        future_time = timezone.now() + timedelta(hours=2)
        form_data = {
            'template': str(other_template.id),
            'candidate_email': 'candidate@example.com',
            'scheduled_date': future_time.strftime('%Y-%m-%d'),
            'scheduled_time': future_time.strftime('%H:%M'),
            'duration_minutes': '60'
        }
        form = InvitationCreationForm(data=form_data, user=self.interviewer)
        self.assertFalse(form.is_valid())
        # Should have a validation error for template field
        self.assertIn('template', form.errors)


class InvitationCreateViewTests(TestCase):
    """Test invitation_create view"""

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

        # Create candidate (should not have access)
        self.candidate = create_user_with_role(
            'candidate',
            'candidate@example.com',
            'pass123',
            UserProfile.CANDIDATE
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Test Template',
            description='Software Engineer position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Technical',
                'content': 'Python',
                'order': 0,
                'weight': 100
            }]
        )

    def test_get_requires_login(self):
        """Test GET requires authentication"""
        response = self.client.get(reverse('invitation_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_requires_interviewer_role(self):
        """Test GET requires interviewer role"""
        self.client.force_login(self.candidate)
        response = self.client.get(reverse('invitation_create'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_as_interviewer(self):
        """Test GET as interviewer shows form"""
        self.client.force_login(self.interviewer)
        response = self.client.get(reverse('invitation_create'))

        # Debug output if test fails
        if response.status_code != 200:
            print(f"User role: {self.interviewer.profile.role}")
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Invitation')
        self.assertIsInstance(response.context['form'], InvitationCreationForm)

    def test_get_with_template_id_preselects_template(self):
        """Test GET with template_id pre-selects the template"""
        self.client.force_login(self.interviewer)
        url = reverse('invitation_create_from_template',
                      kwargs={'template_id': self.template.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check that template field has initial value set
        self.assertEqual(response.context['form'].fields['template'].initial, self.template)

    @patch('active_interview_app.views.send_invitation_email')
    def test_post_valid_data_creates_invitation(self, mock_send_email):
        """Test POST with valid data creates invitation and sends email"""
        self.client.force_login(self.interviewer)

        # Mock email to return True (success)
        mock_send_email.return_value = True

        # Use 2 hours in the future to avoid timezone issues
        future_time = timezone.now() + timedelta(hours=2)
        post_data = {
            'template': self.template.id,
            'candidate_email': 'newcandidate@example.com',
            'scheduled_date': future_time.strftime('%Y-%m-%d'),
            'scheduled_time': future_time.strftime('%H:%M'),
            'duration_minutes': 60
        }

        response = self.client.post(reverse('invitation_create'), post_data)

        # Debug: print response if test fails
        if response.status_code != 302:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}")

        # Check invitation was created
        self.assertEqual(InvitedInterview.objects.count(), 1)
        invitation = InvitedInterview.objects.first()
        self.assertEqual(invitation.candidate_email, 'newcandidate@example.com')
        self.assertEqual(invitation.interviewer, self.interviewer)
        self.assertEqual(invitation.template, self.template)

        # Check email was sent
        mock_send_email.assert_called_once_with(invitation)

        # Check redirect to confirmation
        self.assertRedirects(
            response,
            reverse('invitation_confirmation', kwargs={'invitation_id': invitation.id})
        )

    def test_post_invalid_data_shows_errors(self):
        """Test POST with invalid data shows form errors"""
        self.client.force_login(self.interviewer)

        # Past datetime - use 2 hours ago to be clearly in the past
        past_time = timezone.now() - timedelta(hours=2)
        post_data = {
            'template': self.template.id,
            'candidate_email': 'candidate@example.com',
            'scheduled_date': past_time.strftime('%Y-%m-%d'),
            'scheduled_time': past_time.strftime('%H:%M'),
            'duration_minutes': 60
        }

        response = self.client.post(reverse('invitation_create'), post_data)

        # Debug output if not 200
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}")

        # Should not create invitation
        self.assertEqual(InvitedInterview.objects.count(), 0)

        # Should show form with errors (200 OK with form errors)
        self.assertEqual(response.status_code, 200)
        # The form's clean() method raises a validation error
        self.assertFormError(response.context['form'], None,
                           'Scheduled time must be at least 5 minutes in the future.')


class InvitationConfirmationViewTests(TestCase):
    """Test invitation_confirmation view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@example.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Test Template',
            description='Software Engineer position'
        )

        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=2),
            duration_minutes=60
        )

    def test_get_shows_confirmation(self):
        """Test GET shows confirmation page"""
        self.client.force_login(self.interviewer)
        url = reverse('invitation_confirmation',
                      kwargs={'invitation_id': self.invitation.id})
        response = self.client.get(url)

        # Debug output if test fails
        if response.status_code != 200:
            print(f"User role: {self.interviewer.profile.role}")
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invitation Sent')
        self.assertContains(response, 'candidate@example.com')
        self.assertEqual(response.context['invitation'], self.invitation)

    def test_get_requires_login(self):
        """Test GET requires authentication"""
        url = reverse('invitation_confirmation',
                      kwargs={'invitation_id': self.invitation.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_cannot_access_other_user_invitation(self):
        """Test user cannot access another user's invitation"""
        other_user = create_user_with_role('other', 'other@example.com', 'pass', UserProfile.INTERVIEWER)

        self.client.force_login(other_user)
        url = reverse('invitation_confirmation',
                      kwargs={'invitation_id': self.invitation.id})
        response = self.client.get(url)

        # Should get 404 (get_object_or_404 with user ownership check)
        self.assertEqual(response.status_code, 404)


class InvitationDashboardViewTests(TestCase):
    """Test invitation_dashboard view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@example.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Test Template',
            description='Software Engineer position'
        )

        # Create multiple invitations with different statuses
        self.inv_pending = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='pending@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        self.inv_completed = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='completed@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED
        )

    def test_get_shows_all_invitations(self):
        """Test GET shows all user's invitations"""
        self.client.force_login(self.interviewer)
        response = self.client.get(reverse('invitation_dashboard'))

        # Debug output if test fails
        if response.status_code != 200:
            print(f"User role: {self.interviewer.profile.role}")
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'pending@example.com')
        self.assertContains(response, 'completed@example.com')
        self.assertEqual(len(response.context['invitations']), 2)

    def test_get_requires_login(self):
        """Test GET requires authentication"""
        response = self.client.get(reverse('invitation_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_requires_interviewer_role(self):
        """Test GET requires interviewer role"""
        # Create candidate user (not interviewer)
        candidate = create_user_with_role(
            'candidate',
            'cand@example.com',
            'pass',
            UserProfile.CANDIDATE
        )

        self.client.force_login(candidate)
        response = self.client.get(reverse('invitation_dashboard'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_only_shows_own_invitations(self):
        """Test dashboard only shows user's own invitations"""
        other_interviewer = create_user_with_role(
            'other',
            'other@example.com',
            'pass',
            UserProfile.INTERVIEWER
        )

        other_template = InterviewTemplate.objects.create(
            user=other_interviewer,
            name='Other Template',
            description='Manager position'
        )

        InvitedInterview.objects.create(
            interviewer=other_interviewer,
            candidate_email='other@example.com',
            template=other_template,
            scheduled_time=timezone.now() + timedelta(hours=2),
            duration_minutes=60
        )

        self.client.force_login(self.interviewer)
        response = self.client.get(reverse('invitation_dashboard'))

        # Should only see own invitations (2, not 3)
        self.assertEqual(len(response.context['invitations']), 2)
        self.assertNotContains(response, 'other@example.com')
