"""Shared test fixtures for the Auto Job Apply backend test suite."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.main import app


# ---------------------------------------------------------------------------
# In-memory SQLite database for testing (no disk I/O, fully isolated)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Database lifecycle -- create/drop tables per test session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables once for the entire test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


# ---------------------------------------------------------------------------
# Per-test database session with automatic rollback
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def db_session():
    """Provide a transactional database session that rolls back after each test."""
    async with TestSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ---------------------------------------------------------------------------
# Override the FastAPI dependency so endpoints use the test DB
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Async HTTP client wired to the FastAPI app with test DB."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample CV data fixtures
# ---------------------------------------------------------------------------
SAMPLE_PERSONAL_INFO = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1-555-0100",
    "location": "San Francisco, CA",
    "linkedin": "https://linkedin.com/in/janedoe",
    "website": "https://janedoe.dev",
}

SAMPLE_WORK_EXPERIENCE = [
    {
        "title": "Senior Software Engineer",
        "company": "TechCorp",
        "duration": "Jan 2021 - Present",
        "achievements": [
            "Led a team of 5 engineers to build a microservices platform",
            "Reduced API latency by 40% through caching optimization",
        ],
    },
    {
        "title": "Software Engineer",
        "company": "StartupInc",
        "duration": "Jun 2018 - Dec 2020",
        "achievements": [
            "Built REST APIs serving 10K daily active users",
            "Implemented CI/CD pipeline reducing deployment time by 60%",
        ],
    },
]

SAMPLE_EDUCATION = [
    {
        "degree": "B.S. Computer Science",
        "institution": "University of California, Berkeley",
        "year": "2018",
        "details": "Cum Laude, GPA 3.8",
    }
]

SAMPLE_SKILLS = ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker", "AWS"]

SAMPLE_CERTIFICATIONS = [
    {"name": "AWS Solutions Architect", "issuer": "Amazon Web Services", "year": "2023"},
    {"name": "Certified Kubernetes Administrator", "issuer": "CNCF", "year": "2022"},
]

SAMPLE_CV_DATA = {
    "personal_info": SAMPLE_PERSONAL_INFO,
    "summary": "Experienced software engineer with 6+ years building scalable web applications.",
    "work_experience": SAMPLE_WORK_EXPERIENCE,
    "education": SAMPLE_EDUCATION,
    "skills": SAMPLE_SKILLS,
    "certifications": SAMPLE_CERTIFICATIONS,
}

SAMPLE_RAW_TEXT = """Jane Doe
jane@example.com | +1-555-0100 | San Francisco, CA
linkedin.com/in/janedoe | janedoe.dev

Professional Summary
Experienced software engineer with 6+ years building scalable web applications.

Work Experience
Senior Software Engineer | TechCorp | Jan 2021 - Present
- Led a team of 5 engineers to build a microservices platform
- Reduced API latency by 40% through caching optimization

Software Engineer | StartupInc | Jun 2018 - Dec 2020
- Built REST APIs serving 10K daily active users
- Implemented CI/CD pipeline reducing deployment time by 60%

Education
B.S. Computer Science, University of California, Berkeley, 2018
Cum Laude, GPA 3.8

Skills
Python, FastAPI, React, TypeScript, PostgreSQL, Docker, AWS

Certifications
AWS Solutions Architect - Amazon Web Services (2023)
Certified Kubernetes Administrator - CNCF (2022)
"""


@pytest.fixture
def test_db():
    """Return the async session factory so tests can open their own sessions."""
    return TestSessionLocal


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """Clear all table rows between tests so each test gets a clean DB state."""
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
def sample_cv_data():
    """Return a copy of sample CV data for tests to modify freely."""
    import copy
    return copy.deepcopy(SAMPLE_CV_DATA)


@pytest.fixture
def sample_raw_text():
    return SAMPLE_RAW_TEXT
