"""
Mutmut Configuration for Active Interview Backend
Controls which files and code sections should be mutated.
"""

def pre_mutation(context):
    """
    Filter mutations before they are applied.
    Skip certain files and patterns that shouldn't be mutated.

    Args:
        context: Mutation context with filename, line info, etc.
    """
    # Skip migrations - these are auto-generated
    if 'migrations' in context.filename:
        context.skip = True
        return

    # Skip __init__.py files - usually just imports
    if context.filename.endswith('__init__.py'):
        context.skip = True
        return

    # Skip test files - we're testing the tests, not testing tests themselves
    if '/tests/' in context.filename or '/test_' in context.filename:
        context.skip = True
        return

    if context.filename.endswith('test.py') or context.filename.endswith('tests.py'):
        context.skip = True
        return

    # Skip configuration files
    config_files = ['settings.py', 'wsgi.py', 'asgi.py', 'manage.py', 'urls.py']
    for config_file in config_files:
        if context.filename.endswith(config_file):
            context.skip = True
            return

    # Skip admin.py - mostly Django registration code
    if context.filename.endswith('admin.py'):
        context.skip = True
        return

    # Skip apps.py - Django app configuration
    if context.filename.endswith('apps.py'):
        context.skip = True
        return
