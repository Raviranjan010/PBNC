import pytest
import os
import uuid
from backend.app.core import database
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.job import ProcessingJob
from backend.app.models.question import Question
from backend.app.models.answer import AnswerKey
from backend.app.core.storage import storage
from backend.app.services.pipeline import ExtractionPipeline

def test_pipeline_digital_exam():
    db = database.SyncSessionLocal()
    try:
        # Create a test document record
        user_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        sample_path = os.path.join("samples", "sample_digital_exam.pdf")
        with open(sample_path, "rb") as f:
            content = f.read()

        import asyncio
        rel_path, size = asyncio.run(storage.save_file(content, user_id, doc_id, "sample_digital_exam.pdf"))

        user = User(id=user_id, email=f"pipe_{user_id[:6]}@test.com", hashed_password="pwd", is_active=True)
        db.add(user)
        
        doc = Document(
            id=doc_id, user_id=user_id, filename="sample_digital_exam.pdf",
            original_filename="sample_digital_exam.pdf", file_type="pdf",
            mime_type="application/pdf", file_size_bytes=size, storage_path=rel_path
        )
        db.add(doc)

        job = ProcessingJob(id=job_id, document_id=doc_id, status="QUEUED", current_step="QUEUED", step_details=[])
        db.add(job)
        db.commit()

        # Run pipeline
        ExtractionPipeline.execute_pipeline(db, doc_id, job_id)

        # Verify results
        db.refresh(doc)
        db.refresh(job)
        assert job.status in ["COMPLETED", "PARTIAL", "REVIEW_REQUIRED"]
        assert doc.page_count == 2
        
        questions = db.query(Question).filter(Question.document_id == doc_id).all()
        assert len(questions) >= 3
        
        # Verify question 1
        q1 = next((q for q in questions if q.question_number == "1"), None)
        assert q1 is not None
        assert "Normalization" in q1.question_text
        assert len(q1.options) == 4
        assert q1.source_pages == [1]

    finally:
        db.close()

def test_pipeline_multipage_question():
    db = database.SyncSessionLocal()
    try:
        user_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())

        sample_path = os.path.join("samples", "sample_multipage_question.pdf")
        with open(sample_path, "rb") as f:
            content = f.read()

        import asyncio
        rel_path, size = asyncio.run(storage.save_file(content, user_id, doc_id, "sample_multipage_question.pdf"))

        user = User(id=user_id, email=f"pipe_mp_{user_id[:6]}@test.com", hashed_password="pwd", is_active=True)
        db.add(user)

        doc = Document(
            id=doc_id, user_id=user_id, filename="sample_multipage_question.pdf",
            original_filename="sample_multipage_question.pdf", file_type="pdf",
            mime_type="application/pdf", file_size_bytes=size, storage_path=rel_path
        )
        db.add(doc)

        job = ProcessingJob(id=job_id, document_id=doc_id, status="QUEUED", current_step="QUEUED", step_details=[])
        db.add(job)
        db.commit()

        ExtractionPipeline.execute_pipeline(db, doc_id, job_id)

        questions = db.query(Question).filter(Question.document_id == doc_id).all()
        # Question 2 spans across pages 1 and 2
        q2 = next((q for q in questions if q.question_number == "2"), None)
        assert q2 is not None
        assert 1 in q2.source_pages
        assert 2 in q2.source_pages

    finally:
        db.close()

def test_pipeline_answer_key_association():
    db = database.SyncSessionLocal()
    try:
        user_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())

        sample_path = os.path.join("samples", "sample_exam_with_key.pdf")
        with open(sample_path, "rb") as f:
            content = f.read()

        import asyncio
        rel_path, size = asyncio.run(storage.save_file(content, user_id, doc_id, "sample_exam_with_key.pdf"))

        user = User(id=user_id, email=f"pipe_ak_{user_id[:6]}@test.com", hashed_password="pwd", is_active=True)
        db.add(user)

        doc = Document(
            id=doc_id, user_id=user_id, filename="sample_exam_with_key.pdf",
            original_filename="sample_exam_with_key.pdf", file_type="pdf",
            mime_type="application/pdf", file_size_bytes=size, storage_path=rel_path
        )
        db.add(doc)

        job = ProcessingJob(id=job_id, document_id=doc_id, status="QUEUED", current_step="QUEUED", step_details=[])
        db.add(job)
        db.commit()

        ExtractionPipeline.execute_pipeline(db, doc_id, job_id)

        ak = db.query(AnswerKey).filter(AnswerKey.document_id == doc_id).first()
        assert ak is not None
        assert "1" in ak.parsed_mappings
        assert ak.parsed_mappings["1"] == "A"

        questions = db.query(Question).filter(Question.document_id == doc_id).all()
        q1 = next((q for q in questions if q.question_number == "1"), None)
        assert q1 is not None
        assert q1.answer == "A"
        assert q1.answer_status == "CONFIRMED"

        q2 = next((q for q in questions if q.question_number == "2"), None)
        assert q2 is not None
        assert q2.answer == "C"
        assert q2.answer_status == "CONFIRMED"
        opt_d = next((o for o in q2.options if o.option_key == "D"), None)
        assert opt_d is not None
        assert opt_d.option_text == "Telnet"

    finally:
        db.close()

def test_heuristic_parser_no_answer_key_leak():
    import fitz
    import asyncio
    from backend.app.services.ai.heuristic import HeuristicProvider

    sample_path = os.path.join("samples", "sample_exam_with_key.pdf")
    doc = fitz.open(sample_path)
    pages = [{"page_number": i + 1, "text": page.get_text()} for i, page in enumerate(doc)]
    
    hp = HeuristicProvider()
    questions = asyncio.run(hp.extract_structured_questions(pages))
    
    assert len(questions) == 2
    for q in questions:
        assert "Answer Key" not in q.question_text
        assert "---" not in q.question_text
        for opt in q.options:
            assert "Answer Key" not in opt.text
            assert "---" not in opt.text
            assert not opt.text.endswith(":")

    q2 = next(q for q in questions if q.question_number == "2")
    opt_d = next(o for o in q2.options if o.key == "D")
    assert opt_d.text == "Telnet"
