import pytest
import os
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upload_valid_pdf(client: AsyncClient, test_user_a: dict):
    sample_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample_digital_exam.pdf", file_bytes, "application/pdf")},
        headers=test_user_a["headers"]
    )
    assert response.status_code == 202
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "QUEUED"

@pytest.mark.asyncio
async def test_upload_valid_image(client: AsyncClient, test_user_a: dict):
    sample_path = os.path.join("samples", "sample_scanned_exam.png")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample_scanned_exam.png", file_bytes, "image/png")},
        headers=test_user_a["headers"]
    )
    assert response.status_code == 202
    data = response.json()
    assert "document_id" in data

@pytest.mark.asyncio
async def test_reject_malformed_file(client: AsyncClient, test_user_a: dict):
    sample_path = os.path.join("samples", "sample_malformed.pdf")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample_malformed.pdf", file_bytes, "application/pdf")},
        headers=test_user_a["headers"]
    )
    assert response.status_code == 400
    assert "Unsupported or unrecognized file format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_reject_empty_file(client: AsyncClient, test_user_a: dict):
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
        headers=test_user_a["headers"]
    )
    assert response.status_code == 400
