# Auto Job Apply -- Product & Technical Specification

> **Version**: 1.0  
> **Last updated**: 2026-02-13  
> **Status**: Pre-development  
> **Owner**: Product Manager  

---

## 1. Product Overview

A single-user micro web app that:
1. Stores and manages your CV data (structured, editable)
2. Monitors custom job portal URLs for new listings on a schedule
3. Auto-generates ATS-friendly tailored CVs using OpenAI for each new job
4. Emails you the tailored CV + job link so you can apply manually

**This is a personal productivity tool, not a SaaS product.** No authentication, no multi-tenancy, no billing.

---

## 2. User Profile

- **Single user**, running locally or on a private server
- Technically literate (comfortable with Docker, environment variables)
- Wants to passively monitor job boards and receive ready-to-submit CVs
- Applies manually -- the app is an assistant, not a bot that submits applications

---

## 3. Design System

### 3.1 Philosophy

Minimal & Light -- inspired by Notion and Stripe. Calm, functional, professional. No visual clutter. Every element earns its place.

### 3.2 Color Palette

| Token                  | Value       | Usage                                     |
| ---------------------- | ----------- | ----------------------------------------- |
| `--color-bg`           | `#FFFFFF`   | Page background                           |
| `--color-surface`      | `#F9FAFB`   | Cards, panels, input backgrounds          |
| `--color-border`       | `#E5E7EB`   | Borders, dividers                         |
| `--color-text`         | `#111827`   | Primary text                              |
| `--color-text-muted`   | `#6B7280`   | Secondary/helper text                     |
| `--color-primary`      | `#2563EB`   | Primary actions, links, active states     |
| `--color-primary-hover` | `#1D4ED8`  | Hover state for primary                   |
| `--color-success`      | `#16A34A`   | Success badges, sent status               |
| `--color-warning`      | `#D97706`   | Warnings, pending states                  |
| `--color-danger`       | `#DC2626`   | Errors, destructive actions               |

### 3.3 Typography

- **Font Family**: `Inter` (fallback: `-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif`)
- **Scale**: 12px / 14px / 16px / 20px / 24px / 32px
- **Font Weights**: 400 (body), 500 (labels/nav), 600 (headings), 700 (page titles)
- **Line Height**: 1.5 for body, 1.25 for headings

### 3.4 Spacing

- **Base unit**: 4px
- **Scale**: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64px
- **Card padding**: 24px
- **Page padding**: 32px horizontal, 24px vertical
- **Section gap**: 32px

### 3.5 Layout

- **Desktop**: Fixed left sidebar (240px) + scrollable content area
- **Responsive**: Sidebar collapses to top hamburger menu below 768px
- **Max content width**: 960px (centered in content area)
- **Grid**: CSS Grid / Flexbox, no fixed column system

### 3.6 Component Patterns

| Component     | Specification                                                         |
| ------------- | --------------------------------------------------------------------- |
| Buttons       | Rounded-md (6px), 36px height, filled primary / outlined secondary    |
| Inputs        | 40px height, 1px border, 8px radius, focus ring `--color-primary`     |
| Cards         | White bg, 1px border, 8px radius, subtle shadow (`0 1px 3px` rgba)   |
| Tables        | No outer border, horizontal dividers only, hover row highlight        |
| Badges        | Pill shape, 12px text, color-coded by status                         |
| Modals        | Centered overlay, 480px max-width, backdrop blur                      |
| Toasts        | Bottom-right, auto-dismiss 5s, icon + message                        |
| Empty States  | Centered icon + helper text + CTA button                             |
| Loading       | Skeleton placeholders (not spinners) for content areas                |

### 3.7 Iconography

- **Library**: Lucide React (consistent, lightweight, MIT)
- **Sizes**: 16px inline, 20px in nav, 24px in empty states
- **Style**: Outline, 1.5px stroke

### 3.8 Interaction Principles

- SPA with client-side routing (no page reloads)
- Optimistic UI where possible
- Skeleton loading for data-fetched views
- 150ms ease transitions on hover/focus
- Confirmation dialogs for destructive actions only

---

## 4. Product Functionality

### 4.1 Screen: Dashboard (`/`)

**Purpose**: At-a-glance system status.

**Elements**:
- **Stats bar**: Active Sources count, New Jobs (24h), CVs Sent (7d), Last Scan time
- **Recent jobs table**: Last 10 discovered jobs -- Title, Company, Source, Date, Status badge
- **Quick actions**: "Add Source" button, "Upload CV" button (shown if no CV exists)
- **System status**: Celery worker indicator (green/red), next scan time

**Edge cases**:
- First launch (no CV, no sources): Onboarding empty state with guided setup steps
- Celery not running: Warning banner with troubleshooting guidance

### 4.2 Screen: CV Editor (`/cv`)

**Purpose**: Upload, parse, view, and edit CV data.

**Elements**:
- **Upload zone**: Drag-and-drop or click, PDF/DOCX, max 5MB
- **Parse progress**: Skeleton + status text while OpenAI processes
- **Structured editor**: Sections for Personal Info, Summary, Work Experience, Education, Skills, Certifications
- **Work Experience entries**: Title, Company, Duration, bullet-point achievements (add/remove/reorder)
- **Skills**: Tag-style input
- **Save**: Persists to DB, success toast
- **Preview**: Opens ATS PDF preview of current data

**ATS Template Rules**:
- Single column, no tables, no graphics, no headers/footers
- Bold section headings, clear hierarchy
- Standard fonts only in PDF
- Keywords preserved exactly as entered

**Edge cases**:
- Re-upload: Confirm overwrite
- Parse failure: Error message + option to enter data manually
- Empty optional sections: Allowed

### 4.3 Screen: Job Sources (`/sources`)

**Purpose**: Manage monitored URLs.

**Elements**:
- **Add form**: URL + Portal Name (label) + optional filters description
- **Sources table**: URL, Name, Status (Active/Paused), Last Checked, Jobs Found, Actions
- **Actions**: Pause/Resume, Edit, Delete, "Scan Now" (manual trigger)
- **Validation**: HTTP HEAD check on add

**Scope**: Custom URLs only. No portal-specific login/auth.

**Edge cases**:
- URL unreachable: Warning, but allow saving
- Duplicate URL: Block with validation message
- Delete source with jobs: Confirm dialog, jobs remain in DB

### 4.4 Screen: Jobs (`/jobs`)

**Purpose**: Browse discovered jobs and manage application status.

**Elements**:
- **Filter bar**: By source, status (New/Viewed/CV Sent/Skipped), date range
- **Jobs table**: Title, Company, Location, Source, Date, Status, Actions
- **Detail panel**: Expand row for full description, skill match highlights, tailored CV link
- **Actions**: "Generate CV" (trigger), "Mark Skipped", "Download CV" (PDF)
- **Bulk**: Select multiple + "Skip Selected"

**Status flow**: `New` -> `Viewed` (on click) -> `CV Sent` (after email) or `Skipped` (manual)

**Edge cases**:
- Description fetch failure: Show partial data + note
- Duplicate jobs across sources: Deduplicate by URL
- Long descriptions: Truncate with "Show more"

### 4.5 Screen: Settings (`/settings`)

**Purpose**: Configure email, API keys, scan preferences.

**Sections**:
- **Email**: Address, SMTP host/port/user/password (masked), "Send Test Email"
- **OpenAI**: API key (masked), model dropdown (gpt-4o-mini / gpt-4o)
- **Scan Preferences**: Frequency (3x/5x/8x per day), time window (e.g., 8AM-8PM)
- **Data Management**: Export All (JSON), Clear All Jobs, Reset CV

**Edge cases**:
- Invalid SMTP: Test email shows specific error
- Invalid OpenAI key: Validate on save via test API call
- Destructive actions: Typed confirmation modal

---

## 5. User Flows

### Flow 1: First-Time Setup

1. Open app -> Dashboard shows onboarding empty state
2. Click "Upload CV" -> CV Editor
3. Upload PDF -> OpenAI parses -> Review & edit -> Save
4. Navigate to Sources -> Add first URL
5. Navigate to Settings -> Configure email + OpenAI key
6. System monitors on next scheduled scan

### Flow 2: Daily Passive Usage

1. Celery Beat triggers scan (default 5x/day)
2. Scraper checks all active sources
3. New jobs stored with status "New"
4. Per new job: Fetch description -> Tailor CV -> Generate PDF
5. Email sent to user with PDF + job link
6. User reviews email, applies manually

### Flow 3: Manual Intervention

1. Open Dashboard -> See new jobs
2. Go to Jobs page -> Review details
3. Skip irrelevant jobs
4. For interesting jobs: Click "Generate CV" or download existing
5. Apply manually on portal

---

## 6. Scope Boundaries

| In Scope                                | Out of Scope                             |
| --------------------------------------- | ---------------------------------------- |
| Custom URL scraping (career pages)      | Portal login/auth (LinkedIn login, etc.) |
| Generic HTML parsing for job listings   | Portal-specific APIs                     |
| OpenAI CV tailoring                     | Auto-filling application forms           |
| Email notification to self              | Direct submission to portals             |
| ATS-friendly PDF generation             | Multiple CV template designs             |
| Single-user local/private deployment    | Multi-user, auth, billing                |
| Manual scan trigger                     | Real-time websocket notifications        |
| Basic job deduplication                 | ML-based job relevance scoring           |

---

## 7. Architecture

### 7.1 High-Level Diagram

```
┌─────────────────────┐     ┌──────────────────────────────────┐
│  Frontend            │     │  Backend (FastAPI)                │
│  React + Vite        │────>│  REST API                        │
│  Tailwind CSS        │     │  CV Parser | Scraper | CV Writer │
│  Lucide Icons        │     │  PDF Generator | Email Service   │
└─────────────────────┘     └──────────┬───────────────────────┘
                                       │
                            ┌──────────┴───────────┐
                            │                      │
                     ┌──────┴──────┐      ┌────────┴────────┐
                     │ PostgreSQL  │      │ Celery + Redis   │
                     │ (data)      │      │ (scheduled tasks)│
                     └─────────────┘      └─────────────────┘
                                                   │
                                          ┌────────┴────────┐
                                          │ External         │
                                          │ OpenAI | SMTP    │
                                          │ Job Portal URLs  │
                                          └─────────────────┘
```

### 7.2 Tech Stack

| Layer           | Technology                                          |
| --------------- | --------------------------------------------------- |
| Backend         | Python 3.11+ / FastAPI / Uvicorn                    |
| Frontend        | React 18 + Vite + Tailwind CSS                      |
| Database        | PostgreSQL (SQLAlchemy + Alembic)                    |
| Task Queue      | Celery + Redis + Celery Beat                         |
| LLM             | OpenAI API (gpt-4o-mini for parsing, gpt-4o for CV) |
| Scraping        | httpx + BeautifulSoup4 (Playwright fallback)         |
| PDF             | WeasyPrint (HTML/CSS to PDF)                         |
| Email           | smtplib (Gmail App Password) or SendGrid             |
| Deployment      | Docker Compose -> Railway / Render / AWS ECS         |

### 7.3 Anti-Blocking Strategy

Low request volume (5x/day max) plus:
- Random delays: 2-10s between requests
- User-Agent rotation: 20+ real browser strings
- Full browser-like headers
- Per-domain rate limit: max 1 req/min
- Optional proxy rotation
- Session/cookie reuse
- Playwright fallback for JS-rendered pages

---

## 8. Database Schema

### CVProfile
| Column          | Type     | Notes                        |
| --------------- | -------- | ---------------------------- |
| id              | int PK   |                              |
| personal_info   | JSON     | name, email, phone, location |
| work_experience | JSON     | array of entries             |
| education       | JSON     | array of entries             |
| skills          | JSON     | array of strings             |
| certifications  | JSON     | array of entries             |
| raw_text        | TEXT     | original parsed text         |
| updated_at      | datetime |                              |

### JobSource
| Column              | Type     | Notes                    |
| ------------------- | -------- | ------------------------ |
| id                  | int PK   |                          |
| url                 | string   | unique                   |
| portal_name         | string   | user-defined label       |
| filters_description | string   | optional                 |
| is_active           | boolean  | default true             |
| last_checked        | datetime |                          |
| created_at          | datetime |                          |

### Job
| Column        | Type     | Notes                              |
| ------------- | -------- | ---------------------------------- |
| id            | int PK   |                                    |
| source_id     | int FK   | -> JobSource                       |
| title         | string   |                                    |
| company       | string   |                                    |
| location      | string   |                                    |
| description   | text     |                                    |
| url           | string   | unique (dedup key)                 |
| status        | string   | New / Viewed / CV Sent / Skipped   |
| is_new        | boolean  |                                    |
| discovered_at | datetime |                                    |

### Application
| Column           | Type     | Notes                |
| ---------------- | -------- | -------------------- |
| id               | int PK   |                      |
| job_id           | int FK   | -> Job               |
| tailored_cv_path | string   | file path to PDF     |
| email_sent_to    | string   |                      |
| email_status     | string   | sent / failed        |
| applied_at       | datetime |                      |

### AppSettings
| Column             | Type   | Notes          |
| ------------------ | ------ | -------------- |
| id                 | int PK | always 1 row   |
| notification_email | string |                |
| smtp_host          | string |                |
| smtp_user          | string |                |
| smtp_password      | string | encrypted      |
| openai_api_key     | string | encrypted      |
| scan_frequency     | int    | times per day  |
| scan_window_start  | time   | e.g., 08:00    |
| scan_window_end    | time   | e.g., 20:00    |

**Relationships**:
- JobSource 1--* Job
- Job 1--0..1 Application
- CVProfile is a singleton (one row)
- AppSettings is a singleton (one row)

---

## 9. Project Structure

```
auto-job-apply/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings (env vars)
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── cv.py
│   │   │   ├── job_source.py
│   │   │   ├── job.py
│   │   │   └── application.py
│   │   ├── routers/
│   │   │   ├── cv.py
│   │   │   ├── sources.py
│   │   │   ├── jobs.py
│   │   │   └── settings.py
│   │   ├── services/
│   │   │   ├── cv_parser.py
│   │   │   ├── cv_writer.py
│   │   │   ├── scraper.py
│   │   │   ├── pdf_generator.py
│   │   │   └── email_sender.py
│   │   ├── tasks/
│   │   │   ├── celery_app.py
│   │   │   └── job_monitor.py
│   │   └── templates/
│   │       └── cv_template.html
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── CVEditor.tsx
│   │   │   ├── Sources.tsx
│   │   │   ├── Jobs.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── Spec.md
├── To-do.md
└── readme.md
```

---

## 10. Testing Standards

### 10.1 Testing Philosophy

Tests are mandatory for every milestone. No milestone is considered complete until all tests pass. Tests should be written alongside code, not as an afterthought.

### 10.2 Backend Testing Stack

| Tool | Purpose |
| --- | --- |
| `pytest` | Test runner and framework |
| `pytest-asyncio` | Async test support for FastAPI/SQLAlchemy |
| `httpx` | Async test client for API endpoints |
| `pytest-cov` | Code coverage reporting |
| `unittest.mock` | Mocking external services (OpenAI, SMTP, etc.) |

### 10.3 Frontend Testing Stack

| Tool | Purpose |
| --- | --- |
| `vitest` | Test runner (Vite-native, fast) |
| `@testing-library/react` | Component testing with user-centric queries |
| `@testing-library/user-event` | Simulating user interactions |
| `@testing-library/jest-dom` | DOM assertion matchers |
| `jsdom` | Browser environment for tests |

### 10.4 Test Categories

| Category | Marker/Label | Scope | When to Run |
| --- | --- | --- | --- |
| **Unit** | `@pytest.mark.unit` | Single function/class, mocked deps | On every change |
| **Integration** | `@pytest.mark.integration` | API endpoints, DB operations | On every change |
| **E2E** | `@pytest.mark.e2e` | Full user flows (browser) | Before milestone completion |

### 10.5 Test Requirements Per Milestone

Each milestone must include tests for all new functionality:

| Milestone | Required Backend Tests | Required Frontend Tests |
| --- | --- | --- |
| **M1** | Models (CVProfile, AppSettings), CV parser, PDF generator, CV API endpoints | UI components, API client, Dashboard, CV Editor |
| **M2** | JobSource model, Job model, Source CRUD endpoints, Scraper service | Sources page, source form, table interactions |
| **M3** | Celery task execution, Job monitor, Job dedup, Job endpoints | Jobs page, filter bar, detail panel |
| **M4** | CV writer service, Tailored PDF generation, Job CV endpoint | Generate CV button flow, download |
| **M5** | Email sender, Settings CRUD, SMTP validation, OpenAI key validation | Settings page, form validation, test email |
| **M6** | Dashboard stats, Error handlers, Retry logic | Dashboard stats, system status, onboarding |

### 10.6 Testing Rules

1. **External services are always mocked**: OpenAI, SMTP, web scrapers, Celery -- never call real services in tests
2. **Test DB is in-memory**: Backend tests use `sqlite+aiosqlite:///:memory:` -- no disk I/O, fully isolated
3. **Each test is independent**: Tests must not depend on the order of execution or state from other tests
4. **Coverage target**: Aim for >85% backend coverage, >70% frontend coverage
5. **Test naming**: Descriptive names that explain the scenario and expected outcome
6. **Assertions**: Test both happy path and error cases (invalid input, missing data, service failures)

### 10.7 Running Tests

**Backend:**
```bash
cd backend && python -m pytest tests/ -v              # all tests
cd backend && python -m pytest tests/ -m unit -v       # unit only
cd backend && python -m pytest tests/ --cov=app        # with coverage
```

**Frontend:**
```bash
cd frontend && npm test                    # all tests
cd frontend && npm run test:watch          # watch mode
cd frontend && npm run test:coverage       # with coverage
```

### 10.8 Milestone Completion Checklist

Before marking any milestone as complete:
- [ ] All existing tests pass (`pytest` + `vitest`)
- [ ] New tests written for all new features
- [ ] Code coverage has not decreased
- [ ] No test relies on external services (all mocked)
- [ ] Test run completes in under 30 seconds

---

## 11. Key Libraries

| Purpose         | Library                                     |
| --------------- | ------------------------------------------- |
| Web framework   | `fastapi`, `uvicorn`                        |
| Database ORM    | `sqlalchemy`, `alembic`, `asyncpg`          |
| Task queue      | `celery`, `redis`                           |
| LLM             | `openai`                                    |
| CV file parsing | `python-docx`, `PyPDF2`, `python-multipart` |
| Web scraping    | `httpx`, `beautifulsoup4`, `playwright`     |
| PDF generation  | `weasyprint`                                |
| Email           | `smtplib` (stdlib), or `sendgrid`           |
| Frontend        | `react`, `vite`, `tailwindcss`, `axios`     |
| Icons           | `lucide-react`                              |
