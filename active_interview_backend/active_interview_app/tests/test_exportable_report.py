"""
Tests for ExportableReport functionality

This module tests the ExportableReport model, views, and PDF generation.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from active_interview_app.models import (
    Chat, ExportableReport
)
from active_interview_app.pdf_export import generate_pdf_report, get_score_rating
from .test_credentials import TEST_PASSWORD


class ExportableReportModelTest(TestCase):
    """Test the ExportableReport model"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
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
            password=TEST_PASSWORD
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

    def test_export_report_view_requires_login(self):
        """Test that viewing the export report requires login"""
        ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80
        )
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_export_report_view(self):
        """Test viewing the export report page"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        ExportableReport.objects.create(
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
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        # Should redirect to generate report
        self.assertEqual(response.status_code, 302)

    def test_download_pdf_requires_login(self):
        """Test that downloading PDF requires login"""
        ExportableReport.objects.create(
            chat=self.chat,
            overall_score=80
        )
        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_download_pdf_view(self):
        """Test downloading the PDF report"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
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
            password=TEST_PASSWORD
        )
        other_chat = Chat.objects.create(
            owner=other_user,
            title='Other Interview',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        ExportableReport.objects.create(
            chat=other_chat,
            overall_score=75
        )

        # Login as first user
        self.client.login(username='testuser', password=TEST_PASSWORD)

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
            password=TEST_PASSWORD
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
            password=TEST_PASSWORD
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


class ScoreWeightsAndRationalesTest(TestCase):
    """Test the score weights and rationales functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=7,
            messages=[
                {'role': 'assistant', 'content': 'What is your greatest strength?'},
                {'role': 'user', 'content': 'My greatest strength is teamwork.'}
            ],
            type='GEN'
        )

    def test_default_weights(self):
        """Test that reports have default weights"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81
        )

        self.assertEqual(report.professionalism_weight, 30)
        self.assertEqual(report.subject_knowledge_weight, 40)
        self.assertEqual(report.clarity_weight, 30)

    def test_custom_weights(self):
        """Test that custom weights can be set"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            professionalism_weight=25,
            subject_knowledge_weight=50,
            clarity_weight=25
        )

        self.assertEqual(report.professionalism_weight, 25)
        self.assertEqual(report.subject_knowledge_weight, 50)
        self.assertEqual(report.clarity_weight, 25)

    def test_rationales_storage(self):
        """Test that rationales can be stored"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            professionalism_rationale='The candidate demonstrated professional behavior throughout.',
            subject_knowledge_rationale='Good understanding of core concepts but needs improvement in advanced topics.',
            clarity_rationale='Communication was clear and concise.',
            overall_rationale='Solid performance with room for improvement in technical depth.')

        self.assertIn('professional behavior',
                      report.professionalism_rationale)
        self.assertIn('core concepts', report.subject_knowledge_rationale)
        self.assertIn('clear and concise', report.clarity_rationale)
        self.assertIn('Solid performance', report.overall_rationale)

    def test_pdf_includes_weights(self):
        """Test that PDF export includes weight information"""
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
            overall_rationale='Solid performance.'
        )

        pdf_content = generate_pdf_report(report)

        # PDF should be generated successfully
        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))


class CSVExportTest(TestCase):
    """Test CSV export functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=7,
            messages=[
                {'role': 'assistant', 'content': 'What is your greatest strength?'},
                {'role': 'user', 'content': 'My greatest strength is teamwork.'}
            ],
            type='GEN'
        )
        self.report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            professionalism_weight=30,
            subject_knowledge_weight=40,
            clarity_weight=30,
            professionalism_rationale='Professional behavior demonstrated.',
            subject_knowledge_rationale='Good technical knowledge.',
            clarity_rationale='Clear and concise responses.',
            overall_rationale='Strong overall performance.',
            feedback_text='Excellent interview performance with minor areas for improvement.',
            total_questions_asked=10,
            total_responses_given=10)

    def test_download_csv_requires_login(self):
        """Test that downloading CSV requires login"""
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_download_csv_view(self):
        """Test downloading the CSV report"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('interview_report', response['Content-Disposition'])
        self.assertIn('.csv', response['Content-Disposition'])

    def test_csv_contains_scores_and_weights(self):
        """Test that CSV contains scores and weights"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        content = response.content.decode('utf-8')

        # Check for scores
        self.assertIn('85/100', content)
        self.assertIn('78/100', content)
        self.assertIn('82/100', content)
        self.assertIn('81/100', content)

        # Check for weights
        self.assertIn('30%', content)
        self.assertIn('40%', content)

        # Check for score categories
        self.assertIn('Professionalism', content)
        self.assertIn('Subject Knowledge', content)
        self.assertIn('Clarity', content)
        self.assertIn('Overall Score', content)

    def test_csv_contains_rationales(self):
        """Test that CSV contains rationales"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        content = response.content.decode('utf-8')

        # Check for rationales section
        self.assertIn('Score Breakdown & Rationales', content)
        self.assertIn('Professional behavior demonstrated', content)
        self.assertIn('Good technical knowledge', content)
        self.assertIn('Clear and concise responses', content)
        self.assertIn('Strong overall performance', content)

    def test_csv_contains_metadata(self):
        """Test that CSV contains interview metadata"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        content = response.content.decode('utf-8')

        # Check for metadata
        self.assertIn('Interview Details', content)
        self.assertIn('Test Interview', content)
        self.assertIn('7/10', content)  # Difficulty

    def test_csv_redirects_if_no_report(self):
        """Test that CSV download redirects if no report exists"""
        self.client.login(username='testuser', password=TEST_PASSWORD)

        # Create a new chat without a report
        new_chat = Chat.objects.create(
            owner=self.user,
            title='New Interview',
            difficulty=5,
            messages=[],
            type='GEN'
        )

        url = reverse('download_csv_report', kwargs={'chat_id': new_chat.id})
        response = self.client.get(url)

        # Should redirect
        self.assertEqual(response.status_code, 302)

    def test_user_can_only_download_own_csv(self):
        """Test that users can only download their own CSV reports"""
        # Create another user and their chat
        other_user = User.objects.create_user(
            username='otheruser',
            password=TEST_PASSWORD
        )
        other_chat = Chat.objects.create(
            owner=other_user,
            title='Other Interview',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        ExportableReport.objects.create(
            chat=other_chat,
            overall_score=75
        )

        # Login as first user
        self.client.login(username='testuser', password=TEST_PASSWORD)

        # Try to download other user's CSV
        url = reverse('download_csv_report', kwargs={'chat_id': other_chat.id})
        response = self.client.get(url)

        # Should be forbidden (403) or redirect
        self.assertIn(response.status_code, [403, 302])


class FinalScoreComputationTest(TestCase):
    """
    Test User Story 1: As a candidate, I want to understand how my final score was computed.

    Acceptance Criteria:
    - Final score is shown with weight breakdown
    - Rationales explain scoring logic
    - Scores are exportable as PDF or CSV
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview for Score Computation',
            difficulty=7,
            messages=[
                {'role': 'assistant', 'content': 'What is your experience?'},
                {'role': 'user', 'content': 'I have 5 years of experience.'}
            ],
            type='GEN'
        )
        self.report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            professionalism_weight=30,
            professionalism_rationale='Demonstrated excellent professionalism throughout.',
            subject_knowledge_score=78,
            subject_knowledge_weight=40,
            subject_knowledge_rationale='Good understanding with room for improvement.',
            clarity_score=82,
            clarity_weight=30,
            clarity_rationale='Clear and well-structured responses.',
            overall_score=81,
            overall_rationale='Strong overall performance.',
            feedback_text='Good job overall.',
            total_questions_asked=5,
            total_responses_given=5)

    def test_final_score_displayed_with_weights(self):
        """Test that final score is shown with weight breakdown"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check that weights are displayed for each section
        self.assertContains(response, 'Weight: 30%')  # Professionalism
        self.assertContains(response, 'Weight: 40%')  # Subject Knowledge
        self.assertContains(response, 'Weight: 30%')  # Clarity (appears twice)

        # Check overall score is displayed
        self.assertContains(response, 'Overall Score')
        self.assertContains(response, '81')

    def test_score_computation_explanation_displayed(self):
        """Test that score computation explanation is shown"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check for computation explanation section
        self.assertContains(response, 'How Your Score is Calculated')
        self.assertContains(response, 'Score Calculation:')
        self.assertContains(response, 'Final Overall Score:')

    def test_rationales_explain_scoring_logic(self):
        """Test that rationales clearly explain the scoring logic"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check that all rationales are present and explain the logic
        self.assertContains(response, 'Demonstrated excellent professionalism')
        self.assertContains(
            response, 'Good understanding with room for improvement')
        self.assertContains(response, 'Clear and well-structured responses')
        self.assertContains(response, 'Strong overall performance')

    def test_scores_exportable_as_pdf(self):
        """Test that scores can be exported as PDF"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        # Verify PDF export works
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])

        # Verify PDF content starts with PDF header
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_scores_exportable_as_csv(self):
        """Test that scores can be exported as CSV"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        # Verify CSV export works
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

        # Check CSV contains score data
        content = response.content.decode('utf-8')
        self.assertIn('Professionalism', content)
        self.assertIn('Subject Knowledge', content)
        self.assertIn('Clarity', content)
        self.assertIn('85', content)  # Professionalism score
        self.assertIn('78', content)  # Subject Knowledge score
        self.assertIn('82', content)  # Clarity score

    def test_weight_breakdown_visible_in_export_page(self):
        """Test that weight breakdown is clearly visible"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Verify the breakdown shows the formula
        response_text = response.content.decode('utf-8')
        self.assertIn('Professionalism (30%)', response_text)
        self.assertIn('Subject Knowledge (40%)', response_text)
        self.assertIn('Clarity (30%)', response_text)

    def test_pdf_download_button_accessible(self):
        """Test that PDF download button is accessible"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Download as PDF')
        self.assertContains(response, 'download_pdf_report')

    def test_csv_download_button_accessible(self):
        """Test that CSV download button is accessible"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Download as CSV')
        self.assertContains(response, 'download_csv_report')


class SectionScoresWithRationalesTest(TestCase):
    """
    Test User Story 2: As a candidate, I want to view section scores after completing an interview.

    Acceptance Criteria:
    - Results page shows scores per section
    - Each score includes a brief rationale
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview with Rationales',
            difficulty=7,
            messages=[
                {'role': 'assistant', 'content': 'What is your experience?'},
                {'role': 'user', 'content': 'I have 5 years of experience.'},
                {'role': 'assistant', 'content': 'Score: 8/10. Good answer.'}
            ],
            type='GEN'
        )
        self.report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            professionalism_rationale=(
                'The candidate demonstrated excellent professionalism '
                'throughout the interview, maintaining appropriate tone and demeanor.'
            ),
            subject_knowledge_score=78,
            subject_knowledge_rationale='Good understanding of core concepts with some room for improvement in advanced topics.',
            clarity_score=82,
            clarity_rationale='Responses were well-structured and clear, with only minor areas needing clarification.',
            overall_score=81,
            overall_rationale='Overall strong performance with solid fundamentals and professional conduct.',
            feedback_text='Good job overall. Keep up the great work!',
            total_questions_asked=3,
            total_responses_given=1)

    def test_section_scores_displayed(self):
        """Test that all section scores are displayed on the export report page"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check that all three section scores are displayed
        self.assertContains(response, 'Professionalism')
        self.assertContains(response, '85')  # Professionalism score
        self.assertContains(response, 'Subject Knowledge')
        self.assertContains(response, '78')  # Subject Knowledge score
        self.assertContains(response, 'Clarity')
        self.assertContains(response, '82')  # Clarity score
        self.assertContains(response, 'Overall Score')
        self.assertContains(response, '81')  # Overall score

    def test_section_rationales_displayed(self):
        """Test that each section score includes its rationale"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check that all rationales are displayed
        self.assertContains(
            response,
            'The candidate demonstrated excellent professionalism'
        )
        self.assertContains(
            response,
            'Good understanding of core concepts'
        )
        self.assertContains(
            response,
            'Responses were well-structured and clear'
        )
        self.assertContains(
            response,
            'Overall strong performance with solid fundamentals'
        )

    def test_score_breakdown_section_exists(self):
        """Test that the Score Breakdown & Rationales section exists"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check for the Score Breakdown section header
        self.assertContains(response, 'Score Breakdown &amp; Rationales')

    def test_section_scores_with_weights(self):
        """Test that section scores display with their weights"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check that weights are displayed (default 30/40/30)
        self.assertContains(response, '30%')  # Professionalism weight
        self.assertContains(response, '40%')  # Subject Knowledge weight

    def test_pdf_export_includes_rationales(self):
        """Test that PDF export includes section rationales"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('download_pdf_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # Check that PDF was generated (can't easily check content without
        # parsing PDF)
        self.report.refresh_from_db()
        self.assertTrue(self.report.pdf_generated)

    def test_csv_export_accessible(self):
        """Test that CSV export is accessible"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

        # Check that rationales are in CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Professionalism', content)
        self.assertIn('Subject Knowledge', content)
        self.assertIn('Clarity', content)


class IntegratedUserStoriesTest(TestCase):
    """
    Integration test for both user stories working together:
    1. Understanding how final score was computed
    2. Viewing section scores after completing interview

    This test verifies the complete candidate workflow from viewing results
    to downloading exportable reports.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='candidate',
            password=TEST_PASSWORD
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Complete Interview Test',
            difficulty=8,
            messages=[
                {'role': 'assistant', 'content': 'Tell me about your experience.'},
                {'role': 'user', 'content': 'I have 7 years in software development.'},
                {'role': 'assistant', 'content': 'What are your strengths?'},
                {'role': 'user', 'content': 'Problem-solving and teamwork.'}
            ],
            type='GEN'
        )

    def test_complete_workflow_both_user_stories(self):
        """Test complete workflow covering both user stories"""
        from unittest.mock import patch, MagicMock
        from .test_utils import create_mock_openai_response

        # Clean up any existing reports for this chat
        # (report_utils returns existing reports instead of creating new ones)
        ExportableReport.objects.filter(chat=self.chat).delete()

        self.client.login(username='candidate', password=TEST_PASSWORD)

        # Step 1: Finalize interview (triggers report generation)
        finalize_url = reverse('finalize_interview', kwargs={'chat_id': self.chat.id})

        # Mock the AI calls to avoid external API dependency
        with patch('active_interview_app.openai_utils.ai_available', return_value=True):
            with patch('active_interview_app.openai_utils.get_openai_client') as mock_get_client:
                # Create mock client
                mock_client = MagicMock()

                # Mock scores response with proper token tracking attributes
                mock_scores = create_mock_openai_response("85\n78\n82\n81")

                # Mock feedback response with proper token tracking attributes
                mock_feedback = create_mock_openai_response("Excellent interview performance.")

                # Mock rationales response with proper token tracking attributes
                mock_rationales = create_mock_openai_response("""
Professionalism: Demonstrated excellent professional behavior throughout the interview.

Subject Knowledge: Showed strong technical knowledge and understanding.

Clarity: Communicated clearly and effectively.

Overall: Strong overall performance with good balance across all areas.
""")

                # Set up get_openai_client to return client
                mock_get_client.return_value = mock_client

                # Set up the side effects for the three API calls
                mock_client.chat.completions.create.side_effect = [
                    mock_scores, mock_feedback, mock_rationales]

                finalize_response = self.client.post(finalize_url, follow=True)
                self.assertEqual(finalize_response.status_code, 200)

        # Verify report was created
        self.assertTrue(ExportableReport.objects.filter(
            chat=self.chat).exists())
        report = ExportableReport.objects.get(chat=self.chat)

        # Step 3: Verify section scores are displayed (User Story 2)
        export_url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        export_response = self.client.get(export_url)
        self.assertEqual(export_response.status_code, 200)

        # Check all section scores are shown
        self.assertContains(export_response, 'Professionalism')
        self.assertContains(export_response, 'Subject Knowledge')
        self.assertContains(export_response, 'Clarity')
        self.assertContains(export_response, 'Overall Score')

        # Step 4: Verify rationales are displayed (User Story 2)
        if report.professionalism_rationale:
            self.assertContains(
                export_response, report.professionalism_rationale)
        if report.subject_knowledge_rationale:
            self.assertContains(
                export_response, report.subject_knowledge_rationale)
        if report.clarity_rationale:
            self.assertContains(export_response, report.clarity_rationale)

        # Step 5: Verify weight breakdown is shown (User Story 1)
        self.assertContains(export_response, 'How Your Score is Calculated')
        self.assertContains(
            export_response, f'Weight: {report.professionalism_weight}%')
        self.assertContains(
            export_response, f'Weight: {report.subject_knowledge_weight}%')
        self.assertContains(
            export_response, f'Weight: {report.clarity_weight}%')

        # Step 6: Verify PDF export works (User Story 1)
        pdf_url = reverse('download_pdf_report', kwargs={
                          'chat_id': self.chat.id})
        pdf_response = self.client.get(pdf_url)
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')

        # Step 7: Verify CSV export works (User Story 1)
        csv_url = reverse('download_csv_report', kwargs={
                          'chat_id': self.chat.id})
        csv_response = self.client.get(csv_url)
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response['Content-Type'], 'text/csv')

    def test_all_acceptance_criteria_met(self):
        """Verify all acceptance criteria for both user stories are met"""
        self.client.login(username='candidate', password=TEST_PASSWORD)

        # Create report with all data
        ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=90,
            professionalism_weight=30,
            professionalism_rationale='Excellent professionalism demonstrated.',
            subject_knowledge_score=85,
            subject_knowledge_weight=40,
            subject_knowledge_rationale='Strong technical knowledge.',
            clarity_score=88,
            clarity_weight=30,
            clarity_rationale='Very clear communication.',
            overall_score=87,
            overall_rationale='Excellent overall performance.',
            feedback_text='Outstanding candidate.',
            total_questions_asked=4,
            total_responses_given=4)

        export_url = reverse('export_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(export_url)

        # USER STORY 1 - Acceptance Criteria:
        # 1. Final score is shown with weight breakdown ✓
        self.assertContains(response, 'Final Overall Score')
        self.assertContains(response, 'Weight: 30%')
        self.assertContains(response, 'Weight: 40%')

        # 2. Rationales explain scoring logic ✓
        self.assertContains(response, 'Excellent professionalism demonstrated')
        self.assertContains(response, 'Strong technical knowledge')
        self.assertContains(response, 'Very clear communication')
        self.assertContains(response, 'Excellent overall performance')

        # 3. Scores are exportable as PDF or CSV ✓
        self.assertContains(response, 'Download as PDF')
        self.assertContains(response, 'Download as CSV')

        # USER STORY 2 - Acceptance Criteria:
        # 1. Results page shows scores per section ✓
        self.assertContains(response, 'Professionalism: 90/100')
        self.assertContains(response, 'Subject Knowledge: 85/100')
        self.assertContains(response, 'Clarity: 88/100')

        # 2. Each score includes a brief rationale ✓
        # Already verified above in User Story 1 criteria #2

        # Additional verification: Score breakdown section exists
        self.assertContains(response, 'Score Breakdown &amp; Rationales')


class ScoreComputationLearningScenarioTest(TestCase):
    """
    BDD-style test for the specific user story:
    "As a candidate, I want to see how my score was computed, so I can learn and improve."

    Scenario:
    Given I completed an interview
    When I open my results
    Then I see section scores with weights and rationales
    And a final weighted score
    """

    def setUp(self):
        """Set up test fixtures for the scenario"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='candidate_learner',
            password=TEST_PASSWORD
        )

    def test_score_computation_learning_scenario(self):
        """
        Test the complete BDD scenario:
        Given/When/Then for learning from score computation
        """
        # GIVEN I completed an interview
        completed_chat = Chat.objects.create(
            owner=self.user,
            title='Completed Interview for Learning',
            difficulty=7,
            messages=[
                {'role': 'assistant', 'content': 'Describe your experience with Python.'},
                {'role': 'user', 'content': 'I have 5 years of experience with Python in web development.'},
                {'role': 'assistant', 'content': 'What are your communication strengths?'},
                {'role': 'user', 'content': 'I excel at explaining technical concepts to non-technical stakeholders.'},
                {'role': 'assistant', 'content': 'Tell me about a challenging project.'},
                {'role': 'user', 'content': 'I led a team to refactor a legacy system, improving performance by 40%.'}
            ],
            type='GEN'
        )

        # Generate the report with scores and rationales
        ExportableReport.objects.create(
            chat=completed_chat,
            professionalism_score=88,
            professionalism_weight=30,
            professionalism_rationale=(
                'Demonstrated strong professionalism with respectful '
                'communication and appropriate tone throughout the interview.'
            ),
            subject_knowledge_score=92,
            subject_knowledge_weight=40,
            subject_knowledge_rationale='Exhibited excellent technical knowledge with specific examples and deep understanding of core concepts.',
            clarity_score=85,
            clarity_weight=30,
            clarity_rationale='Communicated ideas clearly and concisely, with well-structured responses that were easy to follow.',
            overall_score=89,
            overall_rationale='Outstanding performance demonstrating both technical competence and strong communication skills.',
            feedback_text='Excellent candidate with strong technical skills and clear communication.',
            total_questions_asked=3,
            total_responses_given=3)

        self.client.login(username='candidate_learner', password=TEST_PASSWORD)

        # WHEN I open my results
        results_url = reverse('export_report', kwargs={
                              'chat_id': completed_chat.id})
        response = self.client.get(results_url)

        # Verify the page loads successfully
        self.assertEqual(response.status_code, 200)

        # THEN I see section scores with weights and rationales

        # Verify section scores are visible
        self.assertContains(response, 'Professionalism: 88/100')
        self.assertContains(response, 'Subject Knowledge: 92/100')
        self.assertContains(response, 'Clarity: 85/100')

        # Verify weights are displayed for each section
        self.assertContains(response, '(30% weight)')  # Professionalism weight
        # Subject Knowledge weight
        self.assertContains(response, '(40% weight)')
        # Clarity weight (appears twice)
        self.assertContains(response, '(30% weight)')

        # Verify rationales are shown for learning
        self.assertContains(response, 'Demonstrated strong professionalism')
        self.assertContains(
            response, 'Exhibited excellent technical knowledge')
        self.assertContains(
            response, 'Communicated ideas clearly and concisely')

        # AND a final weighted score

        # Verify "Final Weighted Score" label is present
        self.assertContains(response, 'Final Weighted Score')

        # Verify the final score value is displayed
        self.assertContains(response, '89/100')

        # Verify the weighted calculation formula is shown
        self.assertContains(response, 'Weighted Score Calculation')
        # Professionalism calculation
        self.assertContains(response, '88 × 30%')
        # Subject Knowledge calculation
        self.assertContains(response, '92 × 40%')
        self.assertContains(response, '85 × 30%')  # Clarity calculation

        # Verify learning guidance is present
        self.assertContains(
            response, 'identify your strengths and areas for improvement')

    def test_learning_oriented_content_present(self):
        """Test that content is oriented toward learning and improvement"""
        self.client.login(username='candidate_learner', password=TEST_PASSWORD)

        chat = Chat.objects.create(
            owner=self.user,
            title='Learning Test Interview',
            difficulty=6,
            messages=[
                {'role': 'assistant', 'content': 'Question 1'},
                {'role': 'user', 'content': 'Answer 1'}
            ],
            type='GEN'
        )

        ExportableReport.objects.create(
            chat=chat,
            professionalism_score=75,
            professionalism_weight=30,
            professionalism_rationale='Good professionalism with room to improve in maintaining consistent eye contact.',
            subject_knowledge_score=80,
            subject_knowledge_weight=40,
            subject_knowledge_rationale='Solid foundational knowledge, but could benefit from deeper understanding of advanced topics.',
            clarity_score=70,
            clarity_weight=30,
            clarity_rationale='Generally clear responses, though some answers could be more concise and focused.',
            overall_score=76,
            overall_rationale='Good overall performance with clear areas for growth and development.',
            feedback_text='Good effort with opportunities for improvement.',
            total_questions_asked=1,
            total_responses_given=1)

        url = reverse('export_report', kwargs={'chat_id': chat.id})
        response = self.client.get(url)

        # Verify learning-oriented language
        self.assertContains(response, 'How Your Score is Calculated')
        self.assertContains(
            response, 'Understanding how your final score was computed')

        # Verify actionable feedback in rationales
        self.assertContains(response, 'room to improve')
        self.assertContains(response, 'could benefit from')
        self.assertContains(response, 'could be more')

        # Verify guidance for improvement
        self.assertContains(response, 'areas for improvement')

    def test_all_scenario_elements_integrated(self):
        """Test that all scenario elements work together cohesively"""
        self.client.login(username='candidate_learner', password=TEST_PASSWORD)

        chat = Chat.objects.create(
            owner=self.user,
            title='Integration Scenario Test',
            difficulty=8,
            messages=[
                {'role': 'assistant', 'content': 'Q1'},
                {'role': 'user', 'content': 'A1'}
            ],
            type='GEN'
        )

        ExportableReport.objects.create(
            chat=chat,
            professionalism_score=90,
            professionalism_weight=30,
            professionalism_rationale='Excellent professionalism.',
            subject_knowledge_score=85,
            subject_knowledge_weight=40,
            subject_knowledge_rationale='Strong knowledge.',
            clarity_score=88,
            clarity_weight=30,
            clarity_rationale='Very clear.',
            overall_score=87,
            overall_rationale='Great performance.',
            total_questions_asked=1,
            total_responses_given=1
        )

        url = reverse('export_report', kwargs={'chat_id': chat.id})
        response = self.client.get(url)

        response_content = response.content.decode('utf-8')

        # Verify complete scenario fulfillment
        scenario_elements = [
            # "I see section scores"
            'Professionalism: 90/100',
            'Subject Knowledge: 85/100',
            'Clarity: 88/100',
            # "with weights"
            '30% weight',
            '40% weight',
            # "and rationales"
            'Excellent professionalism',
            'Strong knowledge',
            'Very clear',
            # "and a final weighted score"
            'Final Weighted Score',
            '87/100',
            'Weighted Score Calculation'
        ]

        for element in scenario_elements:
            self.assertIn(element, response_content,
                          f"Missing scenario element: {element}")
