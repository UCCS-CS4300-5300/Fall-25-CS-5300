"""
OpenAI Utility Functions

Centralized OpenAI client management with graceful degradation.
This module prevents circular imports between views.py and resume_parser.py.
"""

from openai import OpenAI
from django.conf import settings


# OpenAI client configuration with graceful degradation
MAX_TOKENS = 15000
_openai_client = None


def get_openai_client():
    """
    Initialize and return OpenAI client (singleton pattern).
    This prevents import-time errors when API key is not set.

    Returns:
        OpenAI: Initialized OpenAI client instance

    Raises:
        ValueError: If OPENAI_API_KEY is not set or client initialization fails
    """
    global _openai_client
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please configure it in your "
                ".env file or environment variables."
            )
        try:
            _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
    return _openai_client


def _ai_available():
    """
    Return True if the OpenAI client can be initialized and is usable.
    This checks without raising exceptions.

    Returns:
        bool: True if OpenAI client is available, False otherwise
    """
    try:
        get_openai_client()
        return True
    except (ValueError, Exception):
        return False
