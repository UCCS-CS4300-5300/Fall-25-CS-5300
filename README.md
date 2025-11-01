# Active Interview Service

AI-powered interview practice platform to help job seekers prepare for technical interviews with personalized feedback and scoring.

## Overview

Active Interview Service is a Django web application that allows users to practice job interviews with an OpenAI-powered AI interviewer. Upload your resume and a job listing, select an interview type and difficulty, then receive timed questions and real-time feedback to improve your interview skills.

**Production:** https://active-interview-service-production.up.railway.app

## Google OAuth Setup

The application supports Google OAuth authentication, allowing users to sign in with their Google accounts.

### For Local Development

**Prerequisites:**
- Google Cloud Console account
- Active Django admin account (see "Registering Accounts" above)

**Steps:**

1. **Create Google OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing project
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Configure OAuth consent screen if prompted
   - Application type: **Web application**
   - Name: `Active Interview Service - Local`
   - Authorized redirect URIs:
     ```
     http://localhost:8000/accounts/google/login/callback/
     http://127.0.0.1:8000/accounts/google/login/callback/
     ```
   - Click "Create" and save your **Client ID** and **Client Secret**

2. **Configure Django Site**
   - Start your Django server: `python manage.py runserver`
   - Access Django admin: `http://127.0.0.1:8000/admin`
   - Navigate to **Sites** (under "SITES" section)
   - Edit the site with ID=1:
     - Domain name: `localhost:8000`
     - Display name: `Active Interview Service`
   - Save changes

3. **Add Google OAuth App in Django Admin**
   - In Django admin, navigate to **Social applications** (under "SOCIAL ACCOUNTS")
   - Click "Add social application"
   - Fill in the form:
     - **Provider**: Google
     - **Name**: Google OAuth
     - **Client ID**: (paste your Google Client ID)
     - **Secret key**: (paste your Google Client Secret)
     - **Sites**: Select "localhost:8000"
   - Click "Save"

4. **Test OAuth Login**
   - Navigate to `http://localhost:8000/login/`
   - Click "Continue with Google"
   - You should be redirected to Google login
   - After authentication, you'll be redirected back to the application

**Troubleshooting Local OAuth:**
```bash
# Run diagnostic script
cd active_interview_backend
python manage.py shell < ../temp/fix_oauth_setup.py

# Manually verify Site configuration
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> Site.objects.get(id=1)
```

### For Production/CD Deployment

**Prerequisites:**
- Railway/production environment with deployed application
- Production domain name

**Steps:**

1. **Create Production OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new OAuth 2.0 Client ID or edit existing
   - Application type: **Web application**
   - Name: `Active Interview Service - Production`
   - Authorized redirect URIs:
     ```
     https://app.activeinterviewservice.me/accounts/google/login/callback/
     https://your-railway-domain.up.railway.app/accounts/google/login/callback/
     ```
   - Click "Create" and save credentials

2. **Set Environment Variables**

   Add these environment variables to your Railway/production environment:
   ```bash
   GOOGLE_OAUTH_CLIENT_ID=<your production client ID>
   GOOGLE_OAUTH_CLIENT_SECRET=<your production client secret>
   SITE_DOMAIN=app.activeinterviewservice.me
   SITE_NAME=Active Interview Service
   ```

3. **Configure Production Site via Django Shell**

   SSH into your production environment or use Railway's shell:
   ```bash
   python manage.py shell
   ```

   Then run:
   ```python
   from django.contrib.sites.models import Site
   from allauth.socialaccount.models import SocialApp

   # Update Site
   site = Site.objects.get(id=1)
   site.domain = 'app.activeinterviewservice.me'
   site.name = 'Active Interview Service'
   site.save()

   # Create or update Google OAuth app
   app, created = SocialApp.objects.get_or_create(
       provider='google',
       defaults={'name': 'Google OAuth'}
   )
   app.client_id = 'YOUR_PRODUCTION_CLIENT_ID'
   app.secret = 'YOUR_PRODUCTION_CLIENT_SECRET'
   app.save()

   # Link app to site
   if not app.sites.filter(id=1).exists():
       app.sites.add(site)

   print(f"OAuth configured for {site.domain}")
   ```

4. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

5. **Test Production OAuth**
   - Navigate to `https://app.activeinterviewservice.me/login/`
   - Click "Continue with Google"
   - Verify successful authentication

**Automated Production Setup (Recommended for CD):**

Create a management command to automate OAuth setup:

```bash
# In your deployment script or Railway startup
python manage.py shell << 'EOF'
import os
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# Get from environment variables
client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
site_domain = os.getenv('SITE_DOMAIN', 'app.activeinterviewservice.me')
site_name = os.getenv('SITE_NAME', 'Active Interview Service')

if client_id and client_secret:
    # Update site
    site, _ = Site.objects.update_or_create(
        id=1,
        defaults={'domain': site_domain, 'name': site_name}
    )

    # Update OAuth app
    app, _ = SocialApp.objects.update_or_create(
        provider='google',
        defaults={
            'name': 'Google OAuth',
            'client_id': client_id,
            'secret': client_secret
        }
    )

    # Link to site
    app.sites.add(site)
    print(f"✓ OAuth configured for {site_domain}")
else:
    print("⚠ OAuth credentials not found in environment variables")
EOF
```

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

### Environment Variables & Secrets

**For CI Pipeline:**
- `DJANGO_SECRET_KEY` - Django secret key for testing environment
- `OPENAI_API_KEY` - OpenAI API key for AI code reviews

**For CD Pipeline:**
- `RAILWAY_TOKEN` - Railway authentication token
- `RAILWAY_SERVICE_ID` - Railway service identifier for deployment

**For OAuth (Production):**
- `GOOGLE_OAUTH_CLIENT_ID` - Google OAuth Client ID for production
- `GOOGLE_OAUTH_CLIENT_SECRET` - Google OAuth Client Secret for production
- `SITE_DOMAIN` - Production domain (e.g., `app.activeinterviewservice.me`)
- `SITE_NAME` - Application name (e.g., `Active Interview Service`)

**Setting Secrets in GitHub:**
1. Navigate to your repository on GitHub
2. Go to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret with its corresponding value

**Setting Environment Variables in Railway:**
1. Log into Railway dashboard
2. Select your project
3. Navigate to Variables tab
4. Add each environment variable

---

## Troubleshooting

### OAuth Issues

#### Error: "Redirect URI mismatch"
**Problem:** Google OAuth redirect URI doesn't match configured URIs.

**Solution:**
1. Check your Google Cloud Console OAuth credentials
2. Ensure redirect URIs include:
   - Local: `http://localhost:8000/accounts/google/login/callback/` and `http://127.0.0.1:8000/accounts/google/login/callback/`
   - Production: `https://your-domain.com/accounts/google/login/callback/`
3. Make sure there are no trailing slashes missing or extra

#### Error: "Site matching query does not exist"
**Problem:** Django Site object not configured correctly.

**Solution:**
```bash
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> Site.objects.update_or_create(id=1, defaults={'domain': 'localhost:8000', 'name': 'Active Interview Service'})
```

#### Error: "SocialApp matching query does not exist"
**Problem:** Google OAuth app not configured in Django admin.

**Solution:**
1. Go to Django admin: `/admin/`
2. Navigate to Social applications
3. Add a new social application with Google provider
4. Link it to your site

#### OAuth Button Goes to Dead End
**Problem:** OAuth credentials not set up or Site configuration incorrect.

**Solution:**
Run the diagnostic script:
```bash
cd active_interview_backend
python manage.py shell < ../temp/fix_oauth_setup.py
```

This will identify the specific issue and provide fix commands.

#### Users Can't Login After OAuth
**Problem:** User profile or group permissions not set up.

**Solution:**
1. Ensure `average_role` group exists (see "Registering Accounts")
2. Check `active_interview_app/adapters.py` is configured correctly
3. Verify `SOCIALACCOUNT_ADAPTER` setting points to custom adapter

### Database Issues

#### Migrations Out of Sync
```bash
# Reset migrations (WARNING: This deletes data)
python manage.py migrate --fake-initial
python manage.py migrate
```

#### Database Locked (SQLite)
```bash
# Stop all Django processes
pkill -f runserver

# Restart server
python manage.py runserver
```

### Static Files Not Loading

```bash
# Clear and recollect static files
rm -rf staticfiles/
python manage.py collectstatic --noinput
```

### Docker Issues

#### Container Won't Start
```bash
# Full cleanup and restart
docker-compose down --volumes --remove-orphans
docker system prune -f
docker-compose up -d --build
```

#### Can't Connect to Container
```bash
# Check container logs
docker-compose logs web

# Check container status
docker-compose ps
```

---

## AI Use

1. The git diff script in CI.yml was iteratively designed with the help of chatgpt.
2. The check_coverage.sh script was generated by chatgpt, although minor modifications have been made: https://chatgpt.com/share/67cf5f81-5500-8006-894a-7f8403fcc0f
3. The chatbox image on the homepage was generated by chatgpt.
4. The E2E authentication script is adapted from a ChatGPT response
5. The chrome and chromedriver install scripts in CI.yml are adapted from ChatGPT responses
6. The jQuery/Ajax script in chat-view.html is adapted from a ChatGPT response
7. ChatGPT was used to rewrite system prompts for greater clarity
8. The chat creation button hiding script was adapted from a ChatGPT response.
9. Claude Code was used to consolidate and fix the CI/CD workflow configuration.
10. Claude Code was used to create OAuth templates, fix authentication navigation, and write comprehensive tests.

---

## Technologies

1. Django
2. Nginx
3. Gunicorn
4. ChatGPT
5. Bootstrap 5
6. Docker-Compose
7. Digital Ocean
8. Ajax
9. jQuery
10. DOMPurify
11. pymupdf
