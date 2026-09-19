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

All 18 automated tests pass with 100% test integrity.

---

## 6. Demonstration Walkthrough Script (Assignment Section 12)

Use this numbered walkthrough script and the provided test fixtures in [`/samples/`](samples/) to verify or record all 10 mandatory evaluation scenarios:

| # | Demonstration Scenario | Test Fixture File | Exact Endpoint / UI Screen | Verification Evidence |
|---|---|---|---|---|
| **1** | **Uploading a PDF** | `samples/sample_digital_exam.pdf` | `POST /api/v1/documents/upload` or UI Dashboard Upload Box | HTTP 202 Accepted returned with `document_id` and `status: QUEUED`. Real file stored safely. |
| **2** | **Uploading an Image** | `samples/sample_scanned_exam.png` | `POST /api/v1/documents/upload` or UI Dashboard Upload Box | MIME detection identifies `image/png`, processes single-page image through extraction worker. |
| **3** | **Processing a Scanned/Low-Quality Document** | `samples/sample_low_quality_scan.png` | `GET /api/v1/documents/{id}/review-items` or UI `/documents/{id}/review` | OCR degradation detected; extraction warning attached; document flagged for review (`review_required=true`). |
| **4** | **Extracting Multiple Questions** | `samples/sample_digital_exam.pdf` | `GET /api/v1/documents/{id}/questions` or UI `/documents/{id}/questions` | 4 distinct questions extracted (Q1 Normalization, Q2 Stack LIFO, Q3 BST, Q4 Lambda) with page provenance. |
| **5** | **Multi-Page Question Handling** | `samples/sample_multipage_question.pdf` | `GET /api/v1/documents/{id}/questions` or UI `/documents/[id]` | Question 2 clearly indicates `source_pages: [1, 2]` across page split. |
| **6** | **Answer-Key Processing** | `samples/sample_exam_with_key.pdf` | `GET /api/v1/documents/{id}/answers` or UI `/documents/{id}/answers` | Inline answer key detected (`Q1->A, Q2->C`), confirmed on question objects; no answer key header leakage into option text. |
| **7** | **Confidence Scoring & Review Flagging** | `samples/sample_low_quality_scan.png` | `GET /api/v1/review` or UI `/review` | Questions with confidence < 0.85 surfaced in human review queue with actionable reasons. |
| **8** | **Split-Screen Human Review & Edit** | Any document with flagged questions | `GET /api/v1/questions/{id}` & `PATCH /api/v1/questions/{id}` or UI `/questions/[id]` | Side-by-side view with original page snapshot, live editing of text/options, instant re-scoring. |
| **9** | **Exporting Extracted Questions** | Processed document | `GET /api/v1/documents/{id}/export/json` & `/export/csv` or UI Export Buttons | Real structured JSON and RFC 4180 CSV generated and downloaded. |
| **10**| **Security & Multi-Tenancy Isolation** | Two registered user accounts | `GET /api/v1/documents/{user_a_doc_id}` by User B | Returns `403 Forbidden` with `"Access forbidden"`. Zero data leakage across tenants. |

---

## 7. AI Provider Architecture

PaperMind includes a swappable multi-provider architecture conforming to the `AIProvider` abstract base class:
- **Available Providers**:
  - `GeminiProvider`: Uses Google Gemini models (`gemini-1.5-flash`) via REST API with strict JSON schema validation.
  - `OpenAIProvider`: Uses OpenAI chat completion API (`gpt-4o-mini`) with structured JSON mode.
  - `HeuristicProvider`: Built-in deterministic structural parser used as an offline/local fallback.
- **Selection**: Controlled dynamically via the `AI_PROVIDER` environment variable (`gemini`, `openai`, or `heuristic`).

---

## 8. Postman Collection & Swagger Documentation

- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **Postman Collection (v2.1)**: Located at [`postman/PaperMind.postman_collection.json`](postman/PaperMind.postman_collection.json) and downloadable via the frontend `/api-docs` page.

### Swagger UI Authentication Flow
1. Navigate to `http://localhost:8000/docs`.
2. Expand `POST /api/v1/auth/login`, click **Try it out**, enter your JSON credentials (`{"email": "...", "password": "..."}`), and click **Execute**.
3. Copy the returned `access_token` string from the JSON response.
4. Click the green **Authorize** padlock button at the top right of Swagger UI.
5. Paste the token into the **Value** field and click **Authorize**.
6. All protected endpoints (`/documents`, `/questions`, `/review`, `/analytics`, `/auth/me`) are immediately authenticated.

---

## 9. Security Checklist Verification

- [x] Salted bcrypt password hashing for all user accounts.
- [x] Secure JWT issuance with expiration enforcement.
- [x] Strict horizontal multi-tenant document isolation (cross-user access returns 403 Forbidden).
- [x] True magic-byte MIME type validation.
- [x] Filename sanitization and path traversal prevention (`../../` rejected).
- [x] Zero hardcoded secrets; `.env.example` provided.
- [x] Zero fake or hardcoded dashboard metrics.