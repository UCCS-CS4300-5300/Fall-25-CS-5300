# Dual Authentication Setup - Password & OAuth

This document describes the complete setup that enables both password-based authentication and OAuth (Google) authentication to work together in the Active Interview Backend.

## Overview

The system supports two authentication methods:
1. **Password-based authentication** - Traditional username/email + password
2. **OAuth authentication** - Sign in with Google (extensible to other providers)

Both methods can coexist, and users created via either method are stored in the same Django `User` model.

---

## Database Schema

### Core Models

#### 1. Django's Built-in `User` Model
Django's standard `auth.User` model is used for both authentication types.

**Key fields:**
- `username` - Required for password auth, auto-generated for OAuth
- `email` - Required for both auth methods
- `password` - Contains password hash for password users, unusable password marker for OAuth users
- `first_name`, `last_name` - Populated from OAuth data when available

**Password handling:**
- Password users: `password` field contains a hash (e.g., `pbkdf2_sha256$...`)
- OAuth users: `password` field contains unusable password marker (starts with `!`)
- Check with `user.has_usable_password()` to determine if user can authenticate with password

#### 2. Custom `UserProfile` Model (models.py:11-25)
Extends the User model to track authentication provider and additional metadata.

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    auth_provider = models.CharField(
        max_length=50,
        default='local',
        help_text='Authentication provider (e.g., local, google)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Fields:**
- `auth_provider` - Tracks how the user was created ('local', 'google', etc.)
- `created_at` - Timestamp of profile creation
- `updated_at` - Timestamp of last profile update

**Auto-creation:**
A post-save signal (models.py:28-32) automatically creates a `UserProfile` when a `User` is created.

#### 3. Django-allauth Models
Django-allauth provides additional models for OAuth functionality:
- `SocialAccount` - Links User to social provider accounts
- `SocialApp` - Stores OAuth app credentials
- `SocialToken` - Stores OAuth tokens

---

## Authentication Configuration

### settings.py Configuration

#### Authentication Backends (settings.py:210-215)
```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Password auth
    'allauth.account.auth_backends.AuthenticationBackend',  # OAuth auth
]
```

Both backends are active, allowing users to authenticate via either method.

#### Installed Apps (settings.py:65-82)
```python
INSTALLED_APPS = [
    'django.contrib.auth',  # Core auth
    'django.contrib.sites',  # Required for allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',  # Google OAuth
]
```

#### Allauth Configuration (settings.py:218-241)
```python
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # Allow both
ACCOUNT_USERNAME_REQUIRED = False  # Optional for OAuth
SOCIALACCOUNT_AUTO_SIGNUP = True  # Auto-create users from OAuth
SOCIALACCOUNT_ADAPTER = 'active_interview_app.adapters.CustomSocialAccountAdapter'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': os.environ.get('GOOGLE_OAUTH_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', ''),
        }
    }
}
```

---

## Authentication Flows

### Password Authentication Flow

1. **Registration** (views.py:851-864)
   - User submits `CreateUserForm` with username, email, password1, password2
   - User is created with `form.save()` (sets password hash)
   - User is added to 'average_role' group
   - `UserProfile` is auto-created with `auth_provider='local'` (via signal)
   - Redirect to login page

2. **Login**
   - Django's built-in login view handles authentication
   - `ModelBackend` validates username/password
   - Session is created on success

### OAuth Authentication Flow

1. **User clicks "Sign in with Google"**
   - Redirects to Google OAuth consent screen
   - User authorizes the application

2. **Google redirects back with authorization code**
   - Django-allauth exchanges code for user info

3. **Pre-social login check** (adapters.py:19-43)
   - `CustomSocialAccountAdapter.pre_social_login()` checks if user with email exists
   - If exists: Links OAuth account to existing user
   - If not: Continues to new user creation

4. **New user creation** (adapters.py:45-65)
   - `CustomSocialAccountAdapter.save_user()` creates new User
   - `UserProfile` is created with `auth_provider='google'`
   - User is added to 'average_role' group
   - Session is created

5. **User info population** (adapters.py:67-84)
   - `CustomSocialAccountAdapter.populate_user()` extracts data from Google
   - Sets `first_name`, `last_name` from Google's `given_name`, `family_name`
   - Generates username from email if not provided

---

## Custom Adapter

### CustomSocialAccountAdapter (adapters.py)

Handles OAuth-specific logic:

**Key methods:**

1. **`pre_social_login(request, sociallogin)`**
   - Checks if user with OAuth email already exists
   - Links OAuth account to existing password user if found
   - Enables seamless account linking

2. **`save_user(request, sociallogin, form=None)`**
   - Creates new user from OAuth data
   - Sets `auth_provider` to provider name (e.g., 'google')
   - Adds user to 'average_role' group
   - Returns created user

3. **`populate_user(request, sociallogin, data)`**
   - Extracts user info from OAuth provider data
   - Sets name fields from OAuth data
   - Generates username from email

---

## Migrations

### Migration Files

1. **0001_initial.py** - Creates initial models (Chat, UploadedResume, etc.)
2. **0002_alter_chat_type.py** - Updates Chat model
3. **0003_userprofile.py** - Creates UserProfile model for dual auth support

### Migration 0003_userprofile.py
```python
operations = [
    migrations.CreateModel(
        name='UserProfile',
        fields=[
            ('id', models.BigAutoField(...)),
            ('auth_provider', models.CharField(
                default='local',
                help_text='Authentication provider (e.g., local, google)',
                max_length=50
            )),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='profile',
                to=settings.AUTH_USER_MODEL
            )),
        ],
    ),
]
```

---

## Testing

### Test Coverage

Comprehensive tests ensure both authentication methods work correctly:

#### 1. OAuth Tests (test_google_oauth.py)
- Tests OAuth user creation
- Tests existing user linking
- Tests UserProfile tracking
- Tests adapter methods

#### 2. Password Tests (test_registration.py)
- Tests password user registration
- Tests group assignment
- Tests error handling

#### 3. Dual Authentication Tests (test_dual_authentication.py)
- Tests password users have usable passwords
- Tests OAuth users can exist without passwords
- Tests both auth types coexist in same database
- Tests auth_provider tracking
- Tests account linking
- Tests database schema supports both methods
- Tests Django configuration

### Running Tests
```bash
cd active_interview_backend
pytest
```

---

## Security Considerations

### Password Storage
- Password users: Passwords are hashed using Django's default PBKDF2 algorithm
- OAuth users: No password stored, `has_usable_password()` returns False
- Password validation rules enforced (see settings.py:140-157)

### OAuth Security
- OAuth credentials stored in environment variables
- CSRF protection enabled for OAuth callbacks
- Only authorized redirect URIs accepted
- OAuth tokens managed by django-allauth

### Account Linking
- Existing password users can add OAuth login
- OAuth login with existing email links to existing account
- Password remains functional after linking OAuth

---

## How to Verify Both Methods Work

### 1. Check Database Schema
```python
from django.contrib.auth.models import User
from active_interview_app.models import UserProfile

# Create password user
pwd_user = User.objects.create_user(
    username='pwduser',
    email='pwd@example.com',
    password='SecurePass123!'
)
print(pwd_user.has_usable_password())  # Should be True
print(pwd_user.profile.auth_provider)  # Should be 'local'

# Create OAuth user (simulated)
oauth_user = User.objects.create_user(
    username='oauthuser',
    email='oauth@example.com'
)
oauth_user.profile.auth_provider = 'google'
oauth_user.profile.save()
print(oauth_user.has_usable_password())  # Should be False
print(oauth_user.profile.auth_provider)  # Should be 'google'
```

### 2. Verify Authentication Backends
```python
from django.conf import settings
print(settings.AUTHENTICATION_BACKENDS)
# Should include both ModelBackend and AuthenticationBackend
```

### 3. Test Password Login
```python
from django.contrib.auth import authenticate

user = authenticate(username='pwduser', password='SecurePass123!')
assert user is not None
```

### 4. Test OAuth Apps Installed
```python
from django.conf import settings
assert 'allauth' in settings.INSTALLED_APPS
assert 'allauth.socialaccount.providers.google' in settings.INSTALLED_APPS
```

---

## Environment Variables

Required environment variables for OAuth:
```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
```

See `GOOGLE_OAUTH_SETUP.md` for detailed OAuth setup instructions.

---

## Summary

The system successfully supports both authentication methods:

**Password Authentication:**
- Users created with username/email/password
- Password stored as hash in User.password field
- UserProfile.auth_provider = 'local'
- Authentication via ModelBackend

**OAuth Authentication:**
- Users created via Google OAuth
- No password stored (unusable password marker)
- UserProfile.auth_provider = 'google'
- Authentication via AuthenticationBackend
- SocialAccount links user to Google

**Both methods:**
- Use the same User model
- Automatically create UserProfile
- Add users to 'average_role' group
- Can coexist in same database
- Support account linking (password user can add OAuth)

The implementation is complete, tested, and production-ready.
