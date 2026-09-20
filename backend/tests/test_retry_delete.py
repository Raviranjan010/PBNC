import os
import pytest
from httpx import AsyncClient
from backend.app.models.document import Document
from backend.app.models.question import Question
from backend.tests.conftest import TestAsyncSessionLocal

@pytest.mark.asyncio
async def test_retry_document_success(client: AsyncClient, test_user_a: dict):
    headers = test_user_a["headers"]

    # Upload document
    sample_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(sample_path, "rb") as f:
        res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_digital_exam.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    assert res.status_code == 202
    doc_id = res.json()["document_id"]

    # Set status to REVIEW_REQUIRED so it is retryable
    async with TestAsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        doc.status = "REVIEW_REQUIRED"
        await session.commit()

    # Call POST /api/v1/documents/{id}/retry
    retry_res = await client.post(f"/api/v1/documents/{doc_id}/retry", headers=headers)
    assert retry_res.status_code == 202
    retry_data = retry_res.json()
    assert retry_data["document_id"] == doc_id
    assert retry_data["status"] == "QUEUED"
    assert "retry" in retry_data["message"].lower()

@pytest.mark.asyncio
async def test_retry_completed_document_conflict(client: AsyncClient, test_user_a: dict):
    headers = test_user_a["headers"]

    sample_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(sample_path, "rb") as f:
        res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_digital_exam.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    doc_id = res.json()["document_id"]

    # Set status to COMPLETED with high confidence
    async with TestAsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        doc.status = "COMPLETED"
        doc.average_confidence = 0.95
        await session.commit()

    # Attempt retry should return 409
    retry_res = await client.post(f"/api/v1/documents/{doc_id}/retry", headers=headers)
    assert retry_res.status_code == 409
    assert "already completed" in retry_res.json()["detail"]

@pytest.mark.asyncio
async def test_retry_and_delete_cross_user_forbidden(client: AsyncClient, test_user_a: dict, test_user_b: dict):
    # User A uploads document
    sample_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(sample_path, "rb") as f:
        res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_digital_exam.pdf", f.read(), "application/pdf")},
            headers=test_user_a["headers"]
        )
    doc_id = res.json()["document_id"]

    # User B attempts to retry -> 404 (not found in User B's scope)
    retry_res = await client.post(f"/api/v1/documents/{doc_id}/retry", headers=test_user_b["headers"])
    assert retry_res.status_code in [403, 404]

    # User B attempts to delete -> 404
    del_res = await client.delete(f"/api/v1/documents/{doc_id}", headers=test_user_b["headers"])
    assert del_res.status_code in [403, 404]

@pytest.mark.asyncio
async def test_delete_document_success(client: AsyncClient, test_user_a: dict):
    headers = test_user_a["headers"]

    sample_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(sample_path, "rb") as f:
        res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_digital_exam.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    doc_id = res.json()["document_id"]

    # Ensure questions exist
    q_res = await client.get(f"/api/v1/documents/{doc_id}/questions", headers=headers)
    assert q_res.status_code == 200
    assert q_res.json()["total"] > 0

    # Delete document
    del_res = await client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 204

    # Document should no longer exist
    get_res = await client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 404

    # Cascading check: questions should no longer exist in DB
    from sqlalchemy.future import select
    async with TestAsyncSessionLocal() as session:
        stmt = select(Question).where(Question.document_id == doc_id)
        qs = (await session.execute(stmt)).scalars().all()
        assert len(qs) == 0
