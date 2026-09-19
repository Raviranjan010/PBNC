import pytest
import os
import uuid
from httpx import AsyncClient
from backend.tests.conftest import TestAsyncSessionLocal
from backend.app.models.document import Document
from backend.app.models.question import Question, QuestionOption
from backend.app.models.review import ReviewItem

@pytest.mark.asyncio
async def test_get_and_patch_question(client: AsyncClient, test_user_a: dict):
    doc_id = str(uuid.uuid4())
    q_id = str(uuid.uuid4())
    
    # Seed DB with a question needing review
    async with TestAsyncSessionLocal() as session:
        doc = Document(
            id=doc_id, user_id=test_user_a["id"], filename="test.pdf",
            original_filename="test.pdf", file_type="pdf", mime_type="application/pdf",
            file_size_bytes=1000, storage_path="path", status="REVIEW_REQUIRED"
        )
        session.add(doc)

        q = Question(
            id=q_id, document_id=doc_id, question_number="1",
            question_text="Old uncorrected question prompt?",
            question_type="MCQ", answer="B", answer_status="UNCERTAIN",
            confidence=0.62, status="REVIEW_REQUIRED", review_required=True,
            is_reviewed=False, source_pages=[1]
        )
        session.add(q)

        opt1 = QuestionOption(id=str(uuid.uuid4()), question_id=q_id, option_key="A", option_text="Option Alpha")
        opt2 = QuestionOption(id=str(uuid.uuid4()), question_id=q_id, option_key="B", option_text="Option Beta")
        session.add(opt1)
        session.add(opt2)

        rev_item = ReviewItem(
            id=str(uuid.uuid4()), document_id=doc_id, question_id=q_id,
            issue_type="UNCERTAIN_ANSWER", description="Flagged for manual review",
            is_resolved=False
        )
        session.add(rev_item)
        await session.commit()

    # 1. Fetch questions list
    res_list = await client.get(f"/api/v1/documents/{doc_id}/questions", headers=test_user_a["headers"])
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == q_id

    # 2. Human Review Workflow: PATCH question correction and approve
    patch_res = await client.patch(
        f"/api/v1/questions/{q_id}",
        json={
            "question_text": "Corrected and verified question prompt?",
            "answer": "A",
            "status": "VERIFIED",
            "review_required": False,
            "is_reviewed": True,
            "options": [
                {"option_key": "A", "option_text": "Correct Option A"},
                {"option_key": "B", "option_text": "Incorrect Option B"}
            ]
        },
        headers=test_user_a["headers"]
    )
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["question_text"] == "Corrected and verified question prompt?"
    assert patched_data["answer"] == "A"
    assert patched_data["status"] == "VERIFIED"
    assert patched_data["review_required"] is False
    assert patched_data["is_reviewed"] is True

    # 3. Verify changes persist on direct GET
    get_res = await client.get(f"/api/v1/questions/{q_id}", headers=test_user_a["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["question_text"] == "Corrected and verified question prompt?"
