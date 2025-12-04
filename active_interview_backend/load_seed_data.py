#!/usr/bin/env python
"""
Helper script to load seed data and set up test user passwords.

Usage:
    python load_seed_data.py
    python load_seed_data.py --reset  # Reset database first
"""
import os
import sys

# Add the parent directory to Python path so we can import
# active_interview_backend
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Setup Django environment BEFORE importing django
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'active_interview_project.settings'
)
os.environ.setdefault('DJANGO_SECRET_KEY', 'temporary-key-for-seed-data')
os.environ.setdefault('PROD', 'false')

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.db import connection  # noqa: E402
from django.core.management.color import color_style  # noqa: E402

style = color_style()


def reset_database():
    """Delete and recreate the database."""
    print(style.WARNING("Resetting database..."))

    # Close all connections
    connection.close()

    # Delete SQLite database
    db_path = 'db.sqlite3'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(style.SUCCESS(f"[OK] Deleted {db_path}"))

    # Run migrations
    print(style.WARNING("Running migrations..."))
    call_command('migrate', verbosity=0)
    print(style.SUCCESS("[OK] Migrations complete"))


def load_fixtures():
    """Load seed data fixtures."""
    print(style.WARNING("Loading seed data fixtures..."))
    try:
        call_command('loaddata', 'seed_data.json', verbosity=0)
        print(style.SUCCESS("[OK] Fixtures loaded successfully"))
        return True
    except Exception as e:
        print(style.ERROR(f"[FAIL] Failed to load fixtures: {e}"))
        return False


def set_passwords():
    """Set passwords for test users."""
    print(style.WARNING("Setting user passwords..."))

    passwords = {
        'admin_user': 'admin123',
        'interviewer_jane': 'interviewer123',
        'candidate_john': 'candidate123',
    }

    for username, password in passwords.items():
        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            print(style.SUCCESS("[OK] Password set for {}".format(username)))
        except User.DoesNotExist:
            print(style.ERROR("[FAIL] User {} not found".format(username)))
        except Exception as e:
            print(
                style.ERROR(
                    "[FAIL] Failed to set password for {}: {}".format(
                        username, e
                    )
                )
            )


def display_summary():
    """Display summary of loaded data."""
    from active_interview_app.models import (  # noqa: E402
        QuestionBank, Tag, InterviewTemplate, Chat
    )

    print("\n" + "="*60)
    print(style.SUCCESS("*** Seed Data Loaded Successfully! ***"))
    print("="*60)

    print("\n" + style.HTTP_INFO("Users Created:"))
    users = User.objects.all().order_by('id')
    for user in users:
        role = user.profile.role if hasattr(user, 'profile') else 'unknown'
        print("  - {} ({})".format(user.username, role))
        print("    Email: {}".format(user.email))
        if user.username == 'admin_user':
            print("    Password: admin123")
        elif user.username == 'interviewer_jane':
            print("    Password: interviewer123")
        elif user.username == 'candidate_john':
            print("    Password: candidate123")

    print("\n" + style.HTTP_INFO("Question Banks:"))
    for qb in QuestionBank.objects.all():
        question_count = qb.questions.count()
        print("  - {} ({} questions)".format(qb.name, question_count))

    print("\n" + style.HTTP_INFO("Tags:"))
    tags = Tag.objects.all()
    print("  {}".format(', '.join(tag.name for tag in tags)))

    print("\n" + style.HTTP_INFO("Interview Templates:"))
    for template in InterviewTemplate.objects.all():
        section_count = len(template.sections) if template.sections else 0
        print("  - {} ({} sections)".format(template.name, section_count))

    print("\n" + style.HTTP_INFO("Completed Interviews:"))
    for chat in Chat.objects.filter(owner__username='candidate_john'):
        print("  - {} ({})".format(chat.title, chat.type))

    print("\n" + style.WARNING("Next Steps:"))
    print("  1. Run the development server:")
    print("     python manage.py runserver")
    print("\n  2. Login with any of the users above")
    print("\n  3. Explore the application features!")
    print("\n" + "=" * 60 + "\n")


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Load seed data for Active Interview application'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database before loading fixtures'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Auto-accept confirmation prompts'
    )

    args = parser.parse_args()

    print(style.SUCCESS("\n*** Active Interview Seed Data Loader ***\n"))

    # Reset database if requested
    if args.reset:
        if not args.yes:
            confirm = input(
                style.WARNING(
                    "WARNING: This will DELETE all existing data. "
                    "Continue? (yes/no): "
                )
            )
            if confirm.lower() != 'yes':
                print(style.ERROR("Aborted."))
                return
        else:
            print(style.WARNING("Auto-accepting reset (--yes flag provided)"))
        reset_database()

    # Load fixtures
    if not load_fixtures():
        print(style.ERROR("\n[ERROR] Failed to load seed data"))
        return

    # Set passwords
    set_passwords()

    # Display summary
    display_summary()


if __name__ == '__main__':
    main()
