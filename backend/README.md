# DethiAI Backend - Technical Documentation

This document describes the architecture, features, processing pipeline, API surface, data model (Firestore + Storage), configuration, and operational concerns for the DethiAI backend.

## 1) Overview

DethiAI (Đề thi AI) ingests exams (PDF/DOCX), performs OCR to recover Markdown, extracts structured questions via LLMs (LangChain), and generates analogous (similar) exams. It stores uploaded files in Firebase Storage and metadata/content in Firestore. Long-running work runs on Redis RQ workers and progress is reflected in Firestore so the frontend can display it in real time.

## 2) Features

- Upload exams (PDF/DOCX) with Firebase-authenticated users (Google only)
- OCR + page-to-Markdown + structure extraction (LLM)
- Show extracted questions; user selects what to base generation on
- Generate analogous questions per selected item (parallel jobs)
- Track progress at exam-level and per-question (pending/processing/done/error)
- Export on demand to Markdown, compiled PDF, or DOCX
- Clean, structured logging (no emojis)
- Packaged via Docker Compose (API + Worker + Redis)

## 3) Processing Pipeline

1. Upload
   - POST /documents with a file (multipart)
   - Store in Firebase Storage and create Firestore document with status fields
   - Enqueue an OCR initialization job (Redis RQ)
2. OCR (Parallel Processing)
   - OCR initialization job downloads file, counts pages, and generates images in local temp directory
   - Each page OCR job processes one local image file
   - Progress tracked in `ocr_total` and `ocr_completed` fields
   - When all pages complete, extraction job is automatically enqueued
3. Extract
   - Extraction worker concatenates all page Markdown results
   - Use LangChain to convert combined Markdown → JSON exam schema
   - Save original questions into `documents/{doc}/questions` (no answers)
4. Selection + Generate
   - Frontend fetches original questions and lets user select indices
   - POST /documents/{doc}/generate with selected_indices and target_count
   - API creates a generated exam doc with total, completed=0, and per-question placeholders status=pending (q1..qN)
   - Enqueue one job per selected question (parallel)
5. Per-question job
   - Worker sets status=processing for q{index}
   - Calls LLM chain based on question type to generate analogous question + answer/explanation
   - Saves result into q{index} with status=done and increments completed
   - On error sets status=error with error message
6. Export
   - On GET /documents/{doc}/exams/{gen}/export?format=markdown|pdf|docx build Markdown and if pdf/docx, compile with pandoc on demand

## 4) APIs (FastAPI)

Base URL: `/`

- POST `/documents`

  - Body: multipart form with `file`
  - Auth: Firebase ID token (Google provider)
  - Returns: `{ id, job_id }`

- GET `/documents/{docId}`

  - Returns document metadata including `ocr_status`, `extract_status`.

- GET `/documents/{docId}/questions`

  - Returns: `{ questions: [...] }` — original questions (no answers)

- POST `/documents/{docId}/generate`

  - Body: `{ selected_indices: number[], target_count: number }`
  - Creates generated exam and per-question placeholders; enqueues jobs
  - Returns: `{ generated_exam_id, job_ids: string[], total: number }`

- GET `/documents/{docId}/exams/{genId}`

  - Returns: `{ metadata, elements }` — elements include status for generated questions

- GET `/documents/{docId}/exams/{genId}/export?format=markdown|pdf|docx`

  - Returns Markdown source, a compiled PDF download, or a DOCX download

- GET `/healthz`
  - Health check: `{ status: "ok" }`

Auth: All routes except `/healthz` require a valid Firebase ID token with `firebase.sign_in_provider == "google.com"`.

## 5) Firestore Data Model

Top-level collection: `documents`

Document: `documents/{docId}`

- id: string
- filename: string
- content_type: string
- size: number
- storage_path: string (Firebase Storage path)
- created_by: string (uid)
- created_at: number (epoch seconds)
- ocr_status: "pending" | "processing" | "done" | "error"
- extract_status: "pending" | "processing" | "done" | "error"
- original_exam.metadata: { title: string, duration_minutes?: number }

Subcollection: `documents/{docId}/questions` (original exam)

- `_meta`: { type: "original" }
- `q{index}`: { type, index, content, data? } (no answers)

Subcollection: `documents/{docId}/generated_exams`

- `{genId}`:
  - metadata: { title, ... }
  - status: "pending" | "processing" | "done" | "error"
  - total: number
  - completed: number
  - created_at, updated_at
  - Subcollection: `questions`
    - `q{index}`: placeholder created at generation start
      - index: number
      - status: "pending" | "processing" | "done" | "error"
      - when done: full question payload + `answer` (if applicable)

Motivation

- Original questions are separated (no answers).
- Generated exam questions include answers/explanations.
- Per-question docs enable real-time per-question status updates and parallelism.

## 6) Exam Schema (Pydantic)

Top-level Exam

- metadata: { title: string, duration_minutes?: number }
- elements: Array of AnyElement

Elements

- TextElement: { type: "text", content: string }
- MultipleChoiceQuestion: { type: "multiple_choice", index: number, content: string, data: { options: string[] } }
- TrueFalseQuestion: { type: "true_false", index: number, content: string, data: { clauses: string[] } }
- ShortAnswerQuestion: { type: "short_answer", index: number, content: string }

Generated variants include `answer`:

- MultipleChoiceQuestionWithAnswer.answer: { selected_options: number, explanation?: string, error_analysis?: string[] }
- TrueFalseQuestionWithAnswer.answer: { clause_correctness: boolean[], general_explanation?: string, explanations?: string[] }
- ShortAnswerQuestionWithAnswer.answer: { answer_text: string, explanation?: string }

## 7) Storage Layout (Firebase Storage)

- `documents/{uid}/{docId}/{filename}` — original uploaded file location
- Temporary/derived files are generated in containers and not persisted to Storage (OCR output is stored structurally in Firestore, not as files).

## 8) Queueing and Concurrency (Redis RQ)

Queues

- `ocr`: parallel jobs per page — OCR individual pages
- `extract`: single job per upload — extraction after all OCR pages complete
- `generate`: one job per selected question

Progress

- OCR-level: `documents/{docId}.ocr_total` and `ocr_completed`, auto-mark `ocr_status=done` when all pages complete
- Exam-level: `generated_exams/{gen}.total` and `completed`, auto-mark `status=done` when `completed >= total`.
- Per-question: `status` among pending/processing/done/error in `generated_exams/{gen}/questions/q{index}`.

Workflow

1. Upload triggers OCR initialization job
2. OCR job downloads file, converts to images, stores in local temp directory (/tmp/ocr\_{doc_id})
3. Enqueues parallel OCR jobs with local image file paths
4. Each page OCR job processes its image and stores result in Firestore
5. When all pages complete, extraction job is automatically enqueued
6. Extraction job concatenates all page results and extracts exam structure
7. Local temp directory is cleaned up after completion

$ 1 \leq \text{ocr_completed} \leq \text{ocr_total} $

## 9) LLM and Prompts (LangChain)

- Vision OCR: REST call to OpenRouter vision model to get Markdown per page (see `ocr_service.py`).
- Structure extraction: LangChain prompt converts concatenated Markdown to Exam JSON (`langchain_service.extract_exam_from_markdown`).
- Generation chains per type:
  - Multiple choice: `generate_mcq_from_example`
  - True/False: `generate_true_false_from_example`
  - Short answer: `generate_short_answer_from_example`
- Prompt templates live under `app/prompts/`.
- Models are configured via env vars: `OCR_MODEL_NAME`, `GEN_MODEL_NAME`. OpenRouter key: `OPENROUTER_API_KEY`.

## 10) Export

- Build Markdown document from JSON exam (`export_service.build_markdown_from_exam`)
- Optional PDF compilation via `pandoc` on demand
- DOCX export via `pandoc` (`export_service.compile_docx`)

## 11) Configuration

Environment variables (loaded via python-dotenv in dev, or docker-compose envs in containers):

- GOOGLE_APPLICATION_CREDENTIALS=/app/firebase-credentials.json
- FIREBASE_STORAGE_BUCKET=your-project.appspot.com
- OPENROUTER_API_KEY=sk-...
- OCR_MODEL_NAME=openai/gpt-5-vision-mini
- OCR_STRUCT_MODEL=openai/gpt-5-mini
- GEN_MODEL_NAME=openai/gpt-5-mini
- REDIS_HOST=redis
- REDIS_PORT=6379

## 12) Deployment and Local Dev

Docker Compose services:

- api: FastAPI server (port 8080)
- worker: Redis RQ worker (`ocr`, `generate` queues)
- redis: Redis 7-alpine

Local dev (optional) uses `.env` via python-dotenv and uvicorn.

## 13) Error Handling and Logging

- All errors are logged via Python logging (no emojis)
- Worker tasks catch exceptions per unit of work:
  - OCR/Extract: sets `ocr_status`/`extract_status` to `error`
  - Per-question generation: sets `status=error` on `q{index}` with an `error` field

## 14) Security

- Firebase ID Token required for all API endpoints (except `/healthz`)
- Google provider enforced (reject other providers)
- Per-resource ownership check (`created_by == uid`)

## 15) Extensibility

- Add more question types by extending schemas, prompts, and generation dispatcher
- Add docx export by implementing a parallel export service
- Add webhook or SSE/WS stream for API-driven progress updates (currently recommend Firestore listeners)

## 16) Known Requirements/Dependencies

- System packages in container: `libreoffice`, `poppler-utils`, `texlive` for OCR and PDF export
- External LLM access via OpenRouter

## 17) Troubleshooting

- Missing credentials: Ensure `firebase-credentials.json` is mounted and `GOOGLE_APPLICATION_CREDENTIALS` points to it
- OCR tools missing: The Dockerfile installs required system dependencies
- RQ not running: Ensure `worker` service is up and connected to `redis`
- Model errors: Check `OPENROUTER_API_KEY` and model names
