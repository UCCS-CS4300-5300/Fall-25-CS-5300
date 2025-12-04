"""Decorators package for active_interview_app."""

from .ratelimit_decorators import (
    ratelimit_default,
    ratelimit_strict,
    ratelimit_lenient,
    ratelimit_api
)

# Import RBAC decorators from the decorators.py module file
# Note: There's both a decorators.py file AND a decorators/ package in the same directory.
# When both exist, Python's import system finds the package first.
# We need to explicitly load the .py file using importlib.
import importlib.util
import os

# Get path to decorators.py file (sibling to this package directory)
_decorators_module_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'decorators.py'
)

# Load the decorators.py module
_spec = importlib.util.spec_from_file_location("rbac_decorators", _decorators_module_path)
_rbac_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rbac_module)

# Re-export RBAC decorators
admin_required = _rbac_module.admin_required
admin_or_interviewer_required = _rbac_module.admin_or_interviewer_required
role_required = _rbac_module.role_required
owner_or_privileged_required = _rbac_module.owner_or_privileged_required
check_user_permission = _rbac_module.check_user_permission

__all__ = [
    'ratelimit_default',
    'ratelimit_strict',
    'ratelimit_lenient',
    'ratelimit_api',
    'admin_required',
    'admin_or_interviewer_required',
    'role_required',
    'owner_or_privileged_required',
    'check_user_permission'
]
