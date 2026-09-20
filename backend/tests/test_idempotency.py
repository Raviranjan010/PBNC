import os
import pytest
from httpx import AsyncClient
from backend.app.models.question import Question
from backend.app.models.job import ProcessingJob
from backend.app.services.pipeline import ExtractionPipeline
from backend.tests.conftest import TestAsyncSessionLocal, test_sync_engine
from sqlalchemy.orm import sessionmaker

@pytest.mark.asyncio
async def test_pipeline_idempotency_duplicate_redelivery(client: AsyncClient, test_user_a: dict):
    """
    Verifies Defect P1-2:
    Simulates calling ExtractionPipeline.execute_pipeline twice for the same document/job,
    and asserts that the question count does not double.
    """
    headers = test_user_a["headers"]
    sample_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(sample_path, "rb") as f:
        upload_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_digital_exam.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    assert upload_res.status_code == 202
    doc_id = upload_res.json()["document_id"]
    job_id = upload_res.json()["job_id"]

    # In eager test mode, execute_pipeline has already run once
    q_res1 = await client.get(f"/api/v1/documents/{doc_id}/questions", headers=headers)
    assert q_res1.status_code == 200
    initial_count = q_res1.json()["total"]
    assert initial_count == 4

    # Now manually simulate Celery at-least-once redelivery calling execute_pipeline again
    SyncSession = sessionmaker(bind=test_sync_engine)
    with SyncSession() as sync_db:
        # Re-invoke execute_pipeline with the exact same doc_id and job_id
        ExtractionPipeline.execute_pipeline(sync_db, doc_id, job_id)

    # Verify questions did NOT double
    q_res2 = await client.get(f"/api/v1/documents/{doc_id}/questions", headers=headers)
    assert q_res2.status_code == 200
    after_count = q_res2.json()["total"]
    assert after_count == initial_count
