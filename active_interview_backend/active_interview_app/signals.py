"""
Django Signals for Active Interview App

This module contains general application signals.
For spending-related signals, see spending_signals.py (Issue #11, #15.10).
"""

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group


@receiver(post_migrate)
def ensure_average_role_group(sender, **kwargs):
    """Ensure the average_role group exists after migrations."""
    Group.objects.get_or_create(name='average_role')
