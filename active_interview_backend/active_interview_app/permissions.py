"""
Django REST Framework permission classes for role-based access control.

These permissions work with the UserProfile role system to restrict
API access based on user roles.

Related to Issue #69 - RBAC implementation.
"""
from rest_framework import permissions


class IsAdminOrInterviewer(permissions.BasePermission):
    """
    Permission class that allows access only to users with
    'admin' or 'interviewer' role.

    Used for question bank and interview template features that
    should only be accessible to interviewers and admins.
    """
    message = (
        'Access denied. This feature is only available to '
        'Interviewers and Admins.')

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']


class IsAdmin(permissions.BasePermission):
    """
    Permission class that allows access only to users with 'admin' role.
    """
    message = 'Access denied. This feature is only available to Admins.'

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'


class IsOwnerOrPrivileged(permissions.BasePermission):
    """
    Permission class that allows access to owners of objects,
    or users with admin/interviewer privileges.
    """
    message = 'Access denied. You can only access your own resources.'

    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        user_role = request.user.profile.role

        # Admins and interviewers have full access
        if user_role in ['admin', 'interviewer']:
            return True

        # Otherwise, check if user is the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False
