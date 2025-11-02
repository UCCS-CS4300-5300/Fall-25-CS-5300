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

## Web Endpoints

### View User Profile

```
GET /user/<user_id>/profile/
```

Displays a user's profile information.

**Access**:
- Self (view own profile)
- Admin (view any profile)
- Interviewer (view any profile)

**Response**: HTML page displaying:
- Username
- Email
- Full name (if provided)
- Role
- Account creation date
- Authentication provider

**Use Cases**:
- Users viewing their own profile
- Interviewers viewing candidate profiles
- Admins viewing any user profile

**Example**:
```
GET /user/123/profile/
```

## Permission Matrix

| Action | Candidate | Interviewer | Admin |
|--------|-----------|-------------|-------|
| View own profile | ✅ | ✅ | ✅ |
| View other user profiles | ❌ | ✅ | ✅ |
| Request role change | ✅ | ✅ | ✅ |
| View role requests | ❌ | ❌ | ✅ |
| Approve/reject role requests | ❌ | ❌ | ✅ |
| Search for candidates | ❌ | ✅ | ✅ |
| Update user roles (via admin panel) | ❌ | ❌ | Superuser only |

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

## Role Change Request System

### Overview

Candidates can request to become interviewers through a self-service workflow.
Admins review and approve/reject these requests through a dedicated interface.

### User Flow

#### For Candidates

1. Navigate to Profile page
2. Click "Request Interviewer Role" button
3. Fill out request form with reason (optional)
4. Submit request
5. Profile page shows "pending request" status
6. Receive notification when admin reviews

**Note**: Users cannot submit multiple pending requests. They must wait for
admin review before submitting another.

#### For Admins

1. Navigate to "Role Requests" from navbar
2. View pending requests with user details and reason
3. For each request:
   - **Approve**: User's role is immediately updated to interviewer
   - **Reject**: User remains candidate, can add admin notes explaining why

### Endpoints

#### Submit Role Request
```
POST /profile/request-role-change/
```
**Access**: Authenticated users (typically candidates)

**Form Data**:
- `requested_role`: Role being requested (e.g., "interviewer")
- `reason`: (Optional) Explanation for request

**Response**: Redirects to profile page with success message

#### View Role Requests (Admin)
```
GET /role-requests/
```
**Access**: Admin only

**Returns**: HTML page with:
- List of pending requests
- List of recently reviewed requests

#### Review Role Request (Admin)
```
POST /role-requests/<request_id>/review/
```
**Access**: Admin only

**Form Data** (Approve):
```
{
  "action": "approve"
}
```

**Form Data** (Reject):
```
{
  "action": "reject",
  "admin_notes": "Optional feedback for user"
}
```

**Response**: Redirects to role requests list with success message

**Effects**:
- **Approve**: Updates user's role in UserProfile
- **Reject**: Request marked as rejected, no role change

### Database Model: RoleChangeRequest

Location: `active_interview_app/models.py:216-286`

**Fields**:
- `user`: ForeignKey to User making request
- `requested_role`: Role being requested
- `current_role`: Role at time of request
- `status`: pending/approved/rejected
- `reason`: User's explanation (optional)
- `reviewed_by`: Admin who reviewed (null until reviewed)
- `reviewed_at`: Timestamp of review
- `admin_notes`: Admin feedback (optional)

**Example Usage**:
```python
# Check if user has pending request
has_pending = RoleChangeRequest.objects.filter(
    user=request.user,
    status=RoleChangeRequest.PENDING
).exists()

# Get all pending requests
pending = RoleChangeRequest.objects.filter(
    status=RoleChangeRequest.PENDING
).select_related('user')
```

## Candidate Search

### Overview

Admins and interviewers can search for candidates by username to view their
profiles, resumes, and interview history.

### User Flow

1. Navigate to "Search Candidates" from navbar (visible to admins/interviewers)
2. Enter username in search box
3. View list of matching candidates
4. Click "View Profile" to see full candidate details

### Endpoint

#### Search Candidates
```
GET /candidates/search/?q=<query>
```
**Access**: Admin or Interviewer only

**Query Parameters**:
- `q`: Username search query (case-insensitive, partial match)

**Response**: HTML page with:
- Search form
- List of matching candidates (max 20 results)
- For each candidate:
  - Username
  - Email
  - Full name (if provided)
  - Join date
  - Link to view full profile

**Example**:
```
GET /candidates/search/?q=john
# Returns all candidates with "john" in username
# e.g., "john_doe", "bob_johnson"
```

### Search Behavior

- **Case-insensitive**: "JOHN" matches "john_doe"
- **Partial match**: "john" matches "john_doe" and "bob_johnson"
- **Candidates only**: Only returns users with `role=candidate`
- **Limit**: Returns maximum 20 results
- **Empty query**: Shows empty state with instructions

### Integration with Navigation

The navbar conditionally shows links based on user role:

```django
{% if user.profile.role == 'admin' or user.profile.role == 'interviewer' %}
  <li class="nav-item">
    <a class="nav-link" href="{% url 'candidate_search' %}">Search Candidates</a>
  </li>
{% endif %}

{% if user.profile.role == 'admin' %}
  <li class="nav-item">
    <a class="nav-link" href="{% url 'role_requests_list' %}">Role Requests</a>
  </li>
{% endif %}
```

## Testing

### Role Request Tests

Location: `active_interview_app/tests/test_rbac.py:529-756`

**Test Coverage**:
- Candidate can submit role request
- Candidate cannot submit duplicate pending requests
- Unauthenticated users cannot submit requests
- Admin can view role requests list
- Non-admin cannot view role requests list
- Admin can approve requests (updates user role)
- Admin can reject requests (does not update role)
- Non-admin cannot review requests
- Profile page shows pending request status

### Search Tests

Location: `active_interview_app/tests/test_rbac.py:759-908`

**Test Coverage**:
- Admin can access search
- Interviewer can access search
- Candidate cannot access search
- Unauthenticated users cannot access search
- Search by username returns matches
- Exact username match works
- Search is case-insensitive
- Empty query shows appropriate message
- No results handled gracefully
- Search only returns candidates (not admins/interviewers)

**Run Tests**:
```bash
python manage.py test active_interview_app.tests.test_rbac.RoleChangeRequestTest
python manage.py test active_interview_app.tests.test_rbac.CandidateSearchTest
```
