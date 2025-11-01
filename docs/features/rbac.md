# Role-Based Access Control (RBAC)

**Issue**: [#69](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/69)

Role-Based Access Control provides permission management through three distinct user roles.

## Overview

The RBAC system implements a three-tier permission structure:
- **Admin** - Full system access, can manage user roles
- **Interviewer** - Can view candidate profiles and interviews
- **Candidate** - Default role, can manage own profile and interviews

## User Roles

### Role Hierarchy

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | Administrator | All permissions, can update user roles |
| `interviewer` | Interviewer | View all candidate profiles, conduct interviews |
| `candidate` | Candidate (default) | Manage own profile and interviews only |

### Default Role

When a new user registers, they are automatically assigned the `candidate` role.

## Implementation

### Model: UserProfile

Location: `active_interview_app/models.py:11-66`

The `UserProfile` model extends Django's built-in `User` model with:
- `role`: User's permission level (admin/interviewer/candidate)
- `auth_provider`: Authentication method (local/google) - for OAuth compatibility
- Auto-creation via Django signals when a User is created

```python
# Access user role
user_role = request.user.profile.role

# Check if user is admin
if request.user.profile.role == 'admin':
    # Admin-only logic
```

### Decorators

Location: `active_interview_app/decorators.py`

#### `@admin_required`
Requires admin role to access the view.

```python
from active_interview_app.decorators import admin_required

@admin_required
def my_admin_view(request):
    # Only admins can access this
    pass
```

#### `@admin_or_interviewer_required`
Requires admin or interviewer role.

```python
from active_interview_app.decorators import admin_or_interviewer_required

@admin_or_interviewer_required
def view_candidate_data(request):
    # Admins and interviewers can access
    pass
```

#### `@role_required('role1', 'role2', ...)`
Requires one of the specified roles.

```python
from active_interview_app.decorators import role_required

@role_required('admin', 'interviewer')
def my_view(request):
    # Admins and interviewers can access
    pass
```

#### `check_user_permission()`
Helper function for custom permission checks.

```python
from active_interview_app.decorators import check_user_permission

def my_view(request, user_id):
    if check_user_permission(
        request, user_id,
        allow_self=True,
        allow_admin=True,
        allow_interviewer=False
    ):
        # User has permission
        pass
```

## API Endpoints

### Admin Endpoints

#### List All Users
```
GET /api/admin/users/
```
**Access**: Admin only

**Response**:
```json
{
  "users": [
    {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "candidate",
      "auth_provider": "local",
      "date_joined": "2025-01-01T12:00:00Z",
      "is_active": true
    }
  ]
}
```

#### Update User Role
```
PATCH /api/admin/users/<user_id>/role/
```
**Access**: Admin only

**Request Body**:
```json
{
  "role": "interviewer"
}
```

**Valid Roles**: `admin`, `interviewer`, `candidate`

**Response**:
```json
{
  "success": true,
  "user_id": 123,
  "username": "johndoe",
  "role": "interviewer"
}
```

### Candidate Profile Endpoints

#### View Candidate Profile
```
GET /api/candidates/<user_id>/
```
**Access**:
- Owner (self)
- Admin
- Interviewer

**Response**:
```json
{
  "id": 123,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "candidate",
  "auth_provider": "local",
  "date_joined": "2025-01-01T12:00:00Z"
}
```

#### Update Candidate Profile
```
PATCH /api/candidates/<user_id>/update/
```
**Access**: Owner (self) only

**Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "newemaiL@example.com"
}
```

**Response**:
```json
{
  "success": true,
  "user_id": 123,
  "updated_fields": ["first_name", "last_name", "email"],
  "first_name": "John",
  "last_name": "Smith",
  "email": "newemail@example.com"
}
```

## Permission Matrix

| Action | Candidate | Interviewer | Admin |
|--------|-----------|-------------|-------|
| View own profile | ✅ | ✅ | ✅ |
| Update own profile | ✅ | ✅ | ✅ |
| View other profiles | ❌ | ✅ | ✅ |
| Update other profiles | ❌ | ❌ | ❌ |
| List all users | ❌ | ❌ | ✅ |
| Update user roles | ❌ | ❌ | ✅ |

## Error Responses

### 401 Unauthorized
User is not authenticated.

```json
{
  "error": "Unauthorized"
}
```

### 403 Forbidden
User lacks required permissions.

```json
{
  "error": "Forbidden: Insufficient permissions"
}
```

### 404 Not Found
Resource not found.

```json
{
  "error": "User not found"
}
```

### 400 Bad Request
Invalid input data.

```json
{
  "error": "Invalid role. Must be one of: admin, interviewer, candidate"
}
```

## Testing

Location: `active_interview_app/tests/test_rbac.py`

**Test Coverage**: 25 comprehensive tests covering:
- UserProfile model creation and defaults
- Role field validation
- Admin user management endpoints
- Candidate profile access control
- Permission decorators
- Edge cases and error handling

Run tests:
```bash
cd active_interview_backend
python manage.py test active_interview_app.tests.test_rbac
```

## OAuth Compatibility

The `UserProfile` model includes an `auth_provider` field to support OAuth authentication.

When merged with OAuth implementation, users authenticated via Google will have:
- `auth_provider`: `'google'`
- `role`: `'candidate'` (default)
- Roles can still be updated by admins

## Migration

The RBAC feature includes a migration that:
1. Creates the `UserProfile` table
2. Sets up the OneToOne relationship with `User`
3. Creates signals to auto-create profiles for new users

Existing users will have profiles created automatically when they next log in.

## Django Admin vs RBAC Admin

**Important**: RBAC admin role is **separate** from Django's built-in admin system.

### Django Admin (`is_staff`, `is_superuser`)
- Built-in Django database administration interface
- Access to `/admin/` (Django admin UI)
- Used by developers and DBAs for technical management
- Direct database record manipulation
- Created via `python manage.py createsuperuser`
- **Can change user roles** through `/admin/` → User Profiles

### RBAC Admin (`profile.role = 'admin'`)
- Application-level role for business administration
- Access to `/api/admin/users/` and related endpoints
- Used by business administrators for user management
- **Cannot** access Django admin interface (`/admin/`)
- **Can change user roles** through REST API endpoints

### Independence

These systems are **completely independent**:

| User Type | `is_superuser` | `profile.role` | Access `/admin/` | Change Roles via `/admin/` | Access `/api/admin/*` | Change Roles via API |
|-----------|----------------|----------------|-----------------|---------------------------|----------------------|---------------------|
| Developer | `True` | `'candidate'` | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| Business Admin | `False` | `'admin'` | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| System Admin | `True` | `'admin'` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Regular User | `False` | `'candidate'` | ❌ No | ❌ No | ❌ No | ❌ No |

**Recommendation**: Most users should only have **one** admin type. Use RBAC admin for business users who need to manage roles without database access.

## Security Considerations

1. **Default Role**: All new users default to `candidate` for principle of least privilege
2. **API-Only Updates**: User roles can only be updated via API by admins
3. **No Self-Promotion**: Users cannot change their own roles
4. **Profile Ownership**: Only profile owners can update their own data
5. **Admin Segregation**: Only admins can access admin endpoints
6. **Separation of Concerns**: Django admin and RBAC admin are independent systems

## Future Enhancements

Potential improvements for future iterations:
- Fine-grained permissions beyond roles
- Department/team-based access control
- Audit logging for role changes
- Temporary role assignments
- Role expiration dates

## Related Documentation

- [Models Documentation](../architecture/models.md#userprofile)
- [API Reference](../architecture/api.md#rbac-endpoints)
- [Testing Guide](../setup/testing.md)
- [OAuth Implementation](./oauth.md) (when available)

## Troubleshooting

### User has no profile

**Symptom**: `User has no attribute 'profile'`

**Solution**: Ensure migrations have run:
```bash
python manage.py migrate
```

### Permission denied unexpectedly

**Symptom**: 403 errors for operations that should be allowed

**Solution**:
1. Check user's role: `user.profile.role`
2. Verify decorator usage matches required permission
3. Check if user is authenticated

### Role update fails

**Symptom**: Cannot update user roles

**Solution**:
1. Ensure requesting user is admin
2. Verify role value is valid ('admin', 'interviewer', or 'candidate')
3. Check request format (PATCH with JSON body)
