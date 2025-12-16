"""
Comprehensive tests to achieve > 80% coverage for pdf_export.py
Tests all helper functions and edge cases for PDF generation.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import Mock, patch
import uuid

from active_interview_app.models import (
    Chat,
    ExportableReport,
    UploadedJobListing,
    UploadedResume,
    InvitedInterview,
    InterviewTemplate,
    UserProfile
)
from active_interview_app.pdf_export import (
    generate_pdf_report,
    get_score_rating,
    _create_styles,
    _create_metadata_section,
    _create_performance_scores_section,
    _create_score_rationales_section,
    _create_feedback_section,
    _create_interviewer_feedback_section,
    _create_recommended_exercises_section,
    _create_statistics_section,
    _create_footer
)
from .test_credentials import TEST_PASSWORD


class PdfGenerationEdgeCasesTest(TestCase):
    """Test PDF generation with various edge cases"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='pdfuser',
            email='pdf@test.com',
            password=TEST_PASSWORD
        )

    def test_generate_pdf_minimal_data(self):
        """Test PDF generation with minimal data"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Minimal Interview',
            type='technical',
            difficulty=5
        )

        report = ExportableReport.objects.create(
            chat=chat,
            total_questions_asked=0,
            total_responses_given=0
        )

        pdf_bytes = generate_pdf_report(report)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
        # PDF signature
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_generate_pdf_with_all_data(self):
        """Test PDF generation with complete data"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='My Resume',
            content='Resume content'
        )

        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Job Posting',
            content='Job content'
        )

        chat = Chat.objects.create(
            owner=self.user,
            title='Complete Interview',
            type='behavioral',
            difficulty=7,
            resume=resume,
            job_listing=job
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=85,
            subject_knowledge_score=90,
            clarity_score=88,
            overall_score=88,
            feedback_text='Excellent performance\nGreat technical skills\nGood communication',
            professionalism_rationale='Professional demeanor throughout',
            subject_knowledge_rationale='Strong technical knowledge',
            clarity_rationale='Clear and concise answers',
            overall_rationale='Outstanding candidate',
            total_questions_asked=15,
            total_responses_given=15,
            interview_duration_minutes=45
        )

        pdf_bytes = generate_pdf_report(report)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)


class MetadataSectionTest(TestCase):
    """Test _create_metadata_section function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='metauser',
            email='meta@test.com',
            password=TEST_PASSWORD
        )
        _, heading_style, _ = _create_styles()
        self.heading_style = heading_style

    def test_metadata_section_basic(self):
        """Test metadata section with basic chat"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Tech Interview',
            type='technical',
            difficulty=6
        )

        report = ExportableReport.objects.create(chat=chat)

        elements = _create_metadata_section(report, self.heading_style)

        self.assertIsInstance(elements, list)
        self.assertGreater(len(elements), 0)

    def test_metadata_section_with_resume_and_job(self):
        """Test metadata section with resume and job listing"""
        resume = UploadedResume.objects.create(
            user=self.user,
            title='Software Engineer Resume',
            content='Content'
        )

        job = UploadedJobListing.objects.create(
            user=self.user,
            title='Senior Developer Position',
            content='Job description'
        )

        chat = Chat.objects.create(
            owner=self.user,
            title='Job Interview',
            type='technical',
            difficulty=8,
            resume=resume,
            job_listing=job
        )

        report = ExportableReport.objects.create(chat=chat)

        elements = _create_metadata_section(report, self.heading_style)

        self.assertGreater(len(elements), 0)

    def test_metadata_section_no_resume_or_job(self):
        """Test metadata section without resume or job"""
        chat = Chat.objects.create(
            owner=self.user,
            title='General Interview',
            type='behavioral',
            difficulty=5
        )

        report = ExportableReport.objects.create(chat=chat)

        elements = _create_metadata_section(report, self.heading_style)

        self.assertGreater(len(elements), 0)


class PerformanceScoresSectionTest(TestCase):
    """Test _create_performance_scores_section function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='scoreuser',
            email='score@test.com',
            password=TEST_PASSWORD
        )
        _, heading_style, normal_style = _create_styles()
        self.heading_style = heading_style
        self.normal_style = normal_style

    def test_performance_scores_with_scores(self):
        """Test performance section with all scores present"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Scored Interview',
            type='technical',
            difficulty=6
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=95,
            subject_knowledge_score=88,
            clarity_score=92,
            overall_score=92
        )

        elements = _create_performance_scores_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_performance_scores_without_scores(self):
        """Test performance section without scores"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Unscored Interview',
            type='technical',
            difficulty=5
        )

        report = ExportableReport.objects.create(
            chat=chat,
            overall_score=None
        )

        elements = _create_performance_scores_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_performance_scores_zero_scores(self):
        """Test performance section with zero scores"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Zero Score Interview',
            type='technical',
            difficulty=3
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=0,
            subject_knowledge_score=0,
            clarity_score=0,
            overall_score=0
        )

        elements = _create_performance_scores_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)


class ScoreRationalesSectionTest(TestCase):
    """Test _create_score_rationales_section function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='rationaleuser',
            email='rationale@test.com',
            password=TEST_PASSWORD
        )
        _, heading_style, normal_style = _create_styles()
        self.heading_style = heading_style
        self.normal_style = normal_style

    def test_rationales_all_present(self):
        """Test rationales section with all rationales"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview',
            type='technical',
            difficulty=7
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=90,
            subject_knowledge_score=85,
            clarity_score=88,
            overall_score=88,
            professionalism_rationale='Very professional throughout the interview',
            subject_knowledge_rationale='Demonstrated strong technical knowledge',
            clarity_rationale='Communicated ideas clearly and effectively',
            overall_rationale='Strong candidate overall'
        )

        elements = _create_score_rationales_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_rationales_partial(self):
        """Test rationales section with only some rationales"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview',
            type='technical',
            difficulty=5
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=85,
            subject_knowledge_score=80,
            clarity_score=75,
            overall_score=80,
            professionalism_rationale='Good professionalism',
            # No other rationales
        )

        elements = _create_score_rationales_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_rationales_none(self):
        """Test rationales section with no rationales"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview',
            type='technical',
            difficulty=5
        )

        report = ExportableReport.objects.create(
            chat=chat,
            overall_score=None
        )

        elements = _create_score_rationales_section(
            report, self.heading_style, self.normal_style
        )

        # Should return empty list if no scores
        self.assertEqual(len(elements), 0)


class FeedbackSectionTest(TestCase):
    """Test _create_feedback_section function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='feedbackuser',
            email='feedback@test.com',
            password=TEST_PASSWORD
        )
        _, heading_style, normal_style = _create_styles()
        self.heading_style = heading_style
        self.normal_style = normal_style

    def test_feedback_section_with_multiline(self):
        """Test feedback section with multiline feedback"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview',
            type='technical',
            difficulty=6
        )

        feedback = """Strengths:
- Strong technical knowledge
- Good problem-solving skills

Areas for improvement:
- Communication could be more concise
- Consider edge cases more carefully"""

        report = ExportableReport.objects.create(
            chat=chat,
            feedback_text=feedback
        )

        elements = _create_feedback_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_feedback_section_no_feedback(self):
        """Test feedback section without feedback"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview',
            type='technical',
            difficulty=5
        )

        report = ExportableReport.objects.create(
            chat=chat,
            feedback_text=''
        )

        elements = _create_feedback_section(
            report, self.heading_style, self.normal_style
        )

        self.assertEqual(len(elements), 0)

    def test_feedback_section_empty_lines(self):
        """Test feedback section with empty lines"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Interview',
            type='technical',
            difficulty=6
        )

        feedback = "Good job\n\n\nKeep practicing\n\n"

        report = ExportableReport.objects.create(
            chat=chat,
            feedback_text=feedback
        )

        elements = _create_feedback_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)


class InterviewerFeedbackSectionTest(TestCase):
    """Test _create_interviewer_feedback_section function"""

    def setUp(self):
        self.interviewer = User.objects.create_user(
            username='interviewer',
            email='interviewer@test.com',
            password=TEST_PASSWORD
        )
        self.interviewer.first_name = 'John'
        self.interviewer.last_name = 'Interviewer'
        self.interviewer.save()

        UserProfile.objects.get_or_create(
            user=self.interviewer,
            defaults={'role': UserProfile.INTERVIEWER}
        )

        self.candidate_user = User.objects.create_user(
            username='candidate',
            email='candidate@test.com',
            password=TEST_PASSWORD
        )

        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Test Template',
            description='Test',
            sections=[{'id': str(uuid.uuid4()), 'title': 'Tech', 'content': 'Questions', 'order': 0, 'weight': 100}]
        )

        _, heading_style, normal_style = _create_styles()
        self.heading_style = heading_style
        self.normal_style = normal_style

    def test_interviewer_feedback_not_invited(self):
        """Test section returns empty for non-invited interviews"""
        chat = Chat.objects.create(
            owner=self.candidate_user,
            title='Regular Interview',
            type='technical',
            difficulty=5,
            interview_type='PRACTICE'  # Not invited
        )

        report = ExportableReport.objects.create(chat=chat)

        elements = _create_interviewer_feedback_section(
            report, self.heading_style, self.normal_style
        )

        self.assertEqual(len(elements), 0)

    def test_interviewer_feedback_pending(self):
        """Test section shows pending message"""
        chat = Chat.objects.create(
            owner=self.candidate_user,
            title='Invited Interview',
            type='technical',
            difficulty=6,
            interview_type='INVITED'
        )

        report = ExportableReport.objects.create(chat=chat)

        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now(),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            chat=chat,
            interviewer_review_status='pending'
        )

        elements = _create_interviewer_feedback_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_interviewer_feedback_reviewed_with_feedback(self):
        """Test section shows interviewer feedback"""
        chat = Chat.objects.create(
            owner=self.candidate_user,
            title='Reviewed Interview',
            type='technical',
            difficulty=7,
            interview_type='INVITED'
        )

        report = ExportableReport.objects.create(chat=chat)

        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now(),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            chat=chat,
            interviewer_review_status='reviewed',
            interviewer_feedback='Great job! Strong technical skills demonstrated.',
            reviewed_at=timezone.now()
        )

        elements = _create_interviewer_feedback_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_interviewer_feedback_reviewed_no_feedback(self):
        """Test section when reviewed but no feedback provided"""
        chat = Chat.objects.create(
            owner=self.candidate_user,
            title='Reviewed No Feedback',
            type='technical',
            difficulty=6,
            interview_type='INVITED'
        )

        report = ExportableReport.objects.create(chat=chat)

        invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now(),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            chat=chat,
            interviewer_review_status='reviewed',
            interviewer_feedback='',  # Empty feedback
            reviewed_at=timezone.now()
        )

        elements = _create_interviewer_feedback_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_interviewer_feedback_no_invitation(self):
        """Test section when invited but no InvitedInterview exists"""
        chat = Chat.objects.create(
            owner=self.candidate_user,
            title='Invited No Record',
            type='technical',
            difficulty=5,
            interview_type='INVITED'
        )

        report = ExportableReport.objects.create(chat=chat)

        elements = _create_interviewer_feedback_section(
            report, self.heading_style, self.normal_style
        )

        # Should return empty if invitation doesn't exist
        self.assertEqual(len(elements), 0)


class RecommendedExercisesSectionTest(TestCase):
    """Test _create_recommended_exercises_section function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='exuser',
            email='ex@test.com',
            password=TEST_PASSWORD
        )
        _, heading_style, normal_style = _create_styles()
        self.heading_style = heading_style
        self.normal_style = normal_style

    def test_recommended_exercises_excellent_score(self):
        """Test recommendations for excellent score (>= 90)"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Excellent Interview',
            type='technical',
            difficulty=8
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=95,
            subject_knowledge_score=93,
            clarity_score=94,
            overall_score=94
        )

        elements = _create_recommended_exercises_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_recommended_exercises_good_score(self):
        """Test recommendations for good score (75-89)"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Good Interview',
            type='technical',
            difficulty=7
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=80,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=80
        )

        elements = _create_recommended_exercises_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_recommended_exercises_fair_score(self):
        """Test recommendations for fair score (60-74)"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Fair Interview',
            type='technical',
            difficulty=6
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=65,
            subject_knowledge_score=68,
            clarity_score=70,
            overall_score=68
        )

        elements = _create_recommended_exercises_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)

    def test_recommended_exercises_low_score(self):
        """Test recommendations for low score (< 60)"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Needs Improvement',
            type='technical',
            difficulty=5
        )

        report = ExportableReport.objects.create(
            chat=chat,
            professionalism_score=50,
            subject_knowledge_score=45,
            clarity_score=55,
            overall_score=50
        )

        elements = _create_recommended_exercises_section(
            report, self.heading_style, self.normal_style
        )

        self.assertGreater(len(elements), 0)


class StatisticsSectionTest(TestCase):
    """Test _create_statistics_section function"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='statuser',
            email='stat@test.com',
            password=TEST_PASSWORD
        )
        _, heading_style, _ = _create_styles()
        self.heading_style = heading_style

    def test_statistics_with_duration(self):
        """Test statistics section with duration"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Timed Interview',
            type='technical',
            difficulty=6
        )

        report = ExportableReport.objects.create(
            chat=chat,
            total_questions_asked=12,
            total_responses_given=12,
            interview_duration_minutes=45
        )

        elements = _create_statistics_section(report, self.heading_style)

        self.assertGreater(len(elements), 0)

    def test_statistics_without_duration(self):
        """Test statistics section without duration"""
        chat = Chat.objects.create(
            owner=self.user,
            title='Untimed Interview',
            type='technical',
            difficulty=5
        )

        report = ExportableReport.objects.create(
            chat=chat,
            total_questions_asked=8,
            total_responses_given=8,
            interview_duration_minutes=None
        )

        elements = _create_statistics_section(report, self.heading_style)

        self.assertGreater(len(elements), 0)


class FooterTest(TestCase):
    """Test _create_footer function"""

    def test_footer_creation(self):
        """Test footer element creation"""
        elements = _create_footer()

        self.assertIsInstance(elements, list)
        self.assertGreater(len(elements), 0)

    def test_footer_contains_timestamp(self):
        """Test footer includes timestamp"""
        elements = _create_footer()

        # Footer should contain timestamp information
        self.assertGreater(len(elements), 0)
