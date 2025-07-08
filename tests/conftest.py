import pytest
from src.db import init_db


@pytest.fixture(autouse=True)
def setup_database():
    """Automatically initialize the database before each test"""
    init_db()
    yield
    # Cleanup could be added here if needed 