"""
Tests for ExportableReport functionality

This module tests the ExportableReport model, views, and PDF generation.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from active_interview_app.models import (
    Chat, ExportableReport, UploadedJobListing, UploadedResume
)
from active_interview_app.pdf_export import generate_pdf_report, get_score_rating
import json


class ExportableReportModelTest(TestCase):
    """Test the ExportableReport model"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=7,
            messages=[
                {'role': 'assistant', 'content': 'Hello, welcome to the interview.'},
                {'role': 'user', 'content': 'Thank you!'}
            ],
            type='GEN'
        )

    def test_create_exportable_report(self):
        """Test creating an ExportableReport"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            feedback_text='Good job overall.',
            total_questions_asked=10,
            total_responses_given=10
        )

        self.assertEqual(report.chat, self.chat)
        self.assertEqual(report.professionalism_score, 85)
        self.assertEqual(report.subject_knowledge_score, 78)
        self.assertEqual(report.clarity_score, 82)
        self.assertEqual(report.overall_score, 81)
        self.assertEqual(report.total_questions_asked, 10)
        self.assertFalse(report.pdf_generated)

    def test_report_str_method(self):
        """Test the __str__ method of ExportableReport"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80
        )
        self.assertIn('Test Interview', str(report))

    def test_one_to_one_relationship(self):
        """Test that a chat can only have one ExportableReport"""
        ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80
        )

        # Try to create another report for the same chat
        with self.assertRaises(Exception):
            ExportableReport.objects.create(
                chat=self.chat,
                overall_score=85
            )

    def test_question_responses_json_field(self):
        """Test the question_responses JSONField"""
        qa_data = [
            {
                'question': 'What is your experience?',
                'answer': 'I have 5 years of experience.',
                'score': 8,
                'feedback': 'Good answer'
            },
            {
                'question': 'Why do you want this job?',
                'answer': 'I am passionate about the field.',
                'score': 9,
                'feedback': 'Excellent response'
            }
        ]

        report = ExportableReport.objects.create(
            chat=self.chat,
            question_responses=qa_data
        )

        self.assertEqual(len(report.question_responses), 2)
        self.assertEqual(report.question_responses[0]['question'],
                        'What is your experience?')
        self.assertEqual(report.question_responses[1]['score'], 9)


class ExportableReportViewTest(TestCase):
    """Test the ExportableReport views"""

    def setUp(self):
        """Set up test fixtures"""
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
                {'role': 'assistant',
                 'content': 'What is your greatest strength? Professionalism: 85'},
                {'role': 'user', 'content': 'My greatest strength is teamwork.'},
                {'role': 'assistant', 'content': 'Score: 8/10. Good answer.'}
            ],
            type='GEN'
        )

    def test_generate_report_requires_login(self):
        """Test that generating a report requires login"""
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_generate_report_view(self):
        """Test generating a report via the GenerateReportView"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        response = self.client.post(url, follow=True)

        # Check that report was created
        self.assertTrue(ExportableReport.objects.filter(chat=self.chat).exists())
        report = ExportableReport.objects.get(chat=self.chat)

        # Check that statistics were calculated
        self.assertEqual(report.total_questions_asked, 2)
        self.assertEqual(report.total_responses_given, 1)

    def test_export_report_view_requires_login(self):
        """Test that viewing the export report requires login"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80
        )
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_export_report_view(self):
        """Test viewing the export report page"""
        self.client.login(username='testuser', password='testpass123')
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80,
            professionalism_score=85
        )

        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Interview')
        self.assertContains(response, 'Download as PDF')

    def test_export_report_redirects_if_no_report(self):
        """Test that export view redirects if no report exists"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        # Should redirect to generate report
        self.assertEqual(response.status_code, 302)

    def test_download_pdf_requires_login(self):
        """Test that downloading PDF requires login"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80
        )
        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_download_pdf_view(self):
        """Test downloading the PDF report"""
        self.client.login(username='testuser', password='testpass123')
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            feedback_text='Good job overall.'
        )

        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('interview_report', response['Content-Disposition'])

        # Check that pdf_generated flag was set
        report.refresh_from_db()
        self.assertTrue(report.pdf_generated)

    def test_user_can_only_access_own_reports(self):
        """Test that users can only access their own reports"""
        # Create another user and their chat
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        other_chat = Chat.objects.create(
            owner=other_user,
            title='Other Interview',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        other_report = ExportableReport.objects.create(
            chat=other_chat,
            overall_score=75
        )

        # Login as first user
        self.client.login(username='testuser', password='testpass123')

        # Try to access other user's report
        url = reverse('export_report', kwargs={'chat_id': other_chat.id})
        response = self.client.get(url)

        # Should be forbidden (403) or redirect
        self.assertIn(response.status_code, [403, 302])


class PDFExportUtilityTest(TestCase):
    """Test the PDF export utility functions"""

    def setUp(self):
        """Set up test fixtures"""
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
        self.report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            feedback_text='Good job overall.',
            question_responses=[
                {
                    'question': 'What is your experience?',
                    'answer': 'I have 5 years of experience.',
                    'score': 8,
                    'feedback': 'Good answer'
                }
            ],
            total_questions_asked=10,
            total_responses_given=10
        )

    def test_get_score_rating(self):
        """Test the get_score_rating utility function"""
        self.assertEqual(get_score_rating(95), 'Excellent')
        self.assertEqual(get_score_rating(85), 'Good')
        self.assertEqual(get_score_rating(70), 'Fair')
        self.assertEqual(get_score_rating(50), 'Needs Improvement')
        self.assertEqual(get_score_rating(None), 'N/A')

    def test_generate_pdf_report(self):
        """Test generating a PDF report"""
        pdf_content = generate_pdf_report(self.report)

        # Check that PDF content is returned
        self.assertIsNotNone(pdf_content)
        self.assertIsInstance(pdf_content, bytes)

        # Check that it starts with PDF header
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_generate_pdf_with_minimal_data(self):
        """Test generating PDF with minimal report data"""
        minimal_report = ExportableReport.objects.create(
            chat=Chat.objects.create(
                owner=self.user,
                title='Minimal Interview',
                difficulty=5,
                messages=[],
                type='GEN'
            ),
            total_questions_asked=0,
            total_responses_given=0
        )

        pdf_content = generate_pdf_report(minimal_report)

        # Should still generate valid PDF
        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))


class ExportableReportSerializerTest(TestCase):
    """Test the ExportableReportSerializer"""

    def setUp(self):
        """Set up test fixtures"""
        from active_interview_app.serializers import ExportableReportSerializer

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
        self.report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            overall_score=81
        )
        self.serializer = ExportableReportSerializer(instance=self.report)

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        data = self.serializer.data

        self.assertIn('id', data)
        self.assertIn('chat', data)
        self.assertIn('chat_title', data)
        self.assertIn('chat_type', data)
        self.assertIn('chat_difficulty', data)
        self.assertIn('professionalism_score', data)
        self.assertIn('overall_score', data)

    def test_serializer_chat_related_fields(self):
        """Test that chat-related fields are correctly serialized"""
        data = self.serializer.data

        self.assertEqual(data['chat_title'], 'Test Interview')
        self.assertEqual(data['chat_difficulty'], 7)
        self.assertEqual(data['chat_type'], 'General')
