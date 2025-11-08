"""
Tests to boost views.py coverage to >80%
Focuses on untested methods and code paths
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from active_interview_app.models import Chat, ExportableReport, UploadedJobListing, UploadedResume
from active_interview_app.views import GenerateReportView


class GenerateReportMethodsTest(TestCase):
    """Test GenerateReportView private methods"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=7,
            messages=[
                {'role': 'assistant', 'content': 'Question 1?'},
                {'role': 'user', 'content': 'Answer 1'},
                {'role': 'assistant', 'content': 'Feedback: 8/10. Good answer.'},
                {'role': 'assistant', 'content': 'Question 2?'},
                {'role': 'user', 'content': 'Answer 2'}
            ],
            type='GEN'
        )
        self.view = GenerateReportView()

    def test_extract_question_responses(self):
        """Test _extract_question_responses method"""
        qa_pairs = self.view._extract_question_responses(self.chat)

        # Should find 2 Q&A pairs
        self.assertEqual(len(qa_pairs), 2)

        # First pair should have score from feedback
        self.assertEqual(qa_pairs[0]['question'], 'Question 1?')
        self.assertEqual(qa_pairs[0]['answer'], 'Answer 1')
        self.assertEqual(qa_pairs[0]['score'], 8)
        self.assertIn('Good answer', qa_pairs[0]['feedback'])

        # Second pair should not have score (no feedback)
        self.assertEqual(qa_pairs[1]['question'], 'Question 2?')
        self.assertEqual(qa_pairs[1]['answer'], 'Answer 2')
        self.assertNotIn('score', qa_pairs[1])

    def test_extract_question_responses_long_text(self):
        """Test _extract_question_responses truncates long text"""
        long_chat = Chat.objects.create(
            owner=self.user,
            title='Long Text Chat',
            difficulty=5,
            messages=[
                {'role': 'assistant', 'content': 'Q' * 1000},
                {'role': 'user', 'content': 'A' * 1000}
            ],
            type='GEN'
        )

        qa_pairs = self.view._extract_question_responses(long_chat)

        # Should truncate to 500 chars
        self.assertEqual(len(qa_pairs[0]['question']), 500)
        self.assertEqual(len(qa_pairs[0]['answer']), 500)

    def test_extract_question_responses_no_score_pattern(self):
        """Test when feedback doesn't contain score pattern"""
        chat_no_score = Chat.objects.create(
            owner=self.user,
            title='No Score',
            difficulty=5,
            messages=[
                {'role': 'assistant', 'content': 'Question?'},
                {'role': 'user', 'content': 'Answer'},
                {'role': 'assistant', 'content': 'Good job!'}  # No score pattern
            ],
            type='GEN'
        )

        qa_pairs = self.view._extract_question_responses(chat_no_score)

        # Should not have score
        self.assertEqual(len(qa_pairs), 1)
        self.assertNotIn('score', qa_pairs[0])


class GenerateReportAITest(TestCase):
    """Test AI integration paths in GenerateReportView"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[
                {'role': 'assistant', 'content': 'Hello'},
                {'role': 'user', 'content': 'Hi'}
            ],
            type='GEN'
        )

    def test_generate_report_ai_exception(self):
        """Test when AI raises exception"""
        self.client.login(username='testuser', password='pass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.side_effect = Exception('API Error')
                response = self.client.post(url, follow=True)

        # Should still create report with default values
        self.assertEqual(response.status_code, 200)
        report = ExportableReport.objects.get(chat=self.chat)
        self.assertEqual(report.professionalism_score, 0)

    def test_generate_report_ai_invalid_format(self):
        """Test when AI returns invalid format"""
        self.client.login(username='testuser', password='pass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "invalid\nformat\nhere"

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.return_value = mock_response
                response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        # Should default to 0 when parsing fails
        self.assertEqual(report.professionalism_score, 0)

    def test_generate_report_ai_incomplete_scores(self):
        """Test when AI returns incomplete scores"""
        self.client.login(username='testuser', password='pass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "85\n78"  # Only 2 scores

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.return_value = mock_response
                response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        self.assertEqual(report.professionalism_score, 0)

    def test_generate_report_rationale_parsing(self):
        """Test rationale parsing from AI response"""
        self.client.login(username='testuser', password='pass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        mock_scores = MagicMock()
        mock_scores.choices = [MagicMock()]
        mock_scores.choices[0].message.content = "85\n78\n82\n81"

        mock_feedback = MagicMock()
        mock_feedback.choices = [MagicMock()]
        mock_feedback.choices[0].message.content = "Good job!"

        mock_rationale = MagicMock()
        mock_rationale.choices = [MagicMock()]
        mock_rationale.choices[0].message.content = """
Professionalism: Good professional behavior.

Subject Knowledge: Strong knowledge base.

Clarity: Clear communication.

Overall: Great performance.
"""

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.side_effect = [
                    mock_scores,
                    mock_feedback,
                    mock_rationale
                ]
                response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        self.assertIn('professional behavior', report.professionalism_rationale)
        self.assertIn('knowledge base', report.subject_knowledge_rationale)
        self.assertIn('Clear communication', report.clarity_rationale)
        self.assertIn('Great performance', report.overall_rationale)

    def test_generate_report_rationale_multiline(self):
        """Test multiline rationale parsing"""
        self.client.login(username='testuser', password='pass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        mock_scores = MagicMock()
        mock_scores.choices = [MagicMock()]
        mock_scores.choices[0].message.content = "85\n78\n82\n81"

        mock_feedback = MagicMock()
        mock_feedback.choices = [MagicMock()]
        mock_feedback.choices[0].message.content = "Good!"

        mock_rationale = MagicMock()
        mock_rationale.choices = [MagicMock()]
        mock_rationale.choices[0].message.content = """
Professionalism: Professional throughout.
Maintained good posture.

Subject Knowledge: Strong skills.
Some gaps noted.

Clarity: Clear.

Overall: Good.
"""

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.side_effect = [
                    mock_scores,
                    mock_feedback,
                    mock_rationale
                ]
                response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        # Should capture multiline
        self.assertIn('posture', report.professionalism_rationale)
        self.assertIn('gaps', report.subject_knowledge_rationale)

    def test_generate_report_rationale_exception(self):
        """Test when rationale generation fails"""
        self.client.login(username='testuser', password='pass123')
        url = reverse('generate_report', kwargs={'chat_id': self.chat.id})

        mock_scores = MagicMock()
        mock_scores.choices = [MagicMock()]
        mock_scores.choices[0].message.content = "85\n78\n82\n81"

        mock_feedback = MagicMock()
        mock_feedback.choices = [MagicMock()]
        mock_feedback.choices[0].message.content = "Good!"

        with patch('active_interview_app.views._ai_available', return_value=True):
            with patch('active_interview_app.views.get_openai_client') as mock_client:
                mock_client.return_value.chat.completions.create.side_effect = [
                    mock_scores,
                    mock_feedback,
                    Exception('Rationale API error')
                ]
                response = self.client.post(url, follow=True)

        report = ExportableReport.objects.get(chat=self.chat)
        # Should have fallback text
        self.assertIn('Unable to generate', report.professionalism_rationale)


class DownloadCSVTest(TestCase):
    """Test CSV download functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test Interview',
            difficulty=7,
            messages=[],
            type='GEN'
        )

    def test_download_csv_with_job_and_resume(self):
        """Test CSV includes job listing and resume"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Senior Dev',
            filename='job.pdf',
            content='Description'
        )
        resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Content',
            original_filename='resume.pdf'
        )
        self.chat.job_listing = job
        self.chat.resume = resume
        self.chat.save()

        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            overall_score=80,
            professionalism_rationale='Good',
            total_questions_asked=10,
            total_responses_given=10,
            interview_duration_minutes=30
        )

        self.client.login(username='testuser', password='pass123')
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Senior Dev', content)
        self.assertIn('My Resume', content)
        self.assertIn('30 minutes', content)

    def test_download_csv_score_ratings(self):
        """Test CSV includes correct score ratings"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=95,  # Excellent
            subject_knowledge_score=82,  # Good
            clarity_score=68,  # Fair
            overall_score=80,
            total_questions_asked=5,
            total_responses_given=5
        )

        self.client.login(username='testuser', password='pass123')
        url = reverse('download_csv_report', kwargs={'chat_id': self.chat.id})
        response = self.client.get(url)

        content = response.content.decode('utf-8')
        self.assertIn('Excellent', content)
        self.assertIn('Good', content)
        self.assertIn('Fair', content)
