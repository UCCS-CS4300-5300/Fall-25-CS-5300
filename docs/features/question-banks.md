# Question Banks and Interview Templates Feature

Create, manage, and auto-assemble interview questions with intelligent validation and tagging.

## Overview

The Question Banks feature allows Interviewers and Admins to organize interview questions into categorized banks, tag them for easy filtering, and automatically assemble customized interview templates based on difficulty and topic requirements. The system includes comprehensive validation to prevent invalid configurations and provides a professional modal-based user interface.

**Key Benefits:**
- **Organized Question Management:** Group related questions into banks
- **Intelligent Tagging:** Tag questions with topics (e.g., #python, #algorithms)
- **Auto-Assembly:** Automatically create interviews matching difficulty requirements
- **Smart Validation:** Prevents creating interviews with insufficient questions
- **Individual Section Management:** Each question becomes its own manageable section
- **Professional UX:** No browser alerts - all notifications via themed modals

---

## User Workflow

### 1. Create a Question Bank

From the Question Banks page (`/question-banks/`):

1. Click **"Create Question Bank"**
2. Enter a name (e.g., "Python Backend Questions")
3. Enter an optional description
4. Click **"Create"**

**Permissions:** Interviewer or Admin role required

### 2. Add Questions to Bank

After creating a bank:

1. Click **"View Questions"** on a bank card
2. Click **"Add Question"** button
3. Enter the question text
4. Select difficulty level:
   - **Easy:** Fundamental concepts, basic syntax
   - **Medium:** Problem-solving, moderate complexity
   - **Hard:** Advanced topics, system design
5. Select or create tags (e.g., #python, #django, #algorithms)
6. Click **"Save Question"**

**Tag Management:**
- Tags must start with `#` symbol
- Existing tags are suggested automatically
- Create new tags inline while adding questions
- Multiple tags can be assigned to each question

### 3. Auto-Assemble an Interview

From the Question Banks page:

1. Click **"Auto-Assemble Interview"**
2. Configure the interview:
   - **Title:** Name for the interview (e.g., "Python Developer Round 1")
   - **Tags:** Select relevant topics (must select at least one)
   - **Question Count:** Total number of questions needed
   - **Difficulty Distribution:**
     - Easy: Percentage (0-100)
     - Medium: Percentage (0-100)
     - Hard: Percentage (0-100)
     - *Must total exactly 100%*
   - **Question Bank:** (Optional) Limit to specific bank
   - **Randomize:** Shuffle questions (default: enabled)
3. Click **"Assemble Interview"**

**Smart Validation:**
- System validates sufficient questions exist before proceeding
- Provides detailed breakdown if insufficient questions
- Shows available vs. requested by difficulty level
- Clear actionable error messages

### 4. Review and Save Template

After successful assembly:

1. Review the assembled questions
2. See difficulty breakdown and tag distribution
3. Click **"Save as Interview Template"**
4. Template is saved with individual sections for each question
5. Form automatically clears for next interview

**Template Structure:**
- Each question gets its own section
- Sections are weighted evenly (totaling 100%)
- Sections maintain question metadata (difficulty, tags)
- Section titles include question text (truncated to 50 chars)

---

## Question Bank Management

### Creating Question Banks

**Purpose:** Organize questions by topic, role, or interview type

**Best Practices:**
- Use descriptive names (e.g., "Python Backend Questions", "JavaScript Frontend")
- Group related questions together
- Add descriptions explaining the bank's purpose
- Keep banks focused on specific topics

**Example Banks:**
```
Backend Development
├── Python/Django questions
├── Database design
└── API development

Frontend Development
├── JavaScript/React
├── HTML/CSS
└── Performance optimization

System Design
├── Scalability
├── Architecture patterns
└── Distributed systems
```

### Question Management

#### Adding Questions

**Question Text Guidelines:**
- Clear, specific questions
- Include context if needed
- Avoid ambiguous wording
- Test for understanding, not memorization

**Example Questions:**

**Easy:**
```
What is the difference between a list and a tuple in Python?
```

**Medium:**
```
Explain how Django's ORM handles database transactions.
What are the implications of using atomic() decorators?
```

**Hard:**
```
Design a distributed caching system that can handle 1M
requests per second. Discuss consistency, availability,
and partition tolerance trade-offs.
```

#### Difficulty Levels

| Level | Criteria | Time to Answer |
|-------|----------|----------------|
| **Easy** | Basic concepts, definitions, simple syntax | 2-3 minutes |
| **Medium** | Problem-solving, code implementation, moderate depth | 5-10 minutes |
| **Hard** | System design, advanced algorithms, complex trade-offs | 15+ minutes |

#### Tagging System

**Tag Format:** Must start with `#` symbol

**Common Tags:**
- **Languages:** `#python`, `#javascript`, `#java`, `#go`
- **Frameworks:** `#django`, `#react`, `#angular`, `#nodejs`
- **Topics:** `#algorithms`, `#databases`, `#testing`, `#security`
- **Concepts:** `#async`, `#concurrency`, `#design-patterns`, `#api`

**Tag Best Practices:**
- Use lowercase for consistency
- Be specific (use `#django-orm` not just `#django`)
- Multiple tags per question (2-4 tags recommended)
- Create tags that aid in filtering

### Editing and Deleting

**Edit Questions:**
1. View the question bank
2. Click **"Edit"** on a question
3. Modify text, difficulty, or tags
4. Save changes

**Delete Questions:**
1. View the question bank
2. Click **"Delete"** on a question
3. Confirm deletion
4. Question is permanently removed

**Delete Banks:**
1. From Question Banks page
2. Click **"Delete"** on a bank card
3. Confirm deletion
4. Bank and all its questions are removed

---

## Auto-Assembly System

### How Auto-Assembly Works

1. **Tag Selection:** Choose topics to include (OR logic - questions matching ANY tag)
2. **Difficulty Calculation:** System calculates exact counts per difficulty:
   - Easy count = Total × Easy percentage
   - Medium count = Total × Medium percentage
   - Hard count = Total - Easy - Medium (absorbs rounding)
3. **Question Selection:** Retrieves matching questions from selected banks/tags
4. **Randomization:** Shuffles questions if enabled (default)
5. **Validation:** Ensures sufficient questions before proceeding
6. **Template Creation:** Each question becomes an individual section

### Validation System

#### Two-Level Validation

**Level 1: Total Count Validation**
- Checks if total available questions ≥ requested count
- Considers only tagged questions matching criteria
- Returns error if insufficient

**Example Error:**
```
Not enough questions available. Requested: 20, Available: 10

You requested 20 questions, but only 10 are available
with the selected tags and difficulty distribution.
```

**Level 2: Per-Difficulty Validation**
- Validates each difficulty level independently
- Ensures enough questions per difficulty category
- Shows detailed breakdown of shortfall

**Example Error:**
```
Not enough questions for difficulty levels:
easy (need 5, have 3), hard (need 4, have 2)

Breakdown:
• Easy: 5 requested, 3 available ❌
• Medium: 3 requested, 5 available ✅
• Hard: 4 requested, 2 available ❌

Suggestions:
• Reduce the total number of questions
• Adjust the difficulty distribution percentages
• Change tag selection to include more questions
• Add more questions to your question bank
```

#### Validation Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| `200 OK` | Success | Interview assembled successfully |
| `400 BAD REQUEST` | Validation Error | Insufficient questions available |
| `404 NOT FOUND` | Template Error | Template ID not found |

### Difficulty Distribution Examples

#### Balanced Interview (Recommended)
```
Total Questions: 10
Easy: 30% (3 questions)
Medium: 50% (5 questions)
Hard: 20% (2 questions)

Good for: General assessment, entry to mid-level roles
```

#### Advanced Interview
```
Total Questions: 15
Easy: 20% (3 questions)
Medium: 40% (6 questions)
Hard: 40% (6 questions)

Good for: Senior roles, specialized positions
```

#### Screening Interview
```
Total Questions: 8
Easy: 50% (4 questions)
Medium: 40% (3 questions)
Hard: 10% (1 question)

Good for: Initial screening, junior roles
```

### Randomization

**Enabled (Default):**
- Questions selected randomly from available pool
- Different interviews each time
- Prevents pattern memorization

**Disabled:**
- Questions selected in order (by ID)
- Consistent question selection
- Useful for standardized assessments

---

## Interview Template Structure

### Section-Based Architecture

**Design Philosophy:** Each question is its own section for maximum flexibility

**Benefits:**
1. **Individual Management:** Reorder, remove, or edit any question independently
2. **Flexible Weighting:** Adjust importance of each question
3. **Clear Organization:** Section titles show question content
4. **Metadata Preservation:** Difficulty and tags retained in section content

### Section Format

```json
{
  "id": "uuid-v4-string",
  "title": "Question 1: What is the difference between a list...",
  "content": "What is the difference between a list and a tuple in Python?\n\nDifficulty: easy\nTags: #python, #basics",
  "order": 0,
  "weight": 33
}
```

**Fields:**
- **id:** Unique identifier (UUID v4)
- **title:** Question number + truncated question text (max 50 chars)
- **content:** Full question text + metadata
- **order:** Sequential position (0, 1, 2...)
- **weight:** Percentage value (sum = 100%)

### Weight Distribution

**Automatic Distribution:**
- Weights divided evenly among all questions
- Remainders added to first section
- Always totals exactly 100%

**Examples:**

**3 Questions:**
```
Section 1: 34% (33 + 1 remainder)
Section 2: 33%
Section 3: 33%
Total: 100%
```

**5 Questions:**
```
Section 1-5: 20% each
Total: 100%
```

**7 Questions:**
```
Section 1: 15% (14 + 1 remainder)
Section 2-7: 14% each
Total: 100%
```

---

## User Interface Features

### Modal System

**Design:** All notifications use Bootstrap modals (no browser alerts)

#### Notification Types

| Type | Color | Icon | Use Case |
|------|-------|------|----------|
| **Success** | Green | ✓ | Successful operations |
| **Error** | Red | ✗ | Error messages |
| **Warning** | Gold | ⚠ | Validation warnings |
| **Info** | Blue | ℹ | Informational messages |

#### Modal Features

**Success Modals:**
- Green header and button
- Positive confirmation messages
- Example: "Template saved successfully!"

**Error Modals:**
- Red header and button
- Clear error descriptions
- Technical details when helpful
- Example: "Failed to save question. Please try again."

**Warning Modals:**
- Gold header (darker in dark mode)
- Form validation messages
- Actionable suggestions
- Example: "Please enter a question"

**Validation Error Modal:**
- Detailed breakdown table
- Color-coded status indicators
- Available vs. requested comparison
- List of suggestions
- "Adjust Settings" button to return to form

### Dark Mode Support

**Color System:**
- Uses CSS variables for automatic theme adaptation
- Warning color optimized for dark mode (#d68910)
- High contrast maintained across themes
- Professional appearance in both modes

**Light Mode:**
- Warning: Bright orange (#F39C12)
- Clear, vibrant colors

**Dark Mode:**
- Warning: Darker gold (#d68910)
- Reduced eye strain
- Better readability

### Form Behavior

**Auto-Clear After Success:**
- Title field cleared
- Question count reset to 5
- Difficulty percentages reset to 30/50/20
- Tags deselected
- Question bank selection cleared
- Randomize checkbox re-enabled

**Benefit:** Ready for immediate next interview creation

**Validation Warnings:**
- Form stays populated on validation errors
- Users can adjust and retry
- "Adjust Settings" button reopens form

---

## API Endpoints

### Question Bank Endpoints

#### List Question Banks
```http
GET /api/question-banks/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Python Backend Questions",
    "description": "Django and Python questions",
    "question_count": 15,
    "owner": 1,
    "created_at": "2024-11-10T10:00:00Z"
  }
]
```

#### Create Question Bank
```http
POST /api/question-banks/
Content-Type: application/json

{
  "name": "Python Backend Questions",
  "description": "Django and Python questions"
}
```

#### Get Question Bank Details
```http
GET /api/question-banks/{id}/
```

#### Delete Question Bank
```http
DELETE /api/question-banks/{id}/
```

### Question Endpoints

#### Add Question
```http
POST /api/questions/
Content-Type: application/json

{
  "question_bank": 1,
  "text": "What is a Python decorator?",
  "difficulty": "medium",
  "tag_ids": [1, 2, 3]
}
```

#### Update Question
```http
PUT /api/questions/{id}/
Content-Type: application/json

{
  "text": "Updated question text",
  "difficulty": "hard",
  "tag_ids": [1, 2]
}
```

#### Delete Question
```http
DELETE /api/questions/{id}/
```

### Auto-Assembly Endpoints

#### Auto-Assemble Interview
```http
POST /api/auto-assemble-interview/
Content-Type: application/json

{
  "title": "Python Developer Interview",
  "tag_ids": [1, 2, 3],
  "question_count": 10,
  "difficulty_distribution": {
    "easy": 30,
    "medium": 50,
    "hard": 20
  },
  "question_bank_id": 1,
  "randomize": true
}
```

**Success Response (200):**
```json
{
  "title": "Python Developer Interview",
  "questions": [...],
  "total_questions": 10,
  "difficulty_breakdown": {
    "easy": 3,
    "medium": 5,
    "hard": 2
  },
  "tag_breakdown": {...}
}
```

**Validation Error Response (400):**
```json
{
  "error": "Not enough questions available. Requested: 20, Available: 10",
  "available_count": 10,
  "requested_count": 20,
  "breakdown": {
    "easy": {
      "requested": 6,
      "available": 3
    },
    "medium": {
      "requested": 10,
      "available": 5
    },
    "hard": {
      "requested": 4,
      "available": 2
    }
  },
  "message": "Please reduce the number of questions or adjust the difficulty distribution."
}
```

#### Save as Template
```http
POST /api/save-as-template/
Content-Type: application/json

{
  "name": "Python Developer Template",
  "description": "Standard Python interview",
  "tag_ids": [1, 2, 3],
  "question_count": 10,
  "easy_percentage": 30,
  "medium_percentage": 50,
  "hard_percentage": 20,
  "question_bank_id": 1,
  "questions": [...]
}
```

**Response (201):**
```json
{
  "message": "Template saved successfully",
  "template": {
    "id": 5,
    "name": "Python Developer Template",
    "sections": [
      {
        "id": "uuid-1",
        "title": "Question 1: What is a Python decorator?",
        "content": "...",
        "order": 0,
        "weight": 34
      },
      ...
    ]
  }
}
```

### Tag Endpoints

#### List Tags
```http
GET /api/tags/
```

#### Create Tag
```http
POST /api/tags/
Content-Type: application/json

{
  "name": "#python"
}
```

#### Tag Statistics
```http
GET /api/tag-statistics/
```

**Response:**
```json
{
  "total_tags": 25,
  "tags": [
    {
      "name": "#python",
      "question_count": 42
    },
    ...
  ]
}
```

---

## Permissions

### Role-Based Access

| Action | Candidate | Interviewer | Admin |
|--------|-----------|-------------|-------|
| View Question Banks | ❌ | ✅ | ✅ |
| Create Question Banks | ❌ | ✅ | ✅ |
| Add Questions | ❌ | ✅ | ✅ |
| Edit Questions | ❌ | ✅ (own) | ✅ (all) |
| Delete Questions | ❌ | ✅ (own) | ✅ (all) |
| Auto-Assemble | ❌ | ✅ | ✅ |
| Save Templates | ❌ | ✅ | ✅ |
| View All Banks | ❌ | ❌ | ✅ |

**Permission Class:** `IsAdminOrInterviewer`

**Behavior:**
- Candidates cannot access question bank features
- Interviewers can only manage their own content
- Admins have full access to all content

---

## Best Practices

### Question Writing

**DO:**
- ✅ Write clear, specific questions
- ✅ Test practical knowledge
- ✅ Include context when needed
- ✅ Use proper grammar and formatting
- ✅ Tag accurately and consistently
- ✅ Review questions periodically

**DON'T:**
- ❌ Write ambiguous questions
- ❌ Test trivial memorization
- ❌ Use technical jargon without context
- ❌ Create duplicate questions
- ❌ Over-tag or under-tag
- ❌ Leave questions untagged

### Tag Management

**Naming Conventions:**
- Use lowercase consistently
- Specific over generic (`#django-orm` > `#django`)
- Language/framework tags (`#python`, `#react`)
- Topic tags (`#algorithms`, `#security`)
- Concept tags (`#async`, `#testing`)

**Organization:**
- 2-4 tags per question optimal
- Balance specificity and discoverability
- Review tag usage regularly
- Merge similar tags
- Delete unused tags

### Interview Assembly

**Strategy:**
1. **Start Broad:** Select multiple tags
2. **Adjust Distribution:** Match role requirements
3. **Review Preview:** Check question variety
4. **Save Reusable Templates:** For common interview types
5. **Iterate:** Refine based on interview outcomes

**Quality Control:**
- Test distributions before interviews
- Ensure variety in question types
- Balance theoretical and practical questions
- Review difficulty levels regularly
- Update banks with better questions

### Template Management

**Naming:**
- Descriptive names (role, level, focus)
- Version indicators if needed
- Example: "Senior Python Backend - v2"

**Maintenance:**
- Review templates quarterly
- Update with new questions
- Remove outdated content
- Document changes
- Track template effectiveness

---

## Troubleshooting

### Common Issues

#### "Not enough questions available"

**Cause:** Insufficient questions matching tags and difficulty

**Solutions:**
1. Reduce total question count
2. Adjust difficulty percentages
3. Select more tags
4. Add more questions to banks
5. Remove restrictive filters

#### "Please select at least one tag"

**Cause:** No tags selected for assembly

**Solution:** Click on at least one tag before assembling

#### "Difficulty percentages must total 100%"

**Cause:** Easy + Medium + Hard ≠ 100

**Solution:** Adjust percentages to total exactly 100%

#### Questions not appearing

**Possible Causes:**
- Questions not tagged
- Wrong tags selected
- Questions in different bank
- Insufficient permissions

**Solutions:**
- Verify questions have tags
- Check tag selection
- Select correct bank or "All Banks"
- Verify role permissions

#### Template not saving

**Possible Causes:**
- No questions assembled
- Server error
- Permission issue

**Solutions:**
- Assemble interview first
- Check console for errors
- Verify interviewer/admin role
- Try again

---

## Technical Details

### Database Schema

**QuestionBank Model:**
```python
- id: AutoField
- name: CharField(max_length=200)
- description: TextField(optional)
- owner: ForeignKey(User)
- created_at: DateTimeField(auto_now_add=True)
```

**Question Model:**
```python
- id: AutoField
- question_bank: ForeignKey(QuestionBank)
- text: TextField
- difficulty: CharField(choices=['easy', 'medium', 'hard'])
- owner: ForeignKey(User)
- tags: ManyToManyField(Tag)
- created_at: DateTimeField(auto_now_add=True)
```

**Tag Model:**
```python
- id: AutoField
- name: CharField(max_length=50, unique=True)
- created_at: DateTimeField(auto_now_add=True)
```

**InterviewTemplate Model:**
```python
- id: AutoField
- name: CharField(max_length=200)
- description: TextField(optional)
- user: ForeignKey(User)
- sections: JSONField (list of section objects)
- tags: ManyToManyField(Tag)
- question_banks: ManyToManyField(QuestionBank)
- use_auto_assembly: BooleanField
- question_count: IntegerField
- easy_percentage: IntegerField
- medium_percentage: IntegerField
- hard_percentage: IntegerField
- created_at: DateTimeField(auto_now_add=True)
```

### Implementation Files

**Backend:**
- `question_bank_views.py` - API views and business logic
- `models.py` - Database models
- `serializers.py` - API serializers
- `urls.py` - URL routing
- `admin.py` - Admin interface
- `forms.py` - Form definitions

**Frontend:**
- `question_banks.html` - Main template
- `main.css` - Styling with CSS variables
- `theme.js` - Dark mode support

**Tests:**
- `test_question_banks.py` - Comprehensive test suite

### Performance Considerations

**Query Optimization:**
- Uses `select_related()` for foreign keys
- Uses `prefetch_related()` for many-to-many
- Filters in database, not Python
- Pagination for large lists

**Caching:**
- Tag statistics cached
- Question counts cached
- Frequently accessed data optimized

**Validation:**
- Early validation prevents wasted processing
- Count queries before retrieval
- Efficient difficulty filtering

---

## Future Enhancements

### Planned Features

1. **Question Versioning**
   - Track question history
   - Revert to previous versions
   - Compare changes over time

2. **Question Analytics**
   - Track usage frequency
   - Success/failure rates
   - Average time to answer
   - Difficulty calibration

3. **Collaborative Banks**
   - Share banks between interviewers
   - Team-level question pools
   - Approval workflows

4. **Import/Export**
   - Import questions from CSV/JSON
   - Export banks for backup
   - Share question sets

5. **Advanced Filtering**
   - Filter by creation date
   - Filter by usage count
   - Filter by author
   - Saved filter presets

6. **Question Templates**
   - Reusable question formats
   - Code snippet support
   - Image/diagram support
   - Multiple choice options

---

## Support

### Getting Help

**Documentation:** See `/docs/features/` for detailed guides

**Issue Reporting:** Submit issues via GitHub Issues

**Feature Requests:** Discuss in team meetings or submit PR

### Related Documentation

- [Interview Template Functionality](./interview-templates.md)
- [RBAC System](./rbac.md)
- [Style Guide](../STYLE_GUIDE.md)
- [API Documentation](../architecture/api.md)

---

## Changelog

### Version 1.0 (November 2024)

**Added:**
- Question bank creation and management
- Question tagging system
- Auto-assembly with difficulty distribution
- Two-level validation system
- Individual section architecture
- Modal-based UI (replaced all alerts)
- Dark mode optimized colors
- Auto-clearing forms after success
- Comprehensive error messages
- Tag management system

**Technical:**
- Backend validation in `AutoAssembleInterviewView`
- Frontend validation modal with detailed breakdown
- Section-based template structure
- CSS variable system for theming
- JavaScript modal functions
- Test coverage for validation

---

Last Updated: November 2024
