"""
Utility functions for tracking token usage from Claude and ChatGPT API calls.
"""
import subprocess
from django.conf import settings


def get_current_git_branch():
    """
    Get the current git branch name.
    Returns 'unknown' if not in a git repository or if detection fails.
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return 'unknown'


def record_token_usage(user, endpoint, model_name, response):
    """
    Record token usage from an OpenAI or Claude API response.

    Args:
        user: Django User object (or None for anonymous)
        endpoint: String identifying the API endpoint/view (e.g., 'create_chat', 'chat_view')
        model_name: Model identifier (e.g., 'gpt-4o', 'claude-sonnet-4-5-20250929')
        response: API response object containing usage information

    The response object should have a .usage attribute with:
        - prompt_tokens (int)
        - completion_tokens (int)
        - total_tokens (int, optional - will be calculated if not present)
    """
    from .token_usage_models import TokenUsage

    # Skip if token tracking is disabled
    if getattr(settings, 'DISABLE_TOKEN_TRACKING', False):
        return

    # Get git branch
    git_branch = get_current_git_branch()

    # Extract token counts from response
    try:
        usage = response.usage
        prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
        completion_tokens = getattr(usage, 'completion_tokens', 0) or 0

        # Create token usage record
        TokenUsage.objects.create(
            user=user,
            git_branch=git_branch,
            model_name=model_name,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
    except AttributeError as e:
        # Log error but don't break the application
        print(f"Warning: Failed to record token usage: {e}")
    except Exception as e:
        # Catch any other errors to prevent breaking the API call
        print(f"Error recording token usage: {e}")


def record_claude_usage(user, endpoint, response):
    """
    Convenience wrapper for recording Claude API usage.
    Automatically extracts model name from response if available.
    """
    model_name = getattr(response, 'model', 'claude-unknown')
    record_token_usage(user, endpoint, model_name, response)


def record_openai_usage(user, endpoint, response):
    """
    Convenience wrapper for recording OpenAI API usage.
    Automatically extracts model name from response if available.
    """
    model_name = getattr(response, 'model', 'gpt-unknown')
    record_token_usage(user, endpoint, model_name, response)
