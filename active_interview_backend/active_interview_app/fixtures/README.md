# Seed Data Fixtures

This directory contains Django fixtures for loading test data into the database.

## seed_data.json

Comprehensive seed data for testing the Active Interview application.

### What's Included

**Users (3 total):**
1. **Admin User**
   - Username: `admin_user`
   - Email: `admin@example.com`
   - Role: Admin
   - Superuser: Yes

2. **Interviewer**
   - Username: `interviewer_jane`
   - Email: `jane.interviewer@example.com`
   - Role: Interviewer
   - Has question bank and template

3. **Candidate**
   - Username: `candidate_john`
   - Email: `john.candidate@example.com`
   - Role: Candidate
   - Has completed practice interview

**Interviewer Resources:**
- 1 Question Bank: "Software Engineering Technical Questions"
- 8 Questions (easy/medium/hard difficulty)
- 5 Tags: #python, #django, #sql, #behavioral, #algorithms
- 1 Interview Template: "Full-Stack Developer Interview" (3 sections, auto-assembly enabled)

**Candidate Resources:**
- 1 Uploaded Resume (parsed with skills, experience, education)
- 1 Job Listing (Software Engineer position)
- 1 Completed Practice Interview (with conversation history)
- 1 Exportable Report (with scores and feedback)

### Loading the Fixtures

#### Fresh Database (Recommended)

```bash
cd active_interview_backend

# Reset database (WARNING: This deletes all data)
rm db.sqlite3
python manage.py migrate

# Load seed data
python manage.py loaddata seed_data.json

# Create actual superuser password (optional)
python manage.py changepassword admin_user
```

#### Existing Database

```bash
cd active_interview_backend

# Load seed data (will fail if PKs already exist)
python manage.py loaddata seed_data.json
```

**Note:** If you get integrity errors about existing primary keys, you need to either:
1. Reset the database (see "Fresh Database" above), or
2. Edit the fixture to use different primary keys

### Default Passwords

The fixture includes placeholder password hashes. **These are NOT secure and will NOT work for login.**

After loading, set passwords using:

```bash
# Set password for each user
python manage.py changepassword admin_user
python manage.py changepassword interviewer_jane
python manage.py changepassword candidate_john
```

Or use Django shell to set test passwords:

```python
python manage.py shell

from django.contrib.auth.models import User

# Set password for admin
admin = User.objects.get(username='admin_user')
admin.set_password('admin123')  # Use your desired password
admin.save()

# Set password for interviewer
interviewer = User.objects.get(username='interviewer_jane')
interviewer.set_password('interviewer123')
interviewer.save()

# Set password for candidate
candidate = User.objects.get(username='candidate_john')
candidate.set_password('candidate123')
candidate.save()
```

### File Uploads Note

The fixture references uploaded files:
- `uploads/john_doe_resume.pdf`
- `uploads/software_engineer_job.txt`

These files **don't actually exist** in the filesystem. The fixture only creates database records pointing to these paths.

**To use file uploads in tests:**
1. Either create dummy files at these paths in your media directory
2. Or modify your tests to handle missing files gracefully
3. Or upload new files through the application after loading fixtures

### Testing the Loaded Data

After loading and setting passwords, you can test by:

1. **Login as Admin:**
   - Username: `admin_user`
   - Access admin panel at `/admin/`
   - View all users and data

2. **Login as Interviewer:**
   - Username: `interviewer_jane`
   - View question bank with 8 questions
   - View interview template "Full-Stack Developer Interview"
   - Create new invitations

3. **Login as Candidate:**
   - Username: `candidate_john`
   - View completed practice interview
   - View interview results and exportable report

### Customizing the Fixtures

To modify the seed data:

1. Edit `seed_data.json` directly, or
2. Load the fixtures, make changes through Django admin, then export:

```bash
# Export specific models
python manage.py dumpdata active_interview_app.QuestionBank \
                         active_interview_app.Question \
                         active_interview_app.Tag \
                         --indent 2 > custom_questions.json

# Export all app data
python manage.py dumpdata active_interview_app --indent 2 > full_seed.json
```

### Troubleshooting

**Problem:** `IntegrityError: UNIQUE constraint failed`
- **Solution:** Primary keys already exist. Reset database or edit PKs in fixture.

**Problem:** `DoesNotExist: User matching query does not exist`
- **Solution:** Make sure User objects are loaded before related objects (order matters in JSON).

**Problem:** Can't login with loaded users
- **Solution:** Password hashes in fixtures are placeholders. Use `changepassword` or `set_password()`.

**Problem:** FileNotFoundError for uploaded files
- **Solution:** Create dummy files or modify tests to handle missing files.

### CI/CD Usage

For automated testing, you can load fixtures in your test setup:

```python
# In tests
from django.core.management import call_command

class MyTestCase(TestCase):
    fixtures = ['seed_data.json']

    def setUp(self):
        # Fixtures are automatically loaded
        # Set passwords for login tests
        from django.contrib.auth.models import User
        candidate = User.objects.get(username='candidate_john')
        candidate.set_password('testpass123')
        candidate.save()
```

Or in pytest:

```python
import pytest
from django.core.management import call_command

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'seed_data.json')
```
