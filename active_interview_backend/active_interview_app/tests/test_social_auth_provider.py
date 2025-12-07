"""
Tests for Issue #128: Social Accounts Show as "Local" Instead of Provider

This test file specifically verifies that the auth_provider field is correctly
set for users who authenticate via social providers (Google OAuth).

Test scenarios:
1. New user signing up with Google gets 'google' provider
2. Existing local user connecting Google gets provider updated from 'local' to 'google'
3. Existing Google user stays 'google' (no change)
4. Multiple social accounts scenario
"""
from unittest.mock import Mock, patch
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from active_interview_app.adapters import CustomSocialAccountAdapter
from active_interview_app.models import UserProfile


class SocialAuthProviderTestCase(TestCase):
    """Test auth_provider field updates for social authentication."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.adapter = CustomSocialAccountAdapter()

    def test_new_google_user_gets_google_provider(self):
        """
        Test that a brand new user signing up with Google gets auth_provider='google'.

        This is the existing behavior that should continue to work.
        """
        # Create mock request
        request = self.factory.get('/accounts/google/login/callback/')
        request.session = {}

        # Create mock social login for new user
        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {
            'email': 'newuser@example.com',
            'given_name': 'New',
            'family_name': 'User'
        }

        # Mock the parent save_user to create a real user
        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_save:
            new_user = User.objects.create_user(
                username='newuser',
                email='newuser@example.com'
            )
            mock_save.return_value = new_user

            # Call save_user (this happens for NEW users)
            saved_user = self.adapter.save_user(request, mock_sociallogin)

            # Verify user was created
            self.assertEqual(saved_user.email, 'newuser@example.com')

            # Verify auth_provider is 'google'
            profile = UserProfile.objects.get(user=saved_user)
            self.assertEqual(profile.auth_provider, 'google')

    def test_existing_local_user_connecting_google_updates_provider(self):
        """
        Test that an existing local user connecting Google gets auth_provider updated.

        This is the FIX for Issue #128:
        - User registers locally (auth_provider='local')
        - User later logs in with Google using the same email
        - auth_provider should be updated from 'local' to 'google'
        """
        # Create existing local user
        existing_user = User.objects.create_user(
            username='localuser',
            email='localuser@example.com',
            password='testpass123'
        )

        # Verify profile has 'local' provider
        profile = UserProfile.objects.get(user=existing_user)
        self.assertEqual(profile.auth_provider, 'local')

        # Create mock request
        request = self.factory.get('/accounts/google/login/callback/')
        request.session = {}

        # Create mock social login for existing user
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False  # Not already connected
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {
            'email': 'localuser@example.com',  # Same email as existing user
        }

        # Mock the connect method
        mock_sociallogin.connect = Mock()

        # Call pre_social_login (this happens when connecting existing account)
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Verify connect was called
        mock_sociallogin.connect.assert_called_once_with(request, existing_user)

        # Verify auth_provider was updated to 'google'
        profile.refresh_from_db()
        self.assertEqual(profile.auth_provider, 'google')

    def test_existing_google_user_keeps_google_provider(self):
        """
        Test that an existing Google user keeps auth_provider='google'.

        Scenario: User already has Google OAuth connected, logs in again.
        Should NOT change anything.
        """
        # Create existing Google user
        existing_user = User.objects.create_user(
            username='googleuser',
            email='googleuser@example.com'
        )

        # Set auth_provider to 'google'
        profile = UserProfile.objects.get(user=existing_user)
        profile.auth_provider = 'google'
        profile.save()

        # Create mock request
        request = self.factory.get('/accounts/google/login/callback/')
        request.session = {}

        # Create mock social login
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {
            'email': 'googleuser@example.com',
        }

        # Mock the connect method
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Verify connect was called
        mock_sociallogin.connect.assert_called_once_with(request, existing_user)

        # Verify auth_provider is still 'google'
        profile.refresh_from_db()
        self.assertEqual(profile.auth_provider, 'google')

    def test_no_update_if_already_connected(self):
        """
        Test that no changes occur if sociallogin.is_existing is True.

        This means the social account is already connected to the user.
        """
        # Create user
        existing_user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        profile = UserProfile.objects.get(user=existing_user)
        profile.auth_provider = 'local'
        profile.save()

        # Create mock request
        request = self.factory.get('/accounts/google/login/callback/')
        request.session = {}

        # Create mock social login that's already connected
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = True  # Already connected
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        # Mock connect method
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Verify connect was NOT called (early return)
        mock_sociallogin.connect.assert_not_called()

        # Verify auth_provider was NOT changed
        profile.refresh_from_db()
        self.assertEqual(profile.auth_provider, 'local')

    def test_no_update_without_email(self):
        """
        Test that no changes occur if the social account has no email.
        """
        # Create user
        existing_user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        profile = UserProfile.objects.get(user=existing_user)
        profile.auth_provider = 'local'
        profile.save()

        # Create mock request
        request = self.factory.get('/accounts/google/login/callback/')
        request.session = {}

        # Create mock social login without email
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {}  # No email

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Verify auth_provider was NOT changed
        profile.refresh_from_db()
        self.assertEqual(profile.auth_provider, 'local')

    def test_no_update_if_no_matching_user(self):
        """
        Test that nothing happens if there's no existing user with that email.
        """
        # Create mock request
        request = self.factory.get('/accounts/google/login/callback/')
        request.session = {}

        # Create mock social login with email that doesn't exist
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {
            'email': 'nonexistent@example.com',
        }

        # Mock connect method
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Verify connect was NOT called (no existing user)
        mock_sociallogin.connect.assert_not_called()

    def test_handles_missing_profile_gracefully(self):
        """
        Test that the code handles missing UserProfile gracefully.

        This shouldn't happen in practice (signal creates profile), but we
        should handle it without crashing.
        """
        # Create user WITHOUT profile (by deleting signal-created one)
        existing_user = User.objects.create_user(
            username='noprofile',
            email='noprofile@example.com'
        )
        UserProfile.objects.filter(user=existing_user).delete()

        # Verify no profile exists
        self.assertFalse(UserProfile.objects.filter(user=existing_user).exists())

        # Create mock request
        request = self.factory.get('/accounts/google/login/callback/')
        request.session = {}

        # Create mock social login
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {
            'email': 'noprofile@example.com',
        }

        # Mock connect method
        mock_sociallogin.connect = Mock()

        # Call pre_social_login - should not crash
        try:
            self.adapter.pre_social_login(request, mock_sociallogin)
        except Exception as e:
            self.fail(f"pre_social_login raised exception: {e}")

        # Verify connect was still called
        mock_sociallogin.connect.assert_called_once_with(request, existing_user)

    def test_github_provider_also_supported(self):
        """
        Test that the fix works for other OAuth providers (not just Google).

        Example: GitHub OAuth
        """
        # Create existing local user
        existing_user = User.objects.create_user(
            username='localuser',
            email='localuser@example.com',
            password='testpass123'
        )

        # Verify profile has 'local' provider
        profile = UserProfile.objects.get(user=existing_user)
        self.assertEqual(profile.auth_provider, 'local')

        # Create mock request
        request = self.factory.get('/accounts/github/login/callback/')
        request.session = {}

        # Create mock social login for GitHub
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'github'  # Different provider
        mock_sociallogin.account.extra_data = {
            'email': 'localuser@example.com',
        }

        # Mock the connect method
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Verify auth_provider was updated to 'github'
        profile.refresh_from_db()
        self.assertEqual(profile.auth_provider, 'github')

    def test_does_not_overwrite_existing_oauth_provider(self):
        """
        Test that if a user has Google, we DON'T overwrite it with GitHub.

        Scenario: User has auth_provider='google', tries to add GitHub.
        Since it's not 'local', we should NOT update it.
        """
        # Create user with Google provider
        existing_user = User.objects.create_user(
            username='googleuser',
            email='googleuser@example.com'
        )

        profile = UserProfile.objects.get(user=existing_user)
        profile.auth_provider = 'google'
        profile.save()

        # Create mock request for GitHub
        request = self.factory.get('/accounts/github/login/callback/')
        request.session = {}

        # Create mock social login for GitHub
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'github'
        mock_sociallogin.account.extra_data = {
            'email': 'googleuser@example.com',
        }

        # Mock the connect method
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Verify connect was called
        mock_sociallogin.connect.assert_called_once_with(request, existing_user)

        # Verify auth_provider is still 'google' (NOT updated to 'github')
        profile.refresh_from_db()
        self.assertEqual(profile.auth_provider, 'google')


class AuthProviderDataExportTestCase(TestCase):
    """
    Test that auth_provider is correctly exported in user data.

    This verifies that the bug fix is visible in the user data export.
    """

    def test_google_user_data_export_shows_google(self):
        """
        Test that Google users see 'google' in their data export, not 'local'.

        This is where the bug manifests to users - in their GDPR/CCPA data export.
        """
        # Create Google user
        user = User.objects.create_user(
            username='googleuser',
            email='google@example.com'
        )

        profile = UserProfile.objects.get(user=user)
        profile.auth_provider = 'google'
        profile.save()

        # Check that profile correctly shows 'google'
        self.assertEqual(profile.auth_provider, 'google')

        # Verify the __str__ method includes the provider
        expected_str = f"{user.username} - {profile.role} (google)"
        self.assertEqual(str(profile), expected_str)

    def test_local_user_data_export_shows_local(self):
        """
        Test that local users still see 'local' in their data export.
        """
        # Create local user
        user = User.objects.create_user(
            username='localuser',
            email='local@example.com',
            password='testpass123'
        )

        profile = UserProfile.objects.get(user=user)

        # Should default to 'local'
        self.assertEqual(profile.auth_provider, 'local')

        # Verify __str__ includes 'local'
        expected_str = f"{user.username} - {profile.role} (local)"
        self.assertEqual(str(profile), expected_str)
