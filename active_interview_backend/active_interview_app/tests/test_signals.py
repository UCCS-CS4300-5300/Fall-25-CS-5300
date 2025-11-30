from django.test import TestCase
from django.contrib.auth.models import Group
from unittest.mock import patch

from .. import signals


class SignalsTest(TestCase):
    def setUp(self):
        # Ensure a clean state for group
        Group.objects.filter(name='average_role').delete()

    def test_ensure_group_created(self):
        """Calling the receiver creates the 'average_role' group if missing."""
        # Precondition: group doesn't exist
        self.assertFalse(Group.objects.filter(name='average_role').exists())

        # Call the signal handler directly (sender is ignored by the handler)
        signals.ensure_average_role_group(sender=None)

        # Postcondition: group exists
        self.assertTrue(Group.objects.filter(name='average_role').exists())

    def test_ensure_group_idempotent(self):
        """Calling the handler multiple times does not create duplicates."""
        signals.ensure_average_role_group(sender=None)
        signals.ensure_average_role_group(sender=None)

        self.assertEqual(Group.objects.filter(name='average_role').count(), 1)

    @patch('active_interview_app.signals.Group.objects.get_or_create')
    def test_calls_get_or_create(self, mock_get_or_create):
        """Verify the handler uses Group.objects.get_or_create with the expected name."""
        signals.ensure_average_role_group(sender=None)
        mock_get_or_create.assert_called_with(name='average_role')
