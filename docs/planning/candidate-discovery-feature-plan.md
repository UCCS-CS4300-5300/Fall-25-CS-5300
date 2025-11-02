# Candidate Discovery & Role Management - Feature Plan

**Status:** Planning / Partial Implementation
**Related Issues:** #69 (RBAC base), Future: #73, #74, #75
**Date Created:** 2025-01-31
**Last Updated:** 2025-01-31

---

## Overview

Extend RBAC implementation to provide user-facing interfaces for:
1. Interviewers/admins discovering and searching candidates
2. Candidates requesting role changes (e.g., candidate → interviewer)
3. Admins approving/rejecting role requests

**Current State:** RBAC API endpoints exist but no UI for discovery/search.

---

## Implementation Phases

### ✅ Phase 0: RBAC Foundation (COMPLETED)
- UserProfile model with roles
- API endpoints for role management
- Permission decorators
- **Status:** Fully implemented

### 🚧 Phase 1: Role Request System (IN PROGRESS)
**Priority:** HIGH - Implementing now

#### Components:
1. **Model:** `RoleChangeRequest`
2. **Views:** Request submission, admin approval/rejection
3. **Templates:** Request form, admin review page
4. **URLs:** Role request routes

**Details:** See "Role Request System" section below.

### 🔄 Phase 2: Simple Candidate Search (IN PROGRESS)
**Priority:** HIGH - Implementing now

#### Components:
1. **View:** Basic username search
2. **Template:** Search page for admins/interviewers
3. **Navigation:** Add "Find Candidates" link (role-based)

**Details:** See "Simple Search" section below.

### ⏸️ Phase 3: Advanced Search (PENDING FEEDBACK)
**Priority:** MEDIUM - Awaiting team/customer feedback

**Proposed Features:**
- Search by skills, education level/field, years of experience
- "Available for practice" filter
- Multi-criteria search

**Open Questions:**
- Skills on Resume vs UserProfile?
- Simple text search vs structured tags?
- Fuzzy matching needed?

**Next Steps:** Get feedback from team/customer before implementing.

### ⏸️ Phase 4: Profile Enhancements (PENDING FEEDBACK)
**Priority:** MEDIUM - Awaiting team/customer feedback

**Proposed UserProfile Fields:**
- `looking_for_practice` (Boolean)
- `years_experience` (Integer)
- `education_level` (CharField with choices)
- `education_field` (CharField)

**Next Steps:** Confirm with team which fields are needed.

---

## Phase 1: Role Request System (IMPLEMENTING NOW)

### A. Model: RoleChangeRequest

**File:** `active_interview_app/models.py`

```python
class RoleChangeRequest(models.Model):
    """
    Track requests from users to change their role.
    Primarily used for candidates requesting interviewer role.
    """
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_requests'
    )
    requested_role = models.CharField(
        max_length=20,
        help_text='Role being requested (typically "interviewer")'
    )
    current_role = models.CharField(
        max_length=20,
        help_text='Role at time of request'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    reason = models.TextField(
        blank=True,
        help_text='User explanation for role request'
    )

    # Admin review tracking
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_role_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(
        blank=True,
        help_text='Admin notes on approval/rejection'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.current_role} → {self.requested_role} ({self.status})"
```

### B. Views

**File:** `active_interview_app/views.py`

#### 1. Submit Role Request (Candidate)
```python
@login_required
def request_role_change(request):
    """
    Allow users to request a role change.
    POST /profile/request-role-change/
    """
    if request.method == 'POST':
        requested_role = request.POST.get('requested_role')
        reason = request.POST.get('reason', '')

        # Validate
        if requested_role not in ['interviewer', 'admin']:
            messages.error(request, 'Invalid role requested')
            return redirect('profile')

        # Check for existing pending request
        existing = RoleChangeRequest.objects.filter(
            user=request.user,
            status='pending'
        ).exists()

        if existing:
            messages.warning(request, 'You already have a pending request')
            return redirect('profile')

        # Create request
        RoleChangeRequest.objects.create(
            user=request.user,
            requested_role=requested_role,
            current_role=request.user.profile.role,
            reason=reason
        )

        messages.success(request, 'Role request submitted for admin review')
        return redirect('profile')

    return render(request, 'role_request_form.html')
```

#### 2. List Role Requests (Admin)
```python
@admin_required
def role_requests_list(request):
    """
    Show all role requests to admins.
    GET /admin/role-requests/
    """
    pending = RoleChangeRequest.objects.filter(
        status='pending'
    ).select_related('user', 'user__profile')

    reviewed = RoleChangeRequest.objects.exclude(
        status='pending'
    ).select_related('user', 'user__profile', 'reviewed_by')[:20]

    context = {
        'pending_requests': pending,
        'reviewed_requests': reviewed,
    }
    return render(request, 'admin/role_requests.html', context)
```

#### 3. Approve/Reject Request (Admin)
```python
@admin_required
def review_role_request(request, request_id):
    """
    Approve or reject a role change request.
    POST /admin/role-requests/<id>/review/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    role_request = get_object_or_404(RoleChangeRequest, id=request_id)

    action = request.POST.get('action')  # 'approve' or 'reject'
    admin_notes = request.POST.get('admin_notes', '')

    if action == 'approve':
        # Update user's role
        role_request.user.profile.role = role_request.requested_role
        role_request.user.profile.save()

        role_request.status = 'approved'
        messages.success(request, f'Approved: {role_request.user.username} is now {role_request.requested_role}')

    elif action == 'reject':
        role_request.status = 'rejected'
        messages.info(request, f'Rejected role request from {role_request.user.username}')

    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)

    role_request.reviewed_by = request.user
    role_request.reviewed_at = timezone.now()
    role_request.admin_notes = admin_notes
    role_request.save()

    return redirect('role_requests_list')
```

### C. Templates

**File:** `templates/role_request_form.html`
```django
{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <h2>Request Role Change</h2>

    <div class="alert alert-info">
        Current role: <strong>{{ request.user.profile.role|title }}</strong>
    </div>

    <form method="post" action="{% url 'request_role_change' %}">
        {% csrf_token %}

        <div class="mb-3">
            <label class="form-label">Requested Role</label>
            <select name="requested_role" class="form-select" required>
                <option value="">-- Select Role --</option>
                <option value="interviewer">Interviewer</option>
            </select>
            <small class="text-muted">
                Interviewers can conduct practice interviews and view all candidate profiles.
            </small>
        </div>

        <div class="mb-3">
            <label class="form-label">Why do you want this role? (Optional)</label>
            <textarea name="reason" class="form-control" rows="4"
                      placeholder="Tell us about your experience and why you'd like to become an interviewer..."></textarea>
        </div>

        <button type="submit" class="btn btn-primary">Submit Request</button>
        <a href="{% url 'profile' %}" class="btn btn-secondary">Cancel</a>
    </form>
</div>
{% endblock %}
```

**File:** `templates/admin/role_requests.html`
```django
{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <h2>Role Change Requests</h2>

    <h3 class="mt-4">Pending Requests ({{ pending_requests.count }})</h3>

    {% if pending_requests %}
        <div class="list-group mb-4">
            {% for req in pending_requests %}
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h5>{{ req.user.username }}
                            <span class="badge bg-secondary">{{ req.current_role }}</span>
                            →
                            <span class="badge bg-primary">{{ req.requested_role }}</span>
                        </h5>
                        <p class="mb-1"><strong>Email:</strong> {{ req.user.email }}</p>
                        {% if req.reason %}
                            <p class="mb-1"><strong>Reason:</strong> {{ req.reason }}</p>
                        {% endif %}
                        <small class="text-muted">Requested {{ req.created_at|timesince }} ago</small>
                    </div>
                    <div>
                        <form method="post" action="{% url 'review_role_request' req.id %}" style="display: inline;">
                            {% csrf_token %}
                            <input type="hidden" name="action" value="approve">
                            <button type="submit" class="btn btn-success btn-sm">Approve</button>
                        </form>
                        <button type="button" class="btn btn-danger btn-sm"
                                data-bs-toggle="modal" data-bs-target="#rejectModal{{ req.id }}">
                            Reject
                        </button>

                        <!-- Reject Modal -->
                        <div class="modal fade" id="rejectModal{{ req.id }}">
                            <div class="modal-dialog">
                                <div class="modal-content">
                                    <form method="post" action="{% url 'review_role_request' req.id %}">
                                        {% csrf_token %}
                                        <input type="hidden" name="action" value="reject">
                                        <div class="modal-header">
                                            <h5 class="modal-title">Reject Request</h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                        </div>
                                        <div class="modal-body">
                                            <p>Reject role request from <strong>{{ req.user.username }}</strong>?</p>
                                            <div class="mb-3">
                                                <label>Admin Notes (optional)</label>
                                                <textarea name="admin_notes" class="form-control" rows="3"></textarea>
                                            </div>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                            <button type="submit" class="btn btn-danger">Reject</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <p class="text-muted">No pending requests.</p>
    {% endif %}

    <h3 class="mt-5">Recent Reviews</h3>
    {% if reviewed_requests %}
        <div class="list-group">
            {% for req in reviewed_requests %}
            <div class="list-group-item">
                <div class="d-flex justify-content-between">
                    <div>
                        <h6>{{ req.user.username }}
                            {% if req.status == 'approved' %}
                                <span class="badge bg-success">Approved</span>
                            {% else %}
                                <span class="badge bg-danger">Rejected</span>
                            {% endif %}
                        </h6>
                        <small class="text-muted">
                            Reviewed by {{ req.reviewed_by.username }} {{ req.reviewed_at|timesince }} ago
                        </small>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    {% endif %}
</div>
{% endblock %}
```

### D. URLs

**File:** `active_interview_app/urls.py`

```python
# Role request URLs
path('profile/request-role-change/', views.request_role_change, name='request_role_change'),
path('admin/role-requests/', views.role_requests_list, name='role_requests_list'),
path('admin/role-requests/<int:request_id>/review/', views.review_role_request, name='review_role_request'),
```

### E. Profile Page Integration

**Add to profile template:**
```django
{% if user.profile.role == 'candidate' %}
    <div class="card mt-3">
        <div class="card-body">
            <h5>Want to become an interviewer?</h5>
            <p>Help other candidates prepare by conducting practice interviews.</p>

            {% if pending_role_request %}
                <div class="alert alert-warning">
                    You have a pending interviewer request.
                    <small>Submitted {{ pending_role_request.created_at|timesince }} ago</small>
                </div>
            {% else %}
                <a href="{% url 'request_role_change' %}" class="btn btn-primary">
                    Request Interviewer Role
                </a>
            {% endif %}
        </div>
    </div>
{% endif %}
```

### F. Navbar Badge for Admins

**Add to navbar:**
```django
{% if user.profile.role == 'admin' %}
    <li class="nav-item">
        <a class="nav-link" href="{% url 'role_requests_list' %}">
            Role Requests
            {% if pending_role_requests_count > 0 %}
                <span class="badge bg-danger">{{ pending_role_requests_count }}</span>
            {% endif %}
        </a>
    </li>
{% endif %}
```

---

## Phase 2: Simple Candidate Search (IMPLEMENTING NOW)

### A. View: Username Search

**File:** `active_interview_app/views.py`

```python
@admin_or_interviewer_required
def candidate_search(request):
    """
    Simple username search for candidates.
    GET /candidates/search/
    """
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        # Search by username (case-insensitive)
        users = User.objects.filter(
            username__icontains=query,
            profile__role='candidate'
        ).select_related('profile')[:20]  # Limit to 20 results

        results = users

    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'candidates/search.html', context)
```

### B. Template

**File:** `templates/candidates/search.html`

```django
{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <h2>Find Candidates</h2>

    <form method="get" action="{% url 'candidate_search' %}" class="mb-4">
        <div class="input-group">
            <input type="text" name="q" class="form-control"
                   placeholder="Search by username..."
                   value="{{ query }}"
                   autofocus>
            <button type="submit" class="btn btn-primary">Search</button>
        </div>
    </form>

    {% if query %}
        <h4>Results for "{{ query }}"</h4>

        {% if results %}
            <div class="list-group mt-3">
                {% for user in results %}
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="mb-1">{{ user.username }}</h5>
                            <p class="mb-1">
                                {% if user.first_name or user.last_name %}
                                    {{ user.first_name }} {{ user.last_name }}
                                {% endif %}
                            </p>
                            <small class="text-muted">{{ user.email }}</small>
                        </div>
                        <div>
                            <a href="{% url 'candidate_profile_view' user.id %}"
                               class="btn btn-sm btn-outline-primary">
                                View Profile
                            </a>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <p class="text-muted mt-3">No candidates found matching "{{ query }}"</p>
        {% endif %}
    {% else %}
        <p class="text-muted">Enter a username to search for candidates.</p>
    {% endif %}
</div>
{% endblock %}
```

### C. URL

```python
path('candidates/search/', views.candidate_search, name='candidate_search'),
```

### D. Navigation

**Add to navbar (for admins and interviewers):**
```django
{% if user.profile.role in 'admin,interviewer' %}
    <li class="nav-item">
        <a class="nav-link" href="{% url 'candidate_search' %}">
            Find Candidates
        </a>
    </li>
{% endif %}
```

---

## Future Enhancements (ON HOLD - Awaiting Feedback)

### Advanced Search Options

**Skills Search:**
```python
# Search candidates by skill
if skill_query:
    # Option 1: Search in UploadedResume.skills
    users = users.filter(
        uploadedresume__skills__icontains=skill_query
    ).distinct()

    # Option 2: If skills moved to UserProfile
    users = users.filter(
        profile__skills__icontains=skill_query
    )
```

**Education Search:**
```python
education_level = request.GET.get('education_level')
education_field = request.GET.get('education_field')

if education_level:
    users = users.filter(profile__education_level=education_level)

if education_field:
    users = users.filter(profile__education_field__icontains=education_field)
```

**Experience Range:**
```python
min_years = request.GET.get('min_years')
max_years = request.GET.get('max_years')

if min_years:
    users = users.filter(profile__years_experience__gte=min_years)
if max_years:
    users = users.filter(profile__years_experience__lte=max_years)
```

**Available for Practice:**
```python
available_only = request.GET.get('available_for_practice')
if available_only:
    users = users.filter(profile__looking_for_practice=True)
```

---

## Open Questions (For Team/Customer)

### 1. Skills Data Structure
**Question:** Where should skills be stored?

**Options:**
- A: Keep on `UploadedResume.skills` (current)
- B: Move to `UserProfile.skills`
- C: Aggregate from all resumes

**Impact:** Affects search performance and data modeling

### 2. Registration Flow
**Question:** Should role requests be integrated into registration?

**Options:**
- A: Separate step after registration
- B: Optional checkbox during registration
- C: Required field during registration

**Recommendation:** Option A or B

### 3. Search Complexity
**Question:** How sophisticated should search be?

**Options:**
- A: Simple text matching
- B: Structured tags with exact matching
- C: Fuzzy search with AI/ML

**Recommendation:** Start with A, evolve to B if needed

### 4. Profile Visibility
**Question:** Should all candidate profiles be visible to interviewers?

**Options:**
- A: Yes, all candidates visible
- B: Only "available for practice" candidates
- C: Candidates can opt-in/out of directory

**Recommendation:** Discuss privacy implications with team

---

## Testing Checklist

### Role Request System
- [ ] Candidate can submit role request
- [ ] Cannot submit duplicate pending requests
- [ ] Admin sees pending requests with count badge
- [ ] Admin can approve request (role updated)
- [ ] Admin can reject request
- [ ] Non-admin cannot access admin pages (403)
- [ ] Approved users receive new permissions
- [ ] Request history is viewable

### Simple Search
- [ ] Search returns matching usernames
- [ ] Case-insensitive search works
- [ ] Only candidates shown (not interviewers/admins)
- [ ] View profile link works correctly
- [ ] Admin and interviewer can access
- [ ] Candidates cannot access (403)
- [ ] Empty search shows appropriate message

---

## Migration Strategy

### New Fields on UserProfile (Future)
```bash
python manage.py makemigrations
# Migration will add:
# - looking_for_practice (Boolean, default=False)
# - years_experience (Integer, nullable)
# - education_level (CharField, nullable)
# - education_field (CharField, blank=True)
```

### New Model: RoleChangeRequest
```bash
python manage.py makemigrations
# Creates RoleChangeRequest table with indexes
```

---

## Documentation Updates Needed

- [ ] Update `docs/features/rbac.md` with role request flow
- [ ] Add candidate search documentation
- [ ] Update API docs if API endpoints added
- [ ] Add troubleshooting section for common issues

---

## Related Files

**Models:**
- `active_interview_app/models.py` - UserProfile, RoleChangeRequest

**Views:**
- `active_interview_app/views.py` - Role request views, search view

**Templates:**
- `templates/role_request_form.html`
- `templates/admin/role_requests.html`
- `templates/candidates/search.html`
- `templates/profile.html` (updated)
- `templates/components/navbar.html` (updated)

**URLs:**
- `active_interview_app/urls.py`

**Tests:**
- `active_interview_app/tests/test_role_requests.py` (new)
- `active_interview_app/tests/test_candidate_search.py` (new)

---

## Notes

- **Session Date:** 2025-01-31
- **Implementation Priority:** Role requests + simple search
- **Deferred:** Advanced search, profile enhancements
- **Awaiting:** Team/customer feedback on advanced features
