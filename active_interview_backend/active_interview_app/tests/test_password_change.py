"""
Tests for password change functionality.

This module tests the password change feature, including:
- Access to password change page
- Successful password change
- Password validation
- Redirection after success
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class PasswordChangeTestCase(TestCase):
    """Test cases for password change functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.password_change_url = reverse('password_change')
        self.password_change_done_url = reverse('password_change_done')
        self.profile_url = reverse('profile')

        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPassword123!'
        )

    def test_password_change_page_requires_login(self):
        """Test that password change page requires authentication."""
        response = self.client.get(self.password_change_url)

        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_password_change_page_loads_for_authenticated_user(self):
        """Test that authenticated users can access password change page."""
        self.client.login(username='testuser', password='OldPassword123!')
        response = self.client.get(self.password_change_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'registration/password_change_form.html')

    def test_successful_password_change(self):
        """Test that users can successfully change their password."""
        self.client.login(username='testuser', password='OldPassword123!')

        response = self.client.post(self.password_change_url, {
            'old_password': 'OldPassword123!',
            'new_password1': 'NewPassword456!',
            'new_password2': 'NewPassword456!',
        })

        # Should redirect to password change done page
        self.assertEqual(response.status_code, 302)
        self.assertIn('password_change/done', response.url)

        # User should be able to login with new password
        self.client.logout()
        login_successful = self.client.login(
            username='testuser',
            password='NewPassword456!'
        )
        self.assertTrue(login_successful)

    def test_password_change_requires_correct_old_password(self):
        """Test that password change requires the correct old password."""
        self.client.login(username='testuser', password='OldPassword123!')

        response = self.client.post(self.password_change_url, {
            'old_password': 'WrongPassword!',
            'new_password1': 'NewPassword456!',
            'new_password2': 'NewPassword456!',
        })

        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        # Check that there's an error on the old_password field
        self.assertIn('old_password', response.context['form'].errors)

    def test_password_change_requires_matching_passwords(self):
        """Test that new password and confirmation must match."""
        self.client.login(username='testuser', password='OldPassword123!')

        response = self.client.post(self.password_change_url, {
            'old_password': 'OldPassword123!',
            'new_password1': 'NewPassword456!',
            'new_password2': 'DifferentPassword789!',
        })

        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        # Check that there's an error on the new_password2 field
        self.assertIn('new_password2', response.context['form'].errors)

    def test_password_change_validates_password_strength(self):
        """Test that weak passwords are rejected."""
        self.client.login(username='testuser', password='OldPassword123!')

        response = self.client.post(self.password_change_url, {
            'old_password': 'OldPassword123!',
            'new_password1': '123',  # Too short
            'new_password2': '123',
        })

        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        # Check that there's an error on new_password2
        self.assertIn('new_password2', response.context['form'].errors)

    def test_password_change_done_page_loads(self):
        """Test that password change done page loads correctly."""
        self.client.login(username='testuser', password='OldPassword123!')
        response = self.client.get(self.password_change_done_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'registration/password_change_done.html')

    def test_profile_page_contains_password_change_link(self):
        """Test that profile page has a link to password change."""
        self.client.login(username='testuser', password='OldPassword123!')
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'password_change')
        self.assertContains(response, 'Change Password')

    def test_password_change_maintains_user_session(self):
        """Test that user remains logged in after password change."""
        self.client.login(username='testuser', password='OldPassword123!')

        response = self.client.post(self.password_change_url, {
            'old_password': 'OldPassword123!',
            'new_password1': 'NewPassword456!',
            'new_password2': 'NewPassword456!',
        }, follow=True)

        # User should still be authenticated
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'testuser')
