"""
Utility functions for interview invitation workflow.
Handles email sending and calendar invitation generation.

Related to Issues #8, #139 (Email notifications).
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from icalendar import Calendar, Event
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def send_invitation_email(invited_interview):
    """
    Send invitation email to candidate with join link and calendar invite.

    Args:
        invited_interview: InvitedInterview instance

    Returns:
        bool: True if email sent successfully, False otherwise

    Related to Issue #8 (Send Interview Invitation).
    """
    try:
        candidate_email = invited_interview.candidate_email
        join_url = invited_interview.get_join_url()
        window_end = invited_interview.get_window_end()

        # Email subject
        subject = f'Interview Invitation: {invited_interview.template.name}'

        # Render HTML email template
        html_message = render_to_string(
            'emails/invitation_sent.html',
            {
                'invitation': invited_interview,
                'join_url': join_url,
                'window_end': window_end,
                'interviewer': invited_interview.interviewer,
            }
        )

        # Create plain text version
        plain_message = strip_tags(html_message)

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[candidate_email],
        )

        # Attach HTML version
        email.attach_alternative(html_message, "text/html")

        # Generate and attach calendar invite
        ics_content = generate_calendar_invite(invited_interview)
        if ics_content:
            email.attach(
                'interview.ics',
                ics_content,
                'text/calendar'
            )

        # Send email
        email.send(fail_silently=False)

        logger.info(
            f"Invitation email sent to {candidate_email} "
            f"for interview {invited_interview.id}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to send invitation email: {e}")
        # In development, email will be printed to console anyway
        return False


def send_completion_notification_email(invited_interview):
    """
    Notify interviewer that candidate has completed the interview.

    Args:
        invited_interview: InvitedInterview instance

    Returns:
        bool: True if email sent successfully, False otherwise

    Related to Issue #139 (Email Notifications - Completion).
    """
    try:
        interviewer_email = invited_interview.interviewer.email

        # Email subject
        subject = f'Interview Completed: {invited_interview.candidate_email}'

        # Render HTML email template
        html_message = render_to_string(
            'emails/interview_completed.html',
            {
                'invitation': invited_interview,
                'interviewer': invited_interview.interviewer,
                'results_url': (
                    f"{settings.SITE_URL}/invitations/"
                    f"{invited_interview.id}/confirmation/"
                ),
            }
        )

        # Create plain text version
        plain_message = strip_tags(html_message)

        # Send email
        from django.core.mail import send_mail
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [interviewer_email],
            html_message=html_message,
            fail_silently=True,
        )

        logger.info(
            f"Completion notification sent to {interviewer_email} "
            f"for interview {invited_interview.id}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to send completion notification: {e}")
        return False


def send_review_notification_email(invited_interview):
    """
    Notify candidate that interviewer has reviewed their interview.

    Args:
        invited_interview: InvitedInterview instance

    Returns:
        bool: True if email sent successfully, False otherwise

    Related to Issue #139 (Email Notifications - Review).
    """
    try:
        candidate_email = invited_interview.candidate_email

        # Email subject
        subject = f'Interview Reviewed: {invited_interview.template.name}'

        # Render HTML email template
        html_message = render_to_string(
            'emails/interview_reviewed.html',
            {
                'invitation': invited_interview,
                'results_url': (
                    f"{settings.SITE_URL}/invitations/"
                    f"{invited_interview.id}/confirmation/"
                ),
            }
        )

        # Create plain text version
        plain_message = strip_tags(html_message)

        # Send email
        from django.core.mail import send_mail
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [candidate_email],
            html_message=html_message,
            fail_silently=True,
        )

        logger.info(
            f"Review notification sent to {candidate_email} "
            f"for interview {invited_interview.id}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to send review notification: {e}")
        return False


def generate_calendar_invite(invited_interview):
    """
    Generate an iCalendar (.ics) file for the interview invitation.

    Args:
        invited_interview: InvitedInterview instance

    Returns:
        bytes: iCalendar file content, or None if generation failed

    Related to Issue #7 (Google Calendar Integration).
    """
    try:
        # Create calendar
        cal = Calendar()
        cal.add(
            'prodid',
            '-//Active Interview Service//Interview Invitation//EN'
        )
        cal.add('version', '2.0')
        cal.add('method', 'REQUEST')

        # Create event
        event = Event()

        # Event summary (title)
        event.add('summary', f'Interview: {invited_interview.template.name}')

        # Event description
        interviewer_name = (
            invited_interview.interviewer.get_full_name() or
            invited_interview.interviewer.username
        )
        description = (
            f"You have been invited to take an interview.\n\n"
            f"Template: {invited_interview.template.name}\n"
            f"Duration: {invited_interview.duration_minutes} minutes\n"
            f"Interviewer: {interviewer_name}\n\n"
            f"Join Link: {invited_interview.get_join_url()}\n\n"
            f"You can start the interview at the scheduled time and "
            f"complete it within the duration window."
        )
        event.add('description', description)

        # Start time
        event.add('dtstart', invited_interview.scheduled_time)

        # End time (scheduled_time + duration)
        end_time = (
            invited_interview.scheduled_time +
            timedelta(minutes=invited_interview.duration_minutes)
        )
        event.add('dtend', end_time)

        # Location (virtual - join link)
        event.add('location', invited_interview.get_join_url())

        # Organizer (interviewer)
        event.add('organizer', f'mailto:{invited_interview.interviewer.email}')

        # Attendee (candidate)
        event.add('attendee', f'mailto:{invited_interview.candidate_email}')

        # Unique ID
        event.add(
            'uid',
            f'interview-{invited_interview.id}@activeinterviewservice.me'
        )

        # Creation timestamp
        event.add('dtstamp', timezone.now())

        # Status
        event.add('status', 'CONFIRMED')

        # Reminder - 1 hour before
        from icalendar import Alarm
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', 'Interview starting in 1 hour')
        alarm.add('trigger', timedelta(hours=-1))
        event.add_component(alarm)

        # Add event to calendar
        cal.add_component(event)

        # Return as bytes
        return cal.to_ical()

    except Exception as e:
        logger.error(f"Failed to generate calendar invite: {e}")
        return None
