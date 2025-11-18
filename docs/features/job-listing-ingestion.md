# Job Listing Ingestion and AI-Powered Analysis

**Status:** ✅ Implemented
**Issues:** #21, #51, #52, #53
**Version:** 1.0
**Last Updated:** 2025-11-16

---

## Overview

The Job Listing Ingestion feature allows users to upload job descriptions and have them automatically analyzed using AI to extract structured information. This enables candidates to prepare for interviews tailored to specific job requirements.

### Key Capabilities

1. **Job Listing Upload** (Issue #21)
   - Upload job descriptions via text input or file upload
   - Support for `.txt`, `.pdf`, `.doc`, `.docx` file formats
   - Content extraction and storage

2. **AI-Powered Parsing** (Issues #51, #52)
   - Extract required skills (technical, soft skills, domain knowledge)
   - Detect seniority level (entry, mid, senior, lead, executive)
   - Extract structured requirements (education, experience, certifications, responsibilities)

3. **Template Recommendation** (Issue #53)
   - Auto-recommend interview templates based on job analysis
   - Match template difficulty to seniority level
   - Streamlined interview creation workflow

4. **Interview Creation Integration** (Issue #53)
   - Create interviews directly from analyzed job listings
   - Pre-populate job listing in interview creation form
   - Display recommended template suggestions

---

## User Workflows

### Workflow 1: Upload and Analyze Job Listing

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User navigates to Documents page                         │
│    - Clicks "Job Listings" tab                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. User uploads job description                             │
│    Option A: Paste text into textarea                       │
│    Option B: Upload file (.txt, .pdf, .doc, .docx)          │
│    - Click "Upload Job Listing"                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Backend processing                                        │
│    - Create UploadedJobListing record (status: pending)     │
│    - Extract content from file (if uploaded)                │
│    - Save to database                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. AI Parsing (automatic)                                   │
│    - Status: in_progress                                    │
│    - Call OpenAI GPT-4o with job description                │
│    - Extract: required_skills, seniority_level, requirements│
│    - Recommend interview template                           │
│    - Status: success (or error if failed)                   │
│    - Set parsed_at timestamp                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. User views analyzed job listing                          │
│    - See extracted skills                                   │
│    - See detected seniority level                           │
│    - See recommended template                               │
│    - Option to create interview from this listing           │
└─────────────────────────────────────────────────────────────┘
```

### Workflow 2: Create Interview from Job Analysis

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User has analyzed job listing                            │
│    - Job listing has parsing_status: success                │
│    - Required skills extracted                              │
│    - Seniority level detected                               │
│    - Template recommended                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. User clicks "Create Interview" button                    │
│    - Button appears on analyzed job listing card            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Navigate to chat creation with URL parameters            │
│    URL: /chat/create/?job_id=123&template_id=456            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Chat creation form pre-populated                         │
│    - Job listing field pre-selected                         │
│    - Helper message: "Job listing pre-selected from analysis"│
│    - Display: "Recommended template: [template name]"       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. User completes form and creates interview                │
│    - Fill in: title, type, difficulty                       │
│    - Optional: select resume                                │
│    - Click "Create"                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Interview created and started                            │
│    - Chat associated with job listing                       │
│    - AI tailors questions based on required skills          │
│    - Difficulty matches seniority level                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Technical Architecture

### Database Schema

#### UploadedJobListing Model

```python
class UploadedJobListing(models.Model):
    # Core fields (Issue #21)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    content = models.TextField()
    title = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    created_at = models.DateTimeField(auto_now_add=True)

    # Parsed data fields (Issues #51, #52)
    required_skills = models.JSONField(default=list, blank=True)
    # Structure: ["Python", "Django", "5+ years experience", "Leadership"]

    seniority_level = models.CharField(
        max_length=50,
        blank=True,
        choices=SENIORITY_CHOICES
    )
    # Values: 'entry', 'mid', 'senior', 'lead', 'executive'

    requirements = models.JSONField(default=dict, blank=True)
    # Structure: {
    #     "education": ["Bachelor's in CS", "..."],
    #     "years_experience": "5+",
    #     "certifications": ["AWS", "..."],
    #     "responsibilities": ["...", "..."]
    # }

    # Template association (Issue #53)
    recommended_template = models.ForeignKey(
        'InterviewTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Parsing metadata
    parsing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('success', 'Success'),
            ('error', 'Error'),
        ],
        default='pending'
    )
    parsing_error = models.TextField(blank=True, null=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
```

### API Endpoints

#### Job Listing Upload

**Endpoint:** `POST /api/documents/job-listings/`

**Request:**
```json
{
  "filename": "senior_dev_role.txt",
  "content": "Senior Python Developer\n\nRequirements:\n- 5+ years Python...",
  "file": "<file upload>"  // Optional, if uploading file
}
```

**Response (Success):**
```json
{
  "id": 123,
  "user": 1,
  "filename": "senior_dev_role.txt",
  "content": "Senior Python Developer...",
  "title": "Senior Python Developer",
  "created_at": "2025-11-16T10:30:00Z",
  "parsing_status": "in_progress",
  "parsing_error": null,
  "parsed_at": null,
  "required_skills": [],
  "seniority_level": "",
  "requirements": {},
  "recommended_template": null,
  "recommended_template_name": null
}
```

#### Trigger Job Listing Analysis

**Endpoint:** `POST /api/documents/job-listings/{id}/analyze/`

**Response (Success):**
```json
{
  "id": 123,
  "parsing_status": "success",
  "parsed_at": "2025-11-16T10:30:15Z",
  "required_skills": [
    "Python",
    "Django",
    "PostgreSQL",
    "5+ years experience",
    "Team leadership"
  ],
  "seniority_level": "senior",
  "requirements": {
    "education": ["Bachelor's in Computer Science"],
    "years_experience": "5+",
    "certifications": ["AWS Certified Developer"],
    "responsibilities": [
      "Lead backend development projects",
      "Mentor junior developers",
      "Design scalable systems"
    ]
  },
  "recommended_template": 45,
  "recommended_template_name": "Senior System Design"
}
```

**Response (Error):**
```json
{
  "id": 123,
  "parsing_status": "error",
  "parsing_error": "OpenAI service is unavailable. Please ensure OPENAI_API_KEY is configured and valid.",
  "parsed_at": null
}
```

### AI Parsing Service

**Module:** `active_interview_app/job_listing_parser.py`

**Key Functions:**

```python
def parse_job_listing_with_ai(job_description: str) -> Dict[str, Any]:
    """
    Parse job description using OpenAI GPT-4o.

    Args:
        job_description: The job description text

    Returns:
        dict with keys:
        - required_skills (list): Extracted skills
        - seniority_level (str): entry/mid/senior/lead/executive
        - requirements (dict): Structured requirements

    Raises:
        ValueError: If AI unavailable or parsing fails
    """
```

**AI Prompt Strategy:**

1. **System Prompt:** Instructs AI to extract structured data as JSON
2. **User Prompt:** Provides job description content
3. **Response Format:** Forces JSON output via `response_format={"type": "json_object"}`
4. **Temperature:** 0.3 (lower for consistent parsing)
5. **Model:** GPT-4o (most capable model for structured extraction)

**Seniority Level Mapping:**

The AI returns free-form seniority descriptions, which are mapped to standard levels:

| AI Output Variations | Mapped To |
|---------------------|-----------|
| "Junior", "Entry-level", "Graduate" | `entry` |
| "Mid-level", "Intermediate", "Mid" | `mid` |
| "Senior", "Senior-level" | `senior` |
| "Lead", "Principal", "Staff" | `lead` |
| "Executive", "Director", "VP", "C-level" | `executive` |

### Template Recommendation Logic

**Module:** `active_interview_app/views.py` (JobListingAnalysisViewSet)

**Algorithm:**

```python
def recommend_template(job_listing):
    """
    Recommend interview template based on seniority level.

    Priority:
    1. Match seniority level (entry → easy, senior → hard)
    2. Match interview type (SKL for technical roles)
    3. User's templates preferred over defaults
    """

    seniority = job_listing.seniority_level
    user_templates = InterviewTemplate.objects.filter(user=job_listing.user)

    # Map seniority to difficulty range
    difficulty_map = {
        'entry': (1, 2),      # Easy to medium
        'mid': (2, 3),        # Medium to hard
        'senior': (3, 4),     # Hard to very hard
        'lead': (4, 5),       # Very hard
        'executive': (3, 5),  # Hard to very hard
    }

    min_diff, max_diff = difficulty_map.get(seniority, (2, 3))

    # Find matching templates
    recommended = user_templates.filter(
        difficulty__gte=min_diff,
        difficulty__lte=max_diff
    ).order_by('-difficulty').first()

    return recommended
```

---

## Frontend Components

### Document List Page

**File:** `templates/documents/document-list.html`

**Job Listing Card:**

```html
<div class="job-listing-card">
  <h5>{{ job_listing.title }}</h5>
  <p>Uploaded: {{ job_listing.created_at|date:"M d, Y" }}</p>

  <!-- Parsing Status -->
  <div class="parsing-status">
    {% if job_listing.parsing_status == 'success' %}
      <span class="badge bg-success">✓ Analyzed</span>
    {% elif job_listing.parsing_status == 'in_progress' %}
      <span class="badge bg-warning">Analyzing...</span>
    {% elif job_listing.parsing_status == 'error' %}
      <span class="badge bg-danger">Analysis Failed</span>
    {% else %}
      <span class="badge bg-secondary">Pending</span>
    {% endif %}
  </div>

  <!-- Parsed Data (if successful) -->
  {% if job_listing.parsing_status == 'success' %}
    <div class="parsed-data">
      <p><strong>Seniority:</strong> {{ job_listing.get_seniority_level_display }}</p>
      <p><strong>Skills:</strong> {{ job_listing.required_skills|join:", " }}</p>
      {% if job_listing.recommended_template %}
        <p><strong>Recommended:</strong> {{ job_listing.recommended_template.name }}</p>
      {% endif %}
    </div>
  {% endif %}

  <!-- Actions -->
  <div class="actions">
    <button onclick="viewJobDetails({{ job_listing.id }})">View Details</button>
    {% if job_listing.parsing_status == 'success' %}
      <a href="{% url 'chat-create' %}?job_id={{ job_listing.id }}{% if job_listing.recommended_template %}&template_id={{ job_listing.recommended_template.id }}{% endif %}"
         class="btn btn-primary">
        Create Interview
      </a>
    {% endif %}
  </div>
</div>
```

### Chat Creation Page (Pre-populated)

**File:** `templates/chat/chat-create.html`

**Helper Message (when from_job_analysis=True):**

```html
{% if from_job_analysis %}
  <div style="margin: 0 1rem 1.5rem 1rem; padding: 1rem;
              background: var(--surface-highlight);
              border-left: 4px solid var(--primary);
              border-radius: var(--radius);">
    <p style="margin: 0; color: var(--text-primary); font-weight: 500;">
      <svg>...</svg>
      Job listing pre-selected from analysis
    </p>
    {% if suggested_template %}
      <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 0.9rem;">
        Recommended template: <strong>{{ suggested_template.name }}</strong>
      </p>
    {% endif %}
  </div>
{% endif %}
```

---

## Testing Strategy

### Unit Tests

**File:** `active_interview_app/tests/test_job_listing_parser.py`

**Test Coverage:**

1. **Parsing Valid Job Descriptions**
   - Test successful parsing of complete job descriptions
   - Verify all fields extracted correctly
   - Test different seniority levels (entry, mid, senior, lead, executive)

2. **Edge Cases**
   - Empty job descriptions
   - Minimal job descriptions (missing fields)
   - Extremely long job descriptions (truncation)
   - Malformed content

3. **Error Handling**
   - OpenAI API unavailable
   - Invalid API key
   - Malformed JSON responses
   - Wrong data types in responses

4. **Type Correction**
   - Test auto-correction of wrong types from AI
   - Test seniority level mapping variants

**Example Tests:**

```python
class JobListingParserTestCase(TestCase):
    def test_parse_job_listing_valid(self):
        """Test successful parsing of valid job description"""
        result = parse_job_listing_with_ai(sample_job_description)

        self.assertEqual(result['seniority_level'], 'senior')
        self.assertIn('Python', result['required_skills'])
        self.assertIn('Django', result['required_skills'])
        self.assertIsInstance(result['requirements'], dict)

    def test_parse_job_listing_entry_level(self):
        """Test parsing of entry-level job description"""
        entry_job = "Junior Software Developer\n0-2 years experience"
        result = parse_job_listing_with_ai(entry_job)

        self.assertEqual(result['seniority_level'], 'entry')

    def test_parse_job_listing_ai_unavailable(self):
        """Test error handling when OpenAI is unavailable"""
        with patch('job_listing_parser.ai_available', return_value=False):
            with self.assertRaises(ValueError) as context:
                parse_job_listing_with_ai("Test job")

            self.assertIn("OpenAI service is unavailable", str(context.exception))
```

### BDD/Integration Tests

**File:** `features/job_listing_ingestion.feature`

**Scenarios Covered:**

- ✅ Upload job listing from text
- ✅ Upload job listing from file
- ✅ Validation errors for empty content
- ✅ Parse required skills extraction
- ✅ Detect seniority levels (all 5 levels)
- ✅ Extract structured requirements
- ✅ Template recommendation based on seniority
- ✅ Create interview from job analysis (navigation flow)
- ✅ Error handling (API unavailable, malformed content)
- ✅ Security (user isolation)

---

## Error Handling

### Parsing Errors

**Scenario:** OpenAI API is unavailable

**Behavior:**
- Set `parsing_status = 'error'`
- Store error message in `parsing_error` field
- Job listing remains accessible
- User can still manually create interviews
- Display error message in UI

**Example Error Messages:**

```python
# OpenAI unavailable
"OpenAI service is unavailable. Please ensure OPENAI_API_KEY is configured and valid."

# API rate limit
"Job listing parsing failed: OpenAI API rate limit exceeded"

# Invalid response
"Failed to parse OpenAI response as JSON"
```

### Validation Errors

**Scenario:** User uploads empty job description

**Response:**
```json
{
  "error": "Job description cannot be empty",
  "field": "content"
}
```

**Scenario:** User uploads unsupported file format

**Response:**
```json
{
  "error": "Unsupported file format. Please upload .txt, .pdf, .doc, or .docx files",
  "field": "file"
}
```

---

## Performance Considerations

### AI Parsing Performance

- **Average Parsing Time:** 3-5 seconds per job listing
- **Token Usage:** ~500-1000 tokens per job description
- **Rate Limits:** OpenAI API tier-dependent (typically 3500 requests/min)

### Optimization Strategies

1. **Content Truncation:**
   - Limit job descriptions to first 15,000 characters
   - Prevents token limit issues
   - Maintains parsing quality

2. **Async Processing:**
   - Parsing happens after upload (not blocking)
   - User can continue browsing while parsing completes
   - Status updates via polling or WebSocket (future enhancement)

3. **Caching:**
   - Parse results stored in database
   - No re-parsing on subsequent views

---

## Security & Privacy

### User Isolation

- Job listings are associated with `user` foreign key
- All queries filtered by `request.user`
- No cross-user access to job listings
- API endpoints require authentication (`LoginRequiredMixin`)

### Data Sanitization

- File uploads validated for type and size
- Content extracted safely (no code execution)
- Error messages sanitized (no API key exposure)

### Example Security Implementation:

```python
class JobListingViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # Only return current user's job listings
        return UploadedJobListing.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically associate with current user
        serializer.save(user=self.request.user)
```

---

## Future Enhancements

### Phase 2 (Planned)

1. **Real-time Parsing Status**
   - WebSocket updates for parsing progress
   - Live status indicator in UI

2. **Batch Upload**
   - Upload multiple job listings at once
   - Queue-based processing

3. **Skills Matching**
   - Match job required skills to user resume skills
   - Highlight skill gaps
   - Suggest learning resources

4. **Template Auto-selection**
   - Automatically select best template (not just recommend)
   - Option to override selection

5. **Advanced Template Recommendation**
   - ML-based recommendation using past interview performance
   - Consider job type (frontend, backend, full-stack, etc.)
   - Factor in job requirements complexity

6. **Job Listing Comparison**
   - Compare multiple job listings side-by-side
   - Highlight differences in requirements
   - Aggregate skills across multiple listings

---

## Usage Examples

### Example 1: Upload and Analyze Senior Python Role

**Input Job Description:**
```
Senior Python Developer

We're seeking an experienced Python developer to join our backend team.

Requirements:
- 5+ years of Python development experience
- Expert knowledge of Django and Flask frameworks
- Experience with PostgreSQL, Redis, and MongoDB
- Strong understanding of RESTful APIs and microservices
- Experience with Docker and Kubernetes
- Team leadership and mentoring skills

Education:
- Bachelor's degree in Computer Science or related field

Responsibilities:
- Lead backend development projects
- Design scalable and maintainable systems
- Mentor junior developers
- Conduct code reviews
- Collaborate with frontend team on API design
```

**Parsed Output:**
```json
{
  "required_skills": [
    "Python",
    "Django",
    "Flask",
    "PostgreSQL",
    "Redis",
    "MongoDB",
    "RESTful APIs",
    "Microservices",
    "Docker",
    "Kubernetes",
    "Team leadership",
    "Mentoring",
    "5+ years experience"
  ],
  "seniority_level": "senior",
  "requirements": {
    "education": ["Bachelor's degree in Computer Science"],
    "years_experience": "5+",
    "certifications": [],
    "responsibilities": [
      "Lead backend development projects",
      "Design scalable and maintainable systems",
      "Mentor junior developers",
      "Conduct code reviews",
      "Collaborate with frontend team on API design"
    ]
  },
  "recommended_template": "Senior System Design"
}
```

### Example 2: Entry-Level Frontend Developer

**Input Job Description:**
```
Junior Frontend Developer

Looking for a motivated junior developer to join our team.

Requirements:
- 0-2 years of web development experience
- Knowledge of HTML, CSS, JavaScript
- Familiarity with React or Vue.js
- Basic understanding of Git

Responsibilities:
- Build responsive web interfaces
- Collaborate with designers
- Learn from senior developers
```

**Parsed Output:**
```json
{
  "required_skills": [
    "HTML",
    "CSS",
    "JavaScript",
    "React",
    "Vue.js",
    "Git",
    "0-2 years experience"
  ],
  "seniority_level": "entry",
  "requirements": {
    "education": [],
    "years_experience": "0-2",
    "certifications": [],
    "responsibilities": [
      "Build responsive web interfaces",
      "Collaborate with designers",
      "Learn from senior developers"
    ]
  },
  "recommended_template": "Entry Level Coding"
}
```

---

## Related Documentation

- [Models Architecture](../architecture/models.md) - Database schema details
- [API Reference](../api/documents.md) - Full API documentation
- [Resume Parsing](./resume-parsing.md) - Similar AI parsing for resumes
- [Template Management](./template-management.md) - Interview template system

---

## Changelog

### Version 1.0 (2025-11-16)

**Issues Resolved:**
- ✅ Issue #21: Job listing upload and storage
- ✅ Issue #51: AI-powered required skills extraction
- ✅ Issue #52: Seniority level detection and requirements parsing
- ✅ Issue #53: Template recommendation and interview creation integration

**Features Added:**
- Job listing upload (text and file)
- OpenAI GPT-4o parsing integration
- Required skills extraction
- Seniority level detection (5 levels)
- Structured requirements extraction
- Template recommendation algorithm
- Pre-populated interview creation form
- Helper messages and UI indicators
- Comprehensive error handling
- Unit tests (35 test cases)
- BDD feature file (17 scenarios)

**Files Modified:**
- `models.py` - Added parsed data fields to UploadedJobListing
- `job_listing_parser.py` - New AI parsing service
- `serializers.py` - Added recommended_template_name field
- `views.py` - Added analyze endpoint and CreateChat URL parameter handling
- `document-list.html` - Added Create Interview button
- `chat-create.html` - Added helper message for pre-selected job listings
- `test_job_listing_parser.py` - Comprehensive test suite

**Database Migrations:**
- `0011_uploadedjoblisting_parsed_at_and_more.py` - Added parsing fields
