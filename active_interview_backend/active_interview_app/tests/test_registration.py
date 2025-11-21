"""
Tests for user registration functionality.

This module tests the user registration process, including the fix for the
bug where registration would fail with a 500 error if the 'average_role'
group didn't exist in the database.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse


class UserRegistrationTestCase(TestCase):
    """Test cases for user registration."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.register_url = reverse('register_page')

    def test_signal_creates_average_role_group_on_migrate(self):
        """Test that the post_migrate signal creates the average_role group."""
        # The group should be created by the post_migrate signal
        # when the test database is set up
        group = Group.objects.filter(name='average_role').first()
        self.assertIsNotNone(
            group,
            "average_role group should be created by post_migrate signal"
        )

    def test_register_user_with_existing_group(self):
        """Test that registration works when average_role group exists."""
        # Ensure the group exists
        Group.objects.get_or_create(name='average_role')

        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })

        # Should redirect to login after successful registration
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

        # User should be created
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')

        # User should be in the average_role group
        self.assertTrue(
            user.groups.filter(name='average_role').exists(),
            "User should be added to average_role group"
        )

    def test_register_user_without_existing_group(self):
        """
        Test that registration works even when average_role group doesn't exist.

        This tests the fix for the bug where registration would fail with a
        500 error on a fresh production database without the average_role group.
        """
        # Delete the group to simulate fresh database
        Group.objects.filter(name='average_role').delete()

        # Verify group doesn't exist
        self.assertFalse(Group.objects.filter(name='average_role').exists())

        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'NewPass123!',
            'password2': 'NewPass123!',
        })

        # Should NOT return 500 error - should redirect to login
        self.assertEqual(
            response.status_code, 302,
            "Registration should succeed even without existing group"
        )
        self.assertIn('/accounts/login/', response.url)

        # User should be created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')

        # Group should be auto-created by get_or_create
        group = Group.objects.filter(name='average_role').first()
        self.assertIsNotNone(
            group,
            "average_role group should be created by get_or_create"
        )

        # User should be in the group
        self.assertTrue(
            user.groups.filter(name='average_role').exists(),
            "User should be added to the auto-created group"
        )

    def test_multiple_registrations_reuse_same_group(self):
        """Test that multiple user registrations reuse the same group."""
        # Delete existing group
        Group.objects.filter(name='average_role').delete()

        # Register first user
        self.client.post(self.register_url, {
            'username': 'user1',
            'email': 'user1@example.com',
            'password1': 'Pass123!',
            'password2': 'Pass123!',
        })

        # Register second user
        self.client.post(self.register_url, {
            'username': 'user2',
            'email': 'user2@example.com',
            'password1': 'Pass123!',
            'password2': 'Pass123!',
        })

        # Should only have one average_role group
        groups = Group.objects.filter(name='average_role')
        self.assertEqual(
            groups.count(), 1,
            "Only one average_role group should exist"
        )

        # Both users should be in the same group
        user1 = User.objects.get(username='user1')
        user2 = User.objects.get(username='user2')

        self.assertTrue(user1.groups.filter(name='average_role').exists())
        self.assertTrue(user2.groups.filter(name='average_role').exists())

        # They should be in the exact same group instance
        group = groups.first()
        self.assertIn(user1, group.user_set.all())
        self.assertIn(user2, group.user_set.all())
