"""
Role-based access control decorators.

These decorators provide permission checking for views based on user roles
defined in the UserProfile model.

Related to Issue #69 - RBAC implementation.
"""
from functools import wraps
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse


def role_required(*allowed_roles):
    """
    Decorator to require specific role(s) to access a view.

    Usage:
        @role_required('admin')
        @role_required('admin', 'interviewer')

    Args:
        allowed_roles: One or more role strings
            ('admin', 'interviewer', 'candidate')

    Returns:
        403 Forbidden if user doesn't have required role
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check authentication
            if not request.user.is_authenticated:
                # For API/AJAX requests, return 401
                is_api_request = (
                    request.headers.get('Accept') == 'application/json' or
                    request.path.startswith('/api/') or
                    request.path.startswith('/admin/') or
                    request.path.startswith('/candidates/')
                )
                if is_api_request:
                    return JsonResponse(
                        {'error': 'Unauthorized'}, status=401
                    )
                # For regular requests, redirect to login
                login_url = reverse('login')
                return HttpResponseRedirect(f"{login_url}?next={request.path}")

            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                return JsonResponse(
                    {'error': 'Forbidden: User profile not found'},
                    status=403
                )

            user_role = request.user.profile.role

            if user_role not in allowed_roles:
                # Return JSON response for API endpoints
                return JsonResponse(
                    {'error': 'Forbidden: Insufficient permissions'},
                    status=403
                )

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator to require admin role.

    Usage:
        @admin_required
        def my_view(request):
            ...
    """
    return role_required('admin')(view_func)


def admin_or_interviewer_required(view_func):
    """
    Decorator to require admin or interviewer role.

    Usage:
        @admin_or_interviewer_required
        def my_view(request):
            ...
    """
    return role_required('admin', 'interviewer')(view_func)


def owner_or_privileged_required(get_owner_func):
    """
    Decorator to require user to be owner OR have admin/interviewer
    privileges.

    Usage:
        @owner_or_privileged_required(
            lambda request, user_id: User.objects.get(id=user_id)
        )
        def my_view(request, user_id):
            ...

    Args:
        get_owner_func: Function that takes (request, *args, **kwargs)
            and returns the owner User object to check against

    Returns:
        403 Forbidden if user is not owner and doesn't have privileges
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check authentication
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Unauthorized'}, status=401)

            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                return JsonResponse(
                    {'error': 'Forbidden: User profile not found'},
                    status=403
                )

            user_role = request.user.profile.role

            # Admins and interviewers always have access
            if user_role in ['admin', 'interviewer']:
                return view_func(request, *args, **kwargs)

            # Check if user is the owner
            try:
                owner = get_owner_func(request, *args, **kwargs)
                if request.user == owner:
                    return view_func(request, *args, **kwargs)
            except Exception:
                # If we can't determine ownership, deny access
                pass

            # Deny access
            return JsonResponse({'error': 'Forbidden'}, status=403)

        return wrapper
    return decorator


def check_user_permission(request, target_user_id, allow_self=True,
                          allow_admin=True, allow_interviewer=False):
    """
    Helper function to check if user has permission to access/modify
    another user's data.

    Args:
        request: Django request object
        target_user_id: ID of the user being accessed
        allow_self: Whether to allow if request.user.id == target_user_id
        allow_admin: Whether to allow admin role
        allow_interviewer: Whether to allow interviewer role

    Returns:
        True if permission granted, False otherwise
    """
    if not hasattr(request.user, 'profile'):
        return False

    user_role = request.user.profile.role

    # Check role-based permissions
    if allow_admin and user_role == 'admin':
        return True
    if allow_interviewer and user_role == 'interviewer':
        return True

    # Check if accessing own data
    if allow_self and str(request.user.id) == str(target_user_id):
        return True

    return False
