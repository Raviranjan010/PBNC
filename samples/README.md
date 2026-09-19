# PaperMind — Sample Test Fixtures

All sample files in this directory are strictly **TEST FIXTURES** created for reproducible integration testing and assignment demonstration purposes. They are never hardcoded into the application logic or dashboard state.

| File | Scenario / Purpose | Expected Extraction Result |
|---|---|---|
| `sample_digital_exam.pdf` | Clean digital PDF with 4 questions across 2 pages. | 4 MCQ questions, 100% option parsing, page 1 & 2 provenance, confidence >= 0.90 (VERIFIED). |
| `sample_multipage_question.pdf` | Question 2 spans across page 1 and page 2 boundary. | Question 2 detected with `source_pages: [1, 2]`, options intact. |
| `sample_exam_with_key.pdf` | Digital exam containing an embedded Answer Key section at the end. | Questions extracted with answers automatically associated (Q1 -> A, Q2 -> C). |
| `sample_separate_answer_key.pdf` | Standalone answer key document. | Associated to question papers via `POST /api/v1/documents/{id}/related` to resolve solutions. |
| `sample_scanned_exam.png` | Standalone image question paper (PNG format). | Single page rendering, OCR extraction, question detection. |
| `sample_low_quality_scan.png` | Simulated degraded, low-contrast scan. | Degraded OCR detected, extraction warning attached, flags `review_required=true`. |
| `sample_malformed.pdf` | Non-PDF raw text masquerading as a PDF. | Immediate rejection by DocumentValidator with HTTP 400 Bad Request. |
