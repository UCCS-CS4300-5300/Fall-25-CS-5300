"""
Tests for Phase 3: Email and Calendar Integration.

Tests invitation_utils.py functions:
- send_invitation_email()
- send_completion_notification_email()
- send_review_notification_email()
- generate_calendar_invite()

Related Issues: #7, #8, #139
"""
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core import mail
from django.conf import settings
from unittest.mock import patch
from datetime import timedelta
from icalendar import Calendar
import uuid

from active_interview_app.models import (
    InvitedInterview,
    InterviewTemplate,
    UserProfile
)
from active_interview_app.invitation_utils import (
    send_invitation_email,
    send_completion_notification_email,
    send_review_notification_email,
    generate_calendar_invite
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


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver'
)
class InvitationEmailTests(TestCase):
    """Test send_invitation_email() function"""

    def setUp(self):
        """Set up test data"""
        # Create interviewer
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@example.com',
            'pass123',
            UserProfile.INTERVIEWER
        )
        self.interviewer.first_name = 'John'
        self.interviewer.last_name = 'Interviewer'
        self.interviewer.save()

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Software Engineer Interview',
            description='Python/Django position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Technical Skills',
                'content': 'Python, Django, REST APIs',
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

    def test_send_invitation_email_success(self):
        """Test successful email sending"""
        result = send_invitation_email(self.invitation)

        # Should return True
        self.assertTrue(result)

        # Should send exactly one email
        self.assertEqual(len(mail.outbox), 1)

        # Check email details
        email = mail.outbox[0]
        self.assertEqual(email.to, ['candidate@example.com'])
        self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn('Software Engineer Interview', email.subject)

        # Check that body contains key information
        self.assertIn('invitation', email.body.lower())

        # Check HTML alternative exists
        self.assertEqual(len(email.alternatives), 1)
        _html_content = email.alternatives[0][0]

        # Check calendar attachment
        self.assertEqual(len(email.attachments), 1)
        filename, content, mimetype = email.attachments[0]
        self.assertEqual(filename, 'interview.ics')
        self.assertEqual(mimetype, 'text/calendar')

    def test_send_invitation_email_contains_join_url(self):
        """Test email contains join URL"""
        send_invitation_email(self.invitation)

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]

        # Should contain the invitation ID in URL
        self.assertIn(str(self.invitation.id), html_content)
        self.assertIn('invite', html_content.lower())

    def test_send_invitation_email_contains_interviewer_info(self):
        """Test email contains interviewer information"""
        send_invitation_email(self.invitation)

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]

        # Should contain interviewer name or email
        # (exact format depends on template)
        self.assertTrue(
            'John' in html_content or 'interviewer@example.com' in html_content
        )

    def test_send_invitation_email_contains_schedule_info(self):
        """Test email contains scheduling information"""
        send_invitation_email(self.invitation)

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]

        # Should mention duration
        self.assertIn('60', html_content)

    @patch('active_interview_app.invitation_utils.EmailMultiAlternatives.send')
    def test_send_invitation_email_handles_send_failure(self, mock_send):
        """Test graceful handling of email send failure"""
        mock_send.side_effect = Exception("SMTP error")

        result = send_invitation_email(self.invitation)

        # Should return False on failure
        self.assertFalse(result)

    @patch('active_interview_app.invitation_utils.generate_calendar_invite')
    def test_send_invitation_email_without_calendar_attachment(
            self, mock_generate):
        """Test email sends even if calendar generation fails"""
        mock_generate.return_value = None

        result = send_invitation_email(self.invitation)

        # Should still succeed
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        # But no calendar attachment
        email = mail.outbox[0]
        self.assertEqual(len(email.attachments), 0)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver'
)
class CompletionNotificationEmailTests(TestCase):
    """Test send_completion_notification_email() function"""

    def setUp(self):
        """Set up test data"""
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

        # Create completed invitation
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            completed_at=timezone.now()
        )

    def test_send_completion_notification_success(self):
        """Test successful completion notification"""
        result = send_completion_notification_email(self.invitation)

        # Should return True
        self.assertTrue(result)

        # Should send exactly one email
        self.assertEqual(len(mail.outbox), 1)

        # Check email details
        email = mail.outbox[0]
        self.assertEqual(email.to, ['interviewer@example.com'])
        self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn('completed', email.subject.lower())
        self.assertIn('candidate@example.com', email.subject)

    def test_completion_notification_contains_candidate_email(self):
        """Test notification contains candidate email"""
        send_completion_notification_email(self.invitation)

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]

        # Should contain candidate email
        self.assertIn('candidate@example.com', html_content)

    def test_completion_notification_contains_results_link(self):
        """Test notification contains link to results"""
        send_completion_notification_email(self.invitation)

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]

        # Should contain invitation ID for results URL
        self.assertIn(str(self.invitation.id), html_content)

    def test_completion_notification_handles_failure(self):
        """Test graceful handling of send failure"""
        with patch('django.core.mail.send_mail', side_effect=Exception("SMTP error")):
            result = send_completion_notification_email(self.invitation)

            # Should return False on failure
            self.assertFalse(result)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver'
)
class ReviewNotificationEmailTests(TestCase):
    """Test send_review_notification_email() function"""

    def setUp(self):
        """Set up test data"""
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
            description='ML/AI position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Machine Learning',
                'content': 'ML algorithms',
                'order': 0,
                'weight': 100
            }]
        )

        # Create reviewed invitation
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=3),
            duration_minutes=60,
            status=InvitedInterview.REVIEWED,
            completed_at=timezone.now() - timedelta(hours=1),
            interviewer_feedback='Great performance!',
            reviewed_at=timezone.now(),
            interviewer_review_status=InvitedInterview.REVIEW_COMPLETED
        )

    def test_send_review_notification_success(self):
        """Test successful review notification"""
        result = send_review_notification_email(self.invitation)

        # Should return True
        self.assertTrue(result)

        # Should send exactly one email
        self.assertEqual(len(mail.outbox), 1)

        # Check email details
        email = mail.outbox[0]
        self.assertEqual(email.to, ['candidate@example.com'])
        self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn('reviewed', email.subject.lower())
        self.assertIn('Data Scientist Interview', email.subject)

    def test_review_notification_contains_results_link(self):
        """Test notification contains link to view feedback"""
        send_review_notification_email(self.invitation)

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]

        # Should contain invitation ID for results URL
        self.assertIn(str(self.invitation.id), html_content)

    def test_review_notification_contains_template_name(self):
        """Test notification mentions template name"""
        send_review_notification_email(self.invitation)

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]

        # Should mention the interview template
        self.assertIn('Data Scientist', html_content)

    def test_review_notification_handles_failure(self):
        """Test graceful handling of send failure"""
        with patch('django.core.mail.send_mail', side_effect=Exception("SMTP error")):
            result = send_review_notification_email(self.invitation)

            # Should return False on failure
            self.assertFalse(result)


class CalendarInviteGenerationTests(TestCase):
    """Test generate_calendar_invite() function"""

    def setUp(self):
        """Set up test data"""
        # Create interviewer
        self.interviewer = User.objects.create_user(
            'interviewer',
            'interviewer@example.com',
            'pass123'
        )
        self.interviewer.first_name = 'Jane'
        self.interviewer.last_name = 'Smith'
        self.interviewer.save()

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Frontend Developer Interview',
            description='React/TypeScript position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'JavaScript',
                'content': 'ES6, React',
                'order': 0,
                'weight': 100
            }]
        )

        # Create invitation
        self.scheduled_time = timezone.now() + timedelta(days=1)
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=self.scheduled_time,
            duration_minutes=90,
            status=InvitedInterview.PENDING
        )

    def test_generate_calendar_invite_returns_bytes(self):
        """Test calendar invite generation returns bytes"""
        result = generate_calendar_invite(self.invitation)

        # Should return bytes
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    def test_calendar_invite_is_valid_icalendar(self):
        """Test generated content is valid iCalendar format"""
        ics_content = generate_calendar_invite(self.invitation)

        # Should be parseable as iCalendar
        cal = Calendar.from_ical(ics_content)
        self.assertIsNotNone(cal)

        # Should have required properties
        self.assertEqual(cal['version'], '2.0')
        self.assertEqual(cal['method'], 'REQUEST')

    def test_calendar_invite_contains_event(self):
        """Test calendar contains event component"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        # Should have one event
        events = [component for component in cal.walk()
                  if component.name == 'VEVENT']
        self.assertEqual(len(events), 1)

    def test_calendar_event_has_correct_summary(self):
        """Test event has correct summary (title)"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]
        summary = str(event['summary'])

        # Should contain template name
        self.assertIn('Frontend Developer Interview', summary)

    def test_calendar_event_has_correct_times(self):
        """Test event has correct start and end times"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]

        # Start time should match scheduled_time (within 1 second for
        # microsecond differences)
        dtstart = event['dtstart'].dt
        scheduled_time_normalized = self.scheduled_time.replace(
            tzinfo=None, microsecond=0)
        dtstart_normalized = dtstart.replace(
            tzinfo=None, microsecond=0) if hasattr(
            dtstart, 'replace') else dtstart
        self.assertEqual(dtstart_normalized, scheduled_time_normalized)

        # End time should be start + duration
        dtend = event['dtend'].dt
        expected_end = self.scheduled_time + timedelta(minutes=90)
        expected_end_normalized = expected_end.replace(
            tzinfo=None, microsecond=0)
        dtend_normalized = dtend.replace(
            tzinfo=None, microsecond=0) if hasattr(dtend, 'replace') else dtend
        self.assertEqual(dtend_normalized, expected_end_normalized)

    def test_calendar_event_has_description(self):
        """Test event has description with details"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]
        description = str(event['description'])

        # Should contain key information
        self.assertIn('Frontend Developer Interview', description)
        self.assertIn('90 minutes', description)

    def test_calendar_event_has_location(self):
        """Test event has location (join URL)"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]
        location = str(event['location'])

        # Should contain join URL with invitation ID
        self.assertIn(str(self.invitation.id), location)

    def test_calendar_event_has_organizer(self):
        """Test event has organizer (interviewer)"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]
        organizer = str(event['organizer'])

        # Should contain interviewer email
        self.assertIn('interviewer@example.com', organizer)

    def test_calendar_event_has_attendee(self):
        """Test event has attendee (candidate)"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]
        attendee = str(event['attendee'])

        # Should contain candidate email
        self.assertIn('candidate@example.com', attendee)

    def test_calendar_event_has_unique_uid(self):
        """Test event has unique UID"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]
        uid = str(event['uid'])

        # Should contain invitation ID
        self.assertIn(str(self.invitation.id), uid)

    def test_calendar_event_has_status(self):
        """Test event has status CONFIRMED"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]
        status = str(event['status'])

        # Should be CONFIRMED
        self.assertEqual(status, 'CONFIRMED')

    def test_calendar_event_has_alarm(self):
        """Test event has reminder alarm"""
        ics_content = generate_calendar_invite(self.invitation)
        cal = Calendar.from_ical(ics_content)

        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]

        # Should have alarm component
        alarms = [c for c in event.walk() if c.name == 'VALARM']
        self.assertGreater(len(alarms), 0)

        # Check alarm properties
        alarm = alarms[0]
        self.assertEqual(str(alarm['action']), 'DISPLAY')

    @patch('active_interview_app.invitation_utils.Calendar')
    def test_calendar_generation_handles_errors(self, mock_calendar):
        """Test graceful handling of calendar generation errors"""
        mock_calendar.side_effect = Exception("Calendar error")

        result = generate_calendar_invite(self.invitation)

        # Should return None on error
        self.assertIsNone(result)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver'
)
class EmailTemplateRenderingTests(TestCase):
    """Test that email templates render correctly"""

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
            name='Test Interview',
            description='Test position',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Skills',
                'content': 'Test',
                'order': 0,
                'weight': 100
            }]
        )

        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timedelta(hours=1),
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

    def test_invitation_email_template_renders(self):
        """Test invitation email template renders without errors"""
        # Should not raise exception
        try:
            send_invitation_email(self.invitation)
            rendered = True
        except Exception:
            rendered = False

        self.assertTrue(rendered)
        self.assertEqual(len(mail.outbox), 1)

    def test_completion_email_template_renders(self):
        """Test completion email template renders without errors"""
        self.invitation.status = InvitedInterview.COMPLETED
        self.invitation.save()

        try:
            send_completion_notification_email(self.invitation)
            rendered = True
        except Exception:
            rendered = False

        self.assertTrue(rendered)
        self.assertEqual(len(mail.outbox), 1)

    def test_review_email_template_renders(self):
        """Test review email template renders without errors"""
        self.invitation.status = InvitedInterview.REVIEWED
        self.invitation.interviewer_feedback = 'Good job!'
        self.invitation.reviewed_at = timezone.now()
        self.invitation.interviewer_review_status = InvitedInterview.REVIEW_COMPLETED
        self.invitation.save()

        try:
            send_review_notification_email(self.invitation)
            rendered = True
        except Exception:
            rendered = False

        self.assertTrue(rendered)
        self.assertEqual(len(mail.outbox), 1)
