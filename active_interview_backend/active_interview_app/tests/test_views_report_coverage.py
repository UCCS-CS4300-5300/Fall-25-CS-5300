"""
Comprehensive tests for report generation views to increase coverage.

This module provides additional test coverage for GenerateReportView,
ExportReportView, DownloadPDFReportView, and DownloadCSVReportView,
focusing on edge cases and error handling paths.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from active_interview_app.models import Chat, ExportableReport, UploadedJobListing, UploadedResume


class GenerateReportViewCoverageTest(TestCase):
    """Comprehensive tests for GenerateReportView"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=7,
            messages=[
                {'role': 'assistant', 'content': 'Tell me about yourself.'},
                {'role': 'user', 'content': 'I am a software engineer with 5 years experience.'},
                {'role': 'assistant', 'content': 'What are your strengths?'},
                {'role': 'user', 'content': 'My strengths include problem-solving and teamwork.'}
            ],
            type='GEN'
        )

    def test_generate_report_with_ai_success(self):
        """Test report generation with successful AI call"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        # Mock AI to return realistic scores
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "85\n78\n82\n81"

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.return_value = mock_response
                response = self.client.post(url, follow=True)

        self.assertEqual(response.status_code, 200)
        report = ExportableReport.objects.get(chat=self.chat)
        self.assertEqual(report.professionalism_score, 85)
        self.assertEqual(report.subject_knowledge_score, 78)
        self.assertEqual(report.clarity_score, 82)
        self.assertEqual(report.overall_score, 81)

    def test_generate_report_ai_exception_handling(self):
        """Test report generation when AI raises exception"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.side_effect = Exception('API Error')
                response = self.client.post(url, follow=True)

        # Should still create report with default scores
        self.assertEqual(response.status_code, 200)
        report = ExportableReport.objects.get(chat=self.chat)
        self.assertEqual(report.professionalism_score, 0)

    def test_generate_report_ai_invalid_response(self):
        """Test report generation when AI returns invalid format"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "invalid\nresponse\nformat"

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.return_value = mock_response
                response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        # Should default to 0 when parsing fails
        self.assertEqual(report.professionalism_score, 0)

    def test_generate_report_ai_incomplete_scores(self):
        """Test report generation when AI returns incomplete scores"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "85\n78"  # Only 2 scores instead of 4

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.return_value = mock_response
                response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        # Should default to 0 when not enough scores
        self.assertEqual(report.professionalism_score, 0)

    def test_generate_report_deletes_existing_report(self):
        """Test that generating a new report deletes the old one"""
        self.client.login(username='testuser', password='testpass123')

        # Create an existing report
        old_report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=50
        )
        old_report_id = old_report.id

        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        with patch('active_interview_app.views._ai_available', return_value=False):
            response = self.client.post(url, follow=True)

        # Old report should be deleted
        self.assertFalse(ExportableReport.objects.filter(id=old_report_id).exists())
        # New report should exist
        self.assertTrue(ExportableReport.objects.filter(chat=self.chat).exists())

    def test_generate_report_rationale_parsing(self):
        """Test parsing of AI-generated rationales"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        # Mock scores response
        mock_scores_response = MagicMock()
        mock_scores_response.choices = [MagicMock()]
        mock_scores_response.choices[0].message.content = "85\n78\n82\n81"

        # Mock rationales response
        mock_rationale_response = MagicMock()
        mock_rationale_response.choices = [MagicMock()]
        mock_rationale_response.choices[0].message.content = """
Professionalism: The candidate demonstrated strong professional behavior.

Subject Knowledge: Good understanding of core concepts.

Clarity: Communication was clear and concise.

Overall: Solid performance overall.
"""

        # Mock feedback response
        mock_feedback_response = MagicMock()
        mock_feedback_response.choices = [MagicMock()]
        mock_feedback_response.choices[0].message.content = "Great job!"

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                # Return different responses for each call
                mock_client.return_value.chat.completions.create.side_effect = [
                    mock_scores_response,
                    mock_feedback_response,
                    mock_rationale_response
                ]
                response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        self.assertIn('professional behavior', report.professionalism_rationale)
        self.assertIn('core concepts', report.subject_knowledge_rationale)
        self.assertIn('clear and concise', report.clarity_rationale)
        self.assertIn('Solid performance', report.overall_rationale)

    def test_generate_report_rationale_parsing_multiline(self):
        """Test parsing rationales with multiline content"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        mock_scores_response = MagicMock()
        mock_scores_response.choices = [MagicMock()]
        mock_scores_response.choices[0].message.content = "85\n78\n82\n81"

        mock_rationale_response = MagicMock()
        mock_rationale_response.choices = [MagicMock()]
        mock_rationale_response.choices[0].message.content = """
Professionalism: The candidate was professional.
They maintained good eye contact and posture.

Subject Knowledge: Strong technical skills demonstrated.
Some gaps in advanced topics.

Clarity: Clear communication throughout.

Overall: Good performance.
"""

        mock_feedback_response = MagicMock()
        mock_feedback_response.choices = [MagicMock()]
        mock_feedback_response.choices[0].message.content = "Good work!"

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.side_effect = [
                    mock_scores_response,
                    mock_feedback_response,
                    mock_rationale_response
                ]
                response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        # Should capture multiline content
        self.assertIn('eye contact', report.professionalism_rationale)
        self.assertIn('advanced topics', report.subject_knowledge_rationale)

    def test_generate_report_statistics_calculation(self):
        """Test that statistics are correctly calculated from messages"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        with patch('active_interview_app.views._ai_available', return_value=False):
            response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        # 2 assistant messages (questions)
        self.assertEqual(report.total_questions_asked, 2)
        # 2 user messages (responses)
        self.assertEqual(report.total_responses_given, 2)


class ExportReportViewCoverageTest(TestCase):
    """Comprehensive tests for ExportReportView"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=7,
            messages=[],
            type='GEN'
        )

    def test_export_report_with_job_listing(self):
        """Test export view displays job listing info when available"""
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Software Engineer Position',
            filename='job.pdf',
            content='Job description'
        )
        self.chat.job_listing = job_listing
        self.chat.save()

        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Software Engineer Position')

    def test_export_report_with_resume(self):
        """Test export view displays resume info when available"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='John Doe Resume',
            content='Resume content',
            original_filename='resume.pdf'
        )
        self.chat.resume = resume
        self.chat.save()

        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe Resume')


class DownloadPDFReportViewCoverageTest(TestCase):
    """Comprehensive tests for DownloadPDFReportView"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview & Report',
            difficulty=7,
            messages=[],
            type='GEN'
        )

    def test_download_pdf_no_report_exists(self):
        """Test PDF download when report doesn't exist"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        # Should redirect to chat results with error message
        self.assertEqual(response.status_code, 302)

    def test_download_pdf_filename_with_special_chars(self):
        """Test PDF download with special characters in filename"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Special characters should be slugified
        self.assertIn('test-interview', response['Content-Disposition'].lower())

    def test_download_pdf_with_rationales(self):
        """Test PDF download includes rationales"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=85,
            professionalism_score=88,
            subject_knowledge_score=82,
            clarity_score=86,
            professionalism_rationale='Excellent professional behavior demonstrated.',
            subject_knowledge_rationale='Strong knowledge with minor gaps.',
            clarity_rationale='Very clear communication.',
            overall_rationale='Outstanding performance overall.'
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Report should be marked as generated
        report.refresh_from_db()
        self.assertTrue(report.pdf_generated)


class DownloadCSVReportViewCoverageTest(TestCase):
    """Comprehensive tests for DownloadCSVReportView"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=7,
            messages=[],
            type='ISK'  # Industry Skills type
        )

    def test_download_csv_no_report_exists(self):
        """Test CSV download when report doesn't exist"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        # Should redirect to chat results with error message
        self.assertEqual(response.status_code, 302)

    def test_download_csv_with_all_data(self):
        """Test CSV download with complete report data"""
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Senior Developer',
            filename='job.pdf',
            content='Job description'
        )
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Candidate Resume',
            content='Resume content',
            original_filename='resume.pdf'
        )
        self.chat.job_listing = job_listing
        self.chat.resume = resume
        self.chat.save()

        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            professionalism_weight=30,
            subject_knowledge_weight=40,
            clarity_weight=30,
            professionalism_rationale='Professional throughout.',
            subject_knowledge_rationale='Good knowledge.',
            clarity_rationale='Clear communication.',
            overall_rationale='Solid performance.',
            feedback_text='Great job overall!',
            total_questions_asked=15,
            total_responses_given=15,
            interview_duration_minutes=45
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')

        # Verify CSV contains key data
        self.assertIn('Industry Skills', content)  # Interview type
        self.assertIn('85/100', content)  # Professionalism score
        self.assertIn('30%', content)  # Weight
        self.assertIn('Professional throughout', content)  # Rationale
        self.assertIn('Senior Developer', content)  # Job listing
        self.assertIn('Candidate Resume', content)  # Resume
        self.assertIn('45 minutes', content)  # Duration

    def test_download_csv_score_ratings(self):
        """Test CSV includes score ratings"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=95,  # Excellent
            subject_knowledge_score=82,  # Good
            clarity_score=68,  # Fair
            overall_score=80,
            total_questions_asked=10,
            total_responses_given=10
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        content = response.content.decode('utf-8')
        self.assertIn('Excellent', content)
        self.assertIn('Good', content)
        self.assertIn('Fair', content)

    def test_download_csv_without_optional_data(self):
        """Test CSV download with minimal data (no job/resume/duration)"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=80,
            overall_score=78,
            total_questions_asked=5,
            total_responses_given=5,
            interview_duration_minutes=None
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Should still generate valid CSV
        content = response.content.decode('utf-8')
        self.assertIn('Interview Report', content)


class ReportViewsPermissionTest(TestCase):
    """Test permission checking in report views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123'
        )
        self.chat = Chat.objects.create(
            owner=self.user1,
            title='User1 Interview',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        self.report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=75
        )

    def test_generate_report_unauthorized_user(self):
        """Test that only chat owner can generate report"""
        self.client.login(username='user2', password='pass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})
        response = self.client.post(url)

        # Should be forbidden
        self.assertIn(response.status_code, [403, 302])

    def test_export_report_unauthorized_user(self):
        """Test that only chat owner can view export page"""
        self.client.login(username='user2', password='pass123')
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        # Should be forbidden
        self.assertIn(response.status_code, [403, 302])

    def test_download_pdf_unauthorized_user(self):
        """Test that only chat owner can download PDF"""
        self.client.login(username='user2', password='pass123')
        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        # Should be forbidden
        self.assertIn(response.status_code, [403, 302])

    def test_download_csv_unauthorized_user(self):
        """Test that only chat owner can download CSV"""
        self.client.login(username='user2', password='pass123')
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        # Should be forbidden
        self.assertIn(response.status_code, [403, 302])
