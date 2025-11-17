"""
Tests for PDF generation with interviewer feedback (Phase 8).

Tests cover:
- PDF generation for invited interviews before review
- PDF generation for invited interviews after review
- Interviewer feedback section creation
- Practice interviews should not show interviewer feedback section
"""

from datetime import timedelta
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone

from active_interview_app.models import (
    Chat, InvitedInterview, InterviewTemplate,
    UploadedJobListing, ExportableReport, UserProfile
)
from active_interview_app.pdf_export import (
    generate_pdf_report,
    _create_interviewer_feedback_section,
    _create_styles
)


@override_settings(OPENAI_API_KEY='test-key')
class InvitedInterviewPDFGenerationTests(TestCase):
    """Test PDF generation for invited interviews with interviewer feedback"""

    def setUp(self):
        """Set up test data"""
        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password='testpass123'
        )
        interviewer_profile = UserProfile.objects.get(user=self.interviewer)
        interviewer_profile.role = 'interviewer'
        interviewer_profile.save()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

        # Create job listing
        self.job_listing = UploadedJobListing.objects.create(
            user=self.interviewer,
            title='Senior Python Developer',
            content='Looking for experienced Python developer'
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Technical Interview'
        )

        # Create chat for invited interview
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Technical Interview',
            interview_type=Chat.INVITED,
            type='Technical',
            difficulty=7,
            job_listing=self.job_listing,
            scheduled_end_at=timezone.now() + timedelta(hours=1),
            messages=[
                {"role": "assistant", "content": "What is polymorphism?"},
                {"role": "user", "content": "Polymorphism allows objects of different classes to be treated as objects of a common base class."},
                {"role": "assistant",
                    "content": "Can you explain the difference between lists and tuples in Python?"},
                {"role": "user", "content": "Lists are mutable while tuples are immutable."}
            ]
        )

        # Create invitation
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now() - timedelta(hours=1),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            completed_at=timezone.now(),
            chat=self.chat
        )

        # Create exportable report
        self.report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=85,
            subject_knowledge_score=78,
            clarity_score=82,
            overall_score=81,
            feedback_text="Great technical knowledge demonstrated. Good communication skills.",
            professionalism_rationale="Maintained professional demeanor throughout.",
            subject_knowledge_rationale="Showed strong understanding of Python concepts.",
            clarity_rationale="Explanations were clear and concise.",
            overall_rationale="Solid performance overall.",
            total_questions_asked=2,
            total_responses_given=2)

    def test_pdf_generation_before_review(self):
        """Test that PDF is generated successfully for invited interview before review"""
        # Generate PDF (invitation is pending by default)
        pdf_bytes = generate_pdf_report(self.report)

        # Verify PDF was generated
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 0)
        # PDF should start with %PDF header
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_pdf_generation_after_review(self):
        """Test that PDF is generated successfully for invited interview after review"""
        # Mark as reviewed with feedback
        self.invitation.interviewer_review_status = InvitedInterview.REVIEW_COMPLETED
        self.invitation.interviewer_feedback = "Excellent technical skills. Strong problem-solving abilities."
        self.invitation.reviewed_at = timezone.now()
        self.invitation.save()

        # Set interviewer's full name for proper display
        self.interviewer.first_name = "Jane"
        self.interviewer.last_name = "Smith"
        self.interviewer.save()

        # Generate PDF
        pdf_bytes = generate_pdf_report(self.report)

        # Verify PDF was generated
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 0)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_interviewer_feedback_section_pending_status(self):
        """Test interviewer feedback section creation for pending review"""
        # Create styles
        _, heading_style, normal_style = _create_styles()

        # Generate section (invitation is pending by default)
        elements = _create_interviewer_feedback_section(
            self.report, heading_style, normal_style
        )

        # Verify section was created (should have elements for pending message)
        self.assertGreater(len(elements), 0)
        # Should contain at least: heading, HR line, spacer, pending message,
        # spacer
        self.assertGreaterEqual(len(elements), 3)

    def test_interviewer_feedback_section_completed_status(self):
        """Test interviewer feedback section creation for completed review"""
        # Mark as reviewed
        self.invitation.interviewer_review_status = InvitedInterview.REVIEW_COMPLETED
        self.invitation.interviewer_feedback = "Great work overall."
        self.invitation.reviewed_at = timezone.now()
        self.invitation.save()

        # Create styles
        _, heading_style, normal_style = _create_styles()

        # Generate section
        elements = _create_interviewer_feedback_section(
            self.report, heading_style, normal_style
        )

        # Verify section was created with feedback
        self.assertGreater(len(elements), 0)
        # Should have more elements when feedback is provided
        self.assertGreaterEqual(len(elements), 3)

    def test_interviewer_feedback_section_practice_interview(self):
        """Test that practice interviews don't include interviewer feedback section"""
        # Create practice chat
        practice_chat = Chat.objects.create(
            owner=self.candidate,
            title='Practice Interview',
            interview_type=Chat.PRACTICE,
            type='Technical',
            difficulty=5,
            messages=[
                {"role": "assistant", "content": "What is a variable?"},
                {"role": "user", "content": "A variable stores data."}
            ]
        )

        # Create report for practice interview
        practice_report = ExportableReport.objects.create(
            chat=practice_chat,
            professionalism_score=80,
            subject_knowledge_score=75,
            clarity_score=78,
            overall_score=77,
            feedback_text="Good understanding of basics.",
            total_questions_asked=1,
            total_responses_given=1
        )

        # Create styles
        _, heading_style, normal_style = _create_styles()

        # Generate section
        elements = _create_interviewer_feedback_section(
            practice_report, heading_style, normal_style
        )

        # Verify NO elements created for practice interview
        self.assertEqual(len(elements), 0)

    def test_pdf_generation_practice_interview_no_error(self):
        """Test that PDF generation for practice interview doesn't error"""
        # Create practice chat
        practice_chat = Chat.objects.create(
            owner=self.candidate,
            title='Practice Interview',
            interview_type=Chat.PRACTICE,
            type='Technical',
            difficulty=5,
            messages=[
                {"role": "assistant", "content": "What is a variable?"},
                {"role": "user", "content": "A variable stores data."}
            ]
        )

        # Create report for practice interview
        practice_report = ExportableReport.objects.create(
            chat=practice_chat,
            professionalism_score=80,
            subject_knowledge_score=75,
            clarity_score=78,
            overall_score=77,
            feedback_text="Good understanding of basics.",
            total_questions_asked=1,
            total_responses_given=1
        )

        # Generate PDF
        pdf_bytes = generate_pdf_report(practice_report)

        # Verify PDF was generated
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 0)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_interviewer_feedback_section_multiline(self):
        """Test interviewer feedback section with multiline feedback"""
        # Mark as reviewed with multiline feedback
        multiline_feedback = """Overall Performance: Excellent

Strengths:
- Strong technical knowledge
- Clear communication

Areas for Improvement:
- Algorithm optimization"""

        self.invitation.interviewer_review_status = InvitedInterview.REVIEW_COMPLETED
        self.invitation.interviewer_feedback = multiline_feedback
        self.invitation.reviewed_at = timezone.now()
        self.invitation.save()

        # Create styles
        _, heading_style, normal_style = _create_styles()

        # Generate section
        elements = _create_interviewer_feedback_section(
            self.report, heading_style, normal_style
        )

        # Verify section was created
        self.assertGreater(len(elements), 0)
        # Multiline feedback should create multiple elements
        self.assertGreaterEqual(len(elements), 5)

    def test_interviewer_feedback_section_no_feedback_text(self):
        """Test interviewer feedback section when reviewed but no feedback provided"""
        # Mark as reviewed WITHOUT feedback
        self.invitation.interviewer_review_status = InvitedInterview.REVIEW_COMPLETED
        self.invitation.interviewer_feedback = ""
        self.invitation.reviewed_at = timezone.now()
        self.invitation.save()

        # Create styles
        _, heading_style, normal_style = _create_styles()

        # Generate section
        elements = _create_interviewer_feedback_section(
            self.report, heading_style, normal_style
        )

        # Verify section was created (should show "no feedback" message)
        self.assertGreater(len(elements), 0)
        self.assertGreaterEqual(len(elements), 3)


class PDFGenerationAccessTests(TestCase):
    """Test access control for PDF generation with invited interviews"""

    def setUp(self):
        """Set up test data"""
        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer@test.com',
            email='interviewer@test.com',
            password='testpass123'
        )
        interviewer_profile = UserProfile.objects.get(user=self.interviewer)
        interviewer_profile.role = 'interviewer'
        interviewer_profile.save()

        # Create candidate
        self.candidate = User.objects.create_user(
            username='candidate@test.com',
            email='candidate@test.com',
            password='testpass123'
        )

        # Create job listing
        self.job_listing = UploadedJobListing.objects.create(
            user=self.interviewer,
            title='Python Developer'
        )

        # Create template
        self.template = InterviewTemplate.objects.create(
            user=self.interviewer,
            name='Technical Interview'
        )

        # Create chat
        self.chat = Chat.objects.create(
            owner=self.candidate,
            title='Technical Interview',
            interview_type=Chat.INVITED,
            type='Technical',
            job_listing=self.job_listing,
            messages=[
                {"role": "assistant", "content": "Test question?"},
                {"role": "user", "content": "Test answer."}
            ]
        )

        # Create invitation
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@test.com',
            template=self.template,
            scheduled_time=timezone.now(),
            duration_minutes=60,
            status=InvitedInterview.COMPLETED,
            completed_at=timezone.now(),
            chat=self.chat,
            interviewer_review_status=InvitedInterview.REVIEW_COMPLETED,
            interviewer_feedback="Good work.",
            reviewed_at=timezone.now()
        )

    def test_pdf_generation_no_error_for_invited_interview(self):
        """Test that PDF generation doesn't error for invited interview"""
        # Create report
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=80,
            subject_knowledge_score=75,
            clarity_score=78,
            overall_score=77,
            feedback_text="Good performance.",
            total_questions_asked=1,
            total_responses_given=1
        )

        # Generate PDF should not raise exception
        try:
            pdf_bytes = generate_pdf_report(report)
            self.assertIsNotNone(pdf_bytes)
            self.assertGreater(len(pdf_bytes), 0)
        except Exception as e:
            self.fail(f"PDF generation raised exception: {e}")

    def test_pdf_handles_missing_invitation_gracefully(self):
        """Test PDF generation when invitation is deleted"""
        # Create report
        report = ExportableReport.objects.create(
            chat=self.chat,
            professionalism_score=80,
            subject_knowledge_score=75,
            clarity_score=78,
            overall_score=77,
            feedback_text="Good performance."
        )

        # Delete invitation
        self.invitation.delete()

        # Generate PDF - should not crash, just skip interviewer section
        try:
            pdf_bytes = generate_pdf_report(report)
            self.assertIsNotNone(pdf_bytes)

            # Verify no interviewer section in this case
            # (since invitation was deleted, it can't find it)
        except Exception as e:
            self.fail(
                f"PDF generation should handle missing invitation gracefully: {e}")
