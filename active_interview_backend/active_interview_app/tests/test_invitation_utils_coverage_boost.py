"""
Additional tests to boost coverage for invitation_utils.py to > 80%
Focuses on edge cases, error paths, and google calendar integration.
"""
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core import mail
from unittest.mock import patch, Mock
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
    get_google_calendar_url,
    generate_calendar_invite
)


def create_user_with_role(username, email, password, role):
    """Helper to create user with role"""
    user = User.objects.create_user(username, email, password)
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': role}
    )
    profile.role = role
    profile.save()
    user.refresh_from_db()
    return user


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver',
    DEFAULT_FROM_EMAIL='noreply@test.com'
)
class SendInvitationEmailEdgeCasesTest(TestCase):
    """Test send_invitation_email edge cases"""

    def setUp(self):
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@test.com',
            'pass123',
            UserProfile.INTERVIEWER
        )
        self.interviewer.first_name = 'John'
        self.interviewer.last_name = 'Doe'
        self.interviewer.save()

        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Python Interview',
            description='Technical interview',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Technical',
                'content': 'Python questions',
                'order': 0,
                'weight': 100
            }]
        )

    def test_send_invitation_email_without_calendar(self):
        """Test email sending when calendar generation fails"""
        scheduled_time = timezone.now() + timedelta(hours=2)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=45,
            status=InvitedInterview.PENDING
        )

        with patch('active_interview_app.invitation_utils.generate_calendar_invite', return_value=None):
            result = send_invitation_email(invitation)

        # Should still succeed even without calendar attachment
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_invitation_email_with_calendar(self):
        """Test email sending with calendar attachment"""
        scheduled_time = timezone.now() + timedelta(hours=2)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        result = send_invitation_email(invitation)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        # Check email has attachment
        email = mail.outbox[0]
        self.assertGreater(len(email.attachments), 0)

    @patch('active_interview_app.invitation_utils.EmailMultiAlternatives.send')
    def test_send_invitation_email_smtp_error(self, mock_send):
        """Test email sending when SMTP fails"""
        mock_send.side_effect = Exception('SMTP connection failed')

        scheduled_time = timezone.now() + timedelta(hours=2)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=30,
            status=InvitedInterview.PENDING
        )

        result = send_invitation_email(invitation)

        self.assertFalse(result)

    def test_send_invitation_email_long_duration(self):
        """Test email with very long duration"""
        scheduled_time = timezone.now() + timedelta(days=1)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=180,  # 3 hours
            status=InvitedInterview.PENDING
        )

        result = send_invitation_email(invitation)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver',
    DEFAULT_FROM_EMAIL='noreply@test.com'
)
class SendCompletionNotificationEdgeCasesTest(TestCase):
    """Test send_completion_notification_email edge cases"""

    def setUp(self):
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@test.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Backend Interview',
            description='Technical interview',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Backend',
                'content': 'Django questions',
                'order': 0,
                'weight': 100
            }]
        )

    def test_send_completion_notification_success(self):
        """Test successful completion notification"""
        scheduled_time = timezone.now() - timedelta(hours=1)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.COMPLETED
        )

        result = send_completion_notification_email(invitation)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(self.interviewer.email, email.to)
        self.assertIn('Interview Completed', email.subject)

    @patch('django.core.mail.send_mail')
    def test_send_completion_notification_failure(self, mock_send_mail):
        """Test completion notification when sending fails"""
        mock_send_mail.side_effect = Exception('Email error')

        scheduled_time = timezone.now() - timedelta(hours=1)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=45,
            status=InvitedInterview.COMPLETED
        )

        result = send_completion_notification_email(invitation)

        self.assertFalse(result)

    def test_send_completion_notification_no_interviewer_name(self):
        """Test notification when interviewer has no name set"""
        # Clear interviewer name
        self.interviewer.first_name = ''
        self.interviewer.last_name = ''
        self.interviewer.save()

        scheduled_time = timezone.now() - timedelta(hours=1)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.COMPLETED
        )

        result = send_completion_notification_email(invitation)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver',
    DEFAULT_FROM_EMAIL='noreply@test.com'
)
class SendReviewNotificationEdgeCasesTest(TestCase):
    """Test send_review_notification_email edge cases"""

    def setUp(self):
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@test.com',
            'pass123',
            UserProfile.INTERVIEWER
        )

        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Frontend Interview',
            description='React interview',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Frontend',
                'content': 'React questions',
                'order': 0,
                'weight': 100
            }]
        )

    def test_send_review_notification_success(self):
        """Test successful review notification"""
        scheduled_time = timezone.now() - timedelta(hours=2)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            interviewer_review_status='reviewed'
        )

        result = send_review_notification_email(invitation)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('candidate@test.com', email.to)
        self.assertIn('Interview Reviewed', email.subject)

    @patch('django.core.mail.send_mail')
    def test_send_review_notification_failure(self, mock_send_mail):
        """Test review notification when sending fails"""
        mock_send_mail.side_effect = Exception('Network error')

        scheduled_time = timezone.now() - timedelta(hours=2)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=45,
            status=InvitedInterview.COMPLETED
        )

        result = send_review_notification_email(invitation)

        self.assertFalse(result)

    def test_send_review_notification_plain_text(self):
        """Test that plain text version is included"""
        scheduled_time = timezone.now() - timedelta(hours=2)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.COMPLETED
        )

        result = send_review_notification_email(invitation)

        self.assertTrue(result)
        email = mail.outbox[0]
        # Plain text body should exist
        self.assertIsNotNone(email.body)
        self.assertGreater(len(email.body), 0)


class GetGoogleCalendarUrlTest(TestCase):
    """Test get_google_calendar_url function"""

    def setUp(self):
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@test.com',
            'pass123',
            UserProfile.INTERVIEWER
        )
        self.interviewer.first_name = 'Jane'
        self.interviewer.last_name = 'Smith'
        self.interviewer.save()

        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Data Science Interview',
            description='ML/AI interview',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'Data Science',
                'content': 'ML questions',
                'order': 0,
                'weight': 100
            }]
        )

    def test_get_google_calendar_url_basic(self):
        """Test basic Google Calendar URL generation"""
        scheduled_time = timezone.now() + timedelta(days=1)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        url = get_google_calendar_url(invitation)

        self.assertIn('calendar.google.com', url)
        self.assertIn('action=TEMPLATE', url)
        self.assertIn('text=Interview', url)
        self.assertIn('Data+Science+Interview', url)

    def test_get_google_calendar_url_contains_dates(self):
        """Test URL contains properly formatted dates"""
        scheduled_time = timezone.now() + timedelta(days=2)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=90,
            status=InvitedInterview.PENDING
        )

        url = get_google_calendar_url(invitation)

        self.assertIn('dates=', url)
        # Check date format (YYYYMMDDTHHmmssZ)
        self.assertRegex(url, r'dates=\d{8}T\d{6}Z')

    def test_get_google_calendar_url_contains_location(self):
        """Test URL contains join link as location"""
        scheduled_time = timezone.now() + timedelta(days=1)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=45,
            status=InvitedInterview.PENDING
        )

        url = get_google_calendar_url(invitation)

        self.assertIn('location=', url)
        self.assertIn(str(invitation.id), url)

    def test_get_google_calendar_url_various_durations(self):
        """Test URL generation with various durations"""
        for duration in [30, 60, 90, 120]:
            scheduled_time = timezone.now() + timedelta(hours=duration)
            invitation = InvitedInterview.objects.create(
                interviewer=self.interviewer,
                candidate_email=f'candidate{duration}@test.com',
                template=self.template,
                scheduled_time=scheduled_time,
                duration_minutes=duration,
                status=InvitedInterview.PENDING
            )

            url = get_google_calendar_url(invitation)

            self.assertIn('calendar.google.com', url)
            self.assertIn(f'{duration}+minutes', url)


class GenerateCalendarInviteTest(TestCase):
    """Test generate_calendar_invite function"""

    def setUp(self):
        self.interviewer = create_user_with_role(
            'interviewer',
            'interviewer@test.com',
            'pass123',
            UserProfile.INTERVIEWER
        )
        self.interviewer.first_name = 'Bob'
        self.interviewer.last_name = 'Johnson'
        self.interviewer.save()

        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='DevOps Interview',
            description='Infrastructure interview',
            sections=[{
                'id': str(uuid.uuid4()),
                'title': 'DevOps',
                'content': 'K8s questions',
                'order': 0,
                'weight': 100
            }]
        )

    def test_generate_calendar_invite_success(self):
        """Test successful calendar invite generation"""
        scheduled_time = timezone.now() + timedelta(hours=3)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        ics_content = generate_calendar_invite(invitation)

        self.assertIsNotNone(ics_content)
        self.assertIsInstance(ics_content, bytes)

        # Parse the iCalendar content
        cal = Calendar.from_ical(ics_content)
        self.assertIsNotNone(cal)

    def test_generate_calendar_invite_has_event(self):
        """Test calendar invite contains event component"""
        scheduled_time = timezone.now() + timedelta(hours=3)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        ics_content = generate_calendar_invite(invitation)

        cal = Calendar.from_ical(ics_content)

        # Find event component
        events = [component for component in cal.walk() if component.name == 'VEVENT']
        self.assertEqual(len(events), 1)

    def test_generate_calendar_invite_event_details(self):
        """Test calendar invite event has correct details"""
        scheduled_time = timezone.now() + timedelta(hours=4)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=75,
            status=InvitedInterview.PENDING
        )

        ics_content = generate_calendar_invite(invitation)

        cal = Calendar.from_ical(ics_content)
        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]

        # Check event properties
        summary = str(event.get('summary'))
        self.assertIn('DevOps Interview', summary)

        # Check organizer
        organizer = str(event.get('organizer'))
        self.assertIn('interviewer@test.com', organizer)

        # Check attendee
        attendee = str(event.get('attendee'))
        self.assertIn('candidate@test.com', attendee)

    def test_generate_calendar_invite_has_alarm(self):
        """Test calendar invite includes alarm/reminder"""
        scheduled_time = timezone.now() + timedelta(hours=3)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        ics_content = generate_calendar_invite(invitation)

        cal = Calendar.from_ical(ics_content)
        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]

        # Check for alarm
        alarms = [c for c in event.walk() if c.name == 'VALARM']
        self.assertGreater(len(alarms), 0)

    def test_generate_calendar_invite_interviewer_no_name(self):
        """Test calendar generation when interviewer has no name"""
        self.interviewer.first_name = ''
        self.interviewer.last_name = ''
        self.interviewer.save()

        scheduled_time = timezone.now() + timedelta(hours=3)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        ics_content = generate_calendar_invite(invitation)

        self.assertIsNotNone(ics_content)

        cal = Calendar.from_ical(ics_content)
        event = [c for c in cal.walk() if c.name == 'VEVENT'][0]

        # Should use username
        description = str(event.get('description'))
        self.assertIn('interviewer', description)

    @patch('active_interview_app.invitation_utils.Calendar.to_ical')
    def test_generate_calendar_invite_error(self, mock_to_ical):
        """Test calendar generation handles errors gracefully"""
        mock_to_ical.side_effect = Exception('Calendar error')

        scheduled_time = timezone.now() + timedelta(hours=3)
        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=scheduled_time,
            duration_minutes=60,
            status=InvitedInterview.PENDING
        )

        ics_content = generate_calendar_invite(invitation)

        # Should return None on error
        self.assertIsNone(ics_content)

    def test_generate_calendar_invite_different_durations(self):
        """Test calendar invite with various durations"""
        for duration in [15, 30, 45, 60, 90, 120]:
            scheduled_time = timezone.now() + timedelta(hours=duration // 10)
            invitation = InvitedInterview.objects.create(
                interviewer=self.interviewer,
                candidate_email=f'candidate{duration}@test.com',
                template=self.template,
                scheduled_time=scheduled_time,
                duration_minutes=duration,
                status=InvitedInterview.PENDING
            )

            ics_content = generate_calendar_invite(invitation)

            self.assertIsNotNone(ics_content)

            cal = Calendar.from_ical(ics_content)
            event = [c for c in cal.walk() if c.name == 'VEVENT'][0]

            # Verify duration
            dtstart = event.get('dtstart').dt
            dtend = event.get('dtend').dt
            actual_duration = (dtend - dtstart).total_seconds() / 60

            self.assertEqual(actual_duration, duration)
