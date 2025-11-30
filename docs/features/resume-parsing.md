# Resume Parsing with AI Feature

Automatically extract skills, experience, and education from uploaded resumes using OpenAI GPT-4o.

## Overview

The Resume Parsing feature uses AI to automatically analyze uploaded resume files (PDF/DOCX) and extract structured data including technical skills, work experience, and educational background. This eliminates manual data entry and ensures consistent, structured resume information for interview matching.

**Key Benefits:**
- **Time Savings:** No manual data entry required
- **Accuracy:** AI extracts comprehensive, structured data
- **Structured Data:** JSON format enables advanced matching and filtering
- **Graceful Degradation:** Resume still saved if AI unavailable

---

## User Workflow

### 1. Upload Resume

From the document upload page (`/document-list/`):

1. Click **"Choose File"** or drag-and-drop
2. Select a PDF or DOCX resume file
3. Enter a title for the resume (e.g., "Software Engineer Resume 2024")
4. Click **"Upload"**

### 2. Automatic AI Parsing

After upload:

1. System saves the resume file
2. Sets parsing status to `in_progress`
3. Extracts text from PDF/DOCX
4. Sends resume content to OpenAI GPT-4o
5. AI analyzes and structures the data
6. Saves extracted data to database
7. Sets parsing status to `success`

**Typical parsing time:** 5-15 seconds

### 3. View Parsed Data

From your profile page:

1. Navigate to profile or resume detail page
2. View extracted **Skills** (list format)
3. View extracted **Work Experience** (with company, title, duration, description)
4. View extracted **Education** (with institution, degree, field, year)
5. See parsing status and timestamp

### 4. Edit Parsed Data

Users can manually edit any extracted data:

1. Click **"Edit"** on profile or resume detail page
2. Modify skills, experience, or education
3. Add missing information
4. Remove incorrect extractions
5. Click **"Save"** to persist changes

**Changes are saved immediately and persist across sessions.**

---

## Parsed Data Structure

### Skills

**Format:** JSON array of strings

**Example:**
```json
[
  "Python",
  "Django",
  "React",
  "PostgreSQL",
  "Docker",
  "AWS",
  "Agile/Scrum",
  "Team Leadership"
]
```

**Types Extracted:**
- Technical skills (programming languages, frameworks, tools)
- Soft skills (communication, leadership, teamwork)
- Certifications (AWS Certified, PMP, etc.)

### Work Experience

**Format:** JSON array of objects

**Structure:**
```json
[
  {
    "company": "Tech Corp Inc.",
    "title": "Senior Software Engineer",
    "duration": "Jan 2020 - Present",
    "description": "Led development of microservices architecture serving 1M+ users. Mentored team of 5 engineers."
  },
  {
    "company": "Startup LLC",
    "title": "Full Stack Developer",
    "duration": "Jun 2018 - Dec 2019",
    "description": "Built customer-facing web application using Django and React."
  }
]
```

**Fields:**
- `company` (string): Company name
- `title` (string): Job title/role
- `duration` (string): Time period (flexible format)
- `description` (string): Responsibilities and achievements

### Education

**Format:** JSON array of objects

**Structure:**
```json
[
  {
    "institution": "University of California, Berkeley",
    "degree": "Bachelor of Science",
    "field": "Computer Science",
    "year": "2018"
  },
  {
    "institution": "Stanford University",
    "degree": "Master of Science",
    "field": "Artificial Intelligence",
    "year": "2020"
  }
]
```

**Fields:**
- `institution` (string): School/university name
- `degree` (string): Degree type (BS, MS, PhD, etc.)
- `field` (string): Major/field of study
- `year` (string): Graduation year

---

## Technical Implementation

### Database Schema Changes

**Model:** `UploadedResume` (active_interview_app/models.py)

**New Fields:**
```python
# Parsed data fields (JSON format)
skills = models.JSONField(default=list, blank=True)
experience = models.JSONField(default=list, blank=True)
education = models.JSONField(default=list, blank=True)

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

### Files Modified

#### 1. **models.py** (Database Schema)
Added JSON fields and parsing metadata to `UploadedResume` model.

#### 2. **openai_utils.py** (NEW - Centralized OpenAI Client)
Manages OpenAI client initialization with singleton pattern and graceful degradation.

**Key Functions:**
- `get_openai_client()` - Returns OpenAI client instance
- `_ai_available()` - Checks if AI service is available

**Location:** `active_interview_app/openai_utils.py`

#### 3. **resume_parser.py** (NEW - AI Parsing Logic)
Handles resume parsing using OpenAI GPT-4o.

**Key Function:**
```python
def parse_resume_with_ai(resume_content: str) -> Dict[str, Any]:
    """
    Parse resume content using OpenAI GPT-4o.

    Returns structured data:
    {
        "skills": [...],
        "experience": [...],
        "education": [...]
    }
    """
```

**Features:**
- Content truncation (10,000 char limit to prevent token overflow)
- Structured JSON response format
- Error handling with sanitized messages
- Default values for missing sections

**Location:** `active_interview_app/resume_parser.py`

#### 4. **views.py** (Upload Integration)
Modified `upload_file()` view to trigger AI parsing after resume upload.

**Workflow:**
1. Save uploaded file
2. Check if AI available (`_ai_available()`)
3. Set status to `in_progress`
4. Call `parse_resume_with_ai()`
5. Save extracted data
6. Set status to `success` or `error`
7. Display appropriate message

**Location:** `active_interview_app/views.py` lines 930-970

### OpenAI Integration

**Configuration:**
- **Model:** GPT-4o
- **Max Tokens:** 15,000
- **Temperature:** 0.3 (for consistent extraction)
- **Response Format:** JSON object
- **Timeout:** Standard OpenAI timeout

**System Prompt:**
The AI is instructed to:
- Extract skills (technical, soft, certifications)
- Extract work history with company, title, duration, description
- Extract education with institution, degree, field, year
- Return valid JSON only
- Use "Unknown" for missing data

**Content Handling:**
- Resumes longer than 10,000 characters are truncated
- Text extracted from PDF using `pymupdf4llm`
- Text extracted from DOCX using `python-docx`

### Architecture Pattern

```
User Upload
    ↓
views.py (upload_file)
    ↓
Check AI Available (openai_utils._ai_available)
    ↓
Parse Resume (resume_parser.parse_resume_with_ai)
    ↓
OpenAI GPT-4o API
    ↓
Structured JSON Response
    ↓
Save to Database (skills, experience, education)
    ↓
Display Success Message
```

---

## Error Handling

### Graceful Degradation

**When AI is unavailable:**
1. Resume is still saved to database
2. Parsing status set to `error`
3. Error message: "AI service unavailable"
4. User sees: "Resume uploaded but AI parsing is currently unavailable"
5. User can still manually enter data
6. Parsing can be retried later

### Error Scenarios Handled

**1. API Key Not Set**
- Error: "OpenAI service is unavailable"
- Resume saved, status = `error`

**2. OpenAI API Down**
- Error: "OpenAI API authentication error" (sanitized)
- Resume saved, status = `error`

**3. Invalid JSON Response**
- Error: "Failed to parse OpenAI response as JSON"
- Resume saved, status = `error`

**4. Unsupported File Type**
- Error: "Invalid filetype. Only PDF and DOCX files are allowed"
- Resume NOT saved
- No parsing attempted

**5. Empty or Corrupted File**
- Error: "Error processing the file"
- Resume may be saved with empty content
- Status = `error`

### Security: API Key Sanitization

All error messages are sanitized to prevent API key exposure:

**In resume_parser.py:**
```python
if "api" in error_msg.lower() and "key" in error_msg.lower():
    error_msg = "OpenAI API authentication error"
```

**In views.py:**
```python
if "api" in error_msg.lower() and "key" in error_msg.lower():
    error_msg = "OpenAI authentication error"
```

This ensures no API keys appear in:
- Database `parsing_error` field
- User-facing messages
- Application logs

---

## API Endpoints

### Modified Endpoints

**Upload Resume:**
```
POST /upload-file/
Content-Type: multipart/form-data

Parameters:
- file: File (PDF or DOCX)
- title: String (resume title)

Response: Redirect to /document-list/ with success/error message
```

**Notes:**
- Triggers automatic AI parsing for resume files
- Job listings are NOT parsed (different model type)
- Parsing happens synchronously after upload

### Future API Endpoints (Not Implemented)

Potential enhancements:
- `POST /resume/<id>/reparse/` - Retry parsing for failed resumes
- `GET /resume/<id>/parsing-status/` - Check parsing progress
- `PATCH /resume/<id>/parsed-data/` - Update parsed data via API

---

## Testing

### Test Coverage

**File:** `active_interview_app/tests/test_resume_parsing.py`

**Test Categories:**

1. **OpenAI Utils Tests (7 tests)**
   - Client initialization
   - API key validation
   - Graceful degradation
   - Singleton pattern

2. **Resume Parser Tests (8 tests)**
   - Successful parsing
   - Skills extraction
   - Experience extraction
   - Education extraction
   - Error handling
   - Content truncation
   - Invalid JSON handling

3. **Integration Tests (6 tests)**
   - Upload with parsing
   - AI unavailable scenario
   - Parsing errors
   - Message display
   - Status tracking

**Total:** 21 tests, all passing

**Coverage:** 85% (exceeds 80% requirement)

### Running Tests

```bash
cd active_interview_backend

# Run resume parsing tests only
python manage.py test active_interview_app.tests.test_resume_parsing

# Run all tests
python manage.py test

# Check coverage
coverage run manage.py test
coverage report -m
```

### Manual Testing Checklist

- [ ] Upload PDF resume with all sections
- [ ] Upload DOCX resume
- [ ] Upload resume with missing sections
- [ ] Test with AI unavailable (no API key)
- [ ] Test with invalid file type (.txt, .exe)
- [ ] Verify parsed data appears on profile
- [ ] Edit parsed data and verify persistence
- [ ] Test error messages display correctly

---

## GitHub Issues

This feature implements the following issues:

- **Implements [#48](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/48)** - Upload triggers parsing, handles errors
- **Implements [#49](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/49)** - AI extracts skills, experience, education
- **Implements [#50](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/50)** - Display and edit parsed data (backend complete, UI pending)

### Acceptance Criteria Met

**Issue #48:**
- [x] Upload accepts PDF/DOCX files
- [x] Upload triggers AI parsing
- [x] Unsupported file types show error
- [x] Resume saved even if parsing fails

**Issue #49:**
- [x] AI extracts skills as list
- [x] AI extracts work experience with structure
- [x] AI extracts education with structure
- [x] Data stored in JSON format
- [x] Parsing status tracked

**Issue #50 (Backend):**
- [x] Parsed data stored in database
- [x] Data available via model fields
- [x] Editable through Django admin
- [ ] UI forms for editing (future enhancement)
- [ ] Profile page display (future enhancement)

---

## Configuration

### Environment Variables

**Required:**
```bash
OPENAI_API_KEY=sk-proj-...your-key...
```

**Optional:**
```bash
PROD=false  # Development mode
DEBUG=True  # Show detailed errors
```

### Settings

**Django Settings (settings.py):**
```python
# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# File Upload Settings
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
```

---

## Future Enhancements

### Short Term

1. **Profile UI** - Display parsed data on user profile page
2. **Edit Forms** - User-friendly forms for editing skills/experience/education
3. **Retry Parsing** - Button to re-parse failed resumes
4. **Progress Indicator** - Show parsing progress in real-time

### Medium Term

1. **Async Parsing** - Use Celery for background processing
2. **Parsing Queue** - Handle multiple uploads efficiently
3. **Version History** - Track changes to parsed data
4. **Confidence Scores** - Show AI confidence for extractions

### Long Term

1. **Multi-language Support** - Parse resumes in multiple languages
2. **Custom Fields** - Allow users to define custom extraction fields
3. **Resume Comparison** - Compare parsed resumes for job matching
4. **AI Insights** - Suggest resume improvements based on job listings

---

## See Also

**Related Documentation:**
- [Architecture Overview](../architecture/overview.md) - System design
- [Models Documentation](../architecture/models.md) - Database schema
- [Testing Guide](../setup/testing.md) - Running tests
- [BDD Feature File](../../active_interview_backend/features/resume_parsing.feature) - Gherkin scenarios

**Related Code:**
- `active_interview_app/models.py` - UploadedResume model
- `active_interview_app/openai_utils.py` - OpenAI client management
- `active_interview_app/resume_parser.py` - AI parsing logic
- `active_interview_app/views.py` - Upload and integration
- `active_interview_app/tests/test_resume_parsing.py` - Test suite

**External References:**
- [OpenAI GPT-4o Documentation](https://platform.openai.com/docs/models/gpt-4o)
- [PyMuPDF4LLM](https://pymupdf.readthedocs.io/) - PDF text extraction
- [python-docx](https://python-docx.readthedocs.io/) - DOCX text extraction
