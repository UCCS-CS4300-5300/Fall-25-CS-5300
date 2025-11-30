"""
Custom adapters for django-allauth to handle Google OAuth authentication.
"""
import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import Group
from .models import UserProfile

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to handle user creation and authentication via Google OAuth.

    Implements the acceptance criteria:
    - Check database for existing user with Google email
    - Existing user → session created
    - New user → record created with default profile data
    """

    def pre_social_login(self, request, sociallogin):
        """
        Invoked after a user successfully authenticates via a social provider,
        but before the login is processed.

        This checks if a user with this email already exists.
        """
        # If user is already logged in, do nothing
        if sociallogin.is_existing:
            return

        # Try to find existing user by email
        try:
            email = sociallogin.account.extra_data.get('email')
            if email:
                # Check if user with this email exists
                from django.contrib.auth.models import User
                existing_user = User.objects.filter(email=email).first()

                if existing_user:
                    # Connect the social account to the existing user
                    sociallogin.connect(request, existing_user)
        except Exception as e:
            # If anything goes wrong, log it and let allauth handle it normally
            logger.warning(
                f"Failed to connect social account to existing user: {e}"
            )

    def save_user(self, request, sociallogin, form=None):
        """
        Saves a new user when signing up via Google OAuth.

        This method is called when creating a new user account.
        """
        user = super().save_user(request, sociallogin, form)

        # Get the provider (e.g., 'google')
        provider = sociallogin.account.provider

        # Create or update the user profile with the auth provider
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.auth_provider = provider
        profile.save()

        # Add user to the default group (same as regular registration)
        group, created = Group.objects.get_or_create(name='average_role')
        user.groups.add(group)

        return user

    def populate_user(self, request, sociallogin, data):
        """
        Populates user information from social provider data.
        """
        user = super().populate_user(request, sociallogin, data)

        # Google provides first_name and last_name
        if not user.first_name and 'given_name' in data:
            user.first_name = data['given_name']

        if not user.last_name and 'family_name' in data:
            user.last_name = data['family_name']

        # If no username is set, use the part before @ in email
        if not user.username and user.email:
            user.username = user.email.split('@')[0]

        return user
