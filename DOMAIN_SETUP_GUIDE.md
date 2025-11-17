# Custom Domain Setup Guide: activeinterviewservice.app

This guide walks you through setting up your custom domain `activeinterviewservice.app` with Railway and Django.

## Overview

You'll be configuring:
- **Domain:** activeinterviewservice.app (from name.com)
- **Hosting:** Railway
- **Framework:** Django

---

## Step 1: Configure DNS at name.com ⚙️

### 1.1 Log into name.com
1. Go to https://www.name.com
2. Sign in with your account
3. Navigate to "My Domains" and select `activeinterviewservice.app`

### 1.2 Get Railway's Custom Domain Settings First
**IMPORTANT:** Do Step 2 (Railway Configuration) FIRST to get the CNAME target, then come back here!

### 1.3 Add DNS Records

Once you have Railway's CNAME target from Step 2, add these DNS records:

#### Option A: Root Domain Only (Recommended to start)
```
Type: CNAME
Host: @
Answer: <your-railway-domain>.railway.app
TTL: 300 (5 minutes)
```

#### Option B: Root + www (Better for production)
```
Record 1:
Type: CNAME
Host: @
Answer: <your-railway-domain>.railway.app
TTL: 300

Record 2:
Type: CNAME
Host: www
Answer: <your-railway-domain>.railway.app
TTL: 300
```

**Note:** Some registrars don't allow CNAME records for root domains (@). If name.com gives you trouble:
- Use ANAME or ALIAS record type if available
- Or point `www` to Railway and redirect `@` to `www`

### 1.4 Verify DNS Propagation
After adding DNS records, check propagation (can take 5-60 minutes):
```bash
# Windows Command Prompt
nslookup activeinterviewservice.app

# Should show Railway's IP address
```

Online tool: https://dnschecker.org

---

## Step 2: Configure Railway 🚂

### 2.1 Access Your Railway Project
1. Go to https://railway.app
2. Select your Active Interview project
3. Click on your Django service

### 2.2 Add Custom Domain
1. Go to the **Settings** tab
2. Scroll to **Networking** section
3. Under **Custom Domains**, click **+ Add Domain**
4. Enter: `activeinterviewservice.app`
5. (Optional) Also add: `www.activeinterviewservice.app`
6. Click **Add**

### 2.3 Get CNAME Target
Railway will show you a CNAME target like:
```
<your-service>.railway.app
```
**Copy this value** - you'll need it for name.com DNS setup (Step 1.3)

### 2.4 Verify SSL Certificate
- Railway automatically provisions SSL certificates via Let's Encrypt
- This can take 5-30 minutes after DNS propagates
- You'll see a green checkmark when it's ready
- Status will change from "Waiting for DNS" → "Active"

### 2.5 Update Environment Variables (Optional)
If you're using `SITE_URL` in your Railway environment variables:
1. Go to **Variables** tab
2. Update or add: `SITE_URL=https://activeinterviewservice.app`

---

## Step 3: Update Google OAuth (if using Google Sign-In) 🔑

### 3.1 Update Google Cloud Console
1. Go to https://console.cloud.google.com
2. Select your project
3. Navigate to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Under **Authorized JavaScript origins**, add:
   ```
   https://activeinterviewservice.app
   https://www.activeinterviewservice.app
   ```
6. Under **Authorized redirect URIs**, add:
   ```
   https://activeinterviewservice.app/accounts/google/login/callback/
   https://www.activeinterviewservice.app/accounts/google/login/callback/
   ```
7. Click **Save**

### 3.2 Update Django Allauth Site
In Django admin (https://activeinterviewservice.app/admin):
1. Go to **Sites** → Click on your site
2. Update **Domain name** to: `activeinterviewservice.app`
3. Update **Display name** to: `Active Interview Service`
4. Click **Save**

Or via Django shell:
```python
python manage.py shell

from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'activeinterviewservice.app'
site.name = 'Active Interview Service'
site.save()
```

---

## Step 4: Test Your Setup ✅

### 4.1 Basic Connectivity
1. Open browser (incognito mode recommended)
2. Navigate to: `https://activeinterviewservice.app`
3. Verify:
   - ✅ Site loads correctly
   - ✅ HTTPS works (green padlock in browser)
   - ✅ No certificate warnings

### 4.2 Test Features
- ✅ Login/Register works
- ✅ Google OAuth works (if enabled)
- ✅ Static files load (CSS, JS)
- ✅ Create a test chat/interview
- ✅ Email invitations have correct URLs

### 4.3 Test www Redirect (if configured)
Navigate to: `https://www.activeinterviewservice.app`
Should work or redirect to root domain

---

## Step 5: Transition from Old Domain (Optional)

If you want to keep the old domain working during transition:

### Keep Both Domains Active
The Django settings have been updated to accept both:
- `activeinterviewservice.app` (new)
- `app.activeinterviewservice.me` (old)

### Set Up Redirects (Recommended)
To redirect old domain to new:

#### Option A: Railway Redirects
In Railway, you can add a redirect rule (check Railway docs for current method)

#### Option B: Django Middleware
Create middleware to redirect old domain to new:

```python
# active_interview_app/middleware.py
from django.http import HttpResponsePermanentRedirect

class DomainRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host == 'app.activeinterviewservice.me':
            new_url = request.build_absolute_uri().replace(
                'app.activeinterviewservice.me',
                'activeinterviewservice.app'
            )
            return HttpResponsePermanentRedirect(new_url)
        return self.get_response(request)
```

Add to settings.py MIDDLEWARE:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'active_interview_app.middleware.DomainRedirectMiddleware',  # Add this
    # ... rest of middleware
]
```

---

## Troubleshooting 🔧

### DNS Not Resolving
**Problem:** `activeinterviewservice.app` doesn't load
**Solutions:**
1. Wait longer (DNS can take up to 24 hours, usually 5-60 min)
2. Check DNS propagation: https://dnschecker.org
3. Clear your DNS cache:
   ```bash
   # Windows
   ipconfig /flushdns

   # Mac
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   ```
4. Try different browser/device

### HTTPS Certificate Issues
**Problem:** "Not Secure" warning or certificate error
**Solutions:**
1. Wait for Railway to provision certificate (up to 30 min)
2. Check Railway dashboard for certificate status
3. Ensure DNS is fully propagated first
4. Check Railway logs for errors

### CSRF Verification Failed
**Problem:** `CSRF verification failed. Request aborted.`
**Solutions:**
1. Verify domain is in `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
2. Clear browser cookies
3. Ensure `SECURE_PROXY_SSL_HEADER` is set correctly
4. Check Railway logs for actual hostname being sent

### Static Files Not Loading
**Problem:** CSS/JS not loading, site looks broken
**Solutions:**
1. Check `ALLOWED_HOSTS` includes your domain
2. Verify static files are collected: `python manage.py collectstatic`
3. Check Railway deployment logs
4. Ensure WhiteNoise is configured correctly

### Google OAuth Not Working
**Problem:** OAuth callback fails
**Solutions:**
1. Verify redirect URIs in Google Cloud Console
2. Update Django Site domain in admin
3. Check `ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'` in settings
4. Clear browser cookies and try again

### Railway Domain Shows "Waiting for DNS"
**Problem:** Custom domain stuck in waiting state
**Solutions:**
1. Double-check DNS records at name.com
2. Ensure CNAME points to correct Railway domain
3. Wait longer (can take up to 1 hour)
4. Remove and re-add the domain in Railway
5. Contact Railway support if stuck > 24 hours

---

## Email Configuration Note 📧

With the new domain, you might want to set up proper email sending:

### Option 1: Gmail SMTP (Simple, for testing)
Already configured in settings.py, just set environment variables:
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@activeinterviewservice.app
```

**Note:** Gmail will still send from your Gmail address, the FROM header will just show the .app domain

### Option 2: Professional Email Service (Recommended for production)
Consider:
- **SendGrid** (free tier: 100 emails/day)
- **Mailgun** (free tier: 1000 emails/month)
- **Amazon SES** (very cheap, complex setup)
- **Postmark** (great deliverability, paid)

---

## Quick Reference Card 📋

```
Domain:           activeinterviewservice.app
Registrar:        name.com
Hosting:          Railway
Production URL:   https://activeinterviewservice.app
Old URL:          https://app.activeinterviewservice.me (transitional)

DNS Records:
  Type: CNAME
  Host: @
  Value: <your-service>.railway.app

Django Settings Updated:
  ✅ ALLOWED_HOSTS
  ✅ CSRF_TRUSTED_ORIGINS
  ✅ SITE_URL
  ✅ DEFAULT_FROM_EMAIL
```

---

## Next Steps After Setup ✨

1. **Test thoroughly** - Go through all features
2. **Update documentation** - Any README files with URLs
3. **Notify users** - If you have existing users
4. **Monitor logs** - Watch for any domain-related errors
5. **Update Google OAuth** - Test social login
6. **Update any API integrations** - That reference the old domain
7. **Set up monitoring** - Consider uptime monitoring (UptimeRobot, etc.)
8. **Remove old domain** - After confirming everything works (wait 1-2 weeks)

---

## Common Railway Commands

```bash
# View logs
railway logs

# Redeploy
railway up

# Set environment variable
railway variables set SITE_URL=https://activeinterviewservice.app

# Get current variables
railway variables
```

---

## Support Resources

- **Railway Docs:** https://docs.railway.app/guides/public-networking
- **Django Sites Framework:** https://docs.djangoproject.com/en/4.2/ref/contrib/sites/
- **Name.com Support:** https://www.name.com/support
- **DNS Checker:** https://dnschecker.org
- **SSL Checker:** https://www.sslshopper.com/ssl-checker.html

---

## Completed Tasks Checklist

Use this to track your progress:

- [ ] Django settings updated (DONE - committed in code)
- [ ] DNS records added at name.com
- [ ] Custom domain added in Railway
- [ ] DNS propagation verified
- [ ] SSL certificate active
- [ ] Site loads at https://activeinterviewservice.app
- [ ] Google OAuth updated (if applicable)
- [ ] Django Sites updated
- [ ] Static files loading correctly
- [ ] All features tested
- [ ] Email links use new domain
- [ ] Documentation updated
- [ ] Old domain redirect configured (optional)
- [ ] Monitoring set up (optional)

---

**Good luck with your domain setup! The Django code is already updated and ready to go. Now just follow the Railway and name.com steps above.**
