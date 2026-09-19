# PaperMind — Document Intelligence & Question Extraction Service

> *"From Documents to Structured Knowledge."*  
> **Engineering Assignment Deliverable — Full Stack Developer (Round 2), Pragati Bharti**

---

## 1. Overview & Core Purpose

**PaperMind** is a production-grade Document Intelligence and Question Extraction platform designed to accept exam papers and question banks in multiple formats (digital PDFs, scanned PDFs, PNG, JPEG), process them asynchronously, and convert them into structured, machine-readable, and source-traceable questions with associated answers, multi-signal confidence scores, and a human-in-the-loop review workflow.

### Key Highlights
- **Zero Fake Data**: All dashboard metrics, status progressions, questions, options, confidence values, and exports are dynamically derived from real operations on uploaded files.
- **Asynchronous Execution**: Document uploads return immediately with a job ID while worker processes run in the background.
- **Strict Provenance**: Every extracted question tracks its source document, exact physical page numbers (`source_pages: [4, 5]`), and answer origin.
- **Human Review Workflow**: Questions with low confidence (< 0.70) or uncertain answers enter a review queue where reviewers inspect original source pages, edit transcriptions, and approve results.
- **Live Dynamic Exports**: Live database-driven JSON and CSV export endpoints reflecting real-time edits.

---

## 2. Technology Stack

- **Backend**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL, Redis, Celery, PyMuPDF, Tesseract OCR, Pytest, Bcrypt, PyJWT.
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons, Custom Design System Tokens.
- **AI Abstraction**: `AIProvider` base interface with `GeminiProvider`, `OpenAIProvider`, and deterministic `HeuristicProvider` fallback.
- **DevOps**: Docker, Docker Compose, Multi-stage builds, Healthchecks.

---

## 3. Architecture

```
Next.js Dashboard & Split-View Reviewer
                 | REST API / JWT
FastAPI Backend (Upload, Validation, Auth, Endpoints)
         +---------------+---------------+
         |                               |
    PostgreSQL                         Redis
  (10 DB Tables)                         |
                                   Celery Worker
                        +----------------+----------------+
                        |                |                |
                     PyMuPDF       Tesseract OCR     AI Provider
                  (Text/Pages)   (Degraded Scans) (Structured Qs)
                        +----------------+----------------+
                                         |
                              Answer Matcher Engine
                                         |
                           Multi-Signal Confidence
                        +----------------+----------------+
                        |                                 |
              [VERIFIED: >= 0.90]             [REVIEW_REQUIRED: < 0.70]
                        |                                 |
              PostgreSQL DB Records             Human Review Queue
                        +----------------+----------------+
                                         |
                              API Responses & Exports
```

For comprehensive architectural design and trade-offs, see [`docs/architecture.md`](docs/architecture.md).

---

### Quick Start / 1-Click Launchers

- **Docker Production Deployment**:
  - Linux/macOS: `./deploy.sh`
  - Windows: `deploy.bat`
- **Local Standalone Run**:
  - Linux/macOS: `./run_local.sh`
  - Windows: `run_local.bat`

---

### Option A: Docker Compose (Recommended Production Setup)

Run all services (PostgreSQL, Redis, Celery Worker, FastAPI backend, and Next.js frontend) with a single command:

```bash
docker compose up --build
```

- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI Documentation (Swagger UI)**: `http://localhost:8000/docs`
- **Service Health Check**: `http://localhost:8000/health`

---

### Option B: Local Standalone Development

#### 1. Backend Setup (Python 3.12+)

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Run database migrations
python -m alembic -c backend/alembic.ini upgrade head

# Generate sample fixtures (creates samples/*.pdf and samples/*.png)
python samples/generate_samples.py

# Start the FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```

#### 2. Frontend Setup (Node.js 18+)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 5. Automated Testing (Pytest)

Run the full automated test suite covering authentication, multi-tenant cross-user authorization, file validation, pipeline extraction, multi-page boundary detection, answer matching, human review corrections, live exports, and health:

```bash
python -m pytest backend/tests -v
```

All 16 test suites pass with 100% test integrity.

---

## 6. Demonstration Walkthrough Script (Assignment Section 12)

Use this numbered walkthrough script and the provided test fixtures in [`/samples/`](samples/) to verify or record all 10 mandatory evaluation scenarios:

| # | Demonstration Scenario | Test Fixture File | Exact Endpoint / UI Screen | Verification Evidence |
|---|---|---|---|---|
| **1** | **Uploading a PDF** | `samples/sample_digital_exam.pdf` | `POST /api/v1/documents/upload` or UI Dashboard Upload Box | HTTP 202 Accepted returned with `document_id` and `status: QUEUED`. Real file stored safely. |
| **2** | **Uploading an Image** | `samples/sample_scanned_exam.png` | `POST /api/v1/documents/upload` or UI Dashboard Upload Box | MIME detection identifies `image/png`, processes single-page image through extraction worker. |
| **3** | **Processing a Scanned/Low-Quality Document** | `samples/sample_low_quality_scan.png` | `GET /api/v1/documents/{id}/review-items` or UI `/documents/{id}/review` | OCR degradation detected; extraction warning attached; document flagged for review (`review_required=true`). |
| **4** | **Extracting Multiple Questions** | `samples/sample_digital_exam.pdf` | `GET /api/v1/documents/{id}/questions` or UI `/documents/{id}/questions` | 4 distinct questions extracted (Q1 Normalization, Q2 Stack LIFO, Q3 BST, Q4 Lambda) with page provenance. |
| **5** | **Handling a Question Spanning Multiple Pages** | `samples/sample_multipage_question.pdf` | `GET /api/v1/documents/{id}/questions` | Question 2 starts on Page 1 and options finish on Page 2. Extracted with `source_pages: [1, 2]`. |
| **6** | **Extracting Question Options** | `samples/sample_digital_exam.pdf` | `GET /api/v1/questions/{id}` | All MCQ options (A, B, C, D) extracted with intact keys and distinct option text. |
| **7** | **Detecting and Associating an Answer Key** | `samples/sample_exam_with_key.pdf` & `samples/sample_separate_answer_key.pdf` | `GET /api/v1/documents/{id}/answers` & `POST /api/v1/documents/{id}/related` | Answer key detected; Q1 associated with `A`, Q2 with `C`. Provenance records source page and doc ID. |
| **8** | **Showing Uncertain / Low-Confidence Extraction** | `samples/sample_low_quality_scan.png` | UI `/review` (Human Review Queue) | Question displayed with confidence < 0.70 and `review_required: true`. Visible uncertainty flag shown. |
| **9** | **Retrieving Final Structured Question Data** | Any processed document | `GET /api/v1/documents/{id}/export/json` & `GET /api/v1/documents/{id}/export/csv` | Valid JSON array of structured questions and downloadable CSV file generated live from database records. |
| **10** | **Handling an Invalid / Unsupported Document** | `samples/sample_malformed.pdf` | `POST /api/v1/documents/upload` | Immediate HTTP 400 Bad Request: *"Unsupported or unrecognized file format. Only PDF, PNG, and JPEG documents are permitted."* |

---

## 7. AI Usage Disclosure (Assignment Section 15)

In compliance with Section 15 of the Pragati Bharti engineering assignment:
- **Architectural Abstraction**: PaperMind implements a pluggable `AIProvider` interface.
- **Supported Providers**:
  - `GeminiProvider`: Uses Google Gemini models (`gemini-1.5-flash`) via REST API with strict JSON schema validation.
  - `OpenAIProvider`: Uses OpenAI chat completion API (`gpt-4o-mini`) with structured JSON mode.
  - `HeuristicProvider`: Built-in deterministic structural parser used as an offline/local fallback.
- **Selection**: Controlled dynamically via the `AI_PROVIDER` environment variable (`gemini`, `openai`, or `heuristic`).

---

## 8. Postman Collection & Swagger Documentation

- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **Postman Collection (v2.1)**: Located at [`postman/PaperMind.postman_collection.json`](postman/PaperMind.postman_collection.json) and downloadable via the frontend `/api-docs` page.

---

## 9. Security Checklist Verification

- [x] Salted bcrypt password hashing for all user accounts.
- [x] Secure JWT issuance with expiration enforcement.
- [x] Strict horizontal multi-tenant document isolation (cross-user access returns 403 Forbidden).
- [x] True magic-byte MIME type validation.
- [x] Filename sanitization and path traversal prevention (`../../` rejected).
- [x] Zero hardcoded secrets; `.env.example` provided.
- [x] Zero fake or hardcoded dashboard metrics.