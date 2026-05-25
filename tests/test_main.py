"""
Tests for the FastAPI document-processing endpoints.
Uses a dedicated test database so the real DB is never touched.
"""
import pytest
from fastapi.testclient import TestClient
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force test database before any module imports
os.environ["DATABASE_URL"] = "sqlite:///./test_marble.db"

from main import app
from database import Base, engine, get_db


client = TestClient(app)


@pytest.fixture(autouse=True, scope="function")
def setup_and_teardown():
    """Recreate all tables before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_list_docs_empty():
    response = client.get("/documents")
    assert response.status_code == 200
    assert response.json() == []


def test_get_nonexistent_doc():
    response = client.get("/documents/999")
    assert response.status_code == 404


def test_upload_txt():
    content = b"Hello world from test file."
    response = client.post("/upload", files={"file": ("test_hello.txt", content, "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["filename"] == "test_hello.txt"
    assert data["size"] > 0


def test_upload_and_list():
    client.post("/upload", files={"file": ("list_test.txt", b"Some content.", "text/plain")})
    response = client.get("/documents")
    assert response.status_code == 200
    docs = response.json()
    assert any(d["filename"] == "list_test.txt" for d in docs)


def test_upload_and_retrieve():
    resp = client.post("/upload", files={"file": ("retrieve_test.txt", b"This is unique doc content 42.", "text/plain")})
    doc_id = resp.json()["id"]

    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "retrieve_test.txt"
    assert "unique doc content" in data["text"]


def test_delete_doc():
    resp = client.post("/upload", files={"file": ("delete_test.txt", b"To be deleted.", "text/plain")})
    doc_id = resp.json()["id"]

    response = client.delete(f"/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] == doc_id

    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 404


def test_delete_nonexistent():
    response = client.delete("/documents/9999")
    assert response.status_code == 404


def test_extract_existing():
    response = client.post("/extract-existing")
    assert response.status_code == 200
    data = response.json()
    assert "processed" in data