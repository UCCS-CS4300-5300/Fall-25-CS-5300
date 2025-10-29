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
- `UploadedResume` (one-to-many)
- `UploadedJobListing` (one-to-many)
- `Chat` (one-to-many)

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

**Location:** `active_interview_app/models.py`

Stores job posting documents with extracted text.

**Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | ForeignKey(User) | Job listing owner | CASCADE |
| `title` | CharField(100) | User-defined title | Required |
| `file` | FileField | Uploaded file (optional) | blank=True, null=True |
| `text_content` | TextField | Job description text | Optional, blank=True |
| `uploaded_at` | DateTimeField | Upload timestamp | auto_now_add=True |

**Methods:**
- `__str__()` - Returns title

**Creation Methods:**
- **File upload:** Upload PDF/DOCX file
- **Paste text:** Directly paste job description (no file)

**Deletion Behavior:**
- When user is deleted: Job listing is deleted (CASCADE)

**Example:**
```python
# Via file upload
job = UploadedJobListing.objects.create(
    user=user,
    title="Senior Django Developer",
    file=uploaded_file,
    text_content="Extracted job text..."
)

# Via text paste
job = UploadedJobListing.objects.create(
    user=user,
    title="Senior Django Developer",
    text_content="Pasted job description..."
)
```

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
     ├─────< UploadedJobListing
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
| User | Chat | CASCADE (delete chat) |
| User | TokenUsage | SET_NULL (keep record) |
| User | MergeTokenStats | SET_NULL (keep record) |
| Chat | ExportableReport | CASCADE (delete report) |
| UploadedResume | Chat | SET_NULL (keep chat, remove link) |
| UploadedJobListing | Chat | SET_NULL (keep chat, remove link) |

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
- UploadedResume
- UploadedJobListing
- Chat
- ExportableReport
- TokenUsage
- MergeTokenStats

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
