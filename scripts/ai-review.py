# Jacob Hartt
# Tom Hastings
# CS4300.001
# 03/06/2025

from datetime import datetime
import sys
import os
import json
import subprocess
from zoneinfo import ZoneInfo

from openai import OpenAI


TIMEZONE = "America/Denver"
TIME_FORMAT = "%m-%d-%Y_%I%M%p"


def get_current_git_branch():
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return os.environ.get('GITHUB_HEAD_REF') or \
           os.environ.get('GITHUB_REF_NAME') or \
           'unknown'


def track_token_usage_standalone(model_name, prompt_tokens, completion_tokens):
    """
    Track token usage for CI/CD scripts that don't have Django context.
    This writes to a temporary file that can be imported later.
    """
    git_branch = get_current_git_branch()

    # Create a record file for later import
    record = {
        'timestamp': datetime.now().isoformat(),
        'git_branch': git_branch,
        'model_name': model_name,
        'endpoint': 'chat.completions',
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'total_tokens': prompt_tokens + completion_tokens
    }

    # Write to a temp file in the repo
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    temp_dir = os.path.join(repo_root, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    filename = f"token_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(temp_dir, filename)

    with open(filepath, 'w') as f:
        json.dump(record, f, indent=2)

    print(f"\n📊 Token Usage: {record['total_tokens']} tokens "
          f"({prompt_tokens} prompt + {completion_tokens} completion)")
    print(f"   Model: {model_name}")
    print(f"   Branch: {git_branch}")
    print(f"   Saved to: {filepath}\n")


# Startup open ai client
client = OpenAI()

# Get the diff from command line argument 1
diff = ""
with open(sys.argv[1], 'r') as diff_file:
    diff = diff_file.read()
    # print(diff)
    diff_file.close()

# Provide project context here
project_context = """
These code changes are for a Django web app. The app is deployed with
docker-compose and Nginx on DigitalOcean. The app is an active interview
service which uses the ChatGPT API to create a dynamic interview chat
for job-seekers.
""".strip()

# Provide the prompt here
prompt = f"""
At the end of your message, state either AI_REVIEW_FAIL if you found any
significant issues or AI_REVIEW_SUCCESS if the code is acceptable.

{project_context}

Review the following code changes comprehensively and provide detailed feedback.
Please organize your review into the following sections:

## 1. CODE SMELLS
Identify common code smells such as:
- Duplicated code
- Long methods/functions (>50 lines)
- Large classes (too many responsibilities)
- Long parameter lists
- Dead/unused code
- Magic numbers and hardcoded values
- Inappropriate naming conventions
- Feature envy or data clumps

## 2. SECURITY VULNERABILITIES
Check for security issues including:
- OWASP Top 10 vulnerabilities (SQL injection, XSS, CSRF, etc.)
- Insecure authentication/authorization
- Exposed secrets or sensitive data
- Insecure dependencies
- Path traversal vulnerabilities
- Command injection risks
- Unsafe deserialization
- Security misconfigurations

## 3. CODE QUALITY & MAINTAINABILITY
Assess:
- Code complexity (cyclomatic complexity)
- Readability and clarity
- Adherence to DRY (Don't Repeat Yourself)
- SOLID principles compliance
- Separation of concerns
- Proper error handling
- Resource management (memory leaks, file handles, connections)
- Code organization and structure

## 4. BEST PRACTICES & STANDARDS
Evaluate:
- Django best practices
- Python PEP 8 style guide compliance
- REST API design principles
- Database query optimization
- Proper use of Django ORM
- Template security practices
- Static file handling
- Environment variable usage

## 5. PERFORMANCE CONCERNS
Look for:
- N+1 query problems
- Missing database indexes
- Inefficient algorithms
- Memory-intensive operations
- Unnecessary database calls
- Missing caching opportunities
- Large file handling issues

## 6. TESTING & DOCUMENTATION
Check for:
- Missing test coverage for new features
- Inadequate edge case testing
- Missing docstrings/comments
- Unclear function/class documentation
- Missing type hints (where applicable)

## 7. ACCESSIBILITY & UX
If frontend changes:
- WCAG compliance issues
- Missing ARIA labels
- Keyboard navigation problems
- Color contrast issues

## 8. SUMMARY
Provide a brief overall assessment with:
- Critical issues that must be fixed
- Important suggestions for improvement
- Nice-to-have enhancements
- Overall code quality rating (1-10)

```
{diff}
```
""".strip()

# print(prompt)

# Run the prompt
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant that provides information \
                        in Markdown format."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
)
response = completion.choices[0].message.content

# Track token usage
if hasattr(completion, 'usage') and completion.usage:
    track_token_usage_standalone(
        model_name=completion.model,
        prompt_tokens=completion.usage.prompt_tokens,
        completion_tokens=completion.usage.completion_tokens
    )

# Print the response and write markdown file
print(response)

local_time = datetime.now(ZoneInfo(TIMEZONE)).strftime(TIME_FORMAT)
out_path = f"review-{local_time}.md"

with open(out_path, 'w') as out_file:
    out_file.write(response)
    out_file.close()

# # Get last word in the response
# raw_result = response.strip().split()[-1]  # get last word
# plain_result = raw_result.replace("*", "")  # remove italics/bold from result

if "AI_REVIEW_SUCCESS" in response:
    sys.exit(0)  # SUCCESS
else:
    sys.exit(1)  # FAIL
