"""Test configuration and fixtures."""
import pytest
import os
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from fastapi.testclient import TestClient
from unittest.mock import Mock

# Mock LM Studio to avoid dependency on external service
@pytest.fixture(autouse=True)
def mock_lm_studio():
    """Mock LM Studio client for all tests."""
    from ai.lm_studio_client import LMStudioClient
    
    # Store original methods
    original_is_available = LMStudioClient.is_available
    original_categorize = LMStudioClient.categorize_article
    original_summarize = LMStudioClient.summarize_article
    
    # Mock the methods
    LMStudioClient.is_available = Mock(return_value=True)
    LMStudioClient.categorize_article = Mock(return_value={
        "category": "technology",
        "sentiment": "neutral",
        "importance": "medium",
        "topics": ["AI", "Testing"],
        "confidence": 0.9,
        "political_bias": 0.1,
        "bias_confidence": 0.8,
        "bias_reasoning": "Mostly neutral with slight positive sentiment toward technology."
    })
    LMStudioClient.summarize_article = Mock(return_value="Test summary of the article content.")
    
    yield
    
    # Restore original methods
    LMStudioClient.is_available = original_is_available
    LMStudioClient.categorize_article = original_categorize
    LMStudioClient.summarize_article = original_summarize

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from backend.main import app
    return TestClient(app)

@pytest.fixture
def test_db():
    """Create a test database."""
    from database.models import DatabaseManager
    import sqlite3
    
    # Use in-memory database for tests
    test_db_path = ":memory:"
    db = DatabaseManager(test_db_path)
    
    # Create connection attribute for tests that need it
    db.connection = sqlite3.connect(test_db_path)
    
    return db