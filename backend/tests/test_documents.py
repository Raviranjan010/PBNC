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

@pytest.mark.asyncio
async def test_upload_sample_exam_with_key_no_leak(client: AsyncClient, test_user_a: dict):
    sample_path = os.path.join("samples", "sample_exam_with_key.pdf")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample_exam_with_key.pdf", file_bytes, "application/pdf")},
        headers=test_user_a["headers"]
    )
    assert response.status_code == 202
    doc_id = response.json()["document_id"]

    # Check questions endpoint
    q_res = await client.get(f"/api/v1/documents/{doc_id}/questions", headers=test_user_a["headers"])
    assert q_res.status_code == 200
    questions = q_res.json()
    assert len(questions) == 2

    for q in questions:
        assert "Answer Key" not in q["question_text"]
        assert "---" not in q["question_text"]
        for opt in q["options"]:
            assert "Answer Key" not in opt["option_text"]
            assert "---" not in opt["option_text"]

    q2 = next(q for q in questions if q["question_number"] == "2")
    opt_d = next(o for o in q2["options"] if o["option_key"] == "D")
    assert opt_d["option_text"] == "Telnet"

    # Check answers endpoint
    ans_res = await client.get(f"/api/v1/documents/{doc_id}/answers", headers=test_user_a["headers"])
    assert ans_res.status_code == 200
    answers = ans_res.json()
    assert answers["answer_key_found"] is True
    mappings = {item["question_number"]: item["assigned_answer"] for item in answers["matrix"]}
    assert mappings.get("1") == "A"
    assert mappings.get("2") == "C"

