"""
Tests to boost pdf_export.py coverage to >80%
Focuses on untested helper functions
"""

from django.test import TestCase
from django.contrib.auth.models import User
from active_interview_app.models import Chat, ExportableReport, UploadedJobListing, UploadedResume
from active_interview_app.pdf_export import (
    _create_score_rationales_section,
    _create_recommended_exercises_section,
    _create_styles,
    generate_pdf_report,
    get_score_rating,
    _create_metadata_section,
    _create_performance_scores_section,
    _create_feedback_section,
    _create_statistics_section,
    _create_footer
)


class PDFRationalesSectionTest(TestCase):
    """Test _create_score_rationales_section"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass123')
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN'
        )

    def test_rationales_with_scores(self):
        """Test rationales section with scores"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            professionalism_rationale='Good professionalism',
            subject_knowledge_rationale='Solid knowledge',
            clarity_rationale='Clear communication',
            overall_rationale='Good overall'
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_score_rationales_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_rationales_no_scores(self):
        """Test rationales section with no overall score"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=None
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_score_rationales_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_rationales_partial(self):
        """Test with some rationales empty"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=90,
            subject_knowledge_score=85,
            clarity_score=88,
            overall_score=87,
            professionalism_rationale='Excellent',
            subject_knowledge_rationale='',
            clarity_rationale='Good',
            overall_rationale=''
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_score_rationales_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


class PDFRecommendedExercisesTest(TestCase):
    """Test _create_recommended_exercises_section"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass123')
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN'
        )

    def test_exercises_excellent_score(self):
        """Test recommendations for excellent score (>=90)"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=92,
            subject_knowledge_score=91,
            clarity_score=90,
            overall_score=91
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_recommended_exercises_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_exercises_good_score(self):
        """Test recommendations for good score (75-89)"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=80,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=80
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_recommended_exercises_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_exercises_fair_score(self):
        """Test recommendations for fair score (60-74)"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=65,
            subject_knowledge_score=68,
            clarity_score=70,
            overall_score=68
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_recommended_exercises_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_exercises_poor_score(self):
        """Test recommendations for poor score (<60)"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=45,
            subject_knowledge_score=50,
            clarity_score=48,
            overall_score=48
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_recommended_exercises_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_exercises_zero_scores(self):
        """Test with zero scores"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=0,
            subject_knowledge_score=0,
            clarity_score=0,
            overall_score=0
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_recommended_exercises_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_exercises_none_scores(self):
        """Test with None scores"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=None,
            subject_knowledge_score=None,
            clarity_score=None,
            overall_score=None
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_recommended_exercises_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_exercises_mixed_scores(self):
        """Test with mixed high/low scores"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=90,
            subject_knowledge_score=55,
            clarity_score=50,
            overall_score=65
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_recommended_exercises_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


class PDFGenerationTest(TestCase):
    """Test generate_pdf_report function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass123')

    def test_generate_pdf_with_all_data(self):
        """Test PDF generation with all fields populated"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Senior Developer',
            filename='job.pdf',
            content='Job description'
        )
        resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content',
            original_filename='resume.pdf'
        )
        chat = Chat.objects.create(
            owner=self.user,
            title='Full Interview',
            difficulty=8,
            messages=[],
            type='GEN',
            job_listing=job,
            resume=resume
        )
        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=92,
            subject_knowledge_score=88,
            clarity_score=90,
            overall_score=90,
            professionalism_rationale='Excellent professionalism',
            subject_knowledge_rationale='Strong knowledge',
            clarity_rationale='Clear communication',
            overall_rationale='Outstanding',
            feedback_text='Great job!\nExcellent performance.',
            total_questions_asked=20,
            total_responses_given=20,
            interview_duration_minutes=60
        )

        pdf = generate_pdf_report(report)

        self.assertIsNotNone(pdf)
        self.assertIsInstance(pdf, bytes)
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertGreater(len(pdf), 5000)

    def test_generate_pdf_minimal(self):
        """Test PDF with minimal data"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Minimal',
            difficulty=1,
            messages=[],
            type='GEN'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            total_questions_asked=0,
            total_responses_given=0
        )

        pdf = generate_pdf_report(report)

        self.assertIsNotNone(pdf)
        self.assertTrue(pdf.startswith(b'%PDF'))

    def test_generate_pdf_behavioral_interview(self):
        """Test PDF for behavioral interview"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Behavioral',
            difficulty=6,
            messages=[],
            type='BEH'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            overall_score=75,
            total_questions_asked=10,
            total_responses_given=10
        )

        pdf = generate_pdf_report(report)
        self.assertTrue(pdf.startswith(b'%PDF'))

    def test_generate_pdf_technical_interview(self):
        """Test PDF for technical interview"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Technical',
            difficulty=10,
            messages=[],
            type='TEC'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            overall_score=85,
            total_questions_asked=15,
            total_responses_given=15
        )

        pdf = generate_pdf_report(report)
        self.assertTrue(pdf.startswith(b'%PDF'))

    def test_generate_pdf_case_study(self):
        """Test PDF for case study interview"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Case Study',
            difficulty=7,
            messages=[],
            type='CAS'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            overall_score=80,
            total_questions_asked=8,
            total_responses_given=8
        )

        pdf = generate_pdf_report(report)
        self.assertTrue(pdf.startswith(b'%PDF'))

    def test_generate_pdf_multiline_feedback(self):
        """Test PDF with multiline feedback"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Multiline',
            difficulty=5,
            messages=[],
            type='GEN'
        )
        report = ExportableReport.objects.create(
            chat=chat,
            feedback_text='Line 1\n\nLine 2\n\nLine 3',
            overall_score=70,
            total_questions_asked=10,
            total_responses_given=10
        )

        pdf = generate_pdf_report(report)
        self.assertTrue(pdf.startswith(b'%PDF'))


class ScoreRatingTest(TestCase):
    """Test get_score_rating function"""

    def test_rating_excellent(self):
        """Test excellent range"""
        self.assertEqual(get_score_rating(90), 'Excellent')
        self.assertEqual(get_score_rating(95), 'Excellent')
        self.assertEqual(get_score_rating(100), 'Excellent')

    def test_rating_good(self):
        """Test good range"""
        self.assertEqual(get_score_rating(75), 'Good')
        self.assertEqual(get_score_rating(80), 'Good')
        self.assertEqual(get_score_rating(89), 'Good')

    def test_rating_fair(self):
        """Test fair range"""
        self.assertEqual(get_score_rating(60), 'Fair')
        self.assertEqual(get_score_rating(65), 'Fair')
        self.assertEqual(get_score_rating(74), 'Fair')

    def test_rating_needs_improvement(self):
        """Test needs improvement range"""
        self.assertEqual(get_score_rating(0), 'Needs Improvement')
        self.assertEqual(get_score_rating(30), 'Needs Improvement')
        self.assertEqual(get_score_rating(59), 'Needs Improvement')

    def test_rating_none(self):
        """Test None score"""
        self.assertEqual(get_score_rating(None), 'N/A')


class PDFSectionsTest(TestCase):
    """Test individual PDF section creation functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass123')
        self.chat = Chat.objects.create(
            owner=self.user,
            title='Test',
            difficulty=5,
            messages=[],
            type='GEN'
        )

    def test_create_metadata_section(self):
        """Test metadata section creation"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            total_questions_asked=10,
            total_responses_given=10
        )

        _, heading_style, _ = _create_styles()
        result = _create_metadata_section(report, heading_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_metadata_with_job_and_resume(self):
        """Test metadata with job and resume"""
        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job',
            filename='job.pdf',
            content='Content'
        )
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Resume',
            content='Content',
            original_filename='resume.pdf'
        )
        self.chat.job_listing = job
        self.chat.resume = resume
        self.chat.save()

        report = ExportableReport.objects.create(
            chat=self.chat,
            total_questions_asked=10,
            total_responses_given=10
        )

        _, heading_style, _ = _create_styles()
        result = _create_metadata_section(report, heading_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_performance_scores_with_scores(self):
        """Test performance scores section with scores"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            total_questions_asked=10,
            total_responses_given=10
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_performance_scores_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_performance_scores_without_scores(self):
        """Test performance scores section when no overall score"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=None,
            total_questions_asked=5,
            total_responses_given=5
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_performance_scores_section(
            report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_feedback_section_with_text(self):
        """Test feedback section with feedback"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            feedback_text='Good performance',
            total_questions_asked=10,
            total_responses_given=10
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_feedback_section(report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_feedback_section_without_text(self):
        """Test feedback section without feedback"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            feedback_text='',
            total_questions_asked=5,
            total_responses_given=5
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_feedback_section(report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_create_statistics_section(self):
        """Test statistics section"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            total_questions_asked=15,
            total_responses_given=15,
            interview_duration_minutes=45
        )

        _, heading_style, _ = _create_styles()
        result = _create_statistics_section(report, heading_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_statistics_no_duration(self):
        """Test statistics without duration"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            total_questions_asked=10,
            total_responses_given=10,
            interview_duration_minutes=None
        )

        _, heading_style, _ = _create_styles()
        result = _create_statistics_section(report, heading_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_create_footer(self):
        """Test footer creation"""
        result = _create_footer()

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
