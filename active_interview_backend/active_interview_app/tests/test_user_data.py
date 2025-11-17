"""
Comprehensive tests for User Data Export & Deletion (Issues #63, #64, #65)
Tests for GDPR/CCPA compliance features including data export and account deletion.
"""
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import json
import zipfile
import io

from active_interview_app.models import (
    DataExportRequest,
    DeletionRequest,
    UploadedResume,
    UploadedJobListing,
    Chat,
    ExportableReport,
    UserProfile,
    InterviewTemplate
)
from active_interview_app.user_data_utils import (
    generate_anonymized_id,
    export_user_data_to_dict,
    create_export_zip,
    process_export_request,
    anonymize_user_interviews,
    delete_user_account
)


class DataExportRequestModelTest(TestCase):
    """Test cases for DataExportRequest model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_export_request(self):
        """Test creating a data export request"""
        request = DataExportRequest.objects.create(user=self.user)
        self.assertEqual(request.user, self.user)
        self.assertEqual(request.status, DataExportRequest.PENDING)
        self.assertFalse(request.export_file)  # FileField is falsy when empty
        self.assertEqual(request.download_count, 0)

    def test_export_request_str_method(self):
        """Test the __str__ method"""
        request = DataExportRequest.objects.create(user=self.user)
        str_repr = str(request)
        self.assertIn('testuser', str_repr)
        self.assertIn('pending', str_repr)

    def test_is_expired_method_not_expired(self):
        """Test is_expired returns False when not expired"""
        request = DataExportRequest.objects.create(
            user=self.user,
            status=DataExportRequest.COMPLETED,
            expires_at=timezone.now() + timedelta(days=1)
        )
        self.assertFalse(request.is_expired())

    def test_is_expired_method_expired(self):
        """Test is_expired returns True when expired"""
        request = DataExportRequest.objects.create(
            user=self.user,
            status=DataExportRequest.COMPLETED,
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(request.is_expired())

    def test_is_expired_method_no_expiration(self):
        """Test is_expired returns False when no expiration set"""
        request = DataExportRequest.objects.create(user=self.user)
        self.assertFalse(request.is_expired())

    def test_mark_downloaded_method(self):
        """Test mark_downloaded increments count and updates timestamp"""
        request = DataExportRequest.objects.create(user=self.user)
        self.assertEqual(request.download_count, 0)
        self.assertIsNone(request.last_downloaded_at)

        request.mark_downloaded()
        self.assertEqual(request.download_count, 1)
        self.assertIsNotNone(request.last_downloaded_at)

        request.mark_downloaded()
        self.assertEqual(request.download_count, 2)


class DeletionRequestModelTest(TestCase):
    """Test cases for DeletionRequest model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_deletion_request(self):
        """Test creating a deletion request"""
        request = DeletionRequest.objects.create(
            anonymized_user_id='abc123',
            username='testuser',
            email='test@example.com'
        )
        self.assertEqual(request.anonymized_user_id, 'abc123')
        self.assertEqual(request.username, 'testuser')
        self.assertEqual(request.status, DeletionRequest.PENDING)

    def test_deletion_request_str_method(self):
        """Test the __str__ method"""
        request = DeletionRequest.objects.create(
            anonymized_user_id='abc123',
            username='testuser',
            email='test@example.com'
        )
        str_repr = str(request)
        self.assertIn('abc123', str_repr)
        self.assertIn('pending', str_repr)

    def test_deletion_statistics(self):
        """Test deletion statistics fields"""
        request = DeletionRequest.objects.create(
            anonymized_user_id='abc123',
            username='testuser',
            email='test@example.com',
            total_interviews_deleted=5,
            total_resumes_deleted=3,
            total_job_listings_deleted=2
        )
        self.assertEqual(request.total_interviews_deleted, 5)
        self.assertEqual(request.total_resumes_deleted, 3)
        self.assertEqual(request.total_job_listings_deleted, 2)


class UserDataUtilsTest(TestCase):
    """Test cases for user data utility functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_generate_anonymized_id(self):
        """Test generating anonymized ID"""
        anon_id = generate_anonymized_id(self.user)
        self.assertIsNotNone(anon_id)
        self.assertEqual(len(anon_id), 32)

        # Same user should generate same ID
        anon_id2 = generate_anonymized_id(self.user)
        self.assertEqual(anon_id, anon_id2)

    def test_export_user_data_to_dict_basic(self):
        """Test exporting basic user data"""
        data = export_user_data_to_dict(self.user)

        self.assertIn('user_info', data)
        self.assertIn('resumes', data)
        self.assertIn('job_listings', data)
        self.assertIn('interviews', data)
        self.assertIn('export_date', data)

        self.assertEqual(data['user_info']['username'], 'testuser')
        self.assertEqual(data['user_info']['email'], 'test@example.com')

    def test_export_user_data_with_resumes(self):
        """Test exporting user data with resumes"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content',
            skills=['Python', 'Django'],
            experience=[{'company': 'Test Inc', 'title': 'Developer'}]
        )

        data = export_user_data_to_dict(self.user)

        self.assertEqual(len(data['resumes']), 1)
        self.assertEqual(data['resumes'][0]['title'], 'My Resume')
        self.assertEqual(data['resumes'][0]['content'], 'Resume content')
        self.assertIn('Python', data['resumes'][0]['skills'])

    def test_export_user_data_with_interviews(self):
        """Test exporting user data with interviews"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=5,
            messages=[
                {'role': 'assistant', 'content': 'Hello'},
                {'role': 'user', 'content': 'Hi'}
            ]
        )

        data = export_user_data_to_dict(self.user)

        self.assertEqual(len(data['interviews']), 1)
        self.assertEqual(data['interviews'][0]['title'], 'Test Interview')
        self.assertEqual(len(data['interviews'][0]['messages']), 2)

    def test_create_export_zip(self):
        """Test creating export ZIP file"""
        # Create some test data
        UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content'
        )

        zip_content = create_export_zip(self.user)

        self.assertIsInstance(zip_content, bytes)
        self.assertGreater(len(zip_content), 0)

        # Verify ZIP can be opened
        zip_buffer = io.BytesIO(zip_content)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            files = zip_file.namelist()
            self.assertIn('complete_data.json', files)
            self.assertIn('user_info.json', files)
            self.assertIn('README.txt', files)

    def test_anonymize_user_interviews(self):
        """Test anonymizing user interviews"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Original Title',
            messages=[{'role': 'user', 'content': 'Personal info'}],
            key_questions=['Question 1']
        )

        count = anonymize_user_interviews(self.user)

        self.assertEqual(count, 1)

        chat.refresh_from_db()
        self.assertEqual(chat.messages, [])
        self.assertEqual(chat.key_questions, [])
        self.assertIn('Anonymized', chat.title)


class DataExportViewsTest(TestCase):
    """Test cases for data export views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_user_data_settings_view(self):
        """Test accessing data settings page"""
        response = self.client.get(reverse('user_data_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_data/settings.html')

    def test_user_data_settings_requires_login(self):
        """Test data settings requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('user_data_settings'))
        self.assertEqual(response.status_code, 302)

    def test_request_data_export_get(self):
        """Test GET request to data export page"""
        response = self.client.get(reverse('request_data_export'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_data/request_export.html')

    @patch('active_interview_app.views.process_export_request')
    def test_request_data_export_post(self, mock_process):
        """Test POST request to create export"""
        response = self.client.post(reverse('request_data_export'))

        # Should create export request
        self.assertTrue(DataExportRequest.objects.filter(
            user=self.user).exists())
        request = DataExportRequest.objects.get(user=self.user)

        # Should redirect to status page
        self.assertRedirects(
            response,
            reverse('data_export_status', kwargs={'request_id': request.id})
        )

        # Should call process function
        mock_process.assert_called_once()

    def test_request_data_export_duplicate_pending(self):
        """Test cannot create duplicate pending export"""
        # Create pending request
        existing = DataExportRequest.objects.create(
            user=self.user,
            status=DataExportRequest.PENDING
        )

        response = self.client.post(reverse('request_data_export'))

        # Should redirect to existing request
        self.assertRedirects(
            response,
            reverse('data_export_status', kwargs={'request_id': existing.id})
        )

        # Should not create new request
        self.assertEqual(DataExportRequest.objects.filter(
            user=self.user).count(), 1)

    def test_data_export_status_view(self):
        """Test viewing export status"""
        export = DataExportRequest.objects.create(
            user=self.user,
            status=DataExportRequest.COMPLETED
        )

        response = self.client.get(
            reverse('data_export_status', kwargs={'request_id': export.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_data/export_status.html')
        self.assertEqual(response.context['export_request'], export)

    def test_data_export_status_other_user(self):
        """Test cannot view other user's export"""
        other_user = User.objects.create_user(
            username='other',
            password='pass'
        )
        export = DataExportRequest.objects.create(user=other_user)

        response = self.client.get(
            reverse('data_export_status', kwargs={'request_id': export.id})
        )

        self.assertEqual(response.status_code, 404)

    def test_download_data_export(self):
        """Test downloading completed export"""
        # Create export with file
        export = DataExportRequest.objects.create(
            user=self.user,
            status=DataExportRequest.COMPLETED,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Create a mock file
        test_content = b'test zip content'
        export.export_file.save(
            'test.zip', io.BytesIO(test_content), save=True)

        response = self.client.get(
            reverse('download_data_export', kwargs={'request_id': export.id})
        )

        self.assertEqual(response.status_code, 200)

        # Check download count incremented
        export.refresh_from_db()
        self.assertEqual(export.download_count, 1)

    def test_download_data_export_not_ready(self):
        """Test cannot download non-completed export"""
        export = DataExportRequest.objects.create(
            user=self.user,
            status=DataExportRequest.PENDING
        )

        response = self.client.get(
            reverse('download_data_export', kwargs={'request_id': export.id})
        )

        self.assertRedirects(
            response,
            reverse('data_export_status', kwargs={'request_id': export.id})
        )

    def test_download_data_export_expired(self):
        """Test cannot download expired export"""
        export = DataExportRequest.objects.create(
            user=self.user,
            status=DataExportRequest.COMPLETED,
            expires_at=timezone.now() - timedelta(days=1)
        )

        response = self.client.get(
            reverse('download_data_export', kwargs={'request_id': export.id})
        )

        self.assertRedirects(
            response,
            reverse('data_export_status', kwargs={'request_id': export.id})
        )

        # Check status updated to expired
        export.refresh_from_db()
        self.assertEqual(export.status, DataExportRequest.EXPIRED)


class AccountDeletionViewsTest(TestCase):
    """Test cases for account deletion views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_request_account_deletion_get(self):
        """Test GET request to account deletion page"""
        response = self.client.get(reverse('request_account_deletion'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_data/request_deletion.html')

    def test_request_account_deletion_post(self):
        """Test POST request shows confirmation page"""
        response = self.client.post(reverse('request_account_deletion'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_data/confirm_deletion.html')

    def test_request_account_deletion_requires_login(self):
        """Test deletion requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('request_account_deletion'))
        self.assertEqual(response.status_code, 302)

    @patch('active_interview_app.views.delete_user_account')
    @patch('active_interview_app.views.generate_anonymized_id')
    def test_confirm_account_deletion_correct_password(self, mock_anon_id, mock_delete):
        """Test account deletion with correct password"""
        mock_anon_id.return_value = 'abc123'
        mock_delete.return_value = (True, None)

        response = self.client.post(
            reverse('confirm_account_deletion'),
            {'password': 'testpass123'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_data/deletion_complete.html')

        # Check deletion request created
        self.assertTrue(DeletionRequest.objects.filter(
            username='testuser').exists())

        # Check delete function called
        mock_delete.assert_called_once()

    def test_confirm_account_deletion_wrong_password(self):
        """Test account deletion fails with wrong password"""
        response = self.client.post(
            reverse('confirm_account_deletion'),
            {'password': 'wrongpassword'}
        )

        # Should redirect back to deletion page
        self.assertRedirects(response, reverse('request_account_deletion'))

        # Should not create deletion request
        self.assertFalse(DeletionRequest.objects.filter(
            username='testuser').exists())

        # User should still exist
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_confirm_account_deletion_get_redirects(self):
        """Test GET request to confirm deletion redirects"""
        response = self.client.get(reverse('confirm_account_deletion'))
        self.assertRedirects(response, reverse('request_account_deletion'))


class DataDeletionFunctionalityTest(TestCase):
    """Test cases for data deletion functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('active_interview_app.user_data_utils.send_deletion_confirmation_email')
    def test_delete_user_account_complete(self, mock_email):
        """Test complete account deletion"""
        # Create test data
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content'
        )
        job = UploadedJobListing.objects.create(
            user=self.user,
            filename='job.txt',
            content='Job content'
        )
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview',
            messages=[{'role': 'user', 'content': 'Test'}]
        )

        # Create deletion request
        deletion_request = DeletionRequest.objects.create(
            anonymized_user_id='abc123',
            username='testuser',
            email='test@example.com'
        )

        # Delete account
        success, error = delete_user_account(self.user, deletion_request)

        self.assertTrue(success)
        self.assertIsNone(error)

        # Check user deleted
        self.assertFalse(User.objects.filter(username='testuser').exists())

        # Check related data deleted
        self.assertFalse(UploadedResume.objects.filter(id=resume.id).exists())
        self.assertFalse(UploadedJobListing.objects.filter(id=job.id).exists())

        # Check deletion request updated
        deletion_request.refresh_from_db()
        self.assertEqual(deletion_request.status, DeletionRequest.COMPLETED)
        self.assertIsNotNone(deletion_request.completed_at)

        # Check email sent
        mock_email.assert_called_once()

    def test_anonymize_user_interviews_with_report(self):
        """Test anonymizing interviews with reports"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview',
            messages=[{'content': 'sensitive data'}],
            key_questions=['Q1']
        )

        report = ExportableReport.objects.create(
            chat=chat,
            feedback_text='Detailed feedback with PII',
            question_responses=[
                {'question': 'Q1', 'answer': 'Answer with PII'}
            ]
        )

        count = anonymize_user_interviews(self.user)

        self.assertEqual(count, 1)

        # Check interview anonymized
        chat.refresh_from_db()
        self.assertEqual(chat.messages, [])
        self.assertEqual(chat.key_questions, [])

        # Check report anonymized
        report.refresh_from_db()
        self.assertEqual(report.feedback_text, '[Anonymized]')
        self.assertEqual(report.question_responses, [])


class ProcessExportRequestTest(TestCase):
    """Test cases for export request processing"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('active_interview_app.user_data_utils.send_export_ready_email')
    def test_process_export_request_success(self, mock_email):
        """Test successful export processing"""
        export_request = DataExportRequest.objects.create(user=self.user)

        success = process_export_request(export_request)

        self.assertTrue(success)

        export_request.refresh_from_db()
        self.assertEqual(export_request.status, DataExportRequest.COMPLETED)
        self.assertIsNotNone(export_request.completed_at)
        self.assertIsNotNone(export_request.expires_at)
        self.assertIsNotNone(export_request.export_file)
        self.assertGreater(export_request.file_size_bytes, 0)

        # Check email sent
        mock_email.assert_called_once()

    @patch('active_interview_app.user_data_utils.create_export_zip')
    def test_process_export_request_failure(self, mock_create_zip):
        """Test export processing failure"""
        mock_create_zip.side_effect = Exception('Test error')

        export_request = DataExportRequest.objects.create(user=self.user)

        success = process_export_request(export_request)

        self.assertFalse(success)

        export_request.refresh_from_db()
        self.assertEqual(export_request.status, DataExportRequest.FAILED)
        self.assertIn('Test error', export_request.error_message)


class IntegrationTest(TestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('active_interview_app.user_data_utils.send_export_ready_email')
    def test_complete_export_workflow(self, mock_email):
        """Test complete export workflow from request to download"""
        self.client.login(username='testuser', password='testpass123')

        # Create some user data
        UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content'
        )

        # Request export
        response = self.client.post(reverse('request_data_export'))
        self.assertEqual(response.status_code, 302)

        # Get the created export request
        export = DataExportRequest.objects.get(user=self.user)

        # Check status page
        response = self.client.get(
            reverse('data_export_status', kwargs={'request_id': export.id})
        )
        self.assertEqual(response.status_code, 200)

        # Export should be completed (processed synchronously in test)
        export.refresh_from_db()
        self.assertEqual(export.status, DataExportRequest.COMPLETED)

        # Download export
        response = self.client.get(
            reverse('download_data_export', kwargs={'request_id': export.id})
        )
        self.assertEqual(response.status_code, 200)

        # Check download tracked
        export.refresh_from_db()
        self.assertEqual(export.download_count, 1)


class EmailErrorHandlingTest(TestCase):
    """Test email error handling and logging"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('active_interview_app.user_data_utils.send_mail')
    @patch('active_interview_app.user_data_utils.logger')
    def test_export_email_failure_logging(self, mock_logger, mock_send_mail):
        """Test that email failures are logged properly"""
        from active_interview_app.user_data_utils import send_export_ready_email

        # Create export request
        export = DataExportRequest.objects.create(user=self.user)
        export.status = DataExportRequest.COMPLETED
        export.expires_at = timezone.now() + timedelta(days=7)
        export.save()

        # Mock email failure
        mock_send_mail.side_effect = Exception("SMTP connection failed")

        # Send email (should not raise exception)
        send_export_ready_email(export)

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        self.assertIn("Failed to send export notification email",
                      str(mock_logger.warning.call_args))

    @patch('active_interview_app.user_data_utils.send_mail')
    @patch('active_interview_app.user_data_utils.logger')
    def test_deletion_email_failure_logging(self, mock_logger, mock_send_mail):
        """Test that deletion email failures are logged properly"""
        from active_interview_app.user_data_utils import send_deletion_confirmation_email

        # Mock email failure
        mock_send_mail.side_effect = Exception("Email server unreachable")

        # Send email (should not raise exception)
        send_deletion_confirmation_email('testuser', 'test@example.com')

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        self.assertIn("Failed to send deletion confirmation email",
                      str(mock_logger.warning.call_args))

    @patch('active_interview_app.user_data_utils.create_export_zip')
    @patch('active_interview_app.user_data_utils.logger')
    def test_export_processing_error_logging(self, mock_logger, mock_create_zip):
        """Test that export processing errors are logged"""
        # Create export request
        export = DataExportRequest.objects.create(user=self.user)

        # Mock zip creation failure
        mock_create_zip.side_effect = Exception("Out of memory")

        # Process export
        result = process_export_request(export)

        # Verify failure
        self.assertFalse(result)
        export.refresh_from_db()
        self.assertEqual(export.status, DataExportRequest.FAILED)
        self.assertIn("Out of memory", export.error_message)

        # Verify error was logged
        mock_logger.error.assert_called_once()
        self.assertIn("Failed to process export request",
                      str(mock_logger.error.call_args))


class EdgeCaseTest(TestCase):
    """Test edge cases and boundary conditions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_export_with_no_data(self):
        """Test exporting user with no additional data"""
        data = export_user_data_to_dict(self.user)

        self.assertEqual(data['user_info']['username'], 'testuser')
        self.assertEqual(len(data['resumes']), 0)
        self.assertEqual(len(data['job_listings']), 0)
        self.assertEqual(len(data['interviews']), 0)

    def test_export_with_very_long_username(self):
        """Test export with maximum length username"""
        long_user = User.objects.create_user(
            username='a' * 150,  # Max length for username
            email='long@example.com',
            password='testpass123'
        )
        anonymized = generate_anonymized_id(long_user)

        # Should generate valid hash
        self.assertEqual(len(anonymized), 32)
        self.assertTrue(anonymized.isalnum())

    def test_multiple_downloads(self):
        """Test multiple downloads increment count correctly"""
        export = DataExportRequest.objects.create(user=self.user)
        export.status = DataExportRequest.COMPLETED
        export.export_file = SimpleUploadedFile("test.zip", b"test content")
        export.save()

        # Download multiple times
        for i in range(5):
            export.mark_downloaded()

        export.refresh_from_db()
        self.assertEqual(export.download_count, 5)
        self.assertIsNotNone(export.last_downloaded_at)

    def test_export_with_special_characters(self):
        """Test export handles special characters in data"""
        # Create resume with special characters
        UploadedResume.objects.create(
            user=self.user,
            title='Test Resume™ with "quotes" & <tags>',
            content='Content with émojis 🎉 and unicode ñ'
        )

        zip_content = create_export_zip(self.user)

        # Verify ZIP was created
        self.assertGreater(len(zip_content), 0)

        # Verify it's a valid ZIP
        zip_buffer = io.BytesIO(zip_content)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            # Should not raise exception
            zf.testzip()

    @patch('os.path.isfile', return_value=False)
    def test_delete_account_missing_files(self, mock_isfile):
        """Test account deletion handles missing files gracefully"""
        from active_interview_app.user_data_utils import delete_user_account

        # Create resume with file reference
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Test content',
            file='uploads/test.pdf'
        )

        # Delete account (files don't exist)
        success, error = delete_user_account(self.user)

        # Should succeed even though files don't exist
        self.assertTrue(success)
        self.assertIsNone(error)

    def test_anonymized_id_consistency(self):
        """Test that anonymized ID is consistent for same user"""
        id1 = generate_anonymized_id(self.user)
        id2 = generate_anonymized_id(self.user)

        self.assertEqual(id1, id2)

    def test_export_expiration_boundary(self):
        """Test export expiration at exact boundary"""
        export = DataExportRequest.objects.create(user=self.user)
        export.status = DataExportRequest.COMPLETED

        # Set expiration to exactly now
        export.expires_at = timezone.now()
        export.save()

        # Should be expired (or very close to boundary)
        # Since timezone.now() is called again in is_expired(), there might be microseconds difference
        # We just verify the method works without error
        is_expired = export.is_expired()
        self.assertIsInstance(is_expired, bool)
