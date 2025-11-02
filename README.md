# Active Interview Service

AI-powered interview practice platform to help job seekers prepare for technical interviews with personalized feedback and scoring.

## Overview

Active Interview Service is a Django web application that allows users to practice job interviews with an OpenAI-powered AI interviewer. Upload your resume and a job listing, select an interview type and difficulty, then receive timed questions and real-time feedback to improve your interview skills.

**Production:** https://active-interview-service-production.up.railway.app

---

## Quick Start

Choose your preferred development method:

### Option 1: Manual Setup (Recommended for Beginners)

```bash
# 1. Clone and setup
git clone https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300.git
cd Fall-25-CS-5300
python3 -m venv myenv
source myenv/bin/activate  # Windows: .\myenv\Scripts\activate

# 2. Install dependencies
cd active_interview_backend
pip install -r requirements.txt

# 3. Configure environment
export PROD=false
export DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
export OPENAI_API_KEY=your_openai_api_key_here

# 4. Setup database and run
python manage.py migrate
python manage.py createsuperuser  # Create admin account
python manage.py runserver
```

**Access:** `http://127.0.0.1:8000`

**Next:** Create `average_role` group in Django admin to enable user registration. See [Setup Guide](docs/setup/local-development.md#5-create-superuser-and-configure-permissions).

### Option 2: Docker (Recommended for Teams)

```bash
# 1. Clone repository
git clone https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300.git
cd Fall-25-CS-5300

# 2. Create .env file
echo "DJANGO_SECRET_KEY=your_secret_key" > .env
echo "OPENAI_API_KEY=your_openai_key" >> .env

# 3. Start containers
docker-compose up -d --build
```

**Access:** `http://127.0.0.1`

---

## Features

### For Job Seekers

- 📝 **Upload Resumes & Job Listings** - PDF/DOCX support with text extraction
- 🤖 **AI Interview Practice** - Powered by OpenAI GPT-4o
- 🎯 **Multiple Interview Types** - General, Technical Skills, Personality, Final Screening
- 📊 **Performance Feedback** - AI-generated scores and detailed feedback
- 📈 **Progress Tracking** - Save and review past interview sessions
- 📄 **PDF Reports** - Export professional interview reports

### For Developers

- 🔒 **User Authentication** - Django built-in auth with groups
- 🔌 **REST API** - Django REST Framework for resume/job management
- 🧪 **Comprehensive Testing** - 492+ tests with 80%+ coverage
- 🚀 **CI/CD Pipeline** - Automated testing, linting, security scans
- 🐳 **Docker Support** - Consistent development and production environments
- ☁️ **Railway Deployment** - One-click production deployment

---

## Documentation

📚 **[Complete Documentation →](docs/)**

### Setup Guides

- **[Local Development](docs/setup/local-development.md)** - Detailed setup instructions
- **[Testing Guide](docs/setup/testing.md)** - Run tests and check coverage
- **[BDD Feature Files](docs/setup/bdd-feature-files.md)** - Creating feature files from GitHub issues
- **[Troubleshooting](docs/setup/troubleshooting.md)** - Common issues and solutions

### Deployment

- **[CI/CD Pipeline](docs/deployment/ci-cd.md)** - GitHub Actions workflows
- **[Railway Deployment](docs/deployment/railway.md)** - Production deployment guide

### Architecture

- **[System Overview](docs/architecture/overview.md)** - High-level architecture
- **[Database Models](docs/architecture/models.md)** - Model reference
- **[API Reference](docs/architecture/api.md)** - REST API documentation

### Features

- **[Exportable Reports](docs/features/exportable-reports.md)** - PDF report generation

---

## Technology Stack

**Backend:**
- Django 4.2.19
- Django REST Framework 3.15.2
- OpenAI GPT-4o
- Gunicorn (production)

**Database:**
- SQLite (development)
- PostgreSQL (production)

**Frontend:**
- Bootstrap 5
- jQuery
- Ajax

**File Processing:**
- PyMuPDF (PDF parsing)
- python-docx (DOCX parsing)
- ReportLab (PDF generation)

**Deployment:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- Railway (hosting)
- GitHub Actions (CI/CD)

**Testing:**
- Django TestCase
- Selenium (E2E)
- Coverage.py
- Behave (BDD)

---

## Project Structure

```
Fall-25-CS-5300/
├── active_interview_backend/   # Django application
│   ├── active_interview_app/   # Main app
│   │   ├── models.py          # Database models
│   │   ├── views.py           # View logic
│   │   ├── templates/         # HTML templates
│   │   └── tests/             # Test suite
│   ├── features/              # BDD feature files
│   └── manage.py              # Django CLI
├── docs/                       # Documentation
│   ├── setup/                 # Setup guides
│   ├── deployment/            # Deployment docs
│   ├── architecture/          # Architecture docs
│   └── features/              # Feature specs
├── .github/workflows/         # CI/CD pipelines
├── docker-compose.yml         # Development containers
├── docker-compose.prod.yml    # Production containers
└── README.md                  # This file
```

---

## Testing

Run the full test suite:

```bash
cd active_interview_backend
python manage.py test
```

With coverage:

```bash
coverage run manage.py test
coverage report -m
coverage html  # Generate HTML report
```

**CI Requirement:** Minimum 80% code coverage

**[Full Testing Guide →](docs/setup/testing.md)**

---

## Security Considerations

### User Profile Privacy

The `user_profile` view (`active_interview_app/templates/user_profile.html`) displays user information to interviewers and admins when viewing candidate profiles. This view currently shows:

- ✅ Username
- ✅ Email
- ✅ First Name
- ✅ Last Name
- ✅ Role
- ✅ Uploaded resumes (view-only)
- ✅ Uploaded job listings (view-only)

**⚠️ IMPORTANT:** When adding new fields to the `UserProfile` model or user information display:

1. **Always review what information is shown in `user_profile.html`**
2. **Exclude sensitive personal information** (e.g., birthday, SSN, phone number, address)
3. **Owner-only features** (edit/delete buttons, role change requests) must remain excluded from this view
4. **Test with different user roles** (admin, interviewer, candidate) to ensure proper information visibility

The current fields displayed are appropriate for professional interview contexts, but future additions must be carefully evaluated to prevent exposing sensitive candidate information.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick workflow:**
1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure tests pass and coverage ≥ 80%
5. Submit a pull request

---

## CI/CD Pipeline

**Continuous Integration (`.github/workflows/CI.yml`):**
- ✅ Linting (flake8, djlint)
- ✅ Security scans (safety, bandit)
- ✅ Test suite with coverage validation
- ✅ AI-powered code review

**Continuous Deployment (`.github/workflows/CD.yml`):**
- 🚀 Automatic deployment to Railway on push to `main`

**[CI/CD Documentation →](docs/deployment/ci-cd.md)**

---

## Team & AI Attribution

**Team:** Group 7, Spring 2025

**AI Tools Used:**
1. ChatGPT - Git diff script, coverage checker, E2E auth script, Chrome/Chromedriver install, jQuery/Ajax, system prompt rewrites
2. Claude Code - CI/CD consolidation and fixes, test infrastructure improvements

See full attribution in [AI Use section of README](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300#ai-use) (legacy).

---

## License

[Specify license here]

---

## Support

- 📖 **Documentation:** [docs/](docs/)
- 🐛 **Issues:** [GitHub Issues](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/discussions)

---

## Acknowledgments

Built with Django, powered by OpenAI, deployed on Railway.
