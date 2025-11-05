#!/usr/bin/env python3
"""
Import Token Usage from JSON Files

This script imports token usage records from temporary JSON files
created by CI/CD scripts into the Django database.
"""

import os
import sys
import json
import glob
from datetime import datetime

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'active_interview_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'active_interview_project.settings')
import django
django.setup()

from active_interview_app.token_usage_models import TokenUsage


def import_token_usage_from_json_files():
    """Import token usage records from temporary JSON files."""
    temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')

    if not os.path.exists(temp_dir):
        print(f"ℹ️  No temp directory found at {temp_dir}")
        return 0

    # Find all token usage JSON files
    json_files = glob.glob(os.path.join(temp_dir, 'token_usage_*.json'))

    if not json_files:
        print(f"ℹ️  No token usage JSON files found in {temp_dir}")
        return 0

    imported_count = 0
    skipped_count = 0

    print(f"\n📥 Found {len(json_files)} token usage file(s) to import\n")

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                record = json.load(f)

            # Check if already imported (by timestamp and model)
            timestamp = datetime.fromisoformat(record['timestamp'])

            # Check for duplicate
            existing = TokenUsage.objects.filter(
                created_at=timestamp,
                model_name=record['model_name'],
                git_branch=record['git_branch']
            ).first()

            if existing:
                print(f"⏭️  Skipped (duplicate): {os.path.basename(json_file)}")
                skipped_count += 1
                continue

            # Create the record
            TokenUsage.objects.create(
                git_branch=record['git_branch'],
                model_name=record['model_name'],
                endpoint=record['endpoint'],
                prompt_tokens=record['prompt_tokens'],
                completion_tokens=record['completion_tokens'],
                total_tokens=record['total_tokens'],
                created_at=timestamp
            )

            print(f"✅ Imported: {os.path.basename(json_file)}")
            print(f"   Branch: {record['git_branch']}")
            print(f"   Model: {record['model_name']}")
            print(f"   Tokens: {record['total_tokens']:,}\n")

            imported_count += 1

            # Delete the JSON file after successful import
            os.remove(json_file)

        except Exception as e:
            print(f"❌ Error importing {json_file}: {e}")
            continue

    print(f"\n{'='*70}")
    print(f"Import Summary:")
    print(f"  Imported: {imported_count}")
    print(f"  Skipped:  {skipped_count}")
    print(f"{'='*70}\n")

    return imported_count


if __name__ == '__main__':
    try:
        imported = import_token_usage_from_json_files()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during import: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
