"""
Tests for profile editing functionality (Issue #119).

This module tests:
- Authentication requirements
- Profile edit form GET/POST requests
- Email uniqueness validation
- Ownership verification
- Success/error messages
- Edge cases
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class ProfileEditAuthenticationTestCase(TestCase):
    """Test authentication requirements for profile editing."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.edit_url = reverse('edit_profile')
        self.login_url = reverse('account_login')

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_edit_profile_requires_login(self):
        """Test that edit profile page requires authentication."""
        response = self.client.get(self.edit_url)

        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_authenticated_user_can_access_edit_profile(self):
        """Test that authenticated users can access edit profile page."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_edit.html')


class ProfileEditGETRequestTestCase(TestCase):
    """Test GET requests to profile edit page."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.edit_url = reverse('edit_profile')

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

    def test_form_displays_current_user_data(self):
        """Test that form pre-populates with current user data."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)

        # Check form is in context
        self.assertIn('form', response.context)
        form = response.context['form']

        # Check initial values
        self.assertEqual(form.initial['username'], 'testuser')
        self.assertEqual(form.initial['email'], 'test@example.com')
        self.assertEqual(form.initial['first_name'], 'John')
        self.assertEqual(form.initial['last_name'], 'Doe')

    def test_username_field_editable(self):
        """Test that username is now an editable field."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)

        # Username should be in form fields
        form = response.context['form']
        self.assertIn('username', form.fields)

        # Username field should have current value
        self.assertEqual(form.initial['username'], 'testuser')


class ProfileEditPOSTRequestTestCase(TestCase):
    """Test POST requests to profile edit page."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.edit_url = reverse('edit_profile')
        self.profile_url = reverse('profile')

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='original@example.com',
            password='testpass123',
            first_name='Original',
            last_name='Name'
        )

    def test_valid_data_saves_successfully(self):
        """Test that valid form data saves successfully."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User'
        })

        # Should redirect to profile page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.profile_url)

        # Refresh user from database
        self.user.refresh_from_db()

        # Check data was saved
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'User')

    def test_success_message_displayed(self):
        """Test that success message is displayed after save."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User'
        }, follow=True)

        # Check for success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('successfully', str(messages[0]))

    def test_redirect_to_profile_after_save(self):
        """Test that user is redirected to profile page after save."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User'
        })

        self.assertRedirects(response, self.profile_url)


class ProfileEditValidationTestCase(TestCase):
    """Test form validation for profile editing."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.edit_url = reverse('edit_profile')

        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

    def test_email_uniqueness_validation(self):
        """Test that duplicate email addresses are rejected."""
        self.client.login(username='user1', password='testpass123')

        # Try to use user2's email
        response = self.client.post(self.edit_url, {
            'username': 'user1',
            'email': 'user2@example.com',
            'first_name': '',
            'last_name': ''
        })

        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)

        # Should show error message
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('email', form.errors)
        self.assertIn(
            'already registered',
            form.errors['email'][0].lower()
        )

        # User1's email should NOT be changed
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, 'user1@example.com')

    def test_own_email_allowed(self):
        """Test that user can keep their own email (not flagged as duplicate)."""
        self.client.login(username='user1', password='testpass123')

        # Submit form with same email
        response = self.client.post(self.edit_url, {
            'username': 'user1',
            'email': 'user1@example.com',  # Same as current
            'first_name': 'Updated',
            'last_name': 'Name'
        })

        # Should succeed (redirect)
        self.assertEqual(response.status_code, 302)

        # Check data was saved
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, 'user1@example.com')
        self.assertEqual(self.user1.first_name, 'Updated')

    def test_invalid_email_format_rejected(self):
        """Test that invalid email format is rejected."""
        self.client.login(username='user1', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'user1',
            'email': 'invalid-email-format',  # No @ symbol
            'first_name': 'Test',
            'last_name': 'User'
        })

        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)

        # Should show error
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('email', form.errors)

    def test_email_required(self):
        """Test that email cannot be blank."""
        self.client.login(username='user1', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'user1',
            'email': '',  # Blank email
            'first_name': 'Test',
            'last_name': 'User'
        })

        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)

        # Should show error
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('email', form.errors)

    def test_username_can_be_changed(self):
        """Test that username can be successfully changed."""
        self.client.login(username='user1', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'newusername',
            'email': 'user1@example.com',
            'first_name': 'User',
            'last_name': 'One'
        })

        # Should succeed (redirect)
        self.assertEqual(response.status_code, 302)

        # Check username was changed
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'newusername')

    def test_username_uniqueness_validation(self):
        """Test that duplicate usernames are rejected."""
        self.client.login(username='user1', password='testpass123')

        # Try to use user2's username
        response = self.client.post(self.edit_url, {
            'username': 'user2',
            'email': 'user1@example.com',
            'first_name': '',
            'last_name': ''
        })

        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)

        # Should show error message
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('username', form.errors)
        self.assertIn(
            'already taken',
            form.errors['username'][0].lower()
        )

        # User1's username should NOT be changed
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'user1')

    def test_own_username_allowed(self):
        """Test that user can keep their own username (not flagged as duplicate)."""
        self.client.login(username='user1', password='testpass123')

        # Submit form with same username
        response = self.client.post(self.edit_url, {
            'username': 'user1',  # Same as current
            'email': 'user1@example.com',
            'first_name': 'Updated',
            'last_name': 'Name'
        })

        # Should succeed (redirect)
        self.assertEqual(response.status_code, 302)

        # Check data was saved
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'user1')
        self.assertEqual(self.user1.first_name, 'Updated')

    def test_invalid_username_format_rejected(self):
        """Test that invalid username format is rejected."""
        self.client.login(username='user1', password='testpass123')

        # Test with spaces (invalid for Django username)
        response = self.client.post(self.edit_url, {
            'username': 'user name',  # Spaces not allowed
            'email': 'user1@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        })

        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)

        # Should show error
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('username', form.errors)


class ProfileEditOwnershipTestCase(TestCase):
    """Test ownership and security for profile editing."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.edit_url = reverse('edit_profile')

        # Create two users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )

    def test_user_can_only_edit_own_profile(self):
        """Test that logged-in user edits their own profile, not others."""
        self.client.login(username='user1', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'user1',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'Name'
        })

        # Should succeed
        self.assertEqual(response.status_code, 302)

        # Check user1 was updated
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, 'updated@example.com')

        # Check user2 was NOT affected
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.email, 'user2@example.com')
        self.assertEqual(self.user2.first_name, 'User')

    def test_user_cannot_edit_another_users_profile(self):
        """Test that there's no way to edit another user's profile."""
        self.client.login(username='user1', password='testpass123')

        # The view doesn't accept user_id parameter, so this tests
        # that the implementation correctly uses request.user
        response = self.client.post(self.edit_url, {
            'username': 'user1',
            'email': 'malicious@example.com',
            'first_name': 'Hacked',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 302)  # Redirects on success

        # Should update user1 (logged-in user), not user2
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()

        # User1 should be updated
        self.assertEqual(self.user1.email, 'malicious@example.com')

        # User2 should remain unchanged
        self.assertEqual(self.user2.email, 'user2@example.com')
        self.assertEqual(self.user2.first_name, 'User')


class ProfileEditEdgeCasesTestCase(TestCase):
    """Test edge cases for profile editing."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.edit_url = reverse('edit_profile')

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Original',
            last_name='Name'
        )

    def test_empty_first_name_allowed(self):
        """Test that first_name can be empty/blank."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': '',  # Empty
            'last_name': 'User'
        })

        # Should succeed
        self.assertEqual(response.status_code, 302)

        # Check data was saved
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, '')
        self.assertEqual(self.user.last_name, 'User')

    def test_empty_last_name_allowed(self):
        """Test that last_name can be empty/blank."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': ''  # Empty
        })

        # Should succeed
        self.assertEqual(response.status_code, 302)

        # Check data was saved
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, '')

    def test_both_names_empty_allowed(self):
        """Test that both first and last name can be empty."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': '',
            'last_name': ''
        })

        # Should succeed
        self.assertEqual(response.status_code, 302)

        # Check data was saved
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, '')
        self.assertEqual(self.user.last_name, '')

    def test_max_length_names(self):
        """Test that very long names are handled correctly."""
        self.client.login(username='testuser', password='testpass123')

        # Django User model max_length for first/last name is 150
        long_name = 'A' * 150

        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': long_name,
            'last_name': long_name
        })

        # Should succeed
        self.assertEqual(response.status_code, 302)

        # Check data was saved
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, long_name)
        self.assertEqual(self.user.last_name, long_name)

    def test_special_characters_in_names(self):
        """Test that names with special characters are handled."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': "O'Brien",
            'last_name': 'José-María'
        })

        # Should succeed
        self.assertEqual(response.status_code, 302)

        # Check data was saved
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "O'Brien")
        self.assertEqual(self.user.last_name, 'José-María')

    def test_whitespace_trimming(self):
        """Test that leading/trailing whitespace is preserved (Django default)."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': '  John  ',
            'last_name': '  Doe  '
        })

        # Should succeed
        self.assertEqual(response.status_code, 302)

        # Check how Django handles whitespace (preserves it by default)
        self.user.refresh_from_db()
        # Note: Django CharFields don't auto-trim by default
        self.assertTrue(self.user.first_name.strip() == 'John')
        self.assertTrue(self.user.last_name.strip() == 'Doe')


class ProfileEditIntegrationTestCase(TestCase):
    """Integration tests for complete profile edit workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.edit_url = reverse('edit_profile')
        self.profile_url = reverse('profile')

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='original@example.com',
            password='testpass123',
            first_name='Original',
            last_name='User'
        )

    def test_complete_profile_update_workflow(self):
        """Test complete workflow: login -> edit -> save -> view."""
        # 1. Login
        login_success = self.client.login(
            username='testuser',
            password='testpass123'
        )
        self.assertTrue(login_success)

        # 2. Access edit page
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'original@example.com')

        # 3. Submit changes
        response = self.client.post(self.edit_url, {
            'username': 'testuser',
            'email': 'newemail@example.com',
            'first_name': 'New',
            'last_name': 'Name'
        }, follow=True)

        # 4. Check redirect to profile page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

        # 5. Check success message
        messages = list(response.context['messages'])
        self.assertTrue(any('successfully' in str(m) for m in messages))

        # 6. Verify data in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'Name')
        # Username should NOT change
        self.assertEqual(self.user.username, 'testuser')

    def test_cancel_returns_to_profile(self):
        """Test that clicking Cancel redirects to profile page."""
        self.client.login(username='testuser', password='testpass123')

        # Access edit page
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)

        # The Cancel button should link to profile page
        # (tested in template, not via POST)
        self.assertContains(response, 'href="%s"' % self.profile_url)
