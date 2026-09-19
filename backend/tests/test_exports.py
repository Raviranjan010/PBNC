import pytest
import uuid
import csv
import io
import json
from httpx import AsyncClient
from backend.tests.conftest import TestAsyncSessionLocal
from backend.app.models.document import Document
from backend.app.models.question import Question, QuestionOption

@pytest.mark.asyncio
async def test_export_json_and_csv(client: AsyncClient, test_user_a: dict):
    doc_id = str(uuid.uuid4())
    q_id = str(uuid.uuid4())

    async with TestAsyncSessionLocal() as session:
        doc = Document(
            id=doc_id, user_id=test_user_a["id"], filename="export_test.pdf",
            original_filename="export_test.pdf", file_type="pdf", mime_type="application/pdf",
            file_size_bytes=1200, page_count=1, storage_path="path", status="COMPLETED",
            average_confidence=0.95
        )
        session.add(doc)

        q = Question(
            id=q_id, document_id=doc_id, question_number="1",
            question_text="Sample export question?", question_type="MCQ",
            answer="C", answer_status="CONFIRMED", confidence=0.95,
            status="VERIFIED", review_required=False, is_reviewed=True,
            source_pages=[1]
        )
        session.add(q)
        opt = QuestionOption(id=str(uuid.uuid4()), question_id=q_id, option_key="C", option_text="Correct answer")
        session.add(opt)
        await session.commit()

    # Test JSON Export
    json_res = await client.get(f"/api/v1/documents/{doc_id}/export/json", headers=test_user_a["headers"])
    assert json_res.status_code == 200
    assert "application/json" in json_res.headers["content-type"]
    json_body = json.loads(json_res.text)
    assert json_body["document_id"] == doc_id
    assert len(json_body["questions"]) == 1
    assert json_body["questions"][0]["answer"] == "C"

    # Test CSV Export
    csv_res = await client.get(f"/api/v1/documents/{doc_id}/export/csv", headers=test_user_a["headers"])
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    reader = csv.reader(io.StringIO(csv_res.text))
    rows = list(reader)
    assert len(rows) == 2  # Header + 1 question row
    assert rows[0][0] == "Question Number"
    assert rows[1][0] == "1"
    assert rows[1][4] == "C"
