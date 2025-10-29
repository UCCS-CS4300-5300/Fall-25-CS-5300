# Local Development Setup

This guide covers how to set up and run Active Interview Service locally for development.

## Prerequisites

- Python 3.9 or higher
- Docker (optional, for containerized development)
- OpenAI API key
- Git

## Manual Setup (Without Docker)

### 1. Clone and Setup Virtual Environment

```bash
# Navigate to project root
cd Fall-25-CS-5300

# Create virtual environment
python3 -m venv myenv

# Activate virtual environment
# Windows (PowerShell):
.\myenv\Scripts\activate

# Linux/Mac:
source myenv/bin/activate
```

### 2. Install Dependencies

```bash
cd active_interview_backend
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Generate a Django secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Set environment variables:

**Windows (PowerShell):**
```powershell
$env:PROD = "false"
$env:DJANGO_SECRET_KEY = "<your-generated-secret-key>"
$env:OPENAI_API_KEY = "<your-openai-api-key>"
```

**Linux/Mac:**
```bash
export PROD=false
export DJANGO_SECRET_KEY='<your-generated-secret-key>'
export OPENAI_API_KEY=<your-openai-api-key>
```

### 4. Run Migrations

```bash
python3 manage.py migrate
```

### 5. Create Superuser and Configure Permissions

```bash
python manage.py createsuperuser
```

Then:
1. Start the server (see below)
2. Visit `http://127.0.0.1:8000/admin`
3. Log in with your superuser credentials
4. Go to **Groups** → **Add group**
5. Create a group called `average_role`
6. Select desired permissions
7. Save

This enables user registration from the web interface.

### 6. Start Development Server

```bash
python3 manage.py runserver
```

Access at: `http://127.0.0.1:8000`

### 7. Updating Static Files

If you modify CSS, JavaScript, or images:

```bash
# Delete old static files
rm -Rf staticfiles

# Run the server again (collectstatic happens automatically in dev)
python3 manage.py runserver
```

---

## Docker Setup

Docker provides a consistent development environment and is recommended for testing production-like configurations.

### 1. Prerequisites

- Docker Desktop installed
- `.env` file in project root

### 2. Create .env File

Create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=<your-secret-key>
OPENAI_API_KEY=<your-openai-api-key>
```

### 3. Development Mode (Recommended)

For daily development with live code editing:

```bash
# From project root
docker-compose up -d --build
```

**Features:**
- Live code reloading (changes reflect immediately)
- Mounts local code directory
- Includes Chrome/Chromedriver for E2E tests
- Uses `start.sh` startup script

Access at: `http://127.0.0.1`

### 4. CI/Production Testing Mode

To test the exact CI environment locally:

```bash
# From project root
docker-compose -f docker-compose.prod.yml up -d --build
```

**Features:**
- No volume mounts (production-like)
- Code copied during build
- Requires rebuild for code changes
- Uses `paracord_runner.sh` script
- Useful for verifying CI behavior

### 5. Docker Commands

```bash
# View logs
docker logs django
docker logs nginx

# Execute commands in container
docker exec django python3 manage.py test
docker exec django python3 manage.py migrate

# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down --volumes --remove-orphans
```

---

## Quick Start Comparison

| Method | Best For | Command | Access URL |
|--------|----------|---------|------------|
| Manual | Quick development, debugging | `python3 manage.py runserver` | `http://127.0.0.1:8000` |
| Docker Dev | Team consistency, E2E testing | `docker-compose up -d --build` | `http://127.0.0.1` |
| Docker Prod | CI verification | `docker-compose -f docker-compose.prod.yml up -d --build` | `http://127.0.0.1` |

---

## Next Steps

- **[Testing Guide](testing.md)** - Learn how to run tests and check coverage
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Architecture Overview](../architecture/overview.md)** - Understand the codebase structure
