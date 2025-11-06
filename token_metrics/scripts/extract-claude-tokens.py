#!/usr/bin/env python3
"""
Extract Claude Code Token Usage Automatically

This script extracts token usage from the current Claude Code session
by reading conversation metadata or system messages.

Usage:
    python token_metrics/scripts/extract-claude-tokens.py
    python token_metrics/scripts/extract-claude-tokens.py --auto-track
"""

import os
import sys
import json
import re
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
    return os.getcwd()


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


def find_claude_data_dir():
    """Try to find Claude Code conversation data directory."""
    possible_locations = [
        # Windows
        os.path.expandvars(r'%APPDATA%\Claude\conversations'),
        os.path.expandvars(r'%LOCALAPPDATA%\Claude\conversations'),
        os.path.expanduser(r'~\AppData\Roaming\Claude\conversations'),
        os.path.expanduser(r'~\AppData\Local\Claude\conversations'),
        # Mac/Linux
        os.path.expanduser('~/.config/Claude/conversations'),
        os.path.expanduser('~/Library/Application Support/Claude/conversations'),
    ]

    for location in possible_locations:
        if os.path.exists(location):
            return location

    return None


def extract_tokens_from_text(text):
    """Extract token usage from text using regex patterns."""
    # Pattern: "Token usage: 58992/200000; 141008 remaining"
    pattern = r'Token usage:\s*(\d+)/\d+;\s*\d+\s+remaining'
    matches = re.findall(pattern, text)

    if matches:
        # Return the most recent (last) token count
        return int(matches[-1])

    return None


def read_conversation_file(file_path):
    """Try to read conversation data and extract tokens."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

            # Try JSON format
            try:
                data = json.loads(content)
                # Look for token usage in metadata
                if 'metadata' in data and 'token_usage' in data['metadata']:
                    return data['metadata']['token_usage']
            except json.JSONDecodeError:
                pass

            # Try extracting from text
            tokens = extract_tokens_from_text(content)
            if tokens:
                return tokens

    except Exception as e:
        print(f"Could not read {file_path}: {e}", file=sys.stderr)

    return None


def find_latest_conversation():
    """Find the most recent conversation file."""
    claude_dir = find_claude_data_dir()

    if not claude_dir:
        return None

    try:
        # Find all conversation files
        conv_files = []
        for root, dirs, files in os.walk(claude_dir):
            for file in files:
                if file.endswith('.json') or file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    mtime = os.path.getmtime(file_path)
                    conv_files.append((mtime, file_path))

        if not conv_files:
            return None

        # Sort by modification time (most recent first)
        conv_files.sort(reverse=True)

        # Return most recent
        return conv_files[0][1]

    except Exception as e:
        print(f"Error searching for conversations: {e}", file=sys.stderr)
        return None


def get_token_count_from_env():
    """Try to get token count from environment variable (if set by hook)."""
    return os.environ.get('CLAUDE_TOKEN_COUNT')


def prompt_for_tokens():
    """Prompt user to enter token count manually."""
    print("\n" + "="*70)
    print("  CLAUDE CODE TOKEN TRACKER")
    print("="*70)
    print("\nCouldn't automatically detect token usage.")
    print("Please check your Claude Code conversation for a message like:")
    print('  "Token usage: 58992/200000; 141008 remaining"')
    print()

    try:
        token_input = input("Enter token count (or press Enter to skip): ").strip()

        if not token_input:
            return None

        tokens = int(token_input)
        if tokens < 0:
            print("Invalid token count")
            return None

        return tokens

    except (ValueError, KeyboardInterrupt):
        print("\nSkipped token tracking")
        return None


def save_token_record(tokens, notes="Auto-tracked", auto_tracked=False):
    """Save token record for CI/CD import."""
    git_info = get_git_info()
    repo_root = get_repo_root()

    # Create temp directory
    temp_dir = os.path.join(repo_root, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Estimate prompt/completion split (80/20 typical)
    prompt_tokens = int(tokens * 0.8)
    completion_tokens = tokens - prompt_tokens

    # Create record
    record = {
        'timestamp': datetime.now().isoformat(),
        'git_branch': git_info['branch'],
        'commit_sha': git_info['commit'],
        'model_name': 'claude-sonnet-4-5-20250929',
        'endpoint': 'messages',
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'total_tokens': tokens,
        'source': 'auto-tracked' if auto_tracked else 'manual-entry',
        'notes': notes
    }

    # Save to file
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"claude_local_{timestamp_str}.json"
    filepath = os.path.join(temp_dir, filename)

    with open(filepath, 'w') as f:
        json.dump(record, f, indent=2)

    return filepath, record


def update_local_tracking(tokens, notes="Auto-tracked"):
    """Update the local tracking file for this branch."""
    repo_root = get_repo_root()
    tracking_dir = os.path.join(repo_root, 'token_metrics', 'local_tracking')
    os.makedirs(tracking_dir, exist_ok=True)

    git_info = get_git_info()
    branch = git_info['branch']
    safe_branch = branch.replace('/', '_').replace('\\', '_')
    tracking_file = os.path.join(tracking_dir, f'tokens_{safe_branch}.json')

    # Load existing data
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as f:
            data = json.load(f)
    else:
        data = {
            'branch': branch,
            'total_tokens': 0,
            'sessions': [],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }

    # Add new session
    session = {
        'timestamp': datetime.now().isoformat(),
        'tokens': tokens,
        'notes': notes
    }
    data['sessions'].append(session)
    data['total_tokens'] += tokens
    data['last_updated'] = datetime.now().isoformat()

    # Save
    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2)

    return data


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract Claude Code token usage automatically'
    )
    parser.add_argument(
        '--auto-track',
        action='store_true',
        help='Automatically track and save tokens'
    )
    parser.add_argument(
        '--notes',
        type=str,
        default='Auto-tracked',
        help='Notes for this tracking session'
    )
    parser.add_argument(
        '--silent',
        action='store_true',
        help='Suppress output (for hooks)'
    )

    args = parser.parse_args()

    # Try to get token count
    tokens = None
    auto_tracked = False

    # Method 1: Environment variable
    env_tokens = get_token_count_from_env()
    if env_tokens:
        tokens = int(env_tokens)
        auto_tracked = True
        if not args.silent:
            print(f"✅ Found token count from environment: {tokens:,}")

    # Method 2: Try to extract from conversation files
    if not tokens:
        if not args.silent:
            print("🔍 Searching for Claude Code conversation data...")

        conv_file = find_latest_conversation()
        if conv_file:
            tokens = read_conversation_file(conv_file)
            if tokens:
                auto_tracked = True
                if not args.silent:
                    print(f"✅ Extracted {tokens:,} tokens from conversation")

    # Method 3: Prompt user
    if not tokens and not args.silent:
        tokens = prompt_for_tokens()
        auto_tracked = False

    # No tokens found
    if not tokens:
        if not args.silent:
            print("\n⚠️  No token usage found or entered")
            print("💡 Run manually: track-tokens.bat add [count] 'notes'")
        return 1

    # Save the token record
    if args.auto_track:
        try:
            # Update local tracking
            data = update_local_tracking(tokens, args.notes)

            # Save for CI/CD import
            filepath, record = save_token_record(tokens, args.notes, auto_tracked)

            if not args.silent:
                print(f"\n✅ Token tracking complete!")
                print(f"\n📊 Summary:")
                print(f"   Tokens:        {tokens:,}")
                print(f"   Branch:        {record['git_branch']}")
                print(f"   Branch Total:  {data['total_tokens']:,}")
                print(f"   Sessions:      {len(data['sessions'])}")
                print(f"   Saved to:      {os.path.basename(filepath)}")
                print()

            return 0

        except Exception as e:
            print(f"\n❌ Error tracking tokens: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
    else:
        if not args.silent:
            print(f"\n📊 Found {tokens:,} tokens")
            print("💡 Run with --auto-track to save automatically")
        return 0


if __name__ == '__main__':
    sys.exit(main())
