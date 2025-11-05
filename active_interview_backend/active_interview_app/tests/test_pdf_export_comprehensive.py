"""
Comprehensive tests for PDF export functionality

This module provides extensive coverage of all PDF export utility functions,
including edge cases and error handling.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from active_interview_app.models import Chat, ExportableReport, UploadedJobListing, UploadedResume
from active_interview_app.pdf_export import (
    generate_pdf_report,
    get_score_rating,
    _create_styles,
    _create_metadata_section,
    _create_performance_scores_section,
    _create_feedback_section,
    _create_statistics_section,
    _create_footer
)


class GetScoreRatingTest(TestCase):
    """Test get_score_rating function comprehensively"""

    def test_score_rating_excellent_90(self):
        """Test score of exactly 90 returns Excellent"""
        self.assertEqual(get_score_rating(90), 'Excellent')

    def test_score_rating_excellent_95(self):
        """Test score of 95 returns Excellent"""
        self.assertEqual(get_score_rating(95), 'Excellent')

    def test_score_rating_excellent_100(self):
        """Test score of 100 returns Excellent"""
        self.assertEqual(get_score_rating(100), 'Excellent')

    def test_score_rating_good_75(self):
        """Test score of exactly 75 returns Good"""
        self.assertEqual(get_score_rating(75), 'Good')

    def test_score_rating_good_80(self):
        """Test score of 80 returns Good"""
        self.assertEqual(get_score_rating(80), 'Good')

    def test_score_rating_good_89(self):
        """Test score of 89 returns Good"""
        self.assertEqual(get_score_rating(89), 'Good')

    def test_score_rating_fair_60(self):
        """Test score of exactly 60 returns Fair"""
        self.assertEqual(get_score_rating(60), 'Fair')

    def test_score_rating_fair_65(self):
        """Test score of 65 returns Fair"""
        self.assertEqual(get_score_rating(65), 'Fair')

    def test_score_rating_fair_74(self):
        """Test score of 74 returns Fair"""
        self.assertEqual(get_score_rating(74), 'Fair')

    def test_score_rating_needs_improvement_0(self):
        """Test score of 0 returns Needs Improvement"""
        self.assertEqual(get_score_rating(0), 'Needs Improvement')

    def test_score_rating_needs_improvement_30(self):
        """Test score of 30 returns Needs Improvement"""
        self.assertEqual(get_score_rating(30), 'Needs Improvement')

    def test_score_rating_needs_improvement_59(self):
        """Test score of 59 returns Needs Improvement"""
        self.assertEqual(get_score_rating(59), 'Needs Improvement')

    def test_score_rating_none(self):
        """Test None score returns N/A"""
        self.assertEqual(get_score_rating(None), 'N/A')


class CreateStylesTest(TestCase):
    """Test _create_styles function"""

    def test_create_styles_returns_tuple(self):
        """Test that _create_styles returns a tuple of 3 styles"""
        result = _create_styles()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_create_styles_title_style(self):
        """Test title style properties"""
        title_style, _, _ = _create_styles()
        self.assertEqual(title_style.fontSize, 24)
        self.assertEqual(title_style.name, 'CustomTitle')

    def test_create_styles_heading_style(self):
        """Test heading style properties"""
        _, heading_style, _ = _create_styles()
        self.assertEqual(heading_style.fontSize, 16)
        self.assertEqual(heading_style.name, 'CustomHeading')

    def test_create_styles_normal_style(self):
        """Test normal style properties"""
        _, _, normal_style = _create_styles()
        self.assertEqual(normal_style.fontSize, 11)
        self.assertEqual(normal_style.leading, 14)


class PDFSectionCreationTest(TestCase):
    """Test PDF section creation functions"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Sample Interview',
            difficulty=8,
            messages=[],
            type='GEN'
        )
        self.report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            feedback_text='Excellent performance overall.',
            total_questions_asked=15,
            total_responses_given=15,
            interview_duration_minutes=45
        )

    def test_create_metadata_section(self):
        """Test _create_metadata_section returns list of flowables"""
        _, heading_style, _ = _create_styles()
        result = _create_metadata_section(self.report, heading_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_metadata_section_with_job_listing(self):
        """Test metadata section with job listing"""
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            title='Software Engineer',
            filename='job.pdf',
            content='Job description'
        )
        self.chat.job_listing = job_listing
        self.chat.save()

        _, heading_style, _ = _create_styles()
        result = _create_metadata_section(self.report, heading_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_metadata_section_with_resume(self):
        """Test metadata section with resume"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content',
            original_filename='resume.pdf'
        )
        self.chat.resume = resume
        self.chat.save()

        _, heading_style, _ = _create_styles()
        result = _create_metadata_section(self.report, heading_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_performance_scores_section_with_scores(self):
        """Test performance scores section with scores"""
        _, heading_style, normal_style = _create_styles()
        result = _create_performance_scores_section(
            self.report,
            heading_style,
            normal_style
        )

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_performance_scores_section_without_scores(self):
        """Test performance scores section when no overall score exists"""
        report_no_scores = ExportableReport.objects.create(
            chat=Chat.objects.create(
                owner=self.user,
                title='No Scores Interview',
                difficulty=5,
                messages=[],
                type='GEN'
            ),
            overall_score=None,
            total_questions_asked=5,
            total_responses_given=5
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_performance_scores_section(
            report_no_scores,
            heading_style,
            normal_style
        )

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_feedback_section_with_feedback(self):
        """Test feedback section with feedback text"""
        _, heading_style, normal_style = _create_styles()
        result = _create_feedback_section(
            self.report,
            heading_style,
            normal_style
        )

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_feedback_section_without_feedback(self):
        """Test feedback section when no feedback exists"""
        report_no_feedback = ExportableReport.objects.create(
            chat=Chat.objects.create(
                owner=self.user,
                title='No Feedback Interview',
                difficulty=5,
                messages=[],
                type='GEN'
            ),
            feedback_text='',
            total_questions_asked=5,
            total_responses_given=5
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_feedback_section(
            report_no_feedback,
            heading_style,
            normal_style
        )

        self.assertIsInstance(result, list)
        # Should be empty list when no feedback
        self.assertEqual(len(result), 0)

    def test_create_feedback_section_multiline(self):
        """Test feedback section with multiline feedback"""
        multiline_report = ExportableReport.objects.create(
            chat=Chat.objects.create(
                owner=self.user,
                title='Multiline Feedback Interview',
                difficulty=5,
                messages=[],
                type='GEN'
            ),
            feedback_text='Line 1\nLine 2\nLine 3\n',
            total_questions_asked=5,
            total_responses_given=5
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_feedback_section(
            multiline_report,
            heading_style,
            normal_style
        )

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_statistics_section(self):
        """Test statistics section"""
        _, heading_style, _ = _create_styles()
        result = _create_statistics_section(self.report, heading_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_statistics_section_no_duration(self):
        """Test statistics section without interview duration"""
        report_no_duration = ExportableReport.objects.create(
            chat=Chat.objects.create(
                owner=self.user,
                title='No Duration Interview',
                difficulty=5,
                messages=[],
                type='GEN'
            ),
            interview_duration_minutes=None,
            total_questions_asked=10,
            total_responses_given=10
        )

        _, heading_style, _ = _create_styles()
        result = _create_statistics_section(report_no_duration, heading_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_footer(self):
        """Test footer creation"""
        result = _create_footer()

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


class GeneratePDFReportTest(TestCase):
    """Test generate_pdf_report function with various scenarios"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_generate_pdf_complete_report(self):
        """Test PDF generation with complete report data"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Complete Interview Report',
            difficulty=9,
            messages=[],
            type='GEN'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=92,
            subject_knowledge_score=88,
            clarity_score=90,
            overall_score=90,
            feedback_text='Outstanding performance!\nExcellent communication skills.',
            question_responses=[
                {
                    'question': 'Describe your leadership experience',
                    'answer': 'I led a team of 10 engineers.',
                    'score': 9,
                    'feedback': 'Great example'
                }
            ],
            total_questions_asked=20,
            total_responses_given=20,
            interview_duration_minutes=60
        )

        pdf_content = generate_pdf_report(report)

        self.assertIsNotNone(pdf_content)
        self.assertIsInstance(pdf_content, bytes)
        self.assertTrue(pdf_content.startswith(b'%PDF'))
        self.assertGreater(len(pdf_content), 1000)

    def test_generate_pdf_minimal_report(self):
        """Test PDF generation with minimal data"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Minimal Report',
            difficulty=3,
            messages=[],
            type='GEN'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            total_questions_asked=0,
            total_responses_given=0
        )

        pdf_content = generate_pdf_report(report)

        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_generate_pdf_behavioral_interview(self):
        """Test PDF for behavioral interview type"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Behavioral Interview',
            difficulty=7,
            messages=[],
            type='BEH'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            overall_score=85,
            total_questions_asked=10,
            total_responses_given=10
        )

        pdf_content = generate_pdf_report(report)

        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_generate_pdf_technical_interview(self):
        """Test PDF for technical interview type"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Technical Interview',
            difficulty=10,
            messages=[],
            type='TEC'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            overall_score=75,
            total_questions_asked=12,
            total_responses_given=12
        )

        pdf_content = generate_pdf_report(report)

        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_generate_pdf_with_job_and_resume(self):
        """Test PDF with both job listing and resume"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Senior Developer',
            filename='job.pdf',
            content='Job description'
        )
        resume = UploadedResume.objects.create(
            user=self.user,
            title='John Doe Resume',
            content='Resume content',
            original_filename='resume.pdf'
        )
        chat = Chat.objects.create(
            owner=self.user,
            title='Full Context Interview',
            difficulty=8,
            messages=[],
            type='GEN',
            job_listing=job,
            resume=resume
        )
        report = ExportableReport.objects.create(
            chat=chat,
            overall_score=88,
            total_questions_asked=15,
            total_responses_given=15
        )

        pdf_content = generate_pdf_report(report)

        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_generate_pdf_long_feedback(self):
        """Test PDF with very long feedback text"""
        long_feedback = "Great performance! " * 100
        chat = Chat.objects.create(
            owner=self.user,
            title='Long Feedback Interview',
            difficulty=6,
            messages=[],
            type='GEN'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            feedback_text=long_feedback,
            overall_score=80,
            total_questions_asked=8,
            total_responses_given=8
        )

        pdf_content = generate_pdf_report(report)

        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_generate_pdf_special_characters_in_title(self):
        """Test PDF with special characters in title"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview: Software & DevOps Engineer @ Company™',
            difficulty=7,
            messages=[],
            type='GEN'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            overall_score=80,
            total_questions_asked=10,
            total_responses_given=10
        )

        pdf_content = generate_pdf_report(report)

        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_generate_pdf_zero_scores(self):
        """Test PDF with all zero scores"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Zero Scores Interview',
            difficulty=1,
            messages=[],
            type='GEN'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=0,
            subject_knowledge_score=0,
            clarity_score=0,
            overall_score=0,
            total_questions_asked=5,
            total_responses_given=5
        )

        pdf_content = generate_pdf_report(report)

        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_generate_pdf_perfect_scores(self):
        """Test PDF with all perfect (100) scores"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Perfect Scores Interview',
            difficulty=10,
            messages=[],
            type='GEN'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=100,
            subject_knowledge_score=100,
            clarity_score=100,
            overall_score=100,
            feedback_text='Perfect in every way!',
            total_questions_asked=10,
            total_responses_given=10
        )

        pdf_content = generate_pdf_report(report)

        self.assertIsNotNone(pdf_content)
        self.assertTrue(pdf_content.startswith(b'%PDF'))
