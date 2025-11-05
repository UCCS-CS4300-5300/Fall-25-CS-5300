# Token Tracking - Quick Start

**All token tracking files are in the `token_metrics/` folder.**

## Quick Usage (From Repository Root)

```bash
# Single command launcher
track-tokens.bat add 110000 "My feature work"
track-tokens.bat show
track-tokens.bat submit

# Or navigate to token_metrics folder
cd token_metrics
add-tokens.bat 110000 "My feature work"
show-tokens.bat
submit-tokens.bat
```

---

## Full Documentation

📚 **Complete guides in `token_metrics/docs/`:**

- **[TOKEN_TRACKING_GUIDE.md](token_metrics/docs/TOKEN_TRACKING_GUIDE.md)** - Complete user guide
- **[QUICK_TOKEN_REFERENCE.md](token_metrics/docs/QUICK_TOKEN_REFERENCE.md)** - Command reference
- **[TOKEN_EXPORT_IMPORT.md](token_metrics/docs/TOKEN_EXPORT_IMPORT.md)** - Sharing between instances
- **[SYSTEM_ARCHITECTURE.md](token_metrics/docs/SYSTEM_ARCHITECTURE.md)** - System design
- **[PIPELINE_FLOW.md](token_metrics/docs/PIPELINE_FLOW.md)** - CI/CD integration

📂 **Main folder**: `token_metrics/README.md`

---

## Quick Commands

| Command | Description |
|---------|-------------|
| `track-tokens.bat add [count] [notes]` | Add tokens |
| `track-tokens.bat show` | View total |
| `track-tokens.bat submit` | Submit to database |
| `track-tokens.bat export [file]` | Export for sharing |
| `track-tokens.bat import [file]` | Import from file |
| `track-tokens.bat help` | Full help |

---

## Example: Track This Session

```bash
# Add tokens from this conversation
track-tokens.bat add 112000 "Reorganized token files and improved structure"

# Check total
track-tokens.bat show

# Submit when done
track-tokens.bat submit

# Push to see in GitHub Actions
git push
```

---

For complete documentation, see **`token_metrics/` folder**.
