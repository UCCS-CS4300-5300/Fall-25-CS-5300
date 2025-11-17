# Database Models Reference

Complete reference for all Django models in Active Interview Service.

## Core Models

### User

**Built-in Django model** (`django.contrib.auth.models.User`)

Extended with group-based permissions.

**Key Fields:**
- `username` (CharField) - Unique username
- `email` (EmailField) - User email
- `password` (CharField) - Hashed password
- `is_active` (BooleanField) - Account status
- `is_staff` (BooleanField) - Admin access
- `date_joined` (DateTimeField) - Registration date

**Groups:**
- `average_role` - Standard user permissions (created manually)

**Related models:**
- `UserProfile` (one-to-one) - **NEW: Issue #69**
- `UploadedResume` (one-to-many)
- `UploadedJobListing` (one-to-many)
- `Chat` (one-to-many)

---

### UserProfile

**Location:** `active_interview_app/models.py:11-66`

**Issue**: [#69](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/69)

Extended user profile for role-based access control and OAuth support.

**Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | OneToOneField(User) | Associated user | CASCADE, related_name='profile' |
| `role` | CharField(20) | User role | Choices: admin/interviewer/candidate, default='candidate' |
| `auth_provider` | CharField(50) | Auth method | default='local' |
| `created_at` | DateTimeField | Profile creation | auto_now_add=True |
| `updated_at` | DateTimeField | Last update | auto_now=True |

**Role Choices:**
- `ADMIN` (`'admin'`) - Full system access, can manage roles
- `INTERVIEWER` (`'interviewer'`) - Can view all candidate profiles
- `CANDIDATE` (`'candidate'`) - Default role, own data only

**Methods:**
- `__str__()` - Returns formatted string with username, role, and auth provider

**Signals:**
- `create_user_profile` - Auto-creates profile when User is created
- `save_user_profile` - Auto-saves profile when User is saved

**Usage:**
```python
# Access user's role
role = request.user.profile.role

# Check if admin
if request.user.profile.role == 'admin':
    # Admin logic
    pass
```

**Related Documentation:**
- [RBAC Feature Guide](../features/rbac.md)
- [API Reference - RBAC Endpoints](api.md#rbac-endpoints)

---

### UploadedResume

**Location:** `active_interview_app/models.py`

Stores user resume files with extracted text content.

**Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | ForeignKey(User) | Resume owner | CASCADE |
| `title` | CharField(100) | User-defined title | Required |
| `file` | FileField | Uploaded file | `upload_to='uploads/'` |
| `text_content` | TextField | Extracted text | Optional, blank=True |
| `uploaded_at` | DateTimeField | Upload timestamp | auto_now_add=True |

**Methods:**
- `__str__()` - Returns title

**File Processing:**
- PDF files: Extracted with `pymupdf4llm.to_markdown()`
- DOCX files: Extracted with `python-docx`
- Text stored in `text_content` field for AI processing

**Deletion Behavior:**
- When user is deleted: Resume is deleted (CASCADE)
- File is also deleted from filesystem

**Example:**
```python
resume = UploadedResume.objects.create(
    user=user,
    title="Software Engineer Resume",
    file=uploaded_file,
    text_content="Extracted resume text..."
)
```

---

### UploadedJobListing

**Location:** `active_interview_app/models.py:104-184`

**Issues:** [#21](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/21), [#51](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/51), [#52](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/52), [#53](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/53)

Stores job posting documents with AI-powered parsing of requirements, skills, and seniority level.

**Core Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | ForeignKey(User) | Job listing owner | CASCADE |
| `title` | CharField(255) | User-defined or extracted title | Optional |
| `filename` | CharField(255) | Original filename | Required |
| `file` | FileField | Uploaded file (optional) | upload_to='uploads/' |
| `content` | TextField | Job description text | Required |
| `created_at` | DateTimeField | Upload timestamp | auto_now_add=True |

**AI-Parsed Fields (Issues #51, #52):**

| Field | Type | Description | Structure |
|-------|------|-------------|-----------|
| `required_skills` | JSONField | Extracted skills | List: `["Python", "Django", "5+ years"]` |
| `seniority_level` | CharField(50) | Detected seniority | Choices: entry/mid/senior/lead/executive |
| `requirements` | JSONField | Structured requirements | See structure below |
| `recommended_template` | ForeignKey(InterviewTemplate) | Auto-recommended template | SET_NULL, optional (Issue #53) |

**Parsing Metadata:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `parsing_status` | CharField(20) | AI parsing status | Choices: pending/in_progress/success/error |
| `parsing_error` | TextField | Error message if failed | Optional |
| `parsed_at` | DateTimeField | Parsing completion time | Optional |

**Seniority Level Choices:**
- `entry` - Entry Level (0-2 years)
- `mid` - Mid Level (2-5 years)
- `senior` - Senior (5-8 years)
- `lead` - Lead/Principal (8-12 years)
- `executive` - Executive/Director (12+ years)

**Requirements JSON Structure:**
```json
{
  "education": ["Bachelor's in Computer Science", "Master's preferred"],
  "years_experience": "5+",
  "certifications": ["AWS Certified", "PMP"],
  "responsibilities": [
    "Lead backend development projects",
    "Mentor junior developers",
    "Design scalable systems"
  ]
}
```

**Methods:**
- `__str__()` - Returns title

**Creation Methods:**
- **File upload:** Upload PDF/DOCX/TXT file (content auto-extracted)
- **Paste text:** Directly paste job description (no file)
- **Auto-parsing:** AI parsing triggered automatically after creation

**AI Parsing Service:**
- **Module:** `job_listing_parser.py`
- **Model:** OpenAI GPT-4o
- **Extracts:** Required skills, seniority level, structured requirements
- **Recommends:** Best matching interview template based on seniority

**Deletion Behavior:**
- When user is deleted: Job listing is deleted (CASCADE)
- When recommended template deleted: Set to NULL (SET_NULL)

**Example (Manual Creation):**
```python
# Via file upload
job = UploadedJobListing.objects.create(
    user=user,
    filename="senior_dev_role.txt",
    title="Senior Django Developer",
    file=uploaded_file,
    content="Extracted job text...",
    parsing_status='pending'
)

# Via text paste
job = UploadedJobListing.objects.create(
    user=user,
    filename="",
    title="Senior Django Developer",
    content="Pasted job description...",
    parsing_status='pending'
)
```

**Example (After AI Parsing):**
```python
# Get parsed job listing
job = UploadedJobListing.objects.get(id=1)

# Access parsed data
print(job.required_skills)
# ['Python', 'Django', 'PostgreSQL', '5+ years experience']

print(job.seniority_level)
# 'senior'

print(job.requirements)
# {
#   'education': ["Bachelor's in CS"],
#   'years_experience': '5+',
#   'certifications': ['AWS'],
#   'responsibilities': ['Lead projects', 'Mentor developers']
# }

print(job.recommended_template.name)
# 'Senior System Design'
```

**Related Documentation:**
- [Job Listing Ingestion Feature Guide](../features/job-listing-ingestion.md)
- [API Reference - Job Listing Endpoints](api.md#job-listing-endpoints)

---

### Chat

**Location:** `active_interview_app/models.py`

Central model representing an interview session.

**Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | ForeignKey(User) | Chat owner | CASCADE |
| `title` | CharField(50) | Chat name | Required |
| `messages` | JSONField | Message array | default=list, blank=True |
| `key_questions` | JSONField | Timed questions | default=list, blank=True |
| `resume` | ForeignKey(UploadedResume) | Linked resume | SET_NULL, optional |
| `job_listing` | ForeignKey(UploadedJobListing) | Linked job | SET_NULL, optional |
| `difficulty` | IntegerField | Difficulty (1-10) | default=5, validators=[1-10] |
| `type` | CharField(5) | Interview type | Choices: GEN/SKL/PER/FIN |
| `created_at` | DateTimeField | Creation time | auto_now_add=True |
| `updated_at` | DateTimeField | Last update | auto_now=True |

**Interview Types:**

| Code | Display Name | Description |
|------|--------------|-------------|
| `GEN` | General Interview | Broad general questions |
| `SKL` | Industry Skills | Technical/domain-specific |
| `PER` | Personality/Culture Fit | Behavioral questions |
| `FIN` | Final Screening | Comprehensive final round |

**JSON Field Structures:**

**messages:**
```json
[
  {
    "role": "user",
    "content": "Tell me about yourself."
  },
  {
    "role": "assistant",
    "content": "AI response here..."
  }
]
```

**key_questions:**
```json
[
  {
    "question": "Describe a challenging project you worked on.",
    "time_limit": 300
  }
]
```

**Methods:**
- `__str__()` - Returns title
- `get_type_display()` - Returns human-readable type name

**Deletion Behavior:**
- When user deleted: Chat deleted (CASCADE)
- When resume deleted: Set to NULL (SET_NULL)
- When job listing deleted: Set to NULL (SET_NULL)

**Example:**
```python
chat = Chat.objects.create(
    user=user,
    title="Python Developer Interview",
    resume=resume,
    job_listing=job,
    difficulty=7,
    type="SKL",
    messages=[],
    key_questions=[]
)
```

---

### ExportableReport

**Location:** `active_interview_app/models.py`

Stores structured interview report data for PDF generation.

**Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `chat` | OneToOneField(Chat) | Linked chat session | CASCADE |
| `generated_at` | DateTimeField | Generation time | auto_now_add=True |
| `last_updated` | DateTimeField | Last update | auto_now=True |
| `professionalism_score` | IntegerField | Professionalism (0-100) | Optional, validators=[0-100] |
| `subject_knowledge_score` | IntegerField | Technical knowledge | Optional, validators=[0-100] |
| `clarity_score` | IntegerField | Communication clarity | Optional, validators=[0-100] |
| `overall_score` | IntegerField | Overall performance | Optional, validators=[0-100] |
| `feedback_text` | TextField | AI-generated feedback | Optional |
| `question_responses` | JSONField | Q&A array | default=list |
| `total_questions_asked` | IntegerField | Question count | default=0 |
| `total_responses_given` | IntegerField | Response count | default=0 |
| `interview_duration_minutes` | IntegerField | Duration | Optional |
| `pdf_generated` | BooleanField | PDF status | default=False |
| `pdf_file` | FileField | Generated PDF | Optional |

**JSON Field Structure:**

**question_responses:**
```json
[
  {
    "question": "Tell me about yourself.",
    "answer": "User's response...",
    "score": 8,
    "feedback": "Strong response with clear examples."
  }
]
```

**Score Ranges:**
- 0-100 for all score fields
- Validators ensure scores don't exceed range

**Methods:**
- `__str__()` - Returns chat title + "Report"

**Deletion Behavior:**
- When chat deleted: Report deleted (CASCADE)

**Example:**
```python
report = ExportableReport.objects.create(
    chat=chat,
    professionalism_score=85,
    subject_knowledge_score=90,
    clarity_score=78,
    overall_score=84,
    feedback_text="Great interview performance...",
    question_responses=[
        {
            "question": "Describe your experience.",
            "answer": "User answer...",
            "score": 9,
            "feedback": "Excellent detail."
        }
    ],
    total_questions_asked=10,
    total_responses_given=10
)
```

---

### InterviewTemplate

**Location:** `active_interview_app/models.py:285-353`

**Issues:** [#53](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/53), [#124](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/124)

Stores customizable interview templates with question banks, tags, and difficulty distribution.

**Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | ForeignKey(User) | Template owner | CASCADE |
| `name` | CharField(200) | Template name | Required |
| `description` | TextField | Template description | Optional |
| `difficulty` | IntegerField | Overall difficulty (1-5) | validators=[1-5] |
| `question_count` | IntegerField | Number of questions | validators=[1-50] |
| `easy_percentage` | IntegerField | % easy questions | validators=[0-100], default=33 |
| `medium_percentage` | IntegerField | % medium questions | validators=[0-100], default=34 |
| `hard_percentage` | IntegerField | % hard questions | validators=[0-100], default=33 |
| `tags` | ManyToManyField(Tag) | Template tags | Optional |
| `question_banks` | ManyToManyField(QuestionBank) | Associated banks | Optional |
| `created_at` | DateTimeField | Creation time | auto_now_add=True |
| `updated_at` | DateTimeField | Last update | auto_now=True |

**Difficulty Levels:**
- `1` - Very Easy (Entry level, basic questions)
- `2` - Easy (Junior level)
- `3` - Medium (Mid-level, standard technical)
- `4` - Hard (Senior level, complex scenarios)
- `5` - Very Hard (Lead/Principal, system design)

**Difficulty Distribution:**
- Percentages must sum to 100 (validated via `validate_difficulty_distribution()`)
- Default: 33% easy, 34% medium, 33% hard
- Can be customized per template

**Methods:**
- `__str__()` - Returns template name
- `validate_difficulty_distribution()` - Checks percentages sum to 100
- `to_dict()` - Returns JSON-serializable dictionary

**Deletion Behavior:**
- When user deleted: Template deleted (CASCADE)
- When tag deleted: Relationship removed (ManyToMany)
- When question bank deleted: Relationship removed (ManyToMany)
- When template deleted: Job listings with this recommendation set to NULL (SET_NULL)

**Example:**
```python
from active_interview_app.models import InterviewTemplate, Tag, QuestionBank

# Create template
template = InterviewTemplate.objects.create(
    user=user,
    name="Senior System Design",
    description="Advanced system design interview for senior engineers",
    difficulty=4,
    question_count=15,
    easy_percentage=20,
    medium_percentage=40,
    hard_percentage=40
)

# Add tags
backend_tag = Tag.objects.get(name="Backend")
python_tag = Tag.objects.get(name="Python")
template.tags.add(backend_tag, python_tag)

# Add question banks
system_design_bank = QuestionBank.objects.get(name="System Design")
template.question_banks.add(system_design_bank)

# Validate distribution
assert template.validate_difficulty_distribution()  # Should be True
```

**Usage in Job Listing Recommendations:**

Templates are automatically recommended based on job listing seniority:

| Seniority Level | Recommended Difficulty |
|-----------------|------------------------|
| Entry | 1-2 (Easy) |
| Mid | 2-3 (Medium) |
| Senior | 3-4 (Hard) |
| Lead | 4-5 (Very Hard) |
| Executive | 3-5 (Hard to Very Hard) |

**Related Documentation:**
- [Template Management Feature Guide](../features/template-management.md)
- [Job Listing Ingestion Feature Guide](../features/job-listing-ingestion.md)

---

## Token Tracking Models

### TokenUsage

**Location:** `active_interview_app/token_usage_models.py`

Tracks OpenAI API token usage per request.

**Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | ForeignKey(User) | User who made request | SET_NULL, optional |
| `model_name` | CharField(50) | AI model used | e.g., "gpt-4o" |
| `prompt_tokens` | IntegerField | Input tokens | Required |
| `completion_tokens` | IntegerField | Output tokens | Required |
| `total_tokens` | IntegerField | Sum | Auto-calculated on save |
| `request_type` | CharField(50) | Request category | Optional |
| `branch_name` | CharField(100) | Git branch | Optional |
| `created_at` | DateTimeField | Request time | auto_now_add=True |

**Methods:**
- `save()` - Auto-calculates `total_tokens`
- `estimate_cost()` - Calculates cost based on model
- `get_branch_summary(branch)` - Aggregates tokens for a branch

**Pricing (as of implementation):**
- GPT-4o: $0.03/1K prompt, $0.06/1K completion
- Claude Sonnet 4.5: $0.003/1K prompt, $0.015/1K completion

**Example:**
```python
TokenUsage.objects.create(
    user=user,
    model_name="gpt-4o",
    prompt_tokens=1500,
    completion_tokens=800,
    request_type="chat_completion",
    branch_name="feature/new-interview"
)
```

---

### MergeTokenStats

**Location:** `active_interview_app/merge_stats_models.py`

Tracks cumulative token usage when branches are merged.

**Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `source_branch` | CharField(100) | Merged branch name | Required |
| `target_branch` | CharField(100) | Target branch | default="main" |
| `commit_sha` | CharField(40) | Merge commit | unique=True |
| `merged_by` | ForeignKey(User) | User who merged | SET_NULL, optional |
| `merge_date` | DateTimeField | Merge timestamp | auto_now_add=True |
| `total_prompt_tokens` | IntegerField | Sum prompt tokens | default=0 |
| `total_completion_tokens` | IntegerField | Sum completion tokens | default=0 |
| `total_tokens` | IntegerField | Sum all tokens | default=0 |
| `request_count` | IntegerField | Number of requests | default=0 |
| `cumulative_total_tokens` | IntegerField | Running total | default=0 |
| `cumulative_total_cost` | FloatField | Running cost | default=0.0 |
| `pr_number` | IntegerField | GitHub PR number | Optional |
| `notes` | TextField | Additional notes | Optional |

**Properties:**
- `branch_cost` - Calculates cost for this merge

**Class Methods:**
- `create_from_branch(branch, commit, user)` - Creates merge record
- `get_total_cumulative_tokens()` - Total across all merges
- `get_total_cumulative_cost()` - Total cost across all merges
- `get_breakdown_summary()` - Detailed breakdown

**Example:**
```python
merge_stat = MergeTokenStats.create_from_branch(
    source_branch="feature/new-ui",
    commit_sha="abc123",
    merged_by=user
)
```

**Cumulative Tracking:**

Each new merge automatically calculates:
```python
cumulative_total_tokens = previous_cumulative + this_merge_tokens
cumulative_total_cost = previous_cumulative + this_merge_cost
```

---

## Model Relationships

### Entity Relationship Diagram

```
┌──────────┐
│   User   │
└────┬─────┘
     │
     ├─────< UploadedResume
     │
     ├─────< UploadedJobListing ──> InterviewTemplate (recommended_template, optional)
     │
     ├─────< InterviewTemplate ────< Tag (ManyToMany)
     │       │                  └───< QuestionBank (ManyToMany)
     │
     ├─────< Chat ──────< ExportableReport (OneToOne)
     │       │
     │       ├──> UploadedResume (optional)
     │       └──> UploadedJobListing (optional)
     │
     ├─────< TokenUsage
     │
     └─────< MergeTokenStats
```

### Deletion Cascade Rules

| Parent | Child | Behavior |
|--------|-------|----------|
| User | UploadedResume | CASCADE (delete resume) |
| User | UploadedJobListing | CASCADE (delete job) |
| User | InterviewTemplate | CASCADE (delete template) |
| User | Chat | CASCADE (delete chat) |
| User | TokenUsage | SET_NULL (keep record) |
| User | MergeTokenStats | SET_NULL (keep record) |
| Chat | ExportableReport | CASCADE (delete report) |
| UploadedResume | Chat | SET_NULL (keep chat, remove link) |
| UploadedJobListing | Chat | SET_NULL (keep chat, remove link) |
| InterviewTemplate | UploadedJobListing | SET_NULL (keep job listing, remove recommendation) |
| Tag | InterviewTemplate | REMOVE (ManyToMany, keep both) |
| QuestionBank | InterviewTemplate | REMOVE (ManyToMany, keep both) |

---

## Database Indexes

**Automatically indexed fields:**
- Primary keys (`id`)
- Foreign keys
- Unique fields (`commit_sha`)

**Consider adding indexes for:**
- `Chat.created_at` (frequent ordering)
- `TokenUsage.branch_name` (frequent filtering)
- `MergeTokenStats.merge_date` (frequent ordering)

---

## Migrations

**Location:** `active_interview_app/migrations/`

**Key migrations:**
- `0001_initial.py` - Initial models
- `0002_*.py` - Token tracking models
- `0003_alter_chat_type_exportablereport.py` - ExportableReport model

**Creating migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Viewing migrations:**
```bash
python manage.py showmigrations
python manage.py sqlmigrate active_interview_app 0001
```

---

## Admin Interface

All models registered in Django admin (`admin.py`):

**Access:** `http://127.0.0.1:8000/admin`

**Registered models:**
- User (Django default)
- UserProfile
- UploadedResume
- UploadedJobListing
- InterviewTemplate
- Tag
- QuestionBank
- Chat
- ExportableReport
- TokenUsage
- MergeTokenStats
- InvitedInterview
- RoleChangeRequest

**Admin features:**
- List views with filters
- Search by title/username
- Inline editing for related objects
- CSV export (with django-import-export)

---

## Model Usage Examples

### Creating an Interview Session

```python
from django.contrib.auth.models import User
from active_interview_app.models import Chat, UploadedResume

# Get or create user
user = User.objects.get(username='john')

# Get user's resume
resume = UploadedResume.objects.filter(user=user).first()

# Create chat
chat = Chat.objects.create(
    user=user,
    title="Senior Django Dev Interview",
    resume=resume,
    difficulty=8,
    type="SKL"
)
```

### Generating a Report

```python
from active_interview_app.models import ExportableReport

# Get chat
chat = Chat.objects.get(id=1)

# Create or update report
report, created = ExportableReport.objects.get_or_create(chat=chat)
report.professionalism_score = 85
report.subject_knowledge_score = 92
report.clarity_score = 78
report.overall_score = 85
report.save()
```

### Querying Token Usage

```python
from active_interview_app.token_usage_models import TokenUsage, MergeTokenStats

# Get tokens for a branch
tokens = TokenUsage.objects.filter(branch_name='feature/chat').aggregate(
    total=Sum('total_tokens')
)

# Get cumulative stats
total_tokens = MergeTokenStats.get_total_cumulative_tokens()
total_cost = MergeTokenStats.get_total_cumulative_cost()
```

---

## Next Steps

- **[API Reference](api.md)** - REST API endpoints
- **[Architecture Overview](overview.md)** - System architecture
- **[Testing Guide](../setup/testing.md)** - Model testing examples
