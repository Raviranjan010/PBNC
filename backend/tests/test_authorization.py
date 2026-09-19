import pytest
import os
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_cross_user_document_isolation(client: AsyncClient, test_user_a: dict, test_user_b: dict):
    # User A uploads a real sample document
    sample_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    upload_res = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("exam_a.pdf", file_bytes, "application/pdf")},
        headers=test_user_a["headers"]
    )
    assert upload_res.status_code == 202
    doc_id = upload_res.json()["document_id"]

    # User A can access the document
    res_a = await client.get(f"/api/v1/documents/{doc_id}", headers=test_user_a["headers"])
    assert res_a.status_code == 200

    # User B attempts to access User A's document -> Must be 403 Forbidden!
    res_b = await client.get(f"/api/v1/documents/{doc_id}", headers=test_user_b["headers"])
    assert res_b.status_code == 403
    assert "forbidden" in res_b.json()["detail"].lower()

    # User B attempts to access status of User A's document -> 403 Forbidden
    res_status_b = await client.get(f"/api/v1/documents/{doc_id}/status", headers=test_user_b["headers"])
    assert res_status_b.status_code == 403

    # User B attempts to access questions of User A's document -> 403 Forbidden
    res_q_b = await client.get(f"/api/v1/documents/{doc_id}/questions", headers=test_user_b["headers"])
    assert res_q_b.status_code == 403
