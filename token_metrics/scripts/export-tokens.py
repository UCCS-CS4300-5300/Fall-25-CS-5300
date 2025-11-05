#!/usr/bin/env python3
"""
Export Token Data - Create portable token tracking file

This script exports token tracking data to a portable JSON file that can be
shared across different instances, machines, or databases.

Usage:
    python token_metrics/scripts/export-tokens.py --output my_tokens.json
    python token_metrics/scripts/export-tokens.py --output my_tokens.json --branch main
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


def get_git_info():
    """Get current git information."""
    try:
        branch = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        return {'branch': branch, 'commit': commit}
    except Exception:
        return {'branch': 'unknown', 'commit': 'unknown'}


def load_local_tracking(branch=None):
    """Load local tracking data for specified branch."""
    repo_root = get_repo_root()
    tracking_dir = os.path.join(repo_root, 'token_metrics', 'local_tracking')

    if branch is None:
        branch = get_git_info()['branch']

    safe_branch = branch.replace('/', '_').replace('\\', '_')
    tracking_file = os.path.join(tracking_dir, f'tokens_{safe_branch}.json')

    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load tracking file: {e}", file=sys.stderr)

    return None


def export_tokens(output_file, branch=None, include_metadata=True):
    """Export token data to a portable file."""
    git_info = get_git_info()
    target_branch = branch or git_info['branch']

    # Load local tracking data
    tracking_data = load_local_tracking(target_branch)

    if not tracking_data:
        print(f"❌ No tracking data found for branch '{target_branch}'")
        print(f"\nTip: Run 'add-tokens.bat' to start tracking tokens first.")
        return False

    # Create export data structure
    export_data = {
        'export_metadata': {
            'exported_at': datetime.now().isoformat(),
            'exported_by': os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown',
            'export_version': '1.0',
            'source_machine': os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or 'unknown'
        },
        'token_data': {
            'branch': tracking_data['branch'],
            'total_tokens': tracking_data['total_tokens'],
            'sessions': tracking_data['sessions'],
            'created_at': tracking_data['created_at'],
            'last_updated': tracking_data['last_updated']
        }
    }

    # Add git context
    if include_metadata:
        export_data['git_context'] = {
            'branch': git_info['branch'],
            'commit': git_info['commit']
        }

    # Write to file
    try:
        output_path = os.path.abspath(output_file)
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"\n✅ Token data exported successfully!")
        print(f"\n📊 Summary:")
        print(f"   Branch: {tracking_data['branch']}")
        print(f"   Total Tokens: {tracking_data['total_tokens']:,}")
        print(f"   Sessions: {len(tracking_data['sessions'])}")
        print(f"\n💾 Exported to: {output_path}")
        print(f"\n📤 Share this file with others to import your token data!")
        print(f"   They can run: import-tokens.bat {os.path.basename(output_path)}")
        print()

        return True

    except Exception as e:
        print(f"❌ Error exporting token data: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Export token tracking data to a portable file'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output file path (e.g., my_tokens.json)'
    )

    parser.add_argument(
        '--branch', '-b',
        type=str,
        help='Branch to export (defaults to current branch)'
    )

    parser.add_argument(
        '--no-metadata',
        action='store_true',
        help='Exclude export metadata'
    )

    args = parser.parse_args()

    success = export_tokens(
        output_file=args.output,
        branch=args.branch,
        include_metadata=not args.no_metadata
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
