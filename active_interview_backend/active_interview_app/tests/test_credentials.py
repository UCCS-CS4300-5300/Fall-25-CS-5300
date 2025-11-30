"""
Centralized test credentials configuration.

This module provides a single source of truth for test credentials used across
all test files. This approach:
1. Avoids hardcoded passwords scattered throughout test files
2. Makes it easier to update test credentials in one place
3. Reduces security scanner false positives
4. Clearly marks test-only credentials

SECURITY NOTE: These are test-only credentials for local development and CI/CD.
They should NEVER be used in production environments.
"""

# nosec B105 - These are test-only credentials, not production secrets
TEST_PASSWORD = "testpass123"  # nosec B105

# Alternative test passwords for different test scenarios
# nosec B105 - Test credentials only
ALTERNATIVE_PASSWORD = "testpass"  # nosec B105
SIMPLE_PASSWORD = "pass"  # nosec B105

# Test user credentials dictionary for easy access
# nosec B105 - Test credentials only
TEST_USERS = {
    'default': {
        'username': 'testuser',
        'password': TEST_PASSWORD,
        'email': 'test@example.com'
    },
    'admin': {
        'username': 'adminuser',
        'password': TEST_PASSWORD,
        'email': 'admin@example.com'
    },
    'interviewer': {
        'username': 'interviewer',
        'password': TEST_PASSWORD,
        'email': 'interviewer@example.com'
    },
    'candidate': {
        'username': 'candidate',
        'password': TEST_PASSWORD,
        'email': 'candidate@example.com'
    }
}


def get_test_password(password_type='default'):
    """
    Get a test password by type.

    Args:
        password_type: One of 'default', 'alternative', 'simple'

    Returns:
        Test password string
    """
    passwords = {
        'default': TEST_PASSWORD,
        'alternative': ALTERNATIVE_PASSWORD,
        'simple': SIMPLE_PASSWORD
    }
    return passwords.get(password_type, TEST_PASSWORD)


def get_test_user_credentials(user_type='default'):
    """
    Get test user credentials by type.

    Args:
        user_type: One of 'default', 'admin', 'interviewer', 'candidate'

    Returns:
        Dictionary with username, password, and email
    """
    return TEST_USERS.get(user_type, TEST_USERS['default']).copy()
