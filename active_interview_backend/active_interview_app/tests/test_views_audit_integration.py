"""
Tests for audit logging integration in views.py.

These tests ensure audit log entries are created when users perform
actions through view functions. Targets views.py coverage gaps.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import timedelta

from active_interview_app.models import (
    Chat,
    UploadedResume,
    UploadedJobListing,
    ExportableReport,
    AuditLog
)
from .test_credentials import TEST_PASSWORD


class ViewsAuditIntegrationTest(TestCase):
    """Test audit logging integration in views.py"""

    def setUp(self):
        """Create test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

    def test_delete_resume_creates_audit_log(self):
        """Test that deleting a resume creates an audit log entry."""
        # Create a resume
        fake_file = SimpleUploadedFile("resume.pdf", b"resume content")
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_file,
            skills=['Python', 'Django']
        )

        # Delete via POST request
        response = self.client.post(reverse('delete_resume', args=[resume.id]))

        # Check redirect
        self.assertEqual(response.status_code, 302)

        # Check audit log was created
        audit_logs = AuditLog.objects.filter(
            action_type='RESUME_DELETED',
            resource_type='UploadedResume',
            user=self.user
        )
        self.assertEqual(audit_logs.count(), 1)

        audit_log = audit_logs.first()
        self.assertEqual(audit_log.resource_id, str(resume.id))
        self.assertIn('Test Resume', audit_log.description)


    def test_delete_job_without_audit(self):
        """Test that job deletion works (no audit logging implemented yet)."""
        # Create job listing
        fake_file = SimpleUploadedFile("job.txt", b"job content")
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Software Engineer',
            content='Job description',
            filepath='/path',
            filename='job.txt',
            file=fake_file,
            required_skills=['Python', 'Django']
        )

        job_id = job.id

        # Delete via POST
        response = self.client.post(reverse('delete_job', args=[job.id]))

        # Check redirect
        self.assertEqual(response.status_code, 302)

        # Verify job is deleted
        self.assertFalse(UploadedJobListing.objects.filter(id=job_id).exists())

    def test_role_change_request_view(self):
        """Test role change request view (tests views.py code path)."""
        # Make POST request to request role change
        response = self.client.post(
            reverse('request_role_change'),
            {
                'requested_role': 'interviewer',
                'justification': 'I want to conduct interviews'
            }
        )

        # Check redirect or success
        self.assertIn(response.status_code, [200, 302])

        # Check that a role change request was created
        from active_interview_app.models import RoleChangeRequest
        requests = RoleChangeRequest.objects.filter(user=self.user)
        self.assertTrue(requests.exists())

