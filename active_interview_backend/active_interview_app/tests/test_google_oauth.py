"""
Tests for Google OAuth authentication flow.

Tests the following scenario:
- User logs in with Google
- If email exists in users table → user is logged in (session created)
- If email does not exist → new user record is created with Google as auth provider

Acceptance Criteria:
• Check database for existing user with Google email
• Existing user → session created
• New user → record created with default profile data
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User, Group
from django.urls import reverse
from unittest.mock import Mock, patch, MagicMock

from allauth.socialaccount.models import SocialAccount, SocialApp
from allauth.socialaccount.signals import pre_social_login

from active_interview_app.models import UserProfile
from active_interview_app.adapters import CustomSocialAccountAdapter


class GoogleOAuthFlowTest(TestCase):
    """Test Google OAuth authentication flow"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.factory = RequestFactory()

        # Create average_role group (required by adapter)
        self.average_role_group = Group.objects.create(name='average_role')

        # Create a mock SocialApp for Google
        self.social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test-client-id',
            secret='test-secret'
        )
        self.social_app.sites.add(1)

    def test_existing_user_login_creates_session(self):
        """
        Test that when a user with existing email logs in via Google,
        a session is created (user is logged in).
        """
        # Create existing user with email
        existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

        # Create profile for existing user (local auth)
        profile = UserProfile.objects.get(user=existing_user)
        profile.auth_provider = 'local'
        profile.save()

        # Simulate Google login with the same email
        # In reality, allauth would handle the OAuth flow
        # Here we test that the adapter connects the social account

        adapter = CustomSocialAccountAdapter()
        request = self.factory.get('/accounts/google/login/callback/')

        # Create mock social login
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {
            'email': 'existing@example.com',
            'given_name': 'John',
            'family_name': 'Doe'
        }

        # Mock the connect method
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        adapter.pre_social_login(request, mock_sociallogin)

        # Verify that connect was called with the existing user
        mock_sociallogin.connect.assert_called_once()
        call_args = mock_sociallogin.connect.call_args[0]
        self.assertEqual(call_args[1].email, 'existing@example.com')

    def test_new_user_creation_with_google_provider(self):
        """
        Test that when a new user logs in via Google,
        a new User and UserProfile are created with auth_provider='google'.
        """
        # Verify no user exists with this email
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())

        # Create adapter and mock request
        adapter = CustomSocialAccountAdapter()
        request = self.factory.get('/accounts/google/login/callback/')
        request.session = {}

        # Create mock social login for new user
        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {
            'email': 'newuser@example.com',
            'given_name': 'Jane',
            'family_name': 'Smith'
        }

        # Mock user object
        mock_user = User()
        mock_user.email = 'newuser@example.com'
        mock_user.username = 'newuser'
        mock_user.first_name = ''
        mock_user.last_name = ''

        # Test populate_user
        populated_user = adapter.populate_user(request, mock_sociallogin,
                                               mock_sociallogin.account.extra_data)

        self.assertEqual(populated_user.email, 'newuser@example.com')

        # Now test save_user (this creates the user and profile)
        # We need to actually save to test the full flow
        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_save:
            # Create a real user to return from the parent save_user
            new_user = User.objects.create_user(
                username='newuser',
                email='newuser@example.com'
            )
            mock_save.return_value = new_user

            # Call save_user
            saved_user = adapter.save_user(request, mock_sociallogin)

            # Verify user was created
            self.assertEqual(saved_user.email, 'newuser@example.com')

            # Verify UserProfile was created with correct auth_provider
            profile = UserProfile.objects.get(user=saved_user)
            self.assertEqual(profile.auth_provider, 'google')

            # Verify user was added to average_role group
            self.assertTrue(saved_user.groups.filter(name='average_role').exists())

    def test_user_profile_tracks_auth_provider(self):
        """Test that UserProfile correctly tracks the authentication provider"""
        # Create user via local registration
        local_user = User.objects.create_user(
            username='localuser',
            email='local@example.com',
            password='testpass123'
        )

        # Verify profile was created with default 'local' provider
        local_profile = UserProfile.objects.get(user=local_user)
        self.assertEqual(local_profile.auth_provider, 'local')

        # Create user via Google (simulated)
        google_user = User.objects.create_user(
            username='googleuser',
            email='google@example.com'
        )
        google_profile = UserProfile.objects.get(user=google_user)
        google_profile.auth_provider = 'google'
        google_profile.save()

        # Verify correct providers are set
        self.assertEqual(
            UserProfile.objects.get(user=local_user).auth_provider,
            'local'
        )
        self.assertEqual(
            UserProfile.objects.get(user=google_user).auth_provider,
            'google'
        )

    def test_adapter_populates_user_from_google_data(self):
        """Test that adapter correctly populates user fields from Google data"""
        adapter = CustomSocialAccountAdapter()
        request = self.factory.get('/')

        # Create mock social login
        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        # Google data
        google_data = {
            'email': 'testuser@example.com',
            'given_name': 'Test',
            'family_name': 'User'
        }

        # Create user object
        user = User()
        user.email = google_data['email']
        user.username = ''
        user.first_name = ''
        user.last_name = ''

        # Mock the parent class method
        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.populate_user') as mock_populate:
            mock_populate.return_value = user

            # Call adapter method
            populated_user = adapter.populate_user(request, mock_sociallogin, google_data)

            # Verify user fields are populated
            self.assertEqual(populated_user.email, 'testuser@example.com')

    def test_new_user_added_to_default_group(self):
        """Test that new Google OAuth users are added to average_role group"""
        adapter = CustomSocialAccountAdapter()
        request = self.factory.get('/')

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_save:
            # Create real user
            new_user = User.objects.create_user(
                username='grouptest',
                email='grouptest@example.com'
            )
            mock_save.return_value = new_user

            # Call save_user
            saved_user = adapter.save_user(request, mock_sociallogin)

            # Verify user is in average_role group
            self.assertTrue(saved_user.groups.filter(name='average_role').exists())
            self.assertEqual(saved_user.groups.count(), 1)


class UserProfileModelTest(TestCase):
    """Test UserProfile model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_profile_created_on_user_creation(self):
        """Test that UserProfile is automatically created when User is created"""
        # Profile should be created by signal
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_user_profile_default_auth_provider(self):
        """Test that default auth_provider is 'local'"""
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.auth_provider, 'local')

    def test_user_profile_string_representation(self):
        """Test UserProfile __str__ method"""
        profile = UserProfile.objects.get(user=self.user)
        expected = f"{self.user.username} - local"
        self.assertEqual(str(profile), expected)

    def test_user_profile_can_update_auth_provider(self):
        """Test that auth_provider can be updated"""
        profile = UserProfile.objects.get(user=self.user)
        profile.auth_provider = 'google'
        profile.save()

        # Retrieve and verify
        updated_profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(updated_profile.auth_provider, 'google')

    def test_user_profile_timestamps(self):
        """Test that created_at and updated_at are set correctly"""
        profile = UserProfile.objects.get(user=self.user)

        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)

        # Updated_at should be >= created_at
        self.assertGreaterEqual(profile.updated_at, profile.created_at)
