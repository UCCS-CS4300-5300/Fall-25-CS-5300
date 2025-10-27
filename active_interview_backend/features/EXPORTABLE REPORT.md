# Exportable Report Feature

## Overview
The Exportable Report feature enables users to generate, view, and download professional interview reports in PDF format. This feature transforms interview chat data into structured, presentable reports that can be exported and shared.

## Feature Components

### 1. Data Model (`ExportableReport`)
**Location:** `active_interview_backend/active_interview_app/models.py:77-129`

A Django model that stores structured report data for interviews:

#### Fields:
- **`chat`** (OneToOneField): Links to the parent Chat instance
- **Metadata:**
  - `generated_at`: Timestamp of report creation
  - `last_updated`: Auto-updated timestamp

- **Performance Scores (0-100):**
  - `professionalism_score`: Evaluates professional conduct
  - `subject_knowledge_score`: Evaluates technical/domain knowledge
  - `clarity_score`: Evaluates communication clarity
  - `overall_score`: Aggregate performance score

- **Content:**
  - `feedback_text`: AI-generated textual feedback
  - `question_responses`: JSONField storing Q&A pairs with scores
    - Structure: `[{"question": str, "answer": str, "score": int, "feedback": str}, ...]`

- **Statistics:**
  - `total_questions_asked`: Count of interviewer questions
  - `total_responses_given`: Count of candidate responses
  - `interview_duration_minutes`: Optional duration tracking

- **Export Tracking:**
  - `pdf_generated`: Boolean flag for PDF generation status
  - `pdf_file`: FileField for storing generated PDFs

### 2. PDF Generation Engine (`pdf_export.py`)
**Location:** `active_interview_backend/active_interview_app/pdf_export.py`

A comprehensive PDF generation utility built with ReportLab that creates professional, multi-page reports.

#### Main Function:
```python
generate_pdf_report(exportable_report) -> BytesIO
```

#### Report Sections:
1. **Title Section**: Interview report title with chat name
2. **Interview Details**: Metadata table showing:
   - Interview type (General, Skills, Personality, Final Screening)
   - Difficulty level (1-10)
   - Completion date
   - Job position and resume (if applicable)

3. **Performance Assessment**: Visual score grid with:
   - Individual category scores
   - Text ratings (Excellent, Good, Fair, Needs Improvement)
   - Overall score highlighting

4. **AI Feedback**: Formatted feedback text with custom styling

5. **Question & Response Analysis**: Detailed Q&A breakdown with:
   - Question text
   - Candidate answers
   - Individual scores (0-10)
   - Per-question feedback

6. **Interview Statistics**: Summary metrics
7. **Footer**: Auto-generated timestamp

#### Helper Functions:
- `_create_styles()`: Custom PDF styling (colors, fonts, spacing)
- `_create_metadata_section()`: Interview details table
- `_create_performance_scores_section()`: Scores grid with ratings
- `_create_feedback_section()`: AI feedback formatting
- `_create_question_responses_section()`: Q&A breakdown
- `_create_statistics_section()`: Statistics summary
- `_create_footer()`: Generation timestamp footer
- `get_score_rating(score)`: Converts numeric scores to text ratings

### 3. Web Interface (`export-report.html`)
**Location:** `active_interview_backend/active_interview_app/templates/reports/export-report.html`

A responsive HTML template for viewing reports in the browser before downloading.

#### Features:
- **Modern Design**: Clean card-based layout with consistent styling
- **Score Visualization**: Grid display of performance scores
- **Interactive Elements**:
  - Download as PDF button
  - Back to results navigation
- **Content Sections**:
  - Interview metadata table
  - Performance score cards
  - AI feedback display
  - Statistics overview
  - Q&A preview (first 5 questions)
- **Responsive Layout**: Adapts to different screen sizes

### 4. Backend Views
**Location:** `active_interview_backend/active_interview_app/views.py:1118-1327`

#### `GenerateReportView` (POST)
- **URL:** `/chat/<chat_id>/generate-report/`
- **Purpose:** Creates or updates an ExportableReport from chat data
- **Process:**
  1. Validates user ownership of the chat
  2. Creates or retrieves existing report
  3. Extracts scores from chat messages using regex patterns
  4. Parses AI feedback from assistant messages
  5. Builds question-response array
  6. Calculates statistics (question count, response count)
  7. Saves report and redirects to export view

#### `ExportReportView` (GET)
- **URL:** `/chat/<chat_id>/export-report/`
- **Purpose:** Displays the report in browser
- **Features:**
  - Renders HTML template with report data
  - Shows formatted scores, feedback, and Q&A
  - Provides download and navigation buttons

#### `DownloadPDFReportView` (GET)
- **URL:** `/chat/<chat_id>/download-pdf/`
- **Purpose:** Generates and downloads PDF file
- **Process:**
  1. Validates user ownership
  2. Generates or retrieves existing report
  3. Calls `generate_pdf_report()` function
  4. Returns PDF as FileResponse with appropriate headers
  5. Filename format: `interview_report_{chat_title}_{timestamp}.pdf`

### 5. URL Configuration
**Location:** `active_interview_backend/active_interview_app/urls.py:81-88`

```python
path('chat/<int:chat_id>/generate-report/',
     views.GenerateReportView.as_view(), name='generate_report'),
path('chat/<int:chat_id>/export-report/',
     views.ExportReportView.as_view(), name='export_report'),
path('chat/<int:chat_id>/download-pdf/',
     views.DownloadPDFReportView.as_view(), name='download_pdf_report'),
```

### 6. API Serializer
**Location:** `active_interview_backend/active_interview_app/serializers.py`

`ExportableReportSerializer`: Converts ExportableReport model instances to JSON for API responses.

### 7. Database Migration
**Location:** `active_interview_backend/active_interview_app/migrations/0003_alter_chat_type_exportablereport.py`

- Creates ExportableReport table with all fields
- Sets up OneToOne relationship with Chat
- Adds validators for score ranges (0-100)

## Testing
**Location:** `active_interview_backend/active_interview_app/tests/test_exportable_report.py`

Comprehensive test suite with 369 lines covering:
- Model creation and validation
- Score range validation
- Report generation from chats
- PDF generation functionality
- View access permissions
- API endpoints
- Edge cases and error handling

## Usage Workflow

### For Users:
1. **Complete Interview**: Finish an interview chat session
2. **Generate Report**: Click "Generate Report" button on results page
3. **View Report**: Review the formatted report in browser
4. **Download PDF**: Click "Download as PDF" to save a professional copy

### For Developers:
```python
from active_interview_app.models import Chat, ExportableReport
from active_interview_app.pdf_export import generate_pdf_report

# Get or create a report
chat = Chat.objects.get(id=1)
report, created = ExportableReport.objects.get_or_create(chat=chat)

# Set report data
report.professionalism_score = 85
report.subject_knowledge_score = 90
report.clarity_score = 78
report.overall_score = 84
report.feedback_text = "Great performance overall..."
report.save()

# Generate PDF
pdf_bytes = generate_pdf_report(report)

# Save to file
with open('report.pdf', 'wb') as f:
    f.write(pdf_bytes)
```

## Technical Highlights

### PDF Styling
- Custom color scheme (primary: #1a73e8)
- Professional typography with Helvetica fonts
- Multi-page support with proper page breaks
- Tables with alternating row colors
- Responsive column widths

### Data Extraction
- Regex-based score parsing from AI messages
- Keyword-based feedback detection
- Intelligent message filtering (user vs. assistant)
- Fallback handling for missing data

### Security
- `LoginRequiredMixin`: Requires authentication
- `UserPassesTestMixin`: Validates chat ownership
- CSRF protection on POST requests
- Secure file handling for PDF storage

## Dependencies
- **ReportLab**: PDF generation library
- **Django**: Web framework (models, views, templates)
- **Pillow**: Image processing (included in requirements)

## Configuration
Added to `settings.py`:
```python
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
```

## Future Enhancements (Potential)
- Multiple export formats (CSV, Excel, JSON)
- Email report delivery
- Report templates customization
- Batch report generation
- Report sharing with stakeholders
- Graphical visualizations (charts, graphs)
- Historical report comparison

## Files Modified/Created

### New Files:
- `active_interview_app/pdf_export.py` (412 lines)
- `active_interview_app/templates/reports/export-report.html` (305 lines)
- `active_interview_app/tests/test_exportable_report.py` (369 lines)
- `active_interview_app/migrations/0003_alter_chat_type_exportablereport.py`

### Modified Files:
- `active_interview_app/models.py`: Added ExportableReport model
- `active_interview_app/views.py`: Added 3 report views (+213 lines)
- `active_interview_app/urls.py`: Added 3 URL patterns
- `active_interview_app/serializers.py`: Added ExportableReportSerializer
- `active_interview_app/admin.py`: Registered ExportableReport
- `requirements.txt`: Added reportlab dependency

## Commits
- `d49e309`: feat: Add Exportable Report functionality with PDF generation
- `78c219d`: Refactor generate_pdf_report method for better maintainability

## Summary
This feature provides a complete end-to-end solution for converting interview chat data into professional, shareable PDF reports. It includes data modeling, PDF generation, web interface, and comprehensive testing, making interview results easily exportable and presentable to stakeholders.
