"""
Tests to boost pdf_export.py coverage to >80%
Focuses on untested helper functions
"""

from django.test import TestCase
from django.contrib.auth.models import User
from active_interview_app.models import Chat, ExportableReport
from active_interview_app.pdf_export import (
    _create_score_rationales_section,
    _create_recommended_exercises_section,
    _create_styles
)


class PDFRationalesSectionTest(TestCase):
    """Test _create_score_rationales_section"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
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
        result = _create_score_rationales_section(report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_rationales_no_scores(self):
        """Test rationales section with no overall score"""
        report = ExportableReport.objects.create(
            chat=self.chat,
            overall_score=None
        )

        _, heading_style, normal_style = _create_styles()
        result = _create_score_rationales_section(report, heading_style, normal_style)

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
        result = _create_score_rationales_section(report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


class PDFRecommendedExercisesTest(TestCase):
    """Test _create_recommended_exercises_section"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
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
        result = _create_recommended_exercises_section(report, heading_style, normal_style)

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
        result = _create_recommended_exercises_section(report, heading_style, normal_style)

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
        result = _create_recommended_exercises_section(report, heading_style, normal_style)

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
        result = _create_recommended_exercises_section(report, heading_style, normal_style)

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
        result = _create_recommended_exercises_section(report, heading_style, normal_style)

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
        result = _create_recommended_exercises_section(report, heading_style, normal_style)

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
        result = _create_recommended_exercises_section(report, heading_style, normal_style)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
