#!/usr/bin/env python
"""Create test users for local development."""

import os
import django

from django.contrib.auth.models import User  # noqa: E402
from active_interview_app.models import UserProfile  # noqa: E402

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'active_interview_project.settings')
django.setup()

# Create admin user
admin_user, created = User.objects.get_or_create(
    username='admin_user',
    defaults={
        'email': 'admin@example.com',
        'first_name': 'Admin',
        'last_name': 'User',
        'is_superuser': True,
        'is_staff': True,
        'is_active': True
    }
)
admin_user.set_password('admin123')
admin_user.save()

# Create or update admin profile
profile, _ = UserProfile.objects.get_or_create(
    user=admin_user,
    defaults={'role': 'admin', 'auth_provider': 'local'}
)
profile.role = 'admin'
profile.save()

print("✓ Created admin_user (password: admin123)")

# Create interviewer user
interviewer, created = User.objects.get_or_create(
    username='interviewer_jane',
    defaults={
        'email': 'jane.interviewer@example.com',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'is_active': True
    }
)
interviewer.set_password('interviewer123')
interviewer.save()

# Create or update interviewer profile
profile, _ = UserProfile.objects.get_or_create(
    user=interviewer,
    defaults={'role': 'interviewer', 'auth_provider': 'local'}
)
profile.role = 'interviewer'
profile.save()

print("✓ Created interviewer_jane (password: interviewer123)")

# Create candidate user
candidate, created = User.objects.get_or_create(
    username='candidate_john',
    defaults={
        'email': 'john.candidate@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'is_active': True
    }
)
candidate.set_password('candidate123')
candidate.save()

# Create or update candidate profile
profile, _ = UserProfile.objects.get_or_create(
    user=candidate,
    defaults={'role': 'candidate', 'auth_provider': 'local'}
)
profile.role = 'candidate'
profile.save()

print("✓ Created candidate_john (password: candidate123)")

print("\n" + "="*60)
print("Test Users Created Successfully!")
print("="*60)
print("\nAdmin User:")
print("  Username: admin_user")
print("  Password: admin123")
print("  Email: admin@example.com")
print("  Role: Admin (superuser)")
print("\nInterviewer:")
print("  Username: interviewer_jane")
print("  Password: interviewer123")
print("  Email: jane.interviewer@example.com")
print("  Role: Interviewer")
print("\nCandidate:")
print("  Username: candidate_john")
print("  Password: candidate123")
print("  Email: john.candidate@example.com")
print("  Role: Candidate")
print("\n" + "="*60)
print("\nYou can now login at http://localhost")
print("="*60 + "\n")
