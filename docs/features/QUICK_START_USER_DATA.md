# Quick Start: User Data Export & Deletion

**5-Minute Guide** | Issues #63, #64, #65

---

## For Users

### Export Your Data (3 steps)

1. **Profile → Data Settings** button (bottom left)
2. **Request Data Export** → Confirm
3. **Download ZIP** when ready (~5 minutes)

**What you get:** ZIP file with JSON/CSV of all your data

**Link expires:** 7 days after completion

---

### Delete Your Account (4 steps)

⚠️ **PERMANENT - Cannot be undone!**

1. **Profile → Data Settings** → Delete My Account
2. **Export first** (recommended)
3. **Check both boxes** → Enter password
4. **Confirm deletion** → Account deleted immediately

---

## For Developers

### Files Modified/Created

**Core Logic:**
```
active_interview_app/
├── models.py                 (+183 lines) - 2 new models
├── views.py                  (+231 lines) - 6 new views
├── urls.py                   (+13 lines)  - 6 new routes
├── admin.py                  (+113 lines) - 2 admin panels
└── user_data_utils.py        (410 lines)  - NEW utility file
```

**Templates:**
```
templates/
└── user_data/               - NEW directory
    ├── settings.html
    ├── request_export.html
    ├── export_status.html
    ├── request_deletion.html
    ├── confirm_deletion.html
    └── deletion_complete.html
```

**Tests:**
```
tests/
└── test_user_data.py        (642 lines) - 36 tests, 100% pass
```

### Quick Test

```bash
# Run tests
python manage.py test active_interview_app.tests.test_user_data

# Start dev server
PROD=false python manage.py runserver

# Test URLs
http://localhost:8000/profile/data-settings/
http://localhost:8000/profile/data-export/request/
http://localhost:8000/profile/delete-account/
```

---

## For Admins

### Monitor Requests

**Django Admin:**
```
/admin/active_interview_app/dataexportrequest/
/admin/active_interview_app/deletionrequest/
```

**Common Tasks:**
- Check failed exports: filter by `status=failed`
- Review error messages
- Clean expired exports (>7 days)
- Monitor deletion audit trail

---

## Environment Setup

### Development
```bash
PROD=false  # Uses console email backend
```

### Production
```bash
PROD=true
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@activeinterviewservice.me
```

---

## Key Features

✅ **GDPR/CCPA Compliant**
- Right to access (export)
- Right to be forgotten (delete)
- Right to data portability

✅ **Secure**
- Password verification for deletion
- 7-day link expiration
- User-specific access control
- Audit trail for compliance

✅ **User-Friendly**
- Clear navigation from profile
- Progress indicators
- Email notifications (production)
- Helpful warnings and confirmations

---

## Troubleshooting

### Email Error in Dev
```bash
# Solution: Use dev mode
PROD=false python manage.py runserver
```

### Export Failed
```bash
# Check admin panel for error message
# View in Django shell:
python manage.py shell
>>> from active_interview_app.models import DataExportRequest
>>> DataExportRequest.objects.filter(status='failed').last().error_message
```

### Link Expired
- Request new export (links expire after 7 days)

---

## Full Documentation

📖 **Complete Guide:** `/docs/features/user-data-export-deletion.md`

Includes:
- Detailed user guide
- Technical implementation
- API reference
- Admin guide
- Configuration
- Testing
- Troubleshooting

---

## Related Issues

- **#63** - GDPR/CCPA data export & delete (parent issue)
- **#64** - Data Export Functionality
- **#65** - Data Deletion & Anonymization

All issues: ✅ **CLOSED** (November 11, 2025)
