# Troubleshooting Guide

Common issues and solutions when working with Active Interview Service.

## Setup Issues

### Python Version Incompatibility

**Problem:** Wrong Python version

**Solution:**
```bash
# Verify Python version
python --version

# Must be Python 3.12 or higher
# If not, install Python 3.12+
```

**Note:** This project requires Python 3.12+. Both CI and Docker use Python 3.12.

---

### Missing Django Module

**Problem:** `ModuleNotFoundError: No module named 'django'`

**Solution:**
```bash
# Make sure virtual environment is activated
source myenv/bin/activate  # Linux/Mac
.\myenv\Scripts\activate   # Windows

# Install dependencies
cd active_interview_backend
pip install -r requirements.txt
```

---

### Django Secret Key Not Set

**Problem:** `Django SECRET_KEY is not set` or `KeyError: 'DJANGO_SECRET_KEY'`

**Solution:**
```bash
# Generate a secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set environment variable
# Linux/Mac:
export DJANGO_SECRET_KEY='<generated-key>'

# Windows PowerShell:
$env:DJANGO_SECRET_KEY = "<generated-key>"

# Or add to .env file for Docker
echo "DJANGO_SECRET_KEY=<generated-key>" >> .env
```

---

### OpenAI API Key Missing

**Problem:** `OpenAI API key not configured`

**Solution:**
```bash
# Get API key from https://platform.openai.com/api-keys

# Linux/Mac:
export OPENAI_API_KEY=sk-...

# Windows PowerShell:
$env:OPENAI_API_KEY = "sk-..."

# For Docker, add to .env:
echo "OPENAI_API_KEY=sk-..." >> .env
```

---

## Docker Issues

### Docker Container Fails to Start

**Problem:** Container exits immediately or won't start

**Solution:**
```bash
# Check logs
docker logs django
docker logs nginx

# Common fix: Rebuild without cache
docker-compose down --volumes --remove-orphans
docker-compose up -d --build --force-recreate
```

---

### Port Already in Use

**Problem:** `Error: bind: address already in use`

**Solution:**
```bash
# Check what's using port 80/8000
# Linux/Mac:
lsof -i :80
lsof -i :8000

# Windows:
netstat -ano | findstr :80
netstat -ano | findstr :8000

# Kill the process or change Docker Compose port
# Edit docker-compose.yml:
# ports:
#   - "8080:80"  # Use port 8080 instead
```

---

### Docker Network Issues (Arch Linux)

**Problem:** DNS resolution fails in containers

**Solution:**

Follow [this Arch Linux forum post](https://bbs.archlinux.org/viewtopic.php?pid=2025168#p2025168) to fix Docker networking.

Quick fix:
```bash
sudo systemctl restart docker
```

---

### Clean Docker Environment

**When:** Docker behaving inconsistently

**Solution:**
```bash
# Nuclear option - clean everything
docker-compose down --volumes --remove-orphans
docker system prune --all --volumes
sudo systemctl restart docker

# Then rebuild
docker-compose up -d --build
```

---

## Database Issues

### Migration Conflicts

**Problem:** `Conflicting migrations detected`

**Solution:**
```bash
# Create a merge migration
python manage.py makemigrations --merge

# Apply migrations
python manage.py migrate
```

---

### Database Locked (SQLite)

**Problem:** `database is locked`

**Solution:**
```bash
# Make sure no other processes are accessing the database
# Stop the server and restart

# If persists, delete and recreate database:
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

### Can't Create Accounts (Permission Issue)

**Problem:** Registration doesn't work

**Solution:**

The `average_role` group must exist. Create it:

1. Create superuser: `python manage.py createsuperuser`
2. Start server: `python manage.py runserver`
3. Visit `http://127.0.0.1:8000/admin`
4. Go to **Groups** → **Add group**
5. Name it `average_role`
6. Select permissions
7. Save

---

## Static Files Issues

### CSS/Images Not Loading

**Problem:** Changes to CSS/images don't appear

**Solution:**
```bash
# Delete collected static files
rm -Rf active_interview_backend/staticfiles

# In development, Django serves static files automatically
# Just restart the server
python manage.py runserver

# In production/Docker:
docker exec django python3 manage.py collectstatic --noinput
docker-compose restart
```

---

### Static Files 404 in Production

**Problem:** Static files work locally but not in Docker/production

**Solution:**

Check `settings.py` has WhiteNoise configured:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be here
    # ...
]
```

Rebuild containers:
```bash
docker-compose down
docker-compose up -d --build
```

---

## Testing Issues

### Tests Fail: ModuleNotFoundError

**Problem:** `ModuleNotFoundError` when running tests

**Solution:**
```bash
# Make sure you're in the correct directory
cd active_interview_backend

# Install test dependencies
pip install -r requirements.txt
```

---

### Coverage Shows 0%

**Problem:** Running coverage but shows 0% or very low

**Solution:**
```bash
# Make sure you're running coverage correctly
cd active_interview_backend
coverage run manage.py test  # NOT: coverage run --source='.'
coverage report -m

# Check .coveragerc exists and is configured
cat .coveragerc
```

---

### E2E Tests Fail (Chrome/Selenium)

**Problem:** `selenium.common.exceptions.WebDriverException`

**Solution:**

E2E tests require Chrome and Chromedriver.

**Option 1: Skip E2E tests locally**
```bash
# Run only unit tests
python manage.py test --exclude-tag=e2e
```

**Option 2: Run E2E in Docker**
```bash
# Docker has Chrome/Chromedriver pre-installed
docker-compose -f docker-compose.prod.yml up -d --build
docker exec django python3 manage.py test
```

**Option 3: Install Chrome locally**
```bash
# Install Chrome and Chromedriver matching your Chrome version
# https://chromedriver.chromium.org/downloads
```

---

### Coverage Below 80% (CI Fails)

**Problem:** CI pipeline fails with "Coverage below 80%"

**Solution:**

1. Run coverage locally:
```bash
cd active_interview_backend
coverage run manage.py test
coverage html
open htmlcov/index.html
```

2. Find red (uncovered) lines in the HTML report

3. Write tests for uncovered code paths:
   - Exception handlers
   - Edge cases
   - Conditional branches

4. Re-run coverage until ≥ 80%

---

## Git/CI/CD Issues

### CI Tests Pass Locally but Fail in GitHub Actions

**Problem:** Tests work on your machine but fail in CI

**Solution:**

Test in the exact CI environment:
```bash
# Run the production Docker setup locally
docker-compose -f docker-compose.prod.yml up -d --build
docker exec django python3 manage.py test
```

Common differences:
- Environment variables
- Database (SQLite vs PostgreSQL)
- Python version
- Dependency versions

---

### Railway Deployment Fails

**Problem:** Push succeeds but Railway deployment fails

**Solution:**

1. **Check Railway logs:**
   - Railway Dashboard → Your Service → Deployments → View logs

2. **Common issues:**
   - Missing environment variables (DJANGO_SECRET_KEY, OPENAI_API_KEY)
   - Database connection issues
   - Static files not collected

3. **Verify environment variables in Railway:**
   - Dashboard → Your Service → Variables
   - Ensure `PROD=true`, `DJANGO_SECRET_KEY`, `OPENAI_API_KEY` are set

4. **Check Railway secrets in GitHub:**
   - Settings → Secrets → Actions
   - Ensure `RAILWAY_TOKEN` and `RAILWAY_SERVICE_ID` exist

See [Railway Deployment Guide](../deployment/railway.md) for details.

---

## Development Environment Issues

### Code Changes Not Reflecting

**Problem:** You change code but don't see updates

**Solution:**

**Manual development:**
```bash
# Django auto-reloads, but if not working:
# Stop server (Ctrl+C) and restart
python manage.py runserver
```

**Docker development mode:**
```bash
# Should have volume mounts for live reloading
# Check docker-compose.yml has:
#   volumes:
#     - ./active_interview_backend:/app

# If using docker-compose.prod.yml, switch to dev mode:
docker-compose down
docker-compose up -d --build  # Uses docker-compose.yml (dev mode)
```

---

### Import Errors for Project Files

**Problem:** `ImportError: No module named 'active_interview_app'`

**Solution:**
```bash
# Make sure you're in the Django project directory
cd active_interview_backend

# Verify INSTALLED_APPS includes your app
# In settings.py:
INSTALLED_APPS = [
    # ...
    'active_interview_app',
]
```

---

## OpenAI Integration Issues

### OpenAI API Errors

**Problem:** `OpenAI API error: Rate limit exceeded` or `Invalid API key`

**Solution:**

**Rate limit:**
```bash
# Check your OpenAI usage/billing
# Visit: https://platform.openai.com/account/usage

# Implement rate limiting in code
# Or reduce test frequency
```

**Invalid key:**
```bash
# Regenerate key at https://platform.openai.com/api-keys
# Update environment variable
export OPENAI_API_KEY=sk-new-key...
```

**For tests:** Tests should mock OpenAI to avoid API calls:
```python
@patch('active_interview_app.views.get_openai_client')
def test_chat(self, mock_client):
    # Test without hitting real API
```

---

## Clean Restart (Last Resort)

### Everything Is Broken

**When:** You've tried everything and nothing works

**Solution:**

**Linux/Mac (Automated):**
```bash
# ⚠️ WARNING: Commits all code first, then wipes environment
sudo ./scripts/clean-restart.sh
```

**Manual Clean Restart:**
```bash
# 1. Commit your code (or you'll lose it!)
git add .
git commit -m "Save work before clean restart"

# 2. Stop and clean Docker
docker-compose down --volumes --remove-orphans
docker system prune --all --volumes
sudo systemctl restart docker  # Linux only

# 3. Clean git-tracked files (keeps .env and db/)
git clean -fdx -e .env -e active_interview_backend/db

# 4. Rebuild
docker-compose up -d --build
```

---

## Getting Help

If you're still stuck:

1. **Check existing issues:** [GitHub Issues](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues)
2. **Search the docs:** This documentation + README
3. **Check logs:**
   - Docker: `docker logs django`
   - Django: Check console output
   - CI: GitHub Actions logs
4. **Create an issue:** Include error messages, steps to reproduce, and environment details

---

## Next Steps

- **[Local Development Guide](local-development.md)** - Setup instructions
- **[Testing Guide](testing.md)** - Run tests and coverage
- **[CI/CD Documentation](../deployment/ci-cd.md)** - Pipeline details
