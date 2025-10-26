# Google OAuth Setup Guide

This guide explains how to configure Google OAuth authentication for the Active Interview Service.

## Overview

Users can now log in using their Google accounts. The system:
- Checks if a user with the Google email already exists
- If exists: Logs them in (creates session)
- If new: Creates a new user account with Google as the auth provider

## Setup Instructions

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Select **Web application**
6. Configure:
   - **Name**: Active Interview Service (or your preferred name)
   - **Authorized JavaScript origins**:
     - `http://localhost:8000` (for local development)
     - `https://app.activeinterviewservice.me` (for production)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/accounts/google/login/callback/`
     - `https://app.activeinterviewservice.me/accounts/google/login/callback/`
7. Click **Create**
8. Copy the **Client ID** and **Client Secret**

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
```

### 3. Run Migrations

Create and apply the database migrations for the new UserProfile model:

```bash
cd active_interview_backend
python manage.py makemigrations
python manage.py migrate
```

### 4. Configure Site in Django Admin

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Go to `http://localhost:8000/admin/`

3. Navigate to **Sites** and edit the existing site:
   - **Domain name**: `localhost:8000` (for development) or `app.activeinterviewservice.me` (for production)
   - **Display name**: Active Interview Service

4. Navigate to **Social applications** and add a new application:
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: (paste your Client ID)
   - **Secret key**: (paste your Client Secret)
   - **Sites**: Select your site and move it to "Chosen sites"
   - Click **Save**

## How It Works

### User Flow

1. User visits login page
2. Clicks "Sign in with Google"
3. Redirected to Google OAuth consent screen
4. Grants permission
5. Redirected back to application
6. System checks if user exists:
   - **Existing user**: Session created, user logged in
   - **New user**:
     - User account created
     - UserProfile created with `auth_provider='google'`
     - User added to `average_role` group
     - Session created, user logged in

### Database Schema

**UserProfile Model**:
- `user`: OneToOne relationship with Django User
- `auth_provider`: String field (values: 'local', 'google')
- `created_at`: Timestamp when profile was created
- `updated_at`: Timestamp when profile was last updated

### Custom Adapter

The `CustomSocialAccountAdapter` in `active_interview_app/adapters.py`:
- Checks for existing users by email
- Creates user profiles with correct auth provider
- Adds users to the default group
- Populates user data from Google (name, email)

## Testing

Run the Google OAuth tests:

```bash
cd active_interview_backend
pytest active_interview_app/tests/test_google_oauth.py -v
```

## Acceptance Criteria ✓

- ✅ Check database for existing user with Google email
- ✅ Existing user → session created
- ✅ New user → record created with default profile data
- ✅ User added to `average_role` group
- ✅ Auth provider tracked in UserProfile

## Production Deployment

For production deployment:

1. Ensure environment variables are set on your hosting platform (Railway, etc.)
2. Update the Site domain in Django admin to your production domain
3. Add production redirect URIs to Google OAuth credentials
4. Run migrations on production database
5. Test the OAuth flow on production

## Troubleshooting

### "Redirect URI mismatch" error
- Ensure the redirect URI in Google Console exactly matches: `http://localhost:8000/accounts/google/login/callback/`
- Check that the Site domain in Django admin matches your current domain

### "No module named 'allauth'" error
- Install dependencies: `pip install -r requirements.txt`

### Social application not showing in admin
- Run migrations: `python manage.py migrate`
- Ensure `django.contrib.sites` is in INSTALLED_APPS

### Users not being added to group
- Ensure the `average_role` group exists in Django admin
- Check the adapter code in `adapters.py`

## Security Notes

- **Never commit** `.env` files or credentials to Git
- Use strong, unique Client Secrets
- Regularly rotate OAuth credentials
- Only add trusted redirect URIs
- Use HTTPS in production
