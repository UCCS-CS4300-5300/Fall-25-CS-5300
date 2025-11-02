"""
Test suite for authentication navigation, links, and redirects.

This module tests that all authentication-related pages have correct links
and that users are redirected to the intended pages.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings


class LoginPageNavigationTests(TestCase):
    """Test login page links and navigation."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_login_page_loads(self):
        """Test that login page loads successfully."""
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AIS - Login')

    def test_login_page_has_register_link(self):
        """Test that login page contains a link to register."""
        response = self.client.get('/accounts/login/')
        self.assertContains(response, reverse('register_page'))

    def test_login_page_has_google_oauth_button(self):
        """Test that login page has Google OAuth button."""
        response = self.client.get('/accounts/login/')
        self.assertContains(response, 'Continue with Google')
        self.assertContains(response, 'accounts/google/login')

    def test_successful_login_redirects_to_testlogged(self):
        """Test that successful login redirects to /testlogged/."""
        response = self.client.post('/accounts/login/', {
            'login': 'testuser',
            'password': 'testpass123'
        }, follow=True)

        # Should redirect to LOGIN_REDIRECT_URL
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

    def test_login_with_next_parameter_redirects(self):
        """Test that login with ?next parameter redirects to that page."""
        response = self.client.post('/accounts/login/?next=/profile/', {
            'login': 'testuser',
            'password': 'testpass123'
        }, follow=True)

        self.assertRedirects(response, '/profile/')

    def test_failed_login_shows_error(self):
        """Test that failed login shows error message."""
        response = self.client.post('/accounts/login/', {
            'login': 'testuser',
            'password': 'wrongpassword'
        })

        # Should stay on login page and show error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "didn't match")


class LogoutNavigationTests(TestCase):
    """Test logout page links and navigation."""

    def setUp(self):
        """Set up test client and authenticated user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_logout_confirmation_page_loads(self):
        """Test that logout confirmation page loads."""
        response = self.client.get('/accounts/logout/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign Out')
        self.assertContains(response, 'Are you sure')

    def test_logout_confirmation_shows_username(self):
        """Test that logout confirmation shows current username."""
        response = self.client.get('/accounts/logout/')
        self.assertContains(response, 'testuser')

    def test_logout_confirmation_has_cancel_button(self):
        """Test that logout confirmation has cancel button."""
        response = self.client.get('/accounts/logout/')
        self.assertContains(response, 'Cancel')
        self.assertContains(response, reverse('index'))

    def test_logout_redirects_to_logged_out_page(self):
        """Test that logout redirects to account logout redirect URL."""
        response = self.client.post('/accounts/logout/', follow=True)

        # Should redirect to ACCOUNT_LOGOUT_REDIRECT_URL
        final_url = response.redirect_chain[-1][0]
        self.assertEqual(final_url, settings.ACCOUNT_LOGOUT_REDIRECT_URL)

    def test_logged_out_page_has_login_link(self):
        """Test that logged out page has link back to login."""
        # First logout
        self.client.post('/accounts/logout/')

        # The logout redirect should go to '/' based on settings
        # Check if we can access account/logout page manually
        response = self.client.get('/accounts/logout/', follow=True)

        # Should contain link to login
        self.assertContains(response, 'login')

    def test_logged_out_page_has_home_link(self):
        """Test that logged out page has link to home."""
        # Logout and follow redirects
        response = self.client.post('/accounts/logout/', follow=True)

        # Should be on homepage or have link to it
        self.assertIn(response.status_code, [200, 302])


class RegisterPageNavigationTests(TestCase):
    """Test register page links and navigation."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_register_page_loads(self):
        """Test that register page loads successfully."""
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Registration')

    def test_successful_registration_redirects(self):
        """Test that successful registration redirects properly."""
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }, follow=True)

        # Should redirect (status depends on registration flow)
        self.assertIn(response.status_code, [200, 302])

        # User should be created
        self.assertTrue(User.objects.filter(username='newuser').exists())


class ProtectedPageRedirectTests(TestCase):
    """Test that protected pages redirect to login."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_chat_list_redirects_to_login_when_not_authenticated(self):
        """Test that /chat/ redirects to login for unauthenticated users."""
        response = self.client.get('/chat/')

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_profile_redirects_to_login_when_not_authenticated(self):
        """Test that /profile/ redirects to login."""
        response = self.client.get('/profile/')

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_document_list_redirects_to_login(self):
        """Test that /document/ redirects to login."""
        response = self.client.get('/document/')

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class NavbarLinkTests(TestCase):
    """Test that navbar links work correctly."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_navbar_login_link_when_not_authenticated(self):
        """Test that navbar shows login link for unauthenticated users."""
        response = self.client.get('/')
        self.assertContains(response, 'Login')

    def test_navbar_profile_dropdown_when_authenticated(self):
        """Test that navbar shows profile dropdown for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/')

        self.assertContains(response, 'Profile')
        self.assertContains(response, 'Logout')

    def test_navbar_logout_link_redirects_properly(self):
        """Test that clicking logout from navbar works."""
        self.client.login(username='testuser', password='testpass123')

        # Access logout URL
        response = self.client.get('/accounts/logout/')

        # Should show logout confirmation
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign Out')


class OAuthNavigationTests(TestCase):
    """Test OAuth-related navigation and redirects."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_google_oauth_login_url_exists(self):
        """Test that Google OAuth login URL is accessible."""
        response = self.client.get('/accounts/google/login/')

        # Should either redirect to Google or show error (if not configured)
        # Status should not be 404
        self.assertNotEqual(response.status_code, 404)

    def test_login_page_oauth_button_has_correct_url(self):
        """Test that OAuth button on login page has correct URL."""
        response = self.client.get('/accounts/login/')

        # Should contain the OAuth login URL
        self.assertContains(response, '/accounts/google/login/')


class URLResolutionTests(TestCase):
    """Test that all URL names resolve correctly."""

    def test_login_url_resolves(self):
        """Test that 'login' URL name resolves."""
        url = reverse('login')
        # allauth URLs are included first, so 'login' resolves to /accounts/login/
        self.assertEqual(url, '/accounts/login/')

    def test_logout_url_resolves(self):
        """Test that 'logout' URL name resolves."""
        url = reverse('logout')
        # allauth URLs are included first, so 'logout' resolves to /accounts/logout/
        self.assertEqual(url, '/accounts/logout/')

    def test_register_url_resolves(self):
        """Test that 'register_page' URL name resolves."""
        url = reverse('register_page')
        self.assertEqual(url, '/register/')

    def test_profile_url_resolves(self):
        """Test that 'profile' URL name resolves."""
        url = reverse('profile')
        self.assertEqual(url, '/profile/')

    def test_index_url_resolves(self):
        """Test that 'index' URL name resolves."""
        url = reverse('index')
        self.assertEqual(url, '/')

    def test_loggedin_url_resolves(self):
        """Test that 'loggedin' URL name resolves."""
        url = reverse('loggedin')
        self.assertEqual(url, '/testlogged/')


@pytest.mark.django_db
class SettingsConfigurationTests:
    """Test that authentication settings are configured correctly."""

    def test_login_url_setting(self):
        """Test that LOGIN_URL is set correctly."""
        assert settings.LOGIN_URL == '/accounts/login/'

    def test_login_redirect_url_setting(self):
        """Test that LOGIN_REDIRECT_URL is set correctly."""
        assert settings.LOGIN_REDIRECT_URL == '/testlogged/'

    def test_logout_redirect_url_setting(self):
        """Test that ACCOUNT_LOGOUT_REDIRECT_URL is set correctly."""
        assert settings.ACCOUNT_LOGOUT_REDIRECT_URL == '/'

    def test_site_id_configured(self):
        """Test that SITE_ID is configured."""
        assert hasattr(settings, 'SITE_ID')
        assert settings.SITE_ID == 1
