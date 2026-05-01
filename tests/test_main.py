import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Test database
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/marble_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)


def override_get_db():
    """Override dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True, scope="function")
def setup_and_teardown():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Marble" in response.json()["message"]


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database_connected" in data


def test_create_research_session():
    response = client.post(
        "/research/",
        json={"user_query": "Test query"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "final_output" in data
    assert "steps" in data


def test_get_research_session():
    # Create first
    create_resp = client.post(
        "/research/",
        json={"user_query": "Another test query"},
    )
    session_id = create_resp.json()["session_id"]

    # Get it
    response = client.get(f"/research/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["user_query"] == "Another test query"


def test_list_research_sessions():
    response = client.get("/research/?skip=0&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_nonexistent_session():
    response = client.get("/research/99999")
    assert response.status_code == 404
