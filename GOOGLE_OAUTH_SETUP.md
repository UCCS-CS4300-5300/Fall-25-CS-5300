# Google OAuth Setup Guide

This guide will walk you through setting up Google OAuth authentication for the Active Interview Service application.

## Overview

Users can now log in using their Google accounts. The system:
- Checks if a user with the Google email already exists
- If exists: Logs them in (creates session)
- If new: Creates a new user account with Google as the auth provider

## Prerequisites

- A Google account
- Access to Google Cloud Console
- Django application running locally or deployed

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "Active Interview Service")
5. Click "Create"

## Step 2: Enable Google+ API

1. In your Google Cloud Project, go to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click on it and click "Enable"
   - Note: You may also need to enable "Google People API" for profile information

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (unless you have a Google Workspace)
3. Click "Create"
4. Fill in the required information:
   - **App name**: Active Interview Service
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click "Save and Continue"
6. On the "Scopes" page, click "Add or Remove Scopes"
7. Add the following scopes:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
8. Click "Update" and then "Save and Continue"
9. Add test users if you're in testing mode
10. Click "Save and Continue" and then "Back to Dashboard"

## Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application" as the application type
4. Configure the OAuth client:
   - **Name**: Active Interview Service Web Client
   - **Authorized JavaScript origins**:
     - For local development: `http://localhost:8000`
     - For production: `https://app.activeinterviewservice.me`
   - **Authorized redirect URIs**:
     - For local development: `http://localhost:8000/accounts/google/login/callback/`
     - For production: `https://app.activeinterviewservice.me/accounts/google/login/callback/`
5. Click "Create"
6. **IMPORTANT**: Copy your Client ID and Client Secret - you'll need these for the next step

## Step 5: Configure Environment Variables

1. Copy the `.env.example` file to `.env` (if not already done):
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your Google OAuth credentials:
   ```bash
   GOOGLE_OAUTH_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
   ```

3. **IMPORTANT**: Never commit the `.env` file to version control

## Step 6: Run Database Migrations

The Google OAuth integration requires new database tables for django-allauth and the UserProfile model:

```bash
cd active_interview_backend
python manage.py makemigrations
python manage.py migrate
```

## Step 7: Configure Social Application in Django Admin

1. Create a superuser if you haven't already:
   ```bash
   python manage.py createsuperuser
   ```

2. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

3. Go to the Django admin panel: `http://localhost:8000/admin/`

4. Navigate to **Sites** and verify/update the existing site:
   - **Domain name**: `localhost:8000` (for development) or `app.activeinterviewservice.me` (for production)
   - **Display name**: Active Interview Service

5. Navigate to **Social applications** and click "Add social application"

6. Configure the social application:
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: Paste your Google OAuth Client ID
   - **Secret key**: Paste your Google OAuth Client Secret
   - **Sites**: Select your site from "Available sites" and move it to "Chosen sites"

7. Click "Save"

## Step 8: Test the OAuth Flow

1. Log out if you're currently logged in
2. Go to the login page: `http://localhost:8000/accounts/login/`
3. Click the "Sign in with Google" button
4. You should be redirected to Google's sign-in page
5. Select your Google account
6. Grant the requested permissions
7. You should be redirected back to your application and logged in

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

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Solution**: Make sure the redirect URI in your Google Cloud Console exactly matches the one being used by your application:
- Format: `http://localhost:8000/accounts/google/login/callback/`
- Include the trailing slash
- Use `https://` for production
- Ensure the redirect URI in Google Console exactly matches
- Check that the Site domain in Django admin matches your current domain

### Error: "The project does not have access to this API"

**Solution**: Make sure you've enabled the Google+ API (or Google People API) in your Google Cloud Console.

### Error: "Social application matching query does not exist"

**Solution**: Make sure you've configured the Social Application in Django Admin (Step 7).

### "No module named 'allauth'" error

**Solution**: Install dependencies: `pip install -r requirements.txt`

### Social application not showing in admin

**Solution**:
- Run migrations: `python manage.py migrate`
- Ensure `django.contrib.sites` is in INSTALLED_APPS

### Users not being added to group

**Solution**:
- Ensure the `average_role` group exists in Django admin
- Check the adapter code in `adapters.py`

### OAuth works locally but not in production

**Solution**:
1. Verify your production domain is added to "Authorized JavaScript origins" and "Authorized redirect URIs"
2. Make sure the Site domain in Django admin matches your production domain
3. Verify your production `.env` file has the correct Google OAuth credentials
4. Ensure HTTPS is being used (required by Google for production)

## Security Best Practices

1. **Never commit credentials**: Keep your `.env` file in `.gitignore`
2. **Use HTTPS in production**: Google OAuth requires HTTPS for production environments
3. **Rotate secrets regularly**: Consider rotating your OAuth client secret periodically
4. **Limit scopes**: Only request the minimum scopes needed (email and profile)
5. **Monitor usage**: Regularly check your Google Cloud Console for unusual activity
6. Use strong, unique Client Secrets
7. Only add trusted redirect URIs

## Production Deployment Checklist

- [ ] OAuth credentials configured in production environment variables
- [ ] Authorized redirect URIs updated with production domain
- [ ] Site domain updated in Django admin
- [ ] HTTPS enabled and working
- [ ] CSRF and security middleware properly configured
- [ ] OAuth consent screen published (move from testing to production)
- [ ] Test OAuth flow in production environment
- [ ] Ensure environment variables are set on your hosting platform (Railway, etc.)
- [ ] Update the Site domain in Django admin to your production domain
- [ ] Add production redirect URIs to Google OAuth credentials
- [ ] Run migrations on production database

## Additional Configuration for Railway/Production

If deploying to Railway or another platform:

1. Add environment variables in your platform's dashboard:
   - `GOOGLE_OAUTH_CLIENT_ID`
   - `GOOGLE_OAUTH_CLIENT_SECRET`

2. Update authorized redirect URIs to include your Railway domain:
   - `https://your-app.up.railway.app/accounts/google/login/callback/`

3. Update the Site object in Django admin to match your production domain

## Support

For issues related to:
- **Google OAuth setup**: Check [Google OAuth documentation](https://developers.google.com/identity/protocols/oauth2)
- **django-allauth**: Check [django-allauth documentation](https://django-allauth.readthedocs.io/)
- **Application-specific issues**: Create an issue in the project repository

## References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google Cloud Console](https://console.cloud.google.com/)
