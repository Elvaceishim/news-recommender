
import pytest
from unittest.mock import MagicMock
from app.api.main import app
from app.storage.db import get_db
from fastapi.testclient import TestClient
import numpy as np

# Mock the entire database session
@pytest.fixture
def mock_db_session():
    session = MagicMock()
    return session

# Override the get_db dependency
@pytest.fixture
def client(mock_db_session):
    def override_get_db():
        try:
            yield mock_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

# Mock SentenceTransformer to avoid loading heavy models
@pytest.fixture(autouse=True)
def mock_sentence_transformer(monkeypatch):
    class MockModel:
        def encode(self, texts, **kwargs):
            # Return random vectors of dimension 384 (standard MiniLM size)
            if isinstance(texts, str):
                return np.random.rand(384)
            return np.random.rand(len(texts), 384)
            
    import app.embeddings.embedder
    monkeypatch.setattr(app.embeddings.embedder.embedder, "model", MockModel())
