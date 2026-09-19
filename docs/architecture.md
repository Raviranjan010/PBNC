# PaperMind — System Architecture & Technical Specifications

## 1. Executive Architecture Overview

PaperMind is an asynchronous document intelligence platform engineered to transform unstructured exam and question-bank documents (digital PDFs, scanned PDFs, PNG/JPEG images) into structured, machine-readable, and source-traceable questions with associated solutions.

### Core Architectural Topology

```
+---------------------------------------------------------------------------------+
|                                Next.js Frontend                                 |
|         (TypeScript + Tailwind CSS + Design System Tokens + Split-View Viewer)   |
+----------------------------------------+----------------------------------------+
                                         | REST API / JWT
                                         v
+---------------------------------------------------------------------------------+
|                                 FastAPI Backend                                 |
|    (Validation Engine + Storage Layer + Auth & Authorization + Alembic + CORS)  |
+-------------------+--------------------+------------------------------------+
                    |                    |
                    v                    v
          +------------------+  +------------------+
          | PostgreSQL / DB  |  |  Redis / Broker  |
          | (10 Core Tables) |  |   (Task Queue)   |
          +------------------+  +--------+---------+
                                         |
                                         v
                        +----------------------------------+
                        |          Celery Worker           |
                        |      (Extraction Pipeline)       |
                        +----------------+-----------------+
                                         |
         +-------------------------------+-------------------------------+
         |                               |                               |
         v                               v                               v
+------------------+            +------------------+            +------------------+
| PyMuPDF Engine   |            |  Tesseract OCR   |            | AI Provider      |
| Text & Rendering |            | Degraded Fallback|            | Gemini / OpenAI  |
+--------+---------+            +--------+---------+            +--------+---------+
         |                               |                               |
         +-------------------------------+-------------------------------+
                                         |
                                         v
                        +----------------------------------+
                        |      Answer Key Association      |
                        |    (Inline / Appendix / Rel)     |
                        +----------------+-----------------+
                                         |
                                         v
                        +----------------------------------+
                        |     Multi-Signal Confidence      |
                        |  OCR + Prompt + Opts + Answer    |
                        +----------------+-----------------+
                                         |
                      +------------------+------------------+
                      |                                     |
                      v                                     v
            [VERIFIED: >= 0.90]                [REVIEW_REQUIRED: < 0.70]
                      |                                     |
                      v                                     v
            PostgreSQL Persistence                 Human Review Queue
                      |                                     |
                      +------------------+------------------+
                                         |
                                         v
                               Next.js UI & Live Exports
```

---

## 2. Pipeline Execution Order

PaperMind operates under the core principle: **AI is never the blind source of truth**. Processing follows a strict sequential lifecycle:

1. **File Validation**:
   - Magic byte header inspection validates true MIME types (`application/pdf`, `image/png`, `image/jpeg`).
   - Rejects corrupted files, empty files, or files exceeding 25MB.
   - Enforces filename sanitization and path traversal prevention.
2. **Text Extraction & Page Rendering (PyMuPDF)**:
   - High-fidelity text extraction per page while preserving page coordinates and physical boundaries.
   - Renders 150 DPI page snapshots for the frontend original source document viewer.
   - Assesses text density to flag scanned or image pages requiring OCR.
3. **OCR Processing (Tesseract)**:
   - Evaluates word-level confidence metrics on scanned pages.
   - Employs honest degradation: if OCR is blurry or unreadable, attaches warnings and lowers confidence rather than hallucinating text.
4. **AI & Structural Extraction (`AIProvider` abstraction)**:
   - Detects question prompts, logical boundaries, multi-page spans (e.g. question starts on page 4 and options finish on page 5), and option keys (`A.`, `(a)`, `A)`, etc.).
   - All output is validated through Pydantic v2 schemas (`ParsedQuestion`).
5. **Answer Key Detection & Association (`AnswerMatcher`)**:
   - Locates answer keys across inline markers, appendix tables, or related documents.
   - Enforces strict association: if an answer is ambiguous, assigns `answer = null`, `answer_status = 'UNCERTAIN'`, and flags `review_required = true`.
6. **Multi-Signal Confidence Scoring (`ConfidenceCalculator`)**:
   - Computes weighted score from OCR clarity (25%), prompt quality (25%), option completeness (25%), and answer certainty (25%).
   - Maps score to status:
     - `confidence >= 0.90` -> `VERIFIED`
     - `0.70 <= confidence < 0.90` -> `PARTIAL`
     - `confidence < 0.70` -> `REVIEW_REQUIRED`
7. **Database Persistence & Human Review Routing**:
   - Persists questions, options, warnings, and review items to PostgreSQL.
   - Flags low-confidence or uncertain questions to the interactive Human Review Queue.

---

## 3. Database Design (PostgreSQL / Alembic)

The schema consists of 10 strongly typed tables:

| Table | Primary Key | Foreign Keys | Key Attributes |
|---|---|---|---|
| `users` | UUID | — | `email`, `hashed_password` (bcrypt), `is_active`, `created_at` |
| `documents` | UUID | `user_id` -> `users.id` | `filename`, `file_type`, `mime_type`, `file_size_bytes`, `page_count`, `storage_path`, `status`, `average_confidence` |
| `document_pages` | UUID | `document_id` -> `documents.id` | `page_number`, `extracted_text`, `ocr_text`, `width`, `height`, `image_path` |
| `processing_jobs` | UUID | `document_id` -> `documents.id` | `status`, `current_step`, `step_details` (JSON audit trail), `error_message`, `started_at`, `completed_at` |
| `questions` | UUID | `document_id` -> `documents.id` | `question_number`, `question_text`, `question_type`, `answer`, `answer_status`, `confidence`, `status`, `review_required`, `is_reviewed`, `source_pages` (JSON) |
| `question_options` | UUID | `question_id` -> `questions.id` | `option_key`, `option_text` |
| `answer_keys` | UUID | `document_id` -> `documents.id` | `raw_key_text`, `detected_format`, `source_page`, `parsed_mappings` (JSON) |
| `document_relationships` | UUID | `parent_document_id`, `related_document_id` | `relationship_type` (`ANSWER_KEY`, `APPENDIX`) |
| `review_items` | UUID | `document_id`, `question_id` | `issue_type`, `description`, `is_resolved`, `resolved_by`, `resolved_at` |
| `extraction_warnings` | UUID | `document_id`, `question_id` | `stage`, `warning_code`, `message`, `severity` |

---

## 4. Multi-Tenant Security & Isolation

- **Authentication**: Passwords are encrypted using salted `bcrypt` hashes. Authenticated sessions issue signed JSON Web Tokens (HS256) with 24-hour expiration.
- **Cross-User Isolation**: Every document and question operation verifies user ownership via `get_document_for_user`. If User B attempts to access or modify User A's document or questions, the API returns `403 Forbidden` or `404 Not Found`, eliminating horizontal privilege escalation and data leakage.
- **Safe Storage**: Raw filesystem paths are never exposed to clients. Files are isolated under `storage/uploads/{user_id}/{doc_id}.ext`. Path traversal attempts (e.g. `../../etc/passwd`) are sanitized.

---

## 5. Assumptions & Trade-offs

1. **OCR Fallback & Binary Detection**:
   - *Assumption*: Environments may not always have the Tesseract C++ binary globally installed.
   - *Design Choice*: The OCR service wraps pytesseract with honest degradation. If Tesseract is unavailable on the host, the document is flagged with an extraction warning and marked `review_required=true` with a clear explanation, rather than crashing or faking OCR text.
2. **AI Provider Fallback**:
   - *Assumption*: AI API keys (Google Gemini / OpenAI) may not be provided during offline local testing.
   - *Design Choice*: The pipeline provides an internal rule-based heuristic parser (`HeuristicProvider`) that extracts questions, options, and cross-page boundaries deterministically, enabling complete offline test verification without external network dependency.
3. **Database Portability**:
   - *Design Choice*: The system supports standard PostgreSQL via asyncpg in Docker / production, while allowing SQLite in-memory / local files via `DATABASE_URL` for frictionless automated testing.
