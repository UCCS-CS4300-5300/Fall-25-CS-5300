"""
Tests for interview response latency tracking.

Related to Issues #20, #54 (Latency Budget).

Test coverage:
- InterviewResponseLatency model and methods
- LatencyTracker context manager
- Latency tracking utilities
- Alert triggering for threshold violations
- Compliance rate calculations
- Session statistics
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from unittest.mock import patch, MagicMock
import time

from active_interview_app.observability_models import (
    InterviewResponseLatency,
    ErrorLog
)
from active_interview_app.models import (
    Chat,
    UploadedResume,
    UploadedJobListing
)
from active_interview_app.latency_utils import (
    track_interview_response_latency,
    trigger_latency_alert,
    LatencyTracker,
    check_session_compliance,
    get_global_compliance_stats,
    get_latency_threshold
)
from .test_credentials import TEST_PASSWORD


class InterviewResponseLatencyModelTests(TestCase):
    """Test InterviewResponseLatency model functionality."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )

        # Create a resume
        fake_resume = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='My resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume,
            skills=['Python', 'Django']
        )

        # Create a job listing
        fake_job = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Software Engineer',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job,
            required_skills=['Python', 'Django']
        )

        # Create a chat session
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=5,
            type=Chat.GENERAL,
            interview_type=Chat.PRACTICE,
            resume=self.resume,
            job_listing=self.job_listing,
            messages=[]
        )

        self.now = timezone.now()

    def test_create_latency_record(self):
        """Test creating a basic InterviewResponseLatency record."""
        latency = InterviewResponseLatency.objects.create(
            chat=self.chat,
            user=self.user,
            response_time_ms=1500.5,
            ai_processing_time_ms=1200.0,
            question_number=1,
            interview_type=Chat.PRACTICE,
            exceeded_threshold=False,
            threshold_ms=2000
        )

        self.assertEqual(latency.chat, self.chat)
        self.assertEqual(latency.user, self.user)
        self.assertEqual(latency.response_time_ms, 1500.5)
        self.assertEqual(latency.ai_processing_time_ms, 1200.0)
        self.assertEqual(latency.question_number, 1)
        self.assertEqual(latency.interview_type, Chat.PRACTICE)
        self.assertFalse(latency.exceeded_threshold)
        self.assertEqual(latency.threshold_ms, 2000)
        self.assertIsNotNone(latency.timestamp)

    def test_is_within_budget_property(self):
        """Test is_within_budget property."""
        # Within budget
        latency_fast = InterviewResponseLatency.objects.create(
            chat=self.chat,
            user=self.user,
            response_time_ms=1500.0,
            question_number=1,
            interview_type=Chat.PRACTICE,
            threshold_ms=2000
        )
        self.assertTrue(latency_fast.is_within_budget)

        # Exceeded budget
        latency_slow = InterviewResponseLatency.objects.create(
            chat=self.chat,
            user=self.user,
            response_time_ms=2500.0,
            question_number=2,
            interview_type=Chat.PRACTICE,
            exceeded_threshold=True,
            threshold_ms=2000
        )
        self.assertFalse(latency_slow.is_within_budget)

    def test_latency_budget_percentage(self):
        """Test latency budget percentage calculation."""
        latency = InterviewResponseLatency.objects.create(
            chat=self.chat,
            user=self.user,
            response_time_ms=1500.0,
            question_number=1,
            interview_type=Chat.PRACTICE,
            threshold_ms=2000
        )

        # 1500ms / 2000ms = 75%
        self.assertEqual(latency.latency_budget_percentage, 75.0)

    def test_str_representation(self):
        """Test string representation."""
        latency = InterviewResponseLatency.objects.create(
            chat=self.chat,
            user=self.user,
            response_time_ms=1500.0,
            question_number=1,
            interview_type=Chat.PRACTICE,
            threshold_ms=2000
        )

        str_repr = str(latency)
        self.assertIn('✓ OK', str_repr)
        self.assertIn('Q1', str_repr)
        self.assertIn('1500ms', str_repr)

        # Slow response
        latency_slow = InterviewResponseLatency.objects.create(
            chat=self.chat,
            user=self.user,
            response_time_ms=2500.0,
            question_number=2,
            interview_type=Chat.PRACTICE,
            exceeded_threshold=True,
            threshold_ms=2000
        )

        str_repr_slow = str(latency_slow)
        self.assertIn('⚠️ SLOW', str_repr_slow)

    def test_get_session_stats_no_data(self):
        """Test get_session_stats with no latency data."""
        stats = InterviewResponseLatency.get_session_stats(self.chat.id)

        self.assertEqual(stats['total_responses'], 0)
        self.assertEqual(stats['within_budget'], 0)
        self.assertEqual(stats['exceeded_budget'], 0)
        self.assertEqual(stats['budget_compliance_rate'], 0.0)

    def test_get_session_stats_with_data(self):
        """Test get_session_stats with latency data."""
        # Create 10 responses: 9 within budget, 1 exceeded (90% compliance)
        for i in range(9):
            InterviewResponseLatency.objects.create(
                chat=self.chat,
                user=self.user,
                response_time_ms=1500.0 + (i * 50),
                question_number=i + 1,
                interview_type=Chat.PRACTICE,
                exceeded_threshold=False,
                threshold_ms=2000
            )

        # One slow response
        InterviewResponseLatency.objects.create(
            chat=self.chat,
            user=self.user,
            response_time_ms=2500.0,
            question_number=10,
            interview_type=Chat.PRACTICE,
            exceeded_threshold=True,
            threshold_ms=2000
        )

        stats = InterviewResponseLatency.get_session_stats(self.chat.id)

        self.assertEqual(stats['total_responses'], 10)
        self.assertEqual(stats['within_budget'], 9)
        self.assertEqual(stats['exceeded_budget'], 1)
        self.assertEqual(stats['budget_compliance_rate'], 90.0)
        self.assertGreater(stats['p50'], 0)
        self.assertGreater(stats['mean'], 0)

    def test_calculate_compliance_rate_no_data(self):
        """Test calculate_compliance_rate with no data."""
        compliance = InterviewResponseLatency.calculate_compliance_rate()

        self.assertEqual(compliance['total_responses'], 0)
        self.assertEqual(compliance['compliance_rate'], 0.0)
        self.assertFalse(compliance['meets_target'])

    def test_calculate_compliance_rate_with_data(self):
        """Test calculate_compliance_rate with latency data."""
        now = timezone.now()

        # Create responses in the time window
        for i in range(10):
            InterviewResponseLatency.objects.create(
                chat=self.chat,
                user=self.user,
                response_time_ms=1500.0,
                question_number=i + 1,
                interview_type=Chat.PRACTICE,
                exceeded_threshold=False,
                threshold_ms=2000,
                timestamp=now - timedelta(minutes=30)
            )

        compliance = InterviewResponseLatency.calculate_compliance_rate(
            start_time=now - timedelta(hours=1),
            end_time=now
        )

        self.assertEqual(compliance['total_responses'], 10)
        self.assertEqual(compliance['within_budget'], 10)
        self.assertEqual(compliance['compliance_rate'], 100.0)
        self.assertTrue(compliance['meets_target'])
        self.assertEqual(compliance['target_rate'], 90.0)

    def test_calculate_compliance_rate_by_interview_type(self):
        """Test calculate_compliance_rate filtered by interview type."""
        now = timezone.now()

        # Create PRACTICE responses
        for i in range(5):
            InterviewResponseLatency.objects.create(
                chat=self.chat,
                user=self.user,
                response_time_ms=1500.0,
                question_number=i + 1,
                interview_type=Chat.PRACTICE,
                exceeded_threshold=False,
                threshold_ms=2000,
                timestamp=now - timedelta(minutes=30)
            )

        # Create INVITED responses
        invited_chat = Chat.objects.create(
            owner=self.user,
            title='Invited Interview',
            difficulty=5,
            type=Chat.GENERAL,
            interview_type=Chat.INVITED,
            resume=self.resume,
            job_listing=self.job_listing,
            messages=[]
        )

        for i in range(3):
            InterviewResponseLatency.objects.create(
                chat=invited_chat,
                user=self.user,
                response_time_ms=1800.0,
                question_number=i + 1,
                interview_type=Chat.INVITED,
                exceeded_threshold=False,
                threshold_ms=2000,
                timestamp=now - timedelta(minutes=30)
            )

        # Filter by PRACTICE
        practice_compliance = InterviewResponseLatency.calculate_compliance_rate(
            interview_type=Chat.PRACTICE,
            start_time=now - timedelta(hours=1),
            end_time=now
        )
        self.assertEqual(practice_compliance['total_responses'], 5)

        # Filter by INVITED
        invited_compliance = InterviewResponseLatency.calculate_compliance_rate(
            interview_type=Chat.INVITED,
            start_time=now - timedelta(hours=1),
            end_time=now
        )
        self.assertEqual(invited_compliance['total_responses'], 3)

    def test_calculate_percentiles(self):
        """Test calculate_percentiles method."""
        now = timezone.now()

        # Create responses with varying latencies
        latencies = [1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800]
        for i, latency_ms in enumerate(latencies):
            InterviewResponseLatency.objects.create(
                chat=self.chat,
                user=self.user,
                response_time_ms=latency_ms,
                question_number=i + 1,
                interview_type=Chat.PRACTICE,
                exceeded_threshold=(latency_ms > 2000),
                threshold_ms=2000,
                timestamp=now - timedelta(minutes=30)
            )

        percentiles = InterviewResponseLatency.calculate_percentiles(
            start_time=now - timedelta(hours=1),
            end_time=now
        )

        self.assertEqual(percentiles['count'], 10)
        self.assertEqual(percentiles['min'], 1000)
        self.assertEqual(percentiles['max'], 2800)
        self.assertGreater(percentiles['p50'], 1000)
        self.assertLess(percentiles['p50'], 2800)
        self.assertGreater(percentiles['p95'], percentiles['p50'])


class LatencyUtilsTests(TestCase):
    """Test latency utility functions."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )

        fake_resume = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='My resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume,
            skills=['Python']
        )

        fake_job = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Developer',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=5,
            type=Chat.GENERAL,
            interview_type=Chat.PRACTICE,
            resume=self.resume,
            job_listing=self.job_listing,
            messages=[]
        )

    def test_get_latency_threshold(self):
        """Test get_latency_threshold function."""
        threshold = get_latency_threshold()
        self.assertEqual(threshold, 2000)  # Default threshold

    def test_track_interview_response_latency_within_budget(self):
        """Test tracking latency within budget."""
        latency_record = track_interview_response_latency(
            chat=self.chat,
            response_time_ms=1500.0,
            ai_processing_time_ms=1200.0,
            question_number=1
        )

        self.assertIsNotNone(latency_record)
        self.assertEqual(latency_record.chat, self.chat)
        self.assertEqual(latency_record.response_time_ms, 1500.0)
        self.assertEqual(latency_record.ai_processing_time_ms, 1200.0)
        self.assertEqual(latency_record.question_number, 1)
        self.assertFalse(latency_record.exceeded_threshold)

    def test_track_interview_response_latency_exceeded_budget(self):
        """Test tracking latency that exceeds budget."""
        with self.assertLogs('active_interview_app.latency_utils', level='WARNING') as logs:
            latency_record = track_interview_response_latency(
                chat=self.chat,
                response_time_ms=2500.0,
                ai_processing_time_ms=2200.0,
                question_number=1
            )

        self.assertTrue(latency_record.exceeded_threshold)
        # Check that warning was logged
        self.assertTrue(any('Latency budget exceeded' in log for log in logs.output))

    def test_track_interview_response_latency_auto_question_number(self):
        """Test auto-calculation of question_number."""
        # Create first response
        latency1 = track_interview_response_latency(
            chat=self.chat,
            response_time_ms=1500.0
        )
        self.assertEqual(latency1.question_number, 1)

        # Create second response (should auto-increment)
        latency2 = track_interview_response_latency(
            chat=self.chat,
            response_time_ms=1600.0
        )
        self.assertEqual(latency2.question_number, 2)

    def test_trigger_latency_alert(self):
        """Test triggering latency alert for severe violations."""
        latency_record = InterviewResponseLatency.objects.create(
            chat=self.chat,
            user=self.user,
            response_time_ms=6000.0,
            question_number=1,
            interview_type=Chat.PRACTICE,
            exceeded_threshold=True,
            threshold_ms=2000
        )

        with self.assertLogs('active_interview_app.latency_utils', level='ERROR'):
            trigger_latency_alert(latency_record)

        # Check that ErrorLog was created
        error_logs = ErrorLog.objects.filter(error_type='LatencyViolation')
        self.assertEqual(error_logs.count(), 1)
        self.assertEqual(error_logs.first().error_message, 'Severe latency violation: 6000ms')

    def test_check_session_compliance_no_data(self):
        """Test check_session_compliance with no data."""
        stats = check_session_compliance(self.chat)

        self.assertIsNone(stats['meets_target'])
        self.assertIn('No latency data available', stats['message'])

    def test_check_session_compliance_passes(self):
        """Test check_session_compliance when session passes."""
        # Create 10 responses: all within budget (100% compliance)
        for i in range(10):
            InterviewResponseLatency.objects.create(
                chat=self.chat,
                user=self.user,
                response_time_ms=1500.0,
                question_number=i + 1,
                interview_type=Chat.PRACTICE,
                exceeded_threshold=False,
                threshold_ms=2000
            )

        stats = check_session_compliance(self.chat)

        self.assertTrue(stats['meets_target'])
        self.assertIn('✓ PASS', stats['message'])
        self.assertEqual(stats['budget_compliance_rate'], 100.0)

    def test_check_session_compliance_fails(self):
        """Test check_session_compliance when session fails."""
        # Create 10 responses: only 8 within budget (80% compliance < 90% target)
        for i in range(8):
            InterviewResponseLatency.objects.create(
                chat=self.chat,
                user=self.user,
                response_time_ms=1500.0,
                question_number=i + 1,
                interview_type=Chat.PRACTICE,
                exceeded_threshold=False,
                threshold_ms=2000
            )

        for i in range(2):
            InterviewResponseLatency.objects.create(
                chat=self.chat,
                user=self.user,
                response_time_ms=2500.0,
                question_number=i + 9,
                interview_type=Chat.PRACTICE,
                exceeded_threshold=True,
                threshold_ms=2000
            )

        stats = check_session_compliance(self.chat)

        self.assertFalse(stats['meets_target'])
        self.assertIn('✗ FAIL', stats['message'])
        self.assertEqual(stats['budget_compliance_rate'], 80.0)

    def test_get_global_compliance_stats(self):
        """Test get_global_compliance_stats function."""
        now = timezone.now()

        # Create some latency records
        for i in range(10):
            InterviewResponseLatency.objects.create(
                chat=self.chat,
                user=self.user,
                response_time_ms=1500.0,
                question_number=i + 1,
                interview_type=Chat.PRACTICE,
                exceeded_threshold=False,
                threshold_ms=2000,
                timestamp=now - timedelta(hours=12)
            )

        stats = get_global_compliance_stats(hours=24)

        self.assertEqual(stats['total_responses'], 10)
        self.assertEqual(stats['time_window_hours'], 24)
        self.assertEqual(stats['interview_type'], 'ALL')
        self.assertIn('p50', stats)
        self.assertIn('compliance_rate', stats)


class LatencyTrackerTests(TestCase):
    """Test LatencyTracker context manager."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )

        fake_resume = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='My resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume,
            skills=['Python']
        )

        fake_job = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Developer',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=5,
            type=Chat.GENERAL,
            interview_type=Chat.PRACTICE,
            resume=self.resume,
            job_listing=self.job_listing,
            messages=[]
        )

    def test_latency_tracker_basic_usage(self):
        """Test basic LatencyTracker usage."""
        with LatencyTracker(self.chat, question_number=1):
            time.sleep(0.1)  # Simulate work

        # Check that latency was recorded
        latency_records = InterviewResponseLatency.objects.filter(chat=self.chat)
        self.assertEqual(latency_records.count(), 1)

        record = latency_records.first()
        self.assertEqual(record.question_number, 1)
        self.assertGreaterEqual(record.response_time_ms, 100)  # At least 100ms
        self.assertLess(record.response_time_ms, 200)  # Less than 200ms

    def test_latency_tracker_with_ai_processing(self):
        """Test LatencyTracker with AI processing time tracking."""
        with LatencyTracker(self.chat, question_number=1) as tracker:
            time.sleep(0.05)  # Before AI
            with tracker.track_ai_processing():
                time.sleep(0.1)  # Simulate AI processing
            time.sleep(0.05)  # After AI

        record = InterviewResponseLatency.objects.get(chat=self.chat, question_number=1)
        self.assertGreaterEqual(record.response_time_ms, 200)  # Total time
        self.assertGreaterEqual(record.ai_processing_time_ms, 100)  # AI time
        self.assertLess(record.ai_processing_time_ms, record.response_time_ms)

    def test_latency_tracker_auto_question_number(self):
        """Test LatencyTracker with auto-calculated question_number."""
        # First call
        with LatencyTracker(self.chat):
            time.sleep(0.01)

        # Second call
        with LatencyTracker(self.chat):
            time.sleep(0.01)

        records = InterviewResponseLatency.objects.filter(chat=self.chat).order_by('question_number')
        self.assertEqual(records.count(), 2)
        self.assertEqual(records[0].question_number, 1)
        self.assertEqual(records[1].question_number, 2)

    def test_latency_tracker_exception_handling(self):
        """Test that LatencyTracker doesn't suppress exceptions."""
        with self.assertRaises(ValueError):
            with LatencyTracker(self.chat, question_number=1):
                raise ValueError("Test exception")

        # Latency should still be recorded
        latency_records = InterviewResponseLatency.objects.filter(chat=self.chat)
        self.assertEqual(latency_records.count(), 1)


class IntegrationTests(TestCase):
    """Integration tests for latency tracking in views."""

    def setUp(self):
        """Create test data and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client.login(username='testuser', password=TEST_PASSWORD)

        fake_resume = SimpleUploadedFile("resume.pdf", b"resume content")
        self.resume = UploadedResume.objects.create(
            user=self.user,
            title='Test Resume',
            content='My resume content',
            filesize=100,
            original_filename='resume.pdf',
            file=fake_resume,
            skills=['Python']
        )

        fake_job = SimpleUploadedFile("job.txt", b"job content")
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Developer',
            content='Job description',
            filepath='/fake/path',
            filename='job.txt',
            file=fake_job
        )

        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=5,
            type=Chat.GENERAL,
            interview_type=Chat.PRACTICE,
            resume=self.resume,
            job_listing=self.job_listing,
            messages=[
                {"role": "system", "content": "You are an interviewer."},
                {"role": "assistant", "content": "Hello! Let's begin."}
            ]
        )

    @patch('active_interview_app.views.record_openai_usage')
    @patch('active_interview_app.views.ai_available', return_value=True)
    @patch('active_interview_app.views.get_client_and_model')
    def test_chat_view_post_tracks_latency(self, mock_get_client_and_model, mock_ai_available, mock_record_usage):
        """Test that ChatView POST tracks latency."""
        # Mock OpenAI response with proper attributes
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test response."
        mock_response.model = 'gpt-4'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        # get_client_and_model returns (client, model, tier_info)
        mock_get_client_and_model.return_value = (mock_client, 'gpt-4', {'tier': 'test'})

        # Make POST request
        response = self.client.post(
            f'/chat/{self.chat.id}/',
            {'message': 'What is Python?'}
        )

        self.assertEqual(response.status_code, 200)

        # Check that latency was tracked
        latency_records = InterviewResponseLatency.objects.filter(chat=self.chat)
        self.assertGreater(latency_records.count(), 0)

        record = latency_records.first()
        self.assertEqual(record.chat, self.chat)
        self.assertEqual(record.user, self.user)
        self.assertGreater(record.response_time_ms, 0)
