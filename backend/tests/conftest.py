"""
Pytest configuration and fixtures for SmartCompile backend.
Configures an isolated in-memory or temporary SQLite database for tests.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Set environment before loading modules
os.environ["SMARTCOMPILE_DB_PATH"] = ":memory:"
os.environ["AI_PROVIDER"] = "mock"
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""

from backend.main import app
from backend.db.database import init_db, get_db_connection
from backend.config import settings
from backend.services.cache import cache_service

# Ensure settings object does not retain real keys loaded from .env during tests
settings.OPENAI_API_KEY = None
settings.GEMINI_API_KEY = None
settings.ANTHROPIC_API_KEY = None


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Ensure a fresh SQLite database for each test run."""
    db_file = str(tmp_path / "test_smartcompile.db")
    settings.DATABASE_PATH = db_file
    cache_service.db_path = db_file
    init_db(db_file)
    yield db_file


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client
