"""
Django REST Framework permission classes for role-based access control.

These permissions work with the UserProfile role system to restrict
API access based on user roles.

Related to Issue #69 - RBAC implementation.
"""
from rest_framework import permissions
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


class IsAdminOrInterviewer(permissions.BasePermission):
    """
    Permission class that allows access only to users with
    'admin' or 'interviewer' role.

    Used for question bank and interview template features that
    should only be accessible to interviewers and admins.
    """
    message = None

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_orig(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_1(self, request, view):
        # Check if user is authenticated
        if not request.user and not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_2(self, request, view):
        # Check if user is authenticated
        if request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_3(self, request, view):
        # Check if user is authenticated
        if not request.user or request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_4(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return True

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_5(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_6(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(None, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_7(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, None):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_8(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr('profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_9(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, ):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_10(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'XXprofileXX'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_11(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'PROFILE'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_12(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return True

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_13(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = None
        return user_role in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_14(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role not in ['admin', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_15(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['XXadminXX', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_16(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['ADMIN', 'interviewer']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_17(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'XXinterviewerXX']

    def xǁIsAdminOrInterviewerǁhas_permission__mutmut_18(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin or interviewer role
        user_role = request.user.profile.role
        return user_role in ['admin', 'INTERVIEWER']
    
    xǁIsAdminOrInterviewerǁhas_permission__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁIsAdminOrInterviewerǁhas_permission__mutmut_1': xǁIsAdminOrInterviewerǁhas_permission__mutmut_1, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_2': xǁIsAdminOrInterviewerǁhas_permission__mutmut_2, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_3': xǁIsAdminOrInterviewerǁhas_permission__mutmut_3, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_4': xǁIsAdminOrInterviewerǁhas_permission__mutmut_4, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_5': xǁIsAdminOrInterviewerǁhas_permission__mutmut_5, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_6': xǁIsAdminOrInterviewerǁhas_permission__mutmut_6, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_7': xǁIsAdminOrInterviewerǁhas_permission__mutmut_7, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_8': xǁIsAdminOrInterviewerǁhas_permission__mutmut_8, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_9': xǁIsAdminOrInterviewerǁhas_permission__mutmut_9, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_10': xǁIsAdminOrInterviewerǁhas_permission__mutmut_10, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_11': xǁIsAdminOrInterviewerǁhas_permission__mutmut_11, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_12': xǁIsAdminOrInterviewerǁhas_permission__mutmut_12, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_13': xǁIsAdminOrInterviewerǁhas_permission__mutmut_13, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_14': xǁIsAdminOrInterviewerǁhas_permission__mutmut_14, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_15': xǁIsAdminOrInterviewerǁhas_permission__mutmut_15, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_16': xǁIsAdminOrInterviewerǁhas_permission__mutmut_16, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_17': xǁIsAdminOrInterviewerǁhas_permission__mutmut_17, 
        'xǁIsAdminOrInterviewerǁhas_permission__mutmut_18': xǁIsAdminOrInterviewerǁhas_permission__mutmut_18
    }
    
    def has_permission(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁIsAdminOrInterviewerǁhas_permission__mutmut_orig"), object.__getattribute__(self, "xǁIsAdminOrInterviewerǁhas_permission__mutmut_mutants"), args, kwargs, self)
        return result 
    
    has_permission.__signature__ = _mutmut_signature(xǁIsAdminOrInterviewerǁhas_permission__mutmut_orig)
    xǁIsAdminOrInterviewerǁhas_permission__mutmut_orig.__name__ = 'xǁIsAdminOrInterviewerǁhas_permission'


class IsAdmin(permissions.BasePermission):
    """
    Permission class that allows access only to users with 'admin' role.
    """
    message = 'Access denied. This feature is only available to Admins.'

    def xǁIsAdminǁhas_permission__mutmut_orig(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_1(self, request, view):
        # Check if user is authenticated
        if not request.user and not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_2(self, request, view):
        # Check if user is authenticated
        if request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_3(self, request, view):
        # Check if user is authenticated
        if not request.user or request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_4(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return True

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_5(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_6(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(None, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_7(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, None):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_8(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr('profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_9(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, ):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_10(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'XXprofileXX'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_11(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'PROFILE'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_12(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return True

        # Check if user has admin role
        return request.user.profile.role == 'admin'

    def xǁIsAdminǁhas_permission__mutmut_13(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role != 'admin'

    def xǁIsAdminǁhas_permission__mutmut_14(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'XXadminXX'

    def xǁIsAdminǁhas_permission__mutmut_15(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        # Check if user has admin role
        return request.user.profile.role == 'ADMIN'
    
    xǁIsAdminǁhas_permission__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁIsAdminǁhas_permission__mutmut_1': xǁIsAdminǁhas_permission__mutmut_1, 
        'xǁIsAdminǁhas_permission__mutmut_2': xǁIsAdminǁhas_permission__mutmut_2, 
        'xǁIsAdminǁhas_permission__mutmut_3': xǁIsAdminǁhas_permission__mutmut_3, 
        'xǁIsAdminǁhas_permission__mutmut_4': xǁIsAdminǁhas_permission__mutmut_4, 
        'xǁIsAdminǁhas_permission__mutmut_5': xǁIsAdminǁhas_permission__mutmut_5, 
        'xǁIsAdminǁhas_permission__mutmut_6': xǁIsAdminǁhas_permission__mutmut_6, 
        'xǁIsAdminǁhas_permission__mutmut_7': xǁIsAdminǁhas_permission__mutmut_7, 
        'xǁIsAdminǁhas_permission__mutmut_8': xǁIsAdminǁhas_permission__mutmut_8, 
        'xǁIsAdminǁhas_permission__mutmut_9': xǁIsAdminǁhas_permission__mutmut_9, 
        'xǁIsAdminǁhas_permission__mutmut_10': xǁIsAdminǁhas_permission__mutmut_10, 
        'xǁIsAdminǁhas_permission__mutmut_11': xǁIsAdminǁhas_permission__mutmut_11, 
        'xǁIsAdminǁhas_permission__mutmut_12': xǁIsAdminǁhas_permission__mutmut_12, 
        'xǁIsAdminǁhas_permission__mutmut_13': xǁIsAdminǁhas_permission__mutmut_13, 
        'xǁIsAdminǁhas_permission__mutmut_14': xǁIsAdminǁhas_permission__mutmut_14, 
        'xǁIsAdminǁhas_permission__mutmut_15': xǁIsAdminǁhas_permission__mutmut_15
    }
    
    def has_permission(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁIsAdminǁhas_permission__mutmut_orig"), object.__getattribute__(self, "xǁIsAdminǁhas_permission__mutmut_mutants"), args, kwargs, self)
        return result 
    
    has_permission.__signature__ = _mutmut_signature(xǁIsAdminǁhas_permission__mutmut_orig)
    xǁIsAdminǁhas_permission__mutmut_orig.__name__ = 'xǁIsAdminǁhas_permission'


class IsOwnerOrPrivileged(permissions.BasePermission):
    """
    Permission class that allows access to owners of objects,
    or users with admin/interviewer privileges.
    """
    message = 'Access denied. You can only access your own resources.'

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_orig(self, request, view, obj):
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_1(self, request, view, obj):
        # Check if user is authenticated
        if not request.user and not request.user.is_authenticated:
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_2(self, request, view, obj):
        # Check if user is authenticated
        if request.user or not request.user.is_authenticated:
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_3(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or request.user.is_authenticated:
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_4(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return True

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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_5(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if hasattr(request.user, 'profile'):
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_6(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(None, 'profile'):
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_7(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, None):
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_8(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr('profile'):
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_9(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, ):
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_10(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'XXprofileXX'):
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_11(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'PROFILE'):
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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_12(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return True

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

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_13(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        user_role = None

        # Admins and interviewers have full access
        if user_role in ['admin', 'interviewer']:
            return True

        # Otherwise, check if user is the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_14(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        user_role = request.user.profile.role

        # Admins and interviewers have full access
        if user_role not in ['admin', 'interviewer']:
            return True

        # Otherwise, check if user is the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_15(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        user_role = request.user.profile.role

        # Admins and interviewers have full access
        if user_role in ['XXadminXX', 'interviewer']:
            return True

        # Otherwise, check if user is the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_16(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        user_role = request.user.profile.role

        # Admins and interviewers have full access
        if user_role in ['ADMIN', 'interviewer']:
            return True

        # Otherwise, check if user is the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_17(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        user_role = request.user.profile.role

        # Admins and interviewers have full access
        if user_role in ['admin', 'XXinterviewerXX']:
            return True

        # Otherwise, check if user is the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_18(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        user_role = request.user.profile.role

        # Admins and interviewers have full access
        if user_role in ['admin', 'INTERVIEWER']:
            return True

        # Otherwise, check if user is the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_19(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False

        user_role = request.user.profile.role

        # Admins and interviewers have full access
        if user_role in ['admin', 'interviewer']:
            return False

        # Otherwise, check if user is the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_20(self, request, view, obj):
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
        if hasattr(None, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_21(self, request, view, obj):
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
        if hasattr(obj, None):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_22(self, request, view, obj):
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
        if hasattr('owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_23(self, request, view, obj):
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
        if hasattr(obj, ):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_24(self, request, view, obj):
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
        if hasattr(obj, 'XXownerXX'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_25(self, request, view, obj):
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
        if hasattr(obj, 'OWNER'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_26(self, request, view, obj):
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
            return obj.owner != request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_27(self, request, view, obj):
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
        elif hasattr(None, 'user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_28(self, request, view, obj):
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
        elif hasattr(obj, None):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_29(self, request, view, obj):
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
        elif hasattr('user'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_30(self, request, view, obj):
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
        elif hasattr(obj, ):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_31(self, request, view, obj):
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
        elif hasattr(obj, 'XXuserXX'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_32(self, request, view, obj):
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
        elif hasattr(obj, 'USER'):
            return obj.user == request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_33(self, request, view, obj):
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
            return obj.user != request.user

        return False

    def xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_34(self, request, view, obj):
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

        return True
    
    xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_1': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_1, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_2': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_2, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_3': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_3, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_4': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_4, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_5': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_5, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_6': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_6, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_7': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_7, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_8': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_8, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_9': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_9, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_10': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_10, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_11': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_11, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_12': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_12, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_13': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_13, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_14': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_14, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_15': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_15, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_16': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_16, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_17': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_17, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_18': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_18, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_19': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_19, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_20': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_20, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_21': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_21, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_22': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_22, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_23': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_23, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_24': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_24, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_25': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_25, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_26': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_26, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_27': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_27, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_28': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_28, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_29': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_29, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_30': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_30, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_31': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_31, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_32': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_32, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_33': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_33, 
        'xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_34': xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_34
    }
    
    def has_object_permission(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_orig"), object.__getattribute__(self, "xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_mutants"), args, kwargs, self)
        return result 
    
    has_object_permission.__signature__ = _mutmut_signature(xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_orig)
    xǁIsOwnerOrPrivilegedǁhas_object_permission__mutmut_orig.__name__ = 'xǁIsOwnerOrPrivilegedǁhas_object_permission'
