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
    # Try multiple possible temp directory locations
    script_dir = os.path.dirname(__file__)
    possible_temp_dirs = [
        os.path.join(script_dir, '..', '..', 'temp'),  # From token_metrics/scripts
        os.path.join(script_dir, '..', 'temp'),         # From token_metrics
        'temp',                                         # Relative to working dir
    ]

    temp_dir = None
    for possible_dir in possible_temp_dirs:
        abs_path = os.path.abspath(possible_dir)
        if os.path.exists(abs_path):
            temp_dir = abs_path
            break

    if not temp_dir:
        print(f"ℹ️  No temp directory found")
        return 0

    # Find all token usage JSON files (multiple patterns)
    patterns = [
        'token_usage_*.json',     # CI/CD ai-review tokens
        'claude_local_*.json',    # Local Claude Code tracking
        '*_tokens.json',          # Generic exported tokens
    ]

    json_files = []
    for pattern in patterns:
        json_files.extend(glob.glob(os.path.join(temp_dir, pattern)))

    # Remove duplicates
    json_files = list(set(json_files))

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

            # Handle different JSON formats
            # Format 1: Direct format (from ai-review.py and track-claude-tokens.py)
            if 'git_branch' in record and 'timestamp' in record:
                git_branch = record['git_branch']
                timestamp = datetime.fromisoformat(record['timestamp'])
                model_name = record['model_name']
                endpoint = record.get('endpoint', 'unknown')
                prompt_tokens = record['prompt_tokens']
                completion_tokens = record['completion_tokens']
                total_tokens = record['total_tokens']

            # Format 2: Export format (from export-tokens.py)
            elif 'token_data' in record:
                token_data = record['token_data']
                git_branch = token_data['branch']

                # Use the last session timestamp
                if token_data['sessions']:
                    timestamp = datetime.fromisoformat(token_data['sessions'][-1]['timestamp'])
                else:
                    timestamp = datetime.fromisoformat(token_data['last_updated'])

                # Default model for exported data
                model_name = 'claude-sonnet-4-5-20250929'
                endpoint = 'messages'

                # Estimate split (80/20)
                total_tokens = token_data['total_tokens']
                prompt_tokens = int(total_tokens * 0.8)
                completion_tokens = total_tokens - prompt_tokens
            else:
                print(f"⚠️  Unknown format: {os.path.basename(json_file)}")
                skipped_count += 1
                continue

            # Check for duplicate
            existing = TokenUsage.objects.filter(
                created_at=timestamp,
                model_name=model_name,
                git_branch=git_branch
            ).first()

            if existing:
                print(f"⏭️  Skipped (duplicate): {os.path.basename(json_file)}")
                skipped_count += 1
                continue

            # Extract additional metadata if available
            commit_sha = record.get('commit_sha', 'unknown')
            source = record.get('source', 'unknown')
            notes = record.get('notes', '')

            # Create the record with all available metadata
            usage_record = TokenUsage.objects.create(
                git_branch=git_branch,
                model_name=model_name,
                endpoint=endpoint,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                created_at=timestamp
            )

            # Calculate cost for reporting
            if 'claude-sonnet-4-5' in model_name.lower():
                cost = (prompt_tokens / 1_000_000) * 3.00 + (completion_tokens / 1_000_000) * 15.00
            elif 'gpt-4' in model_name.lower():
                cost = (prompt_tokens / 1_000_000) * 2.50 + (completion_tokens / 1_000_000) * 10.00
            else:
                cost = (prompt_tokens / 1_000_000) * 3.00 + (completion_tokens / 1_000_000) * 15.00

            print(f"✅ Imported: {os.path.basename(json_file)}")
            print(f"   Branch:    {git_branch}")
            print(f"   Model:     {model_name}")
            print(f"   Endpoint:  {endpoint}")
            print(f"   Tokens:    {total_tokens:,} ({prompt_tokens:,} input + {completion_tokens:,} output)")
            print(f"   Cost:      ${cost:.4f}")
            print(f"   Timestamp: {timestamp}")
            if source:
                print(f"   Source:    {source}")
            if notes:
                print(f"   Notes:     {notes}")
            print()

            imported_count += 1

            # Delete the JSON file after successful import
            os.remove(json_file)

        except Exception as e:
            print(f"❌ Error importing {json_file}: {e}")
            import traceback
            traceback.print_exc()
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
