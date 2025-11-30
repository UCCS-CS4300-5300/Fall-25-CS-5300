"""
Comprehensive tests to verify both password-based and OAuth authentication work together.

This test suite ensures:
1. Password-based registration and login work correctly
2. OAuth (Google) authentication works correctly
3. Both authentication methods can coexist in the same database
4. Users created via password have auth_provider='local'
5. Users created via OAuth have auth_provider='google'
6. Existing password users can link OAuth accounts
7. Django's User model password field works for both methods
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from django.urls import reverse
from unittest.mock import Mock, patch

from allauth.socialaccount.models import SocialApp
from active_interview_app.models import UserProfile
from active_interview_app.adapters import CustomSocialAccountAdapter


class DualAuthenticationTestCase(TestCase):
    """Test that password and OAuth authentication work together"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.factory = RequestFactory()

        # Create average_role group (required by both auth methods)
        self.average_role_group = Group.objects.get_or_create(name='average_role')[
            0]

        # Create mock SocialApp for Google OAuth
        self.social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test-client-id',
            secret='test-secret'
        )
        self.social_app.sites.add(1)

    def test_password_user_has_usable_password(self):
        """Test that password-registered users have usable passwords"""
        # Create user with password
        user = User.objects.create_user(
            username='passworduser',
            email='password@example.com',
            password='SecurePass123!'
        )

        # Verify password is usable
        self.assertTrue(user.has_usable_password())

        # Verify authentication works
        auth_user = authenticate(
            username='passworduser',
            password='SecurePass123!'
        )
        self.assertIsNotNone(auth_user)
        self.assertEqual(auth_user.id, user.id)

    def test_password_user_has_local_auth_provider(self):
        """Test that password users have auth_provider='local'"""
        user = User.objects.create_user(
            username='localuser',
            email='local@example.com',
            password='Pass123!'
        )

        # Profile should be auto-created by signal
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.auth_provider, 'local')

    def test_oauth_user_can_have_no_password(self):
        """Test that OAuth users can exist without a password"""
        # Create user without password (as OAuth would)
        user = User.objects.create_user(
            username='oauthuser',
            email='oauth@example.com'
        )
        # Don't set password

        # User should not have usable password
        self.assertFalse(user.has_usable_password())

        # But user should still be valid
        self.assertTrue(user.is_active)
        self.assertEqual(user.email, 'oauth@example.com')

    def test_oauth_user_has_google_auth_provider(self):
        """Test that OAuth users have auth_provider='google'"""
        # Simulate OAuth user creation
        adapter = CustomSocialAccountAdapter()
        request = self.factory.get('/')

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_save:
            # Create user
            user = User.objects.create_user(
                username='googleuser',
                email='google@example.com'
            )
            mock_save.return_value = user

            # Call adapter's save_user
            saved_user = adapter.save_user(request, mock_sociallogin)

            # Verify auth_provider is set to 'google'
            profile = UserProfile.objects.get(user=saved_user)
            self.assertEqual(profile.auth_provider, 'google')

    def test_both_auth_methods_coexist(self):
        """Test that password and OAuth users can coexist in same database"""
        # Create password user
        password_user = User.objects.create_user(
            username='pwduser',
            email='pwd@example.com',
            password='Password123!'
        )
        password_profile = UserProfile.objects.get(user=password_user)
        password_profile.auth_provider = 'local'
        password_profile.save()

        # Create OAuth user
        oauth_user = User.objects.create_user(
            username='oauthuser',
            email='oauth@example.com'
        )
        oauth_profile = UserProfile.objects.get(user=oauth_user)
        oauth_profile.auth_provider = 'google'
        oauth_profile.save()

        # Both should exist
        self.assertEqual(User.objects.count(), 2)

        # Verify they have different auth providers
        pwd_profile = UserProfile.objects.get(user=password_user)
        oauth_profile = UserProfile.objects.get(user=oauth_user)

        self.assertEqual(pwd_profile.auth_provider, 'local')
        self.assertEqual(oauth_profile.auth_provider, 'google')

        # Password user should be able to authenticate
        auth_user = authenticate(
            username='pwduser',
            password='Password123!'
        )
        self.assertIsNotNone(auth_user)

        # OAuth user should not authenticate with password
        auth_oauth = authenticate(
            username='oauthuser',
            password='anypassword'
        )
        self.assertIsNone(auth_oauth)

    def test_existing_password_user_can_link_oauth(self):
        """Test that existing password user can add OAuth account"""
        # Create password user
        password_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='ExistingPass123!'
        )

        # Verify profile has local auth
        profile = UserProfile.objects.get(user=password_user)
        self.assertEqual(profile.auth_provider, 'local')

        # Simulate OAuth login with same email
        adapter = CustomSocialAccountAdapter()
        request = self.factory.get('/')

        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {
            'email': 'existing@example.com',
            'given_name': 'John',
            'family_name': 'Doe'
        }
        mock_sociallogin.connect = Mock()

        # Call pre_social_login (should connect to existing user)
        adapter.pre_social_login(request, mock_sociallogin)

        # Verify connect was called
        mock_sociallogin.connect.assert_called_once()

        # User should still be able to authenticate with password
        auth_user = authenticate(
            username='existinguser',
            password='ExistingPass123!'
        )
        self.assertIsNotNone(auth_user)
        self.assertTrue(auth_user.has_usable_password())

    def test_password_field_accepts_both_auth_types(self):
        """Test that Django User.password field works for both auth types"""
        # Password user - should have password hash
        pwd_user = User.objects.create_user(
            username='pwduser',
            email='pwd@example.com',
            password='Password123!'
        )
        self.assertTrue(pwd_user.password.startswith('pbkdf2_sha256'))
        self.assertTrue(len(pwd_user.password) > 50)

        # OAuth user - should have unusable password marker
        oauth_user = User.objects.create_user(
            username='oauthuser',
            email='oauth@example.com'
        )
        # Django sets unusable password by default
        self.assertFalse(oauth_user.has_usable_password())
        self.assertTrue(oauth_user.password.startswith('!'))

    def test_both_users_added_to_same_group(self):
        """Test that both auth methods add users to average_role group"""
        # Create password user
        pwd_user = User.objects.create_user(
            username='pwduser',
            email='pwd@example.com',
            password='Pass123!'
        )
        pwd_user.groups.add(self.average_role_group)

        # Create OAuth user via adapter
        adapter = CustomSocialAccountAdapter()
        request = self.factory.get('/')

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_save:
            oauth_user = User.objects.create_user(
                username='oauthuser',
                email='oauth@example.com'
            )
            mock_save.return_value = oauth_user

            saved_user = adapter.save_user(request, mock_sociallogin)

        # Both should be in average_role group
        self.assertTrue(pwd_user.groups.filter(name='average_role').exists())
        self.assertTrue(saved_user.groups.filter(name='average_role').exists())

        # Same group instance
        pwd_group = pwd_user.groups.get(name='average_role')
        oauth_group = saved_user.groups.get(name='average_role')
        self.assertEqual(pwd_group.id, oauth_group.id)

    def test_user_profile_signal_works_for_both_auth_types(self):
        """Test that UserProfile is auto-created for both auth types"""
        # Password user
        pwd_user = User.objects.create_user(
            username='pwduser',
            email='pwd@example.com',
            password='Pass123!'
        )

        # OAuth user
        oauth_user = User.objects.create_user(
            username='oauthuser',
            email='oauth@example.com'
        )

        # Both should have profiles auto-created by signal
        self.assertTrue(UserProfile.objects.filter(user=pwd_user).exists())
        self.assertTrue(UserProfile.objects.filter(user=oauth_user).exists())

        # Both should have default 'local' provider (adapter changes it for
        # OAuth)
        pwd_profile = UserProfile.objects.get(user=pwd_user)
        oauth_profile = UserProfile.objects.get(user=oauth_user)

        self.assertEqual(pwd_profile.auth_provider, 'local')
        # Default until adapter updates it
        self.assertEqual(oauth_profile.auth_provider, 'local')


class DatabaseSchemaTestCase(TestCase):
    """Test that database schema supports both authentication methods"""

    def test_user_model_has_password_field(self):
        """Test that User model has password field for password auth"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

        # Password field should exist and be populated
        self.assertTrue(hasattr(user, 'password'))
        self.assertIsNotNone(user.password)
        self.assertNotEqual(user.password, '')

    def test_user_profile_has_auth_provider_field(self):
        """Test that UserProfile has auth_provider field"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        profile = UserProfile.objects.get(user=user)

        # Should have auth_provider field
        self.assertTrue(hasattr(profile, 'auth_provider'))
        self.assertEqual(profile.auth_provider, 'local')

    def test_auth_provider_field_accepts_different_values(self):
        """Test that auth_provider can be set to different values"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        profile = UserProfile.objects.get(user=user)

        # Test different provider values
        providers = ['local', 'google', 'github', 'facebook']

        for provider in providers:
            profile.auth_provider = provider
            profile.save()

            # Retrieve and verify
            updated_profile = UserProfile.objects.get(user=user)
            self.assertEqual(updated_profile.auth_provider, provider)

    def test_django_allauth_tables_exist(self):
        """Test that django-allauth tables are available"""
        # This tests that migrations for allauth have run
        from django.db import connection

        tables = connection.introspection.table_names()

        # Check for key allauth tables
        expected_tables = [
            'socialaccount_socialaccount',
            'socialaccount_socialapp',
            'socialaccount_socialtoken',
        ]

        for table in expected_tables:
            self.assertIn(table, tables,
                          f"Table {table} should exist for OAuth support")


class AuthenticationIntegrationTest(TestCase):
    """Integration tests for dual authentication system"""

    def setUp(self):
        """Set up test data"""
        Group.objects.get_or_create(name='average_role')

    def test_full_password_registration_flow(self):
        """Test complete password registration flow"""
        # Register user
        client = Client()
        response = client.post(reverse('register_page'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })

        # Should redirect to login
        self.assertEqual(response.status_code, 302)

        # User should exist with password
        user = User.objects.get(username='newuser')
        self.assertTrue(user.has_usable_password())

        # Profile should exist with local provider
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.auth_provider, 'local')

        # Should be able to login
        login_success = client.login(
            username='newuser',
            password='SecurePass123!'
        )
        self.assertTrue(login_success)

    def test_authentication_backends_configured(self):
        """Test that both authentication backends are configured"""
        from django.conf import settings

        backends = settings.AUTHENTICATION_BACKENDS

        # Should have both backends
        self.assertIn('django.contrib.auth.backends.ModelBackend', backends)
        self.assertIn(
            'allauth.account.auth_backends.AuthenticationBackend', backends)

    def test_oauth_apps_installed(self):
        """Test that OAuth apps are installed"""
        from django.conf import settings

        installed_apps = settings.INSTALLED_APPS

        # Check for allauth apps
        required_apps = [
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
            'allauth.socialaccount.providers.google',
        ]

        for app in required_apps:
            self.assertIn(app, installed_apps,
                          f"{app} should be installed for OAuth support")
