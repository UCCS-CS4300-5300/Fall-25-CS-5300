"""
Comprehensive tests for CustomSocialAccountAdapter

This module provides extensive integration-style tests for adapters.py
to achieve >80% code coverage.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group
from unittest.mock import Mock, patch
from active_interview_app.adapters import CustomSocialAccountAdapter
from active_interview_app.models import UserProfile


class CustomSocialAccountAdapterComprehensiveTest(TestCase):
    """Comprehensive integration tests for CustomSocialAccountAdapter"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.adapter = CustomSocialAccountAdapter()
        # Ensure average_role group exists
        self.average_role_group = Group.objects.get_or_create(name='average_role')[
            0]

    def test_pre_social_login_with_existing_user(self):
        """Test pre_social_login when user already exists with same email"""
        # Create existing user
        _existing_user = User.objects.create_user(
            email='existing@example.com',
            password='testpass'
        )

        request = self.factory.get('/accounts/google/login/callback/')

        # Create mock social login
        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.extra_data = {'email': 'existing@example.com'}
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Verify connect was called with existing user
        mock_sociallogin.connect.assert_called_once()
        called_user = mock_sociallogin.connect.call_args[0][1]
        self.assertEqual(called_user.email, 'existing@example.com')

    def test_pre_social_login_with_no_email(self):
        """Test pre_social_login when social account has no email"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.extra_data = {}  # No email
        mock_sociallogin.connect = Mock()

        # Should not raise exception
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Connect should not be called
        mock_sociallogin.connect.assert_not_called()

    def test_pre_social_login_already_existing(self):
        """Test pre_social_login when sociallogin.is_existing is True"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = True
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Should return early, connect not called
        mock_sociallogin.connect.assert_not_called()

    def test_pre_social_login_no_matching_user(self):
        """Test pre_social_login when no user exists with the email"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.extra_data = {'email': 'newuser@example.com'}
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Connect should not be called (no matching user)
        mock_sociallogin.connect.assert_not_called()

    def test_pre_social_login_exception_handling(self):
        """Test pre_social_login handles exceptions gracefully"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        # Make extra_data raise an exception
        mock_sociallogin.account.extra_data.get = Mock(
            side_effect=Exception("Test error"))

        # Should not raise exception
        try:
            self.adapter.pre_social_login(request, mock_sociallogin)
        except Exception as e:
            self.fail(f"pre_social_login should not raise exception: {e}")

    def test_save_user_creates_profile_with_provider(self):
        """Test save_user creates UserProfile with correct provider"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        # Mock the parent save_user to return a real user
        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_parent:
            new_user = User.objects.create_user(
                username='newgoogleuser',
                email='newgoogleuser@example.com'
            )
            mock_parent.return_value = new_user

            # Call save_user
            saved_user = self.adapter.save_user(request, mock_sociallogin)

            # Verify user returned
            self.assertEqual(saved_user.email, 'newgoogleuser@example.com')

            # Verify UserProfile was created with google provider
            profile = UserProfile.objects.get(user=saved_user)
            self.assertEqual(profile.auth_provider, 'google')

            # Verify user added to average_role group
            self.assertTrue(saved_user.groups.filter(
                name='average_role').exists())

    def test_save_user_updates_existing_profile(self):
        """Test save_user updates existing profile if user already has one"""
        request = self.factory.get('/accounts/google/login/callback/')

        # Create user with existing profile
        existing_user = User.objects.create_user(
            username='userwithlocalprofile',
            email='user@example.com'
        )
        # Profile is auto-created by signal, verify it exists
        profile = UserProfile.objects.get(user=existing_user)
        self.assertEqual(profile.auth_provider, 'local')  # Default

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        # Mock parent to return existing user
        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_parent:
            mock_parent.return_value = existing_user

            # Call save_user
            _saved_user = self.adapter.save_user(request, mock_sociallogin)
            # Verify profile was updated to google
            profile.refresh_from_db()
            self.assertEqual(profile.auth_provider, 'google')

    def test_save_user_with_different_provider(self):
        """Test save_user with a different OAuth provider"""
        request = self.factory.get('/accounts/github/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'github'

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_parent:
            new_user = User.objects.create_user(
                username='githubuser',
                email='githubuser@example.com'
            )
            mock_parent.return_value = new_user

            # Call save_user
            saved_user = self.adapter.save_user(request, mock_sociallogin)

            # Verify profile has github provider
            profile = UserProfile.objects.get(user=saved_user)
            self.assertEqual(profile.auth_provider, 'github')

    def test_populate_user_with_full_google_data(self):
        """Test populate_user with complete Google data"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        google_data = {
            'email': 'john.doe@example.com',
            'given_name': 'John',
            'family_name': 'Doe'
        }

        # Mock parent populate_user
        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.populate_user') as mock_parent:
            # Create user object as parent would
            user = User()
            user.email = 'john.doe@example.com'
            user.username = ''
            user.first_name = ''
            user.last_name = ''
            mock_parent.return_value = user

            # Call populate_user
            populated_user = self.adapter.populate_user(
                request, mock_sociallogin, google_data)

            # Verify first and last names were populated
            self.assertEqual(populated_user.first_name, 'John')
            self.assertEqual(populated_user.last_name, 'Doe')
            # Verify username was set from email
            self.assertEqual(populated_user.username, 'john.doe')

    def test_populate_user_without_names(self):
        """Test populate_user when Google data lacks given_name and family_name"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        google_data = {
            'email': 'user@example.com'
            # No given_name or family_name
        }

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.populate_user') as mock_parent:
            user = User()
            user.email = 'user@example.com'
            user.username = ''
            user.first_name = ''
            user.last_name = ''
            mock_parent.return_value = user

            # Call populate_user
            populated_user = self.adapter.populate_user(
                request, mock_sociallogin, google_data)

            # Names should remain empty
            self.assertEqual(populated_user.first_name, '')
            self.assertEqual(populated_user.last_name, '')
            # Username should still be set from email
            self.assertEqual(populated_user.username, 'user')

    def test_populate_user_with_existing_names(self):
        """Test populate_user doesn't overwrite existing first/last name"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        google_data = {
            'email': 'user@example.com',
            'given_name': 'NewFirst',
            'family_name': 'NewLast'
        }

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.populate_user') as mock_parent:
            # User already has names set
            user = User()
            user.email = 'user@example.com'
            user.username = 'existinguser'
            user.first_name = 'ExistingFirst'
            user.last_name = 'ExistingLast'
            mock_parent.return_value = user

            # Call populate_user
            populated_user = self.adapter.populate_user(
                request, mock_sociallogin, google_data)

            # Should NOT overwrite existing names
            self.assertEqual(populated_user.first_name, 'ExistingFirst')
            self.assertEqual(populated_user.last_name, 'ExistingLast')

    def test_populate_user_with_existing_username(self):
        """Test populate_user doesn't overwrite existing username"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        google_data = {
            'email': 'newuser@example.com',
            'given_name': 'Jane',
            'family_name': 'Smith'
        }

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.populate_user') as mock_parent:
            # User already has username
            user = User()
            user.email = 'newuser@example.com'
            user.username = 'existingusername'
            user.first_name = ''
            user.last_name = ''
            mock_parent.return_value = user

            # Call populate_user
            populated_user = self.adapter.populate_user(
                request, mock_sociallogin, google_data)

            # Should NOT overwrite existing username
            self.assertEqual(populated_user.username, 'existingusername')
            # But should populate names
            self.assertEqual(populated_user.first_name, 'Jane')
            self.assertEqual(populated_user.last_name, 'Smith')

    def test_populate_user_email_without_domain(self):
        """Test populate_user with simple email generates correct username"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        google_data = {
            'email': 'simple@domain.com'
        }

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.populate_user') as mock_parent:
            user = User()
            user.email = 'simple@domain.com'
            user.username = ''
            mock_parent.return_value = user

            # Call populate_user
            populated_user = self.adapter.populate_user(
                request, mock_sociallogin, google_data)

            # Username should be 'simple'
            self.assertEqual(populated_user.username, 'simple')

    def test_populate_user_complex_email(self):
        """Test populate_user with complex email (dots, numbers)"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        google_data = {
            'email': 'john.doe.123@example.com'
        }

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.populate_user') as mock_parent:
            user = User()
            user.email = 'john.doe.123@example.com'
            user.username = ''
            mock_parent.return_value = user

            # Call populate_user
            populated_user = self.adapter.populate_user(
                request, mock_sociallogin, google_data)

            # Username should be 'john.doe.123'
            self.assertEqual(populated_user.username, 'john.doe.123')

    def test_populate_user_no_email(self):
        """Test populate_user when user has no email"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        google_data = {}

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.populate_user') as mock_parent:
            user = User()
            user.email = ''
            user.username = ''
            mock_parent.return_value = user

            # Call populate_user
            populated_user = self.adapter.populate_user(
                request, mock_sociallogin, google_data)

            # Username should remain empty
            self.assertEqual(populated_user.username, '')

    def test_save_user_creates_group_if_not_exists(self):
        """Test save_user creates average_role group if it doesn't exist"""
        # Delete the group if it exists
        Group.objects.filter(name='average_role').delete()

        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_parent:
            new_user = User.objects.create_user(
                username='testgroupcreation',
                email='testgroupcreation@example.com'
            )
            mock_parent.return_value = new_user

            # Call save_user
            saved_user = self.adapter.save_user(request, mock_sociallogin)

            # Verify group was created
            self.assertTrue(Group.objects.filter(name='average_role').exists())

            # Verify user is in the group
            self.assertTrue(saved_user.groups.filter(
                name='average_role').exists())

    def test_save_user_calls_parent_method(self):
        """Test save_user properly calls parent class save_user"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_parent:
            new_user = User.objects.create_user(
                username='parentcalltest',
                email='parentcalltest@example.com'
            )
            mock_parent.return_value = new_user

            # Call save_user
            self.adapter.save_user(request, mock_sociallogin)

            # Verify parent was called with correct arguments
            mock_parent.assert_called_once_with(
                request, mock_sociallogin, None)

    def test_save_user_with_form_parameter(self):
        """Test save_user can accept optional form parameter"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.provider = 'google'

        mock_form = Mock()

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.save_user') as mock_parent:
            new_user = User.objects.create_user(
                username='formtest',
                email='formtest@example.com'
            )
            mock_parent.return_value = new_user

            # Call save_user with form
            self.adapter.save_user(request, mock_sociallogin, form=mock_form)

            # Verify parent was called with form
            mock_parent.assert_called_once_with(
                request, mock_sociallogin, mock_form)

    def test_populate_user_calls_parent_method(self):
        """Test populate_user properly calls parent class populate_user"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        google_data = {'email': 'test@example.com'}

        with patch('active_interview_app.adapters.DefaultSocialAccountAdapter.populate_user') as mock_parent:
            user = User()
            user.email = 'test@example.com'
            mock_parent.return_value = user

            # Call populate_user
            self.adapter.populate_user(request, mock_sociallogin, google_data)

            # Verify parent was called
            mock_parent.assert_called_once_with(
                request, mock_sociallogin, google_data)

    def test_pre_social_login_with_email_none_from_get(self):
        """Test pre_social_login when extra_data.get() explicitly returns None"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        # Explicitly return None for email
        mock_sociallogin.account.extra_data = {'other_field': 'value'}
        mock_sociallogin.connect = Mock()

        # Call pre_social_login
        self.adapter.pre_social_login(request, mock_sociallogin)

        # Connect should not be called
        mock_sociallogin.connect.assert_not_called()

    def test_pre_social_login_exception_during_user_lookup(self):
        """Test pre_social_login handles exception during User.objects.filter"""
        request = self.factory.get('/accounts/google/login/callback/')

        mock_sociallogin = Mock()
        mock_sociallogin.is_existing = False
        mock_sociallogin.account = Mock()
        mock_sociallogin.account.extra_data = {'email': 'test@example.com'}

        # Mock User.objects.filter to raise an exception
        with patch('django.contrib.auth.models.User.objects') as mock_user_objects:
            mock_user_objects.filter.side_effect = Exception("Database error")

            # Should not raise exception
            try:
                self.adapter.pre_social_login(request, mock_sociallogin)
            except Exception as e:
                self.fail(f"pre_social_login should handle exception: {e}")
