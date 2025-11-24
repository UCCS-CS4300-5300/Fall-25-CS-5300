# Bandit Security Issues Quick Reference

Quick reference for common Bandit findings and how to fix them.

## Django-Specific Issues

### B201: Flask Debug Mode (False Positive for Django)

**Issue:** Bandit detects `DEBUG = True` thinking it's Flask
**Django Context:** This is Django's DEBUG setting

**Fix:** Skip this check in `.bandit` if you're not using Flask
```ini
[bandit]
skips = ['B201']
```

### B308: Mark Safe Usage

**Finding:** `mark_safe()` can introduce XSS vulnerabilities

**Bad:**
```python
from django.utils.safestring import mark_safe

html = mark_safe(user_input)  # ❌ XSS risk!
```

**Good:**
```python
from django.utils.html import escape

html = escape(user_input)  # ✅ Escaped
# Or use template auto-escaping
```

**When to use mark_safe:**
- Only with trusted, sanitized input
- After using bleach or similar sanitizer
- For hardcoded HTML templates

### B703: Django Extra() Method

**Finding:** `.extra()` can cause SQL injection

**Bad:**
```python
User.objects.extra(where=[f"name='{user_input}'"])  # ❌ SQL injection!
```

**Good:**
```python
User.objects.filter(name=user_input)  # ✅ Parameterized
# Or use raw with parameters
User.objects.raw("SELECT * FROM users WHERE name = %s", [user_input])
```

### B308: Django Raw SQL

**Finding:** Raw SQL queries need parameterization

**Bad:**
```python
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # ❌ SQL injection!
```

**Good:**
```python
cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])  # ✅ Parameterized
```

## Secret Detection

### B105: Hardcoded Password String

**Finding:** Password strings in code

**Bad:**
```python
password = "admin123"  # ❌ Hardcoded secret
```

**Good:**
```python
import os
password = os.environ.get('PASSWORD')  # ✅ Environment variable

# Or use Django settings
from django.conf import settings
password = settings.SECRET_PASSWORD
```

### B106: Hardcoded Password Argument

**Finding:** Password in function call

**Bad:**
```python
connect(user="admin", password="secret123")  # ❌ Hardcoded
```

**Good:**
```python
import os
connect(
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD')
)  # ✅ From environment
```

### B107: Hardcoded Password Default

**Finding:** Default password in function definition

**Bad:**
```python
def connect(password="default123"):  # ❌ Default password
    pass
```

**Good:**
```python
def connect(password=None):  # ✅ No default
    if password is None:
        password = os.environ.get('PASSWORD')
    # or raise error if not provided
```

## Command Injection

### B602: Shell Injection via Popen

**Finding:** `subprocess.Popen` with `shell=True`

**Bad:**
```python
import subprocess
subprocess.Popen(f"ls {user_input}", shell=True)  # ❌ Command injection!
```

**Good:**
```python
import subprocess
subprocess.Popen(["ls", user_input])  # ✅ List form, no shell
# Or use shlex.quote() if shell is required
import shlex
subprocess.Popen(f"ls {shlex.quote(user_input)}", shell=True)
```

### B603: Subprocess Without Shell

**Finding:** `subprocess` call needs review

**Status:** Usually safe if using list form

**Good Pattern:**
```python
import subprocess

# ✅ Safe: List form
subprocess.run(["git", "status"], check=True)

# ✅ Safe: Quoted user input
import shlex
cmd = f"git log --author={shlex.quote(author)}"
subprocess.run(cmd, shell=True, check=True)
```

### B605: Start Process With Shell

**Finding:** Starting process with `shell=True`

**Same as B602** - use list form or quote inputs

### B607: Start Process With Partial Path

**Finding:** Executable not using full path

**Risk:** Path manipulation attack

**Bad:**
```python
subprocess.run(["python", "script.py"])  # ❌ Which python?
```

**Good:**
```python
import sys
subprocess.run([sys.executable, "script.py"])  # ✅ Explicit python

# Or use full paths
subprocess.run(["/usr/bin/git", "status"])
```

## Cryptography

### B303: MD5 or SHA1 Hash

**Finding:** Weak hash functions

**Bad:**
```python
import hashlib
hashlib.md5(data)  # ❌ Weak hash
hashlib.sha1(data)  # ❌ Weak hash
```

**Good:**
```python
import hashlib

# ✅ For cryptographic purposes
hashlib.sha256(data)
hashlib.sha512(data)

# For passwords specifically, use Django's built-in
from django.contrib.auth.hashers import make_password
hashed = make_password(password)
```

**Exception:** MD5 for non-security purposes
```python
# File checksums (not security-critical)
# Add comment to explain non-security use
checksum = hashlib.md5(file_content).hexdigest()  # nosec B303
```

### B324: Insecure Hash Function

**Finding:** Using insecure hashing mode

**Bad:**
```python
hashlib.new('md5', data)  # ❌ Weak
```

**Good:**
```python
hashlib.new('sha256', data)  # ✅ Strong
```

### B304: Insecure Cipher

**Finding:** Using weak cipher modes

**Bad:**
```python
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_ECB)  # ❌ ECB mode is insecure
```

**Good:**
```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

key = get_random_bytes(16)
cipher = AES.new(key, AES.MODE_GCM)  # ✅ GCM mode
```

### B311: Weak Random

**Finding:** Using `random` module for security

**Bad:**
```python
import random
token = random.randint(1000, 9999)  # ❌ Not cryptographically secure
```

**Good:**
```python
import secrets
token = secrets.token_urlsafe(32)  # ✅ Cryptographically secure

# For Django
from django.utils.crypto import get_random_string
token = get_random_string(32)
```

## File Operations

### B103: File Permissions Too Open

**Finding:** Files created with world-writable permissions

**Bad:**
```python
os.chmod('/path/file', 0o777)  # ❌ World writable
```

**Good:**
```python
os.chmod('/path/file', 0o644)  # ✅ Owner write, others read
os.chmod('/path/file', 0o600)  # ✅ Owner only
```

### B108: Insecure Temp File

**Finding:** Using hardcoded temp file paths

**Bad:**
```python
temp = open('/tmp/myapp.tmp', 'w')  # ❌ Predictable path
```

**Good:**
```python
import tempfile
with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
    temp.write(data)  # ✅ Secure temp file
```

## Deserialization

### B301: Pickle Usage

**Finding:** `pickle.loads()` can execute arbitrary code

**Risk:** Only unpickle trusted data

**Bad:**
```python
import pickle
data = pickle.loads(user_data)  # ❌ Arbitrary code execution!
```

**Good:**
```python
import json
data = json.loads(user_data)  # ✅ Safe for untrusted data

# If you must use pickle (trusted source only):
import pickle
data = pickle.loads(trusted_data)  # nosec B301 - comment explaining trust
```

### B302: Unsafe YAML Load

**Finding:** `yaml.load()` can execute code

**Bad:**
```python
import yaml
data = yaml.load(user_input)  # ❌ Code execution!
```

**Good:**
```python
import yaml
data = yaml.safe_load(user_input)  # ✅ Safe loader
```

## Code Quality

### B101: Assert Used

**Finding:** `assert` statements removed when Python runs with `-O`

**Context:** Don't use assert for security checks

**Bad:**
```python
assert user.is_authenticated  # ❌ Removed with -O flag!
```

**Good:**
```python
if not user.is_authenticated:  # ✅ Always checked
    raise PermissionDenied
```

**OK for tests:**
```python
# In test files, assert is fine
assert response.status_code == 200  # ✅ Test assertion
```

### B112: Try-Except-Continue

**Finding:** Empty exception handlers

**Bad:**
```python
try:
    risky_operation()
except Exception:
    continue  # ❌ Silently fails
```

**Good:**
```python
try:
    risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")  # ✅ Logged
    # Handle or re-raise
```

### B110: Try-Except-Pass

**Finding:** Exception handler does nothing

**Bad:**
```python
try:
    risky_operation()
except Exception:
    pass  # ❌ Silently ignores all errors
```

**Good:**
```python
import logging
logger = logging.getLogger(__name__)

try:
    risky_operation()
except SpecificException as e:
    logger.warning(f"Non-critical error: {e}")  # ✅ Logged
except CriticalException:
    raise  # ✅ Re-raise critical errors
```

## HTTP Security

### B113: Request Without Timeout

**Finding:** HTTP requests without timeout

**Bad:**
```python
import requests
requests.get(url)  # ❌ Can hang forever
```

**Good:**
```python
import requests
requests.get(url, timeout=30)  # ✅ 30 second timeout
```

### B501: Request with verify=False

**Finding:** SSL verification disabled

**Bad:**
```python
requests.get(url, verify=False)  # ❌ MITM vulnerability!
```

**Good:**
```python
requests.get(url, verify=True)  # ✅ Verify SSL (default)
# Or provide custom CA bundle
requests.get(url, verify='/path/to/ca-bundle.crt')
```

## Suppressing False Positives

### Inline Suppression

```python
# Suppress specific finding with comment
password = get_config_password()  # nosec B105

# Suppress specific test ID
result = pickle.loads(trusted_data)  # nosec B301

# Better: Add explanation
# This data comes from trusted internal cache, not user input
result = pickle.loads(cached_data)  # nosec B301
```

### File-Level Exclusion

In `.bandit`:
```ini
[bandit]
# Skip tests globally
skips = ['B101', 'B201']

# Exclude entire files/directories
exclude_dirs = [
    'tests',
    'migrations'
]
```

## Severity Levels

| Severity | Priority | Action |
|----------|----------|--------|
| **High** | 🔴 Critical | Fix immediately before merge |
| **Medium** | 🟡 Important | Fix before release |
| **Low** | 🟢 Optional | Fix when convenient |

## Confidence Levels

| Confidence | Meaning | False Positive Rate |
|------------|---------|---------------------|
| **High** | Very likely real issue | Low |
| **Medium** | Probably an issue | Moderate |
| **Low** | Might be an issue | High |

## Best Practices

1. **Never disable security checks without documentation**
   ```python
   # ❌ Bad
   data = pickle.loads(user_data)  # nosec

   # ✅ Good
   # This data is from our internal cache system, validated on write
   # See: docs/architecture/caching.md
   data = pickle.loads(cache_data)  # nosec B301
   ```

2. **Fix root cause, not symptom**
   - Don't just suppress warnings
   - Refactor to use secure patterns
   - Document why if suppression is truly needed

3. **Prioritize by severity AND confidence**
   - High severity + High confidence = Fix now
   - High severity + Low confidence = Review carefully
   - Low severity + Low confidence = May skip

4. **Test fixes**
   - Ensure fix doesn't break functionality
   - Add test case for the security issue
   - Verify Bandit no longer flags it

## Additional Resources

- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Bandit Test Plugins](https://bandit.readthedocs.io/en/latest/plugins/index.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)

---

**Related:**
- [Security Scanning Guide](security-scanning.md)
- [Testing Guide](testing.md)
