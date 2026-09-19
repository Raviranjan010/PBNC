import os
import sys
import uuid
import asyncio
import httpx
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import Base, async_engine

# Enable eager execution for immediate background job completion
settings.CELERY_TASK_ALWAYS_EAGER = True

async def run_e2e_verification():
    print("==========================================================")
    print("  STARTING COMPREHENSIVE END-TO-END VERIFICATION")
    print("==========================================================")

    # Initialize tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[1/16] Database tables confirmed ready.")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        assert res.json()["status"] == "healthy"
        print("[2/16] /health check passed: 200 OK, healthy.")

        # 2. Register User 1
        user_email = f"e2e_user_{uuid.uuid4().hex[:6]}@papermind.io"
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": user_email,
            "password": "Password123!",
            "full_name": "E2E Lead Auditor"
        })
        assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
        user_id = reg_res.json()["id"]
        print(f"[3/16] User 1 registered successfully: {user_email} (ID: {user_id})")

        # 3. Login User 1
        login_res = await client.post("/api/v1/auth/login", json={
            "email": user_email,
            "password": "Password123!"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[4/16] User 1 login passed, JWT token issued.")

        # 4. Profile /me
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == user_email
        print("[5/16] Profile /auth/me verified.")

        # 5. Upload sample_digital_exam.pdf
        sample_exam_path = os.path.join("samples", "sample_digital_exam.pdf")
        with open(sample_exam_path, "rb") as f:
            pdf_bytes = f.read()

        up_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_digital_exam.pdf", pdf_bytes, "application/pdf")},
            headers=headers
        )
        assert up_res.status_code == 202, f"Upload failed: {up_res.text}"
        doc1_id = up_res.json()["document_id"]
        print(f"[6/16] Digital exam uploaded: HTTP 202 (Document ID: {doc1_id})")

        # 6. Verify processing status transitions
        stat_res = await client.get(f"/api/v1/documents/{doc1_id}/status", headers=headers)
        assert stat_res.status_code == 200
        stat_json = stat_res.json()
        print(f"[7/16] Processing status: {stat_json['status']}, steps: {len(stat_json['step_details'])}")

        # 7. Verify Document Details
        doc_res = await client.get(f"/api/v1/documents/{doc1_id}", headers=headers)
        assert doc_res.status_code == 200
        doc_json = doc_res.json()
        assert doc_json["page_count"] == 2
        assert doc_json["questions_count"] >= 3
        print(f"[8/16] Document details verified: {doc_json['page_count']} pages, {doc_json['questions_count']} questions.")

        # 8. Verify Page Image Rendering (Original Document Viewer)
        page_img_res = await client.get(f"/api/v1/documents/{doc1_id}/pages/1", headers=headers)
        assert page_img_res.status_code == 200
        assert "image/png" in page_img_res.headers["content-type"]
        assert len(page_img_res.content) > 1000
        print("[9/16] Source page 1 image rendered and verified (PNG bytes).")

        # 9. Verify Questions and Options extraction
        q_res = await client.get(f"/api/v1/documents/{doc1_id}/questions", headers=headers)
        assert q_res.status_code == 200
        q_json = q_res.json()
        assert q_json["total"] >= 3
        q1 = next((q for q in q_json["items"] if q["question_number"] == "1"), None)
        assert q1 is not None
        assert "Normalization" in q1["question_text"]
        assert len(q1["options"]) == 4
        print(f"[10/16] Extracted questions verified: Q1 options {len(q1['options'])}, confidence {q1['confidence']}.")

        # 10. Upload sample_multipage_question.pdf & verify multi-page tracking
        mp_path = os.path.join("samples", "sample_multipage_question.pdf")
        with open(mp_path, "rb") as f:
            mp_bytes = f.read()

        up_mp_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_multipage_question.pdf", mp_bytes, "application/pdf")},
            headers=headers
        )
        assert up_mp_res.status_code == 202
        mp_doc_id = up_mp_res.json()["document_id"]
        
        mp_q_res = await client.get(f"/api/v1/documents/{mp_doc_id}/questions", headers=headers)
        mp_q_json = mp_q_res.json()
        q_mp = next((q for q in mp_q_json["items"] if q["question_number"] == "2"), None)
        assert q_mp is not None, "Question 2 spanning pages not found"
        assert 1 in q_mp["source_pages"] and 2 in q_mp["source_pages"], f"Expected source_pages [1,2], got {q_mp['source_pages']}"
        print(f"[11/16] Multi-page question tracking verified: Q2 source_pages={q_mp['source_pages']}.")

        # 11. Upload sample_exam_with_key.pdf & verify Answer Key association
        ak_path = os.path.join("samples", "sample_exam_with_key.pdf")
        with open(ak_path, "rb") as f:
            ak_bytes = f.read()

        up_ak_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_exam_with_key.pdf", ak_bytes, "application/pdf")},
            headers=headers
        )
        assert up_ak_res.status_code == 202
        ak_doc_id = up_ak_res.json()["document_id"]

        ans_keys_res = await client.get(f"/api/v1/documents/{ak_doc_id}/answers", headers=headers)
        assert ans_keys_res.status_code == 200
        ans_keys_json = ans_keys_res.json()
        assert len(ans_keys_json) > 0, "No answer key detected in sample_exam_with_key.pdf"
        assert "1" in ans_keys_json[0]["parsed_mappings"]
        print(f"[12/16] Answer key association verified: Q1 -> {ans_keys_json[0]['parsed_mappings']['1']}.")

        # 12. Human Review Workflow: PATCH question correction & approval
        q1_id = q1["id"]
        patch_res = await client.patch(
            f"/api/v1/questions/{q1_id}",
            json={
                "question_text": "Updated and human-verified question prompt?",
                "answer": "A",
                "status": "VERIFIED",
                "review_required": False,
                "is_reviewed": True,
            },
            headers=headers
        )
        assert patch_res.status_code == 200
        patched_q = patch_res.json()
        assert patched_q["question_text"] == "Updated and human-verified question prompt?"
        assert patched_q["is_reviewed"] is True
        assert patched_q["review_required"] is False
        print("[13/16] Human Review Workflow verified: PATCH question persisted to DB.")

        # 13. Live Exports: JSON and CSV
        exp_json = await client.get(f"/api/v1/documents/{doc1_id}/export/json", headers=headers)
        assert exp_json.status_code == 200
        assert "application/json" in exp_json.headers["content-type"]
        
        exp_csv = await client.get(f"/api/v1/documents/{doc1_id}/export/csv", headers=headers)
        assert exp_csv.status_code == 200
        assert "text/csv" in exp_csv.headers["content-type"]
        assert "Question Number" in exp_csv.text
        print("[14/16] Live JSON and CSV export generation verified.")

        # 14. Analytics
        ana_res = await client.get("/api/v1/analytics", headers=headers)
        assert ana_res.status_code == 200
        ana_json = ana_res.json()
        assert ana_json["total_documents"] >= 3
        assert ana_json["total_questions"] >= 5
        print(f"[15/16] Analytics verified: {ana_json['total_documents']} documents, {ana_json['total_questions']} questions.")

        # 15. Security Isolation (User 2 attempts to access User 1's document)
        user2_email = f"user2_{uuid.uuid4().hex[:6]}@papermind.io"
        await client.post("/api/v1/auth/register", json={
            "email": user2_email,
            "password": "Password123!",
            "full_name": "Intruder"
        })
        l2_res = await client.post("/api/v1/auth/login", json={"email": user2_email, "password": "Password123!"})
        u2_headers = {"Authorization": f"Bearer {l2_res.json()['access_token']}"}

        cross_res = await client.get(f"/api/v1/documents/{doc1_id}", headers=u2_headers)
        assert cross_res.status_code == 403, f"Expected 403 Forbidden on cross-user access, got {cross_res.status_code}"

        # 16. Invalid file rejection
        bad_res = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("bad.pdf", b"NOT A PDF FILE", "application/pdf")},
            headers=headers
        )
        assert bad_res.status_code == 400
        print("[16/16] Multi-tenant cross-user security isolation & invalid file rejection verified.")

    print("==========================================================")
    print("  ALL 16 END-TO-END SYSTEM CHECKS PASSED WITH ZERO DEFECTS!")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(run_e2e_verification())
