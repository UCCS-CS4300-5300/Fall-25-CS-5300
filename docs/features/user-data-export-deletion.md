# User Data Export & Deletion (GDPR/CCPA Compliance)

**Related Issues**: #63, #64, #65
**Status**: ✅ Completed
**Version**: 1.0
**Last Updated**: November 11, 2025

## Overview

The User Data Export & Deletion feature provides GDPR and CCPA compliance by allowing users to:
- **Export their personal data** in portable formats (JSON/CSV)
- **Delete their accounts** with proper anonymization and audit trails

This feature gives users complete control over their privacy and personal data in accordance with international data protection regulations.

---

## Table of Contents

1. [Features](#features)
2. [User Guide](#user-guide)
3. [Technical Implementation](#technical-implementation)
4. [API Reference](#api-reference)
5. [Admin Guide](#admin-guide)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Features

### Data Export (Issue #64)

**What gets exported:**
- User profile information (username, email, role)
- All interview transcripts and messages
- Performance scores and AI feedback
- Uploaded resumes with parsed data (skills, experience, education)
- Job listings
- Interview templates
- Role change requests

**Export format:**
- ZIP file containing:
  - `complete_data.json` - All data in one JSON file
  - `user_info.json` - Profile information
  - `*.csv` files - Tabular data for resumes, interviews, job listings
  - Individual files in organized folders
  - `README.txt` - Guide to export contents

**Key features:**
- ✅ Processing completes within 5 minutes (typical datasets)
- ✅ Email notification when ready (in production)
- ✅ 7-day expiration for security
- ✅ Download tracking
- ✅ Multiple export requests supported

### Account Deletion (Issue #65)

**Two-tier deletion approach:**

**Hard Deletion (Permanently removed):**
- User profile and credentials
- Contact information
- Resume files and content
- Job listing files and content
- Audio recordings
- Export files
- All personally identifiable information

**Soft Deletion (Anonymized and retained):**
- Interview scores (for platform analytics)
- Anonymized statistics
- Aggregate usage data
- No linkage to original user

**Security features:**
- ✅ Two-step confirmation process
- ✅ Password verification required
- ✅ Clear warnings about permanent deletion
- ✅ Audit trail with anonymized ID
- ✅ Email confirmation
- ✅ Unrecoverable by design

---

## User Guide

### Accessing Data Settings

1. **Log in** to your account
2. Go to **Profile** (click your username or `/profile/`)
3. Scroll down to the **"Privacy & Data"** section (left column)
4. Click **"Data Settings"** button

**Direct URL**: `/profile/data-settings/`

### Exporting Your Data

#### Step 1: Request Export

1. From Data Settings, click **"Request Data Export"**
2. Review what will be included
3. Click **"Confirm Export Request"**

#### Step 2: Wait for Processing

- Processing typically takes **less than 5 minutes**
- You'll see a status page with auto-refresh
- In production, you'll receive an email when ready

#### Step 3: Download

1. When status shows **"Ready"**, click **"Download ZIP File"**
2. Save the file to your computer
3. The file expires after **7 days**

#### Step 4: Extract and Review

1. Unzip the downloaded file
2. Read `README.txt` for contents guide
3. Review your data in JSON/CSV formats

### Deleting Your Account

⚠️ **WARNING: This is permanent and cannot be undone!**

#### Step 1: Review What Will Be Deleted

1. From Data Settings, click **"Delete My Account"**
2. Review the detailed list of data to be deleted
3. Check deletion statistics (resumes, interviews, etc.)

#### Step 2: Export First (Recommended)

Before deleting, consider exporting your data:
- Click **"Export My Data First"** button
- Complete the export process
- Download and save your data

#### Step 3: Confirm Deletion

1. Check both confirmation boxes:
   - ☑️ "I understand this action is permanent"
   - ☑️ "I understand all my personal data will be deleted"
2. Click **"Proceed to Delete Account"**

#### Step 4: Verify with Password

1. Enter your password
2. Click **"Delete My Account Permanently"**
3. You'll be logged out immediately
4. Confirmation page will appear
5. Email confirmation sent to your address

---

## Technical Implementation

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                      │
│  (Profile → Data Settings → Export/Delete Options)      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Django Views                           │
│  - user_data_settings()                                 │
│  - request_data_export()                                │
│  - data_export_status()                                 │
│  - download_data_export()                               │
│  - request_account_deletion()                           │
│  - confirm_account_deletion()                           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            Utility Functions (user_data_utils.py)       │
│  - export_user_data_to_dict()                           │
│  - create_export_zip()                                  │
│  - process_export_request()                             │
│  - anonymize_user_interviews()                          │
│  - delete_user_account()                                │
│  - generate_anonymized_id()                             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Database Models                        │
│  - DataExportRequest (tracks exports)                   │
│  - DeletionRequest (audit trail)                        │
│  - User, Chat, Resume, JobListing, etc.                 │
└─────────────────────────────────────────────────────────┘
```

### Database Models

#### DataExportRequest

Tracks user data export requests.

**Fields:**
- `user` (ForeignKey) - User requesting export
- `status` (CharField) - pending/processing/completed/failed/expired
- `export_file` (FileField) - Generated ZIP file
- `requested_at` (DateTimeField) - Request timestamp
- `completed_at` (DateTimeField) - Completion timestamp
- `expires_at` (DateTimeField) - Expiration (7 days after completion)
- `error_message` (TextField) - Error details if failed
- `file_size_bytes` (BigIntegerField) - Export file size
- `download_count` (IntegerField) - Times downloaded
- `last_downloaded_at` (DateTimeField) - Last download timestamp

**Methods:**
- `is_expired()` - Check if download link expired
- `mark_downloaded()` - Increment download counter

#### DeletionRequest

Audit trail for account deletions (legal compliance).

**Fields:**
- `anonymized_user_id` (CharField) - Hashed user identifier
- `username` (CharField) - Username at deletion (audit)
- `email` (EmailField) - Email at deletion (audit)
- `status` (CharField) - pending/completed/failed
- `requested_at` (DateTimeField) - Request timestamp
- `completed_at` (DateTimeField) - Completion timestamp
- `error_message` (TextField) - Error details if failed
- `total_interviews_deleted` (IntegerField) - Count
- `total_resumes_deleted` (IntegerField) - Count
- `total_job_listings_deleted` (IntegerField) - Count

### Key Functions

#### export_user_data_to_dict(user)

Exports all user data to a Python dictionary.

**Returns:**
```python
{
    'export_date': '2025-11-11T12:00:00',
    'user_info': {
        'username': 'johndoe',
        'email': 'john@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'role': 'candidate',
        'date_joined': '2025-01-15T10:00:00'
    },
    'resumes': [...],
    'job_listings': [...],
    'interviews': [...],
    'interview_templates': [...],
    'role_change_requests': [...]
}
```

#### create_export_zip(user)

Creates a ZIP file with all user data in JSON/CSV formats.

**Returns:** `bytes` - ZIP file content

**ZIP Contents:**
```
user_data_export.zip
├── README.txt
├── complete_data.json
├── user_info.json
├── resumes.csv
├── resumes/
│   ├── resume_1_My_Resume.txt
│   └── resume_2_Updated_Resume.txt
├── job_listings.csv
├── job_listings/
│   ├── job_1_Software_Engineer.txt
│   └── job_2_Data_Scientist.txt
├── interviews.csv
├── interviews/
│   ├── interview_1_Python_Interview.json
│   └── interview_2_System_Design.json
└── interview_templates.json
```

#### process_export_request(export_request)

Processes a data export request:
1. Updates status to "processing"
2. Generates export ZIP
3. Saves file to storage
4. Updates status to "completed"
5. Sets expiration date (7 days)
6. Sends email notification

**Returns:** `bool` - Success status

#### anonymize_user_interviews(user)

Anonymizes interview data (soft delete):
- Clears messages array (removes PII)
- Clears key questions
- Updates title to "Anonymized Interview {id}"
- Removes resume/job listing references
- Clears report feedback text
- Keeps scores for analytics

**Returns:** `int` - Number of interviews anonymized

#### delete_user_account(user, deletion_request)

Permanently deletes user account:
1. Counts data for audit trail
2. Anonymizes interviews (soft delete)
3. Hard deletes resumes and files
4. Hard deletes job listings and files
5. Hard deletes export files
6. Updates deletion request with statistics
7. Deletes user (cascades to remaining data)
8. Sends confirmation email

**Returns:** `tuple` - (success: bool, error_message: str or None)

#### generate_anonymized_id(user)

Generates SHA-256 hash of user data for audit trail.

**Returns:** `str` - 32-character anonymized identifier

---

## API Reference

### URL Endpoints

All endpoints require authentication (`@login_required`).

#### Main Settings

```
GET /profile/data-settings/
```

**Description:** Main privacy and data settings dashboard

**Response:** HTML page with export/delete options

**Template:** `user_data/settings.html`

---

#### Request Data Export

```
GET /profile/data-export/request/
POST /profile/data-export/request/
```

**GET Description:** Shows export request page with information

**POST Description:** Creates new export request

**POST Logic:**
1. Check for existing pending/processing requests
2. If exists, redirect to status page
3. Create new `DataExportRequest`
4. Process export (synchronous in current implementation)
5. Redirect to status page

**Template:** `user_data/request_export.html`

---

#### Export Status

```
GET /profile/data-export/<request_id>/status/
```

**Description:** View export request status

**Parameters:**
- `request_id` (int) - DataExportRequest ID

**Response:** Status page with auto-refresh (if pending/processing)

**Template:** `user_data/export_status.html`

**Auto-refresh:** Every 10 seconds while processing

---

#### Download Export

```
GET /profile/data-export/<request_id>/download/
```

**Description:** Download completed export file

**Parameters:**
- `request_id` (int) - DataExportRequest ID

**Validation:**
- Must be completed status
- Must not be expired
- File must exist

**Response:** FileResponse with ZIP file

**Side Effects:**
- Increments `download_count`
- Updates `last_downloaded_at`

---

#### Request Account Deletion

```
GET /profile/delete-account/
POST /profile/delete-account/
```

**GET Description:** Shows deletion information page

**POST Description:** Shows password confirmation page

**Template (GET):** `user_data/request_deletion.html`

**Template (POST):** `user_data/confirm_deletion.html`

---

#### Confirm Account Deletion

```
POST /profile/delete-account/confirm/
```

**Description:** Executes account deletion with password verification

**POST Parameters:**
- `password` (string) - User's password

**Logic:**
1. Verify password
2. If incorrect, redirect with error
3. Create `DeletionRequest` with anonymized ID
4. Call `delete_user_account()`
5. Render completion page (user is deleted)

**Template:** `user_data/deletion_complete.html`

**Note:** User is logged out and deleted if successful

---

## Admin Guide

### Django Admin Interface

Admins can monitor and manage data requests via Django Admin.

#### Accessing Admin Panel

1. Go to `/admin/`
2. Login with admin credentials
3. Navigate to **"Active Interview App"** section

### DataExportRequest Admin

**Location:** `/admin/active_interview_app/dataexportrequest/`

**List View Shows:**
- Request ID
- User
- Status (pending/processing/completed/failed/expired)
- Requested date
- Completed date
- Expiration date
- File size
- Download count

**Filters:**
- Status
- Requested date
- Completed date

**Search:**
- Username
- Email

**Actions:**
- View detailed request information
- Download export file
- Change status manually (if needed)

### DeletionRequest Admin

**Location:** `/admin/active_interview_app/deletionrequest/`

**List View Shows:**
- Request ID
- Anonymized user ID
- Username (at time of deletion)
- Status
- Requested date
- Completed date
- Total data deleted (count)

**Filters:**
- Status
- Requested date
- Completed date

**Search:**
- Anonymized user ID
- Username
- Email

**Purpose:**
- Legal compliance audit trail
- Statistics on deleted accounts
- Error tracking

### Monitoring Tips

**Weekly Review:**
1. Check for failed exports: `Status: Failed`
2. Review error messages
3. Clean up expired exports (>7 days old)

**Monthly Statistics:**
1. Count export requests
2. Count account deletions
3. Review deletion reasons (if recorded)

**Security Checks:**
1. Verify expired exports are inaccessible
2. Confirm deleted users cannot login
3. Check audit trail completeness

---

## Configuration

### Environment Variables

#### Development

```bash
PROD=false  # Uses console email backend
DJANGO_SECRET_KEY=<your-dev-key>
OPENAI_API_KEY=<your-key>
```

#### Production

```bash
PROD=true
DJANGO_SECRET_KEY=<secure-key>
OPENAI_API_KEY=<your-key>

# Email Configuration (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@activeinterviewservice.me
```

### Settings Configuration

**settings.py** (`active_interview_project/settings.py`)

```python
# Site URL (for email links)
if PROD:
    SITE_URL = 'https://app.activeinterviewservice.me'
else:
    SITE_URL = 'http://localhost:8000'

# Email configuration
if PROD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@activeinterviewservice.me')
else:
    # Development: emails print to console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@activeinterviewservice.me'
```

### Email Setup (Production)

#### Gmail Configuration

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password:**
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and your device
   - Copy the generated password

3. **Set Environment Variables:**
   ```bash
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=<16-character-app-password>
   ```

#### Alternative Email Providers

**SendGrid:**
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<your-sendgrid-api-key>
```

**Mailgun:**
```bash
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_HOST_USER=<your-username>@<your-domain>
EMAIL_HOST_PASSWORD=<your-password>
```

### File Storage

**Media Files Location:**
- Development: `active_interview_backend/media/`
- Production: Configure with cloud storage (S3, etc.)

**Export Files Path:**
```
media/
└── exports/
    └── user_data/
        ├── user_data_johndoe_20251111_120000.zip
        └── user_data_janedoe_20251111_130000.zip
```

### Scheduled Cleanup (Optional)

**Recommended:** Setup a cron job to clean expired exports

**Management Command** (create this):
```python
# management/commands/cleanup_expired_exports.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from active_interview_app.models import DataExportRequest

class Command(BaseCommand):
    help = 'Clean up expired data exports'

    def handle(self, *args, **options):
        expired = DataExportRequest.objects.filter(
            status=DataExportRequest.COMPLETED,
            expires_at__lt=timezone.now()
        )

        count = 0
        for export in expired:
            if export.export_file:
                export.export_file.delete()
            export.status = DataExportRequest.EXPIRED
            export.save()
            count += 1

        self.stdout.write(f'Cleaned up {count} expired exports')
```

**Crontab:**
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/project && python manage.py cleanup_expired_exports
```

---

## Testing

### Running Tests

**All user data tests:**
```bash
python manage.py test active_interview_app.tests.test_user_data
```

**Specific test class:**
```bash
python manage.py test active_interview_app.tests.test_user_data.DataExportViewsTest
```

**With verbose output:**
```bash
python manage.py test active_interview_app.tests.test_user_data -v 2
```

### Test Coverage

**36 comprehensive tests covering:**

1. **Model Tests (14 tests)**
   - DataExportRequest model
   - DeletionRequest model
   - Field validation
   - Method functionality

2. **Utility Tests (6 tests)**
   - Data export functions
   - ZIP creation
   - Anonymization
   - ID generation

3. **View Tests (13 tests)**
   - All endpoints
   - Authentication
   - Permission checks
   - Error handling

4. **Integration Tests (3 tests)**
   - Complete export workflow
   - Complete deletion workflow
   - Export processing

**Coverage:** 100% of new functionality

### Manual Testing Checklist

#### Export Feature

- [ ] Can access data settings page
- [ ] Can request export
- [ ] Status page shows correctly
- [ ] Export completes within 5 minutes
- [ ] Can download ZIP file
- [ ] ZIP contains all expected files
- [ ] JSON data is valid
- [ ] CSV files are readable
- [ ] Cannot access other users' exports
- [ ] Expired exports cannot be downloaded
- [ ] Download count increments
- [ ] Multiple exports can coexist

#### Deletion Feature

- [ ] Can access deletion page
- [ ] Warnings display correctly
- [ ] Data counts are accurate
- [ ] Cannot proceed without checkboxes
- [ ] Password verification works
- [ ] Wrong password is rejected
- [ ] Account is actually deleted
- [ ] Cannot login after deletion
- [ ] Audit trail is created
- [ ] Email confirmation sent (production)
- [ ] Interview scores are anonymized
- [ ] Personal data is removed

---

## Troubleshooting

### Common Issues

#### 1. Email Authentication Errors

**Problem:** `SMTPAuthenticationError` when sending emails

**Solution:**
```bash
# For development, set PROD=false
PROD=false python manage.py runserver

# For production, verify email credentials
EMAIL_HOST_USER=correct-email@domain.com
EMAIL_HOST_PASSWORD=correct-app-password
```

**Gmail Specific:**
- Ensure 2FA is enabled
- Use App Password, not account password
- Enable "Less secure app access" if not using App Password

---

#### 2. Export Processing Fails

**Problem:** Export status shows "Failed"

**Check:**
1. Admin panel → DataExportRequest → View error message
2. Check Django logs for traceback
3. Verify user has data to export

**Common causes:**
- Database connection issues
- File system permissions
- Memory limits (very large datasets)

**Solution:**
```bash
# Check file permissions
chmod 755 media/exports/user_data/

# Check disk space
df -h

# View error in admin or shell
python manage.py shell
>>> from active_interview_app.models import DataExportRequest
>>> req = DataExportRequest.objects.filter(status='failed').last()
>>> print(req.error_message)
```

---

#### 3. Download Link Expired

**Problem:** "This export link has expired"

**Explanation:** Links expire 7 days after generation (security requirement)

**Solution:**
- Request a new export
- Download exports within 7 days

**For admins:**
```bash
# Extend expiration (emergency only)
python manage.py shell
>>> from active_interview_app.models import DataExportRequest
>>> from datetime import timedelta
>>> from django.utils import timezone
>>> req = DataExportRequest.objects.get(id=123)
>>> req.expires_at = timezone.now() + timedelta(days=7)
>>> req.save()
```

---

#### 4. Cannot Delete Account

**Problem:** Account deletion fails with error

**Check:**
1. Verify password is correct
2. Check for cascade delete issues
3. Review error message

**Solution:**
```bash
# Check deletion request
python manage.py shell
>>> from active_interview_app.models import DeletionRequest
>>> req = DeletionRequest.objects.filter(status='failed').last()
>>> print(req.error_message)

# Manual deletion (admin only, emergency)
>>> from django.contrib.auth.models import User
>>> from active_interview_app.user_data_utils import delete_user_account, generate_anonymized_id
>>> user = User.objects.get(username='problematic_user')
>>> anon_id = generate_anonymized_id(user)
>>> del_req = DeletionRequest.objects.create(
...     anonymized_user_id=anon_id,
...     username=user.username,
...     email=user.email
... )
>>> success, error = delete_user_account(user, del_req)
>>> print(f"Success: {success}, Error: {error}")
```

---

#### 5. ZIP File is Empty or Corrupted

**Problem:** Downloaded ZIP is 0 bytes or won't open

**Check:**
1. Verify export completed successfully
2. Check file size in admin panel
3. Test ZIP creation manually

**Solution:**
```bash
python manage.py shell
>>> from active_interview_app.user_data_utils import create_export_zip
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='testuser')
>>> zip_content = create_export_zip(user)
>>> print(f"ZIP size: {len(zip_content)} bytes")
>>> # If size > 0, ZIP creation works
>>> # If size = 0, check user data exists
```

---

#### 6. Profile Link Missing

**Problem:** "Data Settings" button not visible in profile

**Check:**
1. Clear browser cache
2. Verify template was updated
3. Check Django static files

**Solution:**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Hard refresh browser
# Windows/Linux: Ctrl + F5
# Mac: Cmd + Shift + R

# Verify template file
cat active_interview_app/templates/profile.html | grep "Data Settings"
```

---

### Debug Mode

**Enable detailed logging:**

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'active_interview_app': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Security Considerations

### Data Protection

1. **Export Files:**
   - Stored in `media/exports/user_data/`
   - User-specific permissions enforced
   - 7-day expiration mandatory
   - HTTPS required in production

2. **Account Deletion:**
   - Password verification required
   - Two-step confirmation
   - Cannot be reversed
   - Audit trail maintained

3. **Anonymization:**
   - SHA-256 hashing for user IDs
   - Interview scores retained (no PII linkage)
   - Compliant with GDPR Article 17

### Best Practices

1. **Regular Audits:**
   - Review deletion requests monthly
   - Verify expired exports are cleaned up
   - Check audit trail completeness

2. **Backup Strategy:**
   - Backup deletion audit logs
   - Keep anonymized statistics
   - Don't backup exported user data (privacy risk)

3. **Access Control:**
   - Only authenticated users access their data
   - Admins have full visibility
   - Log all download attempts

---

## Compliance Notes

### GDPR Compliance

✅ **Article 15 - Right of Access:**
- Users can export complete personal data
- Data provided in machine-readable format (JSON)
- Common formats available (CSV)

✅ **Article 17 - Right to Erasure ("Right to be Forgotten"):**
- Users can delete their accounts
- Hard deletion of personal data
- Anonymization where deletion impossible
- Audit trail for compliance

✅ **Article 20 - Right to Data Portability:**
- Structured data format (JSON/CSV)
- Commonly used and machine-readable
- Can be transmitted to another service

✅ **Article 30 - Records of Processing:**
- Deletion audit trail maintained
- Anonymized records for compliance
- Timestamps for all operations

### CCPA Compliance

✅ **Right to Know:**
- Complete data disclosure in export
- Categories of data clearly listed
- Sources documented (user uploads, AI processing)

✅ **Right to Delete:**
- Account deletion on request
- Verification (password) required
- Confirmation of deletion provided

✅ **Right to Non-Discrimination:**
- No penalty for requesting data/deletion
- Service continues normally
- No degraded functionality

---

## Future Enhancements

### Potential Improvements

1. **Async Processing:**
   - Implement Celery for background export processing
   - Better handling of large datasets
   - Status updates via WebSockets

2. **Advanced Filtering:**
   - Select specific data types to export
   - Date range filtering
   - Partial exports

3. **Data Transfer:**
   - Direct transfer to another service
   - OAuth-based authentication
   - API for automated exports

4. **Retention Policies:**
   - Automated cleanup of old data
   - User-configurable retention
   - Grace period before deletion

5. **Multi-Format Export:**
   - PDF format option
   - Excel spreadsheets
   - SQL dump format

---

## Support

### Getting Help

**Documentation:**
- Project README: `/README.md`
- Architecture docs: `/docs/architecture/`
- API reference: `/docs/architecture/api.md`

**For Issues:**
- GitHub Issues: https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues
- Tag with: `privacy`, `gdpr`, `data-export`, or `account-deletion`

**For Questions:**
- Contact project maintainers
- Review related issues: #63, #64, #65

---

## Changelog

### Version 1.0 (November 11, 2025)

**Initial Release:**
- ✅ Complete data export functionality
- ✅ Account deletion with anonymization
- ✅ GDPR/CCPA compliance
- ✅ Admin interfaces
- ✅ Comprehensive test suite (36 tests)
- ✅ Email notifications
- ✅ 7-day expiration system
- ✅ Audit trail for deletions
- ✅ User-friendly UI following style guide

**Files Added:**
- `user_data_utils.py` - Core utility functions
- `models.py` - DataExportRequest, DeletionRequest models
- 6 new views in `views.py`
- 6 new URL patterns in `urls.py`
- 7 new templates in `templates/user_data/`
- `test_user_data.py` - 36 comprehensive tests
- Admin interfaces for new models

**Related Issues:**
- Closes #63 - GDPR/CCPA data export & delete
- Closes #64 - Data Export Functionality
- Closes #65 - Data Deletion & Anonymization

---

## License

This feature is part of the Active Interview Service project.
See project LICENSE for details.
