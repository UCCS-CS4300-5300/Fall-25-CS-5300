#!/usr/bin/env python3
"""
Automatic Token Tracker - Accumulates tokens across Claude Code sessions

This script reads token usage from system reminders in the conversation history
and maintains a running total that persists across sessions.

Usage:
    python token_metrics/scripts/auto-track-tokens.py --add-tokens 41613
    python token_metrics/scripts/auto-track-tokens.py --show
    python token_metrics/scripts/auto-track-tokens.py --submit
    python token_metrics/scripts/auto-track-tokens.py --reset
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
    """Get current git branch and commit."""
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


def get_tracking_file():
    """Get path to the persistent tracking file."""
    repo_root = get_repo_root()
    tracking_dir = os.path.join(repo_root, 'token_metrics', 'local_tracking')
    os.makedirs(tracking_dir, exist_ok=True)

    git_info = get_git_info()
    branch = git_info['branch']
    # Sanitize branch name for filename
    safe_branch = branch.replace('/', '_').replace('\\', '_')
    return os.path.join(tracking_dir, f'tokens_{safe_branch}.json')


def load_tracking_data():
    """Load existing tracking data."""
    tracking_file = get_tracking_file()

    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load tracking data: {e}")

    # Return default structure
    git_info = get_git_info()
    return {
        'branch': git_info['branch'],
        'total_tokens': 0,
        'sessions': [],
        'created_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }


def save_tracking_data(data):
    """Save tracking data to file."""
    tracking_file = get_tracking_file()
    data['last_updated'] = datetime.now().isoformat()

    try:
        with open(tracking_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving tracking data: {e}")
        return False


def add_tokens(tokens, notes="", auto_export=False):
    """Add tokens to the running total."""
    data = load_tracking_data()

    session = {
        'timestamp': datetime.now().isoformat(),
        'tokens': tokens,
        'notes': notes
    }

    data['sessions'].append(session)
    data['total_tokens'] += tokens

    if save_tracking_data(data):
        print(f"\n✅ Added {tokens:,} tokens to tracking")
        print(f"📊 Total accumulated: {data['total_tokens']:,} tokens")
        print(f"🌳 Branch: {data['branch']}")
        print(f"📝 Sessions tracked: {len(data['sessions'])}\n")

        # Auto-export if requested
        if auto_export:
            export_filename = f"tokens_{data['branch'].replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if auto_export_tokens(export_filename, data):
                print(f"💾 Auto-exported to: {export_filename}\n")

        return True
    return False


def auto_export_tokens(filename, data):
    """Automatically export tokens to a file."""
    try:
        # Get repository root
        repo_root = get_repo_root()
        temp_dir = os.path.join(repo_root, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        output_path = os.path.join(temp_dir, filename)

        # Create export data structure
        export_data = {
            'export_metadata': {
                'exported_at': datetime.now().isoformat(),
                'exported_by': os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown',
                'export_version': '1.0',
                'source_machine': os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or 'unknown',
                'auto_export': True
            },
            'token_data': {
                'branch': data['branch'],
                'total_tokens': data['total_tokens'],
                'sessions': data['sessions'],
                'created_at': data['created_at'],
                'last_updated': data['last_updated']
            }
        }

        # Add git context
        git_info = get_git_info()
        export_data['git_context'] = {
            'branch': git_info['branch'],
            'commit': git_info['commit']
        }

        # Write to file
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        return True
    except Exception as e:
        print(f"⚠️  Auto-export failed: {e}")
        return False


def show_tracking():
    """Display current tracking status."""
    data = load_tracking_data()

    print("\n" + "="*60)
    print("  TOKEN TRACKING STATUS")
    print("="*60 + "\n")

    print(f"🌳 Branch: {data['branch']}")
    print(f"📊 Total Tokens: {data['total_tokens']:,}")
    print(f"📝 Sessions: {len(data['sessions'])}")
    print(f"🕐 Created: {data['created_at'][:19]}")
    print(f"🕐 Last Updated: {data['last_updated'][:19]}")

    if data['sessions']:
        print(f"\n{'Recent Sessions:':<20}")
        print("-" * 60)
        for i, session in enumerate(data['sessions'][-5:], 1):
            timestamp = session['timestamp'][:19]
            tokens = session['tokens']
            notes = session.get('notes', '')
            print(f"  {timestamp} | {tokens:>8,} tokens", end="")
            if notes:
                print(f" | {notes}")
            else:
                print()

    print("\n" + "="*60 + "\n")


def submit_tokens():
    """Submit accumulated tokens to the database."""
    data = load_tracking_data()

    if data['total_tokens'] == 0:
        print("⚠️  No tokens to submit!")
        return False

    print(f"\n📊 Submitting {data['total_tokens']:,} tokens from {len(data['sessions'])} sessions...")

    # Estimate input/output split (rough estimate: 80% input, 20% output)
    input_tokens = int(data['total_tokens'] * 0.8)
    output_tokens = data['total_tokens'] - input_tokens

    # Create notes with session summary
    notes = f"Accumulated from {len(data['sessions'])} Claude Code sessions"

    # Call the track-claude-tokens script
    repo_root = get_repo_root()
    script_path = os.path.join(repo_root, 'token_metrics', 'scripts', 'track-claude-tokens.py')

    try:
        result = subprocess.run(
            [sys.executable, script_path,
             '--input-tokens', str(input_tokens),
             '--output-tokens', str(output_tokens),
             '--notes', notes],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("✅ Successfully submitted token usage!")
            print(result.stdout)

            # Archive the data
            tracking_file = get_tracking_file()
            archive_file = tracking_file.replace('.json', f'_archived_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

            try:
                os.rename(tracking_file, archive_file)
                print(f"📦 Archived tracking data to: {os.path.basename(archive_file)}\n")
            except Exception as e:
                print(f"⚠️  Warning: Could not archive tracking file: {e}\n")

            return True
        else:
            print(f"❌ Error submitting tokens:\n{result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error running track script: {e}")
        return False


def reset_tracking():
    """Reset the tracking data."""
    tracking_file = get_tracking_file()

    if os.path.exists(tracking_file):
        try:
            # Archive before deleting
            archive_file = tracking_file.replace('.json', f'_reset_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            os.rename(tracking_file, archive_file)
            print(f"✅ Reset tracking data (archived to {os.path.basename(archive_file)})\n")
            return True
        except Exception as e:
            print(f"❌ Error resetting tracking: {e}")
            return False
    else:
        print("ℹ️  No tracking data to reset\n")
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Automatic Token Tracker - Accumulate tokens across sessions'
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--add-tokens', type=int, help='Add tokens to the running total')
    group.add_argument('--show', action='store_true', help='Show current tracking status')
    group.add_argument('--submit', action='store_true', help='Submit accumulated tokens to database')
    group.add_argument('--reset', action='store_true', help='Reset tracking data')

    parser.add_argument('--notes', type=str, default='', help='Optional notes for this session')
    parser.add_argument('--auto-export', action='store_true', help='Automatically export after adding tokens')

    args = parser.parse_args()

    if args.add_tokens:
        return 0 if add_tokens(args.add_tokens, args.notes, auto_export=args.auto_export) else 1
    elif args.show:
        show_tracking()
        return 0
    elif args.submit:
        return 0 if submit_tokens() else 1
    elif args.reset:
        return 0 if reset_tracking() else 1


if __name__ == '__main__':
    sys.exit(main())
