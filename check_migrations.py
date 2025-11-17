"""
Script to check if there are any pending migrations
"""
from io import StringIO
from django.core.management import call_command
import django
import os
import sys

# Setup Django
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        'active_interview_backend'))
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'active_interview_project.settings')

django.setup()


# Capture output
output = StringIO()
call_command('makemigrations', '--dry-run', stdout=output, verbosity=2)

result = output.getvalue()
print(result)

if "No changes detected" in result:
    print("\n✓ SUCCESS: No new migrations needed!")
    print("The model is in sync with the latest migration.")
else:
    print("\n✗ WARNING: New migrations would be created!")
    print("This means the model doesn't match the latest migration.")
