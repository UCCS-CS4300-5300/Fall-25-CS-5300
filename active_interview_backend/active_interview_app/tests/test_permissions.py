"""
Comprehensive tests for permission classes (RBAC - Issue #69)
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from unittest.mock import Mock

from active_interview_app.permissions import (
    IsAdminOrInterviewer,
    IsAdmin,
    IsOwnerOrPrivileged
)
from active_interview_app.models import UserProfile, QuestionBank


class IsAdminOrInterviewerTest(TestCase):
    """Tests for IsAdminOrInterviewer permission class"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsAdminOrInterviewer()
        self.view = Mock()

    def test_admin_user_has_permission(self):
        """Test that admin users are granted permission"""
        user = User.objects.create_user(username='admin', password='test')
        user.profile.role = UserProfile.ADMIN
        user.profile.save()

        request = self.factory.get('/')
        request.user = user

        self.assertTrue(self.permission.has_permission(request, self.view))

    def test_interviewer_user_has_permission(self):
        """Test that interviewer users are granted permission"""
        user = User.objects.create_user(
            username='interviewer', password='test')
        user.profile.role = UserProfile.INTERVIEWER
        user.profile.save()

        request = self.factory.get('/')
        request.user = user

        self.assertTrue(self.permission.has_permission(request, self.view))

    def test_candidate_user_denied_permission(self):
        """Test that candidate users are denied permission"""
        user = User.objects.create_user(username='candidate', password='test')
        user.profile.role = UserProfile.CANDIDATE
        user.profile.save()

        request = self.factory.get('/')
        request.user = user

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users are denied"""
        request = self.factory.get('/')
        request.user = Mock(is_authenticated=False)

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_user_without_profile_denied(self):
        """Test that users without profile are denied"""
        user = User.objects.create_user(username='noprofile', password='test')
        # Delete the auto-created profile
        if hasattr(user, 'profile'):
            user.profile.delete()

        request = self.factory.get('/')
        request.user = user

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_none_user_denied(self):
        """Test that None user is denied"""
        request = self.factory.get('/')
        request.user = None

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_permission_message(self):
        """Test that permission has appropriate message"""
        expected_message = 'Access denied. This feature is only available to Interviewers and Admins.'
        self.assertEqual(self.permission.message, expected_message)


class IsAdminTest(TestCase):
    """Tests for IsAdmin permission class"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsAdmin()
        self.view = Mock()

    def test_admin_user_has_permission(self):
        """Test that only admin users are granted permission"""
        user = User.objects.create_user(username='admin', password='test')
        user.profile.role = UserProfile.ADMIN
        user.profile.save()

        request = self.factory.get('/')
        request.user = user

        self.assertTrue(self.permission.has_permission(request, self.view))

    def test_interviewer_user_denied(self):
        """Test that interviewer users are denied"""
        user = User.objects.create_user(
            username='interviewer', password='test')
        user.profile.role = UserProfile.INTERVIEWER
        user.profile.save()

        request = self.factory.get('/')
        request.user = user

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_candidate_user_denied(self):
        """Test that candidate users are denied"""
        user = User.objects.create_user(username='candidate', password='test')
        user.profile.role = UserProfile.CANDIDATE
        user.profile.save()

        request = self.factory.get('/')
        request.user = user

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users are denied"""
        request = self.factory.get('/')
        request.user = Mock(is_authenticated=False)

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_user_without_profile_denied(self):
        """Test that users without profile are denied"""
        user = User.objects.create_user(username='noprofile', password='test')
        # Delete the auto-created profile
        if hasattr(user, 'profile'):
            user.profile.delete()

        request = self.factory.get('/')
        request.user = user

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_none_user_denied(self):
        """Test that None user is denied"""
        request = self.factory.get('/')
        request.user = None

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_permission_message(self):
        """Test that permission has appropriate message"""
        expected_message = 'Access denied. This feature is only available to Admins.'
        self.assertEqual(self.permission.message, expected_message)


class IsOwnerOrPrivilegedTest(TestCase):
    """Tests for IsOwnerOrPrivileged permission class"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsOwnerOrPrivileged()
        self.view = Mock()

    def test_admin_can_access_any_object(self):
        """Test that admin users can access any object"""
        admin = User.objects.create_user(username='admin', password='test')
        admin.profile.role = UserProfile.ADMIN
        admin.profile.save()

        other_user = User.objects.create_user(
            username='other', password='test')
        obj = QuestionBank.objects.create(name='Test Bank', owner=other_user)

        request = self.factory.get('/')
        request.user = admin

        self.assertTrue(self.permission.has_object_permission(
            request, self.view, obj))

    def test_interviewer_can_access_any_object(self):
        """Test that interviewer users can access any object"""
        interviewer = User.objects.create_user(
            username='interviewer', password='test')
        interviewer.profile.role = UserProfile.INTERVIEWER
        interviewer.profile.save()

        other_user = User.objects.create_user(
            username='other', password='test')
        obj = QuestionBank.objects.create(name='Test Bank', owner=other_user)

        request = self.factory.get('/')
        request.user = interviewer

        self.assertTrue(self.permission.has_object_permission(
            request, self.view, obj))

    def test_owner_can_access_own_object_with_owner_attr(self):
        """Test that users can access objects they own (owner attribute)"""
        user = User.objects.create_user(username='user', password='test')
        user.profile.role = UserProfile.CANDIDATE
        user.profile.save()

        obj = QuestionBank.objects.create(name='My Bank', owner=user)

        request = self.factory.get('/')
        request.user = user

        self.assertTrue(self.permission.has_object_permission(
            request, self.view, obj))

    def test_owner_can_access_own_object_with_user_attr(self):
        """Test that users can access objects they own (user attribute)"""
        user = User.objects.create_user(username='user', password='test')
        user.profile.role = UserProfile.CANDIDATE
        user.profile.save()

        # Create mock object with 'user' attribute instead of 'owner'
        obj = Mock()
        obj.user = user
        delattr(obj, 'owner')  # Ensure no 'owner' attribute

        request = self.factory.get('/')
        request.user = user

        self.assertTrue(self.permission.has_object_permission(
            request, self.view, obj))

    def test_candidate_cannot_access_others_object(self):
        """Test that candidate users cannot access other users' objects"""
        user = User.objects.create_user(username='user', password='test')
        user.profile.role = UserProfile.CANDIDATE
        user.profile.save()

        other_user = User.objects.create_user(
            username='other', password='test')
        obj = QuestionBank.objects.create(name='Other Bank', owner=other_user)

        request = self.factory.get('/')
        request.user = user

        self.assertFalse(self.permission.has_object_permission(
            request, self.view, obj))

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users are denied"""
        user = User.objects.create_user(username='owner', password='test')
        obj = QuestionBank.objects.create(name='Test Bank', owner=user)

        request = self.factory.get('/')
        request.user = Mock(is_authenticated=False)

        self.assertFalse(self.permission.has_object_permission(
            request, self.view, obj))

    def test_user_without_profile_denied(self):
        """Test that users without profile are denied"""
        owner = User.objects.create_user(username='owner', password='test')
        obj = QuestionBank.objects.create(name='Test Bank', owner=owner)

        # Create a user without profile for the request
        user = User.objects.create_user(username='noprofile', password='test')
        # Delete the auto-created profile
        if hasattr(user, 'profile'):
            user.profile.delete()

        request = self.factory.get('/')
        request.user = user

        self.assertFalse(self.permission.has_object_permission(
            request, self.view, obj))

    def test_none_user_denied(self):
        """Test that None user is denied"""
        user = User.objects.create_user(username='owner', password='test')
        obj = QuestionBank.objects.create(name='Test Bank', owner=user)

        request = self.factory.get('/')
        request.user = None

        self.assertFalse(self.permission.has_object_permission(
            request, self.view, obj))

    def test_object_without_owner_or_user_denied(self):
        """Test that objects without owner or user attribute are denied for candidates"""
        user = User.objects.create_user(username='user', password='test')
        user.profile.role = UserProfile.CANDIDATE
        user.profile.save()

        # Create mock object without owner or user attributes
        obj = Mock(spec=[])

        request = self.factory.get('/')
        request.user = user

        self.assertFalse(self.permission.has_object_permission(
            request, self.view, obj))

    def test_permission_message(self):
        """Test that permission has appropriate message"""
        expected_message = 'Access denied. You can only access your own resources.'
        self.assertEqual(self.permission.message, expected_message)
