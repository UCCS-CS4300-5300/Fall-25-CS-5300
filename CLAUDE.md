# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered interview practice platform called "Active Interview Service". It's a Django web application that allows users to practice job interviews with an OpenAI-powered interviewer. The system analyzes uploaded resumes and job listings to generate personalized interview questions and provide timed practice sessions.

## Core Architecture

### Application Structure
- **Django monolith**: Single Django app (`active_interview_app`) within project (`active_interview_project`)
- **Backend location**: All Django code is in `active_interview_backend/`
- **Deployment**: Docker Compose with Django + Gunicorn + Nginx
- **Database**: SQLite (stored in `active_interview_backend/db/`)
- **Static files**: Served through Nginx in production, collected to `staticfiles/`

### Key Models (active_interview_backend/active_interview_app/models.py)
- **UploadedResume**: User's resume files with extracted text content
- **UploadedJobListing**: Job posting documents with extracted text
- **Chat**: Interview session containing messages (JSON), key questions (JSON), difficulty (1-10), type (General/Industry Skills/Personality/Final Screening), and foreign keys to resume/job listing

### OpenAI Integration
- Uses OpenAI GPT-4o model for interview conversation
- System prompts generated dynamically based on resume, job listing, difficulty, and interview type
- AI generates 10 timed key questions per interview session
- Located primarily in views.py (ChatView, RestartChat, KeyQuestionsView)

### File Processing
- PDF files: Extracted with pymupdf4llm
- DOCX files: Extracted with python-docx
- File validation with filetype library
- Text content stored in model fields for AI processing

## Environment Setup

### Required Environment Variables
- `DJANGO_SECRET_KEY`: Django secret (auto-generated in dev if PROD=false)
- `OPENAI_API_KEY`: Required for AI interview functionality
- `PROD`: Set to "false" for development, "true" for production

### Local Development (Manual)
```bash
# From project root
python3 -m venv myenv
source myenv/bin/activate  # or .\myenv\bin\activate on Windows PowerShell

# Navigate to backend
cd active_interview_backend
pip install -r requirements.txt

# Generate secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set environment variables
export PROD=false
export DJANGO_SECRET_KEY='<your-secret-key>'
export OPENAI_API_KEY=<your-api-key>

# Run migrations and start server
python3 manage.py migrate
python3 manage.py runserver
```

### Docker Compose Development
```bash
# From project root
# Create .env file with DJANGO_SECRET_KEY and OPENAI_API_KEY
docker-compose up -d --build
```

Access at: `http://127.0.0.1:8000` (manual) or `http://127.0.0.1` (Docker)

### Initial Account Setup
After first run, create a superuser and configure permissions:
```bash
python manage.py createsuperuser
# Access admin at http://127.0.0.1:8000/admin
# Create group called "average_role" with desired permissions
```

## Testing

### Running Tests
```bash
# From active_interview_backend/
python3 manage.py test

# With coverage
coverage run manage.py test
coverage report -m
```

### Test Structure
- All tests in `active_interview_backend/active_interview_app/tests/`
- `test_chat.py`: Chat/interview session tests
- `test_upload.py`: File upload and document management tests
- `test_e2e.py`: End-to-end Selenium tests
- `test.py`: Basic functionality tests

### BDD Feature Files
- Feature files (Gherkin): `active_interview_backend/features/`
- Step definitions: `active_interview_backend/active_interview_app/tests/steps/`
- Feature files document user stories and acceptance criteria
- Use behave or pytest-bdd for running BDD scenarios

### Coverage Requirements
- Minimum 80% coverage enforced by CI
- Configuration in `.coveragerc`: excludes tests/, migrations/, __init__.py, manage.py
- Check script: `scripts/check-coverage.sh coverage_report.txt`

## CI/CD

### GitHub Actions Workflows (.github/workflows/)

**CI.yml** - Runs on all pushes/PRs:
1. **AI Code Review**: Uses OpenAI to review git diff (outputs to artifacts and step summary)
2. **Testing**:
   - Builds production Docker containers
   - Installs Chrome/Chromedriver for E2E tests
   - Runs Django tests with coverage
   - Enforces 80% coverage threshold
3. **Linting**:
   - Python: flake8 (config in `.flake8`)
   - Templates: djlint (config in `djlint.toml`)

**CD.yml**: Deployment workflow (triggered separately)

### Linting
```bash
# Python linting
flake8 --config active_interview_backend/.flake8 .

# Template linting
djlint --configuration active_interview_backend/djlint.toml active_interview_backend/active_interview_app/templates/ --lint
```

## Common Commands

### Django Management
```bash
# Navigate to backend first
cd active_interview_backend

# Database migrations
python3 manage.py makemigrations
python3 manage.py migrate

# Collect static files (required after CSS/image changes)
python3 manage.py collectstatic --noinput

# Create superuser
python3 manage.py createsuperuser

# Run development server
python3 manage.py runserver
```

### Docker Operations
```bash
# Start containers (development)
docker-compose up -d --build

# Start containers (production mode)
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker logs django
docker logs nginx

# Execute commands in container
docker exec django python3 manage.py migrate
docker exec django coverage run manage.py test
```

### Cleaning/Restarting
```bash
# Clean Docker environment
docker-compose down --volumes --remove-orphans
docker system prune --all --volumes
sudo systemctl restart docker

# Clean git-tracked files (preserves .env and db/)
git clean -fdx -e .env -e active_interview_backend/db

# Automated clean restart (Linux/Mac only - commits code first!)
sudo ./scripts/clean-restart.sh
```

## URL Structure

Key routes (defined in `active_interview_backend/active_interview_app/urls.py`):
- `/` - Homepage
- `/accounts/login/` - User login
- `/accounts/register/` - User registration
- `/profile/` - User profile with document management
- `/chat/` - Interview session list
- `/chat/create/` - Create new interview
- `/chat/<id>/` - Active interview view (AJAX-based)
- `/chat/<id>/edit/` - Edit interview settings
- `/chat/<id>/restart/` - Restart interview session
- `/chat/<id>/results/` - View interview results/charts
- `/document/` - Document list (resumes and job postings)
- `/upload-file/` - File upload endpoint

## Key Technologies
- **Backend**: Django 4.2.19, Django REST Framework
- **Server**: Gunicorn (3 workers in production)
- **Web Server**: Nginx (reverse proxy, static file serving)
- **AI**: OpenAI GPT-4o
- **Frontend**: Bootstrap 5, jQuery, Ajax, DOMPurify
- **File Processing**: PyMuPDF, python-docx, filetype
- **Testing**: Django TestCase, Selenium, Coverage.py
- **Deployment**: Docker Compose, Digital Ocean

## Production Notes
- Production uses `docker-compose.prod.yml` with `PROD=true`
- SSL certificates mounted from host at `/etc/letsencrypt`
- Nginx config: `nginx.prod.conf` (prod) vs `nginx.local.conf` (dev)
- Static files collected to shared volume between Django and Nginx
- Allowed hosts include: `app.activeinterviewservice.me`, localhost, 127.0.0.1
- CSRF trusted origins: `https://app.activeinterviewservice.me`

## Development Conventions
- Python code follows flake8 standards (see `.flake8` config)
- Templates follow djlint standards (see `djlint.toml`)
- All new features require tests to maintain 80% coverage
- Interview system prompts are in views.py as textwrap.dedent() strings
