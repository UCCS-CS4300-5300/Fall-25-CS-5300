#!/usr/bin/env python3
"""
Import Token Data - Load token tracking from portable file

This script imports token tracking data from an exported JSON file,
allowing you to transfer token data between instances, machines, or databases.

Usage:
    python token_metrics/scripts/import-tokens.py --input my_tokens.json
    python token_metrics/scripts/import-tokens.py --input my_tokens.json --merge
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path


def get_repo_root():
    """Get repository root directory."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_tracking_file(branch):
    """Get path to the tracking file for specified branch."""
    repo_root = get_repo_root()
    tracking_dir = os.path.join(repo_root, 'token_metrics', 'local_tracking')
    os.makedirs(tracking_dir, exist_ok=True)

    safe_branch = branch.replace('/', '_').replace('\\', '_')
    return os.path.join(tracking_dir, f'tokens_{safe_branch}.json')


def load_tracking_data(branch):
    """Load existing tracking data for branch."""
    tracking_file = get_tracking_file(branch)

    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass

    return None


def save_tracking_data(branch, data):
    """Save tracking data to file."""
    tracking_file = get_tracking_file(branch)

    try:
        with open(tracking_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving tracking data: {e}", file=sys.stderr)
        return False


def import_tokens(input_file, merge=False):
    """Import token data from a portable file."""

    # Load the import file
    try:
        input_path = os.path.abspath(input_file)
        with open(input_path, 'r') as f:
            import_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON file: {input_file}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    # Validate structure
    if 'token_data' not in import_data:
        print(f"❌ Invalid token export file - missing 'token_data' section")
        return False

    token_data = import_data['token_data']
    metadata = import_data.get('export_metadata', {})

    # Display import info
    print(f"\n📥 Importing Token Data")
    print("=" * 60)

    if metadata:
        print(f"\n📋 Export Info:")
        print(f"   Exported: {metadata.get('exported_at', 'Unknown')[:19]}")
        print(f"   By: {metadata.get('exported_by', 'Unknown')}")
        print(f"   From: {metadata.get('source_machine', 'Unknown')}")

    print(f"\n📊 Token Data:")
    print(f"   Branch: {token_data['branch']}")
    print(f"   Total Tokens: {token_data['total_tokens']:,}")
    print(f"   Sessions: {len(token_data['sessions'])}")
    print(f"   Created: {token_data.get('created_at', 'Unknown')[:19]}")

    # Check if tracking data already exists
    existing_data = load_tracking_data(token_data['branch'])

    if existing_data and not merge:
        print(f"\n⚠️  Warning: Tracking data already exists for branch '{token_data['branch']}'")
        print(f"   Existing tokens: {existing_data['total_tokens']:,}")
        print(f"   Existing sessions: {len(existing_data['sessions'])}")
        print(f"\n❌ Import cancelled. Use --merge to combine with existing data.")
        return False

    # Prepare data to save
    if merge and existing_data:
        print(f"\n🔀 Merging with existing data...")

        # Combine sessions
        combined_sessions = existing_data['sessions'] + token_data['sessions']
        combined_tokens = existing_data['total_tokens'] + token_data['total_tokens']

        save_data = {
            'branch': token_data['branch'],
            'total_tokens': combined_tokens,
            'sessions': combined_sessions,
            'created_at': existing_data['created_at'],
            'last_updated': datetime.now().isoformat(),
            'import_history': existing_data.get('import_history', []) + [{
                'imported_at': datetime.now().isoformat(),
                'imported_from': os.path.basename(input_file),
                'tokens_added': token_data['total_tokens'],
                'sessions_added': len(token_data['sessions'])
            }]
        }

        print(f"\n📊 After Merge:")
        print(f"   Total Tokens: {combined_tokens:,}")
        print(f"   Total Sessions: {len(combined_sessions)}")

    else:
        # Create new tracking data
        save_data = {
            'branch': token_data['branch'],
            'total_tokens': token_data['total_tokens'],
            'sessions': token_data['sessions'],
            'created_at': token_data.get('created_at', datetime.now().isoformat()),
            'last_updated': datetime.now().isoformat(),
            'import_history': [{
                'imported_at': datetime.now().isoformat(),
                'imported_from': os.path.basename(input_file),
                'tokens_added': token_data['total_tokens'],
                'sessions_added': len(token_data['sessions'])
            }]
        }

    # Save the data
    if save_tracking_data(token_data['branch'], save_data):
        print(f"\n✅ Token data imported successfully!")
        print(f"\n💡 Next steps:")
        print(f"   • View data: show-tokens.bat")
        print(f"   • Add more: add-tokens.bat [count] [notes]")
        print(f"   • Submit: submit-tokens.bat")
        print()
        return True
    else:
        print(f"\n❌ Failed to save imported data")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Import token tracking data from a portable file'
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Input file path (exported token data JSON)'
    )

    parser.add_argument(
        '--merge', '-m',
        action='store_true',
        help='Merge with existing data instead of replacing'
    )

    args = parser.parse_args()

    success = import_tokens(
        input_file=args.input,
        merge=args.merge
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
