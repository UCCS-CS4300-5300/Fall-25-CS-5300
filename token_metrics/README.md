# Token Metrics System

This folder contains all token usage tracking functionality for Claude and OpenAI APIs.

## Directory Structure

```
token_metrics/
├── backend/
│   ├── models/           # Django models for token tracking
│   ├── utils/            # Tracking decorators and utilities
│   └── tests/            # Comprehensive test suite
├── scripts/              # Python and shell scripts
├── .githooks/            # Git hooks for local tracking
└── docs/                 # Documentation
```

## Quick Start

See `docs/TOKEN_TRACKING.md` for complete documentation.

## Components

### Backend
- **models/**: TokenUsage and MergeTokenStats models
- **utils/**: Decorators and tracking functions
- **tests/**: 200+ tests with 95%+ coverage

### Scripts
- **track-claude-tokens.py**: Track local Claude Code usage
- **import-token-usage.py**: Import JSON records to database
- **report-token-metrics.py**: Generate usage reports
- **ai-review.py**: AI code review with token tracking
- **install-git-hooks.sh/bat**: Install git hooks
- **run-token-tests.sh/bat**: Run test suite

### Git Hooks
- **post-commit**: Prompts to track Claude Code usage

## Installation

From the repository root:

```bash
# Install git hooks
cd token_metrics
./scripts/install-git-hooks.sh  # or .bat on Windows

# Run tests
./scripts/run-token-tests.sh    # or .bat on Windows
```

## Usage

The token tracking system is integrated into the Django application.
Files in this folder are referenced by the main application.

For detailed usage instructions, see `docs/TOKEN_TRACKING.md`.
