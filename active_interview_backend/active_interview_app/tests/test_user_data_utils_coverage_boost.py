"""
Additional tests to boost coverage for user_data_utils.py to > 80%
Focuses on uncovered edge cases and error paths.
"""
from datetime import timedelta
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock, Mock
import io
import zipfile

from active_interview_app.models import (
    DataExportRequest,
    DeletionRequest,
    UploadedResume,
    UploadedJobListing,
    Chat,
    ExportableReport,
    UserProfile,
    RoleChangeRequest,
    InterviewTemplate
)
from active_interview_app.user_data_utils import (
    generate_anonymized_id,
    export_user_data_to_dict,
    create_csv_from_list,
    create_export_zip,
    process_export_request,
    send_export_ready_email,
    anonymize_user_interviews,
    delete_user_account,
    send_deletion_confirmation_email
)
from .test_credentials import TEST_PASSWORD


class GenerateAnonymizedIdTest(TestCase):
    """Test generate_anonymized_id function"""

    def test_generate_anonymized_id_returns_32_chars(self):
        """Test that anonymized ID is exactly 32 characters"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=TEST_PASSWORD
        )
        anon_id = generate_anonymized_id(user)
        self.assertEqual(len(anon_id), 32)

    def test_generate_anonymized_id_consistent(self):
        """Test that same user generates same ID"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=TEST_PASSWORD
        )
        anon_id1 = generate_anonymized_id(user)
        anon_id2 = generate_anonymized_id(user)
        self.assertEqual(anon_id1, anon_id2)

    def test_generate_anonymized_id_different_users(self):
        """Test that different users generate different IDs"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password=TEST_PASSWORD
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password=TEST_PASSWORD
        )
        anon_id1 = generate_anonymized_id(user1)
        anon_id2 = generate_anonymized_id(user2)
        self.assertNotEqual(anon_id1, anon_id2)


class ExportUserDataToDictTest(TestCase):
    """Test export_user_data_to_dict function with various data scenarios"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=TEST_PASSWORD,
            first_name='Test',
            last_name='User'
        )
        self.user.last_login = timezone.now()
        self.user.save()

    def test_export_user_data_basic(self):
        """Test basic user data export"""
        data = export_user_data_to_dict(self.user)

        self.assertIn('export_date', data)
        self.assertIn('user_info', data)
        self.assertEqual(data['user_info']['username'], 'testuser')
        self.assertEqual(data['user_info']['email'], 'test@example.com')
        self.assertEqual(data['user_info']['first_name'], 'Test')
        self.assertEqual(data['user_info']['last_name'], 'User')
        self.assertTrue(data['user_info']['is_active'])

    def test_export_user_data_with_profile(self):
        """Test user data export with UserProfile"""
        profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'role': UserProfile.CANDIDATE,
                'auth_provider': 'email'
            }
        )
        # Update profile in case it already existed with different values
        profile.role = UserProfile.CANDIDATE
        profile.auth_provider = 'email'
        profile.save()

        # Refresh user to get updated profile
        self.user.refresh_from_db()

        data = export_user_data_to_dict(self.user)

        self.assertEqual(data['user_info']['role'], UserProfile.CANDIDATE)
        self.assertEqual(data['user_info']['auth_provider'], 'email')
        self.assertIn('profile_created_at', data['user_info'])

    def test_export_user_data_with_resumes(self):
        """Test user data export with resumes"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Software Engineer Resume',
            content='Resume content here',
            original_filename='resume.pdf',
            filesize=1024,
            skills=['Python', 'Django'],
            experience='5 years',
            education='BS Computer Science',
            parsing_status='completed'
        )

        data = export_user_data_to_dict(self.user)

        self.assertEqual(len(data['resumes']), 1)
        self.assertEqual(data['resumes'][0]['title'], 'Software Engineer Resume')
        self.assertEqual(data['resumes'][0]['skills'], ['Python', 'Django'])
        self.assertEqual(data['resumes'][0]['experience'], '5 years')
        self.assertEqual(data['resumes'][0]['education'], 'BS Computer Science')

    def test_export_user_data_with_job_listings(self):
        """Test user data export with job listings"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Senior Developer',
            filename='job.txt',
            content='Job description here'
        )

        data = export_user_data_to_dict(self.user)

        self.assertEqual(len(data['job_listings']), 1)
        self.assertEqual(data['job_listings'][0]['title'], 'Senior Developer')

    def test_export_user_data_with_interviews(self):
        """Test user data export with interview chats"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content'
        )
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job Title',
            content='Job content'
        )

        chat = Chat.objects.create(
            owner=self.user,
            title='Technical Interview',
            type='technical',
            difficulty=7,
            messages=[{'role': 'ai', 'content': 'Hello'}],
            key_questions=['What is Python?'],
            resume=resume,
            job_listing=job
        )

        data = export_user_data_to_dict(self.user)

        self.assertEqual(len(data['interviews']), 1)
        self.assertEqual(data['interviews'][0]['title'], 'Technical Interview')
        self.assertEqual(data['interviews'][0]['difficulty'], 7)
        self.assertEqual(data['interviews'][0]['resume_title'], 'My Resume')
        self.assertEqual(data['interviews'][0]['job_listing_title'], 'Job Title')

    def test_export_user_data_with_exportable_report(self):
        """Test user data export with exportable report"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview with Report',
            type='behavioral',
            difficulty=5
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=85,
            subject_knowledge_score=90,
            clarity_score=80,
            overall_score=85,
            feedback_text='Great job!',
            question_responses=[{'q': 'Question 1', 'a': 'Answer 1'}],
            total_questions_asked=10,
            total_responses_given=10
        )

        data = export_user_data_to_dict(self.user)

        self.assertEqual(len(data['interviews']), 1)
        self.assertIn('report', data['interviews'][0])
        self.assertEqual(data['interviews'][0]['report']['overall_score'], 85)
        self.assertEqual(data['interviews'][0]['report']['feedback_text'], 'Great job!')

    def test_export_user_data_with_templates(self):
        """Test user data export with interview templates"""
        template = InterviewTemplate.objects.create(
            user=self.user,
            name='Custom Template',
            description='Test template',
            sections=[{'title': 'Section 1', 'content': 'Content'}]
        )

        data = export_user_data_to_dict(self.user)

        self.assertEqual(len(data['interview_templates']), 1)
        self.assertEqual(data['interview_templates'][0]['name'], 'Custom Template')

    def test_export_user_data_with_role_requests(self):
        """Test user data export with role change requests"""
        profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'role': UserProfile.CANDIDATE}
        )

        role_request = RoleChangeRequest.objects.create(
            user=self.user,
            requested_role=UserProfile.INTERVIEWER,
            current_role=UserProfile.CANDIDATE,
            status=RoleChangeRequest.PENDING,
            reason='I want to interview candidates'
        )

        data = export_user_data_to_dict(self.user)

        self.assertEqual(len(data['role_change_requests']), 1)
        self.assertEqual(data['role_change_requests'][0]['requested_role'], UserProfile.INTERVIEWER)
        self.assertEqual(data['role_change_requests'][0]['status'], RoleChangeRequest.PENDING)

    def test_export_user_data_no_last_login(self):
        """Test export for user who has never logged in"""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password=TEST_PASSWORD
        )
        user.last_login = None
        user.save()

        data = export_user_data_to_dict(user)

        self.assertIsNone(data['user_info']['last_login'])


class CreateCsvFromListTest(TestCase):
    """Test create_csv_from_list function"""

    def test_create_csv_from_list_basic(self):
        """Test basic CSV creation"""
        data = [
            {'name': 'Alice', 'age': 30, 'city': 'NYC'},
            {'name': 'Bob', 'age': 25, 'city': 'LA'}
        ]
        fieldnames = ['name', 'age', 'city']

        csv_output = create_csv_from_list(data, fieldnames)

        self.assertIn('name,age,city', csv_output)
        self.assertIn('Alice,30,NYC', csv_output)
        self.assertIn('Bob,25,LA', csv_output)

    def test_create_csv_from_list_extra_fields(self):
        """Test CSV creation with extra fields in data"""
        data = [
            {'name': 'Alice', 'age': 30, 'extra': 'ignored'}
        ]
        fieldnames = ['name', 'age']

        csv_output = create_csv_from_list(data, fieldnames)

        self.assertIn('name,age', csv_output)
        self.assertNotIn('extra', csv_output)
        self.assertNotIn('ignored', csv_output)

    def test_create_csv_from_list_empty(self):
        """Test CSV creation with empty list"""
        data = []
        fieldnames = ['name', 'age']

        csv_output = create_csv_from_list(data, fieldnames)

        self.assertIn('name,age', csv_output)


class CreateExportZipTest(TestCase):
    """Test create_export_zip function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='zipuser',
            email='zip@example.com',
            password=TEST_PASSWORD
        )

    def test_create_export_zip_structure(self):
        """Test that ZIP file has correct structure"""
        zip_content = create_export_zip(self.user)

        # Verify it's valid ZIP
        self.assertIsInstance(zip_content, bytes)

        # Read ZIP contents
        zip_buffer = io.BytesIO(zip_content)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            file_list = zip_file.namelist()

            # Check for required files
            self.assertIn('complete_data.json', file_list)
            self.assertIn('user_info.json', file_list)
            self.assertIn('README.txt', file_list)

    def test_create_export_zip_with_resumes(self):
        """Test ZIP creation with resumes"""
        UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='Resume text here',
            original_filename='resume.pdf',
            filesize=1024
        )

        zip_content = create_export_zip(self.user)
        zip_buffer = io.BytesIO(zip_content)

        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            file_list = zip_file.namelist()

            self.assertIn('resumes.csv', file_list)
            # Check for individual resume file
            resume_files = [f for f in file_list if f.startswith('resumes/resume_')]
            self.assertEqual(len(resume_files), 1)

    def test_create_export_zip_with_job_listings(self):
        """Test ZIP creation with job listings"""
        UploadedJobListing.objects.create(
            user=self.user,
            title='Software Engineer',
            filename='job.txt',
            content='Job posting content'
        )

        zip_content = create_export_zip(self.user)
        zip_buffer = io.BytesIO(zip_content)

        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            file_list = zip_file.namelist()

            self.assertIn('job_listings.csv', file_list)
            job_files = [f for f in file_list if f.startswith('job_listings/job_')]
            self.assertEqual(len(job_files), 1)

    def test_create_export_zip_with_interviews(self):
        """Test ZIP creation with interviews"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            type='technical',
            difficulty=5,
            messages=[{'role': 'user', 'content': 'Hello'}],
            key_questions=['Q1']
        )

        zip_content = create_export_zip(self.user)
        zip_buffer = io.BytesIO(zip_content)

        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            file_list = zip_file.namelist()

            self.assertIn('interviews.csv', file_list)
            interview_files = [f for f in file_list if f.startswith('interviews/interview_')]
            self.assertEqual(len(interview_files), 1)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver'
)
class ProcessExportRequestTest(TestCase):
    """Test process_export_request function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='exportuser',
            email='export@example.com',
            password=TEST_PASSWORD
        )

    @patch('active_interview_app.user_data_utils.send_export_ready_email')
    def test_process_export_request_success(self, mock_send_email):
        """Test successful export request processing"""
        export_request = DataExportRequest.objects.create(user=self.user)

        result = process_export_request(export_request)

        self.assertTrue(result)
        export_request.refresh_from_db()
        self.assertEqual(export_request.status, DataExportRequest.COMPLETED)
        self.assertIsNotNone(export_request.completed_at)
        self.assertIsNotNone(export_request.expires_at)
        self.assertTrue(export_request.export_file)
        self.assertGreater(export_request.file_size_bytes, 0)
        mock_send_email.assert_called_once_with(export_request)

    @patch('active_interview_app.user_data_utils.create_export_zip')
    def test_process_export_request_failure(self, mock_create_zip):
        """Test export request processing failure"""
        mock_create_zip.side_effect = Exception('Test error')

        export_request = DataExportRequest.objects.create(user=self.user)

        result = process_export_request(export_request)

        self.assertFalse(result)
        export_request.refresh_from_db()
        self.assertEqual(export_request.status, DataExportRequest.FAILED)
        self.assertIn('Test error', export_request.error_message)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='http://testserver',
    DEFAULT_FROM_EMAIL='noreply@example.com'
)
class SendExportReadyEmailTest(TestCase):
    """Test send_export_ready_email function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='emailuser',
            email='email@example.com',
            password=TEST_PASSWORD
        )

    @patch('active_interview_app.user_data_utils.send_mail')
    def test_send_export_ready_email_success(self, mock_send_mail):
        """Test successful email sending"""
        export_request = DataExportRequest.objects.create(
            user=self.user,
            status=DataExportRequest.COMPLETED,
            expires_at=timezone.now() + timedelta(days=7)
        )

        send_export_ready_email(export_request)

        mock_send_mail.assert_called_once()

    @patch('active_interview_app.user_data_utils.send_mail')
    def test_send_export_ready_email_failure(self, mock_send_mail):
        """Test email sending failure (should not raise exception)"""
        mock_send_mail.side_effect = Exception('SMTP error')

        export_request = DataExportRequest.objects.create(
            user=self.user,
            status=DataExportRequest.COMPLETED,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Should not raise exception
        try:
            send_export_ready_email(export_request)
        except Exception:
            self.fail("send_export_ready_email raised exception unexpectedly")


class AnonymizeUserInterviewsTest(TestCase):
    """Test anonymize_user_interviews function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='anonuser',
            email='anon@example.com',
            password=TEST_PASSWORD
        )

    def test_anonymize_user_interviews_basic(self):
        """Test basic interview anonymization"""
        chat = Chat.objects.create(
            owner=self.user,
            title='My Interview',
            type='technical',
            difficulty=5,
            messages=[{'role': 'user', 'content': 'My personal info'}],
            key_questions=['Personal question?']
        )

        count = anonymize_user_interviews(self.user)

        self.assertEqual(count, 1)
        chat.refresh_from_db()
        self.assertEqual(chat.messages, [])
        self.assertEqual(chat.key_questions, [])
        self.assertTrue(chat.title.startswith('Anonymized Interview'))

    def test_anonymize_user_interviews_with_report(self):
        """Test anonymization with exportable report"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview with Report',
            type='behavioral',
            difficulty=6,
            messages=[{'role': 'user', 'content': 'Personal data'}],
            key_questions=['Personal question?']
        )

        report = ExportableReport.objects.create(
            chat=chat,
            feedback_text='Detailed personal feedback',
            question_responses=[{'q': 'Q', 'a': 'Personal answer'}],
            professionalism_score=80,
            overall_score=75
        )

        count = anonymize_user_interviews(self.user)

        self.assertEqual(count, 1)
        report.refresh_from_db()
        self.assertEqual(report.feedback_text, '[Anonymized]')
        self.assertEqual(report.question_responses, [])
        # Scores should be preserved
        self.assertEqual(report.professionalism_score, 80)
        self.assertEqual(report.overall_score, 75)

    def test_anonymize_user_interviews_multiple(self):
        """Test anonymizing multiple interviews"""
        for i in range(3):
            Chat.objects.create(
                owner=self.user,
                title=f'Interview {i}',
                type='technical',
                difficulty=5
            )

        count = anonymize_user_interviews(self.user)

        self.assertEqual(count, 3)


class DeleteUserAccountTest(TestCase):
    """Test delete_user_account function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='deleteuser',
            email='delete@example.com',
            password=TEST_PASSWORD
        )

    @patch('active_interview_app.user_data_utils.send_deletion_confirmation_email')
    @patch('os.path.isfile')
    @patch('os.remove')
    def test_delete_user_account_success(self, mock_remove, mock_isfile, mock_send_email):
        """Test successful account deletion"""
        mock_isfile.return_value = False  # Simulate no physical files

        # Create some data
        Chat.objects.create(
            owner=self.user,
            title='Interview',
            type='technical',
            difficulty=5
        )

        UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content'
        )

        success, error = delete_user_account(self.user)

        self.assertTrue(success)
        self.assertIsNone(error)

        # User should be deleted
        self.assertFalse(User.objects.filter(username='deleteuser').exists())

        # Email should be sent
        mock_send_email.assert_called_once()

    @patch('active_interview_app.user_data_utils.send_deletion_confirmation_email')
    def test_delete_user_account_with_deletion_request(self, mock_send_email):
        """Test account deletion with DeletionRequest tracking"""
        deletion_request = DeletionRequest.objects.create(
            anonymized_user_id='test_anon_id',
            username=self.user.username,
            email=self.user.email,
            status=DeletionRequest.PENDING
        )

        # Create test data
        Chat.objects.create(owner=self.user, title='Interview', type='technical', difficulty=5)
        UploadedResume.objects.create(user=self.user, title='Resume', content='Content')
        UploadedJobListing.objects.create(user=self.user, title='Job', content='Content')

        success, error = delete_user_account(self.user, deletion_request)

        self.assertTrue(success)
        # Deletion request is deleted along with user (CASCADE)

    @patch('active_interview_app.user_data_utils.anonymize_user_interviews')
    def test_delete_user_account_failure(self, mock_anonymize):
        """Test account deletion failure"""
        mock_anonymize.side_effect = Exception('Database error')

        success, error = delete_user_account(self.user)

        self.assertFalse(success)
        self.assertIsNotNone(error)
        self.assertIn('Database error', error)

        # User should still exist
        self.assertTrue(User.objects.filter(username='deleteuser').exists())


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@example.com'
)
class SendDeletionConfirmationEmailTest(TestCase):
    """Test send_deletion_confirmation_email function"""

    @patch('active_interview_app.user_data_utils.send_mail')
    def test_send_deletion_confirmation_email_success(self, mock_send_mail):
        """Test successful deletion confirmation email"""
        send_deletion_confirmation_email('testuser', 'test@example.com')

        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertIn('Account Has Been Deleted', args[0])
        self.assertIn('test@example.com', args[3])

    @patch('active_interview_app.user_data_utils.send_mail')
    def test_send_deletion_confirmation_email_failure(self, mock_send_mail):
        """Test deletion confirmation email failure (should not raise)"""
        mock_send_mail.side_effect = Exception('SMTP error')

        # Should not raise exception
        try:
            send_deletion_confirmation_email('testuser', 'test@example.com')
        except Exception:
            self.fail("send_deletion_confirmation_email raised exception unexpectedly")
