# Auto Job Apply -- Project Reference

> **This is the master reference document.** The AI assistant reads this file at the start of every interaction to maintain context, consistency, and alignment with product decisions.

---

## What This Project Is

A **single-user micro web app** that passively monitors job portals, generates tailored ATS-friendly CVs using OpenAI, and emails them to you so you can apply manually. Built with FastAPI + React + PostgreSQL + Celery.

---

## Key Documents

| Document | Path | Purpose |
| -------- | ---- | ------- |
| **Spec** | `Spec.md` | Full product & technical specification -- design system, product functionality (screen-by-screen), architecture, database schema, tech stack, scope boundaries |
| **To-Do** | `To-do.md` | Live milestone-based task tracker -- checkbox format, updated as tasks are completed. This is the source of truth for project progress. |
| **Plan** | `.cursor/plans/auto_job_apply_app_1fdec405.plan.md` | Original planning document with architecture diagrams, data flow, milestones, design system, and product functionality |

---

## Product Decisions (Locked)

These decisions have been made and should not be revisited unless the PM explicitly requests changes.

| Decision | Choice | Rationale |
| -------- | ------ | --------- |
| Visual style | Minimal & Light (Notion/Stripe-inspired) | Clean, professional, non-distracting |
| User model | Single user, no authentication | Personal tool, runs locally or on private server |
| CV template | ATS-friendly only | Single column, no graphics, standard fonts, keyword-optimized |
| Job sources | Custom URLs only | No portal login/auth, generic HTML scraping |
| Email behavior | Notify user only (user applies manually) | Not an auto-apply bot, user stays in control |
| Mobile support | Responsive nice-to-have, desktop-first | Primary usage is on desktop |
| Font | Inter | Clean, widely available, excellent readability |
| Icons | Lucide React | Lightweight, consistent, MIT licensed |
| Loading pattern | Skeleton placeholders | Not spinners -- feels faster and more polished |

---

## AI Assistant Operating Rules

### Before Every Response
1. **Read `readme.md`** to refresh context on project decisions and document locations
2. **Check `To-do.md`** to understand current progress and what milestone we are on
3. **Reference `Spec.md`** for any product or design questions

### When Implementing Code
1. Follow the design system tokens defined in `Spec.md` Section 3
2. Match the component patterns specified (button sizes, card styles, etc.)
3. Follow the project structure defined in `Spec.md` Section 9
4. Use the tech stack and libraries specified -- do not introduce alternatives without asking

### When Updating To-do.md
1. Mark tasks `[x]` immediately after completing them
2. Update the milestone **Status** field when all tasks in a milestone are done (change to "Completed")
3. Update the **Summary Progress** table at the bottom
4. Update the **Last updated** date at the top
5. Never remove completed tasks -- they serve as a project history

### When Asking Questions
1. Check `Spec.md` first -- the answer may already be documented
2. Check locked product decisions in this file
3. Only ask the PM when the spec is genuinely ambiguous or a new decision is needed
4. Frame questions with options and your recommendation

### When Something Is Out of Scope
1. Refer to the "Scope Boundaries" table in `Spec.md` Section 6
2. If the user requests something out of scope, flag it clearly and ask if scope should be expanded

---

## Tech Stack Quick Reference

| Layer | Tech |
| ----- | ---- |
| Backend | Python 3.11+ / FastAPI / Uvicorn |
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| Task Queue | Celery + Redis + Celery Beat |
| LLM | OpenAI (gpt-4o-mini for parsing, gpt-4o for CV writing) |
| Scraping | httpx + BeautifulSoup4 (Playwright fallback) |
| PDF | WeasyPrint |
| Email | smtplib (Gmail App Password) or SendGrid |
| Icons | Lucide React |
| Deploy | Docker Compose -> Cloud (Railway / Render / AWS) |

---

## Design Tokens Quick Reference

```css
/* Colors */
--color-bg: #FFFFFF;
--color-surface: #F9FAFB;
--color-border: #E5E7EB;
--color-text: #111827;
--color-text-muted: #6B7280;
--color-primary: #2563EB;
--color-primary-hover: #1D4ED8;
--color-success: #16A34A;
--color-warning: #D97706;
--color-danger: #DC2626;

/* Typography */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Spacing base: 4px */
/* Scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64px */
```

---

## Testing

### Philosophy

Tests are a first-class concern. Every milestone includes a **testing gate** -- all existing tests must pass before a milestone can be marked as complete.

### Backend Tests (pytest)

**Stack**: pytest + pytest-asyncio + httpx (async test client) + pytest-cov  
**Location**: `backend/tests/`  
**Config**: `backend/pytest.ini`

| Test file | Scope | What it covers |
| --- | --- | --- |
| `test_models.py` | Unit/Integration | CVProfile and AppSettings ORM models (CRUD, JSON fields, defaults) |
| `test_models_m2.py` | Unit/Integration | JobSource and Job ORM models (CRUD, unique URL, status lifecycle) |
| `test_cv_parser.py` | Unit | Text extraction (PDF, DOCX), OpenAI parsing (mocked), file routing |
| `test_pdf_generator.py` | Unit | HTML builder, full HTML generation, PDF fallback logic |
| `test_scraper.py` | Unit | HTML parsing, stealth headers, rate limiting, Playwright fallback |
| `test_api_health.py` | Integration | `GET /api/health` endpoint |
| `test_api_cv.py` | Integration | All CV endpoints: GET, PUT, POST upload, preview, error handling |
| `test_api_sources.py` | Integration | Source CRUD, URL validation, dedup, Scan Now endpoint |
| `conftest.py` | Fixtures | In-memory SQLite, test client, sample CV data |

**Run backend tests:**
```bash
cd backend
# Activate venv
.\venv\Scripts\activate       # Windows
source venv/bin/activate       # macOS/Linux

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing

# Run only unit tests
python -m pytest tests/ -m unit -v

# Run only integration tests
python -m pytest tests/ -m integration -v
```

**Current results**: 110 tests, 89% coverage

### Frontend Tests (Vitest)

**Stack**: Vitest + @testing-library/react + @testing-library/user-event + jsdom  
**Location**: `frontend/src/**/*.test.{ts,tsx}`  
**Config**: `frontend/vite.config.ts` (test section)

| Test file | Scope | What it covers |
| --- | --- | --- |
| `components/ui.test.tsx` | Unit | Button, Input, Card, Badge, Modal, Skeleton, Table components |
| `components/Layout.test.tsx` | Unit | Sidebar navigation, links, brand name |
| `api.test.ts` | Unit | API client functions (getCV, updateCV, uploadCV, healthCheck, sources) |
| `pages/Dashboard.test.tsx` | Integration | Loading, onboarding, regular dashboard, error states |
| `pages/Sources.test.tsx` | Integration | Sources page: form, table, actions, validations, error states |
| `App.test.tsx` | Integration | Route setup, page rendering, navigation |

**Run frontend tests:**
```bash
cd frontend
npm install          # install deps including test libs
npm test             # run all tests once
npm run test:watch   # run in watch mode
npm run test:coverage # run with coverage report
```

### Testing Rules for AI Assistant

1. **After implementing any feature or fix**, run the relevant test suite
2. **Before marking a milestone complete**, run ALL tests (backend + frontend)
3. **New code must have tests** -- add tests alongside new features, endpoints, or components
4. **Mocking**: External services (OpenAI, SMTP, scrapers) are always mocked in tests
5. **Test DB**: Backend tests use an in-memory SQLite database, fully isolated per test

---

## Current Status

**Active Milestone**: All Milestones Complete! 🎉  
**Last Completed**: Milestone 6 -- Dashboard, Polish & Deployment  
**Status**: Production Ready  
**Local Dev**: Backend on http://localhost:8000 | Frontend on http://localhost:5173

