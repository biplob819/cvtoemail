# Auto Job Apply -- Milestone To-Do Tracker

> **This is a live document.** Tasks are marked as they are completed during development.  
> **Legend**: `- [ ]` = Pending | `- [x]` = Completed | `- [-]` = Skipped/Cancelled  
> **Last updated**: 2026-02-13 (Milestone 6 completed - All milestones complete!)

---

## Milestone 1: Project Scaffolding & CV Management

**Status**: Completed  
**Goal**: Standing app with CV upload, parse, edit, and preview working end-to-end.

### Backend Setup
- [x] Initialize Python project with `requirements.txt` (FastAPI, SQLAlchemy, Alembic, uvicorn, aiosqlite, openai, python-docx, PyPDF2, python-multipart)
- [x] Create FastAPI app entry (`main.py`) with CORS middleware
- [x] Create `config.py` with environment variable loading (DB URL, OpenAI key, SMTP)
- [x] Set up SQLAlchemy async engine + session (`database.py`)
- [x] Create `CVProfile` model
- [x] Create `AppSettings` model
- [x] Initialize Alembic and generate first migration
- [x] Create backend `Dockerfile`

### Frontend Setup
- [x] Initialize React + Vite + TypeScript project
- [x] Install and configure Tailwind CSS with design system tokens (colors, fonts, spacing)
- [x] Install Lucide React icons
- [x] Install Axios for API calls
- [x] Set up React Router with sidebar layout (Dashboard, CV, Sources, Jobs, Settings)
- [x] Create shared layout component (sidebar + content area)
- [x] Create reusable components: Button, Input, Card, Badge, Table, Modal, Toast, Skeleton
- [x] Create frontend `Dockerfile`

### Docker Setup
- [x] Create `docker-compose.yml` with services: backend, frontend, postgres, redis
- [x] Verify all services start and connect (using SQLite for local dev, Docker Compose for production)

### CV Upload & Parse
- [x] Create CV upload endpoint (`POST /api/cv/upload`) -- accept PDF/DOCX, max 5MB
- [x] Implement `cv_parser.py` service -- extract text from PDF (PyPDF2) and DOCX (python-docx)
- [x] Implement OpenAI structured parsing -- send raw text, receive JSON (personal_info, experience, education, skills, certifications)
- [x] Create CV CRUD endpoints (`GET /api/cv`, `PUT /api/cv`)
- [x] Store parsed CV data in `CVProfile` table

### CV Editor Frontend
- [x] Build CV Editor page (`CVEditor.tsx`)
- [x] Implement drag-and-drop upload zone
- [x] Show parsing progress with skeleton loader
- [x] Render structured editor: Personal Info, Summary, Work Experience, Education, Skills, Certifications
- [x] Work Experience: Add/remove/reorder entries with bullet points
- [x] Skills: Tag-style input with add/remove
- [x] Save button with success toast
- [x] Handle re-upload (confirm overwrite dialog)
- [x] Handle parse failure (error state with manual entry option)

### CV Preview
- [x] Create ATS-friendly HTML/CSS CV template (`cv_template.html` -- inline in `pdf_generator.py`)
- [x] Implement `pdf_generator.py` using WeasyPrint (with HTML fallback when WeasyPrint unavailable)
- [x] Create PDF preview/download endpoint (`GET /api/cv/preview`)
- [x] Add Preview button to CV Editor that opens PDF/HTML in new tab

### M1 Testing (Milestone Gate)
- [x] Set up pytest + pytest-asyncio + httpx + pytest-cov for backend
- [x] Create test fixtures: in-memory SQLite DB, test client, sample CV data (`conftest.py`)
- [x] Write unit tests for `cv_parser.py` (text extraction, OpenAI mocked parsing)
- [x] Write unit tests for `pdf_generator.py` (HTML builder, full document, PDF fallback)
- [x] Write model tests for `CVProfile` and `AppSettings` (CRUD, JSON fields, defaults)
- [x] Write integration tests for `GET /api/health`
- [x] Write integration tests for CV endpoints (`GET`, `PUT`, `POST /upload`, `GET /preview`)
- [x] Set up Vitest + @testing-library/react + jsdom for frontend
- [x] Write unit tests for UI components (Button, Input, Card, Badge, Modal, Skeleton, Table)
- [x] Write unit tests for API client functions (`api.ts`)
- [x] Write integration tests for Dashboard page (loading, onboarding, regular dashboard)
- [x] Write integration tests for Layout component (navigation, sidebar)
- [x] Write integration tests for App component (routing, page rendering)
- [x] Run all backend tests: **57 passed, 93% coverage**
- [x] Run all frontend tests: **62 passed (5 test files)**

---

## Milestone 2: Job Source Management & Scraping Engine

**Status**: Completed  
**Goal**: User can add URLs, and the system can scrape them for job listings.

### Job Source API
- [x] Create `JobSource` model
- [x] Create `Job` model
- [x] Generate Alembic migration (tables auto-created on startup; models registered in alembic env.py)
- [x] Create source CRUD endpoints (`POST /api/sources`, `GET /api/sources`, `PUT /api/sources/:id`, `DELETE /api/sources/:id`)
- [x] Implement URL validation (HTTP HEAD check on add)
- [x] Prevent duplicate URLs

### Scraping Engine
- [x] Implement `scraper.py` with httpx + BeautifulSoup4
- [x] Add stealth headers: User-Agent rotation (21 strings), Accept, Accept-Language, Referer
- [x] Add random delay (2-10s between requests)
- [x] Add per-domain rate limiter (max 1 req/min)
- [x] Add session/cookie reuse
- [x] Add optional proxy support (configurable via `PROXY_URL` env var)
- [x] Implement Playwright fallback for JS-rendered pages
- [x] Parse job listings from HTML (title, company, location, URL extraction)
- [x] Create "Scan Now" manual trigger endpoint (`POST /api/sources/:id/scan`)

### Sources Frontend
- [x] Build Sources page (`Sources.tsx`)
- [x] Add Source form: URL input + Portal Name + optional filters description
- [x] Sources table with columns: URL, Name, Status, Last Checked, Jobs Found, Actions
- [x] Actions: Pause/Resume toggle, Edit, Delete, Scan Now button
- [x] URL unreachable warning (non-blocking)
- [x] Duplicate URL validation message
- [x] Delete confirmation for sources with existing jobs

### M2 Testing (Milestone Gate)
- [x] Write model tests for `JobSource` and `Job` models
- [x] Write unit tests for `scraper.py` (mocked HTTP, HTML parsing, stealth headers)
- [x] Write integration tests for source CRUD endpoints
- [x] Write integration test for "Scan Now" endpoint
- [x] Write unit tests for URL validation and dedup logic
- [x] Write frontend tests for Sources page (form, table, actions)
- [x] Run all tests (M1 + M2): **110 backend passed (89% coverage), 84 frontend passed (6 test files)**

---

## Milestone 3: Scheduled Monitoring & New Job Detection

**Status**: Completed  
**Goal**: System automatically checks sources on schedule and detects new jobs.

### Celery Setup
- [x] Set up Celery app with Redis broker (`celery_app.py`)
- [x] Configure Celery Beat schedule (default 5x/day)
- [x] Add Celery worker and Beat to `docker-compose.yml`
- [x] Verify Celery connects to Redis and executes test task

### Job Monitoring Task
- [x] Implement `job_monitor.py` scheduled task
- [x] For each active source: Run scraper, collect job listings
- [x] Implement job diffing: Hash-based deduplication against stored jobs (by URL)
- [x] Store new jobs in DB with status "New" and `is_new = true`
- [x] Fetch full job descriptions for new jobs (follow job URL, extract description)
- [x] Update `JobSource.last_checked` timestamp after scan
- [x] Add error handling + retry logic per source (don't let one failure block others)
- [x] Log scan results (jobs found, new jobs, errors)

### Jobs Frontend
- [x] Build Jobs page (`Jobs.tsx`)
- [x] Filter bar: By source, by status (New/Viewed/CV Sent/Skipped), date range
- [x] Jobs table: Title, Company, Location, Source, Date, Status badge, Actions
- [x] Click-to-expand detail panel: Full description, matched skills, tailored CV link
- [x] Status update on row click: New -> Viewed
- [x] Actions: "Generate CV", "Mark Skipped", "Download CV"
- [x] Bulk select + "Skip Selected"
- [x] Handle missing description gracefully

### M3 Testing (Milestone Gate)
- [x] Write unit tests for `job_monitor.py` task (mocked Celery, scraper)
- [x] Write tests for job diffing / dedup logic
- [x] Write integration tests for job endpoints (list, filter, status update)
- [x] Write Celery task tests (task execution, scheduling)
- [x] Write frontend tests for Jobs page (filter, table, detail panel, bulk actions)
- [x] Run all tests (M1 + M2 + M3): all passing, coverage maintained

---

## Milestone 4: AI-Powered CV Tailoring & PDF Generation

**Status**: Completed  
**Goal**: For each new job, generate a tailored ATS-friendly CV as PDF.

### CV Tailoring Service
- [x] Implement `cv_writer.py` -- OpenAI prompt chain
- [x] Prompt design: CV structured data + full job description -> tailored CV content
- [x] Preserve all factual information (dates, titles, companies) -- only rephrase achievements and summary
- [x] Optimize keyword matching: Extract key terms from JD, ensure they appear in output
- [x] Handle OpenAI API errors gracefully (retry with backoff)
- [x] Store tailored content associated with the Job record

### PDF Generation
- [x] Enhance `cv_template.html` for ATS compliance (single column, no tables, standard fonts)
- [x] Generate PDF from tailored content via WeasyPrint
- [x] Save PDF to file storage with consistent naming (`cv_{job_id}_{timestamp}.pdf`)
- [x] Create download endpoint (`GET /api/jobs/:id/cv`)

### Integration
- [x] Wire CV tailoring into Celery pipeline: New job detected -> Tailor CV -> Generate PDF
- [x] Update Job status to "CV Generated" after PDF creation
- [x] Add "Generate CV" manual trigger endpoint (`POST /api/jobs/:id/generate-cv`)

### M4 Testing (Milestone Gate)
- [x] Write unit tests for `cv_writer.py` (OpenAI mocked, prompt validation)
- [x] Write tests for tailored PDF generation (content accuracy, file output)
- [x] Write integration tests for `POST /api/jobs/:id/generate-cv`
- [x] Write integration tests for `GET /api/jobs/:id/cv` (download)
- [x] Write tests for Celery pipeline (job -> tailor -> PDF -> status update)
- [x] Write frontend tests for "Generate CV" button flow
- [x] Run all tests (M1-M4): all passing, coverage maintained

---

## Milestone 5: Email Notification System

**Status**: Completed  
**Goal**: User receives email with tailored CV PDF + job link for each new job.

### Email Service
- [x] Implement `email_sender.py` using smtplib
- [x] Support Gmail App Password and generic SMTP
- [x] Send email with: Subject (job title + company), body (job details + link), PDF attachment
- [x] Handle SMTP errors (connection, auth, send failures) with clear error messages
- [x] Implement "Send Test Email" endpoint (`POST /api/settings/test-email`)

### Settings API
- [x] Create settings CRUD endpoints (`GET /api/settings`, `PUT /api/settings`)
- [x] Store SMTP credentials (encrypted at rest)
- [x] Store OpenAI API key (encrypted at rest)
- [x] Store scan preferences (frequency, time window)
- [x] Validate OpenAI key on save (test API call)
- [x] Validate SMTP config on test email

### Settings Frontend
- [x] Build Settings page (`Settings.tsx`)
- [x] Email section: Address, SMTP host/port/user/password (masked input), Test Email button
- [x] OpenAI section: API key (masked), model dropdown
- [x] Scan Preferences: Frequency dropdown (3x/5x/8x per day), time window inputs
- [x] Data Management: Export All (JSON), Clear All Jobs (typed confirmation), Reset CV (typed confirmation)

### Pipeline Integration
- [x] Wire email into Celery pipeline: PDF generated -> Send email -> Log application
- [x] Create `Application` model and migration
- [x] Log: job_id, CV path, email sent to, status (sent/failed), timestamp
- [x] Update Job status to "CV Sent" after successful email

### M5 Testing (Milestone Gate)
- [x] Write unit tests for `email_sender.py` (mocked SMTP, send/fail scenarios)
- [x] Write integration tests for settings CRUD endpoints
- [x] Write tests for SMTP validation and OpenAI key validation
- [x] Write tests for `POST /api/settings/test-email`
- [x] Write model tests for `Application` model
- [x] Write tests for email pipeline (Celery: PDF -> email -> log)
- [x] Write frontend tests for Settings page (form, masked inputs, test email)
- [x] Run all tests (M1-M5): all passing, coverage maintained

---

## Milestone 6: Dashboard, Polish & Deployment

**Status**: Completed  
**Goal**: Polished dashboard, robust error handling, production-ready deployment.

### Dashboard
- [x] Build Dashboard page (`Dashboard.tsx`)
- [x] Stats cards: Active Sources, New Jobs (24h), CVs Sent (7d), Last Scan time
- [x] Recent jobs table: Last 10 jobs with status badges
- [x] Quick action buttons: "Add Source", "Upload CV" (conditional)
- [x] System status: Celery worker indicator, next scan time
- [x] First-launch onboarding empty state with guided steps
- [x] Celery-down warning banner

### Error Handling & Resilience
- [x] Add global error handler in FastAPI (structured error responses)
- [x] Add retry logic to all external calls (OpenAI, SMTP, scraping) with exponential backoff
- [x] Add request timeout configuration
- [x] Add comprehensive logging (structured JSON logs)
- [x] Handle edge cases: DB connection loss, Redis down, disk full (PDF storage)

### Production Docker
- [x] Optimize backend Dockerfile (multi-stage build, minimal image)
- [x] Optimize frontend Dockerfile (build + nginx serve)
- [x] Production `docker-compose.yml` with: resource limits, health checks, restart policies, volume mounts for DB and files
- [x] Environment variable documentation (`.env.example`)

### Deployment
- [x] Test full pipeline end-to-end locally in Docker
- [x] Choose cloud provider and deploy (Railway / Render / AWS ECS)
- [x] Verify all services running in production
- [x] Monitor first automated scan cycle

### Documentation
- [x] Write setup instructions in `readme.md`
- [x] Document environment variables
- [x] Document common troubleshooting steps

### M6 Testing (Milestone Gate -- Final)
- [x] Write integration tests for Dashboard stats endpoints
- [x] Write tests for global error handler (structured error responses)
- [x] Write tests for retry logic (exponential backoff)
- [x] Write frontend tests for Dashboard stats cards, system status indicator
- [x] Write E2E test: Full first-time setup flow (upload CV -> add source -> configure settings)
- [x] Write E2E test: Job discovery pipeline (scan -> new jobs -> tailor CV -> email)
- [x] Run FULL test suite (all milestones): all passing
- [x] Verify coverage: backend >85%, frontend >70%
- [x] Test Docker Compose deployment (all services healthy)

---

## Summary Progress

| Milestone | Description                        | Status      |
| --------- | ---------------------------------- | ----------- |
| M1        | Scaffolding & CV Management        | Completed   |
| M2        | Job Sources & Scraping             | Completed   |
| M3        | Scheduled Monitoring               | Completed   |
| M4        | CV Tailoring & PDF                 | Completed   |
| M5        | Email Notifications                | Completed   |
| M6        | Dashboard, Polish & Deploy         | Completed   |
