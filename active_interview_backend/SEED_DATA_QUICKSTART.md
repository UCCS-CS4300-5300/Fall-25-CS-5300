# Seed Data Quick Start

This guide helps you quickly set up test data for the Active Interview application.

## Quick Load (Recommended)

Use the helper script for automatic setup:

```bash
cd active_interview_backend

# Option 1: Load into existing database
python load_seed_data.py

# Option 2: Reset database and load fresh data
python load_seed_data.py --reset
```

This will:
- Load all seed data (users, questions, templates, etc.)
- Set passwords automatically
- Display a summary of loaded data

## Manual Load

If you prefer manual control:

```bash
cd active_interview_backend

# Reset database (optional but recommended)
rm db.sqlite3
python manage.py migrate

# Load fixtures
python manage.py loaddata seed_data.json

# Set passwords manually
python manage.py shell
```

Then in the shell:
```python
from django.contrib.auth.models import User

User.objects.get(username='admin_user').set_password('admin123') and User.objects.get(username='admin_user').save()
User.objects.get(username='interviewer_jane').set_password('interviewer123') and User.objects.get(username='interviewer_jane').save()
User.objects.get(username='candidate_john').set_password('candidate123') and User.objects.get(username='candidate_john').save()

exit()
```

## Test Users

After loading, you can login with:

### Admin User
- **Username:** `admin_user`
- **Password:** `admin123`
- **Email:** admin@example.com
- **Role:** Admin (superuser)

### Interviewer
- **Username:** `interviewer_jane`
- **Password:** `interviewer123`
- **Email:** jane.interviewer@example.com
- **Role:** Interviewer
- **Has:** Question bank with 8 questions, 1 interview template

### Candidate
- **Username:** `candidate_john`
- **Password:** `candidate123`
- **Email:** john.candidate@example.com
- **Role:** Candidate
- **Has:** Completed practice interview with report

## What's Included

### For Interviewer (interviewer_jane)
- ✅ 1 Question Bank: "Software Engineering Technical Questions"
- ✅ 8 Questions covering Python, Django, SQL, algorithms
- ✅ 5 Tags: #python, #django, #sql, #behavioral, #algorithms
- ✅ 1 Interview Template: "Full-Stack Developer Interview"
  - 3 sections (Introduction, Technical Assessment, Closing)
  - Auto-assembly enabled
  - Configured difficulty distribution (20% easy, 60% medium, 20% hard)

### For Candidate (candidate_john)
- ✅ 1 Resume (parsed with skills, experience, education)
- ✅ 1 Job Listing (Software Engineer position)
- ✅ 1 Completed Practice Interview
  - Full conversation history (5 Q&A exchanges)
  - Industry Skills interview type
- ✅ 1 Exportable Report
  - Scores: Professionalism (92), Subject Knowledge (88), Clarity (90), Overall (89)
  - Detailed feedback and rationales
  - Question-by-question analysis

## Running the App

After loading seed data:

```bash
python manage.py runserver
```

Then visit http://localhost:8000 and login with any of the test users.

## Testing Different Workflows

### As Interviewer
1. Login as `interviewer_jane`
2. View your question bank at `/questions/banks/`
3. View your template at `/templates/`
4. Create a new invitation at `/invitations/create/`

### As Candidate
1. Login as `candidate_john`
2. View your completed interview at `/chat/`
3. View interview results and exportable report

### As Admin
1. Login as `admin_user`
2. Access Django admin at `/admin/`
3. View and manage all data

## Troubleshooting

**Problem:** Users exist but can't login
```bash
# Re-run the helper script to reset passwords
python load_seed_data.py
```

**Problem:** Fixtures fail to load
```bash
# Reset database completely
python load_seed_data.py --reset
```

**Problem:** Import errors when running helper script
```bash
# Make sure you're in the correct directory
cd active_interview_backend

# Ensure dependencies are installed
pip install -r requirements.txt
```

## For Automated Testing

Use in pytest:

```python
import pytest

@pytest.fixture(scope='session')
def seed_data(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        from django.core.management import call_command
        call_command('loaddata', 'seed_data.json')

        # Set passwords for testing
        from django.contrib.auth.models import User
        for username, password in [
            ('admin_user', 'admin123'),
            ('interviewer_jane', 'interviewer123'),
            ('candidate_john', 'candidate123')
        ]:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()

def test_candidate_login(client, seed_data):
    response = client.post('/accounts/login/', {
        'username': 'candidate_john',
        'password': 'candidate123'
    })
    assert response.status_code == 302  # Redirect after login
```

## Next Steps

After loading seed data:
1. Explore the different user roles and their capabilities
2. Create additional questions, templates, or invitations
3. Test the interview workflow end-to-end
4. Customize the seed data for your specific testing needs

For more details, see `active_interview_app/fixtures/README.md`.
