import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.document import Document, DocumentPage
from backend.app.models.job import ProcessingJob
from backend.app.models.question import Question, QuestionOption
from backend.app.models.answer import AnswerKey
from backend.app.models.review import ReviewItem, ExtractionWarning
from backend.app.core.storage import storage
from backend.app.services.pdf_processor import PDFProcessor
from backend.app.services.ocr_processor import OCRProcessor
from backend.app.services.ai import get_ai_provider
from backend.app.services.answer_matcher import AnswerMatcher, DetectedAnswerKey
from backend.app.services.confidence import ConfidenceCalculator
import asyncio

class ExtractionPipeline:
    @classmethod
    def update_job_step(cls, db: Session, job: ProcessingJob, step_name: str, message: str, status: str = "PROCESSING"):
        job.status = status
        job.current_step = step_name
        steps = list(job.step_details or [])
        steps.append({
            "step": step_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        job.step_details = steps
        db.commit()

    @classmethod
    def execute_pipeline(cls, db: Session, document_id: str, job_id: str) -> None:
        """
        Synchronous pipeline worker executor called by Celery or inline task runner.
        Follows strict pipeline order:
        Document Loading -> Page Text / OCR -> AI Extraction -> Answer Matching -> Confidence Calculation -> DB Persistence.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()

        if not doc or not job:
            return

        try:
            job.started_at = datetime.now(timezone.utc)
            cls.update_job_step(db, job, "INITIALIZING", "Pipeline initialized for document processing.")

            # Read document content from safe storage
            file_abs_path = storage.get_file_path(doc.storage_path)
            with open(file_abs_path, "rb") as f:
                content = f.read()

            # Step 1: Text extraction / rendering
            cls.update_job_step(db, job, "EXTRACTING_TEXT", "Extracting text layers and rendering page snapshots.")
            
            if doc.file_type == "pdf":
                pages_data = PDFProcessor.process_pdf(content)
            else:
                pages_data = [PDFProcessor.process_image(content)]

            doc.page_count = len(pages_data)
            db.commit()

            # Step 2: OCR if scanned pages exist
            cls.update_job_step(db, job, "OCR_PROCESSING", "Checking scanned pages and executing OCR where necessary.")
            
            saved_pages: List[DocumentPage] = []
            page_ocr_confidences: Dict[int, float] = {}
            has_scanned_pages = False

            for p in pages_data:
                # Save page image for the UI viewer
                img_rel_path = storage.save_page_image_sync(p.image_bytes, doc.id, p.page_number)
                ocr_text = ""
                ocr_conf = 1.0

                if p.is_scanned or not p.text:
                    has_scanned_pages = True
                    ocr_res = OCRProcessor.perform_ocr(p.image_bytes)
                    ocr_text = ocr_res.text
                    ocr_conf = ocr_res.confidence
                    page_ocr_confidences[p.page_number] = ocr_conf
                    
                    if ocr_res.warning:
                        warning = ExtractionWarning(
                            document_id=doc.id,
                            stage="OCR",
                            warning_code="OCR_DEGRADED",
                            message=f"Page {p.page_number}: {ocr_res.warning}",
                            severity="WARNING"
                        )
                        db.add(warning)
                else:
                    page_ocr_confidences[p.page_number] = 1.0

                doc_page = DocumentPage(
                    document_id=doc.id,
                    page_number=p.page_number,
                    extracted_text=p.text or ocr_text,
                    ocr_text=ocr_text if ocr_text else None,
                    width=p.width,
                    height=p.height,
                    image_path=img_rel_path,
                )
                db.add(doc_page)
                saved_pages.append(doc_page)

            db.commit()

            # Step 3: AI Structured Extraction
            cls.update_job_step(db, job, "EXTRACTING_QUESTIONS", "Extracting structured questions, options, and page provenance.")
            ai_provider = get_ai_provider()
            
            # Prepare page text payload
            pages_payload = [
                {"page_number": p.page_number, "text": p.extracted_text or ""}
                for p in saved_pages
            ]

            # Run async extraction provider safely in isolated thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                extracted_questions = executor.submit(
                    asyncio.run,
                    ai_provider.extract_structured_questions(pages_payload)
                ).result()

            # Step 4: Answer Key Matching
            cls.update_job_step(db, job, "MATCHING_ANSWERS", "Detecting answer keys and associating solutions.")
            
            # Check for inline or appendix answer keys
            detected_key = AnswerMatcher.find_answer_key_in_pages(pages_payload)
            if detected_key:
                ak_record = AnswerKey(
                    document_id=doc.id,
                    raw_key_text=detected_key.raw_text,
                    detected_format=detected_key.detected_format,
                    source_page=detected_key.source_page,
                    parsed_mappings=detected_key.mappings,
                )
                db.add(ak_record)
                db.commit()

            AnswerMatcher.associate_answers(extracted_questions, detected_key, doc.id)

            # Step 5: Confidence Calculation & Validation
            cls.update_job_step(db, job, "VALIDATING", "Evaluating multi-signal confidence scores and review requirements.")
            
            total_conf = 0.0
            review_required_count = 0
            created_questions: List[Question] = []

            for pq in extracted_questions:
                first_page = pq.source_pages[0] if pq.source_pages else 1
                ocr_conf = page_ocr_confidences.get(first_page, 1.0)
                is_dig = not has_scanned_pages

                conf = ConfidenceCalculator.calculate_question_confidence(
                    question=pq,
                    page_ocr_conf=ocr_conf,
                    is_digital=is_dig
                )
                total_conf += conf

                has_warns = bool(pq.warnings)
                is_uncert = pq.answer_status == "UNCERTAIN"
                status_val, rev_req = ConfidenceCalculator.determine_status_and_review(conf, has_warns, is_uncert)

                if rev_req:
                    review_required_count += 1

                q_record = Question(
                    document_id=doc.id,
                    question_number=pq.question_number,
                    question_text=pq.question_text,
                    question_type=pq.question_type,
                    answer=pq.answer,
                    answer_status=pq.answer_status,
                    answer_source_page=getattr(pq, 'answer_source_page', None),
                    answer_source_document_id=getattr(pq, 'answer_source_document_id', None),
                    confidence=conf,
                    status=status_val,
                    review_required=rev_req,
                    source_pages=pq.source_pages,
                )
                db.add(q_record)
                db.flush()  # populate q_record.id

                # Save Options
                for opt in pq.options:
                    opt_record = QuestionOption(
                        question_id=q_record.id,
                        option_key=opt.key,
                        option_text=opt.text,
                    )
                    db.add(opt_record)

                # Save warnings & review items
                for w_msg in pq.warnings:
                    warn = ExtractionWarning(
                        document_id=doc.id,
                        question_id=q_record.id,
                        stage="PARSING",
                        warning_code="QUESTION_WARNING",
                        message=w_msg,
                        severity="WARNING"
                    )
                    db.add(warn)

                if rev_req:
                    rev_item = ReviewItem(
                        document_id=doc.id,
                        question_id=q_record.id,
                        issue_type="UNCERTAIN_EXTRACTION" if is_uncert else "LOW_CONFIDENCE",
                        description=f"Question {pq.question_number} flagged for review (Confidence: {conf:.2f}). Issues: {', '.join(pq.warnings) if pq.warnings else 'Below confidence threshold'}",
                    )
                    db.add(rev_item)

                created_questions.append(q_record)

            # Final document status
            avg_conf = round(total_conf / len(extracted_questions), 2) if extracted_questions else 0.0
            doc.average_confidence = avg_conf

            if not extracted_questions:
                doc.status = "REVIEW_REQUIRED"
                final_job_status = "REVIEW_REQUIRED"
                review_item = ReviewItem(
                    document_id=doc.id,
                    issue_type="NO_QUESTIONS_FOUND",
                    description="No questions could be extracted from this document. Manual inspection required.",
                )
                db.add(review_item)
            elif review_required_count > 0:
                doc.status = "REVIEW_REQUIRED"
                final_job_status = "REVIEW_REQUIRED"
            elif avg_conf >= 0.90:
                doc.status = "COMPLETED"
                final_job_status = "COMPLETED"
            else:
                doc.status = "PARTIAL"
                final_job_status = "PARTIAL"

            job.completed_at = datetime.now(timezone.utc)
            cls.update_job_step(
                db, job, "FINISHED",
                f"Processing complete. Extracted {len(extracted_questions)} questions ({review_required_count} require review). Average confidence: {avg_conf:.2f}",
                status=final_job_status
            )
            db.commit()

        except Exception as e:
            db.rollback()
            job.status = "FAILED"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            cls.update_job_step(db, job, "FAILED", f"Processing failed: {str(e)}", status="FAILED")
            doc.status = "FAILED"
            db.commit()
