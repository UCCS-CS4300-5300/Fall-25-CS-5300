# Railway Deployment Setup Guide

This guide explains how to set up automated Railway deployment via GitHub Actions.

## Prerequisites

- Railway project created and connected to your GitHub repository
- Someone with repo access can add GitHub secrets
- Railway admin access to get tokens and service IDs

## Setup Steps

### 1. Get Railway Token

1. Go to Railway Project Setting -> Tokens
2. Click "Create Token"
3. Copy the token (you won't see it again!)
4. Store it securely

### 2. Get Railway Service ID

1. Go to your Railway project
2. Click on your Django service
3. Go to Settings tab
4. Find "Service ID" (looks like: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
5. Copy it

### 3. Add GitHub Secrets

Ask someone with GitHub repo admin access to add these secrets:

Go to: Repository → Settings → Secrets and variables → Actions → New repository secret

Add:
- **Name**: `RAILWAY_TOKEN`
  **Value**: (paste the token from step 1)

- **Name**: `RAILWAY_SERVICE_ID`
  **Value**: (paste the service ID from step 2)

### 4. Configure Railway Environment Variables

In Railway dashboard → Your Service → Variables tab, add:

```
DJANGO_SECRET_KEY=<your-secret-key>
OPENAI_API_KEY=<your-openai-api-key>
PROD=true
```

Railway automatically provides:
- `DATABASE_URL` (PostgreSQL connection string)
- `PORT` (port your app should listen on)

### 5. Test Deployment

**Option A: Push to main/prod branch**
```bash
git push origin main
# or
git push origin prod
```

**Option B: Manual trigger**
1. Go to Actions tab on GitHub
2. Select "Continuous Deployment" workflow
3. Click "Run workflow"
4. Select branch and click "Run workflow"

## How It Works

### Automatic Deployment
The CD workflow (`.github/workflows/CD.yml`) runs when:
- Code is pushed to `main` or `prod` branch
- Someone manually triggers it via GitHub Actions UI

### Deployment Process
1. Checkout code from GitHub
2. Install Railway CLI
3. Authenticate with `RAILWAY_TOKEN`
4. Deploy to service specified by `RAILWAY_SERVICE_ID`
5. Show deployment status in GitHub Actions summary

### Alternative: Railway's Built-in GitHub Integration

If you prefer Railway's native GitHub integration instead of using GitHub Actions:

1. **Disable CD.yml**: Rename `.github/workflows/CD.yml` to `.github/workflows/CD.yml.disabled`
2. **Enable Railway GitHub Integration**:
   - Go to Railway dashboard → Your Service → Settings
   - Under "Source", connect your GitHub repository
   - Select branch to deploy from (e.g., `main` or `prod`)
   - Railway will auto-deploy on every push

**Pros of Railway's Native Integration:**
- Simpler setup (no tokens/secrets needed)
- Automatic PR preview environments
- Build logs directly in Railway

**Pros of GitHub Actions CD:**
- Full control over deployment workflow
- Can add pre-deployment checks (wait for CI, run migrations, etc.)
- Deployment status visible in GitHub Actions
- Can deploy to multiple environments in sequence

## Troubleshooting

### Error: "Railway token not found"
- Make sure `RAILWAY_TOKEN` secret is added to GitHub
- Token must be valid and not expired

### Error: "Service not found"
- Check `RAILWAY_SERVICE_ID` is correct
- Ensure the service exists in your Railway project

### Error: "Authentication failed"
- Regenerate Railway token and update GitHub secret
- Ensure token has correct permissions

### Deployment succeeds but app doesn't work
- Check Railway logs: Dashboard → Your Service → Deployments → View logs
- Verify environment variables are set correctly
- Check that `start.sh` or Gunicorn command is working
- Ensure static files are collected (WhiteNoise should handle this)

## Environment Variables Reference

Required in Railway:
- `DJANGO_SECRET_KEY` - Django secret key
- `OPENAI_API_KEY` - OpenAI API key
- `PROD=true` - Enables production mode

Auto-provided by Railway:
- `DATABASE_URL` - PostgreSQL connection (parsed by dj-database-url)
- `PORT` - Port to bind (Gunicorn uses this automatically)

## Useful Commands

### Railway CLI (for local testing)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy manually
railway up

# View logs
railway logs

# Run commands in Railway environment
railway run python manage.py migrate
```

## Support

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- GitHub Actions Docs: https://docs.github.com/actions
