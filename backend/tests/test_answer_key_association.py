import os
import pytest
from httpx import AsyncClient
from backend.app.models.document import Document
from backend.app.models.question import Question, QuestionOption

@pytest.mark.asyncio
async def test_separate_answer_key_association_flow(client: AsyncClient, test_user_a: dict):
    """
    Verifies Defect P0-1 fix:
    Uploading a question paper (sample_digital_exam.pdf) with no embedded key,
    uploading separate answer key (sample_separate_answer_key.pdf),
    linking them via POST /documents/{id}/related,
    and verifying questions resolve to CONFIRMED with proper provenance.
    """
    headers = test_user_a["headers"]

    # 1. Upload Question Paper
    qp_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(qp_path, "rb") as f:
        qp_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_digital_exam.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    assert qp_res.status_code == 202
    qp_id = qp_res.json()["document_id"]

    # Verify initial question state has no answers
    q_initial = await client.get(f"/api/v1/documents/{qp_id}/questions", headers=headers)
    assert q_initial.status_code == 200
    initial_items = q_initial.json()["items"]
    assert len(initial_items) == 4
    for q in initial_items:
        assert q["answer"] is None
        assert q["answer_status"] == "NOT_FOUND"

    # 2. Upload Separate Answer Key
    ak_path = os.path.join("samples", "sample_separate_answer_key.pdf")
    with open(ak_path, "rb") as f:
        ak_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_separate_answer_key.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    assert ak_res.status_code == 202
    ak_id = ak_res.json()["document_id"]

    # 3. Associate Answer Key
    rel_res = await client.post(
        f"/api/v1/documents/{qp_id}/related",
        json={"related_document_id": ak_id, "relationship_type": "ANSWER_KEY"},
        headers=headers
    )
    assert rel_res.status_code == 200
    rel_data = rel_res.json()
    assert rel_data["resolved_count"] == 4
    assert rel_data["invalid_count"] == 0
    assert rel_data["unresolved_count"] == 0

    # 4. Verify questions now have CONFIRMED answers and provenance
    q_resolved = await client.get(f"/api/v1/documents/{qp_id}/questions", headers=headers)
    assert q_resolved.status_code == 200
    resolved_items = q_resolved.json()["items"]
    assert len(resolved_items) == 4

    expected_answers = {"1": "A", "2": "B", "3": "C", "4": "B"}
    for q in resolved_items:
        num = q["question_number"]
        assert q["answer"] == expected_answers[num]
        assert q["answer_status"] == "CONFIRMED"
        assert q["answer_source_document_id"] == ak_id
        assert q["answer_source_page"] == 1
        assert q["review_required"] is False

    # 5. Verify /answers endpoint returns the associated AnswerKey record
    ans_res = await client.get(f"/api/v1/documents/{qp_id}/answers", headers=headers)
    assert ans_res.status_code == 200
    ans_keys = ans_res.json()
    assert len(ans_keys) == 1
    assert ans_keys[0]["document_id"] == qp_id
    assert ans_keys[0]["parsed_mappings"] == expected_answers

@pytest.mark.asyncio
async def test_associate_answer_key_not_finished_processing(client: AsyncClient, test_user_a: dict):
    """
    Verifies that associating an answer key that is not completed returns 409 Conflict.
    """
    headers = test_user_a["headers"]

    # Create dummy question paper
    qp_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(qp_path, "rb") as f:
        qp_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_digital_exam.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    qp_id = qp_res.json()["document_id"]

    # Upload AK
    with open(qp_path, "rb") as f:
        ak_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("ak_temp.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    ak_id = ak_res.json()["document_id"]

    # Manually set ak doc status to PROCESSING
    from backend.tests.conftest import TestAsyncSessionLocal
    async with TestAsyncSessionLocal() as session:
        ak_doc = await session.get(Document, ak_id)
        ak_doc.status = "PROCESSING"
        await session.commit()

    rel_res = await client.post(
        f"/api/v1/documents/{qp_id}/related",
        json={"related_document_id": ak_id, "relationship_type": "ANSWER_KEY"},
        headers=headers
    )
    assert rel_res.status_code == 409
    assert "must finish processing before association" in rel_res.json()["detail"]

@pytest.mark.asyncio
async def test_associate_answer_key_invalid_option_mismatch(client: AsyncClient, test_user_a: dict):
    """
    Verifies Defect P1-3 in separate document context:
    When an answer key maps a question to an option key that does not exist in the question's options,
    the answer is NOT confirmed, status is marked INVALID, answer is None, review_required is True.
    """
    headers = test_user_a["headers"]

    qp_path = os.path.join("samples", "sample_digital_exam.pdf")
    with open(qp_path, "rb") as f:
        qp_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_digital_exam.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    qp_id = qp_res.json()["document_id"]

    # Modify Question 1 in DB so it only has options B, C, D (remove option A)
    from backend.tests.conftest import TestAsyncSessionLocal
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload

    async with TestAsyncSessionLocal() as session:
        stmt = select(Question).options(selectinload(Question.options)).where(
            Question.document_id == qp_id,
            Question.question_number == "1"
        )
        q1 = (await session.execute(stmt)).scalars().first()
        for opt in list(q1.options):
            if opt.option_key == "A":
                await session.delete(opt)
        await session.commit()

    # Upload answer key which maps Q1 -> A
    ak_path = os.path.join("samples", "sample_separate_answer_key.pdf")
    with open(ak_path, "rb") as f:
        ak_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_separate_answer_key.pdf", f.read(), "application/pdf")},
            headers=headers
        )
    ak_id = ak_res.json()["document_id"]

    # Associate
    rel_res = await client.post(
        f"/api/v1/documents/{qp_id}/related",
        json={"related_document_id": ak_id, "relationship_type": "ANSWER_KEY"},
        headers=headers
    )
    assert rel_res.status_code == 200
    data = rel_res.json()
    assert data["invalid_count"] == 1
    assert data["resolved_count"] == 3

    # Check Q1 in document questions
    q_res = await client.get(f"/api/v1/documents/{qp_id}/questions", headers=headers)
    questions = q_res.json()["items"]
    q1 = next(q for q in questions if q["question_number"] == "1")
    assert q1["answer"] is None
    assert q1["answer_status"] == "INVALID"
    assert q1["review_required"] is True
