"""
Bias Detection Service for Interview Feedback

This module provides bias detection functionality for interview feedback text.
It uses pattern matching against a curated library of bias terms to identify
potentially discriminatory language and suggest neutral alternatives.

Related to Issues #18, #57, #58, #59 (Bias Guardrails).

Usage:
    from active_interview_app.bias_detection import BiasDetectionService

    service = BiasDetectionService()
    result = service.analyze_feedback("He is a cultural fit for the team")

    if result['has_bias']:
        print(f"Detected {result['total_flags']} bias flags")
        for flag in result['flagged_terms']:
            print(f"  - {flag['matched_text']}: {flag['explanation']}")
"""

import re
import hashlib
from typing import Dict, List, Optional, Tuple
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.contrib.contenttypes.models import ContentType

from .models import BiasTermLibrary, BiasAnalysisResult


class BiasDetectionService:
    """
    Service class for detecting bias in interview feedback text.

    This service:
    - Loads active bias terms from the database
    - Applies pattern matching to detect bias terms
    - Calculates bias scores and severity levels
    - Provides neutral alternative suggestions
    - Stores analysis results for auditing
    """

    # Cache configuration
    CACHE_KEY_BIAS_TERMS = 'bias_detection:active_terms'
    CACHE_TIMEOUT = 3600  # 1 hour

    # Bias score calculation weights
    # These constants define how different factors contribute to the overall bias score
    SCORE_WEIGHT_UNIQUE_TERMS = 0.2  # Each unique bias term found
    SCORE_WEIGHT_SEVERITY = 0.1       # Weighted severity of all matches
    SCORE_WEIGHT_DENSITY = 0.05       # Density of bias terms (matches per 100 words)

    def __init__(self):
        """Initialize the bias detection service."""
        self._bias_terms_cache = None

    def get_active_bias_terms(self) -> List[BiasTermLibrary]:
        """
        Get all active bias terms from database with caching.

        Returns:
            List of active BiasTermLibrary objects
        """
        # Try cache first
        cached_terms = cache.get(self.CACHE_KEY_BIAS_TERMS)
        if cached_terms is not None:
            return cached_terms

        # Load from database
        terms = list(
            BiasTermLibrary.objects.filter(is_active=True)
            .select_related('created_by')
            .order_by('severity', 'category')
        )

        # Cache for future requests
        cache.set(self.CACHE_KEY_BIAS_TERMS, terms, self.CACHE_TIMEOUT)

        return terms

    def clear_cache(self):
        """Clear the bias terms cache (call when terms are updated)."""
        cache.delete(self.CACHE_KEY_BIAS_TERMS)
        self._bias_terms_cache = None

    def analyze_feedback(
        self,
        feedback_text: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze feedback text for bias indicators.

        Args:
            feedback_text: The feedback text to analyze
            context: Optional context dict (e.g., {'candidate_name': 'John'})

        Returns:
            Dictionary with analysis results:
            {
                'has_bias': bool,
                'total_flags': int,
                'blocking_flags': int,
                'warning_flags': int,
                'severity_level': str,  # 'CLEAN', 'LOW', 'MEDIUM', 'HIGH'
                'bias_score': float,  # 0.0 - 1.0
                'flagged_terms': [
                    {
                        'matched_text': str,
                        'term_id': int,
                        'term': str,
                        'category': str,
                        'severity': int,
                        'explanation': str,
                        'suggestions': [str],
                        'positions': [(start, end)],
                        'pattern': str
                    },
                    ...
                ],
                'text_hash': str
            }
        """
        if not feedback_text or not feedback_text.strip():
            return self._empty_result()

        # Get active bias terms
        bias_terms = self.get_active_bias_terms()

        # Detect bias terms
        flagged_terms = []
        for term in bias_terms:
            matches = self._find_pattern_matches(feedback_text, term)
            if matches:
                flagged_terms.append({
                    'matched_text': matches[0]['text'],  # First match text
                    'term_id': term.id,
                    'term': term.term,
                    'category': term.category,
                    'category_display': term.get_category_display(),
                    'severity': term.severity,
                    'severity_display': term.get_severity_display(),
                    'explanation': term.explanation,
                    'suggestions': term.neutral_alternatives,
                    'positions': [(m['start'], m['end']) for m in matches],
                    'pattern': term.pattern,
                    'match_count': len(matches)
                })

                # Update detection count (async to avoid blocking)
                self._increment_detection_count(term.id)

        # Calculate metrics
        total_flags = len(flagged_terms)
        blocking_flags = sum(
            1 for t in flagged_terms
            if t['severity'] == BiasTermLibrary.BLOCKING
        )
        warning_flags = sum(
            1 for t in flagged_terms
            if t['severity'] == BiasTermLibrary.WARNING
        )

        # Calculate bias score (0.0 - 1.0)
        bias_score = self._calculate_bias_score(flagged_terms, feedback_text)

        # Determine severity level
        severity_level = self._determine_severity_level(
            blocking_flags, warning_flags, bias_score
        )

        # Generate text hash for deduplication
        text_hash = self._hash_text(feedback_text)

        return {
            'has_bias': total_flags > 0,
            'total_flags': total_flags,
            'blocking_flags': blocking_flags,
            'warning_flags': warning_flags,
            'severity_level': severity_level,
            'bias_score': bias_score,
            'flagged_terms': flagged_terms,
            'text_hash': text_hash
        }

    def _find_pattern_matches(
        self,
        text: str,
        term: BiasTermLibrary
    ) -> List[Dict]:
        """
        Find all matches of a bias term pattern in text.

        Args:
            text: Text to search
            term: BiasTermLibrary object with pattern

        Returns:
            List of match dictionaries with 'text', 'start', 'end'
        """
        try:
            # Compile pattern with case-insensitive flag
            pattern = re.compile(term.pattern, re.IGNORECASE)

            matches = []
            for match in pattern.finditer(text):
                matches.append({
                    'text': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })

            return matches

        except re.error as e:
            # Log pattern error but don't crash
            print(f"Invalid regex pattern for term '{term.term}': {e}")
            return []

    def _calculate_bias_score(
        self,
        flagged_terms: List[Dict],
        feedback_text: str
    ) -> float:
        """
        Calculate overall bias score (0.0 - 1.0).

        Formula considers:
        - Number of flags
        - Severity of flags
        - Flag density (flags per word)

        Args:
            flagged_terms: List of flagged term dicts
            feedback_text: Original feedback text

        Returns:
            Float between 0.0 (clean) and 1.0 (highly biased)
        """
        if not flagged_terms:
            return 0.0

        # Count words (rough estimate)
        word_count = len(feedback_text.split())
        if word_count == 0:
            return 0.0

        # Calculate weighted severity sum
        severity_sum = sum(
            t['severity'] * t['match_count']
            for t in flagged_terms
        )

        # Calculate density (flags per 100 words)
        total_matches = sum(t['match_count'] for t in flagged_terms)
        density = (total_matches / word_count) * 100

        # Normalize to 0-1 scale
        # - More flags = higher score
        # - Higher severity = higher score
        # - Higher density = higher score
        score = min(1.0, (
            (len(flagged_terms) * self.SCORE_WEIGHT_UNIQUE_TERMS) +
            (severity_sum * self.SCORE_WEIGHT_SEVERITY) +
            (density * self.SCORE_WEIGHT_DENSITY)
        ))

        return round(score, 3)

    def _determine_severity_level(
        self,
        blocking_flags: int,
        warning_flags: int,
        bias_score: float
    ) -> str:
        """
        Determine overall severity level based on flags and score.

        Args:
            blocking_flags: Number of blocking-severity flags
            warning_flags: Number of warning-severity flags
            bias_score: Calculated bias score (0.0-1.0)

        Returns:
            Severity level: 'CLEAN', 'LOW', 'MEDIUM', 'HIGH'
        """
        if blocking_flags > 0:
            return 'HIGH'

        if warning_flags == 0:
            return 'CLEAN'

        if bias_score >= 0.5:
            return 'MEDIUM'

        return 'LOW'

    def _hash_text(self, text: str) -> str:
        """Generate SHA256 hash of text for deduplication."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _empty_result(self) -> Dict:
        """Return empty analysis result for blank text."""
        return {
            'has_bias': False,
            'total_flags': 0,
            'blocking_flags': 0,
            'warning_flags': 0,
            'severity_level': 'CLEAN',
            'bias_score': 0.0,
            'flagged_terms': [],
            'text_hash': ''
        }

    def _increment_detection_count(self, term_id: int):
        """
        Increment detection count for a bias term (non-blocking).

        Args:
            term_id: ID of BiasTermLibrary object
        """
        try:
            BiasTermLibrary.objects.filter(id=term_id).update(
                detection_count=F('detection_count') + 1
            )
        except Exception:
            # Don't fail analysis if count update fails
            pass

    @transaction.atomic
    def save_analysis_result(
        self,
        content_object,
        analysis: Dict,
        saved_with_warnings: bool = False,
        user_acknowledged: bool = False
    ) -> BiasAnalysisResult:
        """
        Save bias analysis result to database.

        Args:
            content_object: The object being analyzed (InvitedInterview or ExportableReport)
            analysis: Analysis result dict from analyze_feedback()
            saved_with_warnings: Whether user saved despite warnings
            user_acknowledged: Whether user acknowledged warnings

        Returns:
            BiasAnalysisResult object
        """
        content_type = ContentType.objects.get_for_model(content_object)

        # Create or update analysis result
        result, created = BiasAnalysisResult.objects.update_or_create(
            content_type=content_type,
            object_id=content_object.pk,
            defaults={
                'flagged_terms': analysis['flagged_terms'],
                'bias_score': analysis['bias_score'],
                'severity_level': analysis['severity_level'],
                'total_flags': analysis['total_flags'],
                'blocking_flags': analysis['blocking_flags'],
                'warning_flags': analysis['warning_flags'],
                'saved_with_warnings': saved_with_warnings,
                'user_acknowledged': user_acknowledged,
                'feedback_text_hash': analysis['text_hash']
            }
        )

        return result

    def get_analysis_for_object(self, content_object) -> Optional[BiasAnalysisResult]:
        """
        Get saved bias analysis for an object.

        Args:
            content_object: The object to get analysis for

        Returns:
            BiasAnalysisResult or None
        """
        content_type = ContentType.objects.get_for_model(content_object)

        try:
            return BiasAnalysisResult.objects.get(
                content_type=content_type,
                object_id=content_object.pk
            )
        except BiasAnalysisResult.DoesNotExist:
            return None

    def is_feedback_clean(self, feedback_text: str) -> bool:
        """
        Quick check if feedback is clean (no blocking flags).

        Args:
            feedback_text: Feedback text to check

        Returns:
            True if no blocking flags, False otherwise
        """
        analysis = self.analyze_feedback(feedback_text)
        return analysis['blocking_flags'] == 0

    def get_suggestions_for_term(
        self,
        term_text: str,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Get neutral alternative suggestions for a specific term.

        Args:
            term_text: The flagged term text
            context: Optional surrounding context for better suggestions

        Returns:
            List of neutral alternative phrases
        """
        # Find matching term in library
        bias_terms = self.get_active_bias_terms()

        for term in bias_terms:
            if re.search(term.pattern, term_text, re.IGNORECASE):
                return term.neutral_alternatives

        # No specific suggestions found
        return []

    def get_statistics(self) -> Dict:
        """
        Get bias detection statistics across all feedback.

        Returns:
            Dictionary with statistics:
            {
                'total_analyses': int,
                'clean_feedback_count': int,
                'biased_feedback_count': int,
                'bias_rate': float,
                'avg_bias_score': float,
                'category_breakdown': {...},
                'most_detected_terms': [...]
            }
        """
        from django.db.models import Count, Avg

        total_analyses = BiasAnalysisResult.objects.count()
        clean_count = BiasAnalysisResult.objects.filter(
            severity_level='CLEAN'
        ).count()
        biased_count = total_analyses - clean_count

        avg_bias_score = BiasAnalysisResult.objects.aggregate(
            avg=Avg('bias_score')
        )['avg'] or 0.0

        # Category breakdown
        category_counts = {}
        for term in BiasTermLibrary.objects.filter(is_active=True):
            category = term.get_category_display()
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += term.detection_count

        # Most detected terms
        most_detected = list(
            BiasTermLibrary.objects.filter(is_active=True)
            .order_by('-detection_count')[:10]
            .values('term', 'category', 'detection_count')
        )

        return {
            'total_analyses': total_analyses,
            'clean_feedback_count': clean_count,
            'biased_feedback_count': biased_count,
            'bias_rate': (biased_count / total_analyses * 100) if total_analyses > 0 else 0.0,
            'avg_bias_score': round(avg_bias_score, 3),
            'category_breakdown': category_counts,
            'most_detected_terms': most_detected
        }


# Singleton instance for easy import
bias_detection_service = BiasDetectionService()


# Convenience functions
def analyze_feedback(feedback_text: str, context: Optional[Dict] = None) -> Dict:
    """Convenience function to analyze feedback."""
    return bias_detection_service.analyze_feedback(feedback_text, context)


def is_feedback_clean(feedback_text: str) -> bool:
    """Convenience function to check if feedback is clean."""
    return bias_detection_service.is_feedback_clean(feedback_text)


def get_suggestions(term_text: str, context: Optional[str] = None) -> List[str]:
    """Convenience function to get suggestions for a term."""
    return bias_detection_service.get_suggestions_for_term(term_text, context)
