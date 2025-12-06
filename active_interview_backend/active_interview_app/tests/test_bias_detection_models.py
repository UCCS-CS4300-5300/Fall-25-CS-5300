"""
Comprehensive tests for Bias Detection models (BiasTermLibrary, BiasAnalysisResult)

Related to Issues #18, #57, #58, #59 (Bias Guardrails).
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from active_interview_app.models import (
    BiasTermLibrary,
    BiasAnalysisResult,
    InvitedInterview,
    InterviewTemplate,
    Chat
)


class BiasTermLibraryModelTest(TestCase):
    """Test cases for BiasTermLibrary model"""

    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123'
        )

    def test_create_bias_term_with_all_fields(self):
        """Test creating a bias term with all fields"""
        term = BiasTermLibrary.objects.create(
            term='cultural fit',
            category=BiasTermLibrary.OTHER,
            pattern=r'\b(cultural fit|culture fit)\b',
            explanation='Subjective term that can mask bias',
            neutral_alternatives=[
                'team collaboration skills',
                'alignment with company values'
            ],
            severity=BiasTermLibrary.WARNING,
            is_active=True,
            created_by=self.admin_user
        )

        self.assertEqual(term.term, 'cultural fit')
        self.assertEqual(term.category, BiasTermLibrary.OTHER)
        self.assertEqual(term.pattern, r'\b(cultural fit|culture fit)\b')
        self.assertEqual(term.severity, BiasTermLibrary.WARNING)
        self.assertTrue(term.is_active)
        self.assertEqual(term.created_by, self.admin_user)
        self.assertEqual(len(term.neutral_alternatives), 2)

    def test_bias_term_str_method(self):
        """Test the __str__ method returns term with category"""
        term = BiasTermLibrary.objects.create(
            term='too old',
            category=BiasTermLibrary.AGE,
            pattern=r'\btoo old\b',
            explanation='Age discrimination',
            neutral_alternatives=['requires additional training'],
            severity=BiasTermLibrary.BLOCKING
        )
        self.assertEqual(str(term), 'too old (Age-related)')

    def test_bias_term_default_values(self):
        """Test default values are set correctly"""
        term = BiasTermLibrary.objects.create(
            term='test term',
            category=BiasTermLibrary.GENDER,
            pattern=r'\btest\b',
            explanation='Test explanation',
            neutral_alternatives=[]
        )
        self.assertEqual(term.severity, BiasTermLibrary.WARNING)
        self.assertTrue(term.is_active)
        self.assertEqual(term.detection_count, 0)

    def test_bias_term_category_choices(self):
        """Test all category choices are valid"""
        categories = [
            BiasTermLibrary.AGE,
            BiasTermLibrary.GENDER,
            BiasTermLibrary.RACE,
            BiasTermLibrary.DISABILITY,
            BiasTermLibrary.APPEARANCE,
            BiasTermLibrary.FAMILY,
            BiasTermLibrary.OTHER
        ]

        for category in categories:
            term = BiasTermLibrary.objects.create(
                term=f'test_{category}',
                category=category,
                pattern=r'\btest\b',
                explanation='Test',
                neutral_alternatives=[]
            )
            self.assertEqual(term.category, category)
            term.delete()

    def test_bias_term_severity_choices(self):
        """Test both severity levels work correctly"""
        # Warning level
        warning_term = BiasTermLibrary.objects.create(
            term='warning_term',
            category=BiasTermLibrary.OTHER,
            pattern=r'\btest\b',
            explanation='Test',
            neutral_alternatives=[],
            severity=BiasTermLibrary.WARNING
        )
        self.assertEqual(warning_term.severity, 1)
        self.assertEqual(warning_term.get_severity_display(), 'Warning')

        # Blocking level
        blocking_term = BiasTermLibrary.objects.create(
            term='blocking_term',
            category=BiasTermLibrary.OTHER,
            pattern=r'\btest\b',
            explanation='Test',
            neutral_alternatives=[],
            severity=BiasTermLibrary.BLOCKING
        )
        self.assertEqual(blocking_term.severity, 2)
        self.assertEqual(blocking_term.get_severity_display(), 'Blocking')

    def test_bias_term_json_field(self):
        """Test JSONField for neutral_alternatives"""
        alternatives = [
            'alternative 1',
            'alternative 2',
            'alternative 3'
        ]
        term = BiasTermLibrary.objects.create(
            term='test',
            category=BiasTermLibrary.OTHER,
            pattern=r'\btest\b',
            explanation='Test',
            neutral_alternatives=alternatives
        )

        # Reload from database
        term.refresh_from_db()
        self.assertEqual(term.neutral_alternatives, alternatives)
        self.assertIsInstance(term.neutral_alternatives, list)

    def test_bias_term_ordering(self):
        """Test default ordering by category and term"""
        BiasTermLibrary.objects.create(
            term='z_term',
            category=BiasTermLibrary.GENDER,
            pattern=r'\bz\b',
            explanation='Test',
            neutral_alternatives=[]
        )
        BiasTermLibrary.objects.create(
            term='a_term',
            category=BiasTermLibrary.AGE,
            pattern=r'\ba\b',
            explanation='Test',
            neutral_alternatives=[]
        )
        BiasTermLibrary.objects.create(
            term='m_term',
            category=BiasTermLibrary.AGE,
            pattern=r'\bm\b',
            explanation='Test',
            neutral_alternatives=[]
        )

        terms = list(BiasTermLibrary.objects.all())
        # Should be ordered by category first, then term
        self.assertEqual(terms[0].category, BiasTermLibrary.AGE)
        self.assertEqual(terms[0].term, 'a_term')
        self.assertEqual(terms[1].category, BiasTermLibrary.AGE)
        self.assertEqual(terms[1].term, 'm_term')
        self.assertEqual(terms[2].category, BiasTermLibrary.GENDER)

    def test_bias_term_created_by_nullable(self):
        """Test created_by can be null"""
        term = BiasTermLibrary.objects.create(
            term='test',
            category=BiasTermLibrary.OTHER,
            pattern=r'\btest\b',
            explanation='Test',
            neutral_alternatives=[],
            created_by=None
        )
        self.assertIsNone(term.created_by)

    def test_bias_term_timestamps(self):
        """Test created_at and updated_at are set automatically"""
        term = BiasTermLibrary.objects.create(
            term='test',
            category=BiasTermLibrary.OTHER,
            pattern=r'\btest\b',
            explanation='Test',
            neutral_alternatives=[]
        )
        self.assertIsNotNone(term.created_at)
        self.assertIsNotNone(term.updated_at)

        # Update and check updated_at changes
        old_updated_at = term.updated_at
        import time
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        term.explanation = 'Updated explanation'
        term.save()
        self.assertGreater(term.updated_at, old_updated_at)


class BiasAnalysisResultModelTest(TestCase):
    """Test cases for BiasAnalysisResult model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.interviewer = User.objects.create_user(
            username='interviewer',
            password='testpass123'
        )

        # Create a template for InvitedInterview
        self.template = InterviewTemplate.objects.create(
            name='Test Template',
            user=self.interviewer,
            description='Test'
        )

        # Create an InvitedInterview for testing
        self.invitation = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='candidate@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timezone.timedelta(days=1)
        )

    def test_create_bias_analysis_result(self):
        """Test creating a bias analysis result"""
        content_type = ContentType.objects.get_for_model(InvitedInterview)

        result = BiasAnalysisResult.objects.create(
            content_type=content_type,
            object_id=self.invitation.pk,
            flagged_terms=[
                {
                    'term': 'cultural fit',
                    'category': 'other',
                    'severity': 1,
                    'positions': [(10, 22)],
                    'suggestions': ['team collaboration']
                }
            ],
            bias_score=0.35,
            severity_level='LOW',
            total_flags=1,
            blocking_flags=0,
            warning_flags=1,
            saved_with_warnings=False,
            user_acknowledged=False,
            feedback_text_hash='abc123'
        )

        self.assertEqual(result.content_type, content_type)
        self.assertEqual(result.object_id, self.invitation.pk)
        self.assertEqual(result.severity_level, 'LOW')
        self.assertEqual(result.bias_score, 0.35)
        self.assertEqual(result.total_flags, 1)
        self.assertEqual(result.blocking_flags, 0)
        self.assertEqual(result.warning_flags, 1)

    def test_bias_analysis_result_str_method(self):
        """Test the __str__ method"""
        content_type = ContentType.objects.get_for_model(InvitedInterview)

        result = BiasAnalysisResult.objects.create(
            content_type=content_type,
            object_id=self.invitation.pk,
            severity_level='MEDIUM',
            total_flags=3
        )

        str_repr = str(result)
        self.assertIn('MEDIUM', str_repr)
        self.assertIn('3 flags', str_repr)

    def test_bias_analysis_result_default_values(self):
        """Test default values are set correctly"""
        content_type = ContentType.objects.get_for_model(InvitedInterview)

        result = BiasAnalysisResult.objects.create(
            content_type=content_type,
            object_id=self.invitation.pk
        )

        self.assertEqual(result.flagged_terms, [])
        self.assertEqual(result.severity_level, 'CLEAN')
        self.assertEqual(result.total_flags, 0)
        self.assertEqual(result.blocking_flags, 0)
        self.assertEqual(result.warning_flags, 0)
        self.assertFalse(result.saved_with_warnings)
        self.assertFalse(result.user_acknowledged)

    def test_bias_analysis_result_severity_choices(self):
        """Test all severity level choices"""
        content_type = ContentType.objects.get_for_model(InvitedInterview)

        severity_levels = ['CLEAN', 'LOW', 'MEDIUM', 'HIGH']

        for i, level in enumerate(severity_levels):
            # Create a unique invitation for each test
            invitation = InvitedInterview.objects.create(
                interviewer=self.interviewer,
                candidate_email=f'test{i}@example.com',
                template=self.template,
                scheduled_time=timezone.now() + timezone.timedelta(days=1)
            )

            result = BiasAnalysisResult.objects.create(
                content_type=content_type,
                object_id=invitation.pk,
                severity_level=level
            )
            self.assertEqual(result.severity_level, level)

    def test_bias_analysis_result_bias_score_validation(self):
        """Test bias_score is validated between 0.0 and 1.0"""
        content_type = ContentType.objects.get_for_model(InvitedInterview)

        # Valid scores
        valid_result = BiasAnalysisResult.objects.create(
            content_type=content_type,
            object_id=self.invitation.pk,
            bias_score=0.5
        )
        self.assertEqual(valid_result.bias_score, 0.5)

        # Test min boundary
        min_result = BiasAnalysisResult(
            content_type=content_type,
            object_id=str(self.invitation.pk),
            bias_score=0.0,
            flagged_terms=[]
        )
        min_result.full_clean()  # Should not raise

        # Test max boundary
        max_result = BiasAnalysisResult(
            content_type=content_type,
            object_id=str(self.invitation.pk),
            bias_score=1.0,
            flagged_terms=[]
        )
        max_result.full_clean()  # Should not raise

        # Test invalid score (too high)
        with self.assertRaises(ValidationError):
            invalid_result = BiasAnalysisResult(
                content_type=content_type,
                object_id=str(self.invitation.pk),
                bias_score=1.5,
                flagged_terms=[]
            )
            invalid_result.full_clean()

        # Test invalid score (negative)
        with self.assertRaises(ValidationError):
            invalid_result = BiasAnalysisResult(
                content_type=content_type,
                object_id=str(self.invitation.pk),
                bias_score=-0.1,
                flagged_terms=[]
            )
            invalid_result.full_clean()

    def test_bias_analysis_result_json_field(self):
        """Test JSONField for flagged_terms"""
        content_type = ContentType.objects.get_for_model(InvitedInterview)

        flagged_data = [
            {
                'term': 'cultural fit',
                'category': 'other',
                'severity': 1,
                'positions': [[5, 17]],  # JSON converts tuples to lists
                'suggestions': ['team skills']
            },
            {
                'term': 'too old',
                'category': 'age',
                'severity': 2,
                'positions': [[25, 32]],  # JSON converts tuples to lists
                'suggestions': ['experienced']
            }
        ]

        result = BiasAnalysisResult.objects.create(
            content_type=content_type,
            object_id=self.invitation.pk,
            flagged_terms=flagged_data
        )

        # Reload from database
        result.refresh_from_db()
        self.assertEqual(result.flagged_terms, flagged_data)
        self.assertIsInstance(result.flagged_terms, list)
        self.assertEqual(len(result.flagged_terms), 2)

    def test_bias_analysis_result_generic_foreign_key(self):
        """Test GenericForeignKey works with different content types"""
        # Test with InvitedInterview
        invitation_ct = ContentType.objects.get_for_model(InvitedInterview)
        invitation_result = BiasAnalysisResult.objects.create(
            content_type=invitation_ct,
            object_id=self.invitation.pk,
            severity_level='LOW'
        )
        self.assertEqual(invitation_result.content_object, self.invitation)

        # Test with Chat
        chat = Chat.objects.create(
            owner=self.user,
            title='Test Chat'
        )
        chat_ct = ContentType.objects.get_for_model(Chat)
        chat_result = BiasAnalysisResult.objects.create(
            content_type=chat_ct,
            object_id=chat.pk,
            severity_level='MEDIUM'
        )
        self.assertEqual(chat_result.content_object, chat)

    def test_bias_analysis_result_ordering(self):
        """Test default ordering by analyzed_at (newest first)"""
        content_type = ContentType.objects.get_for_model(InvitedInterview)

        # Create multiple results
        result1 = BiasAnalysisResult.objects.create(
            content_type=content_type,
            object_id=self.invitation.pk,
            severity_level='LOW'
        )

        import time
        time.sleep(0.01)

        invitation2 = InvitedInterview.objects.create(
            interviewer=self.interviewer,
            candidate_email='test2@example.com',
            template=self.template,
            scheduled_time=timezone.now() + timezone.timedelta(days=1)
        )

        result2 = BiasAnalysisResult.objects.create(
            content_type=content_type,
            object_id=invitation2.pk,
            severity_level='MEDIUM'
        )

        results = list(BiasAnalysisResult.objects.all())
        # Should be ordered by analyzed_at descending (newest first)
        self.assertEqual(results[0].pk, result2.pk)
        self.assertEqual(results[1].pk, result1.pk)

    def test_bias_analysis_result_timestamps(self):
        """Test analyzed_at is set automatically"""
        content_type = ContentType.objects.get_for_model(InvitedInterview)

        result = BiasAnalysisResult.objects.create(
            content_type=content_type,
            object_id=self.invitation.pk
        )

        self.assertIsNotNone(result.analyzed_at)

    def test_bias_analysis_result_update_or_create(self):
        """Test update_or_create pattern for same object"""
        content_type = ContentType.objects.get_for_model(InvitedInterview)

        # Create initial result
        result1, created1 = BiasAnalysisResult.objects.update_or_create(
            content_type=content_type,
            object_id=self.invitation.pk,
            defaults={
                'severity_level': 'LOW',
                'total_flags': 1
            }
        )
        self.assertTrue(created1)
        self.assertEqual(result1.total_flags, 1)

        # Update same object
        result2, created2 = BiasAnalysisResult.objects.update_or_create(
            content_type=content_type,
            object_id=self.invitation.pk,
            defaults={
                'severity_level': 'MEDIUM',
                'total_flags': 3
            }
        )
        self.assertFalse(created2)
        self.assertEqual(result2.pk, result1.pk)  # Same object
        self.assertEqual(result2.total_flags, 3)  # Updated value
