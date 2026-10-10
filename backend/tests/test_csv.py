"""Unit and integration tests for CSV upload, validation, and encoding resilience."""

import io
from fastapi.testclient import TestClient


def test_valid_csv_upload(client: TestClient, sample_csv_path):
    """Verifies that a valid e-commerce CSV uploads successfully and returns a profile."""
    with open(sample_csv_path, "rb") as f:
        response = client.post(
            "/api/datasets/upload",
            files={"file": ("ecommerce_sales.csv", f, "text/csv")},
        )
    assert response.status_code == 201
    data = response.json()
    assert "dataset_id" in data
    assert data["filename"] == "ecommerce_sales.csv"
    assert data["row_count"] > 30
    assert data["column_count"] == 10
    assert len(data["columns"]) == 10
    assert "revenue" in data["semantic_mappings"]
    assert "order_date" in data["semantic_mappings"]


def test_invalid_file_extension(client: TestClient):
    """Verifies rejection of non-CSV extensions."""
    file_content = b"header1,header2\nval1,val2\n"
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("malicious_script.sh", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 400
    assert "Only .csv files are supported" in response.json()["detail"]


def test_empty_csv_upload(client: TestClient):
    """Verifies rejection of empty (0-byte) files."""
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert response.status_code == 400
    assert "empty (0 bytes)" in response.json()["detail"]


def test_file_size_limit_enforcement(client: TestClient, monkeypatch):
    """Verifies rejection when file size exceeds configured max limit."""
    from app.config import settings
    monkeypatch.setattr(settings, "max_upload_size_mb", 0.0001)  # ~100 bytes

    large_content = b"col1,col2\n" + b"123,456\n" * 50
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("too_large.csv", io.BytesIO(large_content), "text/csv")},
    )
    assert response.status_code == 413
    assert "exceeds maximum allowed limit" in response.json()["detail"]


def test_csv_with_missing_values_and_latin_encoding(client: TestClient):
    """Verifies handling of Latin-1 encoded CSV with missing/null values."""
    latin_csv = "order_id;category;amount\nORD-1;Café;19.99\nORD-2;;25.00\nORD-3;Thé;\n".encode("latin1")
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("latin_sales.csv", io.BytesIO(latin_csv), "text/csv")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["row_count"] == 3
    col_dict = {c["name"]: c for c in data["columns"]}
    assert "category" in col_dict
    assert col_dict["category"]["missing_count"] == 1
