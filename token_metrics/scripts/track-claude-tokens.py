#!/usr/bin/env python3
"""
Track Claude Code Token Usage

This script tracks token usage from Claude Code by reading the session
information and creating records that can be imported into the database.

Usage:
    python scripts/track-claude-tokens.py [--input-tokens X] [--output-tokens Y]

You can call this manually with token counts or use it in a git hook.
"""

import os
import sys
import json
import argparse
from datetime import datetime
import subprocess


def get_git_info():
    """Get current git branch and commit SHA."""
    try:
        branch = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        commit_sha = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        return {'branch': branch, 'commit_sha': commit_sha}
    except Exception as e:
        print(f"Warning: Could not get git info: {e}")
        return {'branch': 'unknown', 'commit_sha': 'unknown'}


def save_token_record(input_tokens, output_tokens, notes=""):
    """Save a token usage record to a JSON file."""
    git_info = get_git_info()

    # Get repository root
    try:
        repo_root = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()
    except Exception:
        repo_root = os.getcwd()

    # Create temp directory
    temp_dir = os.path.join(repo_root, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Create record
    record = {
        'timestamp': datetime.now().isoformat(),
        'git_branch': git_info['branch'],
        'commit_sha': git_info['commit_sha'],
        'model_name': 'claude-sonnet-4-5-20250929',
        'endpoint': 'messages',
        'prompt_tokens': input_tokens,
        'completion_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'source': 'local-claude-code',
        'notes': notes
    }

    # Save to file
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"claude_local_{timestamp_str}.json"
    filepath = os.path.join(temp_dir, filename)

    with open(filepath, 'w') as f:
        json.dump(record, f, indent=2)

    return filepath, record


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Track Claude Code token usage'
    )
    parser.add_argument(
        '--input-tokens',
        type=int,
        help='Number of input tokens used'
    )
    parser.add_argument(
        '--output-tokens',
        type=int,
        help='Number of output tokens used'
    )
    parser.add_argument(
        '--notes',
        type=str,
        default='',
        help='Optional notes about this session'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Prompt for token counts interactively'
    )

    args = parser.parse_args()

    # Interactive mode
    if args.interactive:
        print("\n🤖 Claude Code Token Tracker\n")
        print("Enter the token counts from your Claude Code session:")

        try:
            input_tokens = int(input("  Input tokens: "))
            output_tokens = int(input("  Output tokens: "))
            notes = input("  Notes (optional): ").strip()
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid input or cancelled")
            return 1

    # Command-line mode
    elif args.input_tokens is not None and args.output_tokens is not None:
        input_tokens = args.input_tokens
        output_tokens = args.output_tokens
        notes = args.notes

    # No input provided
    else:
        print("\n⚠️  No token counts provided!")
        print("\nUsage:")
        print("  python scripts/track-claude-tokens.py --input-tokens 1000 --output-tokens 500")
        print("  python scripts/track-claude-tokens.py --interactive")
        print("\nOr check the Claude Code UI for token usage information.")
        return 1

    # Validate
    if input_tokens < 0 or output_tokens < 0:
        print("❌ Error: Token counts must be non-negative")
        return 1

    # Save the record
    try:
        filepath, record = save_token_record(input_tokens, output_tokens, notes)

        print("\n✅ Token usage recorded successfully!\n")
        print(f"  📊 Input tokens:  {input_tokens:,}")
        print(f"  📊 Output tokens: {output_tokens:,}")
        print(f"  📊 Total tokens:  {record['total_tokens']:,}")
        print(f"  🌳 Branch:        {record['git_branch']}")
        print(f"  📝 Commit:        {record['commit_sha'][:8]}")
        print(f"  💾 Saved to:      {os.path.basename(filepath)}")

        if notes:
            print(f"  📝 Notes:         {notes}")

        print("\n💡 This record will be imported when you merge to main.\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error saving token record: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
