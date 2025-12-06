"""
Utility functions for tracking interview response latency.
Supports the latency budget feature (Issues #20, #54).
"""
import time
import logging
from django.conf import settings
from .observability_models import InterviewResponseLatency, ErrorLog

logger = logging.getLogger(__name__)

# Default latency threshold in milliseconds (2 seconds)
DEFAULT_LATENCY_THRESHOLD_MS = 2000


def get_latency_threshold():
    """
    Get the configured latency threshold from settings.

    Returns:
        int: Latency threshold in milliseconds
    """
    return getattr(settings, 'INTERVIEW_LATENCY_THRESHOLD_MS', DEFAULT_LATENCY_THRESHOLD_MS)


def track_interview_response_latency(
    chat,
    response_time_ms,
    ai_processing_time_ms=None,
    question_number=None
):
    """
    Track and log interview response latency.

    Args:
        chat: Chat instance for the interview session
        response_time_ms: Total response time in milliseconds
        ai_processing_time_ms: OpenAI API call duration (optional)
        question_number: Question sequence number (optional, auto-calculated if None)

    Returns:
        InterviewResponseLatency: Created latency record
    """
    threshold_ms = get_latency_threshold()

    # Calculate question number if not provided
    if question_number is None:
        # Count existing latency records for this chat + 1
        question_number = InterviewResponseLatency.objects.filter(chat=chat).count() + 1

    # Determine if threshold was exceeded
    exceeded_threshold = response_time_ms > threshold_ms

    # Create latency record
    latency_record = InterviewResponseLatency.objects.create(
        chat=chat,
        user=chat.owner,
        response_time_ms=response_time_ms,
        ai_processing_time_ms=ai_processing_time_ms,
        question_number=question_number,
        interview_type=chat.interview_type,
        exceeded_threshold=exceeded_threshold,
        threshold_ms=threshold_ms
    )

    # Log if threshold was exceeded
    if exceeded_threshold:
        logger.warning(
            f"Latency budget exceeded: {response_time_ms:.0f}ms > {threshold_ms}ms "
            f"(Chat #{chat.id}, Q{question_number}, User: {chat.owner.username})"
        )

        # Trigger alert for severe latency issues (>5 seconds)
        if response_time_ms > 5000:
            trigger_latency_alert(latency_record)

    return latency_record


def trigger_latency_alert(latency_record):
    """
    Trigger an alert for severe latency violations.

    Args:
        latency_record: InterviewResponseLatency instance
    """
    logger.error(
        f"SEVERE LATENCY VIOLATION: {latency_record.response_time_ms:.0f}ms "
        f"(Chat #{latency_record.chat_id}, Q{latency_record.question_number}, "
        f"User: {latency_record.user.username if latency_record.user else 'Unknown'})"
    )

    # Create error log entry for severe cases
    try:
        ErrorLog.objects.create(
            endpoint=f'/chat/{latency_record.chat_id}/',
            method='POST',
            status_code=200,  # Not an error response, but slow
            error_type='LatencyViolation',
            error_message=f'Severe latency violation: {latency_record.response_time_ms:.0f}ms',
            user_id=latency_record.user_id,
            request_data={
                'chat_id': latency_record.chat_id,
                'question_number': latency_record.question_number,
                'response_time_ms': latency_record.response_time_ms,
                'ai_processing_time_ms': latency_record.ai_processing_time_ms,
                'threshold_ms': latency_record.threshold_ms,
                'interview_type': latency_record.interview_type
            }
        )
    except Exception as e:
        logger.error(f"Failed to create ErrorLog for latency violation: {e}")


class LatencyTracker:
    """
    Context manager for tracking interview response latency.

    Usage:
        with LatencyTracker(chat, question_number=1) as tracker:
            # Code to measure
            with tracker.track_ai_processing():
                response = openai_client.chat.completions.create(...)

        # Latency is automatically recorded when exiting context
    """

    def __init__(self, chat, question_number=None):
        """
        Initialize latency tracker.

        Args:
            chat: Chat instance for the interview session
            question_number: Question sequence number (optional)
        """
        self.chat = chat
        self.question_number = question_number
        self.start_time = None
        self.ai_start_time = None
        self.ai_processing_time_ms = None
        self.response_time_ms = None
        self.latency_record = None

    def __enter__(self):
        """Start tracking total response time."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop tracking and record latency.

        Returns:
            False: Allow exceptions to propagate
        """
        if self.start_time is not None:
            end_time = time.perf_counter()
            self.response_time_ms = (end_time - self.start_time) * 1000

            # Only record latency if chat is saved (has an ID)
            if self.chat.id is not None:
                # Record latency
                self.latency_record = track_interview_response_latency(
                    chat=self.chat,
                    response_time_ms=self.response_time_ms,
                    ai_processing_time_ms=self.ai_processing_time_ms,
                    question_number=self.question_number
                )
            else:
                logger.debug(
                    f"Skipping latency tracking for unsaved chat (response_time: "
                    f"{self.response_time_ms:.0f}ms)"
                )

        # Don't suppress exceptions
        return False

    def track_ai_processing(self):
        """
        Context manager for tracking AI processing time specifically.

        Returns:
            AIProcessingTracker: Context manager for AI processing
        """
        return AIProcessingTracker(self)


class AIProcessingTracker:
    """Context manager for tracking AI API call duration."""

    def __init__(self, latency_tracker):
        """
        Initialize AI processing tracker.

        Args:
            latency_tracker: Parent LatencyTracker instance
        """
        self.latency_tracker = latency_tracker
        self.ai_start_time = None

    def __enter__(self):
        """Start tracking AI processing time."""
        self.ai_start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop tracking AI processing time."""
        if self.ai_start_time is not None:
            ai_end_time = time.perf_counter()
            self.latency_tracker.ai_processing_time_ms = (
                (ai_end_time - self.ai_start_time) * 1000
            )

        # Don't suppress exceptions
        return False


def check_session_compliance(chat):
    """
    Check if an interview session meets the latency budget compliance rate.

    Args:
        chat: Chat instance to check

    Returns:
        dict: Session compliance statistics
    """
    stats = InterviewResponseLatency.get_session_stats(chat.id)

    if stats['total_responses'] == 0:
        return {
            **stats,
            'meets_target': None,  # No data yet
            'message': 'No latency data available for this session'
        }

    meets_target = stats['budget_compliance_rate'] >= 90.0

    message = (
        f"Session latency: {stats['budget_compliance_rate']:.1f}% within budget "
        f"({stats['within_budget']}/{stats['total_responses']} responses). "
        f"Target: 90%. Status: {'✓ PASS' if meets_target else '✗ FAIL'}"
    )

    return {
        **stats,
        'meets_target': meets_target,
        'message': message
    }


def get_global_compliance_stats(interview_type=None, hours=24):
    """
    Get latency compliance statistics across all interviews.

    Args:
        interview_type: Filter by interview type (PRACTICE or INVITED)
        hours: Time window in hours (default: 24)

    Returns:
        dict: Global compliance statistics
    """
    from django.utils import timezone
    from datetime import timedelta

    end_time = timezone.now()
    start_time = end_time - timedelta(hours=hours)

    compliance = InterviewResponseLatency.calculate_compliance_rate(
        interview_type=interview_type,
        start_time=start_time,
        end_time=end_time
    )

    percentiles = InterviewResponseLatency.calculate_percentiles(
        interview_type=interview_type,
        start_time=start_time,
        end_time=end_time
    )

    return {
        **compliance,
        **percentiles,
        'time_window_hours': hours,
        'interview_type': interview_type or 'ALL'
    }
