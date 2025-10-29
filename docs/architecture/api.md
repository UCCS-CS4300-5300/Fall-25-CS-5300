# API Reference

REST API documentation for Active Interview Service.

## Overview

The application provides a REST API built with Django REST Framework for managing resumes and job listings.

**Base URL:** `http://127.0.0.1:8000` (development)

**Authentication:** Session-based (requires login)

**Content-Type:** `application/json`

---

## Authentication

All API endpoints require authentication.

### Login

Use Django's built-in authentication:

```http
POST /accounts/login/
Content-Type: application/x-www-form-urlencoded

username=user&password=pass
```

After successful login, session cookie is set and used for subsequent requests.

### Logout

```http
POST /accounts/logout/
```

---

## Endpoints

### Resume API

#### List Resumes

**GET** `/api/resumes/`

Returns list of resumes for the authenticated user.

**Authentication:** Required

**Response:**
```json
[
  {
    "id": 1,
    "user": 1,
    "title": "Software Engineer Resume",
    "file": "/media/uploads/resume.pdf",
    "text_content": "Extracted resume text...",
    "uploaded_at": "2025-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "user": 1,
    "title": "Senior Developer Resume",
    "file": "/media/uploads/resume2.pdf",
    "text_content": "Another resume...",
    "uploaded_at": "2025-01-20T14:00:00Z"
  }
]
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized

**Filtering:**

Only returns resumes owned by the authenticated user.

---

#### Get Resume

**GET** `/api/resumes/<id>/`

Returns a single resume by ID.

**Authentication:** Required

**Ownership:** User must own the resume

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "title": "Software Engineer Resume",
  "file": "/media/uploads/resume.pdf",
  "text_content": "Extracted resume text content...",
  "uploaded_at": "2025-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized (not owner)
- `404 Not Found` - Resume doesn't exist

---

#### Create Resume (Not via API)

Resumes are created via the web interface upload form, not the API.

Use: **POST** `/upload-file/` (HTML form)

---

#### Update Resume

**PUT** `/api/resumes/<id>/`

**PATCH** `/api/resumes/<id>/` (partial update)

Updates an existing resume.

**Authentication:** Required

**Ownership:** User must own the resume

**Request Body (JSON):**
```json
{
  "title": "Updated Resume Title",
  "text_content": "Updated text content..."
}
```

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "title": "Updated Resume Title",
  "file": "/media/uploads/resume.pdf",
  "text_content": "Updated text content...",
  "uploaded_at": "2025-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Resume doesn't exist

---

#### Delete Resume

**DELETE** `/api/resumes/<id>/`

Deletes a resume.

**Authentication:** Required

**Ownership:** User must own the resume

**Response:** Empty (204)

**Status Codes:**
- `204 No Content` - Success (deleted)
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Resume doesn't exist

**Side Effects:**
- File is deleted from filesystem
- Any chats linked to this resume have `resume` set to NULL

---

### Job Listing API

#### List Job Listings

**GET** `/api/job-listings/`

Returns list of job listings for the authenticated user.

**Authentication:** Required

**Response:**
```json
[
  {
    "id": 1,
    "user": 1,
    "title": "Senior Django Developer",
    "file": "/media/uploads/job.pdf",
    "text_content": "Job description text...",
    "uploaded_at": "2025-01-15T11:00:00Z"
  },
  {
    "id": 2,
    "user": 1,
    "title": "Python Backend Engineer",
    "file": null,
    "text_content": "Pasted job description...",
    "uploaded_at": "2025-01-18T09:30:00Z"
  }
]
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized

**Note:** `file` can be null if job was created via text paste.

---

#### Get Job Listing

**GET** `/api/job-listings/<id>/`

Returns a single job listing by ID.

**Authentication:** Required

**Ownership:** User must own the job listing

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "title": "Senior Django Developer",
  "file": "/media/uploads/job.pdf",
  "text_content": "Full job description text...",
  "uploaded_at": "2025-01-15T11:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Job listing doesn't exist

---

#### Create Job Listing (Not via API)

Job listings are created via web interface, not the API.

Use:
- **POST** `/upload-file/` (file upload)
- **POST** `/save-pasted-text/` (paste text)

---

#### Update Job Listing

**PUT** `/api/job-listings/<id>/`

**PATCH** `/api/job-listings/<id>/` (partial update)

Updates an existing job listing.

**Authentication:** Required

**Ownership:** User must own the job listing

**Request Body (JSON):**
```json
{
  "title": "Updated Job Title",
  "text_content": "Updated job description..."
}
```

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "title": "Updated Job Title",
  "file": "/media/uploads/job.pdf",
  "text_content": "Updated job description...",
  "uploaded_at": "2025-01-15T11:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Job listing doesn't exist

---

#### Delete Job Listing

**DELETE** `/api/job-listings/<id>/`

Deletes a job listing.

**Authentication:** Required

**Ownership:** User must own the job listing

**Response:** Empty (204)

**Status Codes:**
- `204 No Content` - Success (deleted)
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Job listing doesn't exist

**Side Effects:**
- File is deleted from filesystem (if exists)
- Any chats linked to this job have `job_listing` set to NULL

---

## Web Endpoints (Non-REST)

These endpoints use traditional Django views (HTML responses).

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/accounts/login/` | User login |
| POST | `/accounts/logout/` | User logout |
| GET/POST | `/accounts/register/` | User registration |

---

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chat/` | List user's chats |
| GET/POST | `/chat/create/` | Create new chat |
| GET/POST | `/chat/<id>/` | View/interact with chat |
| GET/POST | `/chat/<id>/edit/` | Edit chat settings |
| POST | `/chat/<id>/restart/` | Restart chat (clear messages) |
| POST | `/chat/<id>/delete/` | Delete chat |
| GET | `/chat/<id>/results/` | View interview results |
| GET | `/chat/<id>/charts/` | View performance charts (JSON) |

---

### Document Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/document/` | List all documents (resumes + jobs) |
| GET/POST | `/upload-file/` | Upload resume or job listing |
| POST | `/save-pasted-text/` | Create job from pasted text |
| GET | `/resume/<id>/` | View resume details |
| POST | `/resume/<id>/delete/` | Delete resume |
| GET/POST | `/resume/<id>/edit/` | Edit resume |
| GET | `/job/<id>/` | View job listing details |
| POST | `/job/<id>/delete/` | Delete job listing |
| GET/POST | `/job/<id>/edit/` | Edit job listing |

---

### Report Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/<id>/generate-report/` | Generate exportable report |
| GET | `/chat/<id>/export-report/` | View report in browser |
| GET | `/chat/<id>/download-pdf/` | Download PDF report |

---

### Other Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Homepage |
| GET | `/aboutus/` | About page |
| GET | `/features/` | Features page |
| GET | `/profile/` | User profile |

---

## Error Responses

### 400 Bad Request

**Cause:** Invalid request data

**Example:**
```json
{
  "title": ["This field is required."],
  "text_content": ["Ensure this field has no more than 10000 characters."]
}
```

---

### 401 Unauthorized

**Cause:** Not authenticated

**Response:** Redirect to `/accounts/login/` or JSON error:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 403 Forbidden

**Cause:** Authenticated but not authorized (not owner)

**Response:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 404 Not Found

**Cause:** Resource doesn't exist

**Response:**
```json
{
  "detail": "Not found."
}
```

---

## Pagination

Currently, no pagination is implemented. All API endpoints return full lists.

**Future consideration:** Implement pagination for large datasets.

---

## Rate Limiting

Currently, no rate limiting is implemented.

**Future consideration:** Implement rate limiting to prevent abuse.

---

## CORS

CORS is not enabled by default.

**For frontend apps:** Install `django-cors-headers` and configure allowed origins.

---

## API Client Examples

### Python (requests)

```python
import requests

# Login
session = requests.Session()
login_data = {'username': 'user', 'password': 'pass'}
session.post('http://127.0.0.1:8000/accounts/login/', data=login_data)

# List resumes
resumes = session.get('http://127.0.0.1:8000/api/resumes/').json()
print(resumes)

# Get specific resume
resume = session.get('http://127.0.0.1:8000/api/resumes/1/').json()
print(resume)

# Update resume
update_data = {'title': 'Updated Resume'}
session.patch('http://127.0.0.1:8000/api/resumes/1/', json=update_data)

# Delete resume
session.delete('http://127.0.0.1:8000/api/resumes/1/')
```

---

### JavaScript (fetch)

```javascript
// Login
await fetch('/accounts/login/', {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: 'username=user&password=pass',
  credentials: 'include'  // Include cookies
});

// List resumes
const resumes = await fetch('/api/resumes/', {
  credentials: 'include'
}).then(r => r.json());
console.log(resumes);

// Get specific resume
const resume = await fetch('/api/resumes/1/', {
  credentials: 'include'
}).then(r => r.json());
console.log(resume);

// Update resume
await fetch('/api/resumes/1/', {
  method: 'PATCH',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({title: 'Updated Resume'}),
  credentials: 'include'
});

// Delete resume
await fetch('/api/resumes/1/', {
  method: 'DELETE',
  credentials: 'include'
});
```

---

### cURL

```bash
# Login (get cookies)
curl -c cookies.txt -X POST http://127.0.0.1:8000/accounts/login/ \
  -d "username=user&password=pass"

# List resumes
curl -b cookies.txt http://127.0.0.1:8000/api/resumes/

# Get specific resume
curl -b cookies.txt http://127.0.0.1:8000/api/resumes/1/

# Update resume
curl -b cookies.txt -X PATCH http://127.0.0.1:8000/api/resumes/1/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Resume"}'

# Delete resume
curl -b cookies.txt -X DELETE http://127.0.0.1:8000/api/resumes/1/
```

---

## Serializers

**Location:** `active_interview_app/serializers.py`

### UploadedResumeSerializer

**Fields:**
- `id` (read-only)
- `user` (read-only, auto-set)
- `title`
- `file`
- `text_content`
- `uploaded_at` (read-only)

### UploadedJobListingSerializer

**Fields:**
- `id` (read-only)
- `user` (read-only, auto-set)
- `title`
- `file` (optional)
- `text_content`
- `uploaded_at` (read-only)

---

## Permissions

**ViewSets:**
- `UploadedResumeViewSet`
- `UploadedJobListingViewSet`

**Permission classes:**
- `IsAuthenticated` - User must be logged in

**Queryset filtering:**
- Automatically filters by `user=request.user`
- Users can only see/modify their own data

---

## API Versioning

Currently, no API versioning is implemented.

**Future consideration:** Implement versioning via URL path (`/api/v1/`) or headers.

---

## Testing the API

### Using Django Shell

```python
# Start shell
python manage.py shell

# Make API calls
from django.test import Client
from django.contrib.auth.models import User

client = Client()
user = User.objects.get(username='testuser')
client.force_login(user)

response = client.get('/api/resumes/')
print(response.json())
```

### Using pytest

```python
import pytest
from django.test import Client

@pytest.mark.django_db
def test_list_resumes(client, user):
    client.force_login(user)
    response = client.get('/api/resumes/')
    assert response.status_code == 200
```

---

## Next Steps

- **[Models Reference](models.md)** - Database schema
- **[Architecture Overview](overview.md)** - System design
- **[Testing Guide](../setup/testing.md)** - API testing examples
