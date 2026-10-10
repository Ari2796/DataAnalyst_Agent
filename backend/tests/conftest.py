"""Pytest fixtures for unit and integration testing."""

import sys
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.services.session_service import session_service


@pytest.fixture(autouse=True)
def clean_sessions():
    """Ensure clean session state for every test."""
    session_service._sessions.clear()
    yield
    session_service._sessions.clear()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_csv_path() -> Path:
    """Path to sample e-commerce CSV."""
    return BACKEND_DIR / "data" / "sample_ecommerce.csv"


@pytest.fixture
def sample_df(sample_csv_path) -> pd.DataFrame:
    """Loaded sample e-commerce DataFrame."""
    return pd.read_csv(sample_csv_path)
