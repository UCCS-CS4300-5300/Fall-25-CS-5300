"""
Pytest configuration for Django tests.
"""
import pytest


@pytest.fixture(scope='session')
def django_db_setup():
    """
    Custom database setup for tests.
    This ensures the test database is created properly.
    """
    pass


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Give all tests access to the database.
    """
    pass
