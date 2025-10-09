# AGENTS.md

This file provides guidance to autonomous agents spawned by Claude Code when working on complex, multi-step tasks in this repository.

## Agent Operating Principles

### Task Completion Standards
- Always verify your work before reporting completion
- Run tests after making code changes
- Check linting before finalizing changes
- If you encounter errors, debug them - don't just report failure
- Provide specific file paths and line numbers in your final report

### Code Quality Requirements
- Maintain 80% test coverage - write tests for new functionality
- Follow flake8 standards for Python code
- Follow djlint standards for Django templates
- Match existing code style and patterns in the codebase

### Testing Workflow
When making code changes:
1. Make your changes
2. Run relevant tests: `cd active_interview_backend && python3 manage.py test`
3. Run BDD scenarios if applicable: `behave` or `pytest --bdd`
4. Check coverage: `coverage run manage.py test && coverage report -m`
5. Run linting: `flake8 --config .flake8 .` (from backend directory)
6. Fix any failures before reporting completion

## Common Task Patterns

### Adding New Features
1. Check if a feature file exists in `features/` directory - review user stories and acceptance criteria
2. Read CLAUDE.md to understand the architecture
3. Identify which files need changes (models, views, forms, templates, urls)
4. Check existing similar features for patterns
5. Implement changes following Django conventions
6. Write unit tests in `active_interview_backend/active_interview_app/tests/`
7. Implement step definitions if working from Gherkin scenarios
8. Update URLs in `urls.py` if adding new routes
9. Run migrations if models changed: `python3 manage.py makemigrations && python3 manage.py migrate`
10. Verify with tests and linting

### Bug Fixing
1. Reproduce the bug (check tests or manual verification)
2. Identify root cause using grep/read tools
3. Fix the issue
4. Add test case to prevent regression
5. Verify fix with full test suite
6. Report: what was broken, what you changed, which test proves it's fixed

### Refactoring
1. Understand current implementation thoroughly
2. Write tests for current behavior if coverage is lacking
3. Make incremental changes
4. Run tests after each change
5. Ensure no functionality is lost
6. Report: what you refactored, why, and test results

### Search and Analysis Tasks
When searching for code or analyzing the codebase:
1. Use Grep for code patterns, Glob for file discovery
2. Read relevant files completely, not just snippets
3. Trace function calls across files
4. Check both backend logic (views.py) and frontend (templates/)
5. Report findings with specific file:line references

### Working with BDD Feature Files
When creating or implementing features:
1. **Writing feature files**: Place in `active_interview_backend/features/`
   - Use proper Gherkin syntax (Feature, Scenario, Given/When/Then)
   - Keep scenarios focused and independent
   - Use descriptive scenario names
2. **Implementing step definitions**: Place in `active_interview_backend/active_interview_app/tests/steps/`
   - Create separate step files for different feature areas (e.g., `authentication_steps.py`, `chat_steps.py`)
   - Reuse step definitions across scenarios when possible
   - Keep step implementations focused on test logic, not business logic
3. **Running BDD tests**: Use `behave` (recommended) or `pytest-bdd`
   - Behave: `cd active_interview_backend && behave`
   - Pytest-bdd: `cd active_interview_backend && pytest --bdd`
4. **Integration with unit tests**: BDD scenarios complement but don't replace unit tests
   - Use BDD for user-facing acceptance criteria
   - Use unit tests for implementation details and edge cases

## Django-Specific Guidance

### File Organization
- **Models**: `active_interview_backend/active_interview_app/models.py`
- **Views**: `active_interview_backend/active_interview_app/views.py` (large file, ~900 lines)
- **URLs**: `active_interview_backend/active_interview_app/urls.py`
- **Forms**: `active_interview_backend/active_interview_app/forms.py`
- **Templates**: `active_interview_backend/active_interview_app/templates/`
- **Tests**: `active_interview_backend/active_interview_app/tests/`
- **BDD Features**: `active_interview_backend/features/` (Gherkin user stories)
- **Step Definitions**: `active_interview_backend/active_interview_app/tests/steps/`
- **Settings**: `active_interview_backend/active_interview_project/settings.py`

### Django Conventions in This Project
- Uses class-based views (LoginRequiredMixin, UserPassesTestMixin) for chat/document operations
- Function-based views for simple pages (index, features, etc.)
- AJAX endpoints return JsonResponse
- File uploads handled with FileField models
- User authentication via Django's built-in auth system
- Bootstrap 5 for frontend styling

### Working with the Chat System
The Chat model is central to the application:
- Stores messages as JSON field
- Has key_questions as JSON field (10 timed questions per interview)
- Links to UploadedResume and UploadedJobListing via ForeignKey
- System prompts generated dynamically in views.py based on resume/job listing/difficulty/type
- OpenAI client initialized at module level in views.py

### Database Migrations
Always run migrations after model changes:
```bash
cd active_interview_backend
python3 manage.py makemigrations
python3 manage.py migrate
```

## Docker Environment

### When to Use Docker
- For running full integration tests
- Testing production-like environment
- When tests require Nginx or full stack

### Docker Commands
```bash
# Start development environment
docker-compose up -d --build

# Execute commands in container
docker exec django python3 manage.py test
docker exec django coverage run manage.py test

# View logs
docker logs django

# Stop and clean
docker-compose down --volumes --remove-orphans
```

## OpenAI Integration Notes

- API key required in environment: `OPENAI_API_KEY`
- Model used: `gpt-4o`
- Max tokens: 15000 (defined in views.py)
- Client initialized at module level: `client = OpenAI(api_key=settings.OPENAI_API_KEY)`
- System prompts are long and use textwrap.dedent() for readability
- AI calls in: ChatView (conversation), RestartChat (regenerate session), KeyQuestionsView (generate questions)

## File Upload Processing

When working with file upload features:
- PDF extraction: pymupdf4llm library
- DOCX extraction: python-docx library
- File type validation: filetype library
- Files saved to media/uploads/ directory
- Text content extracted and stored in model.content field
- Original filename preserved in model.original_filename field

## Error Handling

If you encounter errors:
1. **Test failures**: Read the full traceback, identify the failing assertion, fix root cause
2. **Import errors**: Check requirements.txt, verify file structure
3. **Migration errors**: Check for conflicting migrations, try `--merge` if needed
4. **Docker errors**: Check logs with `docker logs django`, verify .env file exists
5. **Coverage failures**: Write tests for uncovered code, check .coveragerc for exclusions

## Reporting Results

Your final report should include:
- **Summary**: What you accomplished in 2-3 sentences
- **Files changed**: List with file:line references for key changes
- **Tests**: Did tests pass? Coverage percentage?
- **Verification**: How did you verify your work?
- **Issues**: Any blockers or problems encountered?
- **Next steps**: What remains to be done (if task is incomplete)?

### Good Report Example
```
Successfully implemented user profile export feature.

Files changed:
- active_interview_backend/active_interview_app/views.py:456 - Added ProfileExportView
- active_interview_backend/active_interview_app/urls.py:34 - Added /profile/export/ route
- active_interview_backend/active_interview_app/tests/test_profile.py:89 - Added test_profile_export

Tests: All passed (45 tests). Coverage: 84% (above 80% requirement).
Linting: No flake8 or djlint errors.

Verification: Tested export functionality manually and with automated test.
```

### Poor Report Example
```
I made some changes to the views file and added stuff. It might work but I'm not sure. There were some errors but I tried to fix them.
```

## Special Considerations

### Static Files
If you modify CSS, JavaScript, or images:
1. Delete `active_interview_backend/staticfiles/` directory
2. Run `python3 manage.py collectstatic --noinput`
3. Restart server/container

### Security
- Never commit secrets or API keys
- Use environment variables for sensitive data
- Validate user input in forms
- Use Django's built-in CSRF protection

### Performance
- OpenAI API calls are expensive - avoid unnecessary calls during testing
- Consider using test fixtures or mocks for AI functionality in tests
- Database is SQLite - suitable for development but be aware of limitations

## Getting Unstuck

If you're stuck:
1. Read CLAUDE.md for architecture overview
2. Search for similar existing functionality (e.g., grep for similar view patterns)
3. Check Django documentation for framework-specific questions
4. Look at test files to understand expected behavior
5. Use Glob to find relevant files, Grep to find code patterns
6. Read the full context of files, not just snippets
