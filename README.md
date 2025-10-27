# Group-7-Spring-2025
## Setup, Startup and Accessing
### Local Manual 
#### Setup
1. Navigate to the root of the project.
2. Make a venv: `python3 -m venv myenv`
3. Load the venv
   - Windows(Powershell): `.\myenv\bin\activate`
   - Linux/Mac: `source myenv/bin/activate`
5. Navigate to the active_interview_backend/ folder
6. Install the requirements: `pip install -r requirements.txt`
7. Generate a secret django key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
8. Run a django migration: `python3 manage.py migrate`
9. Export these environment variables to your local machine
   - Windows(Powershell)
      - `$env:PROD = "false"`
      - `$env:DJANGO_SECRET_KEY = "<your secret key>"`
      - `$env:OPENAI_API_KEY = "<your api key>"`
   - Linux/Mac
      - `export PROD=false`
      - `export DANGO_SECRET_KEY='<your secret key>'` (make sure to surround the key itself in apostraphes)
      - `export OPENAI_API_KEY=<your api key>`

#### Startup
1. Navigate to the root of the project.
2. <ins>(if you recently ran the clean-startup script)</ins> Repeat the manual setup steps 2-5 to set up the venv after it was erased
3. Load the venv
   - Windows(Powershell): `.\myenv\bin\activate`
   - Linux/Mac: `source myenv/bin/activate`
4. Navigate to the active_interview_backend/ folder
5. <ins>(if you changed a static file like **CSS** or **images**)</ins> Delete the folder active_interview_backend/staticfiles/: `rm -Rf staticfiles`
6. Run the server manually: `python3 manage.py runserver`


#### Registering Accounts
In order to allow people to register accounts from the page, permission levels must be set.
1. Activate your virtual environement
2. use the command 'python manage.py createsuperuser' to create an admin
3. launch the django project
4. Access through the means of the wep page or any other access point into the admin site 'http://127.0.0.1:8000/admin'
5. Go to groups
6. Add group called average_role and select permission levels
7. save the group
Now you should be able to register accounts on the page.



#### Accessing
`http://127.0.0.1:8000`

### Local Docker-Compose
#### Setup
1. Navigate to the root of the project.
2. Make a venv: `python3 -m venv myenv`
3. Load the venv: `source myenv/bin/activate`
4. Install the requirements: `pip install -r active_interview_backend/requirements.txt`
5. Generate a secret django key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
6. Make an OpenAI API key.
6. Edit open a `.env` file in the root of your project and fill it out like so:
```
DJANGO_SECRET_KEY=<your secret key>
OPENAI_API_KEY=<your api key>
```

#### Startup - Development Mode (default)
For local development with live code editing and full testing capabilities:
1. Navigate to the root of the project.
2. Run `docker-compose up -d --build`
   - Uses `docker-compose.yml`
   - Mounts local code directory for live editing
   - Runs `start.sh` script
   - Includes Chrome/Chromedriver for running E2E tests locally
   - Code changes reflect immediately without rebuilding

#### Startup - CI/Production Testing Mode
To test the exact CI environment locally (without volume mounts):
1. Navigate to the root of the project.
2. Run `docker-compose -f docker-compose.prod.yml up -d --build`
   - Uses `docker-compose.prod.yml`
   - No volume mounts (production-like environment)
   - Runs `paracord_runner.sh` script
   - Includes Chrome/Chromedriver for E2E tests
   - Requires full rebuild to see code changes
   - Useful for verifying behavior matches CI exactly

#### Key Differences

| Feature | Development (`docker-compose.yml`) | CI/Production Testing (`docker-compose.prod.yml`) |
|---------|-------------------------------------|---------------------------------------------------|
| Volume Mount | ✅ Local code mounted | ❌ Code copied during build |
| Live Editing | ✅ Changes reflect immediately | ❌ Requires rebuild |
| Startup Script | `start.sh` | `paracord_runner.sh` |
| Chrome/Testing | ✅ Pre-installed | ✅ Pre-installed |
| Use Case | Day-to-day development + testing | Verify CI environment locally |

#### Accessing
`http://127.0.0.1`

## Debugging
### Network Issues
#### Arch Linux(And Derivatives)
Please follow [the last post on this forum thread](https://bbs.archlinux.org/viewtopic.php?pid=2025168#p2025168) to fix your local docker's networking issues.

## Cleaning
Every once in a while, your local environment may break because of a refactor, but the code works just fine in production.  Here is a way to clean your local environment on linux/mac:
1. Navigate to the root of the project.
2. `docker-compose down --volumes --remove-orphans`
3. `docker system prune --all --volumes`
4. `sudo systemctl restart docker`
5. `git clean -fdx -e .env -e active_interview_backend/db`

## Restarting Cleanly
I have created an linux/mac script that should make cleanly restarting local deployments in a way that avoids bugs much easier.  If you run windows, look at scripts/clean-restart.sh and do the equivalent commands for windows.
> [!CAUTION]
> Make sure to commit your code before using this.  The script can and will wipe all non-committed code, so you will lose work if you forget.
1. Navigate to the root of the project.
2. `sudo ./scripts/clean-restart.sh`

## CI/CD Pipeline

The project uses separate Continuous Integration (CI) and Continuous Deployment (CD) workflows to ensure code quality and automated deployments.

### Workflow: `CI.yml` (Continuous Integration)

Runs on push to `main` branch, pull requests to `main`, or manual dispatch (`workflow_dispatch`).

**Jobs:**

1. **Lint** - Code quality checks
   - Python linting with `flake8`
   - Django template linting with `djlint`
   - Outputs results to GitHub Step Summary

2. **Security** - Security scanning (depends on Lint)
   - Dependency vulnerability scanning with `safety`
   - Static code analysis with `bandit`
   - Generates JSON reports and uploads as artifacts
   - Retention: 14 days

3. **Test** - Runs Django tests with coverage validation (depends on Security)
   - Spins up Docker containers with `docker-compose.prod.yml`
   - Installs Chrome (v135.0.7049.52-1) and Chromedriver for Selenium tests
   - Runs Django test suite with coverage tracking
   - Enforces minimum 80% code coverage requirement
   - Uploads coverage reports as artifacts
   - Cleans up Docker resources after completion

4. **AI Review** - Automated code review using OpenAI (runs in parallel)
   - Analyzes git diffs for pushes and pull requests
   - Generates AI-powered code review feedback
   - Uploads review reports as artifacts
   - Adds review summary to GitHub Step Summary

5. **Cleanup** - Archive and cleanup (runs after all jobs complete)
   - Downloads all artifacts from previous jobs
   - Creates compressed archive of essential files (coverage, security, AI review)
   - Uploads consolidated archive with 30-day retention
   - Generates cleanup summary

**Environment Variables:**
- `PYTHON_VERSION`: 3.13
- `CHROME_VERSION`: 135.0.7049.52-1
- `CHROMEDRIVER_VERSION`: 135.0.7049.52
- `RETENTION_DAYS`: 14

### Workflow: `CD.yml` (Continuous Deployment)

Runs on push to `prod` or `main` branches, or manual dispatch (`workflow_dispatch`).

**Jobs:**

1. **Deploy** - Deploys to Railway
   - Checks out code
   - Installs Railway CLI via npm
   - Deploys using Railway service
   - Generates deployment summary with status, branch, commit, and timestamp

**Deployment Details:**
- Target: Railway platform
- Triggers: Push to `prod` or `main` branches, or manual trigger
- Method: Railway CLI (`railway up`)

### Required Secrets

**For CI Pipeline:**
- `DJANGO_SECRET_KEY` - Django secret key for testing environment
- `OPENAI_API_KEY` - OpenAI API key for AI code reviews

**For CD Pipeline:**
- `RAILWAY_TOKEN` - Railway authentication token
- `RAILWAY_SERVICE_ID` - Railway service identifier for deployment

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
