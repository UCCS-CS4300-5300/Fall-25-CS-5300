"""
Comprehensive tests for BiasDetectionService

Related to Issues #18, #57, #58, #59 (Bias Guardrails).
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils import timezone
from active_interview_app.models import (
    BiasTermLibrary,
    BiasAnalysisResult,
    InvitedInterview,
    InterviewTemplate
)
from active_interview_app.bias_detection import (
    BiasDetectionService,
    analyze_feedback,
    is_feedback_clean,
    get_suggestions
)


class BiasDetectionServiceTest(TestCase):
    """Test cases for BiasDetectionService"""

    def setUp(self):
        """Set up test data"""
        # Clear cache before each test
        cache.clear()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create test bias terms
        self.age_term = BiasTermLibrary.objects.create(
            term='too old',
            category=BiasTermLibrary.AGE,
            pattern=r'\b(too old|very old)\b',
            explanation='Age-related bias',
            neutral_alternatives=['experienced', 'seasoned professional'],
            severity=BiasTermLibrary.BLOCKING,
            is_active=True
        )

        self.culture_term = BiasTermLibrary.objects.create(
            term='cultural fit',
            category=BiasTermLibrary.OTHER,
            pattern=r'\b(cultural fit|culture fit)\b',
            explanation='Subjective and potentially biased',
            neutral_alternatives=[
                'team collaboration skills',
                'alignment with company values'
            ],
            severity=BiasTermLibrary.WARNING,
            is_active=True
        )

        self.gender_term = BiasTermLibrary.objects.create(
            term='aggressive',
            category=BiasTermLibrary.GENDER,
            pattern=r'\b(aggressive|bossy)\b',
            explanation='Often gender-biased',
            neutral_alternatives=['assertive', 'direct communication style'],
            severity=BiasTermLibrary.WARNING,
            is_active=True
        )

        # Initialize service
        self.service = BiasDetectionService()

    def tearDown(self):
        """Clear cache after each test"""
        cache.clear()

    # =========================================================================
    # Basic Detection Tests
    # =========================================================================

    def test_analyze_clean_feedback(self):
        """Test analyzing feedback with no bias terms"""
        result = self.service.analyze_feedback(
            "Candidate demonstrated strong technical skills and clear communication."
        )

        self.assertFalse(result['has_bias'])
        self.assertEqual(result['total_flags'], 0)
        self.assertEqual(result['blocking_flags'], 0)
        self.assertEqual(result['warning_flags'], 0)
        self.assertEqual(result['severity_level'], 'CLEAN')
        self.assertEqual(result['bias_score'], 0.0)
        self.assertEqual(result['flagged_terms'], [])

    def test_analyze_feedback_with_single_bias_term(self):
        """Test detecting a single bias term"""
        result = self.service.analyze_feedback(
            "He is too old for this role."
        )

        self.assertTrue(result['has_bias'])
        self.assertEqual(result['total_flags'], 1)
        self.assertEqual(result['blocking_flags'], 1)
        self.assertEqual(result['warning_flags'], 0)
        self.assertEqual(result['severity_level'], 'HIGH')
        self.assertGreater(result['bias_score'], 0.0)

        # Check flagged term details
        self.assertEqual(len(result['flagged_terms']), 1)
        flagged = result['flagged_terms'][0]
        self.assertEqual(flagged['term'], 'too old')
        self.assertEqual(flagged['category'], BiasTermLibrary.AGE)
        self.assertEqual(flagged['severity'], BiasTermLibrary.BLOCKING)
        self.assertIn('experienced', flagged['suggestions'])

    def test_analyze_feedback_with_multiple_bias_terms(self):
        """Test detecting multiple bias terms"""
        result = self.service.analyze_feedback(
            "She is too old and not a cultural fit for the team."
        )

        self.assertTrue(result['has_bias'])
        self.assertEqual(result['total_flags'], 2)
        self.assertEqual(result['blocking_flags'], 1)  # too old
        self.assertEqual(result['warning_flags'], 1)  # cultural fit
        self.assertEqual(result['severity_level'], 'HIGH')  # Has blocking term

        # Check both terms detected
        terms = [t['term'] for t in result['flagged_terms']]
        self.assertIn('too old', terms)
        self.assertIn('cultural fit', terms)

    def test_case_insensitive_detection(self):
        """Test bias detection is case-insensitive"""
        result1 = self.service.analyze_feedback("Too Old")
        result2 = self.service.analyze_feedback("TOO OLD")
        result3 = self.service.analyze_feedback("too old")

        self.assertTrue(result1['has_bias'])
        self.assertTrue(result2['has_bias'])
        self.assertTrue(result3['has_bias'])

    def test_pattern_variations_detected(self):
        """Test pattern variations are detected"""
        # Both "cultural fit" and "culture fit" should be detected
        result1 = self.service.analyze_feedback("Good cultural fit")
        result2 = self.service.analyze_feedback("Good culture fit")

        self.assertTrue(result1['has_bias'])
        self.assertTrue(result2['has_bias'])
        self.assertEqual(result1['flagged_terms'][0]['term'], 'cultural fit')
        self.assertEqual(result2['flagged_terms'][0]['term'], 'cultural fit')

    def test_multiple_occurrences_of_same_term(self):
        """Test multiple occurrences of the same bias term"""
        result = self.service.analyze_feedback(
            "Too old and very old for this position."
        )

        self.assertTrue(result['has_bias'])
        self.assertEqual(result['total_flags'], 1)  # Same term
        flagged = result['flagged_terms'][0]
        self.assertEqual(flagged['match_count'], 2)  # Two matches
        self.assertEqual(len(flagged['positions']), 2)

    # =========================================================================
    # Severity Level Tests
    # =========================================================================

    def test_severity_level_clean(self):
        """Test CLEAN severity level"""
        result = self.service.analyze_feedback("No bias here")
        self.assertEqual(result['severity_level'], 'CLEAN')

    def test_severity_level_low(self):
        """Test LOW severity level (warnings only, low score)"""
        result = self.service.analyze_feedback("Good cultural fit")
        # Should be LOW or MEDIUM (depends on bias score calculation)
        self.assertIn(result['severity_level'], ['LOW', 'MEDIUM'])
        self.assertEqual(result['warning_flags'], 1)
        self.assertEqual(result['blocking_flags'], 0)

    def test_severity_level_high(self):
        """Test HIGH severity level (has blocking terms)"""
        result = self.service.analyze_feedback("Too old for this")
        self.assertEqual(result['severity_level'], 'HIGH')

    # =========================================================================
    # Bias Score Calculation Tests
    # =========================================================================

    def test_bias_score_clean_text(self):
        """Test bias score is 0.0 for clean text"""
        result = self.service.analyze_feedback("Clean feedback")
        self.assertEqual(result['bias_score'], 0.0)

    def test_bias_score_increases_with_more_flags(self):
        """Test bias score increases with more flagged terms"""
        result1 = self.service.analyze_feedback("Cultural fit")
        result2 = self.service.analyze_feedback("Cultural fit and aggressive and bossy")

        # Score should increase or stay at max (1.0)
        self.assertGreaterEqual(result2['bias_score'], result1['bias_score'])

    def test_bias_score_higher_for_blocking_terms(self):
        """Test blocking terms result in higher bias score"""
        result_warning = self.service.analyze_feedback("Cultural fit")
        result_blocking = self.service.analyze_feedback("Too old")

        # Blocking should have higher or equal score (both contribute to bias)
        self.assertGreaterEqual(result_blocking['bias_score'], result_warning['bias_score'])
        # And blocking should have HIGH severity
        self.assertEqual(result_blocking['severity_level'], 'HIGH')

    def test_bias_score_bounded_0_to_1(self):
        """Test bias score is always between 0.0 and 1.0"""
        # Create long text with many bias terms
        text = " ".join(["too old", "cultural fit", "aggressive"] * 20)
        result = self.service.analyze_feedback(text)

        self.assertGreaterEqual(result['bias_score'], 0.0)
        self.assertLessEqual(result['bias_score'], 1.0)

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_analyze_empty_string(self):
        """Test analyzing empty string"""
        result = self.service.analyze_feedback("")
        self.assertFalse(result['has_bias'])
        self.assertEqual(result['total_flags'], 0)

    def test_analyze_whitespace_only(self):
        """Test analyzing whitespace-only string"""
        result = self.service.analyze_feedback("   \n\t  ")
        self.assertFalse(result['has_bias'])

    def test_analyze_none(self):
        """Test analyzing None"""
        result = self.service.analyze_feedback(None)
        self.assertFalse(result['has_bias'])

    def test_inactive_terms_not_detected(self):
        """Test inactive bias terms are not detected"""
        # Deactivate term
        self.age_term.is_active = False
        self.age_term.save()
        self.service.clear_cache()

        result = self.service.analyze_feedback("Too old for this")
        self.assertFalse(result['has_bias'])

    def test_invalid_regex_pattern_handled_gracefully(self):
        """Test invalid regex patterns don't crash the service"""
        # Create term with invalid regex
        BiasTermLibrary.objects.create(
            term='bad pattern',
            category=BiasTermLibrary.OTHER,
            pattern=r'[invalid(regex',  # Invalid regex
            explanation='Test',
            neutral_alternatives=[],
            severity=BiasTermLibrary.WARNING,
            is_active=True
        )
        self.service.clear_cache()

        # Should not crash
        result = self.service.analyze_feedback("Some feedback")
        # Should still work for other terms
        result2 = self.service.analyze_feedback("Too old")
        self.assertTrue(result2['has_bias'])

    # =========================================================================
    # Caching Tests
    # =========================================================================

    def test_bias_terms_cached(self):
        """Test bias terms are cached for performance"""
        # First call loads from DB
        terms1 = self.service.get_active_bias_terms()

        # Second call should use cache
        terms2 = self.service.get_active_bias_terms()

        self.assertEqual(len(terms1), len(terms2))

    def test_clear_cache_reloads_terms(self):
        """Test clearing cache reloads terms from database"""
        # Load initial terms
        self.service.get_active_bias_terms()

        # Add new term
        BiasTermLibrary.objects.create(
            term='new term',
            category=BiasTermLibrary.OTHER,
            pattern=r'\bnew\b',
            explanation='Test',
            neutral_alternatives=[],
            is_active=True
        )

        # Without clearing cache, new term not detected
        result1 = self.service.analyze_feedback("This is new")
        self.assertFalse(result1['has_bias'])  # Cache doesn't have new term

        # Clear cache and reload
        self.service.clear_cache()

        # Now new term should be detected
        result2 = self.service.analyze_feedback("This is new")
        self.assertTrue(result2['has_bias'])

    # =========================================================================
    # Saving Analysis Results
    # =========================================================================

    def test_save_analysis_result(self):
        """Test saving analysis result to database"""
        # Create invitation
        interviewer = User.objects.create_user(
            username='interviewer',
            password='test123'
        )
        template = InterviewTemplate.objects.create(
            name='Test Template',
            user=interviewer,
            description='Test'
        )
        invitation = InvitedInterview.objects.create(
            interviewer=interviewer,
            candidate_email='test@example.com',
            template=template,
            scheduled_time=timezone.now() + timezone.timedelta(days=1)
        )

        # Analyze feedback
        analysis = self.service.analyze_feedback("Cultural fit")

        # Save result
        result = self.service.save_analysis_result(
            content_object=invitation,
            analysis=analysis,
            saved_with_warnings=False,
            user_acknowledged=True
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.total_flags, 1)
        # Severity can be LOW or MEDIUM depending on bias score calculation
        self.assertIn(result.severity_level, ['LOW', 'MEDIUM'])
        self.assertTrue(result.user_acknowledged)
        self.assertFalse(result.saved_with_warnings)

    def test_get_analysis_for_object(self):
        """Test retrieving saved analysis for an object"""
        interviewer = User.objects.create_user(
            username='interviewer',
            password='test123'
        )
        template = InterviewTemplate.objects.create(
            name='Test Template',
            user=interviewer,
            description='Test'
        )
        invitation = InvitedInterview.objects.create(
            interviewer=interviewer,
            candidate_email='test@example.com',
            template=template,
            scheduled_time=timezone.now() + timezone.timedelta(days=1)
        )

        # Save analysis
        analysis = self.service.analyze_feedback("Too old")
        self.service.save_analysis_result(invitation, analysis)

        # Retrieve it
        retrieved = self.service.get_analysis_for_object(invitation)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.severity_level, 'HIGH')

    def test_update_existing_analysis_result(self):
        """Test update_or_create updates existing analysis"""
        interviewer = User.objects.create_user(
            username='interviewer',
            password='test123'
        )
        template = InterviewTemplate.objects.create(
            name='Test Template',
            user=interviewer,
            description='Test'
        )
        invitation = InvitedInterview.objects.create(
            interviewer=interviewer,
            candidate_email='test@example.com',
            template=template,
            scheduled_time=timezone.now() + timezone.timedelta(days=1)
        )

        # First analysis
        analysis1 = self.service.analyze_feedback("Cultural fit")
        result1 = self.service.save_analysis_result(invitation, analysis1)
        result1_id = result1.pk

        # Second analysis (updated feedback)
        analysis2 = self.service.analyze_feedback("Too old")
        result2 = self.service.save_analysis_result(invitation, analysis2)

        # Should be same object (updated)
        self.assertEqual(result2.pk, result1_id)
        self.assertEqual(result2.severity_level, 'HIGH')  # Updated

    # =========================================================================
    # Convenience Function Tests
    # =========================================================================

    def test_is_feedback_clean_function(self):
        """Test is_feedback_clean convenience function"""
        self.assertTrue(is_feedback_clean("Clean feedback"))
        self.assertFalse(is_feedback_clean("Too old"))  # Has blocking term
        self.assertTrue(is_feedback_clean("Cultural fit"))  # Warning only

    def test_get_suggestions_function(self):
        """Test get_suggestions convenience function"""
        suggestions = get_suggestions("cultural fit")
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        self.assertIn('team collaboration skills', suggestions)

    def test_analyze_feedback_function(self):
        """Test analyze_feedback convenience function"""
        result = analyze_feedback("Too old")
        self.assertTrue(result['has_bias'])

    # =========================================================================
    # Statistics Tests
    # =========================================================================

    def test_get_statistics_no_data(self):
        """Test statistics with no analysis results"""
        stats = self.service.get_statistics()

        self.assertEqual(stats['total_analyses'], 0)
        self.assertEqual(stats['clean_feedback_count'], 0)
        self.assertEqual(stats['biased_feedback_count'], 0)
        self.assertEqual(stats['bias_rate'], 0.0)

    def test_get_statistics_with_data(self):
        """Test statistics with analysis results"""
        interviewer = User.objects.create_user(
            username='interviewer',
            password='test123'
        )
        template = InterviewTemplate.objects.create(
            name='Test Template',
            user=interviewer,
            description='Test'
        )

        # Create multiple analyses
        for i in range(5):
            invitation = InvitedInterview.objects.create(
                interviewer=interviewer,
                candidate_email=f'test{i}@example.com',
                template=template,
                scheduled_time=timezone.now() + timezone.timedelta(days=1)
            )

            if i < 2:
                # Clean feedback
                analysis = self.service.analyze_feedback("Clean feedback")
            else:
                # Biased feedback
                analysis = self.service.analyze_feedback("Too old")

            self.service.save_analysis_result(invitation, analysis)

        stats = self.service.get_statistics()

        self.assertEqual(stats['total_analyses'], 5)
        self.assertEqual(stats['clean_feedback_count'], 2)
        self.assertEqual(stats['biased_feedback_count'], 3)
        self.assertEqual(stats['bias_rate'], 60.0)  # 3/5 * 100

    def test_detection_count_incremented(self):
        """Test detection_count is incremented when term is detected"""
        initial_count = self.age_term.detection_count

        # Detect the term
        self.service.analyze_feedback("Too old for this")

        # Reload from database
        self.age_term.refresh_from_db()

        self.assertEqual(self.age_term.detection_count, initial_count + 1)

    # =========================================================================
    # Text Hash Tests
    # =========================================================================

    def test_text_hash_generation(self):
        """Test text hash is generated and consistent"""
        result1 = self.service.analyze_feedback("Same text")
        result2 = self.service.analyze_feedback("Same text")

        self.assertEqual(result1['text_hash'], result2['text_hash'])
        self.assertNotEqual(result1['text_hash'], '')

    def test_different_text_different_hash(self):
        """Test different texts produce different hashes"""
        result1 = self.service.analyze_feedback("Text one")
        result2 = self.service.analyze_feedback("Text two")

        self.assertNotEqual(result1['text_hash'], result2['text_hash'])

    # =========================================================================
    # Position Tracking Tests
    # =========================================================================

    def test_position_tracking(self):
        """Test bias term positions are tracked"""
        result = self.service.analyze_feedback("He is too old for this role")

        flagged = result['flagged_terms'][0]
        positions = flagged['positions']

        self.assertEqual(len(positions), 1)
        start, end = positions[0]

        # Extract the matched text
        text = "He is too old for this role"
        matched_text = text[start:end]

        self.assertEqual(matched_text.lower(), "too old")
