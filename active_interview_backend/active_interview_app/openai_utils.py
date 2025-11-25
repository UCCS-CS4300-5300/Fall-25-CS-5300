"""
OpenAI Utility Functions

Centralized OpenAI client management with graceful degradation and tier-based fallback.
This module prevents circular imports between views.py and resume_parser.py.

Updated for:
- Issue #13: API key rotation from key pool
- Issue #14: Automatic fallback tier switching based on spending cap
"""

from openai import OpenAI
from django.conf import settings


# OpenAI client configuration with graceful degradation
MAX_TOKENS = 15000
_openai_client = None
_current_api_key = None


def get_api_key_from_pool(model_tier='premium'):
    """
    Get the active API key from the key pool for a specific tier.

    Falls back to settings.OPENAI_API_KEY or OPENAI_API_FALLBACK_KEY based on tier.

    Args:
        model_tier (str): Model tier ('premium', 'standard', 'fallback')

    Returns:
        str: Active API key

    Raises:
        ValueError: If no API key is available
    """
    try:
        # Import here to avoid circular imports
        from .api_key_rotation_models import APIKeyPool
        from django.db import connection

        # Check if database tables exist (important for tests and migrations)
        if not connection.introspection.table_names():
            # Database not ready, skip to fallback
            raise Exception("Database not ready")

        # Try to get active key from pool for this tier
        active_key = APIKeyPool.get_active_key(
            provider='openai',
            model_tier=model_tier
        )

        if active_key:
            # Increment usage counter
            active_key.increment_usage()
            return active_key.get_key()

    except Exception:
        # If key pool is not set up or fails, fall back to settings
        # This is normal during tests, migrations, or when pool is not configured
        pass

    # Fallback to environment variables based on tier
    if model_tier == 'fallback':
        # Use fallback key for fallback tier
        fallback_key = getattr(settings, 'OPENAI_API_FALLBACK_KEY', None)
        if fallback_key:
            return fallback_key

    # Use primary key for premium/standard tiers
    if settings.OPENAI_API_KEY:
        return settings.OPENAI_API_KEY

    raise ValueError(
        f"No OpenAI API key available for tier '{model_tier}'. Either:\n"
        "1. Add a key to the API Key Pool (recommended), or\n"
        "2. Set OPENAI_API_KEY in your .env file\n"
        "3. For fallback tier, set OPENAI_API_FALLBACK_KEY in your .env file"
    )


def get_openai_client(model_tier='premium', force_refresh=False):
    """
    Initialize and return OpenAI client for a specific model tier.
    This prevents import-time errors when API key is not set.

    Updated for Issue #13 to support key rotation and Issue #14 for tier-based fallback.
    Will use a new client if the active key has changed.

    Args:
        model_tier (str): Model tier ('premium', 'standard', 'fallback')
        force_refresh (bool): Force recreation of client even if one exists

    Returns:
        OpenAI: Initialized OpenAI client instance

    Raises:
        ValueError: If no API key is available or client initialization fails
    """
    global _openai_client, _current_api_key

    try:
        # Get current active key for this tier
        current_key = get_api_key_from_pool(model_tier=model_tier)

        # Check if we need to refresh the client
        # (key has changed or client doesn't exist)
        if force_refresh or _openai_client is None or _current_api_key != current_key:
            _openai_client = OpenAI(api_key=current_key)
            _current_api_key = current_key

        return _openai_client

    except Exception as e:
        raise ValueError(f"Failed to initialize OpenAI client for tier '{model_tier}': {e}")


def ai_available():
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


def get_current_api_key_info(model_tier='premium'):
    """
    Get information about the currently active API key for a specific tier.

    Args:
        model_tier (str): Model tier ('premium', 'standard', 'fallback')

    Returns:
        dict: Key information or None if no key available

    Useful for monitoring and debugging which key is being used.
    """
    try:
        from .api_key_rotation_models import APIKeyPool

        active_key = APIKeyPool.get_active_key(
            provider='openai',
            model_tier=model_tier
        )

        if active_key:
            return {
                'key_name': active_key.key_name,
                'masked_key': active_key.get_masked_key(),
                'model_tier': active_key.model_tier,
                'usage_count': active_key.usage_count,
                'last_used_at': active_key.last_used_at,
                'activated_at': active_key.activated_at,
                'source': 'key_pool'
            }

    except Exception:
        pass

    # Using environment variable fallback
    if model_tier == 'fallback':
        fallback_key = getattr(settings, 'OPENAI_API_FALLBACK_KEY', None)
        if fallback_key:
            masked = f"{fallback_key[:10]}...{fallback_key[-4:]}" if len(fallback_key) > 14 else "***"
            return {
                'key_name': 'Fallback Environment Variable',
                'masked_key': masked,
                'model_tier': 'fallback',
                'usage_count': None,
                'last_used_at': None,
                'activated_at': None,
                'source': 'environment_fallback'
            }

    if settings.OPENAI_API_KEY:
        key = settings.OPENAI_API_KEY
        masked = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
        return {
            'key_name': 'Primary Environment Variable',
            'masked_key': masked,
            'model_tier': model_tier,
            'usage_count': None,
            'last_used_at': None,
            'activated_at': None,
            'source': 'environment'
        }

    return None


def get_client_and_model(force_tier=None):
    """
    Get OpenAI client and model name with automatic tier selection.

    This is the recommended way to get a client for making API calls.
    It automatically:
    1. Checks spending cap status
    2. Selects appropriate tier (premium/standard/fallback)
    3. Gets the right API key for that tier
    4. Returns client and model name

    Args:
        force_tier (str): Force a specific tier (for testing/admin override)

    Returns:
        tuple: (client, model_name, tier_info)
            - client: OpenAI client instance
            - model_name: Model to use (e.g., 'gpt-4o', 'gpt-3.5-turbo')
            - tier_info: Dict with tier details and spending info

    Example:
        client, model, tier_info = get_client_and_model()
        response = client.chat.completions.create(
            model=model,
            messages=[...]
        )
    """
    from .model_tier_manager import get_active_tier, get_model_for_tier, get_tier_info

    # Get active tier based on spending cap
    active_tier = get_active_tier(force_tier=force_tier)

    # Get model name for this tier
    model_name = get_model_for_tier(tier=active_tier, provider='openai')

    # Get client with key for this tier
    client = get_openai_client(model_tier=active_tier)

    # Get full tier info for logging/monitoring
    tier_info = get_tier_info()

    return client, model_name, tier_info
